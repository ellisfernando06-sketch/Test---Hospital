# -*- coding: utf-8 -*
"""capacitacion_cert_ui.py — /certificar (formulario + autorización)."""
from __future__ import annotations

import discord
from discord import ui, app_commands
from discord.ext import commands

try:
    import permisos
except Exception:
    permisos = None


def _puede_iniciar(member: discord.Member) -> bool:
    if not isinstance(member, discord.Member):
        return False
    if member.guild_permissions.administrator:
        return True
    if permisos is None:
        return False
    try:
        return permisos.member_tiene_alguna_key(
            member,
            "OWNER", "CO_OWNER",
            "DIRECTOR_DOCENCIA", "DIRECTOR_GENERAL",
            "DIRECTOR_MEDICO", "DIRECTOR_ENFERMERIA",
            "DIRECTOR_ADMINISTRATIVO", "DIRECTOR",
            "SUPERVISOR", "JEFE_DEPARTAMENTO",
        )
    except Exception:
        return False


class ModalCertificar(ui.Modal, title="Datos del certificado"):
    capacitacion = ui.TextInput(
        label="Capacitación que recibe",
        placeholder="Ej: RCP Básico",
        max_length=120,
        required=True,
    )
    descripcion = ui.TextInput(
        label="Descripción (opcional)",
        style=discord.TextStyle.paragraph,
        max_length=400,
        required=False,
    )
    departamento = ui.TextInput(
        label="Departamento (opcional)",
        max_length=80,
        required=False,
    )

    def __init__(self, bot: commands.Bot, usuario: discord.Member):
        super().__init__()
        self.bot = bot
        self.usuario = usuario

    async def on_submit(self, inter: discord.Interaction):
        if not _puede_iniciar(inter.user):
            return await inter.response.send_message("Sin permiso.", ephemeral=True)
        await inter.response.defer(ephemeral=True)
        cap = str(self.capacitacion).strip()
        desc = str(self.descripcion).strip() if self.descripcion.value else ""
        depto = str(self.departamento).strip() if self.departamento.value else ""
        firma_file = None
        try:
            import firmas
            reg_f = firmas.obtener_firma_usuario(inter.user.id)
            if reg_f:
                firma_file = reg_f.get("file")
        except Exception as e:
            print("[certificar] firma:", e)
        try:
            import firmas
            aid = await firmas.solicitar_autorizacion_certificado(
                self.bot, inter,
                receptor=self.usuario,
                capacitacion=cap,
                descripcion=desc,
                departamento=depto,
                firma_encargado_file=firma_file,
            )
            await inter.followup.send(
                f"Solicitud #{aid} enviada.\n"
                f"Graduado: {self.usuario.mention}\nCapacitación: {cap}\n"
                f"Pendiente: Director de Investigación y Docencia.",
                ephemeral=True,
            )
        except Exception as e:
            print("[certificar] auth:", e)
            await inter.followup.send(f"Error: {e}", ephemeral=True)


def registrar(bot: commands.Bot) -> None:
    try:
        names = {c.name for c in bot.tree.get_commands()}
    except Exception:
        names = set()
    if "certificar" in names:
        print("[capacitacion_cert_ui] certificar ya existe")
        return

    @bot.tree.command(name="certificar", description="Certificado RP con autorización")
    @app_commands.describe(usuario="Receptor")
    async def certificar(inter: discord.Interaction, usuario: discord.Member):
        if not isinstance(inter.user, discord.Member) or not _puede_iniciar(inter.user):
            return await inter.response.send_message("Sin permiso.", ephemeral=True)
        await inter.response.send_modal(ModalCertificar(bot, usuario))

    print("[capacitacion_cert_ui] OK /certificar")
