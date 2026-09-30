# -*- coding: utf-8 -*-
"""permisos.py — keys organigrama + alias legado."""
from __future__ import annotations
from typing import List, Sequence, Set, Tuple
import discord
from discord import app_commands
import roles_config
import roles_store

_ALIAS_KEYS = {
    "OWNER": "FUNDADOR_OWNER",
    "GERENTE_DEVELOPER": "FUNDADOR_OWNER",
    "DIRECTOR_GENERAL": "DIR_GENERAL",
    "DIRECTOR_MEDICO": "DIR_MEDICO",
    "DIRECTOR_ENFERMERIA": "DIR_ENFERMERIA",
    "DIRECTOR_RRHH": "DIR_RRHH",
    "DIRECTOR_DOCENCIA": "DIR_DOCENCIA",
    "DIRECTOR_LOGISTICA": "DIR_LOGISTICA",
    "PASANTE": "INTERNO",
}

_ALIAS_NOMBRES = {
    "FUNDADOR_OWNER": ("fundador y owner", "fundador", "owner", "gerente developer", "🛠️ gerente developer", "👑 fundador y owner"),
    "CO_OWNER": ("co-owner", "co owner", "🤝 co-owner"),
    "DIR_GENERAL": ("director general",),
    "DIR_MEDICO": ("director médico", "director medico"),
    "DIR_ENFERMERIA": ("director de enfermería", "director de enfermeria"),
    "DIR_RRHH": ("director de rrhh",),
    "DIR_DOCENCIA": ("director de docencia", "director de docencia e investigación"),
    "DIR_LOGISTICA": ("director de logística", "director de logistica"),
    "PREFECTO_OPERACIONES": ("prefecto de operaciones", "prefecto"),
    "RESIDENTE": ("residente",),
    "INTERNO": ("interno", "practicante", "pasante"),
}

KEYS_AUTORIDADES = ("FUNDADOR_OWNER", "CO_OWNER")
KEYS_STAFF_SERVER = ("ADMIN_JEFE", "ADMIN", "ADMIN_PRUEBA")
KEYS_GERENCIA = ("PREFECTO_OPERACIONES", "DIR_GENERAL", "DIR_MEDICO", "DIR_ENFERMERIA", "DIR_RRHH", "DIR_DOCENCIA", "DIR_LOGISTICA")
KEYS_EMITIR_CERTIFICADO = ("PREFECTO_OPERACIONES", "DIR_DOCENCIA", "FUNDADOR_OWNER", "CO_OWNER")
KEYS_FIRMAR_ENCARGADO = KEYS_GERENCIA + KEYS_AUTORIDADES + (
    "JEFE_DEPARTAMENTO", "JEFE_SERVICIO", "JEFE_SERVICIO_ENF", "JEFE_GUIA_RESIDENTES",
    "MEDICO_ESPECIALISTA", "MEDICO_GENERAL", "ENFERMERO_ESPECIALISTA", "ENFERMERO_GENERAL",
)
try:
    KEYS_APROBAR_INACTIVIDAD = tuple(roles_config.KEYS_APROBAR_INACTIVIDAD)
except Exception:
    KEYS_APROBAR_INACTIVIDAD = KEYS_AUTORIDADES + ("PREFECTO_OPERACIONES", "DIR_GENERAL", "DIR_RRHH")

KEYS_MEDICO = (
    "INTERNO", "RESIDENTE", "JEFE_GUIA_RESIDENTES", "MEDICO_GENERAL", "MEDICO_ESPECIALISTA", "JEFE_SERVICIO", "DIR_MEDICO",
    "AUXILIAR_ENFERMERIA", "ENFERMERO_FORMACION", "GUIA_AUXILIARES_ENF", "ENFERMERO_GENERAL", "ENFERMERO_ESPECIALISTA", "JEFE_SERVICIO_ENF", "DIR_ENFERMERIA",
    "TECNICO_SALUD", "PARAMEDICO", "PREFECTO_OPERACIONES", "DIR_GENERAL",
) + KEYS_AUTORIDADES

KEYS_DOCENCIA_STAFF = ("JEFE_GUIA_RESIDENTES", "GUIA_AUXILIARES_ENF", "JEFE_DEPARTAMENTO", "JEFE_SERVICIO", "DIR_DOCENCIA", "PREFECTO_OPERACIONES") + KEYS_AUTORIDADES
KEYS_RRHH = ("DIR_RRHH", "DIR_GENERAL", "PREFECTO_OPERACIONES") + KEYS_AUTORIDADES
KEYS_DESPIDOS = KEYS_RRHH

class SinPermiso(app_commands.AppCommandError):
    def __init__(self, keys_requeridas: List[str]):
        self.keys_requeridas = keys_requeridas
        nombres = [roles_config.nombre_key(_normalizar_key(k)) for k in keys_requeridas]
        super().__init__("Se requiere: " + ", ".join(nombres))

def _normalizar_key(key: str) -> str:
    return _ALIAS_KEYS.get(key, key)

def _nombres_para_key(key: str) -> Set[str]:
    key = _normalizar_key(key)
    out: Set[str] = set()
    oficial = roles_config.KEYS_NOMBRES.get(key)
    if oficial:
        out.add(oficial[0].lower().strip())
    for alt in _ALIAS_NOMBRES.get(key, ()): 
        out.add(alt.lower().strip())
    return out

def nivel_de_key(key: str) -> int:
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
    nombres = {(r.name or "").lower().strip() for r in member.roles}
    out, seen = [], set()
    for key, rid in roles_store.todas_las_keys().items():
        nk = _normalizar_key(key)
        if rid in ids and nk not in seen:
            out.append(nk); seen.add(nk)
    for key in list(getattr(roles_config, "JERARQUIA_KEYS", [])) + ["INACTIVIDAD_JUSTIFICADA"]:
        if key in seen: continue
        for nom in _nombres_para_key(key):
            if nom in nombres:
                out.append(key); seen.add(key); break
    return out

def member_tiene_key(member: discord.Member, key: str) -> bool:
    key_n = _normalizar_key(key)
    candidates = [key, key_n]
    for old, newk in _ALIAS_KEYS.items():
        if key_n == newk: candidates.append(old)
    ids_member = {r.id for r in member.roles}
    seen = set()
    for k in candidates:
        if k in seen: continue
        seen.add(k)
        rid = roles_store.obtener_id_key(k)
        if rid and rid in ids_member: return True
    nombres = {(r.name or "").lower().strip() for r in member.roles}
    for nom in _nombres_para_key(key_n):
        if nom in nombres: return True
    return False

def member_tiene_alguna_key(member: discord.Member, *keys: str) -> bool:
    for k in keys:
        if k == "DIRECTOR" or _normalizar_key(k) == "DIRECTOR":
            if any(member_tiene_key(member, dk) for dk in KEYS_GERENCIA):
                return True
            continue
        if member_tiene_key(member, k): return True
    return False

def nivel_del_member(member: discord.Member) -> int:
    keys = [k for k in keys_del_member(member) if k != "INACTIVIDAD_JUSTIFICADA"]
    if not keys:
        return 0 if member.guild_permissions.administrator else 999
    return min(nivel_de_key(k) for k in keys)

def puede_actuar_sobre(emisor: discord.Member, objetivo: discord.Member) -> bool:
    if member_tiene_key(emisor, "FUNDADOR_OWNER"): return True
    return nivel_del_member(emisor) < nivel_del_member(objetivo)

def member_es_autoridad(member: discord.Member) -> bool:
    if member_tiene_alguna_key(member, *KEYS_AUTORIDADES, "OWNER"): return True
    if not roles_store.todas_las_keys() and member.guild_permissions.administrator: return True
    return False

def member_es_staff_server(member: discord.Member) -> bool:
    return member_tiene_alguna_key(member, *KEYS_STAFF_SERVER, *KEYS_AUTORIDADES)

def member_es_gerencia(member: discord.Member) -> bool:
    return member_tiene_alguna_key(member, *KEYS_GERENCIA, *KEYS_AUTORIDADES)

def member_puede_emitir_certificado(member: discord.Member) -> bool:
    return member_tiene_alguna_key(member, *KEYS_EMITIR_CERTIFICADO)

def member_puede_firmar_encargado(member: discord.Member) -> bool:
    return member_tiene_alguna_key(member, *KEYS_FIRMAR_ENCARGADO)

def member_puede_aprobar_inactividad(member: discord.Member) -> bool:
    return member_tiene_alguna_key(member, *KEYS_APROBAR_INACTIVIDAD)

def require_key(*keys: str):
    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            raise SinPermiso(list(keys))
        u = interaction.user
        if member_tiene_key(u, "FUNDADOR_OWNER") or member_tiene_key(u, "OWNER"): return True
        if member_tiene_alguna_key(u, *keys): return True
        if not roles_store.todas_las_keys() and u.guild_permissions.administrator: return True
        raise SinPermiso(list(keys))
    return app_commands.check(predicate)

def require_nivel(nivel_maximo: int):
    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            raise SinPermiso([f"nivel<={nivel_maximo}"])
        if nivel_del_member(interaction.user) <= nivel_maximo: return True
        raise SinPermiso([f"nivel<={nivel_maximo}"])
    return app_commands.check(predicate)

def require_autoridad():
    return require_key("FUNDADOR_OWNER", "CO_OWNER", "OWNER")

def member_staff_server(member: discord.Member) -> bool:
    return member_es_staff_server(member)

def member_gerencia(member: discord.Member) -> bool:
    return member_es_gerencia(member)
