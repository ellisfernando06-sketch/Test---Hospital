# -*- coding: utf-8 -*
"""capacitacion_cert_ui.py — Modal y lógica de /certificar."""
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


class ModalCertificar(ui.Modal, title="🎓 Datos del certificado"):
    capacitacion = ui.TextInput(
        label="Capacitación que recibe",
        placeholder="Ej: RCP Básico, Trauma I…",
        max_length=120,
        required=True,
    )
    descripcion = ui.TextInput(
        label="Descripción / contenido (opcional)",
        style=discord.TextStyle.paragraph,
        placeholder="Qué aprendió o superó…",
        max_length=400,
        required=False,
    )
    departamento = ui.TextInput(
        label="Departamento / área (opcional)",
        placeholder="Cuerpo Médico, Enfermería…",
        max_length=80,
        required=False,
    )

    def __init__(self, bot: commands.Bot, usuario: discord.Member):
        super().__init__()
        self.bot = bot
        self.usuario = usuario

    async def on_submit(self, inter: discord.Interaction):
        if not _puede_iniciar(inter.user):
            return await inter.response.send_message("❌ Sin permiso.", ephemeral=True)

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
            else:
                await inter.followup.send(
                    "⚠️ Sin firma registrada. Usa `/registrar_firma` (Encargado / Instructor).",
                    ephemeral=True,
                )
        except Exception as e:
            print("[certificar] firma:", e)

        try:
            import firmas
            aid = await firmas.solicitar_autorizacion_certificado(
                self.bot,
                inter,
                receptor=self.usuario,
                capacitacion=cap,
                descripcion=desc,
                departamento=depto,
                firma_encargado_file=firma_file,
            )
            await inter.followup.send(
                f"📨 Solicitud **#{aid}** enviada.\n"
                f"**Graduado:** {self.usuario.mention}\n"
                f"**Capacitación:** {cap}\n\n"
                f"Pendiente: **Director de Investigación y Docencia** → Autorizar y firmar.",
                ephemeral=True,
            )
        except Exception as e:
            print("[certificar] auth:", e)
            await inter.followup.send(f"❌ Error: `{e}`", ephemeral=True)


def registrar(bot: commands.Bot) -> None:
    """Registra /certificar solo si aún no está en el árbol."""
    presentes = {c.name for c in bot.tree.get_commands()}

    async def _abrir(inter: discord.Interaction, usuario: discord.Member):
        if not isinstance(inter.user, discord.Member) or not _puede_iniciar(inter.user):
            await inter.response.send_message("❌ Sin permiso para certificar.", ephemeral=True)
            return
        await inter.response.send_modal(ModalCertificar(bot, usuario))

    if "certificar" not in presentes:
        @bot.tree.command(
            name="certificar",
            description="Certificado RP → formulario → autorización Director Investigación y Docencia",
        )
        @app_commands.describe(usuario="Personal que recibe el certificado")
        async def certificar_cmd(inter: discord.Interaction, usuario: discord.Member):
            await _abrir(inter, usuario)
        print("[capacitacion_cert_ui] ✓ /certificar")
    else:
        print("[capacitacion_cert_ui] · /certificar ya registrado")

    # Subcomando del grupo si existe
    try:
        grupo = bot.tree.get_command("capacitacion")
        if grupo is not None and hasattr(grupo, "get_command"):
            if grupo.get_command("certificar") is None:
                @grupo.command(name="certificar", description="Igual que /certificar")
                @app_commands.describe(usuario="Personal que recibe el certificado")
                async def certificar_g(inter: discord.Interaction, usuario: discord.Member):
                    await _abrir(inter, usuario)
                print("[capacitacion_cert_ui] ✓ capacitacion certificar")
    except Exception as e:
        print("[capacitacion_cert_ui] grupo:", e)
