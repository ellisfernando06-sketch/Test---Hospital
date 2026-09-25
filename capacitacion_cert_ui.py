# -*- coding: utf-8 -*-
"""Comando /certificar: selecciona una certificación abierta e inicia tres aprobaciones."""
from __future__ import annotations
import discord
from discord import ui, app_commands
from discord.ext import commands
import certificaciones_abiertas
try:
    import permisos
except Exception:
    permisos = None


def _puede_iniciar(member):
    if not isinstance(member, discord.Member): return False
    if member.guild_permissions.administrator: return True
    return bool(permisos and permisos.member_tiene_alguna_key(member,
        "OWNER", "CO_OWNER", "DIRECTOR_DOCENCIA", "DIRECTOR_GENERAL",
        "DIRECTOR", "ENCARGADO_AREA", "JEFE_DEPARTAMENTO"))

class CertificacionSelect(ui.Select):
    def __init__(self, bot, usuario):
        self.bot, self.usuario = bot, usuario
        items = certificaciones_abiertas.listar_certificaciones_activas()[:25]
        if not items:
            options = [discord.SelectOption(label="No hay certificaciones abiertas", value="0")]
        else:
            options = [discord.SelectOption(label=str(x["nombre"])[:100], value=str(x["id"]), description=str(x.get("descripcion") or "")[:100]) for x in items]
        super().__init__(placeholder="Selecciona la certificación...", options=options, disabled=not items)

    async def callback(self, inter):
        cert = certificaciones_abiertas.obtener_certificacion(int(self.values[0]))
        await inter.response.send_modal(DatosCertificado(self.bot, self.usuario, cert))

class SeleccionCertificacion(ui.View):
    def __init__(self, bot, usuario):
        super().__init__(timeout=300)
        self.add_item(CertificacionSelect(bot, usuario))

class DatosCertificado(ui.Modal, title="Datos del estudiante"):
    cedula = ui.TextInput(label="Cédula / identificación", max_length=80, required=True)
    departamento = ui.TextInput(label="Ala o departamento", max_length=100, required=False)
    descripcion = ui.TextInput(label="Observaciones", style=discord.TextStyle.paragraph, max_length=400, required=False)

    def __init__(self, bot, usuario, cert):
        super().__init__(); self.bot, self.usuario, self.cert = bot, usuario, cert

    async def on_submit(self, inter):
        if not _puede_iniciar(inter.user):
            return await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
        await inter.response.defer(ephemeral=True)
        import firmas
        firma = firmas.obtener_firma_usuario(inter.user.id) or {}
        try:
            aid = await firmas.solicitar_autorizacion_certificado(
                self.bot, inter, receptor=self.usuario, certificacion=self.cert,
                cedula=str(self.cedula), departamento=str(self.departamento or "").strip(),
                descripcion=str(self.descripcion or "").strip(), firma_encargado_file=firma.get("file"))
            await inter.followup.send(f"✅ Solicitud #{aid} creada. Requiere firma del encargado, Docencia y del Director del ala/departamento.", ephemeral=True)
        except Exception as exc:
            await inter.followup.send(f"❌ No se pudo crear la solicitud: {exc}", ephemeral=True)

def registrar(bot: commands.Bot) -> None:
    if any(c.name == "certificar" for c in bot.tree.get_commands()): return
    @bot.tree.command(name="certificar", description="Certifica un estudiante con tres firmas obligatorias")
    @app_commands.describe(usuario="Estudiante que aprobó la certificación")
    async def certificar(inter: discord.Interaction, usuario: discord.Member):
        if not _puede_iniciar(inter.user):
            return await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
        await inter.response.send_message("Selecciona la certificación abierta:", view=SeleccionCertificacion(bot, usuario), ephemeral=True)
