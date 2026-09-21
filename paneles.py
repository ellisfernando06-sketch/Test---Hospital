# -*- coding: utf-8 -*-
"""
paneles.py — Vistas persistentes de tickets y acciones.
"""
from __future__ import annotations

import asyncio

import discord
from discord import ui

import config
import permisos
import roles_store
from estilos import crear_embed


def _rol_staff_servidor(guild: discord.Guild):
    """Detecta el rol de Staff del Servidor por nombre."""
    nombres = ["🖥️ Staff del Servidor", "Staff del Servidor", "Staff", "STAFF"]
    for n in nombres:
        r = discord.utils.get(guild.roles, name=n)
        if r:
            return r
    rid = roles_store.obtener_id_key("STAFF_SERVIDOR")
    if rid:
        return guild.get_role(rid)
    return None


class AbrirTicketView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Abrir ticket", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="ticket_abrir")
    async def abrir(self, interaction: discord.Interaction, button: ui.Button):
        guild = interaction.guild
        if not guild:
            return
        cat = guild.get_channel(config.TICKET_CATEGORIA_ID) if config.TICKET_CATEGORIA_ID else None
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }

        for key in config.TICKET_STAFF_KEYS:
            if key == "DIRECTOR":
                for dk in config.DIRECTOR_KEYS:
                    rid = roles_store.obtener_id_key(dk)
                    if rid:
                        rol = guild.get_role(rid)
                        if rol:
                            overwrites[rol] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
            else:
                rid = roles_store.obtener_id_key(key)
                if rid:
                    rol = guild.get_role(rid)
                    if rol:
                        overwrites[rol] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        staff_role = _rol_staff_servidor(guild)
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        nombre = f"ticket-{interaction.user.name}"[:90]
        try:
            canal = await guild.create_text_channel(
                nombre,
                category=cat if isinstance(cat, discord.CategoryChannel) else None,
                overwrites=overwrites,
                reason=f"Ticket de {interaction.user}",
            )
        except discord.Forbidden:
            await interaction.response.send_message("❌ No tengo permisos para crear canales.", ephemeral=True)
            return

        embed = crear_embed(
            "info",
            "🎫 Ticket abierto",
            f"Hola {interaction.user.mention}, describe tu consulta. Un miembro del staff te atenderá.\n\n"
            f"Puedes adjuntar **imágenes, videos o texto** como evidencia.",
        )

        content_parts = [interaction.user.mention]
        if staff_role:
            content_parts.append(staff_role.mention)

        await canal.send(
            content=" ".join(content_parts),
            embed=embed,
            view=CerrarTicketView(),
        )
        await interaction.response.send_message(f"✅ Ticket creado: {canal.mention}", ephemeral=True)


class CerrarTicketView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Cerrar ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ticket_cerrar")
    async def cerrar(self, interaction: discord.Interaction, button: ui.Button):
        if not isinstance(interaction.user, discord.Member):
            return
        if not permisos.member_tiene_alguna_key(interaction.user, *config.TICKET_STAFF_KEYS, "OWNER"):
            if not interaction.channel or not str(interaction.channel.name).startswith(("ticket-", "apelacion-")):
                await interaction.response.send_message("❌ Solo staff puede cerrar tickets.", ephemeral=True)
                return
        await interaction.response.send_message("🔒 Cerrando ticket en 3 segundos…")
        await asyncio.sleep(3)
        try:
            await interaction.channel.delete(reason=f"Cerrado por {interaction.user}")
        except Exception:
            pass


class PanelAccionesView(ui.View):
    """Panel genérico de acciones rápidas (placeholder extensible)."""
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Mi expediente", style=discord.ButtonStyle.secondary, emoji="📁", custom_id="panel_mi_expediente")
    async def mi_exp(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message(
            "Usa el comando `/mi_expediente` para ver tu expediente completo.",
            ephemeral=True,
        )
