# -*- coding: utf-8 -*-
"""
permisos.py — Sistema de keys / jerarquía.
"""
from __future__ import annotations

from typing import List, Optional, Set

import discord
from discord import app_commands

import config
import roles_store


class SinPermiso(app_commands.AppCommandError):
    def __init__(self, keys_requeridas: List[str]):
        self.keys_requeridas = keys_requeridas
        super().__init__(f"Se requiere una de: {', '.join(keys_requeridas)}")


def nivel_de_key(key: str) -> int:
    """Nivel numérico (mayor = más alto). DIRECTOR_* se trata como DIRECTOR."""
    if key.startswith("DIRECTOR_"):
        key = "DIRECTOR"
    try:
        return config.JERARQUIA_KEYS.index(key)
    except ValueError:
        return -1


def nivel_de_rol(role_id: int) -> int:
    """Si el rol es una key conocida, devuelve su nivel; si no, -1."""
    for key, rid in roles_store.todas_las_keys().items():
        if rid == role_id:
            return nivel_de_key(key)
    # Escalafones de departamento: nivel STAFF-ish
    return -1


def keys_del_member(member: discord.Member) -> List[str]:
    ids = {r.id for r in member.roles}
    out = []
    for key, rid in roles_store.todas_las_keys().items():
        if rid in ids:
            out.append(key)
    return out


def member_tiene_key(member: discord.Member, key: str) -> bool:
    rid = roles_store.obtener_id_key(key)
    if not rid:
        return False
    return any(r.id == rid for r in member.roles)


def member_tiene_alguna_key(member: discord.Member, *keys: str) -> bool:
    for k in keys:
        if k == "DIRECTOR":
            if any(member_tiene_key(member, dk) for dk in config.DIRECTOR_KEYS):
                return True
        elif member_tiene_key(member, k):
            return True
    return False


def nivel_del_member(member: discord.Member) -> int:
    keys = keys_del_member(member)
    if not keys:
        return -1
    return max(nivel_de_key(k) for k in keys)


def puede_actuar_sobre(emisor: discord.Member, objetivo: discord.Member) -> bool:
    """True si el emisor tiene nivel estrictamente mayor que el objetivo (OWNER siempre puede)."""
    if member_tiene_key(emisor, "OWNER"):
        return True
    return nivel_del_member(emisor) > nivel_del_member(objetivo)


def departamento_del_member(member: discord.Member) -> Optional[str]:
    """Devuelve el slug del departamento si tiene algún rol de escalafón."""
    ids = {r.id for r in member.roles}
    for slug, data in config.DEPARTAMENTOS.items():
        escalafon = roles_store.escalafon_ids(slug, len(data["escalafon_nombres"]))
        if any(rid and rid in ids for rid in escalafon):
            return slug
        # También cuenta si tiene la key de director de ese depto
        if member_tiene_key(member, data["director_key"]):
            return slug
    return None


def require_key(*keys: str):
    """Decorador de app_commands: exige al menos una de las keys."""

    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            raise SinPermiso(list(keys))
        if member_tiene_alguna_key(interaction.user, *keys):
            return True
        raise SinPermiso(list(keys))

    return app_commands.check(predicate)
