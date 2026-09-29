# -*- coding: utf-8 -*-
"""
estilos.py — Embeds profesionales del Hospital.
Colores temáticos, timestamp, footer. API estable para todo el bot.
"""
from __future__ import annotations

from typing import Optional, Dict, Any

import discord

import config

COLORES = {
    "exito": 0x2ECC71,
    "error": 0xE74C3C,
    "aviso": 0xF39C12,
    "info": 0x3498DB,
    "medico": 0x1ABC9C,
    "finanzas": 0xF1C40F,
    "neutral": 0x95A5A6,
    "roblox": 0x00A2FF,
    "whitelist": 0x57F287,
    "sancion": 0xED4245,
    "investigacion": 0x5865F2,
    "aprobado": 0x57F287,
    "rechazado": 0xED4245,
    "pendiente": 0xFEE75C,
}

EMOJI_TIPO = {
    "exito": "✅",
    "error": "❌",
    "aviso": "⚠️",
    "info": "ℹ️",
    "medico": "🩺",
    "finanzas": "💰",
    "neutral": "📋",
    "roblox": "🎮",
    "whitelist": "🏆",
    "sancion": "⚖️",
    "investigacion": "🔎",
}


def crear_embed(
    tipo: str,
    titulo: str,
    descripcion: str = "",
    autor: Optional[discord.abc.User] = None,
    footer_extra: str = "",
    thumbnail_url: Optional[str] = None,
    image_url: Optional[str] = None,
) -> discord.Embed:
    color = COLORES.get(tipo, COLORES["neutral"])
    emoji = EMOJI_TIPO.get(tipo, "📌")

    if not any(c in titulo for c in ("✅", "❌", "⚠️", "ℹ️", "🎮", "🏆", "⚖️", "🔎", "🩺")):
        titulo = f"{emoji} {titulo}"

    embed = discord.Embed(
        title=titulo,
        description=descripcion or None,
        color=color,
        timestamp=discord.utils.utcnow(),
    )

    if autor:
        avatar = getattr(autor.display_avatar, "url", None)
        embed.set_author(
            name=str(autor.display_name if hasattr(autor, "display_name") else autor),
            icon_url=avatar,
        )

    thumb = thumbnail_url or (config.LOGO_URL if getattr(config, "LOGO_URL", None) else None)
    if thumb:
        embed.set_thumbnail(url=thumb)

    if image_url:
        embed.set_image(url=image_url)

    hospital = getattr(config, "NOMBRE_HOSPITAL", None) or "Hospital General"
    foot = hospital
    if footer_extra:
        foot = f"{hospital}  •  {footer_extra}"
    embed.set_footer(text=foot)
    return embed


def embed_exito_rapido(titulo: str, descripcion: str, autor: Optional[discord.abc.User] = None) -> discord.Embed:
    return crear_embed("exito", titulo, descripcion, autor=autor)


def embed_error_rapido(titulo: str, descripcion: str) -> discord.Embed:
    return crear_embed("error", titulo, descripcion)


def embed_whitelist_roblox(
    discord_user: discord.abc.User,
    roblox_data: Dict[str, Any],
    aprobado: bool = True,
    staff: Optional[discord.abc.User] = None,
) -> discord.Embed:
    username = roblox_data.get("username") or roblox_data.get("name") or "—"
    display = roblox_data.get("displayName") or username
    user_id = roblox_data.get("id") or "—"
    created = roblox_data.get("created") or "—"
    avatar_url = roblox_data.get("avatar_url")
    profile_url = f"https://www.roblox.com/users/{user_id}/profile" if user_id != "—" else None

    estado = "✅ APROBADO" if aprobado else "❌ RECHAZADO"
    color = COLORES["aprobado"] if aprobado else COLORES["rechazado"]

    desc = (
        f"**Verificación de personaje completada.**\n\n"
        f"Tu cuenta de Roblox ha sido enlazada.\n"
        f"Bienvenido/a al equipo del **{getattr(config, 'NOMBRE_HOSPITAL', 'Hospital General')}**."
    )
    if not aprobado:
        desc = "La verificación **no fue aprobada**. Puedes corregir datos y volver a intentar."

    embed = discord.Embed(
        title="🏆 Whitelist / Verificación Roblox" if aprobado else "❌ Verificación no aprobada",
        description=desc,
        color=color,
        timestamp=discord.utils.utcnow(),
        url=profile_url,
    )
    embed.set_author(
        name=f"Postulante: {discord_user}",
        icon_url=getattr(discord_user.display_avatar, "url", None),
    )
    if avatar_url:
        embed.set_thumbnail(url=avatar_url)

    embed.add_field(name="🎮 Usuario Roblox", value=f"`{username}`", inline=True)
    embed.add_field(name="📛 Display Name", value=f"**{display}**", inline=True)
    embed.add_field(name="🆔 User ID", value=f"`{user_id}`", inline=True)

    if created and created != "—":
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
            created_fmt = dt.strftime("%d/%m/%Y")
        except Exception:
            created_fmt = str(created)[:10]
        embed.add_field(name="📅 Cuenta creada", value=created_fmt, inline=True)

    embed.add_field(name="📊 Estado", value=f"**{estado}**", inline=True)
    if staff:
        embed.add_field(name="👮 Evaluador", value=f"{staff.mention}", inline=True)
    if profile_url:
        embed.add_field(name="🔗 Perfil Roblox", value=f"[Abrir perfil]({profile_url})", inline=False)

    embed.set_footer(text=f"{getattr(config, 'NOMBRE_HOSPITAL', 'Hospital General')}  •  Sistema de Verificación")
    return embed


def embed_roblox_verificacion(
    discord_user: discord.abc.User,
    roblox_data: Dict[str, Any],
    staff: Optional[discord.abc.User] = None,
    aprobado: bool = True,
) -> discord.Embed:
    """Alias usado por verificacion.py y comandos_nuevos (mismo diseño whitelist)."""
    return embed_whitelist_roblox(
        discord_user=discord_user,
        roblox_data=roblox_data,
        aprobado=aprobado,
        staff=staff,
    )
