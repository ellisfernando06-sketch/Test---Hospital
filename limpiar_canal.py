# -*- coding: utf-8 -*
"""limpiar_canal.py — /limpiar /limpiar_todo /sincronizar_comandos."""
from __future__ import annotations

import asyncio
from typing import Optional
from datetime import datetime, timezone, timedelta

import discord
from discord import app_commands
from discord.ext import commands

try:
    import permisos
except Exception:
    permisos = None

GUILD_ID = 1381360019467014184


def _puede_limpiar(member: discord.Member) -> bool:
    if member.guild_permissions.manage_messages or member.guild_permissions.administrator:
        return True
    if permisos is None:
        return member.guild_permissions.manage_channels
    try:
        return permisos.member_tiene_alguna_key(
            member,
            "OWNER", "CO_OWNER", "DIRECTOR_GENERAL", "DIRECTOR_ADMINISTRATIVO",
            "DIRECTOR_DISCIPLINA", "SUPERVISOR", "STAFF_SERVIDOR",
        )
    except Exception:
        return False


async def _borrar_mensajes(channel: discord.TextChannel, *, cantidad: Optional[int] = None) -> dict:
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
    for nombre in ("limpiar", "limpiar_todo", "sincronizar_comandos"):
        try:
            bot.tree.remove_command(nombre)
        except Exception:
            pass

    @bot.tree.command(name="limpiar", description="Borra N mensajes o vacia el canal (incluye antiguos).")
    @app_commands.describe(
        cantidad="Cuantos borrar (1-5000). Vacio = hasta 5000.",
        canal="Canal (por defecto: este).",
    )
    async def limpiar(
        inter: discord.Interaction,
        cantidad: Optional[app_commands.Range[int, 1, 5000]] = None,
        canal: Optional[discord.TextChannel] = None,
    ):
        if not isinstance(inter.user, discord.Member):
            await inter.response.send_message("Solo en el servidor.", ephemeral=True)
            return
        if not _puede_limpiar(inter.user):
            await inter.response.send_message("Necesitas Gestionar mensajes o staff.", ephemeral=True)
            return
        dest = canal or inter.channel
        if not isinstance(dest, discord.TextChannel):
            await inter.response.send_message("Solo canales de texto.", ephemeral=True)
            return
        me = dest.guild.me if dest.guild else None
        if me and not dest.permissions_for(me).manage_messages:
            await inter.response.send_message("No tengo Gestionar mensajes.", ephemeral=True)
            return
        if cantidad is None:
            aviso = f"Vaciando {dest.mention} (max. 5000)..."
        else:
            aviso = f"Borrando hasta {cantidad} mensajes en {dest.mention}..."
        await inter.response.send_message(aviso, ephemeral=True)
        try:
            stats = await _borrar_mensajes(dest, cantidad=cantidad)
        except Exception as e:
            await inter.followup.send(f"Error: {e}", ephemeral=True)
            return
        await inter.followup.send(
            embed=discord.Embed(
                title="Limpieza completada",
                description=f"{dest.mention}\nBorrados: {stats['borrados']} | Fallidos: {stats['fallidos']}",
                color=0xE67E22,
            ),
            ephemeral=True,
        )

    @bot.tree.command(name="limpiar_todo", description="Vacia el canal por completo (hasta 5000 msgs).")
    @app_commands.describe(canal="Canal a vaciar (por defecto: este).")
    async def limpiar_todo(
        inter: discord.Interaction,
        canal: Optional[discord.TextChannel] = None,
    ):
        if not isinstance(inter.user, discord.Member):
            await inter.response.send_message("Solo en el servidor.", ephemeral=True)
            return
        if not _puede_limpiar(inter.user):
            await inter.response.send_message("Necesitas Gestionar mensajes o staff.", ephemeral=True)
            return
        dest = canal or inter.channel
        if not isinstance(dest, discord.TextChannel):
            await inter.response.send_message("Solo canales de texto.", ephemeral=True)
            return
        me = dest.guild.me if dest.guild else None
        if me and not dest.permissions_for(me).manage_messages:
            await inter.response.send_message("No tengo Gestionar mensajes.", ephemeral=True)
            return
        await inter.response.send_message(f"Vaciando {dest.mention}...", ephemeral=True)
        try:
            stats = await _borrar_mensajes(dest, cantidad=None)
        except Exception as e:
            await inter.followup.send(f"Error: {e}", ephemeral=True)
            return
        await inter.followup.send(
            embed=discord.Embed(
                title="Canal vaciado",
                description=f"{dest.mention}\nBorrados: {stats['borrados']}",
                color=0xE74C3C,
            ),
            ephemeral=True,
        )

    @bot.tree.command(
        name="sincronizar_comandos",
        description="Restaura TODOS los slash commands del servidor (admin).",
    )
    async def sincronizar_comandos(inter: discord.Interaction):
        if not isinstance(inter.user, discord.Member):
            await inter.response.send_message("Solo en el servidor.", ephemeral=True)
            return
        ok = inter.user.guild_permissions.administrator
        if not ok and permisos is not None:
            try:
                ok = permisos.member_tiene_alguna_key(
                    inter.user, "OWNER", "CO_OWNER", "DIRECTOR_GENERAL"
                )
            except Exception:
                ok = False
        if not ok:
            await inter.response.send_message("Solo administracion / owner.", ephemeral=True)
            return
        await inter.response.defer(ephemeral=True)
        try:
            fn = getattr(bot, "_hospital_sync_todo", None)
            if callable(fn):
                names = await fn("manual")
            else:
                g = discord.Object(id=GUILD_ID)
                try:
                    bot.tree.clear_commands(guild=g)
                except Exception:
                    pass
                bot.tree.copy_global_to(guild=g)
                synced = await bot.tree.sync(guild=g)
                names = sorted(c.name for c in synced)
            await inter.followup.send(
                f"**{len(names)}** comandos restaurados:\n"
                f"`{'`, `'.join(names[:80])}`"
                + ("..." if len(names) > 80 else ""),
                ephemeral=True,
            )
        except Exception as e:
            await inter.followup.send(f"Error: {e}", ephemeral=True)

    print("[limpiar_canal] OK")
