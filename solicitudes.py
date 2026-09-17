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
                # BUG CORREGIDO: aquí se usaba interaction.followup.send(...).
                # Todos los llamadores de enviar_solicitud() lo hacen ANTES de
                # responder la interacción (interaction.response.send_message
                # se llama después). Un followup solo funciona si ya se envió
                # una respuesta inicial (send_message o defer); si no, Discord
                # rechaza el envío (el except Exception lo tragaba en
                # silencio y el aviso simplemente nunca llegaba a nadie).
                # Se usa interaction.channel.send() en su lugar, que no
                # depende del estado de la respuesta de la interacción.
                try:
                    await interaction.channel.send(
                        content=f"{rol.mention} — nueva solicitud",
                        embed=embed,
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

    def __init__(self, departamento_slug: str, departamento_nombre: str, asunto_sugerido: str = ""):
        super().__init__()
        self.departamento_slug = departamento_slug
        self.departamento_nombre = departamento_nombre
        # BUG CORREGIDO: bot_hospital.py llamaba a este modal como
        # CartaSolicitudModal(asunto, departamento.value, departamento.name),
        # es decir, con 3 argumentos y en el orden equivocado respecto a este
        # __init__ (que solo aceptaba 2). Eso hacía que /carta_solicitud
        # truene con TypeError apenas se ejecutaba. Ahora el __init__ acepta
        # también el "asunto" que el usuario ya escribió en el comando y lo
        # precarga como valor por defecto del campo del modal, en vez de
        # pedírselo dos veces.
        if asunto_sugerido:
            self.asunto.default = asunto_sugerido[:100]

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

    def __init__(self, usuario: discord.Member, cargo_actual: str, cargo_propuesto: str):
        super().__init__()
        # BUG CORREGIDO: esta clase no tenía __init__ propio, pero
        # bot_hospital.py la instanciaba como
        # SolicitudDescargoModal(usuario, cargo_actual, cargo_propuesto).
        # discord.ui.Modal.__init__ no acepta argumentos posicionales, así
        # que /solicitud_descargo truena con TypeError apenas se ejecuta.
        # Además, aunque no tronara, esos tres datos nunca se usaban en el
        # mensaje final. Ahora se guardan y se incluyen en el embed.
        self.usuario = usuario
        self.cargo_actual = cargo_actual
        self.cargo_propuesto = cargo_propuesto

    async def on_submit(self, interaction: discord.Interaction):
        embed = crear_embed("aviso", "📝 Solicitud de descargo", str(self.motivo), autor=interaction.user)
        embed.add_field(name="Afectado", value=self.usuario.mention)
        embed.add_field(name="Cargo actual", value=self.cargo_actual)
        embed.add_field(name="Cargo propuesto", value=self.cargo_propuesto)
        await enviar_solicitud(interaction, config.RRHH_KEY, embed, "log_solicitudes")
        await interaction.response.send_message("✅ Solicitud de descargo enviada a RRHH.", ephemeral=True)


class SolicitudPermisoModal(discord.ui.Modal, title="Solicitud de permiso"):
    desde = discord.ui.TextInput(label="Desde (fecha)", max_length=40)
    hasta = discord.ui.TextInput(label="Hasta (fecha)", max_length=40)
    motivo = discord.ui.TextInput(label="Motivo", style=discord.TextStyle.paragraph, max_length=500)

    def __init__(self, departamento_slug: str, departamento_nombre: str):
        super().__init__()
        # BUG CORREGIDO: igual que arriba, esta clase no tenía __init__
        # propio pero bot_hospital.py la instanciaba con 2 argumentos
        # posicionales (slug, nombre) → TypeError al ejecutar
        # /solicitud_permiso. Además la solicitud siempre se enviaba a
        # RRHH sin importar el departamento, contradiciendo la descripción
        # del comando ("se envía a tu propio departamento"). Ahora se
        # guarda el departamento y se usa para elegir el destinatario.
        self.departamento_slug = departamento_slug
        self.departamento_nombre = departamento_nombre

    async def on_submit(self, interaction: discord.Interaction):
        embed = crear_embed("aviso", "🗓️ Solicitud de permiso", str(self.motivo), autor=interaction.user)
        embed.add_field(name="Desde", value=str(self.desde))
        embed.add_field(name="Hasta", value=str(self.hasta))
        embed.add_field(name="Departamento", value=self.departamento_nombre)
        if self.departamento_slug and self.departamento_slug in config.DEPARTAMENTOS:
            dest = config.DEPARTAMENTOS[self.departamento_slug]["director_key"]
        else:
            dest = config.RRHH_KEY
        await enviar_solicitud(interaction, dest, embed, "log_solicitudes")
        await interaction.response.send_message("✅ Solicitud de permiso enviada.", ephemeral=True)
        
