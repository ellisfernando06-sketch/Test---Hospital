# -*- coding: utf-8 -*-
"""
bienvenida.py — Mensaje de bienvenida del hospital.
Estilo tecnológico, en español, claro y visualmente cuidado.
"""
from __future__ import annotations

from typing import Optional

import discord
from discord.ext import commands

import config


def _hospital() -> str:
    return getattr(config, "NOMBRE_HOSPITAL", None) or "Hospital General"


def embed_bienvenida(member: discord.Member) -> discord.Embed:
    hospital = _hospital()
    total = member.guild.member_count if member.guild else "—"

    emb = discord.Embed(
        title="🖥️  Sistema de acceso — Bienvenida",
        description=(
            f"```\n"
            f" HOSPITAL  ·  {hospital.upper()}\n"
            f" MÓDULO    ·  INGRESO AL SERVIDOR\n"
            f"```\n\n"
            f"Hola, {member.mention}.\n\n"
            f"Acabas de entrar al sistema de **{hospital}**.\n"
            f"Aquí se gestiona el personal, el roleplay y los módulos del hospital.\n\n"
            f"**Estado de tu acceso**\n"
            f"```\n"
            f" Cuenta Discord ....... CONECTADA\n"
            f" Registro ............. EN PROCESO\n"
            f" Comunidad ............ PENDIENTE DE REGLAS\n"
            f"```\n\n"
            f"**Qué hacer ahora**\n"
            f"1️⃣ Lee el **reglamento** (`/reglas` o el panel de reglas)\n"
            f"2️⃣ Acepta las reglas en tus mensajes directos\n"
            f"3️⃣ Si vas a trabajar aquí, sigue el proceso de **postulación**\n"
            f"4️⃣ Respeta canales IC (roleplay) y OOC (fuera de personaje)\n\n"
            f"*El sistema te guiará con los paneles y comandos del hospital.*"
        ),
        color=0x00D2A0,
        timestamp=discord.utils.utcnow(),
    )

    emb.set_author(
        name=f"Nuevo ingreso · {member.display_name}",
        icon_url=getattr(member.display_avatar, "url", None),
    )
    try:
        emb.set_thumbnail(url=member.display_avatar.url)
    except Exception:
        pass

    emb.add_field(name="👤 Usuario", value=f"{member.mention}", inline=True)
    emb.add_field(name="🆔 ID", value=f"`{member.id}`", inline=True)
    emb.add_field(name="📊 Miembros", value=f"`{total}`", inline=True)

    emb.set_footer(text=f"🖥️  {hospital}  ·  Sistema de gestión  │  Módulo de bienvenida")
    return emb


def embed_bienvenida_dm(member: discord.Member) -> discord.Embed:
    hospital = _hospital()
    emb = discord.Embed(
        title="🖥️  Acceso registrado",
        description=(
            f"```\n"
            f" {hospital.upper()}\n"
            f" BIENVENIDA AL SISTEMA\n"
            f"```\n\n"
            f"Hola, **{member.display_name}**.\n\n"
            f"Tu entrada al servidor quedó registrada.\n\n"
            f"**Siguiente paso**\n"
            f"• Abre el servidor y usa **`/reglas`**\n"
            f"• O pulsa el panel de reglamento en el canal de información\n"
            f"• Acepta las reglas para obtener el rol de comunidad\n\n"
            f"Cuando tengas el rol, podrás moverte por los canales públicos.\n"
            f"Si quieres unirte al personal, busca el canal de **postulaciones**.\n\n"
            f"*Cualquier duda: canal de soporte.*"
        ),
        color=0x2E86DE,
        timestamp=discord.utils.utcnow(),
    )
    emb.set_footer(text=f"🖥️  {hospital}  ·  Sistema de gestión")
    return emb


def _canal_bienvenida(guild: discord.Guild) -> Optional[discord.TextChannel]:
    canales = getattr(config, "CANALES", {}) or {}
    cid = canales.get("bienvenida")
    if cid:
        ch = guild.get_channel(int(cid))
        if isinstance(ch, discord.TextChannel):
            return ch
    for nombre in ("bienvenida", "welcome", "entrada", "ingresos"):
        for ch in guild.text_channels:
            if nombre in (ch.name or "").lower():
                return ch
    return None


async def _on_member_join(member: discord.Member) -> None:
    if member.bot:
        return
    guild = member.guild
    if not guild:
        return

    emb = embed_bienvenida(member)
    canal = _canal_bienvenida(guild)
    if canal:
        try:
            await canal.send(content=member.mention, embed=emb)
        except Exception:
            pass

    try:
        await member.send(embed=embed_bienvenida_dm(member))
    except Exception:
        pass


def registrar(bot: commands.Bot) -> None:
    # Listener (no pisa otros on_member_join)
    bot.add_listener(_on_member_join, "on_member_join")
    print("[bienvenida] OK — ingreso tecnológico al servidor")
