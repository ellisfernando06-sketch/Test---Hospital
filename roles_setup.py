# -*- coding: utf-8 -*-
"""
roles_setup.py — Detecta roles existentes por nombre (con emoji).
Si no existen, los CREA con el nombre + emoji y color de config.py.
Guarda IDs y ordena roles por categorías.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

import discord

import config
import roles_store


def _hex_to_colour(hex_str: str) -> discord.Colour:
    h = hex_str.lstrip("#")
    return discord.Colour(int(h, 16))


def _buscar_rol_por_nombre(guild: discord.Guild, nombre: str) -> Optional[discord.Role]:
    for r in guild.roles:
        if r.name == nombre:
            return r
    nombre_l = nombre.lower()
    for r in guild.roles:
        if r.name.lower() == nombre_l:
            return r
    return None


async def _asegurar_rol(
    guild: discord.Guild,
    nombre: str,
    color_hex: str,
    resumen: List[str],
) -> Optional[discord.Role]:
    existente = _buscar_rol_por_nombre(guild, nombre)
    if existente:
        resumen.append(f"✅ Detectado: **{nombre}** (ID `{existente.id}`)")
        return existente

    try:
        rol = await guild.create_role(
            name=nombre,
            colour=_hex_to_colour(color_hex),
            reason="Configuración automática del bot hospitalario",
        )
        resumen.append(f"🆕 Creado: **{nombre}** (ID `{rol.id}`)")
        return rol
    except discord.Forbidden:
        resumen.append(f"❌ Sin permisos para crear: **{nombre}**")
        return None
    except Exception as e:
        resumen.append(f"❌ Error al crear **{nombre}**: {e}")
        return None


def _orden_deseado() -> List[Tuple[str, str]]:
    orden: List[Tuple[str, str]] = []
    seps = {s[0]: s[1] for s in getattr(config, "SEPARADORES_ROLES", [])}

    def sep(key: str):
        if key in seps:
            orden.append(("sep", seps[key]))

    sep("sep_cupula")
    for key in ["OWNER", "CO_OWNER"]:
        if key in config.KEYS_NOMBRES:
            orden.append(("key", config.KEYS_NOMBRES[key][0]))

    sep("sep_servidor")
    for key in ["DIRECTOR_GENERAL", "DIRECTOR_DISCIPLINA", "DIRECTOR_ADMINISTRATIVO", "STAFF_SERVIDOR"]:
        if key in config.KEYS_NOMBRES:
            orden.append(("key", config.KEYS_NOMBRES[key][0]))
    if "staff_servidor" in config.DEPARTAMENTOS:
        for nombre in reversed(config.DEPARTAMENTOS["staff_servidor"]["escalafon_nombres"]):
            orden.append(("escalafon", nombre))

    sep("sep_directores")
    skip = {"DIRECTOR_DISCIPLINA", "DIRECTOR_GENERAL", "DIRECTOR_ADMINISTRATIVO"}
    for key in config.DIRECTOR_KEYS:
        if key in skip:
            continue
        orden.append(("key", config.KEYS_NOMBRES[key][0]))

    depto_sep = {
        "medico": "sep_medico",
        "especialidades": "sep_especialidades",
        "enfermeria": "sep_enfermeria",
        "rrhh": "sep_rrhh",
        "finanzas": "sep_finanzas",
        "logistica": "sep_logistica",
        "seguridad": "sep_seguridad",
        "administracion": "sep_admin",
        "docencia": "sep_docencia",
    }
    for slug, data in config.DEPARTAMENTOS.items():
        if slug == "staff_servidor":
            continue
        sk = depto_sep.get(slug)
        if sk:
            sep(sk)
        for nombre in reversed(data["escalafon_nombres"]):
            orden.append(("escalafon", nombre))

    sep("sep_mandos")
    for key in ["ENCARGADO_AREA", "JEFE_DEPARTAMENTO", "SUPERVISOR"]:
        if key in config.KEYS_NOMBRES:
            orden.append(("key", config.KEYS_NOMBRES[key][0]))

    sep("sep_staff")
    for key in ["RESIDENTE", "STAFF", "PASANTE", "VOLUNTARIO"]:
        if key in config.KEYS_NOMBRES:
            orden.append(("key", config.KEYS_NOMBRES[key][0]))

    orden.append(("extra", config.ROL_SUSPENDIDO_NOMBRE))
    return orden


async def ordenar_roles(guild: discord.Guild) -> List[str]:
    resumen: List[str] = []
    bot_member = guild.me
    if not bot_member:
        return ["❌ No se pudo obtener el miembro del bot."]

    bot_top = bot_member.top_role
    orden = _orden_deseado()

    roles_ordenados: List[discord.Role] = []
    for _, nombre in orden:
        rol = _buscar_rol_por_nombre(guild, nombre)
        if rol and rol < bot_top and not rol.is_default() and not rol.managed:
            roles_ordenados.append(rol)

    if not roles_ordenados:
        resumen.append("⚠️ No hay roles gestionables para ordenar (¿el rol del bot está por encima?).")
        return resumen

    base_pos = bot_top.position - 1
    positions = {}
    roles_omitidos: List[discord.Role] = []
    for i, rol in enumerate(roles_ordenados):
        nueva = base_pos - i
        if nueva < 1:
            roles_omitidos.append(rol)
            continue
        positions[rol] = nueva

    if not positions:
        resumen.append("⚠️ No hay espacio de posiciones disponible para reordenar.")
        return resumen

    try:
        await guild.edit_role_positions(positions=positions, reason="Orden por categorías (bot hospital)")
        resumen.append(f"✅ Roles reordenados ({len(positions)} roles).")
        resumen.append("")
        resumen.append("**Orden aplicado (arriba → abajo):**")
        for r in roles_ordenados:
            if r in positions:
                resumen.append(f"  • {r.name}")
        if roles_omitidos:
            resumen.append("")
            resumen.append(
                f"⚠️ {len(roles_omitidos)} rol(es) no se pudieron reordenar: "
                + ", ".join(r.name for r in roles_omitidos)
            )
    except discord.Forbidden:
        resumen.append("❌ Sin permisos para reordenar roles.")
    except Exception as e:
        resumen.append(f"❌ Error al reordenar: {e}")

    return resumen


async def configurar_todo(guild: discord.Guild) -> List[str]:
    resumen: List[str] = ["**Keys (cargos)**"]

    for key, (nombre, color) in config.KEYS_NOMBRES.items():
        rol = await _asegurar_rol(guild, nombre, color, resumen)
        if rol:
            roles_store.guardar_key(key, rol.id)

    resumen.append("")
    resumen.append("**Departamentos / escalafones**")
    for slug, data in config.DEPARTAMENTOS.items():
        resumen.append(f"— {data['emoji']} {data['nombre']}")
        ids: List[Optional[int]] = []
        color_dir = config.KEYS_NOMBRES.get(data["director_key"], ("", "#95A5A6"))[1]
        for nombre in data["escalafon_nombres"]:
            rol = await _asegurar_rol(guild, nombre, color_dir, resumen)
            ids.append(rol.id if rol else None)
        roles_store.guardar_escalafon(slug, ids)

    resumen.append("")
    resumen.append("**Separadores de categoría**")
    for sep_key, nombre, color in getattr(config, "SEPARADORES_ROLES", []):
        rol = await _asegurar_rol(guild, nombre, color, resumen)
        if rol:
            roles_store.guardar_extra(sep_key, rol.id)

    resumen.append("")
    resumen.append("**Extras**")
    rol_sus = await _asegurar_rol(guild, config.ROL_SUSPENDIDO_NOMBRE, config.ROL_SUSPENDIDO_COLOR, resumen)
    if rol_sus:
        roles_store.guardar_extra("SUSPENDIDO", rol_sus.id)

    resumen.append("")
    resumen.append("**Ordenamiento por categorías**")
    resumen.extend(await ordenar_roles(guild))

    return resumen
