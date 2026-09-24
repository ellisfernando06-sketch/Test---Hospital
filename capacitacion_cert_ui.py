# -*- coding: utf-8 -*
"""
capacitacion_cert_ui.py — /capacitacion certificar con formulario previo.
Solicita la capacitación y datos antes de generar el diploma imagen.
"""
from __future__ import annotations

import discord
from discord import ui, app_commands
from discord.ext import commands

import config

try:
    import capacitaciones
except Exception:
    capacitaciones = None

try:
    from permisos import require_key, member_tiene_alguna_key
except Exception:
    require_key = None
    member_tiene_alguna_key = None


def _puede_certificar(member: discord.Member) -> bool:
    if not isinstance(member, discord.Member):
        return False
    if member.guild_permissions.administrator:
        return True
    if member_tiene_alguna_key is None:
        return False
    try:
        return member_tiene_alguna_key(
            member,
            "OWNER", "CO_OWNER",
            "DIRECTOR_DOCENCIA", "DIRECTOR_GENERAL",
            "DIRECTOR_MEDICO", "DIRECTOR_ENFERMERIA",
            "DIRECTOR_ADMINISTRATIVO", "DIRECTOR",
            "SUPERVISOR", "JEFE_DEPARTAMENTO",
        )
    except Exception:
        return False


class ModalCertificar(ui.Modal, title="🎓 Emitir certificado"):
    capacitacion = ui.TextInput(
        label="Capacitación que recibe",
        placeholder="Ej: RCP Básico, Trauma I, Protocolo quirófano…",
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
    observaciones = ui.TextInput(
        label="Observaciones (opcional)",
        style=discord.TextStyle.paragraph,
        placeholder="Calificación, horas, instructor…",
        max_length=200,
        required=False,
    )

    def __init__(self, bot: commands.Bot, usuario: discord.Member):
        super().__init__()
        self.bot = bot
        self.usuario = usuario

    async def on_submit(self, inter: discord.Interaction):
        if not _puede_certificar(inter.user):
            await inter.response.send_message("❌ Sin permiso para certificar.", ephemeral=True)
            return

        await inter.response.defer()

        cap = str(self.capacitacion).strip()
        desc = str(self.descripcion).strip() if self.descripcion.value else ""
        depto = str(self.departamento).strip() if self.departamento.value else ""
        notas = str(self.observaciones).strip() if self.observaciones.value else ""

        # Guardar en capacitaciones legacy
        if capacitaciones is not None:
            try:
                capacitaciones.certificar(self.usuario.id, cap, inter.user.id)
            except Exception as e:
                print("[capacitacion_cert] store:", e)

        # Registro docencia + número
        num = "CERT-RP"
        try:
            import docencia as _doc
            reg = _doc.emitir(
                self.usuario.id,
                cap,
                "personalizado",
                desc or notas,
                inter.user.id,
                notas=notas,
                departamento=depto,
            )
            num = f"CERT-{int(reg.get('id') or 0):05d}"
        except Exception as e:
            print("[capacitacion_cert] docencia:", e)

        hospital = getattr(config, "NOMBRE_HOSPITAL", "Hospital") or "Hospital"
        nombre = getattr(self.usuario, "display_name", None) or str(self.usuario)
        emisor = getattr(inter.user, "display_name", None) or str(inter.user)

        try:
            from certificado_imagen import generar_certificado
            buf = generar_certificado(
                nombre_receptor=nombre,
                titulo=cap,
                capacitacion=cap,
                hospital=hospital,
                emisor=emisor,
                numero=num,
                descripcion=desc or notas,
                departamento=depto,
            )
            archivo = discord.File(buf, filename=f"certificado_{self.usuario.id}.png")

            emb = discord.Embed(
                title="🎓 Certificado emitido",
                description=(
                    f"**Graduado:** {self.usuario.mention}\n"
                    f"**Capacitación:** {cap}\n"
                    f"**N.º:** `{num}`\n"
                    f"**Emitido por:** {inter.user.mention}\n"
                    f"📌 *Solo Roleplay*"
                ),
                color=0x8E44AD,
                timestamp=discord.utils.utcnow(),
            )
            if depto:
                emb.add_field(name="Área", value=depto, inline=True)
            if desc:
                emb.add_field(name="Contenido", value=desc[:200], inline=False)
            emb.set_footer(text=f"{hospital}  •  Docencia")

            await inter.followup.send(
                content=f"🎓 {self.usuario.mention} — certificado en **{cap}**",
                embed=emb,
                file=archivo,
            )

            # DM
            try:
                buf2 = generar_certificado(
                    nombre_receptor=nombre,
                    titulo=cap,
                    capacitacion=cap,
                    hospital=hospital,
                    emisor=emisor,
                    numero=num,
                    descripcion=desc or notas,
                    departamento=depto,
                )
                await self.usuario.send(
                    content=f"🎓 Has recibido un certificado de **{hospital}** por la capacitación **{cap}**:",
                    file=discord.File(buf2, filename=f"certificado_{self.usuario.id}.png"),
                )
            except Exception:
                pass

            # Log
            try:
                import logs_store
                ch = logs_store.resolver_canal_log(self.bot, inter.guild, "log_capacitaciones")
                if ch:
                    await ch.send(
                        content=f"🎓 Certificado · {self.usuario.mention} · **{cap}** · por {inter.user.mention}",
                        embed=emb,
                    )
            except Exception:
                pass

        except Exception as e:
            print("[capacitacion_cert] imagen:", e)
            await inter.followup.send(
                f"🎓 {self.usuario.mention} certificado en **{cap}**.\n"
                f"❌ No se pudo generar la imagen: `{e}`"
            )


def registrar(bot: commands.Bot) -> None:
    """
    Sustituye el subcomando certificar del grupo capacitacion
    para abrir el modal de datos.
    """

    async def _certificar_callback(inter: discord.Interaction, usuario: discord.Member):
        if not isinstance(inter.user, discord.Member) or not _puede_certificar(inter.user):
            await inter.response.send_message(
                "❌ Solo Docencia / Dirección / Supervisión pueden certificar.",
                ephemeral=True,
            )
            return
        await inter.response.send_modal(ModalCertificar(bot, usuario))

    # Intentar reemplazar el comando del grupo existente
    try:
        grupo = bot.tree.get_command("capacitacion")
        if grupo is not None and hasattr(grupo, "get_command"):
            viejo = grupo.get_command("certificar")
            if viejo is not None:
                try:
                    grupo.remove_command("certificar")
                except Exception:
                    pass

            @grupo.command(name="certificar", description="Certificar: pide datos y genera diploma en imagen")
            @app_commands.describe(usuario="Personal que recibe el certificado")
            async def certificar(inter: discord.Interaction, usuario: discord.Member):
                await _certificar_callback(inter, usuario)

            print("[capacitacion_cert_ui] ✓ certificar con modal OK")
            return
    except Exception as e:
        print("[capacitacion_cert_ui] no se pudo parchear grupo:", e)

    # Fallback: comando independiente
    @bot.tree.command(name="certificar_capacitacion", description="Certificar con diploma (formulario)")
    @app_commands.describe(usuario="Personal que recibe el certificado")
    async def certificar_capacitacion(inter: discord.Interaction, usuario: discord.Member):
        await _certificar_callback(inter, usuario)

    print("[capacitacion_cert_ui] fallback /certificar_capacitacion OK")
