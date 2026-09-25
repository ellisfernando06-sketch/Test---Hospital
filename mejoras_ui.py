# -*- coding: utf-8 -*
"""mejoras_ui.py — plantillas + ban OOC con apelación (cuarentena si hay apelación)."""
from __future__ import annotations

from datetime import timedelta
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
            "✅ Notas guardadas.", ephemeral=True
        )


class VistaResolverApelacion(ui.View):
    def __init__(
        self,
        user_id: int = 0,
        guild_id: int = 0,
        motivo: str = "",
        version_hechos: str = "",
        en_cuarentena: bool = True,
        staff_id: int = 0,
    ):
        super().__init__(timeout=None)
        self.user_id = int(user_id or 0)
        self.guild_id = int(guild_id or 0)
        self.motivo = motivo or ""
        self.version_hechos = version_hechos or ""
        self.notas_entrevista = ""
        self.en_cuarentena = en_cuarentena
        self.staff_id = int(staff_id or 0)

    @ui.button(label="Citar a entrevista", style=discord.ButtonStyle.primary, emoji="🎤")
    async def citar_entrevista(self, inter: discord.Interaction, _btn: ui.Button):
        if not isinstance(inter.user, discord.Member) or not _puede_moderar(inter.user):
            return await inter.response.send_message("❌ Solo staff con ban.", ephemeral=True)

        guild = inter.guild or inter.client.get_guild(self.guild_id)
        if not guild or not inter.channel:
            return await inter.response.send_message(
                "❌ No se pudo abrir la entrevista aquí.", ephemeral=True
            )

        await inter.response.defer(ephemeral=True)

        sancionado = guild.get_member(self.user_id)
        encargado = guild.get_member(self.staff_id) if self.staff_id else None

        rol_disc = None
        try:
            import roles_store
            rid = roles_store.obtener_id_key("DIRECTOR_DISCIPLINA")
            if rid:
                rol_disc = guild.get_role(int(rid))
        except Exception:
            pass
        if rol_disc is None:
            for r in guild.roles:
                if "disciplina" in (r.name or "").lower():
                    rol_disc = r
                    break

        nombre = f"entrevista-{getattr(sancionado, 'display_name', self.user_id)}"[:90]
        sala = None

        # 1) Intentar hilo privado
        try:
            if isinstance(inter.channel, (discord.TextChannel, discord.Thread)):
                parent = inter.channel.parent if isinstance(inter.channel, discord.Thread) else inter.channel
                if isinstance(parent, discord.TextChannel):
                    sala = await parent.create_thread(
                        name=nombre,
                        type=discord.ChannelType.private_thread,
                        invitable=False,
                        reason=f"Entrevista apelación {self.user_id}",
                    )
        except Exception as e:
            print("[entrevista] thread:", e)
            sala = None

        # 2) Fallback: canal de texto privado
        if sala is None:
            try:
                overs = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    guild.me: discord.PermissionOverwrite(
                        view_channel=True, send_messages=True, manage_channels=True
                    ),
                    inter.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                }
                if sancionado:
                    overs[sancionado] = discord.PermissionOverwrite(
                        view_channel=True, send_messages=True
                    )
                if encargado:
                    overs[encargado] = discord.PermissionOverwrite(
                        view_channel=True, send_messages=True
                    )
                if rol_disc:
                    overs[rol_disc] = discord.PermissionOverwrite(
                        view_channel=True, send_messages=True
                    )
                sala = await guild.create_text_channel(
                    name=nombre[:90],
                    overwrites=overs,
                    reason=f"Entrevista apelación {self.user_id}",
                )
            except Exception as e:
                return await inter.followup.send(
                    f"❌ No pude crear el grupo de entrevista: `{e}`",
                    ephemeral=True,
                )

        # Añadir personas al hilo privado
        async def _add(m):
            if not m or not isinstance(sala, discord.Thread):
                return
            try:
                await sala.add_user(m)
            except Exception:
                pass

        await _add(inter.user)
        if sancionado:
            await _add(sancionado)
        if encargado:
            await _add(encargado)
        if rol_disc:
            for m in list(rol_disc.members)[:15]:
                await _add(m)

        partes = [inter.user.mention, f"<@{self.user_id}>"]
        if self.staff_id:
            partes.append(f"<@{self.staff_id}>")
        if rol_disc:
            partes.append(rol_disc.mention)

        emb = discord.Embed(
            title="🎤 Sala de entrevista — apelación",
            description=(
                f"**Motivo de la sanción:** {self.motivo or '—'}\n\n"
                f"**Participantes previstos:**\n"
                f"• Sancionado: <@{self.user_id}>\n"
                f"• Encargado del ban: <@{self.staff_id or 0}>\n"
                f"• Director de Disciplina: {rol_disc.mention if rol_disc else '_configura el rol DIRECTOR_DISCIPLINA_'}\n"
                f"• Abrió la cita: {inter.user.mention}\n\n"
                f"Hablen el caso aquí. Luego en el panel de apelación: **Aprobar** o **Negar**."
            ),
            color=0x3498DB,
        )
        if self.version_hechos:
            emb.add_field(
                name="📝 Versión del sancionado",
                value=str(self.version_hechos)[:1000],
                inline=False,
            )

        try:
            await sala.send(content=" ".join(partes), embed=emb)
        except Exception as e:
            print("[entrevista] send:", e)

        if self.user_id in _APELACIONES:
            _APELACIONES[self.user_id]["estado"] = "cita_entrevista"
            _APELACIONES[self.user_id]["sala_id"] = getattr(sala, "id", None)

        try:
            u = await inter.client.fetch_user(self.user_id)
            await u.send(
                f"🎤 Te citaron a **entrevista de apelación**.\n"
                f"Motivo: {self.motivo or '—'}\n"
                f"Entra aquí: {getattr(sala, 'jump_url', sala.mention)}"
            )
        except Exception:
            pass

        await inter.followup.send(
            f"✅ Entrevista abierta: {sala.mention}\n"
            f"Incluye sancionado, encargado del ban y Director de Disciplina.",
            ephemeral=True,
        )

    @ui.button(label="Aprobar (liberar)", style=discord.ButtonStyle.success, emoji="✅")
    async def aprobar(self, inter: discord.Interaction, _btn: ui.Button):
        if not isinstance(inter.user, discord.Member) or not _puede_moderar(inter.user):
            return await inter.response.send_message("❌ Solo staff con ban.", ephemeral=True)
        guild = inter.guild or inter.client.get_guild(self.guild_id)
        if not guild:
            return await inter.response.send_message("❌ Servidor no encontrado.", ephemeral=True)
        await inter.response.defer()
        resultado = f"✅ **APROBADA** por {inter.user.mention}\nUsuario: <@{self.user_id}>"
        member = guild.get_member(self.user_id)
        if member:
            try:
                await member.timeout(None, reason=f"Apelación aprobada por {inter.user}")
                resultado += "\nCuarentena **retirada**."
            except Exception as e:
                resultado += f"\n⚠️ Timeout: {e}"
        else:
            try:
                await guild.unban(
                    discord.Object(id=self.user_id),
                    reason=f"Apelación aprobada por {inter.user}"[:500],
                )
                resultado += "\n**Desbaneado**."
            except Exception:
                pass
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
            await u.send("✅ Apelación **aprobada**. Restricción retirada.")
        except Exception:
            pass
        _APELACIONES.pop(self.user_id, None)
        self.stop()

    @ui.button(label="Negar (ban definitivo)", style=discord.ButtonStyle.danger, emoji="❌")
    async def negar(self, inter: discord.Interaction, _btn: ui.Button):
        if not isinstance(inter.user, discord.Member) or not _puede_moderar(inter.user):
            return await inter.response.send_message("❌ Solo staff con ban.", ephemeral=True)
        guild = inter.guild or inter.client.get_guild(self.guild_id)
        if not guild:
            return await inter.response.send_message("❌ Servidor no encontrado.", ephemeral=True)
        await inter.response.defer()
        resultado = f"❌ **NEGADA** por {inter.user.mention}\n"
        try:
            await guild.ban(
                discord.Object(id=self.user_id),
                reason=f"Apelación negada · {self.motivo}"[:500],
                delete_message_seconds=0,
            )
            resultado += f"Ban definitivo: <@{self.user_id}>"
        except TypeError:
            try:
                await guild.ban(
                    discord.Object(id=self.user_id),
                    reason=f"Apelación negada"[:500],
                )
                resultado += f"Ban definitivo: <@{self.user_id}>"
            except Exception as e:
                resultado += f"Error: `{e}`"
        except Exception as e:
            resultado += f"Error: `{e}`"
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
            await u.send(f"❌ Apelación **negada**. Ban aplicado.\nMotivo: {self.motivo or '—'}")
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
        title="📨 Apelación de sanción OOC",
        description=(
            f"**Usuario:** {user.mention} (`{user.id}`)\n"
            f"**Motivo:** {motivo}\n"
            + (f"**Staff del ban:** <@{staff_id}>\n" if staff_id else "")
            + "\nEn **cuarentena**. Usa **Citar a entrevista** para abrir sala con Disciplina."
        ),
        color=0xF39C12,
    )
    emb.add_field(name="📝 Versión del usuario", value=str(version)[:1000], inline=False)
    emb.set_footer(text="1) Entrevista en grupo → 2) Aprobar o Negar")

    vista = VistaResolverApelacion(
        user_id=user.id,
        guild_id=guild_id,
        motivo=motivo,
        version_hechos=str(version),
        en_cuarentena=True,
        staff_id=staff_id,
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

    @ui.button(label="Apelar", style=discord.ButtonStyle.primary, emoji="📨")
    async def apelar(self, inter: discord.Interaction, _btn: ui.Button):
        data = _APELACIONES.get(inter.user.id)
        if not data or not data.get("permite_apelacion", False):
            try:
                await inter.response.send_message("⛔ Sin derecho a apelación.")
            except Exception:
                pass
            return
        data["estado"] = "esperando_version"
        texto = (
            "📨 **Apelación iniciada.**\n\n"
            f"**Motivo:** {self.motivo or data.get('motivo') or '—'}\n\n"
            "Escribe en **un mensaje** tu versión de los hechos."
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
                    await msg.channel.send("⛔ No puedes apelar este caso.")
                except Exception:
                    pass
                return
            data["estado"] = "esperando_version"
            try:
                await msg.channel.send(
                    f"📨 **Apelación iniciada.**\nMotivo: {data.get('motivo') or '—'}\n\n"
                    f"Escribe tu versión de los hechos en un mensaje."
                )
            except Exception:
                pass
            return

        if data and data.get("permite_apelacion") and data.get("estado") == "esperando_version":
            if contenido.upper() == "APELAR":
                return
            if len(contenido) < 10:
                try:
                    await msg.channel.send("Escribe más detalle.")
                except Exception:
                    pass
                return
            data["version_hechos"] = contenido[:1500]
            data["estado"] = "enviada"
            ok = await _enviar_apelacion_a_staff(bot, msg.author, data)
            try:
                await msg.channel.send(
                    "✅ Enviado al staff." if ok else "No pude enviar (logs)."
                )
            except Exception:
                pass

    try:
        bot.tree.remove_command("balance")
    except Exception:
        pass

    @bot.tree.command(name="balance", description="Consulta tu balance")
    @app_commands.describe(usuario="Usuario (solo finanzas/admin)")
    async def balance_cmd(inter: discord.Interaction, usuario: Optional[discord.Member] = None):
        objetivo = usuario or inter.user
        if usuario and usuario.id != inter.user.id:
            if not isinstance(inter.user, discord.Member) or not _es_finanzas(inter.user):
                return await inter.response.send_message("❌ Solo tu balance.", ephemeral=True)
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

    @bot.tree.command(name="historial_financiero", description="Historial financiero")
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

    @bot.tree.command(name="balance_general", description="Balance general")
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

    @bot.tree.command(name="anuncio", description="Anuncio oficial")
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

    try:
        bot.tree.remove_command("ooc_ban")
    except Exception:
        pass

    @bot.tree.command(name="ooc_ban", description="[OOC] Sanción grave — con o sin apelación")
    @app_commands.describe(
        usuario="Usuario",
        motivo="Motivo",
        apelacion="¿Derecho a apelación?",
    )
    @app_commands.choices(
        apelacion=[
            app_commands.Choice(
                name="Sí — cuarentena + puede apelar",
                value="si",
            ),
            app_commands.Choice(
                name="No — ban inmediato sin apelación",
                value="no",
            ),
        ]
    )
    async def ooc_ban_cmd(
        inter: discord.Interaction,
        usuario: discord.Member,
        motivo: str,
        apelacion: app_commands.Choice[str],
    ):
        if not isinstance(inter.user, discord.Member) or not inter.guild:
            return await inter.response.send_message("Solo en servidor.", ephemeral=True)
        if not (
            inter.user.guild_permissions.ban_members
            or inter.user.guild_permissions.administrator
        ):
            return await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
        if usuario.id == inter.user.id:
            return await inter.response.send_message("❌ No a ti mismo.", ephemeral=True)
        if usuario.top_role >= inter.user.top_role and not inter.user.guild_permissions.administrator:
            return await inter.response.send_message("❌ Rol igual/superior.", ephemeral=True)

        await inter.response.defer(ephemeral=True)
        guild = inter.guild
        permite = apelacion.value == "si"
        dm_ok = False

        if permite:
            _APELACIONES[usuario.id] = {
                "motivo": motivo,
                "guild_id": guild.id,
                "staff_id": inter.user.id,
                "permite_apelacion": True,
                "estado": "puede_apelar",
                "version_hechos": "",
                "cuarentena": True,
            }
        else:
            _APELACIONES.pop(usuario.id, None)

        try:
            emb = discord.Embed(
                title=f"{'⚠️ Cuarentena (apelación)' if permite else '🔨 Ban'} · {guild.name}",
                color=0xF39C12 if permite else 0xED4245,
            )
            emb.add_field(name="📋 Motivo", value=motivo or "—", inline=False)
            emb.add_field(name="👮 Staff", value=inter.user.display_name, inline=True)
            if permite:
                emb.add_field(
                    name="📨 Cómo apelar",
                    value=(
                        "1. Pulsa **Apelar** o escribe **APELAR**\n"
                        "2. Cuenta los hechos\n"
                        "3. Staff abre **entrevista** (grupo)\n"
                        "4. Liberan o ban definitivo"
                    ),
                    inline=False,
                )
                await usuario.send(
                    embed=emb,
                    view=VistaApelarBan(
                        motivo=motivo, guild_id=guild.id, staff_id=inter.user.id
                    ),
                )
            else:
                emb.add_field(name="⛔ Apelación", value="No admite apelación", inline=False)
                await usuario.send(embed=emb)
            dm_ok = True
        except Exception as e:
            print("[ooc_ban] DM", e)

        if permite:
            try:
                await usuario.timeout(
                    timedelta(days=28),
                    reason=f"[OOC cuarentena] {motivo}"[:500],
                )
            except Exception as e:
                return await inter.followup.send(
                    f"❌ Timeout falló: `{e}` (permiso Moderar miembros / rol del bot)",
                    ephemeral=True,
                )
            estado_txt = "Cuarentena — puede apelar"
        else:
            try:
                await guild.ban(usuario, reason=f"[OOC] {motivo}"[:500], delete_message_seconds=0)
            except TypeError:
                try:
                    await guild.ban(usuario, reason=f"[OOC] {motivo}"[:500])
                except Exception as e:
                    return await inter.followup.send(f"❌ {e}", ephemeral=True)
            except Exception as e:
                return await inter.followup.send(f"❌ {e}", ephemeral=True)
            estado_txt = "Ban sin apelación"

        log_emb = PlantillaBan.log(inter.user, usuario, motivo)
        log_emb.add_field(name="Modo", value=estado_txt, inline=False)
        await inter.followup.send(
            embed=log_emb,
            content=None if dm_ok else "⚠️ Sin DM",
            ephemeral=True,
        )
        for tipo in ("log_sanciones_ooc", "log_sanciones", "log_moderacion"):
            try:
                import logs_store
                ch = logs_store.resolver_canal_log(bot, guild, tipo)
                if ch:
                    await ch.send(embed=log_emb)
                    break
            except Exception:
                continue

    print("[mejoras_ui] ✓ OK")
