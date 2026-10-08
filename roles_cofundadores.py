# -*- coding: utf-8 -*-
"""
Roles de autoridades del Hospital General (detectar / renombrar / crear).
Keys nuevas; no borra keys antiguas (CO_OWNER sigue existiendo como alias).
"""
from __future__ import annotations

from typing import Dict, List, Tuple

import discord
from discord.ext import commands

# key → (nombre Discord, color hex)
ROLES_AUTORIDAD: Dict[str, Tuple[str, str]] = {
    "FUNDADOR_OWNER": ("👑 Fundador del Hospital", "#9B59B6"),  # morado mando
    "COFUNDADOR_GOBERNANZA": ("🤝 Co-Fundador · Gobernanza", "#3498DB"),  # azul
    "COFUNDADOR_INTERINSTITUCIONAL": ("🌐 Co-Fundador · Interinstitucional", "#1ABC9C"),  # verde azulado
    "COFUNDADOR_CALIDAD": ("🏅 Co-Fundador · Calidad", "#E67E22"),  # coral/naranja
}

# Alias legados: Gerente de Fundación / Co-Owner → se trata como Gobernanza si no hay key nueva
LEGACY_CO_OWNER = "CO_OWNER"

_NOMBRES_VIEJOS: Dict[str, List[str]] = {
    "FUNDADOR_OWNER": [
        "fundador y owner",
        "fundador del hospital",
        "owner",
        "👑 fundador",
        "gerente developer",
    ],
    "COFUNDADOR_GOBERNANZA": [
        "co-owner",
        "co owner",
        "gerente de fundación",
        "gerente de fundacion",
        "🤝 co-owner",
        "🤝 gerente",
        "co-fundador · gobernanza",
        "cofundador gobernanza",
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
        if not isinstance(kn, dict):
            return
        for key, (nombre, color) in ROLES_AUTORIDAD.items():
            kn[key] = (nombre, color)
        # legado: Co-Owner visible como Gerente / alias gobernanza
        if "CO_OWNER" in kn:
            kn["CO_OWNER"] = ("🤝 Gerente de Fundación", "#3498DB")
        # jerarquía: insertar co-fundadores tras fundador
        jer = getattr(rc, "JERARQUIA_KEYS", None)
        if isinstance(jer, list):
            for k in (
                "COFUNDADOR_GOBERNANZA",
                "COFUNDADOR_INTERINSTITUCIONAL",
                "COFUNDADOR_CALIDAD",
            ):
                if k not in jer:
                    try:
                        idx = jer.index("CO_OWNER") + 1 if "CO_OWNER" in jer else 1
                    except Exception:
                        idx = 1
                    jer.insert(idx, k)
        sec = getattr(rc, "SECCIONES", None)
        if isinstance(sec, dict) and "autoridades" in sec:
            keys = list(sec["autoridades"].get("keys") or [])
            for k in ROLES_AUTORIDAD:
                if k not in keys:
                    keys.append(k)
            sec["autoridades"]["keys"] = keys
    except Exception as e:
        print(f"[roles_cofund] config: {e}")


async def _asegurar_roles(guild: discord.Guild) -> None:
    try:
        import roles_store
    except Exception:
        roles_store = None

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
                        if viejo in rn:
                            role = r
                            break
                    if role:
                        break

        # CO_OWNER legado → enlazar a Gobernanza si no hay rol propio aún
        if role is None and key == "COFUNDADOR_GOBERNANZA" and roles_store:
            try:
                rid2 = roles_store.get_role_id(guild.id, "CO_OWNER")
                if rid2:
                    role = guild.get_role(int(rid2))
            except Exception:
                pass

        if role is None:
            try:
                role = await guild.create_role(
                    name=nombre,
                    color=_hex_color(color),
                    reason="Organigrama: Co-Fundadores / Fundador",
                    hoist=False,
                    mentionable=False,
                )
                print(f"[roles_cofund] creado {nombre} en {guild.name}")
            except Exception as e:
                print(f"[roles_cofund] create {key}: {e}")
                continue
        else:
            if role.name != nombre and not role.managed and not role.is_default():
                try:
                    await role.edit(name=nombre, reason="Renombre organigrama autoridades")
                    print(f"[roles_cofund] renombrado → {nombre}")
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
                    try:
                        f(guild.id, key, role.id)  # type: ignore
                        break
                    except Exception:
                        pass


def member_es_fundador(m: discord.Member) -> bool:
    if m.guild and m.id == m.guild.owner_id:
        return True
    try:
        import permisos

        return bool(
            permisos.member_tiene_alguna_key(m, "FUNDADOR_OWNER", "OWNER")
        )
    except Exception:
        return False


def member_es_cofundador(m: discord.Member, zona: str | None = None) -> bool:
    keys = {
        "gobernanza": ("COFUNDADOR_GOBERNANZA", "CO_OWNER"),
        "interinstitucional": ("COFUNDADOR_INTERINSTITUCIONAL",),
        "calidad": ("COFUNDADOR_CALIDAD",),
    }
    try:
        import permisos

        if zona and zona in keys:
            return bool(permisos.member_tiene_alguna_key(m, *keys[zona]))
        return bool(
            permisos.member_tiene_alguna_key(
                m,
                "COFUNDADOR_GOBERNANZA",
                "COFUNDADOR_INTERINSTITUCIONAL",
                "COFUNDADOR_CALIDAD",
                "CO_OWNER",
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

    print("[roles_cofund] OK — Fundador + 3 Co-Fundadores")
