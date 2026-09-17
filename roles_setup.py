# -*- coding: utf-8 -*-
"""
roles_setup.py — Detecta roles existentes por nombre (NO crea nuevos si ya existen),
guarda IDs y ordena roles por categorías (RRHH, Médico, etc.).
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
    """Busca por nombre exacto (case-sensitive como en Discord)."""
    for r in guild.roles:
        if r.name == nombre:
            return r
    # Fallback: sin importar mayúsculas
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
    """
    Si el rol ya existe (por nombre), lo usa y no crea otro.
    Solo crea si no existe ninguno con ese nombre.
    """
    existente = _buscar_rol_por_nombre(guild, nombre)
    if existente:
        resumen.append(f"✅ Detectado: **{nombre}** (ID `{existente.id}`)")
        return existente

    # Crear solo si no existe
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
    Lista ordenada (de arriba hacia abajo en Discord) de (tipo, nombre_rol).
    tipo: 'key' | 'escalafon' | 'extra'
    """
    orden: List[Tuple[str, str]] = []

    # Cúpula
    for key in ["OWNER", "CO_OWNER", "ENCARGADO_DISCIPLINA", "JEFE_JUNTA_DIRECTIVA", "JUNTA_DIRECTIVA"]:
        if key in config.KEYS_NOMBRES:
            orden.append(("key", config.KEYS_NOMBRES[key][0]))

    # Directores (en orden de config)
    for key in config.DIRECTOR_KEYS:
        orden.append(("key", config.KEYS_NOMBRES[key][0]))

    # Por cada departamento: director ya está arriba; aquí el escalafón de mayor a menor
    for slug, data in config.DEPARTAMENTOS.items():
        # Escalafón de mayor a menor (invertido)
        for nombre in reversed(data["escalafon_nombres"]):
            orden.append(("escalafon", nombre))

    # Niveles genéricos
    for key in ["JEFE_DEPARTAMENTO", "SUPERVISOR", "STAFF"]:
        if key in config.KEYS_NOMBRES:
            orden.append(("key", config.KEYS_NOMBRES[key][0]))

    # Suspendido al final
    orden.append(("extra", config.ROL_SUSPENDIDO_NOMBRE))

    return orden


async def ordenar_roles(guild: discord.Guild) -> List[str]:
    """
    Reordena los roles del servidor según categorías.
    Discord: posición más alta = más arriba en la lista.
    El bot solo mueve roles por debajo de su propio rol.
    """
    resumen: List[str] = []
    bot_member = guild.me
    if not bot_member:
        return ["❌ No se pudo obtener el miembro del bot."]

    bot_top = bot_member.top_role
    orden = _orden_deseado()

    # Construir lista de roles existentes en el orden deseado (solo los que existen)
    roles_ordenados: List[discord.Role] = []
    for _, nombre in orden:
        rol = _buscar_rol_por_nombre(guild, nombre)
        if rol and rol < bot_top and not rol.is_default() and not rol.managed:
            roles_ordenados.append(rol)

    if not roles_ordenados:
        resumen.append("⚠️ No hay roles gestionables para ordenar (¿el rol del bot está por encima?).")
        return resumen

    # Discord API: edit positions — asignamos posiciones decrecientes bajo el bot
    # Posición del bot es la máxima que podemos tocar.
    base_pos = bot_top.position - 1
    positions = {}
    for i, rol in enumerate(roles_ordenados):
        nueva = base_pos - i
        if nueva < 1:
            nueva = 1
        positions[rol] = nueva

    try:
        await guild.edit_role_positions(positions=positions, reason="Orden por categorías (bot hospital)")
        resumen.append(f"✅ Roles reordenados ({len(roles_ordenados)} roles).")
        # Detalle por categoría
        resumen.append("")
        resumen.append("**Orden aplicado (arriba → abajo):**")
        for r in roles_ordenados:
            resumen.append(f"  • {r.name}")
    except discord.Forbidden:
        resumen.append("❌ Sin permisos para reordenar roles. Sube el rol del bot por encima de los roles a ordenar.")
    except Exception as e:
        resumen.append(f"❌ Error al reordenar: {e}")

    return resumen


async def configurar_todo(guild: discord.Guild) -> List[str]:
    """
    1. Detecta (o crea si no existen) todos los roles de keys, escalafones y extras.
    2. Guarda sus IDs en roles_store.
    3. Ordena por categorías.
    """
    resumen: List[str] = ["**Keys (cargos)**"]

    # Keys
    for key, (nombre, color) in config.KEYS_NOMBRES.items():
        rol = await _asegurar_rol(guild, nombre, color, resumen)
        if rol:
            roles_store.guardar_key(key, rol.id)

    # Escalafones por departamento
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

    # Extra: Suspendido
    resumen.append("")
    resumen.append("**Extras**")
    rol_sus = await _asegurar_rol(guild, config.ROL_SUSPENDIDO_NOMBRE, config.ROL_SUSPENDIDO_COLOR, resumen)
    if rol_sus:
        roles_store.guardar_extra("SUSPENDIDO", rol_sus.id)

    # Ordenar
    resumen.append("")
    resumen.append("**Ordenamiento por categorías**")
    resumen.extend(await ordenar_roles(guild))

    return resumen
