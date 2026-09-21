# -*- coding: utf-8 -*-
"""
centro_solicitudes.py — Sistema General de Solicitudes
Datos, estados, categorías y embeds (6 categorías).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import discord

import config
import roles_store

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "centro_solicitudes.json")

ESTADOS = {
    "en_revision": ("🟡 En revisión", 0xF1C40F),
    "en_investigacion": ("🔵 En investigación", 0x3498DB),
    "info_requerida": ("🟠 Información requerida", 0xE67E22),
    "en_espera": ("🟣 En espera", 0x9B59B6),
    "resuelta": ("🟢 Resuelta", 0x2ECC71),
    "rechazada": ("🔴 Rechazada", 0xE74C3C),
    "cerrada": ("⚫ Cerrada", 0x95A5A6),
}

PRIORIDADES = {
    "normal": ("🟢 Normal", 0x2ECC71),
    "media": ("🟡 Media", 0xF1C40F),
    "alta": ("🟠 Alta", 0xE67E22),
    "urgente": ("🔴 Urgente", 0xE74C3C),
}

CATEGORIAS = {
    "sancion": {
        "emoji": "🛡️",
        "nombre": "Sanciones",
        "titulo": "🛡️ SOLICITUD DE SANCIÓN",
        "descripcion": "Solicitudes relacionadas con sanciones, infracciones y medidas administrativas.",
        "menu_desc": "Solicitar revisión, aplicación o información relacionada con una sanción.",
        "prefijo": "sancion",
        "color": 0x8E44AD,
    },
    "apelacion": {
        "emoji": "⚖️",
        "nombre": "Apelaciones",
        "titulo": "⚖️ SOLICITUD DE APELACIÓN",
        "descripcion": "Solicita la revisión de una sanción o decisión administrativa.",
        "menu_desc": "Apelar una sanción o decisión administrativa.",
        "prefijo": "apelacion",
        "color": 0x2980B9,
    },
    "investigacion": {
        "emoji": "🔎",
        "nombre": "Investigaciones",
        "titulo": "🔎 SOLICITUD DE INVESTIGACIÓN",
        "descripcion": "Solicita una investigación sobre un usuario, situación o incidente.",
        "menu_desc": "Solicitar una investigación.",
        "prefijo": "investigacion",
        "color": 0x16A085,
    },
    "reporte": {
        "emoji": "🚨",
        "nombre": "Reportes",
        "titulo": "🚨 REPORTE",
        "descripcion": "Reporta comportamientos, incumplimientos o situaciones que requieran intervención.",
        "menu_desc": "Reportar a un usuario o situación.",
        "prefijo": "reporte",
        "color": 0xC0392B,
    },
    "general": {
        "emoji": "📩",
        "nombre": "Solicitud General",
        "titulo": "📩 SOLICITUD GENERAL",
        "descripcion": "Utiliza esta opción cuando tu solicitud no corresponda a ninguna de las categorías anteriores.",
        "menu_desc": "Realizar una solicitud que no pertenece a otra categoría.",
        "prefijo": "solicitud",
        "color": 0x3498DB,
    },
    "consulta": {
        "emoji": "📋",
        "nombre": "Consultas",
        "titulo": "📋 CONSULTA",
        "descripcion": "Para realizar consultas o solicitar información al equipo correspondiente.",
        "menu_desc": "Realizar una consulta administrativa.",
        "prefijo": "consulta",
        "color": 0x1ABC9C,
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fecha_legible(iso: Optional[str] = None) -> str:
    if not iso:
        iso = _now()
    try:
        dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(iso)[:16] if iso else "—"


def _load() -> dict:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_PATH):
        return {"contador": 0, "solicitudes": {}}
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"contador": 0, "solicitudes": {}}
        data.setdefault("contador", 0)
        data.setdefault("solicitudes", {})
        if not isinstance(data["solicitudes"], dict):
            data["solicitudes"] = {}
        return data
    except Exception:
        return {"contador": 0, "solicitudes": {}}


def _save(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _siguiente_numero() -> int:
    data = _load()
    data["contador"] = int(data.get("contador") or 0) + 1
    _save(data)
    return int(data["contador"])


def guardar_solicitud(reg: dict) -> None:
    if not isinstance(reg, dict) or "id" not in reg:
        return
    data = _load()
    data["solicitudes"][str(reg["id"])] = reg
    _save(data)


def obtener_solicitud(sid: int) -> Optional[dict]:
    data = _load()
    item = data.get("solicitudes", {}).get(str(sid))
    return item if isinstance(item, dict) else None


def actualizar_solicitud(sid: int, **kwargs) -> Optional[dict]:
    data = _load()
    key = str(sid)
    if key not in data.get("solicitudes", {}):
        return None
    reg = data["solicitudes"][key]
    reg.update(kwargs)
    reg["actualizado"] = _now()
    data["solicitudes"][key] = reg
    _save(data)
    return reg


def _cat(reg: dict) -> dict:
    slug = (reg or {}).get("categoria") or "general"
    return CATEGORIAS.get(slug) or CATEGORIAS["general"]


def embed_panel_principal() -> discord.Embed:
    embed = discord.Embed(
        title="📋 Centro de Solicitudes",
        description=(
            "Selecciona el tipo de solicitud que deseas realizar.\n"
            "Un miembro del equipo revisará tu caso y te responderá en el ticket."
        ),
        color=0x3498DB,
        timestamp=discord.utils.utcnow(),
    )
    for slug, cat in CATEGORIAS.items():
        embed.add_field(
            name=f"{cat['emoji']} {cat['nombre']}",
            value=cat.get("menu_desc") or cat.get("descripcion") or "—",
            inline=False,
        )
    embed.set_footer(text=f"{config.NOMBRE_HOSPITAL}  •  Centro de Solicitudes")
    return embed


def embed_ticket(reg: Optional[dict], guild: Optional[discord.Guild] = None) -> discord.Embed:
    if not isinstance(reg, dict):
        reg = {}
    cat = _cat(reg)
    estado_key = reg.get("estado") or "en_revision"
    estado_info = ESTADOS.get(estado_key) or ESTADOS["en_revision"]
    estado_txt, color = estado_info[0], estado_info[1]
    prio_key = reg.get("prioridad") or "normal"
    prio_info = PRIORIDADES.get(prio_key) or PRIORIDADES["normal"]
    prio_txt = prio_info[0]
    try:
        num = int(reg.get("numero") or reg.get("id") or 0)
    except (TypeError, ValueError):
        num = 0
    titulo_cat = cat.get("titulo") or f"{cat.get('emoji', '📋')} SOLICITUD"
    embed = discord.Embed(
        title=f"{titulo_cat}  ·  #{num:04d}",
        description=(
            "**Solicitud registrada correctamente.**\n\n"
            "📋 **Instrucciones para el solicitante:**\n"
            "• Puedes adjuntar **imágenes, videos o archivos** como evidencia adicional en este canal.\n"
            "• Responde de forma clara y profesional cuando el staff te solicite más información.\n"
            "• Evita mensajes innecesarios o spam; esto puede retrasar la resolución.\n\n"
            "👮 **Instrucciones para el staff / director:**\n"
            "• Revise la solicitud y las evidencias adjuntas.\n"
            "• Actualice el estado del ticket según corresponda (en investigación, resuelta, etc.).\n"
            "• Si requiere autorización superior, derívalo o use el sistema de aprobación.\n"
            "• Cierre el ticket únicamente cuando el caso esté resuelto."
        ),
        color=color,
        timestamp=discord.utils.utcnow(),
    )
    embed.add_field(name="Estado", value=estado_txt, inline=True)
    embed.add_field(name="Prioridad", value=prio_txt, inline=True)
    autor_id = reg.get("autor_id")
    if autor_id:
        embed.add_field(name="Solicitante", value=f"<@{autor_id}>", inline=True)
    campos = reg.get("campos") or {}
    if isinstance(campos, dict):
        for k, v in list(campos.items())[:10]:
            embed.add_field(name=str(k), value=str(v)[:500] or "—", inline=False)
    embed.set_footer(text=f"{config.NOMBRE_HOSPITAL}  •  Ticket #{num:04d}")
    return embed


def embed_log_accion(reg: dict, accion: str, por: Optional[discord.Member] = None) -> discord.Embed:
    color = 0x2ECC71 if "resuel" in (accion or "").lower() else 0x3498DB
    embed = discord.Embed(
        title=f"📋 Log — {accion}",
        description=f"Solicitud **#{reg.get('numero') or reg.get('id')}**",
        color=color,
        timestamp=discord.utils.utcnow(),
    )
    if por:
        embed.add_field(name="Por", value=por.mention, inline=True)
    embed.set_footer(text=config.NOMBRE_HOSPITAL)
    return embed


def _rol_staff(guild: discord.Guild) -> Optional[discord.Role]:
    return (
        discord.utils.get(guild.roles, name="🖥️ Staff del Servidor")
        or discord.utils.get(guild.roles, name="Staff del Servidor")
        or discord.utils.get(guild.roles, name="Staff")
    )


def _categoria_canal(guild: discord.Guild) -> Optional[discord.CategoryChannel]:
    cid = getattr(config, "TICKET_CATEGORIA_ID", None)
    if cid:
        ch = guild.get_channel(cid)
        if isinstance(ch, discord.CategoryChannel):
            return ch
    return None


async def enviar_log_solicitud(bot: discord.Client, embed: discord.Embed) -> None:
    canal_id = config.CANALES.get("log_solicitudes")
    if not canal_id:
        return
    canal = bot.get_channel(canal_id)
    if not canal:
        return
    try:
        await canal.send(embed=embed)
    except discord.Forbidden:
        pass
