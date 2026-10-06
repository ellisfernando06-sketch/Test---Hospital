# -*- coding: utf-8 -*-
"""
Roles de sanción en el perfil del miembro.

  advertencia     → ⚠️ Advertencia
  disciplinaria   → 🔨 Sanción Disciplinaria
  administrativa  → 📋 Sanción Administrativa
  ban             → ⏳ Cuarentena
  timeout/kick    → 🔨 Sanción Disciplinaria
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

import discord
from discord.ext import commands

_ROLES_SANCION: Dict[str, Tuple[str, Optional[int]]] = {
    "advertencia": ("⚠️ Advertencia", 0xF1C40F),
    "disciplinaria": ("🔨 Sanción Disciplinaria", 0xE67E22),
    "sancion": ("🔨 Sanción Disciplinaria", 0xE67E22),
    "sanción": ("🔨 Sanción Disciplinaria", 0xE67E22),
    "administrativa": ("📋 Sanción Administrativa", 0x8E44AD),
    "ban": ("⏳ Cuarentena", 0x95A5A6),
    "timeout": ("🔨 Sanción Disciplinaria", 0xE67E22),
    "kick": ("🔨 Sanción Disciplinaria", 0xE67E22),
}


async def _obtener_o_crear_rol(
    guild: discord.Guild, nombre: str, color: Optional[int]
) -> Optional[discord.Role]:
    rol = discord.utils.get(guild.roles, name=nombre)
    if rol:
        return rol
    # Buscar por nombre sin emoji
    base = nombre.split(" ", 1)[-1].lower() if " " in nombre else nombre.lower()
    for r in guild.roles:
        if base in (r.name or "").lower() and any(
            x in (r.name or "").lower()
            for x in ("advertencia", "disciplinaria", "administrativa", "cuarentena")
        ):
            return r
    try:
        kwargs = {
            "name": nombre,
            "permissions": discord.Permissions.none(),
            "hoist": False,
            "mentionable": False,
            "reason": "Rol de estado de sanción",
        }
        if color is not None:
            kwargs["colour"] = discord.Colour(color)
        return await guild.create_role(**kwargs)
    except Exception as e:
        print(f"[sancion_roles] crear {nombre}: {e}")
        return None


async def otorgar_rol_sancion(
    guild: discord.Guild, member: discord.Member, tipo: str
) -> Optional[discord.Role]:
    tipo_n = (tipo or "").lower()
    meta = _ROLES_SANCION.get(tipo_n)
    if not meta:
        print(f"[sancion_roles] tipo desconocido: {tipo_n}")
        return None
    nombre, color = meta
    rol = await _obtener_o_crear_rol(guild, nombre, color)
    if not rol:
        return None
    if rol not in member.roles:
        try:
            await member.add_roles(rol, reason=f"Sanción: {tipo_n}")
            print(f"[sancion_roles] + {nombre} → {member}")
        except Exception as e:
            print(f"[sancion_roles] add: {e}")
            return None
    return rol


async def quitar_rol_sancion(
    guild: discord.Guild, member: discord.Member, tipo: str
) -> None:
    tipo_n = (tipo or "").lower()
    meta = _ROLES_SANCION.get(tipo_n)
    if not meta:
        return
    nombre, _ = meta
    rol = discord.utils.get(guild.roles, name=nombre)
    if rol and rol in member.roles:
        try:
            await member.remove_roles(rol, reason="Sanción anulada")
        except Exception as e:
            print(f"[sancion_roles] remove: {e}")


async def quitar_todos_roles_sancion(
    guild: discord.Guild, member: discord.Member
) -> None:
    nombres = {meta[0] for meta in _ROLES_SANCION.values()}
    for r in list(member.roles):
        if r.name in nombres or "cuarentena" in (r.name or "").lower():
            try:
                await member.remove_roles(r, reason="Sanción anulada")
            except Exception:
                pass


def registrar(bot: commands.Bot) -> None:
    print("[sancion_roles] OK — otorgar_rol_sancion listo")
