# -*- coding: utf-8 -*-
"""
roles_categoria.py — Roles de categoría (uniformes) al entrar.
Separado para no romper roles_setup.
"""
from __future__ import annotations

from typing import List, Optional

import discord

import roles_config
import roles_store

_CLAVES_CATEGORIA = ("uniforme_medico", "uniforme_enfermeria", "accesorio_rp")


def _buscar_por_nombre(guild: discord.Guild, nombre: str) -> Optional[discord.Role]:
    if not nombre:
        return None
    for r in guild.roles:
        if r.name == nombre:
            return r
    nl = nombre.lower().strip()
    for r in guild.roles:
        if (r.name or "").lower().strip() == nl:
            return r
    return None


def roles_de_categoria(guild: discord.Guild) -> List[discord.Role]:
    """Uniforme médico, enfermería y accesorio RP."""
    out: List[discord.Role] = []
    vistos = set()

    for clave in _CLAVES_CATEGORIA:
        rid = roles_store.obtener_extra(f"otorgado_{clave}")
        if rid:
            rol = guild.get_role(rid)
            if rol and rol.id not in vistos:
                out.append(rol)
                vistos.add(rol.id)
                continue
        nombre = roles_config.ROLES_OTORGADOS_CONSERVAR.get(clave, (None,))[0]
        if nombre:
            r = _buscar_por_nombre(guild, nombre)
            if r and r.id not in vistos:
                out.append(r)
                vistos.add(r.id)

    # Fallback por palabras en el nombre
    keywords = (
        ("uniforme médico", "uniforme medico"),
        ("uniforme enfermería", "uniforme enfermeria"),
        ("accesorio rp", "accesorio"),
    )
    for r in guild.roles:
        if r.id in vistos or r.is_default() or r.managed:
            continue
        rn = (r.name or "").lower()
        for group in keywords:
            if any(k in rn for k in group):
                out.append(r)
                vistos.add(r.id)
                break
    return out


async def otorgar_categorias_al_entrar(member: discord.Member) -> int:
    roles = roles_de_categoria(member.guild)
    if not roles:
        return 0
    a_dar = [r for r in roles if r not in member.roles]
    if not a_dar:
        return 0
    try:
        await member.add_roles(*a_dar, reason="Bienvenida — roles de categoría")
        return len(a_dar)
    except discord.Forbidden:
        return -1
    except Exception:
        return -1
