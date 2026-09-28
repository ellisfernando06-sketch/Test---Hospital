# -*- coding: utf-8 -*-
"""bienvenida.py — Bienvenida tech limpia al entrar al servidor."""
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
        title="🖥️  Bienvenida al sistema",
        description=(
            f"Hola, {member.mention}.\n\n"
            f"Entraste a **{hospital}**.\n"
            f"Este bot gestiona personal, roleplay y módulos del hospital.\n\n"
            f"**Tu acceso**\n"
            f"🟢 Cuenta conectada\n"
            f"🟡 Comunidad — acepta las reglas\n\n"
            f"**Qué hacer**\n"
            f"1. Usa `/reglas` o el panel de reglamento\n"
            f"2. Acepta las reglas en el MD del bot\n"
            f"3. Si quieres trabajar aquí, ve a **postulaciones**\n"
            f"4. Separa canales de RP (IC) y fuera de rol (OOC)"
        ),
        color=0x1ABC9C,
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

    emb.add_field(name="Usuario", value=member.mention, inline=True)
    emb.add_field(name="ID", value=f"`{member.id}`", inline=True)
    emb.add_field(name="Miembros", value=f"`{total}`", inline=True)
    emb.set_footer(text=f"🖥️ {hospital} · Sistema de gestión")
    return emb


def embed_bienvenida_dm(member: discord.Member) -> discord.Embed:
    hospital = _hospital()
    return discord.Embed(
        title="🖥️  Acceso registrado",
        description=(
            f"Hola, **{member.display_name}**.\n\n"
            f"Tu entrada a **{hospital}** quedó registrada.\n\n"
            f"**Siguiente paso**\n"
            f"• En el servidor usa **`/reglas`**\n"
            f"• O abre el panel de reglamento\n"
            f"• Acepta las reglas para el rol de comunidad\n\n"
            f"Luego podrás usar los canales públicos.\n"
            f"Para unirte al personal, busca **postulaciones**."
        ),
        color=0x3498DB,
        timestamp=discord.utils.utcnow(),
    ).set_footer(text=f"🖥️ {hospital} · Sistema de gestión")


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
    if member.bot or not member.guild:
        return
    emb = embed_bienvenida(member)
    canal = _canal_bienvenida(member.guild)
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
    bot.add_listener(_on_member_join, "on_member_join")
    print("[bienvenida] OK")
