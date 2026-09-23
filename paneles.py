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


def _miembros_autorizados_ticket(guild: discord.Guild) -> list:
    """Miembros con roles/keys de staff o personal (máx. 25 para el menú)."""
    keys_ok = set(getattr(config, "TICKET_STAFF_KEYS", []) or [])
    keys_ok.update({"OWNER", "CO_OWNER", "STAFF", "STAFF_SERVIDOR", "SUPERVISOR", "RESIDENTE"})
    for dk in getattr(config, "DIRECTOR_KEYS", []) or []:
        keys_ok.add(dk)

    role_ids = set()
    for key in keys_ok:
        rid = roles_store.obtener_id_key(key)
        if rid:
            role_ids.add(rid)
    for rol in guild.roles:
        n = (rol.name or "").lower()
        if any(x in n for x in ("director", "supervisor", "staff", "rrhh", "médico", "medico", "enfermer")):
            role_ids.add(rol.id)

    vistos = set()
    miembros = []
    for member in guild.members:
        if member.bot or member.id in vistos:
            continue
        if any(r.id in role_ids for r in member.roles):
            vistos.add(member.id)
            miembros.append(member)
            if len(miembros) >= 25:
                break
    miembros.sort(key=lambda m: (m.display_name or m.name).lower())
    return miembros


def _puede_gestionar_ticket(user: discord.abc.User) -> bool:
    if not isinstance(user, discord.Member):
        return False
    return permisos.member_tiene_alguna_key(user, *config.TICKET_STAFF_KEYS, "OWNER")


class TicketAnadirSelect(ui.Select):
    """Menú desplegable de personal autorizado para añadir al ticket."""

    def __init__(self, guild: discord.Guild):
        miembros = _miembros_autorizados_ticket(guild)
        options = []
        for m in miembros:
            options.append(
                discord.SelectOption(
                    label=(m.display_name or m.name)[:100],
                    value=str(m.id),
                    description=f"@{m.name}"[:100],
                    emoji="👤",
                )
            )
        if not options:
            options = [
                discord.SelectOption(
                    label="No hay personal autorizado detectado",
                    value="none",
                    description="Usa el selector libre de usuarios",
                )
            ]
        super().__init__(
            placeholder="👥 Elige una persona autorizada…",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        if not _puede_gestionar_ticket(interaction.user):
            await interaction.response.send_message("❌ Solo staff autorizado.", ephemeral=True)
            return
        val = self.values[0] if self.values else None
        if not val or val == "none":
            await interaction.response.send_message(
                "❌ No hay personas disponibles. Usa el selector libre.",
                ephemeral=True,
            )
            return
        try:
            uid = int(val)
        except ValueError:
            await interaction.response.send_message("❌ ID inválido.", ephemeral=True)
            return
        member = interaction.guild.get_member(uid) if interaction.guild else None
        if not member:
            await interaction.response.send_message("❌ Usuario no encontrado.", ephemeral=True)
            return
        try:
            await interaction.channel.set_permissions(
                member, view_channel=True, send_messages=True, attach_files=True
            )
        except discord.Forbidden:
            await interaction.response.send_message("❌ No puedo modificar permisos.", ephemeral=True)
            return
        await interaction.response.send_message(f"✅ {member.mention} añadido al ticket.")


class TicketAnadirUserSelect(ui.UserSelect):
    """Selector nativo de Discord para cualquier usuario."""

    def __init__(self):
        super().__init__(
            placeholder="🔍 O busca cualquier usuario del servidor…",
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction):
        if not _puede_gestionar_ticket(interaction.user):
            await interaction.response.send_message("❌ Solo staff autorizado.", ephemeral=True)
            return
        users = self.values
        if not users:
            await interaction.response.send_message("❌ No seleccionaste a nadie.", ephemeral=True)
            return
        user = users[0]
        member = interaction.guild.get_member(user.id) if interaction.guild else None
        if not member:
            await interaction.response.send_message(
                "❌ Ese usuario no está en el servidor.", ephemeral=True
            )
            return
        try:
            await interaction.channel.set_permissions(
                member, view_channel=True, send_messages=True, attach_files=True
            )
        except discord.Forbidden:
            await interaction.response.send_message("❌ No puedo modificar permisos.", ephemeral=True)
            return
        await interaction.response.send_message(f"✅ {member.mention} añadido al ticket.")


class TicketAnadirView(ui.View):
    def __init__(self, guild: discord.Guild):
        super().__init__(timeout=120)
        self.add_item(TicketAnadirSelect(guild))
        self.add_item(TicketAnadirUserSelect())


class CerrarTicketView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Añadir usuario", style=discord.ButtonStyle.secondary, emoji="👥", custom_id="ticket_adduser")
    async def adduser(self, interaction: discord.Interaction, button: ui.Button):
        if not isinstance(interaction.user, discord.Member):
            return
        if not _puede_gestionar_ticket(interaction.user):
            await interaction.response.send_message("❌ Solo staff autorizado.", ephemeral=True)
            return
        if not interaction.guild:
            await interaction.response.send_message("❌ Solo en el servidor.", ephemeral=True)
            return
        await interaction.response.send_message(
            "👥 **Añadir persona al ticket**\n"
            "• Menú superior: personal autorizado (roles de staff / hospital)\n"
            "• Menú inferior: buscar cualquier usuario del servidor",
            view=TicketAnadirView(interaction.guild),
            ephemeral=True,
        )

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
