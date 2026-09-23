# -*- coding: utf-8 -*
"""limpiar_canal.py — Borrar mensajes de un canal (todos o N), sin límite de antigüedad."""
from __future__ import annotations

import asyncio
from typing import Optional
from datetime import datetime, timezone, timedelta

import discord
from discord import app_commands
from discord.ext import commands

import permisos


def _puede_limpiar(member: discord.Member) -> bool:
    if member.guild_permissions.manage_messages or member.guild_permissions.administrator:
        return True
    return permisos.member_tiene_alguna_key(
        member,
        "OWNER", "CO_OWNER", "DIRECTOR_GENERAL", "DIRECTOR_ADMINISTRATIVO",
        "DIRECTOR_DISCIPLINA", "SUPERVISOR", "STAFF_SERVIDOR",
    )


async def _borrar_mensajes(
    channel: discord.TextChannel,
    *,
    cantidad: Optional[int] = None,
) -> dict:
    limite = cantidad if cantidad is not None else 5000
    limite = max(1, min(int(limite), 5000))

    mensajes = []
    async for m in channel.history(limit=limite):
        mensajes.append(m)

    if not mensajes:
        return {"borrados": 0, "fallidos": 0, "bulk": 0, "individual": 0}

    corte = datetime.now(timezone.utc) - timedelta(days=13, hours=23)
    recientes = [m for m in mensajes if m.created_at >= corte]
    antiguos = [m for m in mensajes if m.created_at < corte]

    borrados = fallidos = bulk = individual = 0

    for i in range(0, len(recientes), 100):
        lote = recientes[i : i + 100]
        if len(lote) == 1:
            try:
                await lote[0].delete()
                borrados += 1
                individual += 1
            except Exception:
                fallidos += 1
        else:
            try:
                await channel.delete_messages(lote)
                borrados += len(lote)
                bulk += len(lote)
            except Exception:
                for m in lote:
                    try:
                        await m.delete()
                        borrados += 1
                        individual += 1
                    except Exception:
                        fallidos += 1
                    await asyncio.sleep(0.35)
        await asyncio.sleep(0.4)

    for m in antiguos:
        try:
            await m.delete()
            borrados += 1
            individual += 1
        except discord.NotFound:
            pass
        except Exception:
            fallidos += 1
        await asyncio.sleep(0.4)

    return {"borrados": borrados, "fallidos": fallidos, "bulk": bulk, "individual": individual}


def registrar(bot: commands.Bot) -> None:

    @bot.tree.command(
        name="limpiar",
        description="Borra mensajes del canal (todos o una cantidad). Incluye mensajes antiguos.",
    )
    @app_commands.describe(
        cantidad="Cuántos mensajes borrar (más recientes). Vacío = vaciar canal (máx. 5000).",
        canal="Canal a limpiar (por defecto: este canal).",
    )
    async def limpiar(
        inter: discord.Interaction,
        cantidad: Optional[app_commands.Range[int, 1, 5000]] = None,
        canal: Optional[discord.TextChannel] = None,
    ):
        if not isinstance(inter.user, discord.Member):
            await inter.response.send_message("❌ Solo en el servidor.", ephemeral=True)
            return
        if not _puede_limpiar(inter.user):
            await inter.response.send_message(
                "❌ Necesitas **Gestionar mensajes** o un rol de staff/dirección.",
                ephemeral=True,
            )
            return

        dest = canal or inter.channel
        if not isinstance(dest, discord.TextChannel):
            await inter.response.send_message("❌ Solo canales de texto.", ephemeral=True)
            return

        me = dest.guild.me if dest.guild else None
        if me and not dest.permissions_for(me).manage_messages:
            await inter.response.send_message(
                "❌ No tengo permiso **Gestionar mensajes** en ese canal.",
                ephemeral=True,
            )
            return

        if cantidad is None:
            aviso = (
                f"⚠️ Vas a **vaciar** {dest.mention} (hasta 5000 mensajes, "
                f"incluyendo antiguos). Puede tardar varios minutos."
            )
        else:
            aviso = f"Borrando hasta **{cantidad}** mensajes en {dest.mention}…"

        await inter.response.send_message(aviso, ephemeral=True)

        try:
            stats = await _borrar_mensajes(dest, cantidad=cantidad)
        except discord.Forbidden:
            await inter.followup.send("❌ Sin permisos para borrar en ese canal.", ephemeral=True)
            return
        except Exception as e:
            await inter.followup.send(f"❌ Error: {e}", ephemeral=True)
            return

        emb = discord.Embed(
            title="🧹 Canal limpio",
            description=f"Canal: {dest.mention}",
            color=0x2ECC71,
        )
        emb.add_field(name="Borrados", value=str(stats["borrados"]), inline=True)
        emb.add_field(name="Fallidos", value=str(stats["fallidos"]), inline=True)
        emb.add_field(
            name="Método",
            value=f"Bulk: {stats['bulk']} · Individual: {stats['individual']}",
            inline=False,
        )
        emb.set_footer(text=f"Por {inter.user.display_name}")
        await inter.followup.send(embed=emb, ephemeral=True)

        try:
            msg = await dest.send(
                f"🧹 **{stats['borrados']}** mensajes eliminados por {inter.user.mention}."
            )
            await asyncio.sleep(5)
            await msg.delete()
        except Exception:
            pass

    @bot.tree.command(
        name="limpiar_todo",
        description="Vacía por completo un canal (hasta 5000 msgs, sin límite de antigüedad).",
    )
    @app_commands.describe(canal="Canal a vaciar (por defecto: este).")
    async def limpiar_todo(
        inter: discord.Interaction,
        canal: Optional[discord.TextChannel] = None,
    ):
        if not isinstance(inter.user, discord.Member):
            await inter.response.send_message("❌ Solo en el servidor.", ephemeral=True)
            return
        if not _puede_limpiar(inter.user):
            await inter.response.send_message(
                "❌ Necesitas **Gestionar mensajes** o un rol de staff/dirección.",
                ephemeral=True,
            )
            return
        dest = canal or inter.channel
        if not isinstance(dest, discord.TextChannel):
            await inter.response.send_message("❌ Solo canales de texto.", ephemeral=True)
            return
        me = dest.guild.me if dest.guild else None
        if me and not dest.permissions_for(me).manage_messages:
            await inter.response.send_message(
                "❌ No tengo permiso **Gestionar mensajes** en ese canal.",
                ephemeral=True,
            )
            return

        await inter.response.send_message(
            f"⚠️ Vaciando {dest.mention} (máx. 5000, incluye mensajes antiguos)…",
            ephemeral=True,
        )
        try:
            stats = await _borrar_mensajes(dest, cantidad=None)
        except Exception as e:
            await inter.followup.send(f"❌ Error: {e}", ephemeral=True)
            return

        await inter.followup.send(
            embed=discord.Embed(
                title="🧹 Canal vaciado",
                description=(
                    f"{dest.mention}\n"
                    f"**Borrados:** {stats['borrados']} · **Fallidos:** {stats['fallidos']}\n"
                    f"Bulk: {stats['bulk']} · Individual: {stats['individual']}"
                ),
                color=0xE74C3C,
            ),
            ephemeral=True,
        )

    print("[limpiar_canal] OK")
