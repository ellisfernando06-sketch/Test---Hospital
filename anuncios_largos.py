# -*- coding: utf-8 -*-
"""anuncios_largos.py — Anuncios y reglamento sin límite de texto (partición automática)."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List, Optional

import discord
from discord import app_commands
from discord.ext import commands

import config
import permisos
from estilos import crear_embed
from permisos import require_key

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_REGLAMENTO_PATH = os.path.join(_DATA_DIR, "reglamento.json")

# Límite seguro para description de embed Discord (~4096)
_MAX_EMBED_DESC = 3900


def _split_text(text: str, max_len: int = _MAX_EMBED_DESC) -> List[str]:
    """Parte texto largo respetando saltos de línea cuando sea posible."""
    text = (text or "").strip()
    if not text:
        return [""]
    if len(text) <= max_len:
        return [text]
    chunks: List[str] = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        cut = text.rfind("\n", 0, max_len)
        if cut < max_len // 3:
            cut = max_len
        chunks.append(text[:cut].rstrip())
        text = text[cut:].lstrip("\n")
    return chunks


def _embeds_anuncio(
    titulo: str,
    cuerpo: str,
    autor: discord.abc.User,
    color: int = 0x2C3E50,
    subtitulo: str = "",
) -> List[discord.Embed]:
    partes = _split_text(cuerpo)
    total = len(partes)
    embeds: List[discord.Embed] = []
    for i, parte in enumerate(partes):
        if i == 0:
            title = f"📢 {titulo}"
            if subtitulo:
                title = f"📢 {subtitulo} · {titulo}"
        else:
            title = f"📢 {titulo} (parte {i + 1}/{total})"
        emb = discord.Embed(
            title=title,
            description=parte or "_Sin contenido_",
            color=color,
            timestamp=datetime.now(timezone.utc),
        )
        if i == 0:
            emb.set_author(
                name=f"Publicado por {getattr(autor, 'display_name', autor)}",
                icon_url=getattr(getattr(autor, "display_avatar", None), "url", None),
            )
        footer = f"{getattr(config, 'NOMBRE_HOSPITAL', 'Hospital')}  ·  Anuncios oficiales"
        if total > 1:
            footer += f"  ·  {i + 1}/{total}"
        emb.set_footer(text=footer)
        embeds.append(emb)
    return embeds


async def _publicar_en_canal(
    interaction: discord.Interaction,
    embeds: List[discord.Embed],
    prefer_keys: tuple = ("anuncios", "log_general", "bot_status"),
) -> discord.abc.Messageable:
    """Elige canal de anuncios si existe; si no, el canal actual."""
    canal = None
    guild = interaction.guild
    if guild:
        for key in prefer_keys:
            cid = config.CANALES.get(key)
            if cid:
                c = guild.get_channel(cid)
                if c and isinstance(c, discord.TextChannel):
                    canal = c
                    break
    if canal is None:
        canal = interaction.channel
    for emb in embeds:
        await canal.send(embed=emb)
    return canal


def _load_reglamento() -> dict:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_REGLAMENTO_PATH):
        return {}
    try:
        with open(_REGLAMENTO_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_reglamento(titulo: str, texto: str, por: int) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    data = {
        "titulo": titulo,
        "texto": texto,
        "actualizado_por": por,
        "actualizado_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(_REGLAMENTO_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    # También actualiza config en memoria si existe el atributo
    try:
        config.REGLAS_TEXTO = texto
    except Exception:
        pass


def registrar(bot: commands.Bot) -> None:
    # Quitar el anuncio del núcleo (límite corto) para reemplazarlo
    for nombre in ("anuncio", "anuncio_direccion", "agregar_reglamento"):
        try:
            bot.tree.remove_command(nombre)
        except Exception:
            pass

    @bot.tree.command(
        name="anuncio",
        description="Publica un anuncio oficial (sin límite de tamaño; se parte solo si es muy largo)",
    )
    @app_commands.describe(
        titulo="Título del anuncio",
        mensaje="Contenido completo del anuncio (puede ser muy largo)",
    )
    @require_key("DIRECTOR", "OWNER", "DIRECTOR_GENERAL", "CO_OWNER", "DIRECTOR_ADMINISTRATIVO")
    async def anuncio(
        interaction: discord.Interaction,
        titulo: str,
        mensaje: str,
    ):
        await interaction.response.defer(ephemeral=True)
        try:
            embeds = _embeds_anuncio(titulo, mensaje, interaction.user)
            canal = await _publicar_en_canal(interaction, embeds)
            partes = len(embeds)
            extra = f" ({partes} mensajes)" if partes > 1 else ""
            where = canal.mention if hasattr(canal, "mention") else "este canal"
            await interaction.followup.send(
                f"✅ Anuncio publicado en {where}{extra}.",
                ephemeral=True,
            )
        except Exception as e:
            print(f"[anuncio] error: {e}")
            await interaction.followup.send(
                f"❌ No se pudo publicar el anuncio: `{e}`",
                ephemeral=True,
            )

    @bot.tree.command(
        name="anuncio_direccion",
        description="Anuncio oficial de una dirección (texto largo permitido)",
    )
    @app_commands.describe(
        direccion="Nombre de la dirección (ej: Médica, RRHH, Disciplina)",
        titulo="Título del anuncio",
        mensaje="Contenido completo (sin límite de tamaño)",
    )
    @require_key(
        "DIRECTOR", "OWNER", "DIRECTOR_GENERAL", "CO_OWNER",
        "DIRECTOR_ADMINISTRATIVO", "DIRECTOR_DISCIPLINA", "DIRECTOR_MEDICO",
        "DIRECTOR_ENFERMERIA", "DIRECTOR_RRHH", "DIRECTOR_FINANCIERO",
        "DIRECTOR_LOGISTICA", "DIRECTOR_SEGURIDAD", "DIRECTOR_DOCENCIA",
    )
    async def anuncio_direccion(
        interaction: discord.Interaction,
        direccion: str,
        titulo: str,
        mensaje: str,
    ):
        await interaction.response.defer(ephemeral=True)
        try:
            embeds = _embeds_anuncio(
                titulo,
                mensaje,
                interaction.user,
                color=0x1ABC9C,
                subtitulo=direccion.strip() or "Dirección",
            )
            canal = await _publicar_en_canal(interaction, embeds)
            partes = len(embeds)
            extra = f" ({partes} mensajes)" if partes > 1 else ""
            where = canal.mention if hasattr(canal, "mention") else "este canal"
            await interaction.followup.send(
                f"✅ Anuncio de **{direccion}** publicado en {where}{extra}.",
                ephemeral=True,
            )
        except Exception as e:
            print(f"[anuncio_direccion] error: {e}")
            await interaction.followup.send(
                f"❌ No se pudo publicar: `{e}`",
                ephemeral=True,
            )

    @bot.tree.command(
        name="agregar_reglamento",
        description="Guarda y publica el reglamento completo (sin límite de tamaño)",
    )
    @app_commands.describe(
        titulo="Título del reglamento (ej: Reglamento general)",
        texto="Texto completo del reglamento (puede ser muy largo)",
        publicar="Si es True, lo publica en el canal de anuncios ahora",
    )
    @require_key("OWNER", "CO_OWNER", "DIRECTOR_GENERAL", "DIRECTOR_ADMINISTRATIVO")
    async def agregar_reglamento(
        interaction: discord.Interaction,
        titulo: str,
        texto: str,
        publicar: bool = True,
    ):
        await interaction.response.defer(ephemeral=True)
        try:
            _save_reglamento(titulo, texto, interaction.user.id)
            msg = f"✅ Reglamento **{titulo}** guardado ({len(texto)} caracteres)."
            if publicar:
                embeds = _embeds_anuncio(
                    titulo,
                    texto,
                    interaction.user,
                    color=0x5865F2,
                    subtitulo="Reglamento",
                )
                # Usar título tipo reglamento
                for i, emb in enumerate(embeds):
                    if i == 0:
                        emb.title = f"📜 {titulo}"
                    else:
                        emb.title = f"📜 {titulo} (parte {i + 1}/{len(embeds)})"
                    emb.color = 0x5865F2
                canal = await _publicar_en_canal(interaction, embeds)
                partes = len(embeds)
                where = canal.mention if hasattr(canal, "mention") else "este canal"
                msg += f" Publicado en {where}"
                if partes > 1:
                    msg += f" ({partes} mensajes)"
                msg += "."
            await interaction.followup.send(msg, ephemeral=True)
        except Exception as e:
            print(f"[agregar_reglamento] error: {e}")
            await interaction.followup.send(
                f"❌ Error al guardar/publicar el reglamento: `{e}`",
                ephemeral=True,
            )

    print("[anuncios_largos] OK — anuncio, anuncio_direccion, agregar_reglamento")
