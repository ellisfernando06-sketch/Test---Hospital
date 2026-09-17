# -*- coding: utf-8 -*-
"""
solicitudes.py — Envío de solicitudes a keys (con escalada).
"""
from __future__ import annotations

from typing import Optional

import discord

import config
import permisos
import roles_store
from estilos import crear_embed


async def enviar_solicitud(
    interaction: discord.Interaction,
    key_destino: str,
    embed: discord.Embed,
    canal_log: Optional[str] = None,
) -> None:
    """
    Envía el embed a un canal de log (si existe) y menciona / intenta avisar
    a quien tenga la key destino. Si nadie la tiene, escala por ESCALADA_SOLICITUDES.
    """
    guild = interaction.guild
    if not guild:
        return

    # Log opcional
    if canal_log:
        canal_id = config.CANALES.get(canal_log)
        if canal_id:
            canal = guild.get_channel(canal_id)
            if canal:
                try:
                    await canal.send(embed=embed)
                except discord.Forbidden:
                    pass

    # Buscar miembros con la key (o escalada)
    keys_a_probar = [key_destino] + [k for k in config.ESCALADA_SOLICITUDES if k != key_destino]
    mencionado = False
    for key in keys_a_probar:
        rid = roles_store.obtener_id_key(key)
        if not rid:
            continue
        rol = guild.get_role(rid)
        if not rol:
            continue
        miembros = [m for m in guild.members if rol in m.roles]
        if miembros:
            # Intentar DM al primero online; si no, mencionar en el canal de interacción
            for m in miembros:
                try:
                    await m.send(f"📬 Nueva solicitud dirigida a **{config.nombre_key(key)}**:", embed=embed)
                    mencionado = True
                    break
                except discord.Forbidden:
                    continue
            if not mencionado:
                # Fallback: responder en el canal con mención
                try:
                    await interaction.followup.send(
                        content=f"{rol.mention} — nueva solicitud",
                        embed=embed,
                        ephemeral=False,
                    )
                    mencionado = True
                except Exception:
                    pass
            break

    if not mencionado:
        # Último recurso: solo log general
        pass


# Modales genéricos usados por el bot principal
class CartaSolicitudModal(discord.ui.Modal, title="Carta de solicitud"):
    asunto = discord.ui.TextInput(label="Asunto", max_length=100)
    contenido = discord.ui.TextInput(label="Contenido", style=discord.TextStyle.paragraph, max_length=1500)

    def __init__(self, departamento_slug: str, departamento_nombre: str):
        super().__init__()
        self.departamento_slug = departamento_slug
        self.departamento_nombre = departamento_nombre

    async def on_submit(self, interaction: discord.Interaction):
        if self.departamento_slug and self.departamento_slug in config.DEPARTAMENTOS:
            dest = config.DEPARTAMENTOS[self.departamento_slug]["director_key"]
        else:
            dest = config.KEY_SOLICITUD_GENERAL
        embed = crear_embed("info", f"✉️ Solicitud: {self.asunto}", str(self.contenido), autor=interaction.user)
        embed.add_field(name="Destino", value=self.departamento_nombre)
        await enviar_solicitud(interaction, dest, embed, "log_solicitudes")
        await interaction.response.send_message("✅ Solicitud enviada.", ephemeral=True)


class SolicitudDescargoModal(discord.ui.Modal, title="Solicitud de descargo"):
    motivo = discord.ui.TextInput(label="Motivo del descargo", style=discord.TextStyle.paragraph, max_length=1000)

    async def on_submit(self, interaction: discord.Interaction):
        embed = crear_embed("aviso", "📝 Solicitud de descargo", str(self.motivo), autor=interaction.user)
        await enviar_solicitud(interaction, config.RRHH_KEY, embed, "log_solicitudes")
        await interaction.response.send_message("✅ Solicitud de descargo enviada a RRHH.", ephemeral=True)


class SolicitudPermisoModal(discord.ui.Modal, title="Solicitud de permiso"):
    desde = discord.ui.TextInput(label="Desde (fecha)", max_length=40)
    hasta = discord.ui.TextInput(label="Hasta (fecha)", max_length=40)
    motivo = discord.ui.TextInput(label="Motivo", style=discord.TextStyle.paragraph, max_length=500)

    async def on_submit(self, interaction: discord.Interaction):
        embed = crear_embed("aviso", "🗓️ Solicitud de permiso", str(self.motivo), autor=interaction.user)
        embed.add_field(name="Desde", value=str(self.desde))
        embed.add_field(name="Hasta", value=str(self.hasta))
        await enviar_solicitud(interaction, config.RRHH_KEY, embed, "log_solicitudes")
        await interaction.response.send_message("✅ Solicitud de permiso enviada.", ephemeral=True)
