# -*- coding: utf-8 -*-
"""
roles_acceso.py — Roles de acceso del servidor (no jerarquía).
- Miembro: al aceptar / firmar las reglas
- Comunidad: al verificarse (Roblox)
Separadores del organigrama: solo visuales (sin color, sin permisos, no se otorgan a usuarios).
"""
from __future__ import annotations

from typing import Optional

import discord

NOMBRES_MIEMBRO = (
    "👤 Miembro",
    "Miembro",
    "✅ Miembro",
    "miembro",
)
NOMBRES_COMUNIDAD = (
    "🌐 Comunidad",
    "Comunidad",
    "✅ Comunidad",
    "comunidad",
    "Miembro de la comunidad",
)
NOMBRES_VISITANTE = (
    "👤 Visitante",
    "Visitante",
    "visitante",
)


def _buscar(guild: discord.Guild, nombres: tuple) -> Optional[discord.Role]:
    lower = {n.lower() for n in nombres}
    for r in guild.roles:
        if r.name in nombres or (r.name or "").lower() in lower:
            return r
    for r in guild.roles:
        rn = (r.name or "").lower()
        for n in lower:
            if n in rn:
                return r
    return None


def rol_miembro(guild: discord.Guild) -> Optional[discord.Role]:
    return _buscar(guild, NOMBRES_MIEMBRO)


def rol_comunidad(guild: discord.Guild) -> Optional[discord.Role]:
    return _buscar(guild, NOMBRES_COMUNIDAD)


def rol_visitante(guild: discord.Guild) -> Optional[discord.Role]:
    return _buscar(guild, NOMBRES_VISITANTE)


async def asegurar_roles_acceso(guild: discord.Guild) -> dict:
    """Crea Miembro y Comunidad si no existen (sin permisos especiales)."""
    out = {}
    specs = [
        ("miembro", "👤 Miembro", 0x2ECC71),
        ("comunidad", "🌐 Comunidad", 0x3498DB),
        ("visitante", "👤 Visitante", 0x95A5A6),
    ]
    for key, nombre, color in specs:
        existing = _buscar(guild, (nombre, nombre.replace("👤 ", "").replace("🌐 ", "")))
        if existing:
            out[key] = existing
            continue
        try:
            rol = await guild.create_role(
                name=nombre,
                colour=discord.Colour(color),
                permissions=discord.Permissions.none(),
                hoist=False,
                mentionable=False,
                reason="Roles de acceso (reglas / verificación)",
            )
            out[key] = rol
        except Exception as e:
            print(f"[roles_acceso] no se pudo crear {nombre}: {e}", flush=True)
    return out
