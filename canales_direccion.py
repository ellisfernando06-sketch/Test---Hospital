# -*- coding: utf-8 -*-
"""
canales_direccion.py — Canales de cada dirección + envío de solicitudes.

- /configurar_canal_direccion  → guarda canal por área
- /ver_canales_direccion       → lista guardados
- enviar_solicitud_area(...)   → canal del área + DM a quienes tengan el rol

Áreas: docencia, medico, enfermeria, rrhh, logistica, general,
       cancilleria, seguridad, verificacion, staff, inactividad
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Sequence, Tuple

import discord
from discord import app_commands
from discord.ext import commands

_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
_PATH = os.path.join(_DATA, "canales_direccion.json")

# area_key → (nombre visible, keys de roles que firman/autorizan)
AREAS: Dict[str, Dict[str, Any]] = {
    "docencia": {
        "nombre": "Docencia / Certificados",
        "emoji": "📚",
        "keys": ["DIR_DOCENCIA", "DIRECTOR_DOCENCIA"],
    },
    "medico": {
        "nombre": "Dirección Médica",
        "emoji": "🩺",
        "keys": ["DIR_MEDICO", "DIRECTOR_MEDICO"],
    },
    "enfermeria": {
        "nombre": "Dirección de Enfermería",
        "emoji": "💉",
        "keys": ["DIR_ENFERMERIA", "DIRECTOR_ENFERMERIA"],
    },
    "rrhh": {
        "nombre": "Recursos Humanos",
        "emoji": "👥",
        "keys": ["DIR_RRHH", "DIRECTOR_RRHH"],
    },
    "logistica": {
        "nombre": "Logística",
        "emoji": "📦",
        "keys": ["DIR_LOGISTICA", "DIRECTOR_LOGISTICA"],
    },
    "general": {
        "nombre": "Dirección General",
        "emoji": "🖥️",
        "keys": ["DIR_GENERAL", "DIRECTOR_GENERAL"],
    },
    "cancilleria": {
        "nombre": "Cancillería (operaciones)",
        "emoji": "🏛️",
        "keys": ["CANCILLER", "VICE_CANCILLER", "PREFECTO_OPERACIONES"],
    },
    "seguridad": {
        "nombre": "Seguridad",
        "emoji": "🛡️",
        "keys": ["JEFE_SEGURIDAD", "SUPERVISOR_SEGURIDAD"],
    },
    "verificacion": {
        "nombre": "Verificaciones / Whitelist",
        "emoji": "✅",
        "keys": ["DIR_RRHH", "DIRECTOR_RRHH", "CANCILLER", "PREFECTO_OPERACIONES"],
    },
    "staff": {
        "nombre": "Staff del servidor",
        "emoji": "🛡️",
        "keys": ["ADMIN_JEFE", "ADMIN", "FUNDADOR_OWNER", "CO_OWNER", "OWNER"],
    },
    "inactividad": {
        "nombre": "Inactividad",
        "emoji": "⏸️",
        "keys": ["DIR_RRHH", "DIRECTOR_RRHH", "CANCILLER", "DIR_GENERAL"],
    },
}

# Qué área usa cada tipo de solicitud
TIPO_A_AREA = {
    "certificado": "docencia",
    "certificacion": "docencia",
    "firma_docencia": "docencia",
    "capacitacion": "docencia",
    "medico": "medico",
    "enfermeria": "enfermeria",
    "rrhh": "rrhh",
    "despido": "rrhh",
    "sancion": "rrhh",
    "logistica": "logistica",
    "general": "general",
    "cancilleria": "cancilleria",
    "operaciones": "cancilleria",
    "seguridad": "seguridad",
    "verificacion": "verificacion",
    "whitelist": "verificacion",
    "staff": "staff",
    "inactividad": "inactividad",
}


def _load() -> dict:
    os.makedirs(_DATA, exist_ok=True)
    if not os.path.isfile(_PATH):
        return {"canales": {}}
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("canales", {})
        return data
    except Exception:
        return {"canales": {}}


def _save(data: dict) -> None:
    os.makedirs(_DATA, exist_ok=True)
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def guardar_canal(area: str, channel_id: int, guild_id: int) -> None:
    data = _load()
    data["canales"][area] = {"channel_id": int(channel_id), "guild_id": int(guild_id)}
    _save(data)


def obtener_canal_id(area: str) -> Optional[int]:
    reg = _load()["canales"].get(area)
    if not reg:
        return None
    try:
        return int(reg["channel_id"])
    except Exception:
        return None


def area_por_tipo(tipo: str) -> str:
    t = (tipo or "").lower().strip()
    return TIPO_A_AREA.get(t, t if t in AREAS else "staff")


def _role_ids_for_keys(guild: discord.Guild, keys: Sequence[str]) -> List[int]:
    ids: List[int] = []
    try:
        import roles_store

        for k in keys:
            rid = roles_store.obtener_id_key(k)
            if rid:
                ids.append(int(rid))
    except Exception:
        pass
    # Fallback por nombre oficial
    try:
        import roles_config

        for k in keys:
            nom = roles_config.KEYS_NOMBRES.get(k)
            if not nom:
                continue
            nombre = nom[0]
            for r in guild.roles:
                if r.name == nombre or (nombre.lower() in (r.name or "").lower()):
                    ids.append(r.id)
    except Exception:
        pass
    return list(dict.fromkeys(ids))


def miembros_con_keys(guild: discord.Guild, keys: Sequence[str]) -> List[discord.Member]:
    role_ids = set(_role_ids_for_keys(guild, keys))
    out: List[discord.Member] = []
    for m in guild.members:
        if m.bot:
            continue
        if any(r.id in role_ids for r in m.roles):
            out.append(m)
            continue
        # admin fallback solo para staff area
        if "OWNER" in keys or "FUNDADOR_OWNER" in keys:
            if m.guild_permissions.administrator:
                out.append(m)
    # unique
    seen = set()
    uniq = []
    for m in out:
        if m.id not in seen:
            seen.add(m.id)
            uniq.append(m)
    return uniq


async def enviar_solicitud_area(
    bot: commands.Bot,
    guild: discord.Guild,
    *,
    area: str,
    embed: discord.Embed,
    view: Optional[discord.ui.View] = None,
    content: str = "",
    dm_embed: Optional[discord.Embed] = None,
) -> Dict[str, Any]:
    """
    Envía al canal configurado del área y por DM a quienes tienen el rol.
    Devuelve {"canal": bool, "dms": int, "sin_canal": bool, "miembros": int}.
    """
    info = AREAS.get(area) or AREAS["staff"]
    keys = info.get("keys") or []
    result = {"canal": False, "dms": 0, "sin_canal": False, "miembros": 0, "area": area}

    cid = obtener_canal_id(area)
    ch = guild.get_channel(cid) if cid else None
    if isinstance(ch, discord.TextChannel):
        try:
            await ch.send(content=content or None, embed=embed, view=view)
            result["canal"] = True
        except Exception as e:
            print(f"[canales_direccion] canal {area}: {e}", flush=True)
    else:
        result["sin_canal"] = True

    targets = miembros_con_keys(guild, keys)
    result["miembros"] = len(targets)
    dm_emb = dm_embed or embed
    for m in targets:
        try:
            await m.send(
                content=(
                    f"📬 **Solicitud · {info.get('emoji', '')} {info.get('nombre', area)}**\n"
                    f"Revisa y firma/autoriza si corresponde."
                ),
                embed=dm_emb,
                view=view,
            )
            result["dms"] += 1
        except Exception:
            pass
    return result


async def enviar_solicitud_tipo(
    bot: commands.Bot,
    guild: discord.Guild,
    *,
    tipo: str,
    embed: discord.Embed,
    view: Optional[discord.ui.View] = None,
    content: str = "",
) -> Dict[str, Any]:
    return await enviar_solicitud_area(
        bot, guild, area=area_por_tipo(tipo), embed=embed, view=view, content=content
    )


def _puede_cfg(member: discord.Member) -> bool:
    if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
        return True
    try:
        import permisos

        return permisos.member_tiene_alguna_key(
            member, "FUNDADOR_OWNER", "CO_OWNER", "OWNER", "CANCILLER", "PREFECTO_OPERACIONES"
        )
    except Exception:
        return False


def registrar(bot: commands.Bot) -> None:
    for name in ("configurar_canal_direccion", "ver_canales_direccion"):
        try:
            bot.tree.remove_command(name)
        except Exception:
            pass

    choices = [
        app_commands.Choice(name=f"{v['emoji']} {v['nombre']}", value=k)
        for k, v in AREAS.items()
    ]

    @bot.tree.command(
        name="configurar_canal_direccion",
        description="[Staff] Asigna el canal donde llegan solicitudes de un área",
    )
    @app_commands.describe(
        area="Dirección / área",
        canal="Canal de texto de esa dirección",
    )
    @app_commands.choices(area=choices)
    async def cfg_canal(
        inter: discord.Interaction,
        area: app_commands.Choice[str],
        canal: discord.TextChannel,
    ):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _puede_cfg(inter.user):
            return await inter.response.send_message(
                "❌ Solo administración / cancillería.", ephemeral=True
            )
        guardar_canal(area.value, canal.id, inter.guild.id)
        info = AREAS[area.value]
        keys = ", ".join(f"`{k}`" for k in info["keys"])
        await inter.response.send_message(
            embed=discord.Embed(
                title="✅ Canal de dirección guardado",
                description=(
                    f"**Área:** {info['emoji']} {info['nombre']}\n"
                    f"**Canal:** {canal.mention}\n"
                    f"**Roles que reciben DM:** {keys}\n\n"
                    f"Las solicitudes de esta área irán aquí y a los MD de quien tenga el rol."
                ),
                color=0x2ECC71,
            ),
            ephemeral=True,
        )

    @bot.tree.command(
        name="ver_canales_direccion",
        description="Lista los canales de dirección configurados",
    )
    async def ver_canales(inter: discord.Interaction):
        if not inter.guild:
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        data = _load()["canales"]
        lines = []
        for k, info in AREAS.items():
            reg = data.get(k)
            if reg and reg.get("channel_id"):
                ch = inter.guild.get_channel(int(reg["channel_id"]))
                mention = ch.mention if ch else f"`{reg['channel_id']}` (no visible)"
                lines.append(f"{info['emoji']} **{info['nombre']}** → {mention}")
            else:
                lines.append(
                    f"{info['emoji']} **{info['nombre']}** → _sin configurar_"
                )
        await inter.response.send_message(
            embed=discord.Embed(
                title="📁 Canales de dirección",
                description="\n".join(lines),
                color=0x3498DB,
            ),
            ephemeral=True,
        )

    print("[canales_direccion] OK — /configurar_canal_direccion + envío canal/DM")
