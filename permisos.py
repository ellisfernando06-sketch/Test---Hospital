# -*- coding: utf-8 -*-
"""
permisos.py — Sistema de keys / jerarquía según organigrama oficial.
Fuente de verdad: roles_config.py
"""
from __future__ import annotations

from typing import List, Optional

import discord
from discord import app_commands

import roles_config
import roles_store

# Compatibilidad temporal: keys antiguas → nuevas
_ALIAS_KEYS = {
    "OWNER": "FUNDADOR_OWNER",
    "DIRECTOR_GENERAL": "DIR_GENERAL",
    "DIRECTOR_MEDICO": "DIR_MEDICO",
    "DIRECTOR_RRHH": "DIR_RRHH",
    "DIRECTOR_DOCENCIA": "DIR_DOCENCIA",
    "DIRECTOR_LOGISTICA": "DIR_LOGISTICA",
    "PASANTE": "INTERNO",
}


class SinPermiso(app_commands.AppCommandError):
    def __init__(self, keys_requeridas: List[str]):
        self.keys_requeridas = keys_requeridas
        super().__init__(f"Se requiere una de: {', '.join(keys_requeridas)}")


def _normalizar_key(key: str) -> str:
    return _ALIAS_KEYS.get(key, key)


def nivel_de_key(key: str) -> int:
    """Nivel numérico (menor índice = más alto en la jerarquía)."""
    key = _normalizar_key(key)
    try:
        return roles_config.JERARQUIA_KEYS.index(key)
    except ValueError:
        return 999


def nivel_de_rol(role_id: int) -> int:
    for key, rid in roles_store.todas_las_keys().items():
        if rid == role_id:
            return nivel_de_key(key)
    return 999


def keys_del_member(member: discord.Member) -> List[str]:
    ids = {r.id for r in member.roles}
    out = []
    for key, rid in roles_store.todas_las_keys().items():
        if rid in ids:
            out.append(key)
    return out


def member_tiene_key(member: discord.Member, key: str) -> bool:
    key = _normalizar_key(key)
    rid = roles_store.obtener_id_key(key)
    if not rid:
        return False
    return any(r.id == rid for r in member.roles)


def member_tiene_alguna_key(member: discord.Member, *keys: str) -> bool:
    for k in keys:
        k = _normalizar_key(k)
        # "DIRECTOR" genérico → cualquier DIR_*
        if k == "DIRECTOR":
            for dk in ("DIR_GENERAL", "DIR_MEDICO", "DIR_RRHH", "DIR_DOCENCIA", "DIR_LOGISTICA"):
                if member_tiene_key(member, dk):
                    return True
        elif member_tiene_key(member, k):
            return True
    return False


def nivel_del_member(member: discord.Member) -> int:
    keys = keys_del_member(member)
    if not keys:
        return 999
    return min(nivel_de_key(k) for k in keys)


def puede_actuar_sobre(emisor: discord.Member, objetivo: discord.Member) -> bool:
    if member_tiene_key(emisor, "FUNDADOR_OWNER"):
        return True
    return nivel_del_member(emisor) < nivel_del_member(objetivo)  # menor índice = más alto


def require_key(*keys: str):
    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            raise SinPermiso(list(keys))
        if member_tiene_alguna_key(interaction.user, *keys):
            return True
        raise SinPermiso(list(keys))
    return app_commands.check(predicate)


# ── Grupos de keys del organigrama ────────────────────────────────────

KEYS_AUTORIDADES = ("FUNDADOR_OWNER", "CO_OWNER")

KEYS_STAFF_SERVER = ("ADMIN_JEFE", "ADMIN", "ADMIN_PRUEBA")

KEYS_GERENCIA = (
    "PREFECTO_OPERACIONES",
    "DIR_GENERAL",
    "DIR_MEDICO",
    "DIR_RRHH",
    "DIR_DOCENCIA",
    "DIR_LOGISTICA",
)

KEYS_EMITIR_CERTIFICADO = (
    "PREFECTO_OPERACIONES",
    "DIR_DOCENCIA",
    "FUNDADOR_OWNER",
    "CO_OWNER",
)

KEYS_APROBAR_INACTIVIDAD = tuple(roles_config.KEYS_APROBAR_INACTIVIDAD)

KEYS_MEDICO = (
    "INTERNO", "RESIDENTE", "JEFE_GUIA_RESIDENTES",
    "MEDICO_GENERAL", "MEDICO_ESPECIALISTA", "JEFE_SERVICIO",
    "DIR_MEDICO",
) + KEYS_GERENCIA[:2] + KEYS_AUTORIDADES  # Prefecto, DIR_GENERAL + autoridades

KEYS_DOCENCIA_STAFF = (
    "JEFE_GUIA_RESIDENTES", "JEFE_DEPARTAMENTO", "JEFE_SERVICIO",
    "DIR_DOCENCIA",
) + KEYS_AUTORIDADES + ("PREFECTO_OPERACIONES",)


def member_puede_emitir_certificado(member: discord.Member) -> bool:
    return member_tiene_alguna_key(member, *KEYS_EMITIR_CERTIFICADO)


def member_puede_firmar_encargado(member: discord.Member) -> bool:
    """Encargado de una capacitación puede firmar el primer paso."""
    return member_tiene_alguna_key(
        member,
        "JEFE_DEPARTAMENTO", "JEFE_SERVICIO", "JEFE_GUIA_RESIDENTES",
        "MEDICO_ESPECIALISTA", "MEDICO_GENERAL",
        "DIR_MEDICO", "DIR_DOCENCIA", "DIR_LOGISTICA", "DIR_RRHH", "DIR_GENERAL",
        "PREFECTO_OPERACIONES", "FUNDADOR_OWNER", "CO_OWNER",
    )


def member_staff_server(member: discord.Member) -> bool:
    return member_tiene_alguna_key(member, *KEYS_STAFF_SERVER, *KEYS_AUTORIDADES)


def member_gerencia(member: discord.Member) -> bool:
    return member_tiene_alguna_key(member, *KEYS_GERENCIA, *KEYS_AUTORIDADES)
