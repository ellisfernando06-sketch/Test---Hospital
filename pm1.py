# -*- coding: utf-8 -*
"""
paneles_miembros.py — Paneles interactivos para miembros/staff y publicación
con canal de logs obligatorio para evaluación.
"""
from __future__ import annotations

from typing import Optional

import discord
from discord import ui, app_commands
from discord.ext import commands

import config
import permisos
import roles_store
import logs_store
from estilos import crear_embed

try:
    from postulaciones import PostulacionModal
except Exception:
    PostulacionModal = None

try:
    from quejas import QuejaModal
except Exception:
    QuejaModal = None

try:
    from centro_solicitudes_ui import (
        FormSancion, FormApelacion, FormInvestigacion, FormReporte,
        FormGeneral, FormConsulta, PanelSolicitudesView,
    )
except Exception:
    FormSancion = FormApelacion = FormInvestigacion = FormReporte = None
    FormGeneral = FormConsulta = PanelSolicitudesView = None


def _puede_publicar_paneles(user: discord.abc.User) -> bool:
    if not isinstance(user, discord.Member):
        return False
    return permisos.member_tiene_alguna_key(
        user, "OWNER", "CO_OWNER", "DIRECTOR_ADMINISTRATIVO",
        "DIRECTOR_GENERAL", "DIRECTOR",
    )


async def _guardar_y_confirmar(
    interaction: discord.Interaction,
    destino: discord.TextChannel,
    canal_logs: discord.TextChannel,
    tipo_log: str,
    embed: discord.Embed,
    view: ui.View,
    etiqueta: str,
) -> None:
    logs_store.set_canal(tipo_log, canal_logs.id)
    await destino.send(embed=embed, view=view)
    await interaction.response.send_message(
        f"✅ **{etiqueta}** publicado en {destino.mention}.\n"
        f"📥 Evaluaciones / logs → {canal_logs.mention} (`{tipo_log}`)",
        ephemeral=True,
    )


class MenuStaffDisciplina(ui.Select):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        options = [
            discord.SelectOption(
                label="Solicitud de sanción",
                value="sancion",
                emoji="🛡️",
                description="Aplicar o solicitar una sanción",
            ),
            discord.SelectOption(
                label="Investigación interna",
                value="investigacion",
                emoji="🔎",
                description="Abrir investigación formal",
            ),
            discord.SelectOption(
                label="Apelación",
                value="apelacion",
                emoji="⚖️",
                description="Revisar apelación de sanción",
            ),
            discord.SelectOption(
                label="Reporte disciplinario",
                value="reporte",
                emoji="🚨",
                description="Reportar incidente a dirección",
            ),
        ]
        super().__init__(
            placeholder="⚖️ Acción disciplinaria…",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="panel_staff_disciplina_menu",
        )

    async def callback(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("❌ Solo en servidor.", ephemeral=True)
            return
        if not permisos.member_staff_disciplina(interaction.user):
            await interaction.response.send_message(
                "❌ Solo **jefes / encargados de staff del servidor** o **dirección**.",
                ephemeral=True,
            )
            return
        val = self.values[0] if self.values else "sancion"
        formularios = {
            "sancion": FormSancion,
            "investigacion": FormInvestigacion,
            "apelacion": FormApelacion,
            "reporte": FormReporte,
        }
        cls = formularios.get(val)
        if not cls:
            await interaction.response.send_message(
                "❌ Formulario no disponible. Usa `/panel_solicitudes` o reinicia el bot.",
                ephemeral=True,
            )
            return
        await interaction.response.send_modal(cls(self.bot))


class PanelStaffDisciplinaView(ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.add_item(MenuStaffDisciplina(bot))


def embed_panel_staff_disciplina() -> discord.Embed:
    return discord.Embed(
        title="⚖️ Panel Staff — Disciplina e Investigaciones",
        description=(
            "Panel **restringido** para jefes/encargados del **Staff del Servidor** "
            "y **Dirección**.\n\n"
            "Usa el menú para:\n"
            "• Solicitar **sanciones**\n"
            "• Abrir **investigaciones**\n"
            "• Gestionar **apelaciones**\n"
            "• Enviar **reportes** disciplinarios\n\n"
            "Las solicitudes se crean en canal privado y se registran en el "
            "canal de logs configurado al publicar este panel."
        ),
        color=0x8E44AD,
    )


class MenuPostulaciones(ui.Select):
    def __init__(self):
        options = []
        deps = getattr(config, "DEPARTAMENTOS", {}) or {}
        for slug, data in deps.items():
            if not isinstance(data, dict):
                continue
            nombre = str(data.get("nombre") or slug)[:100]
            options.append(
                discord.SelectOption(
                    label=nombre,
                    value=str(slug),
                    description=f"Postularse a {nombre}"[:100],
                    emoji="📋",
                )
            )
        if not options:
            options = [
                discord.SelectOption(label="Staff general", value="general", emoji="📋"),
            ]
        super().__init__(
            placeholder="📋 Elige departamento…",
            min_values=1,
            max_values=1,
            options=options[:25],
            custom_id="panel_postulaciones_menu",
        )

    async def callback(self, interaction: discord.Interaction):
        if not PostulacionModal:
            await interaction.response.send_message(
                "❌ Módulo de postulaciones no disponible.", ephemeral=True
            )
            return
        slug = self.values[0] if self.values else "general"
        deps = getattr(config, "DEPARTAMENTOS", {}) or {}
        data = deps.get(slug) or {}
        nombre = str(data.get("nombre") or slug)
        try:
            await interaction.response.send_modal(PostulacionModal(slug, nombre))
        except TypeError:
            await interaction.response.send_modal(PostulacionModal())


class PanelPostulacionesView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MenuPostulaciones())


def embed_panel_postulaciones() -> discord.Embed:
    return discord.Embed(
        title="📋 Centro de Postulaciones",
        description=(
            "¿Quieres unirte al personal del hospital?\n"
            "Selecciona el **departamento** y completa el formulario.\n\n"
            "Tu postulación será enviada al canal de evaluación configurado "
            "para que la dirección correspondiente la revise."
        ),
        color=0x3498DB,
    )


class MenuQuejas(ui.Select):
    def __init__(self):
        options = []
        deps = getattr(config, "DEPARTAMENTOS", {}) or {}
        for slug, data in deps.items():
            if not isinstance(data, dict):
                continue
            nombre = str(data.get("nombre") or slug)[:100]
            options.append(
                discord.SelectOption(
                    label=nombre,
                    value=str(slug),
                    description="Queja sobre este departamento"[:100],
                    emoji="📢",
                )
            )
        if not options:
            options = [
                discord.SelectOption(label="General / RRHH", value="rrhh", emoji="📢"),
            ]
        super().__init__(
            placeholder="📢 Área de la queja…",
            min_values=1,
            max_values=1,
            options=options[:25],
            custom_id="panel_quejas_menu",
        )

    async def callback(self, interaction: discord.Interaction):
        if not QuejaModal:
            await interaction.response.send_message(
                "❌ Módulo de quejas no disponible.", ephemeral=True
            )
            return
        slug = self.values[0] if self.values else "rrhh"
        deps = getattr(config, "DEPARTAMENTOS", {}) or {}
        data = deps.get(slug) or {}
        nombre = str(data.get("nombre") or slug)
        try:
            await interaction.response.send_modal(QuejaModal(slug, nombre))
        except TypeError:
            await interaction.response.send_modal(QuejaModal())


class PanelQuejasView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MenuQuejas())


def embed_panel_quejas() -> discord.Embed:
    return discord.Embed(
        title="📢 Centro de Quejas Formales",
        description=(
            "Presenta una **queja formal** de forma confidencial.\n"
            "Elige el área involucrada y describe los hechos.\n\n"
