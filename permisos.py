# -*- coding: utf-8 -*
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
    for key, rid in roles_store.todas_las_keys().items():
        if rid == role_id:
            return nivel_de_key(key)
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
    if member_tiene_key(emisor, "OWNER"):
        return True
    return nivel_del_member(emisor) > nivel_del_member(objetivo)


def departamento_del_member(member: discord.Member) -> Optional[str]:
    ids = {r.id for r in member.roles}
    for slug, data in config.DEPARTAMENTOS.items():
        escalafon = roles_store.escalafon_ids(slug, len(data["escalafon_nombres"]))
        if any(rid and rid in ids for rid in escalafon):
            return slug
        if member_tiene_key(member, data["director_key"]):
            return slug
    return None


def require_key(*keys: str):
    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            raise SinPermiso(list(keys))
        if member_tiene_alguna_key(interaction.user, *keys):
            return True
        raise SinPermiso(list(keys))

    return app_commands.check(predicate)


# ── Jerarquía médica / staff ──────────────────────────────────────────

KEYS_MEDICO_BASICO = (
    "VOLUNTARIO", "PASANTE", "STAFF", "RESIDENTE",
    "SUPERVISOR", "JEFE_DEPARTAMENTO", "ENCARGADO_AREA",
    "DIRECTOR", "DIRECTOR_MEDICO", "DIRECTOR_ENFERMERIA",
    "OWNER", "CO_OWNER",
)

KEYS_MEDICO_AVANZADO = (
    "SUPERVISOR", "JEFE_DEPARTAMENTO", "ENCARGADO_AREA",
    "DIRECTOR", "DIRECTOR_MEDICO", "DIRECTOR_ENFERMERIA",
    "OWNER", "CO_OWNER",
)

KEYS_MEDICO_DIRECTOR = (
    "DIRECTOR_MEDICO", "DIRECTOR_ENFERMERIA", "DIRECTOR_GENERAL",
    "DIRECTOR", "OWNER", "CO_OWNER",
)

KEYS_STAFF_DISCIPLINA = (
    "OWNER", "CO_OWNER",
    "DIRECTOR_GENERAL", "DIRECTOR_DISCIPLINA", "DIRECTOR_ADMINISTRATIVO",
    "DIRECTOR_RRHH", "DIRECTOR",
    "JEFE_DEPARTAMENTO", "ENCARGADO_AREA", "STAFF_SERVIDOR",
)


def member_medico_basico(member: discord.Member) -> bool:
    return member_tiene_alguna_key(member, *KEYS_MEDICO_BASICO)


def member_medico_avanzado(member: discord.Member) -> bool:
    return member_tiene_alguna_key(member, *KEYS_MEDICO_AVANZADO)


def member_medico_director(member: discord.Member) -> bool:
    return member_tiene_alguna_key(member, *KEYS_MEDICO_DIRECTOR)


def member_staff_disciplina(member: discord.Member) -> bool:
    """Jefes/encargados de staff del servidor o alguna dirección."""
    if member_tiene_alguna_key(member, *KEYS_STAFF_DISCIPLINA):
        return True
    nombres = {(r.name or "").lower() for r in member.roles}
    for n in nombres:
        if any(x in n for x in (
            "head staff", "jefe staff", "encargado staff", "director",
            "owner", "co-owner", "disciplina", "rrhh", "jefe de",
        )):
            return True
    return False


def require_medico(nivel: str = "basico"):
    """Decorador: nivel = basico | avanzado | director."""
    mapa = {
        "basico": KEYS_MEDICO_BASICO,
        "avanzado": KEYS_MEDICO_AVANZADO,
        "director": KEYS_MEDICO_DIRECTOR,
    }
    keys = mapa.get(nivel, KEYS_MEDICO_BASICO)
    return require_key(*keys)
