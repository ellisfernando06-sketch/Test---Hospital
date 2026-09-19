# -*- coding: utf-8 -*-
"""
estilos.py — Embeds con colores temáticos del hospital.
"""
from __future__ import annotations

from typing import Optional

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
}


def crear_embed(
    tipo: str,
    titulo: str,
    descripcion: str = "",
    autor: Optional[discord.abc.User] = None,
) -> discord.Embed:
    color = COLORES.get(tipo, COLORES["neutral"])
    embed = discord.Embed(
        title=titulo,
        description=descripcion or None,
        color=color,
        timestamp=discord.utils.utcnow(),
    )
    if autor:
        embed.set_author(name=str(autor), icon_url=getattr(autor.display_avatar, "url", None))
    if config.LOGO_URL:
        embed.set_thumbnail(url=config.LOGO_URL)
    embed.set_footer(text=config.NOMBRE_HOSPITAL)
    return embed
