# -*- coding: utf-8 -*
"""mejoras_ui.py — plantillas + ban OOC con apelación opcional."""
from __future__ import annotations

from typing import Dict, Optional

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

# user_id -> datos de apelación (solo si el ban tiene derecho a apelar)
_APELACIONES: Dict[int, dict] = {}


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


def _puede_moderar(member: discord.Member) -> bool:
    return bool(
        member.guild_permissions.administrator
        or member.guild_permissions.ban_members
    )


class ModalNotasEntrevista(ui.Modal, title="Notas de entrevista de apelación"):
    notas = ui.TextInput(
        label="Qué se habló / conclusiones",
        style=discord.TextStyle.paragraph,
        placeholder="Resumen de la entrevista…",
        required=True,
        max_length=1500,
    )

    def __init__(self, parent_view: "VistaResolverApelacion"):
        super().__init__()
        self.parent_view = parent_view

    async def on_submit(self, inter: discord.Interaction):
        self.parent_view.notas_entrevista = str(self.notas.value)
        uid = self.parent_view.user_id
        if uid in _APELACIONES:
            _APELACIONES[uid]["notas_entrevista"] = self.parent_view.notas_entrevista
            _APELACIONES[uid]["estado"] = "entrevistado"
        try:
            emb = inter.message.embeds[0] if inter.message and inter.message.embeds else None
            if emb:
                emb.color = 0x3498DB
                emb.add_field(
                    name="🎤 Entrevista registrada",
                    value=f"**Por:** {inter.user.mention}\n{self.parent_view.notas_entrevista[:800]}",
                    inline=False,
                )
                await inter.message.edit(embed=emb, view=self.parent_view)
        except Exception:
            pass
        await inter.response.send_message(
            "✅ Entrevista registrada. Ahora puedes **Aprobar** o **Negar**.",
            ephemeral=True,
        )
        try:
            u = await inter.client.fetch_user(uid)
            await u.send(
                "🎤 El staff registró tu entrevista de apelación. Pronto decidirán."
            )
        except Exception:
            pass


class VistaResolverApelacion(ui.View):
    def __init__(
        self,
        user_id: int = 0,
        guild_id: int = 0,
        motivo: str = "",
        version_hechos: str = "",
    ):
        super().__init__(timeout=None)
        self.user_id = int(user_id or 0)
        self.guild_id = int(guild_id or 0)
        self.motivo = motivo or ""
        self.version_hechos = version_hechos or ""
        self.notas_entrevista = ""

    @ui.button(label="Citar a entrevista", style=discord.ButtonStyle.primary, emoji="🎤")
    async def citar_entrevista(self, inter: discord.Interaction, _btn: ui.Button):
        if not isinstance(inter.user, discord.Member) or not _puede_moderar(inter.user):
            return await inter.response.send_message("❌ Solo staff con ban.", ephemeral=True)
        try:
            u = await inter.client.fetch_user(self.user_id)
            await u.send(
                f"🎤 **Cita de entrevista — apelación**\n"
                f"Staff: {inter.user.display_name}\n"
                f"Motivo del ban: {self.motivo or '—'}"
            )
        except Exception:
            pass
        if self.user_id in _APELACIONES:
            _APELACIONES[self.user_id]["estado"] = "cita_entrevista"
        await inter.response.send_modal(ModalNotasEntrevista(self))

    @ui.button(label="Aprobar (desbanear)", style=discord.ButtonStyle.success, emoji="✅")
    async def aprobar(self, inter: discord.Interaction, _btn: ui.Button):
        if not isinstance(inter.user, discord.Member) or not _puede_moderar(inter.user):
            return await inter.response.send_message("❌ Solo staff con ban.", ephemeral=True)
        guild = inter.guild or inter.client.get_guild(self.guild_id)
        if not guild:
            return await inter.response.send_message("❌ Servidor no encontrado.", ephemeral=True)
        await inter.response.defer()
        try:
            await guild.unban(
                discord.Object(id=self.user_id),
                reason=f"Apelación aprobada por {inter.user}"[:500],
            )
            resultado = f"✅ **APROBADA** por {inter.user.mention}\nDesbaneado: <@{self.user_id}>"
        except Exception as e:
            resultado = f"❌ No se pudo desbanear: `{e}`"
        try:
            emb = inter.message.embeds[0] if inter.message.embeds else discord.Embed(title="Apelación")
            emb.color = 0x2ECC71
            emb.add_field(name="Resolución", value=resultado[:1024], inline=False)
            await inter.message.edit(embed=emb, view=None)
        except Exception:
            pass
        await inter.followup.send(resultado, ephemeral=True)
        try:
            u = await inter.client.fetch_user(self.user_id)
            await u.send("✅ Tu apelación fue **aprobada**. Puedes volver a unirte si tienes invitación.")
        except Exception:
            pass
        _APELACIONES.pop(self.user_id, None)
        self.stop()

    @ui.button(label="Negar apelación", style=discord.ButtonStyle.danger, emoji="❌")
    async def negar(self, inter: discord.Interaction, _btn: ui.Button):
        if not isinstance(inter.user, discord.Member) or not _puede_moderar(inter.user):
            return await inter.response.send_message("❌ Solo staff con ban.", ephemeral=True)
        await inter.response.defer()
        resultado = f"❌ **NEGADA** por {inter.user.mention}\nBan de <@{self.user_id}> se mantiene."
        try:
            emb = inter.message.embeds[0] if inter.message.embeds else discord.Embed(title="Apelación")
            emb.color = 0xE74C3C
            emb.add_field(name="Resolución", value=resultado[:1024], inline=False)
            await inter.message.edit(embed=emb, view=None)
        except Exception:
            pass
        await inter.followup.send(resultado, ephemeral=True)
        try:
            u = await inter.client.fetch_user(self.user_id)
            await u.send(
                f"❌ Tu apelación fue **negada**. El ban se mantiene.\nMotivo: {self.motivo or '—'}"
            )
        except Exception:
            pass
        _APELACIONES.pop(self.user_id, None)
        self.stop()


async def _enviar_apelacion_a_staff(bot, user: discord.abc.User, data: dict) -> bool:
    if not data.get("permite_apelacion", True):
        return False
    guild_id = int(data.get("guild_id") or 0)
    staff_id = int(data.get("staff_id") or 0)
    motivo = data.get("motivo") or "—"
    version = data.get("version_hechos") or "_Sin versión_"
    guild = bot.get_guild(guild_id) if guild_id else None
    if not guild:
        return False

    emb = discord.Embed(
        title="📨 Apelación de ban OOC",
        description=(
            f"**Usuario:** {user.mention} (`{user.id}`)\n"
            f"**Motivo del ban:** {motivo}\n"
            + (f"**Staff que baneó:** <@{staff_id}>\n" if staff_id else "")
            + "\nRecomendado: **entrevista** antes de decidir."
        ),
        color=0xF39C12,
    )
    emb.add_field(name="📝 Versión del usuario", value=str(version)[:1000], inline=False)
    emb.set_footer(text="1) Entrevista → 2) Aprobar o Negar")

    vista = VistaResolverApelacion(
        user_id=user.id, guild_id=guild_id, motivo=motivo, version_hechos=str(version)
    )

    for tipo in ("log_sanciones_ooc", "log_sanciones", "log_moderacion", "log_solicitudes"):
        try:
            import logs_store
            ch = logs_store.resolver_canal_log(bot, guild, tipo)
            if ch:
                await ch.send(embed=emb, view=vista)
                return True
        except Exception:
            continue
    try:
        ch = guild.system_channel
        if ch and guild.me and ch.permissions_for(guild.me).send_messages:
            await ch.send(embed=emb, view=vista)
            return True
    except Exception:
        pass
    for ch in guild.text_channels:
        try:
            if guild.me and ch.permissions_for(guild.me).send_messages:
                await ch.send(embed=emb, view=vista)
                return True
        except Exception:
            continue
    return False


class VistaApelarBan(ui.View):
    def __init__(self, motivo: str = "", guild_id: int = 0, staff_id: int = 0):
        super().__init__(timeout=None)
        self.motivo = motivo or ""
        self.guild_id = int(guild_id or 0)
        self.staff_id = int(staff_id or 0)

    @ui.button(label="Apelar ban", style=discord.ButtonStyle.primary, emoji="📨")
    async def apelar(self, inter: discord.Interaction, _btn: ui.Button):
        data = _APELACIONES.get(inter.user.id)
        if not data or not data.get("permite_apelacion", False):
            try:
                await inter.response.send_message(
                    "⛔ Este ban **no tiene derecho a apelación**."
                )
            except Exception:
                pass
            return

        data["estado"] = "esperando_version"
        texto = (
            "📨 **Apelación iniciada.**\n\n"
            f"**Motivo de tu ban:** {self.motivo or data.get('motivo') or '—'}\n\n"
            "**Paso a paso:**\n"
            "1️⃣ Escribe en **un mensaje** tu versión de los hechos\n"
            "2️⃣ El staff revisará tu caso\n"
            "3️⃣ Pueden **citarte a entrevista**\n"
            "4️⃣ Luego **aprueban** o **niegan**\n\n"
            "Envía ahora tu versión de los hechos."
        )
        try:
            await inter.response.send_message(texto)
        except Exception:
            try:
                await inter.followup.send(texto)
            except Exception:
                pass
        try:
            _btn.disabled = True
            await inter.message.edit(view=self)
        except Exception:
            pass
        self.stop()


def registrar(bot: commands.Bot) -> None:

    @bot.listen("on_message")
    async def _apelacion_por_mensaje(msg: discord.Message):
        if msg.guild is not None or msg.author.bot:
            return

        contenido = msg.content.strip()
        data = _APELACIONES.get(msg.author.id)

        if contenido.upper() == "APELAR":
            if not data or not data.get("permite_apelacion", False):
                try:
                    await msg.channel.send(
                        "⛔ No puedes apelar.\n"
                        "Este ban **no tiene derecho a apelación**, "
                        "o no hay un ban reciente registrado."
                    )
                except Exception:
                    pass
                return
            data["estado"] = "esperando_version"
            try:
                await msg.channel.send(
                    f"📨 **Apelación iniciada.**\n\n"
                    f"**Motivo de tu ban:** {data.get('motivo') or '—'}\n\n"
                    f"**Paso a paso:**\n"
                    f"1️⃣ Escribe tu versión de los hechos (un mensaje)\n"
                    f"2️⃣ Staff revisa\n"
                    f"3️⃣ Pueden citarte a **entrevista**\n"
                    f"4️⃣ Aprueban o niegan\n\n"
                    f"Envía ahora tu versión."
                )
            except Exception:
                pass
            return

        if data and data.get("permite_apelacion") and data.get("estado") == "esperando_version":
            if contenido.upper() == "APELAR":
                return
            if len(contenido) < 10:
                try:
                    await msg.channel.send("Escribe más detalle sobre lo que pasó.")
                except Exception:
                    pass
                return
            data["version_hechos"] = contenido[:1500]
            data["estado"] = "enviada"
            ok = await _enviar_apelacion_a_staff(bot, msg.author, data)
            try:
                if ok:
                    await msg.channel.send(
                        "✅ Versión enviada al staff.\n"
                        "Pueden entrevistarte y luego aprobar o negar."
                    )
                else:
                    await msg.channel.send("No pude enviar la apelación (logs no configurados).")
            except Exception:
                pass

    # ── resto de comandos (balance, etc.) ─────────────────────────────
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
        await inter.response.send_message(
            embed=PlantillaBalance.principal(objetivo, saldo, movs), ephemeral=True
        )

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
                return await inter.response.send_message("❌ Solo tu historial.", ephemeral=True)
        try:
            movs = economia.historial(objetivo.id, 15)
        except Exception:
            movs = economia.ultimos_movimientos(objetivo.id, 15)
        await inter.response.send_message(
            embed=PlantillaHistorialFinanciero.principal(objetivo, movs), ephemeral=True
        )

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
        await inter.response.send_message(
            embed=PlantillaBalanceGeneral.principal(resumen), ephemeral=True
        )

    try:
        bot.tree.remove_command("anuncio")
    except Exception:
        pass

    @bot.tree.command(name="anuncio", description="Publica un anuncio oficial")
    @app_commands.describe(titulo="Título", mensaje="Contenido")
    async def anuncio_cmd(inter: discord.Interaction, titulo: str, mensaje: str):
        if not isinstance(inter.user, discord.Member):
            return await inter.response.send_message("Solo en servidor.", ephemeral=True)
        if not (
            inter.user.guild_permissions.administrator
            or (permisos and permisos.member_tiene_alguna_key(
                inter.user, "OWNER", "CO_OWNER", "DIRECTOR_GENERAL", "DIRECTOR_ADMINISTRATIVO"
            ))
        ):
            return await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
        await inter.response.send_message(embed=PlantillaAnuncio.publicar(titulo, mensaje, inter.user))

    try:
        bot.tree.remove_command("asignar_tarea")
    except Exception:
        pass

    @bot.tree.command(name="asignar_tarea", description="Asigna una tarea")
    @app_commands.describe(usuario="Personal", titulo="Título", detalle="Detalle", plazo="Plazo")
    async def tarea_cmd(
        inter: discord.Interaction,
        usuario: discord.Member,
        titulo: str,
        detalle: str,
        plazo: str = "",
    ):
        if not isinstance(inter.user, discord.Member):
            return await inter.response.send_message("Solo en servidor.", ephemeral=True)
        try:
            await usuario.send(
                embed=PlantillaTarea.asignacion(usuario, inter.user, titulo, detalle, plazo)
            )
        except Exception:
            return await inter.response.send_message("⚠️ No pude enviar DM.", ephemeral=True)
        await inter.response.send_message(
            embed=PlantillaTarea.confirmacion(usuario, titulo), ephemeral=True
        )

    # ── /ooc_ban con opción de apelación ──────────────────────────────
    try:
        bot.tree.remove_command("ooc_ban")
    except Exception:
        pass

    @bot.tree.command(
        name="ooc_ban",
        description="[OOC] Ban — elige si tiene derecho a apelación",
    )
    @app_commands.describe(
        usuario="Usuario a banear",
        motivo="Motivo del ban (se envía por DM)",
        apelacion="¿Este ban tiene derecho a apelación?",
    )
    @app_commands.choices(
        apelacion=[
            app_commands.Choice(name="Sí — con derecho a apelación", value="si"),
            app_commands.Choice(name="No — sin apelación", value="no"),
        ]
    )
    async def ooc_ban_cmd(
        inter: discord.Interaction,
        usuario: discord.Member,
        motivo: str,
        apelacion: app_commands.Choice[str],
    ):
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
        permite = apelacion.value == "si"
        dm_ok = False

        # Solo registrar apelación si tiene derecho
        if permite:
            _APELACIONES[usuario.id] = {
                "motivo": motivo,
                "guild_id": guild.id,
                "staff_id": inter.user.id,
                "permite_apelacion": True,
                "estado": "puede_apelar",
                "version_hechos": "",
            }
        else:
            _APELACIONES.pop(usuario.id, None)

        # DM al baneado
        try:
            emb = discord.Embed(
                title=f"🔨 Has sido baneado de {guild.name}",
                color=0xED4245,
            )
            emb.add_field(name="📋 Motivo del ban", value=motivo or "No especificado", inline=False)
            emb.add_field(
                name="👮 Staff",
                value=getattr(inter.user, "display_name", str(inter.user)),
                inline=True,
            )

            if permite:
                emb.add_field(
                    name="✅ Derecho a apelación",
                    value="**Sí** — puedes apelar",
                    inline=True,
                )
                emb.add_field(
                    name="📨 Cómo apelar (paso a paso)",
                    value=(
                        "**1.** Pulsa el botón **Apelar ban** o escribe **APELAR** aquí\n"
                        "**2.** Cuenta tu versión de los hechos\n"
                        "**3.** El staff puede citarte a **entrevista**\n"
                        "**4.** El staff **aprueba** (desban) o **niega**"
                    ),
                    inline=False,
                )
                vista = VistaApelarBan(
                    motivo=motivo, guild_id=guild.id, staff_id=inter.user.id
                )
                await usuario.send(embed=emb, view=vista)
            else:
                emb.add_field(
                    name="⛔ Derecho a apelación",
                    value="**No** — este ban **no** admite apelación",
                    inline=True,
                )
                emb.add_field(
                    name="ℹ️ Información",
                    value=(
                        "No podrás usar el botón de apelar ni el comando **APELAR**.\n"
                        "La decisión del staff es definitiva para este caso."
                    ),
                    inline=False,
                )
                await usuario.send(embed=emb)

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
        log_emb.add_field(
            name="Apelación",
            value="✅ Con derecho" if permite else "⛔ Sin derecho",
            inline=True,
        )
        extra = "" if dm_ok else "\n⚠️ No se pudo enviar el DM."
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
        @bot.tree.command(name="sancion_aplicar", description="Sanción abierta/cerrada + apelación")
        @app_commands.describe(
            usuario="Sancionado", tipo="Tipo", motivo="Motivo",
            modalidad="Abierta o cerrada", apelacion="¿Apelación?",
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
                usuario, inter.user, tipo, motivo,
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
        @app_commands.describe(item="Ítem", cantidad="Cantidad", area="Área", notas="Notas")
        async def solicitar_insumo_cmd(
            inter: discord.Interaction,
            item: str,
            cantidad: app_commands.Range[int, 1, 9999],
            area: str = "",
            notas: str = "",
        ):
            emb = PlantillaLogistica.solicitud_insumo(inter.user, item, int(cantidad), area, notas)
            await inter.response.send_message(embed=emb)

    if "cap_historial" not in {c.name for c in bot.tree.get_commands()}:
        @bot.tree.command(name="cap_historial", description="Historial de capacitaciones")
        @app_commands.describe(usuario="Usuario")
        async def cap_hist_cmd(inter: discord.Interaction, usuario: Optional[discord.Member] = None):
            if capacitaciones is None:
                return await inter.response.send_message("Módulo no disponible.", ephemeral=True)
            u = usuario or inter.user
            lista = capacitaciones.completadas_de(u.id)
            await inter.response.send_message(
                embed=PlantillaCapacitacion.historial(u, lista), ephemeral=True
            )

    print("[mejoras_ui] ✓ OK")
