# -*- coding: utf-8 -*
"""
roles_setup.py — Categorías (separadores) y roles dentro de cada una.
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
    if "gerente developer" in nombre_l:
        for r in guild.roles:
            rn = r.name.lower()
            if rn in ("👑 owner", "owner", "👑owner") or "owner" == rn.strip("👑 ").strip():
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
        if existente.name != nombre and "owner" in existente.name.lower() and "gerente" in nombre.lower():
            try:
                await existente.edit(name=nombre, colour=_hex_to_colour(color_hex), reason="Renombrar a Gerente Developer")
                resumen.append(f"🔄 Renombrado: **{existente.name}** → **{nombre}**")
            except Exception:
                resumen.append(f"✅ Detectado: **{existente.name}** (ID `{existente.id}`)")
        else:
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
    """
    Orden de arriba → abajo (categorías + roles dentro).
    """
    orden: List[Tuple[str, str]] = []
    seps = {s[0]: s[1] for s in getattr(config, "SEPARADORES_ROLES", [])}

    def sep(key: str):
        if key in seps:
            orden.append(("sep", seps[key]))

    # 1. Cúpula
    sep("sep_cupula")
    if "OWNER" in config.KEYS_NOMBRES:
        orden.append(("key", config.KEYS_NOMBRES["OWNER"][0]))
    if "CO_OWNER" in config.KEYS_NOMBRES:
        orden.append(("key", config.KEYS_NOMBRES["CO_OWNER"][0]))

    # 2. Staff servidor
    sep("sep_servidor")
    if "STAFF_SERVIDOR" in config.KEYS_NOMBRES:
        orden.append(("key", config.KEYS_NOMBRES["STAFF_SERVIDOR"][0]))
    if "staff_servidor" in config.DEPARTAMENTOS:
        for nombre in reversed(config.DEPARTAMENTOS["staff_servidor"]["escalafon_nombres"]):
            orden.append(("escalafon", nombre))

    # 3. Dirección
    sep("sep_directores")
    for key in [
        "DIRECTOR_GENERAL",
        "DIRECTOR_DISCIPLINA",
        "DIRECTOR_ADMINISTRATIVO",
        "DIRECTOR_MEDICO",
        "DIRECTOR_ENFERMERIA",
        "DIRECTOR_RRHH",
        "DIRECTOR_FINANCIERO",
        "DIRECTOR_LOGISTICA",
        "DIRECTOR_SEGURIDAD",
        "DIRECTOR_DOCENCIA",
    ]:
        if key in config.KEYS_NOMBRES:
            orden.append(("key", config.KEYS_NOMBRES[key][0]))

    # 4. Departamentos / escalafones
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

    # 5. Mandos intermedios + personal
    sep("sep_mandos")
    for key in ["ENCARGADO_AREA", "JEFE_DEPARTAMENTO", "SUPERVISOR"]:
        if key in config.KEYS_NOMBRES:
            orden.append(("key", config.KEYS_NOMBRES[key][0]))

    sep("sep_staff")
    for key in ["RESIDENTE", "STAFF", "PASANTE", "VOLUNTARIO"]:
        if key in config.KEYS_NOMBRES:
            orden.append(("key", config.KEYS_NOMBRES[key][0]))

    # 6. Categorías de otorgados: separador + roles de esa categoría
    otorgados = getattr(config, "ROLES_OTORGADOS", {}) or {}
    for sep_key in (
        "sep_graduados",
        "sep_identificacion",
        "sep_equipo_rp",
        "sep_uniformes",
    ):
        sep(sep_key)
        for _clave, (nombre, _color, sk) in otorgados.items():
            if sk == sep_key:
                orden.append(("otorgado", nombre))

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
        resumen.append("⚠️ No hay roles gestionables para ordenar.")
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
        resumen.append("⚠️ No hay espacio de posiciones.")
        return resumen

    try:
        await guild.edit_role_positions(positions=positions, reason="Orden hospital")
        resumen.append(f"✅ Roles reordenados ({len(positions)}).")
        resumen.append("**Orden (categorías + roles):**")
        for r in roles_ordenados:
            if r in positions:
                resumen.append(f"  • {r.name}")
        if roles_omitidos:
            resumen.append(f"⚠️ Omitidos: {', '.join(r.name for r in roles_omitidos)}")
    except discord.Forbidden:
        resumen.append("❌ Sin permisos para reordenar.")
    except Exception as e:
        resumen.append(f"❌ Error: {e}")

    return resumen


async def configurar_todo(guild: discord.Guild) -> List[str]:
    resumen: List[str] = ["**Keys (cargos / permisos del bot)**"]

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
    resumen.append("**Categorías (separadores)**")
    for sep_key, nombre, color in getattr(config, "SEPARADORES_ROLES", []):
        rol = await _asegurar_rol(guild, nombre, color, resumen)
        if rol:
            roles_store.guardar_extra(sep_key, rol.id)

    resumen.append("")
    resumen.append("**Roles otorgados (dentro de cada categoría)**")
    for clave, (nombre, color, sep_key) in getattr(config, "ROLES_OTORGADOS", {}).items():
        rol = await _asegurar_rol(guild, nombre, color, resumen)
        if rol:
            roles_store.guardar_extra(f"otorgado_{clave}", rol.id)

    resumen.append("")
    resumen.append("**Extras**")
    rol_sus = await _asegurar_rol(guild, config.ROL_SUSPENDIDO_NOMBRE, config.ROL_SUSPENDIDO_COLOR, resumen)
    if rol_sus:
        roles_store.guardar_extra("SUSPENDIDO", rol_sus.id)

    resumen.append("")
    resumen.append("**Orden**")
    resumen.extend(await ordenar_roles(guild))

    return resumen
