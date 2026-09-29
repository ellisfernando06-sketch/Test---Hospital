# -*- coding: utf-8 -*-
"""
roles_setup.py — Crea y ordena roles según el organigrama oficial (roles_config).
No borra roles antiguos aquí; eso se hace en un paso posterior con respaldo.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

import discord

import roles_config
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
    # Compatibilidad: detectar el antiguo "Gerente Developer" / Owner
    if "fundador" in nombre_l or "owner" in nombre_l:
        for r in guild.roles:
            rn = (r.name or "").lower()
            if any(x in rn for x in ("gerente developer", "👑 owner", "owner", "fundador")):
                return r
    return None


async def _asegurar_rol(
    guild: discord.Guild,
    nombre: str,
    color_hex: str,
    resumen: List[str],
    *,
    renombrar_si_antiguo: bool = False,
) -> Optional[discord.Role]:
    existente = _buscar_rol_por_nombre(guild, nombre)
    if existente:
        # Si es el antiguo Owner/Gerente y el nuevo es Fundador y Owner → renombrar
        if renombrar_si_antiguo and existente.name != nombre:
            try:
                await existente.edit(
                    name=nombre,
                    colour=_hex_to_colour(color_hex),
                    reason="Migración a organigrama oficial",
                )
                resumen.append(f"🔄 Renombrado: **{existente.name}** → **{nombre}**")
            except Exception:
                resumen.append(f"✅ Detectado: **{existente.name}** (ID `{existente.id}`)")
        else:
            # Ajustar color si hace falta
            try:
                color_actual = str(existente.colour)
                if color_hex.lower() not in color_actual.lower():
                    await existente.edit(colour=_hex_to_colour(color_hex), reason="Ajuste color organigrama")
            except Exception:
                pass
            resumen.append(f"✅ Detectado: **{nombre}** (ID `{existente.id}`)")
        return existente

    try:
        rol = await guild.create_role(
            name=nombre,
            colour=_hex_to_colour(color_hex),
            reason="Organigrama oficial — creación automática",
            mentionable=False,
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
    """Orden de arriba → abajo según organigrama oficial."""
    orden: List[Tuple[str, str]] = []

    seps = {s[0]: s[1] for s in roles_config.SEPARADORES_ROLES}

    def sep(key: str):
        if key in seps:
            orden.append(("sep", seps[key]))

    # Autoridades
    sep("sep_autoridades")
    for key in ("FUNDADOR_OWNER", "CO_OWNER"):
        if key in roles_config.KEYS_NOMBRES:
            orden.append(("key", roles_config.KEYS_NOMBRES[key][0]))

    # Staff del Server
    sep("sep_staff_server")
    for key in ("ADMIN_JEFE", "ADMIN", "ADMIN_PRUEBA"):
        if key in roles_config.KEYS_NOMBRES:
            orden.append(("key", roles_config.KEYS_NOMBRES[key][0]))

    # Gerencia
    sep("sep_gerencia")
    for key in (
        "PREFECTO_OPERACIONES", "DIR_GENERAL", "DIR_MEDICO",
        "DIR_RRHH", "DIR_DOCENCIA", "DIR_LOGISTICA",
    ):
        if key in roles_config.KEYS_NOMBRES:
            orden.append(("key", roles_config.KEYS_NOMBRES[key][0]))

    # Jefatura
    sep("sep_jefatura")
    if "JEFE_DEPARTAMENTO" in roles_config.KEYS_NOMBRES:
        orden.append(("key", roles_config.KEYS_NOMBRES["JEFE_DEPARTAMENTO"][0]))

    # Área Médica
    sep("sep_area_medica")
    for key in (
        "JEFE_SERVICIO", "MEDICO_ESPECIALISTA", "MEDICO_GENERAL",
        "JEFE_GUIA_RESIDENTES", "RESIDENTE", "INTERNO",
    ):
        if key in roles_config.KEYS_NOMBRES:
            orden.append(("key", roles_config.KEYS_NOMBRES[key][0]))

    # Área Administrativa
    sep("sep_area_admin")
    for key in ("ADMINISTRATIVO_SENIOR", "ADMINISTRATIVO_JUNIOR"):
        if key in roles_config.KEYS_NOMBRES:
            orden.append(("key", roles_config.KEYS_NOMBRES[key][0]))

    # Sistema
    sep("sep_sistema")
    if "INACTIVIDAD_JUSTIFICADA" in roles_config.KEYS_NOMBRES:
        orden.append(("key", roles_config.KEYS_NOMBRES["INACTIVIDAD_JUSTIFICADA"][0]))

    # Roles otorgados conservados (Docencia + Seguridad + Uniformes)
    for _clave, (nombre, _color) in roles_config.ROLES_OTORGADOS_CONSERVAR.items():
        orden.append(("otorgado", nombre))

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
        await guild.edit_role_positions(positions=positions, reason="Orden organigrama oficial")
        resumen.append(f"✅ Roles reordenados ({len(positions)}).")
        resumen.append("**Orden (organigrama oficial):**")
        for r in roles_ordenados:
            if r in positions:
                resumen.append(f"  • {r.name}")
        if roles_omitidos:
            resumen.append(f"⚠️ Omitidos por posición: {', '.join(r.name for r in roles_omitidos)}")
    except discord.Forbidden:
        resumen.append("❌ Sin permisos para reordenar roles.")
    except Exception as e:
        resumen.append(f"❌ Error al reordenar: {e}")

    return resumen


async def configurar_organigrama(guild: discord.Guild) -> List[str]:
    """
    Crea / detecta todos los roles del organigrama oficial +
    Inactividad Justificada + roles otorgados conservados.
    Guarda los IDs en roles_store.
    """
    resumen: List[str] = ["**Organigrama oficial — Roles de permiso**"]

    for key, (nombre, color) in roles_config.KEYS_NOMBRES.items():
        renombrar = key == "FUNDADOR_OWNER"  # renombrar antiguo Owner/Gerente
        rol = await _asegurar_rol(guild, nombre, color, resumen, renombrar_si_antiguo=renombrar)
        if rol:
            roles_store.guardar_key(key, rol.id)

    resumen.append("")
    resumen.append("**Roles otorgados conservados (Docencia + Seguridad + Uniformes)**")
    for clave, (nombre, color) in roles_config.ROLES_OTORGADOS_CONSERVAR.items():
        rol = await _asegurar_rol(guild, nombre, color, resumen)
        if rol:
            roles_store.guardar_extra(f"otorgado_{clave}", rol.id)

    resumen.append("")
    resumen.append("**Separadores de sección**")
    for sep_key, nombre, color in roles_config.SEPARADORES_ROLES:
        rol = await _asegurar_rol(guild, nombre, color, resumen)
        if rol:
            roles_store.guardar_extra(sep_key, rol.id)

    resumen.append("")
    resumen.append("**Orden jerárquico**")
    resumen.extend(await ordenar_roles(guild))

    return resumen


# Alias de compatibilidad con el código antiguo
async def configurar_todo(guild: discord.Guild) -> List[str]:
    return await configurar_organigrama(guild)
