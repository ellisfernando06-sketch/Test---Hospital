# -*- coding: utf-8 -*-
"""
Renombra en config y en Discord (si existen):
  FUNDADOR_OWNER → 👑 Fundador del Hospital
  CO_OWNER       → 🤝 Gerente de Fundación
Las keys no cambian (permisos siguen igual).
"""
from __future__ import annotations

import discord
from discord.ext import commands

_NOMBRES = {
    "FUNDADOR_OWNER": "👑 Fundador del Hospital",
    "CO_OWNER": "🤝 Gerente de Fundación",
}

_ALIAS_EXTRA = {
    "FUNDADOR_OWNER": (
        "fundador del hospital",
        "fundador hospital",
        "fundador y owner",
        "fundador y owner",
        "owner",
        "👑 fundador del hospital",
        "👑 fundador y owner",
    ),
    "CO_OWNER": (
        "gerente de fundación",
        "gerente de fundacion",
        "co-owner",
        "co owner",
        "🤝 gerente de fundación",
        "🤝 co-owner",
    ),
}


def _parche_config() -> None:
    try:
        import roles_config as rc

        if hasattr(rc, "ROLES") and isinstance(rc.ROLES, dict):
            for key, nombre in _NOMBRES.items():
                if key in rc.ROLES:
                    old = rc.ROLES[key]
                    if isinstance(old, tuple) and len(old) >= 2:
                        rc.ROLES[key] = (nombre, old[1])
                    elif isinstance(old, dict):
                        old["nombre"] = nombre
                    else:
                        rc.ROLES[key] = nombre
                else:
                    # formato alternativo
                    pass
        # ORGANIGRAMA o similar
        for attr in ("ORGANIGRAMA", "ROLES_ORGANIGRAMA", "ROLE_NAMES"):
            d = getattr(rc, attr, None)
            if isinstance(d, dict):
                for key, nombre in _NOMBRES.items():
                    if key in d:
                        v = d[key]
                        if isinstance(v, tuple) and len(v) >= 2:
                            d[key] = (nombre, v[1])
                        elif isinstance(v, str):
                            d[key] = nombre
    except Exception as e:
        print(f"[roles_nombres] config: {e}")

    try:
        import permisos

        if hasattr(permisos, "ROLE_ALIASES") and isinstance(permisos.ROLE_ALIASES, dict):
            for key, aliases in _ALIAS_EXTRA.items():
                cur = list(permisos.ROLE_ALIASES.get(key) or [])
                for a in aliases:
                    if a not in cur:
                        cur.append(a)
                permisos.ROLE_ALIASES[key] = tuple(cur)
        # algunos módulos usan un dict KEY -> nombres
        for attr in ("KEY_ALIASES", "ALIASES", "ROLE_NAME_HINTS"):
            d = getattr(permisos, attr, None)
            if isinstance(d, dict):
                for key, aliases in _ALIAS_EXTRA.items():
                    cur = list(d.get(key) or [])
                    for a in aliases:
                        if a not in cur:
                            cur.append(a)
                    d[key] = type(d.get(key) or ())(cur) if isinstance(d.get(key), tuple) else cur
    except Exception as e:
        print(f"[roles_nombres] permisos: {e}")


async def _renombrar_en_guild(guild: discord.Guild) -> None:
    try:
        import roles_store
    except Exception:
        roles_store = None

    for key, nuevo in _NOMBRES.items():
        role = None
        rid = None
        if roles_store is not None:
            try:
                rid = roles_store.get_role_id(guild.id, key)
            except Exception:
                try:
                    rid = roles_store.get(guild.id, key)
                except Exception:
                    rid = None
        if rid:
            role = guild.get_role(int(rid))
        if role is None:
            # buscar por nombres viejos
            viejos = {
                "FUNDADOR_OWNER": (
                    "fundador y owner",
                    "fundador y owner",
                    "owner",
                    "👑 fundador y owner",
                ),
                "CO_OWNER": ("co-owner", "co owner", "🤝 co-owner"),
            }.get(key, ())
            for r in guild.roles:
                n = (r.name or "").lower().strip()
                if n == nuevo.lower().strip():
                    role = r
                    break
                if any(v in n for v in viejos):
                    role = r
                    break
        if role is None or role.is_default() or role.managed:
            continue
        if role.name == nuevo:
            continue
        try:
            await role.edit(name=nuevo, reason="Organigrama: renombre autoridades")
            print(f"[roles_nombres] {guild.name}: {key} → {nuevo}")
        except Exception as e:
            print(f"[roles_nombres] edit {key}: {e}")


def registrar(bot: commands.Bot) -> None:
    _parche_config()

    @bot.listen("on_ready")
    async def _rename_autoridades_once():
        if getattr(bot, "_roles_nombres_done", False):
            return
        bot._roles_nombres_done = True  # type: ignore
        for g in bot.guilds:
            try:
                await _renombrar_en_guild(g)
            except Exception as e:
                print(f"[roles_nombres] guild: {e}")

    print("[roles_nombres] OK — Fundador del Hospital / Gerente de Fundación")
