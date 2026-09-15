"""
permisos.py
===========
Lógica de permisos por "key". Los IDs de rol ya NO viven en config.py:
se leen de roles_store.py, que el bot llena solo al correr
/configurar_roles. Este archivo no necesita edición.
"""

import discord
from discord import app_commands

import config
import roles_store


class SinPermiso(app_commands.CheckFailure):
    """Error personalizado cuando a alguien le falta una key requerida."""

    def __init__(self, keys_requeridas):
        self.keys_requeridas = keys_requeridas
        super().__init__(f"Se requiere una de estas keys: {', '.join(keys_requeridas)}")


def _ids_del_member(member: discord.Member) -> set:
    return {r.id for r in member.roles}


def ids_de_key(key: str) -> set:
    """IDs de rol de Discord asociados a una key (ya creados/asignados)."""
    if key == "DIRECTOR":
        ids = set()
        for k in config.DIRECTOR_KEYS:
            rid = roles_store.obtener_id_key(k)
            if rid:
                ids.add(rid)
        return ids
    rid = roles_store.obtener_id_key(key)
    return {rid} if rid else set()


def member_tiene_key(member: discord.Member, key: str) -> bool:
    ids_requeridos = ids_de_key(key)
    if not ids_requeridos:
        return False
    return bool(_ids_del_member(member) & ids_requeridos)


def member_tiene_alguna_key(member: discord.Member, *keys: str) -> bool:
    if member_tiene_key(member, "OWNER"):
        return True
    return any(member_tiene_key(member, k) for k in keys)


def nivel_del_member(member: discord.Member) -> int:
    nivel = -1
    for i, key in enumerate(config.JERARQUIA_KEYS):
        if member_tiene_key(member, key):
            nivel = max(nivel, i)
    return nivel


def nivel_de_rol(role_id: int) -> int:
    nivel = -1
    for i, key in enumerate(config.JERARQUIA_KEYS):
        if role_id in ids_de_key(key):
            nivel = max(nivel, i)
    return nivel


def puede_actuar_sobre(emisor: discord.Member, objetivo: discord.Member) -> bool:
    """True si `emisor` tiene autoridad jerárquica para actuar sobre `objetivo`
    (despedir, suspender, etc.). El OWNER siempre puede."""
    if member_tiene_key(emisor, "OWNER"):
        return True
    return nivel_del_member(emisor) > nivel_del_member(objetivo)


def require_key(*keys: str):
    """Decorador: exige al menos una de las keys indicadas (OWNER siempre pasa)."""

    async def predicate(interaction: discord.Interaction) -> bool:
        member = interaction.user
        if not isinstance(member, discord.Member):
            return False
        if member_tiene_alguna_key(member, *keys):
            return True
        raise SinPermiso(keys)

    return app_commands.check(predicate)


def keys_del_member(member: discord.Member) -> list:
    return [k for k in config.KEYS_NOMBRES if member_tiene_key(member, k)]


def departamento_por_director_key(director_key: str):
    for slug, data in config.DEPARTAMENTOS.items():
        if data["director_key"] == director_key:
            return slug
    return None


def departamento_del_member(member: discord.Member):
    """Detecta a qué departamento pertenece un member: por tener un rol de su
    escalafón, o por ser el director de ese departamento. Devuelve el slug o
    None si no pertenece a ninguno."""
    ids_member = _ids_del_member(member)
    for slug, data in config.DEPARTAMENTOS.items():
        cantidad = len(data["escalafon_nombres"])
        ids_escalafon = {rid for rid in roles_store.escalafon_ids(slug, cantidad) if rid}
        if ids_member & ids_escalafon:
            return slug
        if member_tiene_key(member, data["director_key"]):
            return slug
    return None


def miembros_con_key(guild: discord.Guild, key: str) -> list:
    """Lista de members del guild que tienen esa key (para DMs, ej. RRHH)."""
    ids = ids_de_key(key)
    if not ids:
        return []
    return [m for m in guild.members if not m.bot and (_ids_del_member(m) & ids)]
