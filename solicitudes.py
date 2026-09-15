"""
solicitudes.py
==============
Formularios rellenables (modales de Discord) para:

  1. Carta de Solicitud general -> se envía por DM al DIRECTOR del
     departamento elegido (o al Presidente del Consejo si se marca
     "General / Junta Directiva").
  2. Solicitud de Descargo/Degradación -> SIEMPRE se envía por DM al
     encargado de Recursos Humanos (config.RRHH_KEY), sin importar el
     departamento del afectado.
  3. Solicitud de Permiso/Licencia -> se envía por DM al director del
     departamento AL QUE PERTENECE quien la solicita (detectado
     automáticamente por sus roles).

Regla general de enrutamiento: cada solicitud sube a la entidad
superior encargada de esa sección. Si nadie tiene esa key asignada
todavía, sube un nivel más (Presidente del Consejo) y, en última
instancia, al Owner, para que ninguna solicitud se pierda. Si ni así
hay alguien disponible, o si el DM falla porque la persona tiene los
mensajes privados cerrados, la solicitud queda publicada en el canal
de registro correspondiente (config.CANALES). No necesita edición.

`enviar_solicitud()` y `miembros_encargados()` son públicas y también
las reutilizan quejas.py y postulaciones.py para enrutar con la misma
lógica de "sube un nivel si no hay nadie disponible".
"""

import discord
from discord import ui

import config
import permisos
from estilos import crear_embed


async def miembros_encargados(guild: discord.Guild, key: str) -> list:
    """Devuelve los miembros con `key`; si no hay nadie, sube de nivel."""
    miembros = permisos.miembros_con_key(guild, key)
    if miembros:
        return miembros
    if key != "JEFE_JUNTA_DIRECTIVA":
        miembros = permisos.miembros_con_key(guild, "JEFE_JUNTA_DIRECTIVA")
    if miembros:
        return miembros
    return permisos.miembros_con_key(guild, "OWNER")


async def enviar_solicitud(interaction: discord.Interaction, key_destino: str, embed: discord.Embed, canal_log: str):
    guild = interaction.guild
    destinatarios = await miembros_encargados(guild, key_destino)

    entregados = 0
    for miembro in destinatarios:
        try:
            await miembro.send(embed=embed)
            entregados += 1
        except discord.Forbidden:
            continue

    canal_id = config.CANALES.get(canal_log)
    if canal_id:
        canal = interaction.client.get_channel(canal_id)
        if canal:
            try:
                await canal.send(embed=embed)
            except discord.Forbidden:
                pass

    if entregados:
        await interaction.response.send_message(
            f"✅ Tu solicitud fue enviada por DM a {entregados} encargado(s).", ephemeral=True
        )
    elif canal_id:
        await interaction.response.send_message(
            "⚠️ No se pudo entregar por DM (mensajes privados cerrados o nadie con ese cargo "
            "asignado todavía), pero quedó publicada en el canal de registro correspondiente.",
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            "⚠️ No hay nadie con el cargo encargado de recibir esto todavía, y no hay canal de "
            "registro configurado en config.CANALES. Avisa a un Director o al Owner.",
            ephemeral=True,
        )


# ===========================================================================
# 1) CARTA DE SOLICITUD GENERAL
# ===========================================================================
class CartaSolicitudModal(ui.Modal):
    contenido = ui.TextInput(
        label="Contenido de la solicitud",
        style=discord.TextStyle.paragraph,
        max_length=1500,
        placeholder="Explica con detalle tu solicitud...",
    )

    def __init__(self, asunto: str, departamento_slug: str, departamento_nombre: str):
        super().__init__(title=f"Solicitud — {departamento_nombre}"[:45])
        self.asunto = asunto
        self.departamento_slug = departamento_slug
        self.departamento_nombre = departamento_nombre

    async def on_submit(self, interaction: discord.Interaction):
        embed = crear_embed(
            "info", f"📨 Solicitud: {self.asunto}", str(self.contenido.value), autor=interaction.user
        )
        embed.add_field(name="Dirigida a", value=self.departamento_nombre)
        embed.add_field(name="Solicitante", value=interaction.user.mention)

        if self.departamento_slug == "general":
            key_destino = config.SOLICITUD_GENERAL_KEY
        else:
            key_destino = config.DEPARTAMENTOS[self.departamento_slug]["director_key"]

        await enviar_solicitud(interaction, key_destino, embed, "log_documentos")


# ===========================================================================
# 2) SOLICITUD DE DESCARGO / DEGRADACIÓN (siempre a RRHH)
# ===========================================================================
class SolicitudDescargoModal(ui.Modal, title="Solicitud de Descargo"):
    motivo = ui.TextInput(
        label="Motivo del descargo",
        style=discord.TextStyle.paragraph,
        max_length=1500,
        placeholder="Explica por qué se solicita el descargo/degradación...",
    )

    def __init__(self, usuario: discord.Member, cargo_actual: str, cargo_propuesto: str):
        super().__init__()
        self.usuario = usuario
        self.cargo_actual = cargo_actual
        self.cargo_propuesto = cargo_propuesto

    async def on_submit(self, interaction: discord.Interaction):
        embed = crear_embed(
            "aviso", "📉 Solicitud de Descargo/Degradación", str(self.motivo.value), autor=interaction.user
        )
        embed.add_field(name="Afectado", value=self.usuario.mention)
        embed.add_field(name="Cargo actual", value=self.cargo_actual)
        embed.add_field(name="Cargo propuesto", value=self.cargo_propuesto)
        embed.add_field(name="Solicitado por", value=interaction.user.mention, inline=False)

        await enviar_solicitud(interaction, config.RRHH_KEY, embed, "log_personal")


# ===========================================================================
# 3) SOLICITUD DE PERMISO / LICENCIA (rutea al director del propio depto.)
# ===========================================================================
class SolicitudPermisoModal(ui.Modal, title="Solicitud de Permiso/Licencia"):
    fechas = ui.TextInput(label="Fechas (desde - hasta)", placeholder="Ej: 20/09 al 25/09", max_length=100)
    motivo = ui.TextInput(label="Motivo", style=discord.TextStyle.paragraph, max_length=1000)

    def __init__(self, departamento_slug: str, departamento_nombre: str):
        super().__init__()
        self.departamento_slug = departamento_slug
        self.departamento_nombre = departamento_nombre

    async def on_submit(self, interaction: discord.Interaction):
        embed = crear_embed(
            "aviso", "📝 Solicitud de Permiso/Licencia", str(self.motivo.value), autor=interaction.user
        )
        embed.add_field(name="Departamento", value=self.departamento_nombre)
        embed.add_field(name="Fechas", value=str(self.fechas.value))
        embed.add_field(name="Solicitante", value=interaction.user.mention)

        if self.departamento_slug == "general":
            key_destino = config.SOLICITUD_GENERAL_KEY
        else:
            key_destino = config.DEPARTAMENTOS[self.departamento_slug]["director_key"]

        await enviar_solicitud(interaction, key_destino, embed, "log_personal")
