# -*- coding: utf-8 -*-
"""
bienvenida.py — Bienvenida cálida, ordenada y guiada por puntos.
Separadores al entrar. Sin roles de jerarquía automáticos.
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
        f"Hola, {member.mention} 👋\n\n"
        f"Nos alegra tenerte en **{hospital}**.\n"
        f"Este es un espacio de **roleplay hospitalario**: profesional, "
        f"respetuoso y pensado para que disfrutes la experiencia.\n\n"
        f"╔══════════════════════════╗\n"
        f"║   **Tu guía de ingreso**   ║\n"
        f"╚══════════════════════════╝\n\n"
        f"**1.** Lee las **normativas** del servidor\n"
        f"　　· RP · Discord · General\n\n"
        f"**2.** Acepta las **reglas**\n"
        f"　　→ Obtienes el rol **Miembro**\n\n"
        f"**3.** Completa la **verificación Roblox**\n"
        f"　　→ Examen breve · el staff aprueba tu entrada\n"
        f"　　→ Rol **Comunidad** al ser aceptado/a\n\n"
        f"**4.** (Opcional) Si deseas personal sanitario\n"
        f"　　→ Revisa **postulaciones**\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 *Ve con calma. El staff está para orientarte.*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"¡Bienvenido/a a la familia de **{hospital}**! 🏥✨"
    )

    emb = discord.Embed(
        title=f"🏥  Bienvenido/a a {hospital}",
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
    emb.add_field(name="👥 Comunidad", value=f"`{total}` miembros", inline=True)
    emb.set_footer(text=f"{hospital}  ·  Te acompañamos en cada paso")
    return emb


def embed_bienvenida_dm(member: discord.Member) -> discord.Embed:
    hospital = _hospital()
    desc = (
        f"Hola, **{member.display_name}**.\n\n"
        f"Tu ingreso a **{hospital}** quedó registrado.\n\n"
        f"**Pasos recomendados**\n"
        f"**1.** Normativas del servidor\n"
        f"**2.** Aceptar reglas → **Miembro**\n"
        f"**3.** Verificación Roblox → **Comunidad**\n\n"
        f"Si tienes dudas, abre un ticket o pregunta en ayuda.\n\n"
        f"Que tengas una excelente estadía. 🩺"
    )
    emb = discord.Embed(
        title=f"💌 Acceso a {hospital}",
        description=desc,
        color=0x3498DB,
        timestamp=discord.utils.utcnow(),
    )
    emb.set_footer(text=f"{hospital} · Mensaje automático de bienvenida")
    return emb


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
    for name in ("bienvenida", "welcome", "ingresos", "general"):
        for ch in guild.text_channels:
            cn = (ch.name or "").lower()
            if name in cn:
                return ch
    return guild.system_channel


async def _on_member_join(member: discord.Member) -> None:
    if member.bot or not member.guild:
        return

    try:
        import asyncio
        import roles_setup

        await asyncio.sleep(1.2)
        n = await roles_setup.asignar_separadores_miembro(member)
        if n == 0:
            await asyncio.sleep(1.5)
            n = await roles_setup.asignar_separadores_miembro(member)
        print(f"[bienvenida] separadores +{n} → {member}", flush=True)
    except Exception as e:
        print(f"[bienvenida] separadores: {e}", flush=True)

    emb = embed_bienvenida(member)
    canal = _canal_bienvenida(member.guild)
    if canal:
        try:
            await canal.send(content=f"✨ {member.mention}", embed=emb)
        except Exception as e:
            print(f"[bienvenida] canal: {e}", flush=True)

    try:
        await member.send(embed=embed_bienvenida_dm(member))
    except Exception:
        pass


def registrar(bot: commands.Bot) -> None:
    bot.add_listener(_on_member_join, "on_member_join")

    @bot.tree.command(
        name="probar_bienvenida",
        description="[Staff] Envía una muestra del mensaje de bienvenida",
    )
    async def probar_bienvenida(inter: discord.Interaction):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        emb = embed_bienvenida(inter.user)
        await inter.response.send_message(
            content="*(Vista previa de bienvenida)*",
            embed=emb,
            ephemeral=True,
        )

    print("[bienvenida] OK — guía por puntos + /probar_bienvenida", flush=True)
