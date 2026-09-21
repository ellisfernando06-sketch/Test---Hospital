# -*- coding: utf-8 -*-
"""
sanciones.py — Historial de sanciones, quitar sanción y apelaciones.

- Guarda cada sanción en data/sanciones.json
- Envía log al canal log_sanciones
- /quitar_sancion: anula una sanción (si fue sin razón u otro motivo)
- /apelar_sancion: abre ticket dirigido al Director Administrativo
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import discord

import config
import permisos
import roles_store
from estilos import crear_embed

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "sanciones.json")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> dict:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_PATH):
        return {"sanciones": [], "contador": 0}
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("sanciones", [])
        data.setdefault("contador", 0)
        return data
    except Exception:
        return {"sanciones": [], "contador": 0}


def _save(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def registrar_sancion(
    usuario_id: int,
    tipo: str,
    motivo: str,
    autor_id: int,
    evidencia: str = "",
    evidencia_urls: Optional[List[str]] = None,
    duracion: str = "",
    canal_log_id: Optional[int] = None,
    mensaje_log_id: Optional[int] = None,
) -> dict:
    """Registra una sanción y devuelve el registro creado."""
    data = _load()
    data["contador"] = int(data.get("contador", 0)) + 1
    sid = data["contador"]
    reg = {
        "id": sid,
        "usuario_id": usuario_id,
        "tipo": tipo,
        "motivo": motivo,
        "evidencia": evidencia or "",
        "evidencia_urls": evidencia_urls or [],
        "duracion": duracion or "",
        "autor_id": autor_id,
        "fecha": _now(),
        "activa": True,
        "anulada": False,
        "anulada_por": None,
        "anulada_motivo": None,
        "anulada_fecha": None,
        "canal_log_id": canal_log_id,
        "mensaje_log_id": mensaje_log_id,
    }
    data["sanciones"].append(reg)
    _save(data)
    return reg


def obtener_sancion(sancion_id: int) -> Optional[dict]:
    data = _load()
    for s in data["sanciones"]:
        if int(s.get("id", 0)) == int(sancion_id):
            return s
    return None


def sanciones_de(usuario_id: int, solo_activas: bool = False) -> List[dict]:
    data = _load()
    out = [s for s in data["sanciones"] if int(s.get("usuario_id", 0)) == int(usuario_id)]
    if solo_activas:
        out = [s for s in out if s.get("activa") and not s.get("anulada")]
    return out


def anular_sancion(sancion_id: int, autor_id: int, motivo: str) -> Optional[dict]:
    data = _load()
    for s in data["sanciones"]:
        if int(s.get("id", 0)) == int(sancion_id):
            if s.get("anulada"):
                return None
            s["activa"] = False
            s["anulada"] = True
            s["anulada_por"] = autor_id
            s["anulada_motivo"] = motivo
            s["anulada_fecha"] = _now()
            _save(data)
            return s
    return None


def embed_sancion(reg: dict, guild: Optional[discord.Guild] = None) -> discord.Embed:
    """Embed profesional, creativo y completo para una sanción."""
    estado = "❌ ANULADA" if reg.get("anulada") else ("✅ ACTIVA" if reg.get("activa") else "⏹ INACTIVA")
    color = "sancion" if not reg.get("anulada") else "neutral"
    titulo = f"Sanción #{reg.get('id')} — {reg.get('tipo', 'General')}"

    desc = (
        f"**Motivo de la sanción:**\n"
        f"> {reg.get('motivo', '—')}\n\n"
        f"**Estado actual:** {estado}"
    )
    if reg.get("duracion"):
        desc += f"\n**Duración:** `{reg['duracion']}`"
    if reg.get("evidencia"):
        desc += f"\n\n**📝 Evidencia (texto):**\n{reg['evidencia']}"

    embed = crear_embed(color, titulo, desc)

    uid = reg.get("usuario_id")
    if guild and uid:
        m = guild.get_member(int(uid))
        embed.add_field(name="👤 Sancionado", value=m.mention if m else f"<@{uid}>", inline=True)
    else:
        embed.add_field(name="👤 Sancionado", value=f"<@{uid}>", inline=True)

    autor = reg.get("autor_id")
    embed.add_field(name="👮 Impuesta por", value=f"<@{autor}>" if autor else "—", inline=True)
    fecha_fmt = str(reg.get("fecha", "—"))[:19].replace("T", " ") + " UTC"
    embed.add_field(name="📅 Fecha", value=fecha_fmt, inline=True)

    urls = reg.get("evidencia_urls") or []
    if urls:
        links = "\n".join(f"[🔗 Evidencia {i+1}]({u})" for i, u in enumerate(urls[:8]))
        embed.add_field(name="📎 Evidencias adjuntas", value=links, inline=False)
        # Primera imagen como imagen grande del embed
        first = urls[0]
        if any(first.lower().endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp")):
            embed.set_image(url=first)

    if reg.get("anulada"):
        embed.add_field(
            name="🗑️ Anulación",
            value=(
                f"**Por:** <@{reg.get('anulada_por')}>\n"
                f"**Motivo:** {reg.get('anulada_motivo', '—')}\n"
                f"**Fecha:** {str(reg.get('anulada_fecha', ''))[:19]}"
            ),
            inline=False,
        )

    embed.set_footer(text=f"{config.NOMBRE_HOSPITAL}  •  Sistema de Sanciones Disciplinarias")
    return embed


def embed_historial(usuario: discord.Member, lista: List[dict]) -> discord.Embed:
    if not lista:
        return crear_embed("info", f"📜 Historial de sanciones — {usuario.display_name}", "Sin sanciones registradas.")

    lineas = []
    for s in lista[-15:]:
        estado = "❌" if s.get("anulada") else "✅"
        lineas.append(
            f"{estado} **#{s.get('id')}** · {s.get('tipo', '?')} · {str(s.get('fecha', ''))[:10]}\n"
            f"↳ {s.get('motivo', '—')[:80]}"
        )
    embed = crear_embed(
        "aviso",
        f"📜 Historial de sanciones — {usuario.display_name}",
        "\n\n".join(lineas),
        autor=usuario,
    )
    activas = sum(1 for s in lista if s.get("activa") and not s.get("anulada"))
    embed.add_field(name="Total", value=str(len(lista)), inline=True)
    embed.add_field(name="Activas", value=str(activas), inline=True)
    return embed


async def enviar_log_sancion(bot: discord.Client, embed: discord.Embed) -> Optional[discord.Message]:
    canal_id = config.CANALES.get("log_sanciones")
    if not canal_id:
        return None
    canal = bot.get_channel(canal_id)
    if not canal:
        return None
    try:
        return await canal.send(embed=embed)
    except discord.Forbidden:
        return None


async def abrir_ticket_apelacion(
    guild: discord.Guild,
    usuario: discord.Member,
    sancion: dict,
) -> Optional[discord.TextChannel]:
    """Abre un ticket de apelación dirigido al Director Administrativo + staff."""
    cat = guild.get_channel(config.TICKET_CATEGORIA_ID) if config.TICKET_CATEGORIA_ID else None
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        usuario: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
    }

    # Director Administrativo
    rid_admin = roles_store.obtener_id_key("DIRECTOR_ADMINISTRATIVO")
    if rid_admin:
        rol = guild.get_role(rid_admin)
        if rol:
            overwrites[rol] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

    # Staff del servidor y keys de ticket
    for key in config.TICKET_STAFF_KEYS:
        if key == "DIRECTOR":
            for dk in config.DIRECTOR_KEYS:
                rid = roles_store.obtener_id_key(dk)
                if rid:
                    rol = guild.get_role(rid)
                    if rol:
                        overwrites[rol] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        else:
            rid = roles_store.obtener_id_key(key)
            if rid:
                rol = guild.get_role(rid)
                if rol:
                    overwrites[rol] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

    # Rol Staff del Servidor por nombre
    staff_role = discord.utils.get(guild.roles, name="🖥️ Staff del Servidor") or discord.utils.get(guild.roles, name="Staff del Servidor")
    if staff_role:
        overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

    nombre = f"apelacion-{usuario.name}"[:90]
    try:
        canal = await guild.create_text_channel(
            nombre,
            category=cat if isinstance(cat, discord.CategoryChannel) else None,
            overwrites=overwrites,
            reason=f"Apelación de sanción #{sancion.get('id')} por {usuario}",
        )
    except discord.Forbidden:
        return None

    # Mención staff + director admin
    menciones = []
    if staff_role:
        menciones.append(staff_role.mention)
    if rid_admin:
        rol_a = guild.get_role(rid_admin)
        if rol_a:
            menciones.append(rol_a.mention)

    embed = embed_sancion(sancion, guild)
    embed.title = f"📨 Apelación de sanción #{sancion.get('id')}"
    intro = crear_embed(
        "aviso",
        "📨 Ticket de apelación",
        f"{usuario.mention} solicita apelar la sanción **#{sancion.get('id')}**.\n"
        f"**Director Administrativo** y staff, por favor revisen el caso.\n\n"
        f"El usuario puede adjuntar más pruebas (imágenes, videos o texto) en este canal.",
    )

    from paneles import CerrarTicketView
    content = " ".join(menciones) if menciones else usuario.mention
    await canal.send(content=content, embed=intro)
    await canal.send(embed=embed, view=CerrarTicketView())
    return canal
