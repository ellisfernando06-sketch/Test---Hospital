# -*- coding: utf-8 -*
"""Comando /certificar: selector de certificación + modal (sin interacción negada)."""
from __future__ import annotations

import traceback

import discord
from discord import ui, app_commands
from discord.ext import commands

import certificaciones_abiertas

try:
    import permisos
except Exception:
    permisos = None


def _puede_iniciar(member) -> bool:
    if not isinstance(member, discord.Member):
        return False
    if member.guild_permissions.administrator:
        return True
    if not permisos:
        return False
    return bool(
        permisos.member_tiene_alguna_key(
            member,
            "OWNER",
            "CO_OWNER",
            "DIRECTOR_DOCENCIA",
            "DIRECTOR_GENERAL",
            "DIRECTOR",
            "ENCARGADO_AREA",
            "JEFE_DEPARTAMENTO",
            "SUPERVISOR",
        )
    )


class CertificacionSelect(ui.Select):
    def __init__(self, bot, usuario: discord.Member):
        self.bot = bot
        self.usuario = usuario
        certificaciones_abiertas.asegurar_defaults()
        items = certificaciones_abiertas.listar_certificaciones_activas()[:25]
        if not items:
            options = [
                discord.SelectOption(
                    label="(Sin certificaciones — avisa a un admin)",
                    value="none",
                    description="No hay certificaciones activas",
                )
            ]
            disabled = True
        else:
            options = []
            for x in items:
                options.append(
                    discord.SelectOption(
                        label=str(x.get("nombre") or f"#{x.get('id')}")[:100],
                        value=str(x["id"]),
                        description=str(x.get("descripcion") or "Sin descripción")[:100],
                    )
                )
            disabled = False
        super().__init__(
            placeholder="Elige la certificación…",
            options=options,
            disabled=disabled,
            min_values=1,
            max_values=1,
        )

    async def callback(self, inter: discord.Interaction):
        try:
            val = self.values[0] if self.values else ""
            if val in ("", "none", "0"):
                return await inter.response.send_message(
                    "❌ No hay certificación válida seleccionada.",
                    ephemeral=True,
                )
            cert = certificaciones_abiertas.obtener_certificacion(int(val))
            if not cert:
                return await inter.response.send_message(
                    "❌ Esa certificación ya no existe. Vuelve a usar `/certificar`.",
                    ephemeral=True,
                )
            await inter.response.send_modal(DatosCertificado(self.bot, self.usuario, cert))
        except Exception as e:
            traceback.print_exc()
            try:
                if inter.response.is_done():
                    await inter.followup.send(f"❌ Error: `{e}`", ephemeral=True)
                else:
                    await inter.response.send_message(f"❌ Error: `{e}`", ephemeral=True)
            except Exception:
                pass


class SeleccionCertificacion(ui.View):
    def __init__(self, bot, usuario: discord.Member):
        super().__init__(timeout=300)
        self.add_item(CertificacionSelect(bot, usuario))


class DatosCertificado(ui.Modal, title="Datos del estudiante"):
    cedula = ui.TextInput(label="Cédula / identificación", max_length=80, required=True)
    departamento = ui.TextInput(label="Ala o departamento", max_length=100, required=False)
    descripcion = ui.TextInput(
        label="Observaciones",
        style=discord.TextStyle.paragraph,
        max_length=400,
        required=False,
    )

    def __init__(self, bot, usuario, cert):
        super().__init__()
        self.bot = bot
        self.usuario = usuario
        self.cert = cert

    async def on_submit(self, inter: discord.Interaction):
        try:
            if not _puede_iniciar(inter.user):
                return await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
            if not self.cert:
                return await inter.response.send_message("❌ Certificación inválida.", ephemeral=True)

            await inter.response.defer(ephemeral=True)
            import firmas

            firma = firmas.obtener_firma_usuario(inter.user.id) or {}
            try:
                aid = await firmas.solicitar_autorizacion_certificado(
                    self.bot,
                    inter,
                    receptor=self.usuario,
                    certificacion=self.cert,
                    cedula=str(self.cedula),
                    departamento=str(self.departamento or "").strip(),
                    descripcion=str(self.descripcion or "").strip(),
                    firma_encargado_file=firma.get("file"),
                )
                await inter.followup.send(
                    f"✅ Solicitud **#{aid}** creada para {self.usuario.mention}.\n"
                    f"Certificación: **{self.cert.get('nombre')}**\n"
                    f"Requiere firmas: encargado, Docencia y Director del ala.",
                    ephemeral=True,
                )
            except Exception as exc:
                traceback.print_exc()
                await inter.followup.send(f"❌ No se pudo crear la solicitud: `{exc}`", ephemeral=True)
        except Exception as e:
            traceback.print_exc()
            try:
                if inter.response.is_done():
                    await inter.followup.send(f"❌ Error: `{e}`", ephemeral=True)
                else:
                    await inter.response.send_message(f"❌ Error: `{e}`", ephemeral=True)
            except Exception:
                pass


def registrar(bot: commands.Bot) -> None:
    print("[capacitacion_cert_ui] cargando…")
    try:
        certificaciones_abiertas.asegurar_defaults()
        # Quitar raíz vieja si existe para re-registrar limpio
        try:
            bot.tree.remove_command("certificar")
        except Exception:
            pass

        @bot.tree.command(
            name="certificar",
            description="Certifica un estudiante (elige certificación en el menú)",
        )
        @app_commands.describe(usuario="Estudiante que aprobó la certificación")
        async def certificar(inter: discord.Interaction, usuario: discord.Member):
            try:
                if not isinstance(inter.user, discord.Member):
                    return await inter.response.send_message(
                        "❌ Solo en el servidor.", ephemeral=True
                    )
                if not _puede_iniciar(inter.user):
                    return await inter.response.send_message(
                        "❌ Sin permiso para certificar.\n"
                        "Se requiere: Docencia, Director, Jefe, Supervisor, OWNER…",
                        ephemeral=True,
                    )

                certificaciones_abiertas.asegurar_defaults()
                items = certificaciones_abiertas.listar_certificaciones_activas()
                if not items:
                    return await inter.response.send_message(
                        "❌ No hay certificaciones activas en el sistema.\n"
                        "Un admin debe crearlas en el panel de certificaciones.",
                        ephemeral=True,
                    )

                await inter.response.send_message(
                    content=(
                        f"🎓 Certificar a **{usuario.display_name}**\n"
                        f"Selecciona la certificación en el menú de abajo:"
                    ),
                    view=SeleccionCertificacion(bot, usuario),
                    ephemeral=True,
                )
            except Exception as e:
                traceback.print_exc()
                try:
                    if inter.response.is_done():
                        await inter.followup.send(f"❌ Error: `{e}`", ephemeral=True)
                    else:
                        await inter.response.send_message(f"❌ Error: `{e}`", ephemeral=True)
                except Exception:
                    pass

        print("[capacitacion_cert_ui] ✓ OK")
    except Exception:
        print("[capacitacion_cert_ui] ✗ error:")
        traceback.print_exc()
