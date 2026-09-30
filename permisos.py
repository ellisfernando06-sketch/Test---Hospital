# -*- coding: utf-8 -*-
"""
permisos.py — Sistema de permisos del hospital.
================================================
Fuente de verdad: roles_config (organigrama oficial).

- Keys nuevas (FUNDADOR_OWNER, DIR_*, …) y alias antiguas (OWNER, DIRECTOR_*).
- Detección por ID en roles.json y, si falta, por nombre del rol en Discord.
- Grupos de permiso (autoridades, gerencia, certificados, inactividad, …).
- Decoradores require_key / require_nivel para slash commands.
"""
from __future__ import annotations

from typing import Iterable, List, Optional, Sequence, Set, Tuple

import discord
from discord import app_commands

import roles_config
import roles_store

# ── Alias keys antiguas → organigrama nuevo ───────────────────────────────
_ALIAS_KEYS = {
    "OWNER": "FUNDADOR_OWNER",
    "GERENTE_DEVELOPER": "FUNDADOR_OWNER",
    "DIRECTOR_GENERAL": "DIR_GENERAL",
    "DIRECTOR_MEDICO": "DIR_MEDICO",
    "DIRECTOR_RRHH": "DIR_RRHH",
    "DIRECTOR_DOCENCIA": "DIR_DOCENCIA",
    "DIRECTOR_LOGISTICA": "DIR_LOGISTICA",
    "DIRECTOR_ENFERMERIA": "DIR_MEDICO",  # mapeo razonable de legado
    "PASANTE": "INTERNO",
}

# Nombres alternativos que se aceptan al buscar por rol en Discord
_ALIAS_NOMBRES: dict[str, Tuple[str, ...]] = {
    "FUNDADOR_OWNER": (
        "fundador y owner", "fundador", "owner",
        "gerente developer", "🛠️ gerente developer", "👑 fundador y owner",
    ),
    "CO_OWNER": ("co-owner", "co owner", "🤝 co-owner"),
    "DIR_GENERAL": ("director general", "🖥️ director general"),
    "DIR_MEDICO": ("director médico", "director medico", "🩺 director médico"),
    "DIR_RRHH": ("director de rrhh", "director de recursos humanos"),
    "DIR_DOCENCIA": (
        "director de docencia",
        "director de investigación y docencia",
        "director de docencia e investigación",
    ),
    "DIR_LOGISTICA": ("director de logística", "director de logistica"),
    "PREFECTO_OPERACIONES": ("prefecto de operaciones", "prefecto"),
    "RESIDENTE": ("residente", "📚 residente"),
    "INTERNO": ("interno", "practicante", "interno / practicante", "pasante"),
}


class SinPermiso(app_commands.AppCommandError):
    def __init__(self, keys_requeridas: List[str]):
        self.keys_requeridas = keys_requeridas
        nombres = [roles_config.nombre_key(_normalizar_key(k)) for k in keys_requeridas]
        super().__init__(
            "Se requiere uno de estos cargos: " + ", ".join(nombres)
        )


def _normalizar_key(key: str) -> str:
    return _ALIAS_KEYS.get(key, key)


def _nombres_para_key(key: str) -> Set[str]:
    """Nombres de Discord que equivalen a esta key."""
    key = _normalizar_key(key)
    out: Set[str] = set()
    oficial = roles_config.KEYS_NOMBRES.get(key)
    if oficial:
        out.add(oficial[0].lower().strip())
    for alt in _ALIAS_NOMBRES.get(key, ()):
        out.add(alt.lower().strip())
    # También el nombre de la key antigua si aplica
    for old, new in _ALIAS_KEYS.items():
        if new == key:
            try:
                import config as _cfg
                tup = getattr(_cfg, "KEYS_NOMBRES", {}).get(old)
                if tup:
                    out.add(str(tup[0]).lower().strip())
            except Exception:
                pass
    return out


def nivel_de_key(key: str) -> int:
    """Menor índice = más alto en la jerarquía."""
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
    """Todas las keys del organigrama que tiene el miembro."""
    ids = {r.id for r in member.roles}
    nombres = {(r.name or "").lower().strip() for r in member.roles}
    out: List[str] = []
    seen: Set[str] = set()

    # 1) Por ID guardado
    for key, rid in roles_store.todas_las_keys().items():
        nk = _normalizar_key(key)
        if rid in ids and nk not in seen:
            out.append(nk)
            seen.add(nk)

    # 2) Por nombre oficial / alias (si aún no está en store)
    for key in roles_config.JERARQUIA_KEYS:
        if key in seen:
            continue
        for nom in _nombres_para_key(key):
            if nom in nombres:
                out.append(key)
                seen.add(key)
                break

    # INACTIVIDAD no es jerarquía de mando, pero puede listarse
    if "INACTIVIDAD_JUSTIFICADA" not in seen:
        for nom in _nombres_para_key("INACTIVIDAD_JUSTIFICADA"):
            if nom in nombres:
                out.append("INACTIVIDAD_JUSTIFICADA")
                break

    return out


def member_tiene_key(member: discord.Member, key: str) -> bool:
    """True si el miembro tiene esa key (ID en store o nombre del rol)."""
    key_n = _normalizar_key(key)
    candidates = [key, key_n]
    for old, newk in _ALIAS_KEYS.items():
        if key_n == newk:
            candidates.append(old)

    ids_member = {r.id for r in member.roles}
    seen: Set[str] = set()
    for k in candidates:
        if k in seen:
            continue
        seen.add(k)
        rid = roles_store.obtener_id_key(k)
        if rid and rid in ids_member:
            return True

    # Fallback por nombre
    nombres = {(r.name or "").lower().strip() for r in member.roles}
    for nom in _nombres_para_key(key_n):
        if nom in nombres:
            return True
    return False


def member_tiene_alguna_key(member: discord.Member, *keys: str) -> bool:
    for k in keys:
        if k in ("DIRECTOR",) or _normalizar_key(k) == "DIRECTOR":
            dirs = (
                "DIR_GENERAL", "DIR_MEDICO", "DIR_RRHH", "DIR_DOCENCIA", "DIR_LOGISTICA",
                "DIRECTOR_GENERAL", "DIRECTOR_MEDICO", "DIRECTOR_RRHH",
                "DIRECTOR_DOCENCIA", "DIRECTOR_LOGISTICA",
            )
            if any(member_tiene_key(member, dk) for dk in dirs):
                return True
            continue
        if member_tiene_key(member, k):
            return True
    return False


def member_tiene_todas_keys(member: discord.Member, *keys: str) -> bool:
    return all(member_tiene_key(member, k) for k in keys)


def nivel_del_member(member: discord.Member) -> int:
    keys = [k for k in keys_del_member(member) if k != "INACTIVIDAD_JUSTIFICADA"]
    if not keys:
        # Admin de Discord sin key aún → tratar como autoridad temporal solo para setup
        if member.guild_permissions.administrator:
            return 0
        return 999
    return min(nivel_de_key(k) for k in keys)


def puede_actuar_sobre(emisor: discord.Member, objetivo: discord.Member) -> bool:
    """El emisor solo puede actuar sobre alguien de nivel inferior (o igual solo si es Fundador)."""
    if member_tiene_key(emisor, "FUNDADOR_OWNER"):
        return True
    return nivel_del_member(emisor) < nivel_del_member(objetivo)


def member_es_autoridad(member: discord.Member) -> bool:
    if member_tiene_alguna_key(member, *KEYS_AUTORIDADES, "OWNER"):
        return True
    # Si aún no hay keys en el store, permitir administrador para bootstrap
    if not roles_store.todas_las_keys() and member.guild_permissions.administrator:
        return True
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


def nombres_keys_requeridas(keys: Sequence[str]) -> str:
    return ", ".join(roles_config.nombre_key(_normalizar_key(k)) for k in keys)


def require_key(*keys: str):
    """Decorador: el usuario debe tener al menos una de las keys."""
    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            raise SinPermiso(list(keys))
        # Autoridades siempre pasan si se pide cualquier key de gerencia/staff
        if member_es_autoridad(interaction.user) and any(
            _normalizar_key(k) in (
                set(KEYS_AUTORIDADES)
                | set(KEYS_STAFF_SERVER)
                | set(KEYS_GERENCIA)
                | {"OWNER", "FUNDADOR_OWNER", "CO_OWNER"}
            )
            or True
            for k in keys
        ):
            # Solo auto-bypass si alguna key pedida es de alto nivel o es autoridad y se pidió OWNER
            if member_tiene_alguna_key(interaction.user, *keys):
                return True
            # Fundador siempre puede
            if member_tiene_key(interaction.user, "FUNDADOR_OWNER") or member_tiene_key(
                interaction.user, "OWNER"
            ):
                return True
        if member_tiene_alguna_key(interaction.user, *keys):
            return True
        # Bootstrap: admin sin keys configuradas
        if not roles_store.todas_las_keys() and interaction.user.guild_permissions.administrator:
            return True
        raise SinPermiso(list(keys))
    return app_commands.check(predicate)


def require_nivel(nivel_maximo: int):
    """Decorador: nivel del miembro debe ser <= nivel_maximo (0 = más alto)."""
    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            raise SinPermiso([f"nivel<={nivel_maximo}"])
        if nivel_del_member(interaction.user) <= nivel_maximo:
            return True
        raise SinPermiso([f"nivel<={nivel_maximo}"])
    return app_commands.check(predicate)


def require_autoridad():
    return require_key("FUNDADOR_OWNER", "CO_OWNER", "OWNER")


# ── Grupos del organigrama ────────────────────────────────────────────────

KEYS_AUTORIDADES: Tuple[str, ...] = ("FUNDADOR_OWNER", "CO_OWNER")

KEYS_STAFF_SERVER: Tuple[str, ...] = ("ADMIN_JEFE", "ADMIN", "ADMIN_PRUEBA")

KEYS_GERENCIA: Tuple[str, ...] = (
    "PREFECTO_OPERACIONES",
    "DIR_GENERAL",
    "DIR_MEDICO",
    "DIR_RRHH",
    "DIR_DOCENCIA",
    "DIR_LOGISTICA",
)

KEYS_EMITIR_CERTIFICADO: Tuple[str, ...] = (
    "PREFECTO_OPERACIONES",
    "DIR_DOCENCIA",
    "FUNDADOR_OWNER",
    "CO_OWNER",
)

KEYS_FIRMAR_ENCARGADO: Tuple[str, ...] = (
    "JEFE_DEPARTAMENTO",
    "JEFE_SERVICIO",
    "JEFE_GUIA_RESIDENTES",
    "MEDICO_ESPECIALISTA",
    "MEDICO_GENERAL",
    "DIR_MEDICO",
    "DIR_DOCENCIA",
    "DIR_LOGISTICA",
    "DIR_RRHH",
    "DIR_GENERAL",
    "PREFECTO_OPERACIONES",
    "FUNDADOR_OWNER",
    "CO_OWNER",
)

try:
    KEYS_APROBAR_INACTIVIDAD: Tuple[str, ...] = tuple(roles_config.KEYS_APROBAR_INACTIVIDAD)
except Exception:
    KEYS_APROBAR_INACTIVIDAD = (
        "FUNDADOR_OWNER",
        "CO_OWNER",
        "PREFECTO_OPERACIONES",
        "DIR_GENERAL",
        "DIR_RRHH",
    )

KEYS_MEDICO: Tuple[str, ...] = (
    "INTERNO",
    "RESIDENTE",
    "JEFE_GUIA_RESIDENTES",
    "MEDICO_GENERAL",
    "MEDICO_ESPECIALISTA",
    "JEFE_SERVICIO",
    "DIR_MEDICO",
    "PREFECTO_OPERACIONES",
    "DIR_GENERAL",
) + KEYS_AUTORIDADES

KEYS_DOCENCIA_STAFF: Tuple[str, ...] = (
    "JEFE_GUIA_RESIDENTES",
    "JEFE_DEPARTAMENTO",
    "JEFE_SERVICIO",
    "DIR_DOCENCIA",
    "PREFECTO_OPERACIONES",
) + KEYS_AUTORIDADES

KEYS_RRHH: Tuple[str, ...] = ("DIR_RRHH", "DIR_GENERAL", "PREFECTO_OPERACIONES") + KEYS_AUTORIDADES

KEYS_DESPIDOS: Tuple[str, ...] = KEYS_RRHH

# Aliases de funciones antiguas (no romper imports)
def member_staff_server(member: discord.Member) -> bool:
    return member_es_staff_server(member)


def member_gerencia(member: discord.Member) -> bool:
    return member_es_gerencia(member)
