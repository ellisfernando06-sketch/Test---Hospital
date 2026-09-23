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


class PanelMiembrosView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Mi expediente", style=discord.ButtonStyle.primary, emoji="📁", custom_id="pm_exp")
    async def exp(self, inter: discord.Interaction, btn: ui.Button):
        await inter.response.send_message("Usa `/mi_expediente` o `/ficha`.", ephemeral=True)

    @ui.button(label="Mis sanciones", style=discord.ButtonStyle.secondary, emoji="⚠️", custom_id="pm_sanc")
    async def sanc(self, inter: discord.Interaction, btn: ui.Button):
        await inter.response.send_message("Usa `/mi_sanciones`.", ephemeral=True)

    @ui.button(label="Abrir ticket", style=discord.ButtonStyle.success, emoji="🎫", custom_id="pm_tkt")
    async def tkt(self, inter: discord.Interaction, btn: ui.Button):
        await inter.response.send_message("Usa el **Panel de Tickets** del servidor.", ephemeral=True)


def registrar(bot: commands.Bot) -> None:

    @bot.tree.command(name="panel_staff_disciplina",
                      description="Panel staff: sanciones/investigaciones (jefes y dirección)")
    @app_commands.describe(canal="Canal del panel", canal_logs="Canal privado de evaluación")
    async def panel_staff_disciplina(inter: discord.Interaction,
                                     canal: discord.TextChannel,
                                     canal_logs: discord.TextChannel):
        if not _puede_pub(inter.user):
            await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
            return
        emb = discord.Embed(
            title="⚖️ Panel Staff — Disciplina e Investigaciones",
            description=(
                "Solo **jefes/encargados de staff del servidor** y **dirección**.\n"
                "Menú: sanción · investigación · apelación · reporte.\n"
                "Se crea canal privado y se registra en el canal de logs indicado."
            ), color=0x8E44AD)
        await _pub(inter, canal, canal_logs, "staff_disciplina", emb, PanelStaffDiscView(bot), "Panel Staff Disciplina")
        logs_store.set_canal("log_sanciones", canal_logs.id)
        logs_store.set_canal("log_investigaciones", canal_logs.id)
        logs_store.set_canal("aprobaciones_rrhh", canal_logs.id)

    @bot.tree.command(name="panel_postulaciones",
                      description="Panel postulaciones (requiere canal de evaluación)")
    @app_commands.describe(canal="Canal del panel", canal_logs="Canal donde dirección evalúa")
    async def panel_postulaciones(inter: discord.Interaction,
                                  canal: discord.TextChannel,
                                  canal_logs: discord.TextChannel):
        if not _puede_pub(inter.user):
            await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
            return
        emb = discord.Embed(
            title="📋 Centro de Postulaciones",
            description="Elige departamento y completa el formulario. La dirección revisará en el canal de logs.",
            color=0x3498DB)
        await _pub(inter, canal, canal_logs, "log_postulaciones", emb, PanelPostView(), "Panel Postulaciones")

    @bot.tree.command(name="panel_quejas",
                      description="Panel quejas formales (requiere canal de evaluación)")
    @app_commands.describe(canal="Canal del panel", canal_logs="Canal RRHH de evaluación")
    async def panel_quejas(inter: discord.Interaction,
                           canal: discord.TextChannel,
                           canal_logs: discord.TextChannel):
        if not _puede_pub(inter.user):
            await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
            return
        emb = discord.Embed(
            title="📢 Centro de Quejas Formales",
            description="Presenta una queja confidencial. RRHH la evalúa en el canal de logs.",
            color=0xE67E22)
        await _pub(inter, canal, canal_logs, "log_quejas", emb, PanelQuejaView(), "Panel Quejas")

    @bot.tree.command(name="panel_miembros",
                      description="Panel interactivo para pacientes y miembros")
    @app_commands.describe(canal="Canal del panel (opcional)")
    async def panel_miembros(inter: discord.Interaction,
                             canal: Optional[discord.TextChannel] = None):
        if not _puede_pub(inter.user):
            await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
            return
        dest = canal or inter.channel
        if not isinstance(dest, discord.TextChannel):
            await inter.response.send_message("❌ Canal inválido.", ephemeral=True)
            return
        emb = discord.Embed(
            title="👤 Panel de Miembros",
            description="Accesos rápidos: expediente · sanciones · orientación de tickets.",
            color=0x1ABC9C)
        await dest.send(embed=emb, view=PanelMiembrosView())
        await inter.response.send_message(f"✅ Panel miembros en {dest.mention}.", ephemeral=True)

    @bot.tree.command(name="panel_solicitudes_logs",
                      description="Centro de solicitudes + canal de logs de evaluación")
    @app_commands.describe(canal="Canal del panel", canal_logs="Canal de evaluación del personal")
    async def panel_solicitudes_logs(inter: discord.Interaction,
                                     canal: discord.TextChannel,
                                     canal_logs: discord.TextChannel):
        if not _puede_pub(inter.user):
            await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
            return
        logs_store.set_canal("log_solicitudes", canal_logs.id)
        logs_store.set_canal("aprobaciones", canal_logs.id)
        emb = discord.Embed(
            title="📩 Centro de Solicitudes",
            description="Selecciona el tipo de solicitud. El personal evaluará en el canal de logs.",
            color=0x3498DB)
        view = PanelSolicitudesView(bot) if PanelSolicitudesView else ui.View()
        await canal.send(embed=emb, view=view)
        await inter.response.send_message(
            f"✅ Solicitudes en {canal.mention}\n📥 Logs → {canal_logs.mention}", ephemeral=True)

    @bot.tree.command(name="configurar_canal_logs",
                      description="Asigna canal de evaluación/logs de un tipo")
    @app_commands.describe(tipo="Tipo de log", canal_logs="Canal privado")
    @app_commands.choices(tipo=[
        app_commands.Choice(name="Solicitudes", value="log_solicitudes"),
        app_commands.Choice(name="Postulaciones", value="log_postulaciones"),
        app_commands.Choice(name="Quejas", value="log_quejas"),
        app_commands.Choice(name="Sanciones", value="log_sanciones"),
        app_commands.Choice(name="Investigaciones", value="log_investigaciones"),
        app_commands.Choice(name="Aprobaciones RRHH", value="aprobaciones_rrhh"),
        app_commands.Choice(name="Aprobaciones", value="aprobaciones"),
        app_commands.Choice(name="Staff disciplina", value="staff_disciplina"),
    ])
    async def configurar_canal_logs(inter: discord.Interaction,
                                    tipo: app_commands.Choice[str],
                                    canal_logs: discord.TextChannel):
        if not _puede_pub(inter.user):
            await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
            return
        logs_store.set_canal(tipo.value, canal_logs.id)
        await inter.response.send_message(f"✅ `{tipo.value}` → {canal_logs.mention}", ephemeral=True)

    bot.add_view(PanelStaffDiscView(bot))
    bot.add_view(PanelPostView())
    bot.add_view(PanelQuejaView())
    bot.add_view(PanelMiembrosView())
    print("[paneles_miembros] OK")
