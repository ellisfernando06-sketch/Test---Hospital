# -*- coding: utf-8 -*-
"""
Autoridades:
  · Fundador del Hospital
  · Co-Fundador · Gobernanza
  · Co-Fundador · Interinstitucional
  · Co-Fundador · Calidad

Elimina / no usa el rol «Gerente de Fundación» (CO_OWNER legado).
"""
from __future__ import annotations

from typing import Dict, List, Tuple

import discord
from discord.ext import commands

ROLES_AUTORIDAD: Dict[str, Tuple[str, str]] = {
    "FUNDADOR_OWNER": ("👑 Fundador del Hospital", "#9B59B6"),
    "COFUNDADOR_GOBERNANZA": ("🤝 Co-Fundador · Gobernanza", "#3498DB"),
    "COFUNDADOR_INTERINSTITUCIONAL": ("🌐 Co-Fundador · Interinstitucional", "#1ABC9C"),
    "COFUNDADOR_CALIDAD": ("🏅 Co-Fundador · Calidad", "#E67E22"),
}

# Nombres a eliminar del servidor si existen
ROLES_ELIMINAR_NOMBRES = (
    "gerente de fundación",
    "gerente de fundacion",
    "🤝 gerente de fundación",
    "🤝 gerente de fundacion",
    "co-owner",
    "co owner",
    "🤝 co-owner",
)

_NOMBRES_VIEJOS: Dict[str, List[str]] = {
    "FUNDADOR_OWNER": [
        "fundador y owner",
        "fundador del hospital",
        "owner",
        "👑 fundador",
        "gerente developer",
    ],
    "COFUNDADOR_GOBERNANZA": [
        "co-fundador · gobernanza",
        "cofundador gobernanza",
        "gobernanza",
    ],
    "COFUNDADOR_INTERINSTITUCIONAL": [
        "co-fundador · interinstitucional",
        "cofundador interinstitucional",
        "interinstitucional",
    ],
    "COFUNDADOR_CALIDAD": [
        "co-fundador · calidad",
        "cofundador calidad",
        "calidad y acreditación",
        "calidad y acreditacion",
    ],
}


def _hex_color(h: str) -> discord.Color:
    h = (h or "#95A5A6").lstrip("#")
    try:
        return discord.Color(int(h, 16))
    except Exception:
        return discord.Color.default()


def _parche_roles_config() -> None:
    try:
        import roles_config as rc

        kn = getattr(rc, "KEYS_NOMBRES", None)
        if isinstance(kn, dict):
            for key, (nombre, color) in ROLES_AUTORIDAD.items():
                kn[key] = (nombre, color)
            # Quitar nombre "Gerente de Fundación" del legado
            if "CO_OWNER" in kn:
                # Dejar key técnica pero sin nombre de gerente; redirigir a Gobernanza
                kn["CO_OWNER"] = kn.get(
                    "COFUNDADOR_GOBERNANZA",
                    ("🤝 Co-Fundador · Gobernanza", "#3498DB"),
                )

        jer = getattr(rc, "JERARQUIA_KEYS", None)
        if isinstance(jer, list):
            for k in ROLES_AUTORIDAD:
                if k not in jer:
                    try:
                        idx = jer.index("FUNDADOR_OWNER") + 1
                    except Exception:
                        idx = 1
                    jer.insert(idx, k)
            # No es necesario borrar CO_OWNER de jerarquía (compat), pero no se usa en UI

        sec = getattr(rc, "SECCIONES", None)
        if isinstance(sec, dict) and "autoridades" in sec:
            keys = [
                "FUNDADOR_OWNER",
                "COFUNDADOR_GOBERNANZA",
                "COFUNDADOR_INTERINSTITUCIONAL",
                "COFUNDADOR_CALIDAD",
            ]
            sec["autoridades"]["keys"] = keys
            sec["autoridades"]["nombre"] = "Autoridades"
    except Exception as e:
        print(f"[roles_cofund] config: {e}")


async def _eliminar_gerente(guild: discord.Guild) -> None:
    """Borra roles con nombre Gerente de Fundación / Co-Owner legado."""
    for role in list(guild.roles):
        if role.is_default() or role.managed:
            continue
        n = (role.name or "").lower().strip()
        if any(x in n for x in ROLES_ELIMINAR_NOMBRES):
            # No borrar si ya es un Co-Fundador nuevo
            if "co-fundador" in n or "cofundador" in n:
                continue
            try:
                await role.delete(reason="Organigrama: eliminar Gerente de Fundación / Co-Owner")
                print(f"[roles_cofund] eliminado rol legado: {role.name}")
            except Exception as e:
                print(f"[roles_cofund] no se pudo eliminar {role.name}: {e}")


async def _asegurar_roles(guild: discord.Guild) -> None:
    try:
        import roles_store
    except Exception:
        roles_store = None

    await _eliminar_gerente(guild)

    existing = {r.name.lower().strip(): r for r in guild.roles}

    for key, (nombre, color) in ROLES_AUTORIDAD.items():
        role = None
        rid = None
        if roles_store is not None:
            for fn in ("get_role_id", "get"):
                try:
                    f = getattr(roles_store, fn, None)
                    if f:
                        rid = f(guild.id, key)
                        if rid:
                            break
                except Exception:
                    rid = None
        if rid:
            role = guild.get_role(int(rid))

        if role is None:
            target = nombre.lower().strip()
            if target in existing:
                role = existing[target]
            else:
                for viejo in _NOMBRES_VIEJOS.get(key, []):
                    for rn, r in existing.items():
                        if viejo in rn and "gerente" not in rn:
                            role = r
                            break
                    if role:
                        break

        if role is None:
            try:
                role = await guild.create_role(
                    name=nombre,
                    color=_hex_color(color),
                    reason="Organigrama autoridades Hospital General",
                    hoist=False,
                    mentionable=False,
                )
                print(f"[roles_cofund] creado {nombre}")
            except Exception as e:
                print(f"[roles_cofund] create {key}: {e}")
                continue
        else:
            if role.name != nombre and not role.managed and not role.is_default():
                try:
                    await role.edit(name=nombre, reason="Renombre autoridades")
                except Exception as e:
                    print(f"[roles_cofund] rename {key}: {e}")

        if roles_store is not None and role:
            for fn in ("set_role_id", "set", "save_role"):
                try:
                    f = getattr(roles_store, fn, None)
                    if f:
                        f(guild.id, key, role.id)
                        break
                except Exception:
                    pass


def member_es_fundador(m: discord.Member) -> bool:
    if m.guild and m.id == m.guild.owner_id:
        return True
    try:
        import permisos

        return bool(permisos.member_tiene_alguna_key(m, "FUNDADOR_OWNER", "OWNER"))
    except Exception:
        return False


def member_es_cofundador(m: discord.Member, zona: str | None = None) -> bool:
    keys_map = {
        "gobernanza": ("COFUNDADOR_GOBERNANZA",),
        "interinstitucional": ("COFUNDADOR_INTERINSTITUCIONAL",),
        "calidad": ("COFUNDADOR_CALIDAD",),
    }
    try:
        import permisos

        if zona and zona in keys_map:
            return bool(permisos.member_tiene_alguna_key(m, *keys_map[zona]))
        return bool(
            permisos.member_tiene_alguna_key(
                m,
                "COFUNDADOR_GOBERNANZA",
                "COFUNDADOR_INTERINSTITUCIONAL",
                "COFUNDADOR_CALIDAD",
            )
        )
    except Exception:
        return False


def registrar(bot: commands.Bot) -> None:
    _parche_roles_config()

    @bot.listen("on_ready")
    async def _roles_cofund_ready():
        if getattr(bot, "_cofund_roles_done", False):
            return
        bot._cofund_roles_done = True  # type: ignore
        for g in bot.guilds:
            try:
                await _asegurar_roles(g)
            except Exception as e:
                print(f"[roles_cofund] guild: {e}")

    print("[roles_cofund] OK — sin Gerente de Fundación; 3 Co-Fundadores")
