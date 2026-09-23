# -*- coding: utf-8 -*
"""paneles_miembros.py — Paneles interactivos + canal_logs obligatorio."""
from __future__ import annotations
from typing import Optional
import discord
from discord import ui, app_commands
from discord.ext import commands
import config, permisos, logs_store
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
        FormSancion, FormApelacion, FormInvestigacion, FormReporte, PanelSolicitudesView,
    )
except Exception:
    FormSancion = FormApelacion = FormInvestigacion = FormReporte = PanelSolicitudesView = None


def _puede_pub(user) -> bool:
    return isinstance(user, discord.Member) and permisos.member_tiene_alguna_key(
        user, "OWNER", "CO_OWNER", "DIRECTOR_ADMINISTRATIVO", "DIRECTOR_GENERAL", "DIRECTOR",
    )


async def _pub(inter, destino, canal_logs, tipo, embed, view, label):
    logs_store.set_canal(tipo, canal_logs.id)
    await destino.send(embed=embed, view=view)
    await inter.response.send_message(
        f"✅ **{label}** en {destino.mention}\n📥 Logs → {canal_logs.mention} (`{tipo}`)",
        ephemeral=True,
    )


class MenuStaffDisc(ui.Select):
    def __init__(self, bot):
        self.bot = bot
        opts = [
            discord.SelectOption(label="Sanción", value="sancion", emoji="🛡️"),
            discord.SelectOption(label="Investigación", value="investigacion", emoji="🔎"),
            discord.SelectOption(label="Apelación", value="apelacion", emoji="⚖️"),
            discord.SelectOption(label="Reporte", value="reporte", emoji="🚨"),
        ]
        super().__init__(placeholder="⚖️ Acción disciplinaria…", options=opts,
                         min_values=1, max_values=1, custom_id="panel_staff_disc_menu")

    async def callback(self, inter: discord.Interaction):
        if not isinstance(inter.user, discord.Member) or not permisos.member_staff_disciplina(inter.user):
            await inter.response.send_message(
                "❌ Solo jefes/encargados de staff del servidor o dirección.", ephemeral=True)
            return
        m = {"sancion": FormSancion, "investigacion": FormInvestigacion,
             "apelacion": FormApelacion, "reporte": FormReporte}
        cls = m.get(self.values[0] if self.values else "sancion")
        if not cls:
            await inter.response.send_message("❌ Formulario no cargado. Reinicia el bot.", ephemeral=True)
            return
        await inter.response.send_modal(cls(self.bot))


class PanelStaffDiscView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.add_item(MenuStaffDisc(bot))


class MenuPost(ui.Select):
    def __init__(self):
        opts = []
        for slug, data in (getattr(config, "DEPARTAMENTOS", {}) or {}).items():
            if isinstance(data, dict):
                n = str(data.get("nombre") or slug)[:100]
                opts.append(discord.SelectOption(label=n, value=str(slug), emoji="📋",
                                                 description=f"Postularse a {n}"[:100]))
        if not opts:
            opts = [discord.SelectOption(label="Staff general", value="general", emoji="📋")]
        super().__init__(placeholder="📋 Departamento…", options=opts[:25],
                         min_values=1, max_values=1, custom_id="panel_post_menu")

    async def callback(self, inter: discord.Interaction):
        if not PostulacionModal:
            await inter.response.send_message("❌ Postulaciones no disponibles.", ephemeral=True)
            return
        slug = self.values[0]
        data = (getattr(config, "DEPARTAMENTOS", {}) or {}).get(slug) or {}
        await inter.response.send_modal(PostulacionModal(slug, str(data.get("nombre") or slug)))


class PanelPostView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MenuPost())


class MenuQueja(ui.Select):
    def __init__(self):
        opts = []
        for slug, data in (getattr(config, "DEPARTAMENTOS", {}) or {}).items():
            if isinstance(data, dict):
                n = str(data.get("nombre") or slug)[:100]
                opts.append(discord.SelectOption(label=n, value=str(slug), emoji="📢"))
        if not opts:
            opts = [discord.SelectOption(label="RRHH / General", value="rrhh", emoji="📢")]
        super().__init__(placeholder="📢 Área de la queja…", options=opts[:25],
                         min_values=1, max_values=1, custom_id="panel_queja_menu")

    async def callback(self, inter: discord.Interaction):
        if not QuejaModal:
            await inter.response.send_message("❌ Quejas no disponibles.", ephemeral=True)
            return
        slug = self.values[0]
        data = (getattr(config, "DEPARTAMENTOS", {}) or {}).get(slug) or {}
        await inter.response.send_modal(QuejaModal(slug, str(data.get("nombre") or slug)))


class PanelQuejaView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MenuQueja())
