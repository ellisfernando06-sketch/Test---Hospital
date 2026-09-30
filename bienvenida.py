# -*- coding: utf-8 -*-
"""bienvenida.py — Bienvenida + roles de categoría al entrar."""
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
            f"**Qué hacer**\n"
            f"1. Usa `/reglas` o el panel de reglamento\n"
            f"2. Acepta las reglas\n"
            f"3. Completa la verificación Roblox si aplica\n"
            f"4. Postulaciones si quieres unirte al personal"
        ),
        color=0x1ABC9C,
        timestamp=discord.utils.utcnow(),
    )
    emb.set_author(name=f"Nuevo ingreso · {member.display_name}", icon_url=getattr(member.display_avatar, "url", None))
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
            f"Tu entrada a **{hospital}** quedó registrada.\n"
            f"Usa `/reglas` y completa verificación si aplica."
        ),
        color=0x3498DB,
        timestamp=discord.utils.utcnow(),
    ).set_footer(text=f"🖥️ {hospital}")

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
    # Roles de categoría (uniformes) al entrar
    try:
        import roles_setup
        n = await roles_setup.asignar_uniformes_al_entrar(member)
        if n and n > 0:
            print(f"[bienvenida] uniformes +{n} a {member.id}")
    except Exception as e:
        print(f"[bienvenida] uniformes: {e}")
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
    print("[bienvenida] OK — uniformes de categoría al entrar")
