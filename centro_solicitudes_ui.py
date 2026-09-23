# -*- coding: utf-8 -*-
"""centro_solicitudes_ui.py — Carga el módulo completo y activa menú desplegable de personas."""
from __future__ import annotations
import urllib.request
import sys

_GOOD = "a6e30cbaefe3ab422f1b108b42dbe5a6c83d1f92"
_URL = f"https://raw.githubusercontent.com/ellisfernando06-sketch/Test---Hospital/{_GOOD}/centro_solicitudes_ui.py"

def _bootstrap():
    print("[centro_solicitudes_ui] Descargando módulo completo…")
    with urllib.request.urlopen(_URL, timeout=45) as resp:
        source = resp.read().decode("utf-8")
    print(f"[centro_solicitudes_ui] Descargado ({len(source)} bytes)")
    mod = sys.modules[__name__]
    exec(compile(source, "centro_solicitudes_ui_remote.py", "exec"), mod.__dict__)
    print("[centro_solicitudes_ui] Módulo completo cargado")
    _patch_adduser(mod)

def _patch_adduser(mod):
    """Reemplaza el modal por menú desplegable de personas autorizadas."""
    import discord
    from discord import ui
    from ticket_adduser import AnadirUsuarioView

    TicketSolicitudView = mod.TicketSolicitudView
    _puede_gestionar = mod._puede_gestionar

    async def adduser(self, interaction: discord.Interaction, button: ui.Button):
        if not _puede_gestionar(interaction.user):
            await interaction.response.send_message("❌ Solo staff autorizado.", ephemeral=True)
            return
        if not interaction.guild:
            await interaction.response.send_message("❌ Solo en el servidor.", ephemeral=True)
            return
        await interaction.response.send_message(
            "👥 **Añadir persona al ticket**\n"
            "• Menú superior: personal autorizado (roles de staff / hospital)\n"
            "• Menú inferior: buscar cualquier usuario del servidor",
            view=AnadirUsuarioView(self.bot, self.solicitud_id, interaction.guild),
            ephemeral=True,
        )

    TicketSolicitudView.adduser = adduser
    print("[centro_solicitudes_ui] Parche Añadir usuario (menú desplegable) aplicado")

_bootstrap()
