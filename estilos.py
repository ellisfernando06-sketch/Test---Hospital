"""
estilos.py
==========
Estilo visual consistente para todos los embeds del bot: mismos
colores según el tipo de mensaje, mismo footer/logo, timestamp, etc.
No necesita edición.
"""

import discord
import config

COLOR_INFO = discord.Color.blurple()
COLOR_EXITO = discord.Color.green()
COLOR_ERROR = discord.Color.red()
COLOR_AVISO = discord.Color.orange()
COLOR_MEDICO = discord.Color.blue()
COLOR_FINANZAS = discord.Color.gold()

_COLORES = {
    "info": COLOR_INFO,
    "exito": COLOR_EXITO,
    "error": COLOR_ERROR,
    "aviso": COLOR_AVISO,
    "medico": COLOR_MEDICO,
    "finanzas": COLOR_FINANZAS,
}


def crear_embed(
    tipo: str,
    titulo: str,
    descripcion: str = "",
    autor: discord.Member = None,
) -> discord.Embed:
    embed = discord.Embed(
        title=titulo,
        description=descripcion,
        color=_COLORES.get(tipo, COLOR_INFO),
        timestamp=discord.utils.utcnow(),
    )
    embed.set_footer(text=config.NOMBRE_HOSPITAL)
    if config.LOGO_URL:
        embed.set_thumbnail(url=config.LOGO_URL)
        embed.set_footer(text=config.NOMBRE_HOSPITAL, icon_url=config.LOGO_URL)
    if autor:
        embed.set_author(name=autor.display_name, icon_url=autor.display_avatar.url)
    return embed
