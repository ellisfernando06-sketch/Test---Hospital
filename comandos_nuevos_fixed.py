# -*- coding: utf-8 -*-
"""comandos_nuevos — restored"""
from __future__ import annotations
from datetime import timedelta
from typing import Optional, List
import discord
from discord import app_commands
from discord.ext import commands
import config, permisos, registros, sanciones, verificacion
from estilos import crear_embed
from permisos import require_key

def registrar(bot: commands.Bot) -> None:
    @bot.tree.command(name="sancionar", description="Aplica una sancion con historial y log")
    @app_commands.describe(usuario="Usuario", tipo="Tipo", motivo="Motivo", evidencia_texto="Texto evidencia", evidencia_archivo="Evidencia 1", evidencia_archivo2="Evidencia 2", evidencia_archivo3="Evidencia 3", duracion="Duracion")
    @app_commands.choices(tipo=[
        app_commands.Choice(name="Advertencia", value="Advertencia"),
        app_commands.Choice(name="Sancion interna", value="Sanción interna"),
        app_commands.Choice(name="Sancion disciplinaria", value="Sanción disciplinaria"),
        app_commands.Choice(name="Sancion administrativa", value="Sanción administrativa"),
        app_commands.Choice(name="Suspension", value="Suspensión"),
        app_commands.Choice(name="Otra", value="Otra"),
    ])
    @require_key("DIRECTOR", "DIRECTOR_DISCIPLINA", "DIRECTOR_ADMINISTRATIVO", "DIRECTOR_RRHH", "DIRECTOR_GENERAL", "SUPERVISOR", "OWNER", "CO_OWNER")
    async def sancionar(interaction: discord.Interaction, usuario: discord.Member, tipo: app_commands.Choice[str], motivo: str, evidencia_texto: str = "", evidencia_archivo: Optional[discord.Attachment] = None, evidencia_archivo2: Optional[discord.Attachment] = None, evidencia_archivo3: Optional[discord.Attachment] = None, duracion: str = ""):
        if not permisos.puede_actuar_sobre(interaction.user, usuario):
            await interaction.response.send_message("No puedes sancionar a ese usuario.", ephemeral=True)
            return
        urls = [a.url for a in (evidencia_archivo, evidencia_archivo2, evidencia_archivo3) if a]
        reg = sanciones.registrar_sancion(usuario.id, tipo.value, motivo, interaction.user.id, evidencia_texto, urls, duracion)
        registros.registrar_evento_cargo(usuario.id, "sancion", f"[{tipo.value}] {motivo}", interaction.user.id)
        embed = sanciones.embed_sancion(reg, interaction.guild)
        await interaction.response.send_message(embed=embed)
        await sanciones.enviar_log_sancion(bot, embed)

    @bot.tree.command(name="verificar_roblox", description="Envia DM de verificacion Roblox")
    @app_commands.describe(usuario="Visitante (opcional)")
    @require_key("DIRECTOR_ADMINISTRATIVO", "DIRECTOR_GENERAL", "DIRECTOR_RRHH", "OWNER", "CO_OWNER", "SUPERVISOR")
    async def verificar_roblox(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("Solo en servidor.", ephemeral=True)
            return
        r_vis = verificacion.rol_visitante(guild)
        r_miem = verificacion.rol_miembro(guild)
        if not r_vis or not r_miem:
            await interaction.response.send_message("Faltan roles Visitante o Miembro.", ephemeral=True)
            return
        if usuario:
            ok = await verificacion.enviar_dm_verificacion(usuario, interaction.user)
            await interaction.response.send_message("DM enviado." if ok else "No se pudo enviar DM.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        enviados = sum(1 for m in list(guild.members)[:25] if r_vis in m.roles and not m.bot and await verificacion.enviar_dm_verificacion(m, interaction.user))
        await interaction.followup.send(f"DMs enviados: {enviados}", ephemeral=True)

    @bot.tree.command(name="ver_roblox", description="Consulta Roblox verificado")
    @app_commands.describe(usuario="Usuario")
    @require_key("STAFF", "SUPERVISOR", "DIRECTOR", "OWNER")
    async def ver_roblox(interaction: discord.Interaction, usuario: discord.Member):
        info = verificacion.obtener_roblox_completo(usuario.id)
        if not info:
            await interaction.response.send_message(f"{usuario.mention} no tiene Roblox verificado.", ephemeral=True)
            return
        from estilos import embed_roblox_verificacion
        data = {"name": info.get("roblox"), "id": info.get("roblox_id"), "displayName": info.get("displayName") or info.get("roblox"), "avatar_url": info.get("avatar_url")}
        embed = embed_roblox_verificacion(usuario, data, None, True)
        embed.title = "Roblox verificado"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="mi_sanciones", description="Tu historial de sanciones")
    async def mi_sanciones(interaction: discord.Interaction):
        lista = sanciones.sanciones_de(interaction.user.id)
        embed = sanciones.embed_historial(interaction.user, lista)
        await interaction.response.send_message(embed=embed, ephemeral=True)
