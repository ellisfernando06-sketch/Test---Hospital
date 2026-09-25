# -*- coding: utf-8 -*
"""
mejoras_ui.py — Aplica plantillas del cuaderno a comandos existentes.
"""
from __future__ import annotations

from typing import Optional

import discord
from discord import app_commands, ui
from discord.ext import commands

import economia
from plantillas_comandos import (
    PlantillaAnuncio,
    PlantillaBalance,
    PlantillaBalanceGeneral,
    PlantillaBan,
    PlantillaCapacitacion,
    PlantillaHistorialFinanciero,
    PlantillaLogistica,
    PlantillaSancion,
    PlantillaTarea,
)

try:
    import permisos
except Exception:
    permisos = None

try:
    import capacitaciones
except Exception:
    capacitaciones = None


def _es_finanzas(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    if permisos is None:
        return False
    try:
        return permisos.member_tiene_alguna_key(
            member, "OWNER", "CO_OWNER", "DIRECTOR_FINANCIERO"
        )
    except Exception:
        return False


class VistaApelarBan(ui.View):
    """Botón de apelación en DM."""

    def __init__(self, motivo: str = "", guild_id: int = 0, staff_id: int = 0):
        super().__init__(timeout=None)
        self.motivo = motivo or ""
        self.guild_id = int(guild_id or 0)
        self.staff_id = int(staff_id or 0)

    @ui.button(
        label="Apelar ban",
        style=discord.ButtonStyle.primary,
        emoji="📨",
        custom_id="ooc_ban_apelar",
    )
    async def apelar(self, inter: discord.Interaction, _btn: ui.Button):
        # En DM no existe ephemeral → provoca "error de interacción"
        msg = (
            "📨 Tu **apelación** fue enviada al staff del servidor.\n"
            f"Motivo del ban: **{self.motivo or '—'}**\n"
            "Un administrador la revisará."
        )
        try:
            if inter.guild is None:
                await inter.response.send_message(msg)
            else:
                await inter.response.send_message(msg, ephemeral=True)
        except Exception:
            try:
                if not inter.response.is_done():
                    await inter.response.send_message(msg)
                else:
                    await inter.followup.send(msg)
            except Exception:
                return

        bot = inter.client
        guild = bot.get_guild(self.guild_id) if self.guild_id else None

        desc = (
            f"**Usuario:** {inter.user.mention} (`{inter.user.id}`)\n"
            f"**Motivo del ban:** {self.motivo or '—'}\n"
        )
        if self.staff_id:
            desc += f"**Staff que baneó:** <@{self.staff_id}>"

        emb = discord.Embed(
            title="📨 Apelación de ban OOC",
            description=desc,
            color=0xF39C12,
        )
        emb.set_footer(text="Apelación enviada desde DM del baneado")

        if not guild:
            return

        for tipo in ("log_sanciones_ooc", "log_sanciones", "log_moderacion", "log_solicitudes"):
            try:
                import logs_store
                ch = logs_store.resolver_canal_log(bot, guild, tipo)
                if ch:
                    await ch.send(embed=emb)
                    return
            except Exception:
                continue
        try:
            ch = guild.system_channel
            if ch and ch.permissions_for(guild.me).send_messages:
                await ch.send(embed=emb)
                return
        except Exception:
            pass
        for ch in guild.text_channels:
            try:
                if ch.permissions_for(guild.me).send_messages:
                    await ch.send(embed=emb)
                    return
            except Exception:
                continue


def registrar(bot: commands.Bot) -> None:
    try:
        bot.add_view(VistaApelarBan())
    except Exception:
        pass

    try:
        bot.tree.remove_command("balance")
    except Exception:
        pass

    @bot.tree.command(name="balance", description="Consulta tu balance (plantilla mejorada)")
    @app_commands.describe(usuario="Usuario a consultar (solo finanzas/admin)")
    async def balance_cmd(inter: discord.Interaction, usuario: Optional[discord.Member] = None):
        objetivo = usuario or inter.user
        if usuario and usuario.id != inter.user.id:
            if not isinstance(inter.user, discord.Member) or not _es_finanzas(inter.user):
                return await inter.response.send_message(
                    "❌ Solo puedes ver tu propio balance.", ephemeral=True
                )
        saldo = economia.obtener_balance(objetivo.id)
        movs = []
        try:
            movs = economia.ultimos_movimientos(objetivo.id, 5)
        except Exception:
            try:
                movs = economia.historial(objetivo.id, 5)
            except Exception:
                movs = []
        emb = PlantillaBalance.principal(objetivo, saldo, movs)
        await inter.response.send_message(embed=emb, ephemeral=True)

    try:
        bot.tree.remove_command("historial_financiero")
    except Exception:
        pass

    @bot.tree.command(name="historial_financiero", description="Historial financiero estructurado")
    @app_commands.describe(usuario="Usuario (solo finanzas/admin)")
    async def hist_fin_cmd(inter: discord.Interaction, usuario: Optional[discord.Member] = None):
        objetivo = usuario or inter.user
        if usuario and usuario.id != inter.user.id:
            if not isinstance(inter.user, discord.Member) or not _es_finanzas(inter.user):
                return await inter.response.send_message(
                    "❌ Solo tu historial.", ephemeral=True
                )
        try:
            movs = economia.historial(objetivo.id, 15)
        except Exception:
            movs = economia.ultimos_movimientos(objetivo.id, 15)
        emb = PlantillaHistorialFinanciero.principal(objetivo, movs)
        await inter.response.send_message(embed=emb, ephemeral=True)

    try:
        bot.tree.remove_command("balance_general")
    except Exception:
        pass

    @bot.tree.command(name="balance_general", description="Balance general del hospital")
    async def bal_gen_cmd(inter: discord.Interaction):
        if not isinstance(inter.user, discord.Member) or not _es_finanzas(inter.user):
            return await inter.response.send_message("❌ Solo finanzas / admin.", ephemeral=True)
        try:
            resumen = economia.resumen_general(10)
        except Exception:
            resumen = {"total_en_circulacion": 0, "cuentas_activas": 0, "ultimos": []}
        if "ultimos" not in resumen and "movimientos" in resumen:
            resumen["ultimos"] = resumen["movimientos"]
        emb = PlantillaBalanceGeneral.principal(resumen)
        await inter.response.send_message(embed=emb, ephemeral=True)

    try:
        bot.tree.remove_command("anuncio")
    except Exception:
        pass

    @bot.tree.command(name="anuncio", description="Publica un anuncio oficial (plantilla profesional)")
    @app_commands.describe(titulo="Título del anuncio", mensaje="Contenido")
    async def anuncio_cmd(inter: discord.Interaction, titulo: str, mensaje: str):
        if not isinstance(inter.user, discord.Member):
            return await inter.response.send_message("Solo en servidor.", ephemeral=True)
        if not (
            inter.user.guild_permissions.administrator
            or (permisos and permisos.member_tiene_alguna_key(
                inter.user, "OWNER", "CO_OWNER", "DIRECTOR_GENERAL", "DIRECTOR_ADMINISTRATIVO"
            ))
        ):
            return await inter.response.send_message("❌ Sin permiso para anunciar.", ephemeral=True)
        emb = PlantillaAnuncio.publicar(titulo, mensaje, inter.user)
        await inter.response.send_message(embed=emb)

    try:
        bot.tree.remove_command("asignar_tarea")
    except Exception:
        pass

    @bot.tree.command(name="asignar_tarea", description="Asigna una tarea (plantilla mejorada)")
    @app_commands.describe(
        usuario="Personal",
        titulo="Título de la tarea",
        detalle="Detalle / instrucciones",
        plazo="Plazo opcional",
    )
    async def tarea_cmd(
        inter: discord.Interaction,
        usuario: discord.Member,
        titulo: str,
        detalle: str,
        plazo: str = "",
    ):
        if not isinstance(inter.user, discord.Member):
            return await inter.response.send_message("Solo en servidor.", ephemeral=True)
        emb_dm = PlantillaTarea.asignacion(usuario, inter.user, titulo, detalle, plazo)
        try:
            await usuario.send(embed=emb_dm)
        except Exception:
            return await inter.response.send_message(
                "⚠️ No pude enviar DM; revisa privacidad del usuario.", ephemeral=True
            )
        emb_ok = PlantillaTarea.confirmacion(usuario, titulo)
        await inter.response.send_message(embed=emb_ok, ephemeral=True)

    try:
        bot.tree.remove_command("ooc_ban")
    except Exception:
        pass

    @bot.tree.command(name="ooc_ban", description="[OOC] Ban con DM de motivo y botón de apelación")
    @app_commands.describe(usuario="Usuario a banear", motivo="Motivo del ban (se envía por DM)")
    async def ooc_ban_cmd(inter: discord.Interaction, usuario: discord.Member, motivo: str):
        if not isinstance(inter.user, discord.Member) or not inter.guild:
            return await inter.response.send_message("Solo en un servidor.", ephemeral=True)

        if not (
            inter.user.guild_permissions.ban_members
            or inter.user.guild_permissions.administrator
        ):
            return await inter.response.send_message("❌ Sin permiso de ban.", ephemeral=True)

        if usuario.id == inter.user.id:
            return await inter.response.send_message("❌ No puedes banearte a ti mismo.", ephemeral=True)

        if usuario.top_role >= inter.user.top_role and not inter.user.guild_permissions.administrator:
            return await inter.response.send_message(
                "❌ No puedes banear a alguien con rol igual o superior.", ephemeral=True
            )

        await inter.response.defer(ephemeral=True)

        guild = inter.guild
        guild_id = guild.id
        staff_id = inter.user.id
        dm_ok = False

        try:
            emb = PlantillaBan.dm_baneado(motivo, inter.user, guild.name)
            vista = VistaApelarBan(motivo=motivo, guild_id=guild_id, staff_id=staff_id)
            await usuario.send(embed=emb, view=vista)
            dm_ok = True
        except Exception as e:
            print(f"[ooc_ban] DM falló: {e}")

        try:
            await guild.ban(
                usuario,
                reason=f"[OOC] {motivo}"[:500],
                delete_message_seconds=0,
            )
        except TypeError:
            try:
                await guild.ban(usuario, reason=f"[OOC] {motivo}"[:500])
            except Exception as e:
                return await inter.followup.send(f"❌ No se pudo banear: `{e}`", ephemeral=True)
        except Exception as e:
            return await inter.followup.send(f"❌ No se pudo banear: `{e}`", ephemeral=True)

        log_emb = PlantillaBan.log(inter.user, usuario, motivo)
        extra = "" if dm_ok else "\n⚠️ No se pudo enviar el DM (el usuario tiene cerrados los mensajes)."
        await inter.followup.send(embed=log_emb, content=extra or None, ephemeral=True)

        for tipo in ("log_sanciones_ooc", "log_sanciones", "log_moderacion"):
            try:
                import logs_store
                ch = logs_store.resolver_canal_log(bot, guild, tipo)
                if ch:
                    await ch.send(embed=log_emb)
                    break
            except Exception:
                continue

    if "sancion_aplicar" not in {c.name for c in bot.tree.get_commands()}:
        @bot.tree.command(
            name="sancion_aplicar",
            description="Aplica sanción eligiendo abierta o con derecho a apelación",
        )
        @app_commands.describe(
            usuario="Sancionado",
            tipo="Tipo de sanción",
            motivo="Motivo",
            modalidad="Abierta o cerrada",
            apelacion="¿Derecho a apelación?",
        )
        @app_commands.choices(
            modalidad=[
                app_commands.Choice(name="Sanción abierta", value="abierta"),
                app_commands.Choice(name="Sanción cerrada", value="cerrada"),
            ],
            apelacion=[
                app_commands.Choice(name="Con derecho a apelación", value="si"),
                app_commands.Choice(name="Sin apelación", value="no"),
            ],
        )
        async def sancion_aplicar_cmd(
            inter: discord.Interaction,
            usuario: discord.Member,
            tipo: str,
            motivo: str,
            modalidad: app_commands.Choice[str],
            apelacion: app_commands.Choice[str],
        ):
            if not isinstance(inter.user, discord.Member):
                return
            emb = PlantillaSancion.registro(
                usuario,
                inter.user,
                tipo,
                motivo,
                abierta=(modalidad.value == "abierta"),
                con_apelacion=(apelacion.value == "si"),
            )
            await inter.response.send_message(embed=emb)
            try:
                await usuario.send(embed=emb)
            except Exception:
                pass

    if "solicitar_insumo" not in {c.name for c in bot.tree.get_commands()}:
        @bot.tree.command(name="solicitar_insumo", description="Solicita insumos a logística")
        @app_commands.describe(item="Nombre del ítem", cantidad="Cantidad", area="Área", notas="Notas")
        async def solicitar_insumo_cmd(
            inter: discord.Interaction,
            item: str,
            cantidad: app_commands.Range[int, 1, 9999],
            area: str = "",
            notas: str = "",
        ):
            emb = PlantillaLogistica.solicitud_insumo(inter.user, item, int(cantidad), area, notas)
            await inter.response.send_message(embed=emb)
            try:
                import logs_store
                ch = logs_store.resolver_canal_log(bot, inter.guild, "log_inventario")
                if ch:
                    await ch.send(embed=emb)
            except Exception:
                pass

    if "cap_historial" not in {c.name for c in bot.tree.get_commands()}:
        @bot.tree.command(name="cap_historial", description="Historial de capacitaciones (plantilla estructurada)")
        @app_commands.describe(usuario="Usuario")
        async def cap_hist_cmd(inter: discord.Interaction, usuario: Optional[discord.Member] = None):
            if capacitaciones is None:
                return await inter.response.send_message("Módulo no disponible.", ephemeral=True)
            u = usuario or inter.user
            lista = capacitaciones.completadas_de(u.id)
            emb = PlantillaCapacitacion.historial(u, lista)
            await inter.response.send_message(embed=emb, ephemeral=True)

    print("[mejoras_ui] ✓ plantillas aplicadas a comandos clave")
