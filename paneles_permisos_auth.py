# -*- coding: utf-8 -*-
"""Permisos de paneles de autoridades."""
from __future__ import annotations

from typing import Optional, Tuple

import discord

from paneles_autoridades_config import (
    KEY_CALIDAD,
    KEY_FUNDADOR,
    KEY_GOBERNANZA,
    KEY_INTER,
)

try:
    import permisos
except Exception:
    permisos = None

try:
    import roles_config
except Exception:
    roles_config = None


def _tiene(m: discord.Member, *keys: str) -> bool:
    if m.guild and m.id == m.guild.owner_id and KEY_FUNDADOR in keys:
        return True
    if permisos is None:
        return False
    try:
        return bool(permisos.member_tiene_alguna_key(m, *keys))
    except Exception:
        return False


def es_fundador(m: discord.Member) -> bool:
    return _tiene(m, KEY_FUNDADOR, "OWNER")


def zona_de(m: discord.Member) -> Optional[str]:
    if _tiene(m, KEY_GOBERNANZA):
        return "gobernanza"
    if _tiene(m, KEY_INTER):
        return "interinstitucional"
    if _tiene(m, KEY_CALIDAD):
        return "calidad"
    return None


def panel_de(m: discord.Member) -> Optional[str]:
    """Rol más alto → panel."""
    if es_fundador(m):
        return "fundador"
    return zona_de(m)


def puede_usar_panel(m: discord.Member, panel: str) -> bool:
    if panel == "fundador":
        return es_fundador(m)
    if es_fundador(m):
        return True  # fundador puede mirar zonas
    z = zona_de(m)
    if z == panel:
        return True
    # delegación
    try:
        from paneles_store import tiene_delegacion

        if tiene_delegacion(m.guild.id, m.id, panel) or tiene_delegacion(
            m.guild.id, m.id, "*"
        ):
            return True
    except Exception:
        pass
    return False


def _nivel(key: str) -> int:
    if roles_config is None:
        return 999
    try:
        return int(roles_config.nivel_de_key(key))
    except Exception:
        jer = getattr(roles_config, "JERARQUIA_KEYS", []) or []
        try:
            return jer.index(key)
        except ValueError:
            return 999


def keys_del_miembro(m: discord.Member) -> list:
    out = []
    if roles_config is None or permisos is None:
        return out
    jer = getattr(roles_config, "JERARQUIA_KEYS", []) or []
    for k in jer:
        try:
            if permisos.member_tiene_alguna_key(m, k):
                out.append(k)
        except Exception:
            pass
    return out


def nivel_miembro(m: discord.Member) -> int:
    keys = keys_del_miembro(m)
    if not keys:
        return 999
    return min(_nivel(k) for k in keys)


def puede_actuar_sobre(actor: discord.Member, objetivo: discord.Member) -> Tuple[bool, str]:
    """No actuar sobre igual o superior. Fundador sí sobre Co-Fundadores."""
    if actor.id == objetivo.id:
        return False, "No puedes actuar sobre ti mismo."
    if es_fundador(objetivo) and not es_fundador(actor):
        return False, "No puedes actuar sobre el Fundador."
    # Co-Fundadores entre sí
    za, zo = zona_de(actor), zona_de(objetivo)
    if zo and za and zo != za and not es_fundador(actor):
        # otro cofundador
        if zona_de(objetivo):
            return False, "No puedes actuar sobre otro Co-Fundador."
    if zona_de(objetivo) and not es_fundador(actor):
        return False, "No puedes actuar sobre un Co-Fundador."
    na, no = nivel_miembro(actor), nivel_miembro(objetivo)
    if no <= na and not es_fundador(actor):
        return False, "Solo puedes actuar sobre personas **por debajo** de tu jerarquía."
    return True, ""
