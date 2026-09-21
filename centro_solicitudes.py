# -*- coding: utf-8 -*-
"""
centro_solicitudes.py — Sistema General de Solicitudes

Diseño institucional: panel principal, menú, formularios, tickets,
estados, prioridad, logs y almacenamiento persistente.
Las 6 categorías tienen título y color propios en el embed del ticket.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import discord
from discord import ui, app_commands
from discord.ext import commands

import config
import permisos
import roles_store
from estilos import crear_embed

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
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(iso)[:16]


def _load() -> dict:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_PATH):
        return {"contador": 0, "solicitudes": {}}
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("contador", 0)
        data.setdefault("solicitudes", {})
        return data
    except Exception:
        return {"contador": 0, "solicitudes": {}}


def _save(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _siguiente_numero() -> int:
    data = _load()
    data["contador"] = int(data.get("contador", 0)) + 1
    _save(data)
    return data["contador"]


def guardar_solicitud(reg: dict) -> None:
    data = _load()
    data["solicitudes"][str(reg["id"])] = reg
    _save(data)


def obtener_solicitud(sid: int) -> Optional[dict]:
    data = _load()
    return data["solicitudes"].get(str(sid))


def actualizar_solicitud(sid: int, **kwargs) -> Optional[dict]:
    data = _load()
    key = str(sid)
    if key not in data["solicitudes"]:
        return None
    data["solicitudes"][key].update(kwargs)
    data["solicitudes"][key]["fecha_actualizacion"] = _now()
    _save(data)
    return data["solicitudes"][key]


def _rol_staff(guild: discord.Guild) -> Optional[discord.Role]:
    nombres = ["🖥️ Staff del Servidor", "Staff del Servidor", "Staff", "STAFF"]
    for n in nombres:
        r = discord.utils.get(guild.roles, name=n)
        if r:
            return r
    rid = roles_store.obtener_id_key("STAFF_SERVIDOR")
    if rid:
        return guild.get_role(rid)
    return None


def _categoria_canal(guild: discord.Guild) -> Optional[discord.CategoryChannel]:
    cid = getattr(config, "TICKET_CATEGORIA_ID", None)
    if cid:
        ch = guild.get_channel(cid)
        if isinstance(ch, discord.CategoryChannel):
            return ch
    return None


async def enviar_log_solicitud(bot: discord.Client, embed: discord.Embed) -> None:
    canal_id = config.CANALES.get("log_solicitudes") or config.CANALES.get("log_general")
    if not canal_id:
        return
    canal = bot.get_channel(canal_id)
    if canal:
        try:
            await canal.send(embed=embed)
        except discord.Forbidden:
            pass


def embed_panel_principal() -> discord.Embed:
    desc = (
        "Bienvenido al **Centro de Solicitudes**.\n"
        "Desde este apartado podrás realizar diferentes tipos de solicitudes "
        "para que el equipo administrativo pueda revisarlas y darles seguimiento.\n\n"
        "Selecciona a continuación el tipo de solicitud que deseas realizar."
    )
    embed = discord.Embed(
        title="🏛️ CENTRO DE SOLICITUDES",
        description=desc,
        color=0x2C3E50,
        timestamp=discord.utils.utcnow(),
    )
    for key, cat in CATEGORIAS.items():
        embed.add_field(
            name=f"{cat['emoji']} {cat['nombre']}",
            value=cat["descripcion"],
            inline=False,
        )
    embed.set_footer(text=f"{config.NOMBRE_HOSPITAL} · Sistema de Solicitudes")
    if config.LOGO_URL:
        embed.set_thumbnail(url=config.LOGO_URL)
    return embed


def embed_ticket(reg: dict, guild: Optional[discord.Guild] = None) -> discord.Embed:
    """Embed profesional del ticket — diseño propio por cada una de las 6 categorías."""
    cat = CATEGORIAS.get(reg.get("categoria", "general"), CATEGORIAS["general"])
    estado_key = reg.get("estado", "en_revision")
    estado_txt, color = ESTADOS.get(estado_key, ESTADOS["en_revision"])
    prio_key = reg.get("prioridad", "normal")
    prio_txt, _ = PRIORIDADES.get(prio_key, PRIORIDADES["normal"])

    num = reg.get("numero", reg.get("id", 0))
    titulo_cat = cat.get("titulo", f"{cat['emoji']} SOLICITUD")
    embed = discord.Embed(
        title=f"{titulo_cat}  ·  #{num:04d}",
        description=(
            "La solicitud ha sido creada correctamente.\n"
            "Un miembro del equipo correspondiente revisará el caso.\n\n"
            "Puedes adjuntar **imágenes, videos o texto** como evidencia adicional.\n"
            "Evita enviar mensajes innecesarios."
        ),
        color=color,
        timestamp=discord.utils.utcnow(),
    )

    solicitante = f"<@{reg.get('usuario_id')}>"
    embed.add_field(name="👤 Solicitante", value=solicitante, inline=True)
    embed.add_field(name="📂 Categoría", value=f"{cat['emoji']} {cat['nombre']}", inline=True)
    embed.add_field(name="🆔 Número", value=f"`#{num:04d}`", inline=True)
    embed.add_field(name="🟡 Estado", value=estado_txt, inline=True)
    embed.add_field(name="📌 Prioridad", value=prio_txt, inline=True)
    embed.add_field(name="📅 Creada", value=_fecha_legible(reg.get("fecha_creacion")), inline=True)

    resp = reg.get("responsable_id")
    embed.add_field(
        name="👮 Responsable",
        value=f"<@{resp}>" if resp else "— Sin asignar",
        inline=True,
    )

    campos = reg.get("campos") or {}
    if campos:
        lineas = []
        for k, v in campos.items():
            if v and str(v).strip() not in ("—", "-"):
                lineas.append(f"**{k}**\n{v}")
        if lineas:
            texto = "\n\n".join(lineas)
            if len(texto) > 1020:
                texto = texto[:1017] + "…"
            embed.add_field(name="📝 Información proporcionada", value=texto, inline=False)

    if reg.get("resolucion"):
        embed.add_field(name="✅ Resolución", value=reg["resolucion"][:500], inline=False)

    if reg.get("motivo_cierre"):
        embed.add_field(
            name="🔒 Cierre",
            value=f"**Motivo:** {reg['motivo_cierre']}\n**Fecha:** {_fecha_legible(reg.get('fecha_cierre'))}",
            inline=False,
        )

    embed.set_footer(text=f"{config.NOMBRE_HOSPITAL}  ·  Sistema de Solicitudes  ·  ID {reg.get('id')}")
    if config.LOGO_URL:
        embed.set_thumbnail(url=config.LOGO_URL)
    return embed


def embed_log_accion(reg: dict, accion: str, autor: discord.abc.User, detalle: str = "") -> discord.Embed:
    cat = CATEGORIAS.get(reg.get("categoria", "general"), CATEGORIAS["general"])
    num = reg.get("numero", reg.get("id", 0))
    embed = discord.Embed(
        title="📋 SOLICITUD ACTUALIZADA",
        color=0x2C3E50,
        timestamp=discord.utils.utcnow(),
    )
    embed.add_field(name="ID", value=f"#{num:04d}", inline=True)
    embed.add_field(name="Categoría", value=f"{cat['emoji']} {cat['nombre']}", inline=True)
    embed.add_field(name="Usuario", value=f"<@{reg.get('usuario_id')}>", inline=True)
    resp = reg.get("responsable_id")
    embed.add_field(name="Responsable", value=f"<@{resp}>" if resp else "—", inline=True)
    embed.add_field(name="Acción", value=accion, inline=True)
    embed.add_field(name="Realizada por", value=autor.mention if hasattr(autor, "mention") else str(autor), inline=True)
    if detalle:
        embed.add_field(name="Detalle", value=detalle[:500], inline=False)
    embed.add_field(name="Fecha", value=_fecha_legible(), inline=True)
    embed.set_footer(text=config.NOMBRE_HOSPITAL)
    return embed
