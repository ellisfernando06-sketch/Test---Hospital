# -*- coding: utf-8 -*
"""centro_solicitudes_ui.py — Formularios, tickets y comandos del Centro de Solicitudes."""
from __future__ import annotations

import asyncio
from typing import Dict, Optional

import discord
from discord import ui, app_commands
from discord.ext import commands

import config
import permisos
import roles_store
from centro_solicitudes import (
    CATEGORIAS, ESTADOS, PRIORIDADES,
    embed_panel_principal, embed_ticket, embed_log_accion,
    guardar_solicitud, obtener_solicitud, actualizar_solicitud,
    _siguiente_numero, _rol_staff, _categoria_canal, enviar_log_solicitud,
    _now, _fecha_legible,
)


# ---------------------------------------------------------------------------
# Formularios (Modals) — 6 categorías
# ---------------------------------------------------------------------------

class FormSancion(ui.Modal, title="🛡️ Solicitud de Sanción"):
    usuario_inv = ui.TextInput(label="Usuario involucrado", placeholder="ID o mención", max_length=100)
    motivo = ui.TextInput(label="Motivo", style=discord.TextStyle.paragraph, max_length=500)
    descripcion = ui.TextInput(label="Descripción", style=discord.TextStyle.paragraph, max_length=1000)
    evidencias = ui.TextInput(label="Evidencias", style=discord.TextStyle.paragraph, max_length=800, required=False)
    info_extra = ui.TextInput(label="Información adicional", style=discord.TextStyle.paragraph, max_length=500, required=False)

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        campos = {
            "Usuario involucrado": str(self.usuario_inv),
            "Motivo": str(self.motivo),
            "Descripción": str(self.descripcion),
            "Evidencias": str(self.evidencias) if self.evidencias.value else "—",
            "Información adicional": str(self.info_extra) if self.info_extra.value else "—",
        }
        await crear_ticket_solicitud(self.bot, interaction, "sancion", campos)


class FormApelacion(ui.Modal, title="⚖️ Apelación de Sanción"):
    usuario_sanc = ui.TextInput(label="Usuario sancionado", placeholder="ID o mención", max_length=100)
    sancion = ui.TextInput(label="Sanción recibida", max_length=200)
    motivo = ui.TextInput(label="Motivo de la apelación", style=discord.TextStyle.paragraph, max_length=800)
    hechos = ui.TextInput(label="Explicación de los hechos", style=discord.TextStyle.paragraph, max_length=1000)
    evidencias = ui.TextInput(label="Evidencias adicionales", style=discord.TextStyle.paragraph, max_length=800, required=False)

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        campos = {
            "Usuario sancionado": str(self.usuario_sanc),
            "Sanción recibida": str(self.sancion),
            "Motivo de la apelación": str(self.motivo),
            "Explicación de los hechos": str(self.hechos),
            "Evidencias adicionales": str(self.evidencias) if self.evidencias.value else "—",
        }
        await crear_ticket_solicitud(self.bot, interaction, "apelacion", campos)


class FormInvestigacion(ui.Modal, title="🔎 Solicitud de Investigación"):
    usuarios = ui.TextInput(label="Usuario/s involucrado/s", placeholder="ID o mención", max_length=200)
    motivo = ui.TextInput(label="Motivo de la investigación", style=discord.TextStyle.paragraph, max_length=500)
    descripcion = ui.TextInput(label="Descripción del caso", style=discord.TextStyle.paragraph, max_length=1000)
    evidencias = ui.TextInput(label="Evidencias", style=discord.TextStyle.paragraph, max_length=800, required=False)
    info_extra = ui.TextInput(label="Información adicional", style=discord.TextStyle.paragraph, max_length=500, required=False)

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        campos = {
            "Usuario/s involucrado/s": str(self.usuarios),
            "Motivo": str(self.motivo),
            "Descripción del caso": str(self.descripcion),
            "Evidencias": str(self.evidencias) if self.evidencias.value else "—",
            "Información adicional": str(self.info_extra) if self.info_extra.value else "—",
        }
        await crear_ticket_solicitud(self.bot, interaction, "investigacion", campos)


class FormReporte(ui.Modal, title="🚨 Reporte"):
    usuario = ui.TextInput(label="Usuario reportado", placeholder="ID o mención", max_length=100)
    motivo = ui.TextInput(label="Motivo del reporte", max_length=200)
    descripcion = ui.TextInput(label="Descripción", style=discord.TextStyle.paragraph, max_length=1000)
    fecha_hora = ui.TextInput(label="Fecha y hora aproximada", placeholder="Ej: 20/09/2026 18:00", max_length=80)
    evidencias = ui.TextInput(label="Evidencias / Testigos", style=discord.TextStyle.paragraph, max_length=800, required=False)

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        campos = {
            "Usuario reportado": str(self.usuario),
            "Motivo del reporte": str(self.motivo),
            "Descripción": str(self.descripcion),
            "Fecha y hora aproximada": str(self.fecha_hora),
            "Evidencias / Testigos": str(self.evidencias) if self.evidencias.value else "—",
        }
        await crear_ticket_solicitud(self.bot, interaction, "reporte", campos)


class FormGeneral(ui.Modal, title="📩 Solicitud General"):
    asunto = ui.TextInput(label="Asunto", max_length=120)
    descripcion = ui.TextInput(label="Descripción", style=discord.TextStyle.paragraph, max_length=1500)
    area = ui.TextInput(label="Área relacionada", placeholder="Ej: RRHH, Médico, Finanzas…", max_length=100)
    evidencias = ui.TextInput(label="Evidencias / documentos", style=discord.TextStyle.paragraph, max_length=800, required=False)
    info_extra = ui.TextInput(label="Información adicional", style=discord.TextStyle.paragraph, max_length=500, required=False)

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        campos = {
            "Asunto": str(self.asunto),
            "Descripción": str(self.descripcion),
            "Área relacionada": str(self.area),
            "Evidencias/documentos": str(self.evidencias) if self.evidencias.value else "—",
            "Información adicional": str(self.info_extra) if self.info_extra.value else "—",
        }
        await crear_ticket_solicitud(self.bot, interaction, "general", campos)


class FormConsulta(ui.Modal, title="📋 Consulta"):
    asunto = ui.TextInput(label="Asunto", max_length=120)
    pregunta = ui.TextInput(label="Pregunta", style=discord.TextStyle.paragraph, max_length=1500)
    info_extra = ui.TextInput(label="Información adicional", style=discord.TextStyle.paragraph, max_length=500, required=False)

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        campos = {
            "Asunto": str(self.asunto),
            "Pregunta": str(self.pregunta),
            "Información adicional": str(self.info_extra) if self.info_extra.value else "—",
        }
        await crear_ticket_solicitud(self.bot, interaction, "consulta", campos)


async def crear_ticket_solicitud(
    bot: commands.Bot,
    interaction: discord.Interaction,
    categoria: str,
    campos: Dict[str, str],
) -> None:
    guild = interaction.guild
    if not guild or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("❌ Solo disponible en el servidor.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    numero = _siguiente_numero()
    cat = CATEGORIAS.get(categoria, CATEGORIAS["general"])
    nombre_canal = f"{cat['prefijo']}-{numero:04d}"[:90]

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, attach_files=True, embed_links=True
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, manage_channels=True, manage_messages=True
        ),
    }

    staff_role = _rol_staff(guild)
    if staff_role:
        overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

    for key in getattr(config, "TICKET_STAFF_KEYS", []):
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

    category = _categoria_canal(guild)
    try:
        canal = await guild.create_text_channel(
            nombre_canal,
            category=category,
            overwrites=overwrites,
            reason=f"Solicitud #{numero:04d} — {cat['nombre']} por {interaction.user}",
        )
    except discord.Forbidden:
        await interaction.followup.send("❌ No tengo permisos para crear canales.", ephemeral=True)
        return

    reg = {
        "id": numero,
        "numero": numero,
        "usuario_id": interaction.user.id,
        "categoria": categoria,
        "estado": "en_revision",
        "prioridad": "normal",
        "responsable_id": None,
        "fecha_creacion": _now(),
        "fecha_actualizacion": _now(),
        "fecha_cierre": None,
        "motivo_cierre": None,
        "campos": campos,
        "resolucion": None,
        "canal_id": canal.id,
        "usuarios_extra": [],
    }
    guardar_solicitud(reg)

    embed = embed_ticket(reg, guild)
    menciones = [interaction.user.mention]
    if staff_role:
        menciones.append(staff_role.mention)

    view = TicketSolicitudView(bot, numero)
    await canal.send(content=" ".join(menciones), embed=embed, view=view)

    await interaction.followup.send(
        f"✅ Solicitud **#{numero:04d}** creada: {canal.mention}",
        ephemeral=True,
    )

    log = embed_log_accion(reg, "Creación de solicitud", interaction.user, f"Canal: {canal.mention}")
    await enviar_log_solicitud(bot, log)


class MenuCategorias(ui.Select):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        options = [
            discord.SelectOption(
                label=cat["nombre"],
                value=key,
                description=cat["menu_desc"][:100],
                emoji=cat["emoji"],
            )
            for key, cat in CATEGORIAS.items()
        ]
        super().__init__(
            placeholder="📂 Selecciona el tipo de solicitud",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="centro_menu_categorias",
        )

    async def callback(self, interaction: discord.Interaction):
        cat = self.values[0]
        formularios = {
            "sancion": FormSancion,
            "apelacion": FormApelacion,
            "investigacion": FormInvestigacion,
            "reporte": FormReporte,
            "general": FormGeneral,
            "consulta": FormConsulta,
        }
        cls = formularios.get(cat)
        if not cls:
            await interaction.response.send_message("❌ Categoría no válida.", ephemeral=True)
            return
        await interaction.response.send_modal(cls(self.bot))


class PanelSolicitudesView(ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.add_item(MenuCategorias(bot))


def _puede_gestionar(user: discord.abc.User) -> bool:
    if not isinstance(user, discord.Member):
        return False
    return permisos.member_tiene_alguna_key(
        user,
        "OWNER", "CO_OWNER", "DIRECTOR", "DIRECTOR_ADMINISTRATIVO",
        "DIRECTOR_DISCIPLINA", "DIRECTOR_GENERAL", "DIRECTOR_RRHH",
        "SUPERVISOR", "STAFF_SERVIDOR",
    )


class ConfirmarCierreView(ui.View):
    def __init__(self, bot: commands.Bot, solicitud_id: int):
        super().__init__(timeout=60)
        self.bot = bot
        self.solicitud_id = solicitud_id

    @ui.button(label="Confirmar", style=discord.ButtonStyle.danger, emoji="✅")
    async def confirmar(self, interaction: discord.Interaction, button: ui.Button):
        if not _puede_gestionar(interaction.user):
            await interaction.response.send_message("❌ No tienes permiso.", ephemeral=True)
            return
        motivo = "Cerrada por el staff"
        actualizar_solicitud(
            self.solicitud_id, estado="cerrada", motivo_cierre=motivo, fecha_cierre=_now(),
        )
        reg = obtener_solicitud(self.solicitud_id)
        embed = embed_ticket(reg, interaction.guild)
        await interaction.response.edit_message(
            content=f"🔒 Solicitud cerrada por {interaction.user.mention}", embed=embed, view=None,
        )
        if reg:
            log = embed_log_accion(reg, "Cierre", interaction.user, motivo)
            await enviar_log_solicitud(self.bot, log)
        if interaction.channel:
            try:
                await interaction.channel.send("🔒 Este canal se eliminará en 5 segundos…")
                await asyncio.sleep(5)
                await interaction.channel.delete(reason=f"Solicitud #{self.solicitud_id} cerrada")
            except Exception:
                pass

    @ui.button(label="Cancelar", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancelar(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="Cierre cancelado.", embed=None, view=None)


class PrioridadSelect(ui.Select):
    def __init__(self, bot: commands.Bot, solicitud_id: int):
        self.bot = bot
        self.solicitud_id = solicitud_id
        options = [
            discord.SelectOption(label="Normal", value="normal", emoji="🟢"),
            discord.SelectOption(label="Media", value="media", emoji="🟡"),
            discord.SelectOption(label="Alta", value="alta", emoji="🟠"),
            discord.SelectOption(label="Urgente", value="urgente", emoji="🔴"),
        ]
        super().__init__(placeholder="Selecciona prioridad", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if not _puede_gestionar(interaction.user):
            await interaction.response.send_message("❌ Solo staff autorizado.", ephemeral=True)
            return
        prio = self.values[0]
        reg = actualizar_solicitud(self.solicitud_id, prioridad=prio)
        if not reg:
            await interaction.response.send_message("❌ Solicitud no encontrada.", ephemeral=True)
            return
        await interaction.response.send_message(
            f"✅ Prioridad actualizada a **{PRIORIDADES[prio][0]}**.", ephemeral=True
        )
        try:
            async for msg in interaction.channel.history(limit=20):
                if msg.author == interaction.client.user and msg.embeds:
                    await msg.edit(embed=embed_ticket(reg, interaction.guild), view=TicketSolicitudView(self.bot, self.solicitud_id))
                    break
        except Exception:
            pass
        log = embed_log_accion(reg, "Cambio de prioridad", interaction.user, PRIORIDADES[prio][0])
        await enviar_log_solicitud(self.bot, log)


class PrioridadView(ui.View):
    def __init__(self, bot: commands.Bot, solicitud_id: int):
        super().__init__(timeout=60)
        self.add_item(PrioridadSelect(bot, solicitud_id))


class AnadirUsuarioModal(ui.Modal, title="👥 Añadir usuario al ticket"):
    usuario = ui.TextInput(label="ID o mención del usuario", max_length=100)

    def __init__(self, bot: commands.Bot, solicitud_id: int):
        super().__init__()
        self.bot = bot
        self.solicitud_id = solicitud_id

    async def on_submit(self, interaction: discord.Interaction):
        if not _puede_gestionar(interaction.user):
            await interaction.response.send_message("❌ Solo staff autorizado.", ephemeral=True)
            return
        raw = str(self.usuario).strip().replace("<@", "").replace("!", "").replace(">", "")
        try:
            uid = int(raw)
        except ValueError:
            await interaction.response.send_message("❌ ID inválido.", ephemeral=True)
            return
        member = interaction.guild.get_member(uid) if interaction.guild else None
        if not member:
            await interaction.response.send_message("❌ Usuario no encontrado.", ephemeral=True)
            return
        try:
            await interaction.channel.set_permissions(member, view_channel=True, send_messages=True, attach_files=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ No puedo modificar permisos.", ephemeral=True)
            return
        reg = obtener_solicitud(self.solicitud_id)
        extras = list((reg or {}).get("usuarios_extra") or [])
        if uid not in extras:
            extras.append(uid)
            actualizar_solicitud(self.solicitud_id, usuarios_extra=extras)
        await interaction.response.send_message(f"✅ {member.mention} añadido al ticket.")
        if reg:
            log = embed_log_accion(reg, "Usuario añadido", interaction.user, member.mention)
            await enviar_log_solicitud(self.bot, log)


class EstadoSelect(ui.Select):
    def __init__(self, bot: commands.Bot, solicitud_id: int):
        self.bot = bot
        self.solicitud_id = solicitud_id
        options = [
            discord.SelectOption(label=v[0], value=k)
            for k, v in ESTADOS.items()
        ]
        super().__init__(placeholder="Cambiar estado", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if not _puede_gestionar(interaction.user):
            await interaction.response.send_message("❌ Solo staff autorizado.", ephemeral=True)
            return
        nuevo = self.values[0]
        reg_old = obtener_solicitud(self.solicitud_id)
        old_txt = ESTADOS.get((reg_old or {}).get("estado", ""), ("?", 0))[0]
        reg = actualizar_solicitud(self.solicitud_id, estado=nuevo)
        if not reg:
            await interaction.response.send_message("❌ Solicitud no encontrada.", ephemeral=True)
            return
        await interaction.response.send_message(
            f"✅ Estado: **{old_txt}** → **{ESTADOS[nuevo][0]}**", ephemeral=True
        )
        try:
            async for msg in interaction.channel.history(limit=20):
                if msg.author == interaction.client.user and msg.embeds:
                    await msg.edit(embed=embed_ticket(reg, interaction.guild), view=TicketSolicitudView(self.bot, self.solicitud_id))
                    break
        except Exception:
            pass
        log = embed_log_accion(reg, "Cambio de estado", interaction.user, f"{old_txt} → {ESTADOS[nuevo][0]}")
        await enviar_log_solicitud(self.bot, log)


class EstadoView(ui.View):
    def __init__(self, bot: commands.Bot, solicitud_id: int):
        super().__init__(timeout=60)
        self.add_item(EstadoSelect(bot, solicitud_id))


class TicketSolicitudView(ui.View):
    def __init__(self, bot: commands.Bot, solicitud_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.solicitud_id = solicitud_id

    @ui.button(label="Reclamar", style=discord.ButtonStyle.primary, emoji="👋", custom_id="sol_reclamar")
    async def reclamar(self, interaction: discord.Interaction, button: ui.Button):
        if not _puede_gestionar(interaction.user):
            await interaction.response.send_message("❌ Solo staff autorizado.", ephemeral=True)
            return
        reg = actualizar_solicitud(self.solicitud_id, responsable_id=interaction.user.id, estado="en_revision")
        if not reg:
            await interaction.response.send_message("❌ Solicitud no encontrada.", ephemeral=True)
            return
        await interaction.response.edit_message(embed=embed_ticket(reg, interaction.guild), view=self)
        log = embed_log_accion(reg, "Reclamado", interaction.user)
        await enviar_log_solicitud(self.bot, log)

    @ui.button(label="Cerrar", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="sol_cerrar")
    async def cerrar(self, interaction: discord.Interaction, button: ui.Button):
        if not _puede_gestionar(interaction.user):
            await interaction.response.send_message("❌ Solo staff autorizado.", ephemeral=True)
            return
        await interaction.response.send_message(
            "⚠️ ¿Estás seguro de que deseas cerrar esta solicitud?",
            view=ConfirmarCierreView(self.bot, self.solicitud_id),
            ephemeral=True,
        )

    @ui.button(label="Prioridad", style=discord.ButtonStyle.secondary, emoji="📌", custom_id="sol_prioridad")
    async def prioridad(self, interaction: discord.Interaction, button: ui.Button):
        if not _puede_gestionar(interaction.user):
            await interaction.response.send_message("❌ Solo staff autorizado.", ephemeral=True)
            return
        await interaction.response.send_message(
            "Selecciona la prioridad:", view=PrioridadView(self.bot, self.solicitud_id), ephemeral=True,
        )

    @ui.button(label="Añadir usuario", style=discord.ButtonStyle.secondary, emoji="👥", custom_id="sol_adduser")
    async def adduser(self, interaction: discord.Interaction, button: ui.Button):
        if not _puede_gestionar(interaction.user):
            await interaction.response.send_message("❌ Solo staff autorizado.", ephemeral=True)
            return
        await interaction.response.send_modal(AnadirUsuarioModal(self.bot, self.solicitud_id))

    @ui.button(label="Estado", style=discord.ButtonStyle.secondary, emoji="📝", custom_id="sol_estado")
    async def estado(self, interaction: discord.Interaction, button: ui.Button):
        if not _puede_gestionar(interaction.user):
            await interaction.response.send_message("❌ Solo staff autorizado.", ephemeral=True)
            return
        await interaction.response.send_message(
            "Selecciona el nuevo estado:", view=EstadoView(self.bot, self.solicitud_id), ephemeral=True,
        )


def registrar(bot: commands.Bot) -> None:
    """Registra el panel y vistas del centro de solicitudes."""

    @bot.tree.command(
        name="panel_solicitudes",
        description="Publica el Centro de Solicitudes (panel profesional)",
    )
    @app_commands.describe(canal="Canal donde publicar el panel (opcional)")
    async def panel_solicitudes(
        interaction: discord.Interaction,
        canal: Optional[discord.TextChannel] = None,
    ):
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("❌ Solo en servidor.", ephemeral=True)
            return
        if not permisos.member_tiene_alguna_key(
            interaction.user, "OWNER", "CO_OWNER", "DIRECTOR_ADMINISTRATIVO", "DIRECTOR_GENERAL"
        ):
            await interaction.response.send_message(
                "❌ Solo Owner / Director Administrativo / Director General.", ephemeral=True
            )
            return

        destino = canal or interaction.channel
        if not isinstance(destino, discord.TextChannel):
            await interaction.response.send_message("❌ Canal inválido.", ephemeral=True)
            return

        embed = embed_panel_principal()
        view = PanelSolicitudesView(bot)
        await destino.send(embed=embed, view=view)
        await interaction.response.send_message(
            f"✅ Panel de solicitudes publicado en {destino.mention}.", ephemeral=True
        )

    bot.add_view(PanelSolicitudesView(bot))
