"""
paneles.py
==========
Componentes interactivos (botones, modales) en vez de solo comandos
de texto: sistema de tickets estilo "panel de moderación" y un panel
de acciones rápidas.

Estas vistas son PERSISTENTES (timeout=None) — se registran una vez
en bot_hospital.py (bot.add_view(...)) para que los botones sigan
funcionando aunque el bot se reinicie. No necesita edición.
"""

import asyncio

import discord
from discord import ui

import config
import economia
import permisos
from estilos import crear_embed


# ===========================================================================
# SISTEMA DE TICKETS
# ===========================================================================

async def _crear_ticket(interaction: discord.Interaction):
    guild = interaction.guild
    autor = interaction.user

    nombre_canal = f"ticket-{autor.name}".lower().replace(" ", "-")[:90]
    existente = discord.utils.get(guild.text_channels, name=nombre_canal)
    if existente:
        await interaction.response.send_message(
            f"⚠️ Ya tienes un ticket abierto: {existente.mention}", ephemeral=True
        )
        return

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        autor: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True
        ),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),
    }
    for key in config.TICKET_STAFF_KEYS:
        for role_id in permisos.ids_de_key(key):
            rol = guild.get_role(role_id)
            if rol:
                overwrites[rol] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, read_message_history=True
                )

    categoria = guild.get_channel(config.TICKET_CATEGORIA_ID) if config.TICKET_CATEGORIA_ID else None

    try:
        canal = await guild.create_text_channel(
            nombre_canal,
            overwrites=overwrites,
            category=categoria,
            topic=f"Ticket de {autor} (id:{autor.id})",
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ No tengo permisos para crear canales.", ephemeral=True
        )
        return

    embed = crear_embed(
        "info",
        "🎫 Nuevo Ticket",
        f"{autor.mention}, cuenta con detalle tu situación. El personal correspondiente te atenderá pronto.",
    )
    await canal.send(content=autor.mention, embed=embed, view=CerrarTicketView())
    await interaction.response.send_message(f"✅ Ticket creado: {canal.mention}", ephemeral=True)


class AbrirTicketView(ui.View):
    """Vista persistente con el botón para abrir un ticket."""

    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="🎫 Abrir Ticket", style=discord.ButtonStyle.primary, custom_id="hospital:abrir_ticket")
    async def abrir_ticket(self, interaction: discord.Interaction, button: ui.Button):
        await _crear_ticket(interaction)


class CerrarTicketView(ui.View):
    """Vista persistente con el botón para cerrar/eliminar el ticket."""

    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="🔒 Cerrar Ticket", style=discord.ButtonStyle.danger, custom_id="hospital:cerrar_ticket")
    async def cerrar_ticket(self, interaction: discord.Interaction, button: ui.Button):
        member = interaction.user
        if not isinstance(member, discord.Member):
            return

        topic = interaction.channel.topic or ""
        es_autor = f"id:{member.id}" in topic
        es_staff = permisos.member_tiene_alguna_key(member, *config.TICKET_STAFF_KEYS, "OWNER")

        if not (es_autor or es_staff):
            await interaction.response.send_message(
                "❌ No puedes cerrar este ticket.", ephemeral=True
            )
            return

        await interaction.response.send_message("🔒 Cerrando ticket en 5 segundos...")

        for target, overwrite in list(interaction.channel.overwrites.items()):
            if isinstance(target, discord.Member):
                overwrite.send_messages = False
                await interaction.channel.set_permissions(target, overwrite=overwrite)

        await asyncio.sleep(5)
        await interaction.channel.delete(reason=f"Ticket cerrado por {member}")


# ===========================================================================
# MODAL: formulario rápido (sin tener que escribir el comando completo)
# ===========================================================================

class ReporteRapidoModal(ui.Modal, title="Reporte / Formulario Rápido"):
    titulo_reporte = ui.TextInput(label="Título", max_length=100)
    contenido = ui.TextInput(label="Contenido", style=discord.TextStyle.paragraph, max_length=1000)

    async def on_submit(self, interaction: discord.Interaction):
        embed = crear_embed(
            "info", f"📄 {self.titulo_reporte.value}", str(self.contenido.value), autor=interaction.user
        )
        await interaction.response.send_message(embed=embed)


# ===========================================================================
# PANEL DE ACCIONES RÁPIDAS
# ===========================================================================

class PanelAccionesView(ui.View):
    """
    Vista persistente con botones de acceso rápido a las funciones más
    comunes del bot. Cada botón revisa el cargo (key) de quien lo pulsa
    antes de dejarlo continuar — la restricción por key sigue aplicando
    igual que en los comandos de texto.
    """

    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="📄 Nuevo formulario", style=discord.ButtonStyle.secondary, custom_id="hospital:formulario_rapido")
    async def formulario_rapido(self, interaction: discord.Interaction, button: ui.Button):
        member = interaction.user
        if not permisos.member_tiene_alguna_key(
            member, "DIRECTOR", "JEFE_DEPARTAMENTO", "JEFE_JUNTA_DIRECTIVA", "OWNER"
        ):
            await interaction.response.send_message(
                "❌ No tienes el cargo necesario para emitir formularios.", ephemeral=True
            )
            return
        await interaction.response.send_modal(ReporteRapidoModal())

    @ui.button(label="💰 Mi balance", style=discord.ButtonStyle.secondary, custom_id="hospital:mi_balance_btn")
    async def mi_balance(self, interaction: discord.Interaction, button: ui.Button):
        saldo = economia.obtener_balance(interaction.user.id)
        await interaction.response.send_message(f"💰 Tu balance: **${saldo:,.2f}**", ephemeral=True)

    @ui.button(label="🔑 Mis permisos", style=discord.ButtonStyle.secondary, custom_id="hospital:mis_permisos_btn")
    async def mis_permisos_btn(self, interaction: discord.Interaction, button: ui.Button):
        keys = permisos.keys_del_member(interaction.user)
        texto = ", ".join(keys) if keys else "Ninguna key asignada."
        await interaction.response.send_message(f"🔑 Tus keys: **{texto}**", ephemeral=True)

    @ui.button(label="🎫 Abrir Ticket", style=discord.ButtonStyle.primary, custom_id="hospital:abrir_ticket_panel")
    async def abrir_ticket_panel(self, interaction: discord.Interaction, button: ui.Button):
        await _crear_ticket(interaction)
