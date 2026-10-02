# -*- coding: utf-8 -*-
"""
bienvenida.py — Bienvenida automática al entrar.
NO otorga roles de jerarquía ni herramientas.
Los roles de acceso se dan al firmar reglas (Miembro) y al verificarse (Comunidad).
Los separadores SÍ se colocan en el miembro (sin color/permisos) para verse en su clasificación de roles.
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
    desc = (
        f"¡Hola, {member.mention}!\n\n"
        f"Acabas de ingresar a **{hospital}**.\n"
        f"Este servidor es un espacio de **roleplay hospitalario**.\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"**📋 Primeros pasos**\n"
        f"1️⃣ Lee y **acepta las reglas** → rol **Miembro**\n"
        f"2️⃣ Completa la **verificación** → rol **Comunidad**\n"
        f"3️⃣ Si quieres unirte al personal → **postulaciones**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"¡Que tengas una excelente estadía! 🩺"
    )
    emb = discord.Embed(
        title=f"🏥 Bienvenido/a a {hospital}",
        description=desc,
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
    emb.add_field(name="👤 Usuario", value=member.mention, inline=True)
    emb.add_field(name="🆔 ID", value=f"`{member.id}`", inline=True)
    emb.add_field(name="👥 Miembros", value=f"`{total}`", inline=True)
    emb.set_footer(text=f"{hospital} · Bienvenida automática")
    return emb


def embed_bienvenida_dm(member: discord.Member) -> discord.Embed:
    hospital = _hospital()
    desc = (
        f"Hola, **{member.display_name}**.\n\n"
        f"Tu entrada a **{hospital}** quedó registrada.\n\n"
        f"**Siguiente paso**\n"
        f"• Acepta las **reglas** → rol **Miembro**\n"
        f"• Completa la **verificación** → rol **Comunidad**\n\n"
        f"¡Bienvenido/a!"
    )
    return discord.Embed(
        title=f"🏥 Acceso a {hospital}",
        description=desc,
        color=0x3498DB,
        timestamp=discord.utils.utcnow(),
    ).set_footer(text=hospital)


def _canal_bienvenida(guild: discord.Guild) -> Optional[discord.TextChannel]:
    try:
        import roles_store

        cid = roles_store.obtener_extra("canal_bienvenida")
        if cid:
            ch = guild.get_channel(int(cid))
            if isinstance(ch, discord.TextChannel):
                return ch
    except Exception:
        pass
    keywords = ("bienvenida", "welcome", "general", "inicio", "lobby")
    for kw in keywords:
        for ch in guild.text_channels:
            name = (ch.name or "").lower().replace("-", " ").replace("_", " ")
            if kw in name:
                return ch
    try:
        sys_ch = guild.system_channel
        if isinstance(sys_ch, discord.TextChannel):
            return sys_ch
    except Exception:
        pass
    return None


async def _on_member_join(member: discord.Member) -> None:
    if member.bot or not member.guild:
        return

    # Separadores: se colocan en el miembro para verse en su lista de roles
    # (sin color, sin permisos; solo clasificación visual, separados del resto)
    try:
        import roles_setup

        n = await roles_setup.asignar_separadores_miembro(member)
        if n:
            print(f"[bienvenida] separadores +{n} → {member}", flush=True)
    except Exception as e:
        print(f"[bienvenida] separadores: {e}", flush=True)

    emb = embed_bienvenida(member)
    canal = _canal_bienvenida(member.guild)
    if canal:
        try:
            await canal.send(content=f"👋 {member.mention}", embed=emb)
        except Exception as e:
            print(f"[bienvenida] canal: {e}", flush=True)

    try:
        await member.send(embed=embed_bienvenida_dm(member))
    except Exception:
        pass


def registrar(bot: commands.Bot) -> None:
    bot.add_listener(_on_member_join, "on_member_join")
    print("[bienvenida] OK — separadores al entrar + mensaje", flush=True)
