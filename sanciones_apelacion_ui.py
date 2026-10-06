# -*- coding: utf-8 -*-
"""
Sanciones: DM + Apelar → log de apelaciones + botón entrevista (ticket privado).
Estado de sanción por menú (sin ID).
"""
from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from typing import Optional

import discord
from discord import app_commands, ui
from discord.ext import commands

import config

try:
    import sanciones as sanc
except Exception:
    sanc = None

try:
    import paneles as _paneles
except Exception:
    _paneles = None

try:
    import roles_store
except Exception:
    roles_store = None

try:
    import logs_store
except Exception:
    logs_store = None


def _hospital() -> str:
    return getattr(config, "NOMBRE_HOSPITAL", None) or "Hospital General"


def _es_staff(m: discord.Member) -> bool:
    if m.guild_permissions.administrator or m.guild_permissions.manage_guild:
        return True
    try:
        import permisos

        return permisos.member_tiene_alguna_key(
            m,
            "FUNDADOR_OWNER",
            "CO_OWNER",
            "OWNER",
            "ADMIN",
            "ADMIN_JEFE",
            "CANCILLER",
            "DIR_RRHH",
            "DIRECTOR_RRHH",
            "DIRECTOR_ADMINISTRATIVO",
        )
    except Exception:
        return False


async def _rol_cuarentena(guild: discord.Guild) -> Optional[discord.Role]:
    for r in guild.roles:
        rn = (r.name or "").lower()
        if "cuarentena" in rn or "quarantine" in rn:
            return r
    try:
        return await guild.create_role(
            name="⏳ Cuarentena",
            colour=discord.Colour.dark_grey(),
            hoist=True,
            reason="Ban disciplinario apelable",
        )
    except Exception:
        return None


def _canal_log_apelaciones(
    bot: commands.Bot, guild: discord.Guild
) -> Optional[discord.TextChannel]:
    # roles_store / logs_store / config / nombre
    for key in ("log_apelaciones", "canal_log_apelaciones", "apelaciones"):
        try:
            if roles_store:
                cid = roles_store.obtener_extra(key)
                if cid:
                    ch = guild.get_channel(int(cid))
                    if isinstance(ch, discord.TextChannel):
                        return ch
        except Exception:
            pass
        try:
            if logs_store:
                ch = logs_store.resolver_canal_log(bot, guild, key)
                if isinstance(ch, discord.TextChannel):
                    return ch
        except Exception:
            pass
    try:
        canales = getattr(config, "CANALES", {}) or {}
        cid = canales.get("log_apelaciones") or canales.get("apelaciones")
        if cid:
            ch = guild.get_channel(int(cid))
            if isinstance(ch, discord.TextChannel):
                return ch
    except Exception:
        pass
    for ch in guild.text_channels:
        n = (ch.name or "").lower()
        if "apelacion" in n or "apelación" in n:
            if "log" in n or n.startswith("→") or "admin" in n:
                return ch
    for ch in guild.text_channels:
        if "apelacion" in (ch.name or "").lower():
            return ch
    return None


def _categoria_tickets(guild: discord.Guild) -> Optional[discord.CategoryChannel]:
    cid = getattr(config, "TICKET_CATEGORIA_ID", None)
    if cid:
        ch = guild.get_channel(int(cid))
        if isinstance(ch, discord.CategoryChannel):
            return ch
    for c in guild.categories:
        if "ticket" in (c.name or "").lower():
            return c
    return None


def embed_dm_sancion(reg: dict) -> discord.Embed:
    tipo = (reg.get("tipo") or "sanción").lower()
    titulo = {
        "advertencia": "⚠️ Advertencia formal",
        "sancion": "🔨 Sanción disciplinaria",
        "sanción": "🔨 Sanción disciplinaria",
        "ban": "🚫 Ban disciplinario (cuarentena)",
    }.get(tipo, "📋 Medida disciplinaria")
    color = {
        "advertencia": 0xF1C40F,
        "sancion": 0xE67E22,
        "sanción": 0xE67E22,
        "ban": 0xC0392B,
    }.get(tipo, 0xE74C3C)
    activa = bool(reg.get("activa")) and not bool(reg.get("anulada"))
    emb = discord.Embed(
        title=titulo,
        description=(
            f"Se ha registrado una medida en **{_hospital()}**.\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"**ID:** `#{reg.get('id')}`\n"
            f"**Tipo:** {(reg.get('tipo') or '—').title()}\n"
            f"**Estado:** {'✅ Activa' if activa else '❌ No activa'}\n"
            f"**Motivo:**\n{reg.get('motivo') or '—'}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Si no estás de acuerdo, pulsa **Apelar**.\n"
            f"La solicitud va a **administración**."
        ),
        color=color,
        timestamp=datetime.now(timezone.utc),
    )
    if reg.get("duracion"):
        emb.add_field(name="Duración", value=str(reg["duracion"]), inline=True)
    emb.set_footer(text=f"{_hospital()}  ·  Sistema disciplinario")
    return emb


def embed_log_apelacion(
    member: discord.Member, reg: dict, ticket: Optional[discord.TextChannel]
) -> discord.Embed:
    activa = bool(reg.get("activa")) and not bool(reg.get("anulada"))
    emb = discord.Embed(
        title=f"⚖️ Nueva apelación · Sanción #{reg.get('id')}",
        description=(
            f"**Usuario:** {member.mention} (`{member.id}`)\n"
            f"**Tipo sanción:** `{reg.get('tipo')}`\n"
            f"**Estado sanción:** {'✅ Activa' if activa else '❌ Inactiva'}\n"
            f"**Motivo original:**\n{reg.get('motivo') or '—'}\n\n"
            f"**Ticket de apelación:** {ticket.mention if ticket else '—'}\n\n"
            f"Usa **Abrir entrevista** para un canal privado solo con el apelante."
        ),
        color=0x5D6D7E,
        timestamp=datetime.now(timezone.utc),
    )
    emb.set_author(
        name=member.display_name,
        icon_url=getattr(member.display_avatar, "url", None),
    )
    emb.set_footer(text=f"{_hospital()}  ·  Log de apelaciones")
    return emb


class LogApelacionView(ui.View):
    """Botones en el canal de logs de apelaciones."""

    def __init__(self, user_id: int = 0, sancion_id: int = 0):
        super().__init__(timeout=None)
        self.user_id = int(user_id or 0)
        self.sancion_id = int(sancion_id or 0)

    def _ids_from_message(self, inter: discord.Interaction):
        uid, sid = self.user_id, self.sancion_id
        if inter.message and inter.message.embeds:
            desc = inter.message.embeds[0].description or ""
            m = re.search(r"\((\d{15,20})\)", desc)
            if m:
                uid = int(m.group(1))
            m2 = re.search(r"#(\d+)", inter.message.embeds[0].title or "")
            if not m2:
                m2 = re.search(r"Sanción #(\d+)", desc)
            if m2:
                sid = int(m2.group(1))
        return uid, sid

    @ui.button(
        label="Abrir entrevista",
        style=discord.ButtonStyle.success,
        emoji="🎤",
        custom_id="apelacion_log:entrevista",
    )
    async def entrevista(self, inter: discord.Interaction, button: ui.Button):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _es_staff(inter.user):
            return await inter.response.send_message(
                "❌ Solo staff / administración.", ephemeral=True
            )

        uid, sid = self._ids_from_message(inter)
        member = inter.guild.get_member(uid)
        if not member:
            return await inter.response.send_message(
                "❌ El usuario no está en el servidor.", ephemeral=True
            )

        await inter.response.defer(ephemeral=True)

        cat = _categoria_tickets(inter.guild)
        overwrites = {
            inter.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                attach_files=True,
                read_message_history=True,
            ),
            inter.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                attach_files=True,
                read_message_history=True,
            ),
            inter.guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True,
            ),
        }
        # Admins
        for r in inter.guild.roles:
            if r.permissions.administrator and r != inter.guild.default_role:
                overwrites[r] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True
                )

        name = f"entrevista-apelacion-{member.name}"[:90].lower().replace(" ", "-")
        try:
            canal = await inter.guild.create_text_channel(
                name,
                category=cat,
                overwrites=overwrites,
                topic=f"Entrevista apelación #{sid} · {member}",
                reason=f"Entrevista apelación por {inter.user}",
            )
        except Exception as e:
            return await inter.followup.send(f"❌ {e}", ephemeral=True)

        emb = discord.Embed(
            title="🎤 Entrevista de apelación",
            description=(
                f"Canal **privado** para la entrevista.\n\n"
                f"**Apelante:** {member.mention}\n"
                f"**Staff:** {inter.user.mention}\n"
                f"**Sanción:** `#{sid}`\n\n"
                f"Mantengan el respeto. Al terminar, cierren el ticket."
            ),
            color=0x1ABC9C,
            timestamp=datetime.now(timezone.utc),
        )
        view_cierre = None
        if _paneles is not None:
            try:
                view_cierre = _paneles.CerrarTicketView()
            except Exception:
                pass
        kw = {
            "content": f"{member.mention} {inter.user.mention}",
            "embed": emb,
        }
        if view_cierre:
            kw["view"] = view_cierre
        await canal.send(**kw)
        await inter.followup.send(
            f"✅ Entrevista abierta: {canal.mention}", ephemeral=True
        )

    @ui.button(
        label="Ver sanción",
        style=discord.ButtonStyle.secondary,
        emoji="📜",
        custom_id="apelacion_log:ver",
    )
    async def ver(self, inter: discord.Interaction, button: ui.Button):
        if sanc is None:
            return await inter.response.send_message(
                "❌ Sistema no disponible.", ephemeral=True
            )
        uid, sid = self._ids_from_message(inter)
        reg = sanc.obtener_sancion(sid) if sid else None
        if not reg:
            return await inter.response.send_message(
                "❌ Sanción no encontrada.", ephemeral=True
            )
        activa = bool(reg.get("activa")) and not bool(reg.get("anulada"))
        emb = discord.Embed(
            title=f"Sanción #{reg.get('id')}",
            description=(
                f"**Tipo:** {reg.get('tipo')}\n"
                f"**Estado:** {'✅ Activa' if activa else '❌ No activa'}\n"
                f"**Motivo:** {reg.get('motivo') or '—'}\n"
                f"**Usuario:** <@{reg.get('usuario_id')}>"
            ),
            color=0x2ECC71 if activa else 0x95A5A6,
        )
        await inter.response.send_message(embed=emb, ephemeral=True)


async def enviar_log_apelacion(
    bot: commands.Bot,
    guild: discord.Guild,
    member: discord.Member,
    reg: dict,
    ticket: Optional[discord.TextChannel],
) -> None:
    canal = _canal_log_apelaciones(bot, guild)
    if not canal:
        print("[apelacion] sin canal log_apelaciones")
        return
    emb = embed_log_apelacion(member, reg, ticket)
    view = LogApelacionView(member.id, int(reg.get("id") or 0))
    try:
        await canal.send(embed=emb, view=view)
    except Exception as e:
        print(f"[apelacion] log: {e}")


async def abrir_apelacion_completa(
    bot: commands.Bot,
    guild: discord.Guild,
    member: discord.Member,
    reg: dict,
) -> Optional[discord.TextChannel]:
    if sanc is None:
        return None
    canal = await sanc.abrir_ticket_apelacion(guild, member, reg)
    await enviar_log_apelacion(bot, guild, member, reg, canal)
    return canal


class ApelarSancionView(ui.View):
    def __init__(self, sancion_id: int = 0):
        super().__init__(timeout=None)
        self.sancion_id = int(sancion_id or 0)

    @ui.button(
        label="Apelar",
        style=discord.ButtonStyle.primary,
        emoji="⚖️",
        custom_id="sancion:apelar",
    )
    async def apelar(self, inter: discord.Interaction, button: ui.Button):
        if sanc is None:
            return await inter.response.send_message(
                "❌ Sistema no disponible.", ephemeral=True
            )

        sid = self.sancion_id
        if not sid and inter.message and inter.message.embeds:
            m = re.search(r"#(\d+)", inter.message.embeds[0].description or "")
            if m:
                sid = int(m.group(1))

        reg = sanc.obtener_sancion(sid) if sid else None
        if not reg:
            lista = sanc.sanciones_de(inter.user.id, solo_activas=True)
            reg = lista[-1] if lista else None

        if not reg:
            return await inter.response.send_message(
                "❌ No hay sanción activa para apelar.", ephemeral=True
            )
        if reg.get("anulada") or not reg.get("activa", True):
            return await inter.response.send_message(
                "❌ Esa sanción ya no está activa.", ephemeral=True
            )

        await inter.response.defer(ephemeral=True)

        guild = inter.guild
        if guild is None:
            for g in inter.client.guilds:
                if g.get_member(inter.user.id):
                    guild = g
                    break
        if guild is None:
            return await inter.followup.send(
                "❌ No se encontró el servidor.", ephemeral=True
            )

        member = guild.get_member(inter.user.id)
        if not member:
            return await inter.followup.send(
                "❌ No estás en el servidor.", ephemeral=True
            )

        canal = await abrir_apelacion_completa(inter.client, guild, member, reg)
        if not canal:
            return await inter.followup.send(
                "❌ No se pudo abrir la apelación.", ephemeral=True
            )
        await inter.followup.send(
            f"✅ Apelación abierta: {canal.mention}\n"
            f"También quedó registrada en el **log de apelaciones**.",
            ephemeral=True,
        )


async def notificar_usuario(
    bot: commands.Bot, guild: discord.Guild, reg: dict
) -> bool:
    uid = int(reg.get("usuario_id") or 0)
    member = guild.get_member(uid)
    if not member:
        return False

    tipo = (reg.get("tipo") or "").lower()
    if tipo == "ban":
        rol = await _rol_cuarentena(guild)
        if rol and rol not in member.roles:
            try:
                await member.add_roles(
                    rol, reason=f"Ban disciplinario #{reg.get('id')}"
                )
            except Exception as e:
                print(f"[sanciones_apelacion] cuarentena: {e}")

    try:
        await member.send(
            embed=embed_dm_sancion(reg),
            view=ApelarSancionView(int(reg.get("id") or 0)),
        )
        return True
    except Exception as e:
        print(f"[sanciones_apelacion] dm: {e}")
        return False


def embed_panel_apelaciones() -> discord.Embed:
    return discord.Embed(
        title=f"⚖️  Centro de Apelaciones · {_hospital()}",
        description=(
            f"Si recibiste **advertencia**, **sanción** o **ban** (cuarentena),\n"
            f"puedes pedir revisión formal.\n\n"
            f"La apelación se registra en el **log de apelaciones**.\n"
            f"Administración puede abrir una **entrevista privada**.\n\n"
            f"*Solo medidas **activas** se pueden apelar.*"
        ),
        color=0x5D6D7E,
        timestamp=datetime.now(timezone.utc),
    ).set_footer(text=f"{_hospital()}  ·  Apelaciones formales")


class PanelApelacionesView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(
        label="Abrir apelación",
        style=discord.ButtonStyle.primary,
        emoji="⚖️",
        custom_id="panel_apelaciones:abrir",
    )
    async def abrir(self, inter: discord.Interaction, button: ui.Button):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if sanc is None:
            return await inter.response.send_message(
                "❌ Sistema no disponible.", ephemeral=True
            )
        lista = sanc.sanciones_de(inter.user.id, solo_activas=True)
        if not lista:
            return await inter.response.send_message(
                "No tienes sanciones **activas** para apelar.",
                ephemeral=True,
            )
        reg = lista[-1]
        await inter.response.defer(ephemeral=True)
        canal = await abrir_apelacion_completa(
            inter.client, inter.guild, inter.user, reg
        )
        if not canal:
            return await inter.followup.send(
                "❌ No se pudo crear el ticket.", ephemeral=True
            )
        await inter.followup.send(
            f"✅ Apelación **#{reg.get('id')}** → {canal.mention}",
            ephemeral=True,
        )

    @ui.button(
        label="Ver mis sanciones activas",
        style=discord.ButtonStyle.secondary,
        emoji="📜",
        custom_id="panel_apelaciones:estado",
    )
    async def estado(self, inter: discord.Interaction, button: ui.Button):
        if sanc is None:
            return await inter.response.send_message(
                "❌ Sistema no disponible.", ephemeral=True
            )
        lista = sanc.sanciones_de(inter.user.id)
        activas = [s for s in lista if s.get("activa") and not s.get("anulada")]
        if not activas:
            return await inter.response.send_message(
                "✅ No tienes sanciones activas.", ephemeral=True
            )
        lineas = [
            f"• **#{s.get('id')}** · `{s.get('tipo')}` · **Activa**\n"
            f"  Motivo: {(s.get('motivo') or '—')[:120]}"
            for s in activas[-10:]
        ]
        await inter.response.send_message(
            embed=discord.Embed(
                title="📜 Tus sanciones activas",
                description="\n\n".join(lineas),
                color=0xE67E22,
            ),
            ephemeral=True,
        )


def registrar(bot: commands.Bot) -> None:
    try:
        bot.add_view(ApelarSancionView(0))
        bot.add_view(PanelApelacionesView())
        bot.add_view(LogApelacionView(0, 0))
    except Exception:
        pass

    if sanc is not None and not getattr(sanc, "_apelacion_hook", False):
        _orig = sanc.registrar_sancion

        def _wrapped(*args, **kwargs):
            reg = _orig(*args, **kwargs)
            try:

                async def _task():
                    await asyncio.sleep(0.4)
                    for g in bot.guilds:
                        if await notificar_usuario(bot, g, reg):
                            break

                bot.loop.create_task(_task())
            except Exception as e:
                print(f"[sanciones_apelacion] hook: {e}")
            return reg

        sanc.registrar_sancion = _wrapped  # type: ignore
        sanc._apelacion_hook = True  # type: ignore

    @bot.tree.command(
        name="configurar_log_apelaciones",
        description="[Staff] Define el canal de logs de apelaciones",
    )
    @app_commands.describe(canal="Canal de logs")
    async def configurar_log_apelaciones(
        inter: discord.Interaction, canal: discord.TextChannel
    ):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _es_staff(inter.user):
            return await inter.response.send_message(
                "❌ Solo staff.", ephemeral=True
            )
        try:
            if roles_store:
                roles_store.guardar_extra("log_apelaciones", canal.id)
        except Exception as e:
            return await inter.response.send_message(
                f"❌ {e}", ephemeral=True
            )
        await inter.response.send_message(
            f"✅ Log de apelaciones: {canal.mention}", ephemeral=True
        )

    @bot.tree.command(
        name="panel_apelaciones",
        description="[Staff] Publica el panel de apelaciones",
    )
    @app_commands.describe(canal="Canal del panel")
    async def panel_apelaciones(
        inter: discord.Interaction,
        canal: Optional[discord.TextChannel] = None,
    ):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _es_staff(inter.user):
            return await inter.response.send_message(
                "❌ Solo staff.", ephemeral=True
            )
        destino = canal or (
            inter.channel if isinstance(inter.channel, discord.TextChannel) else None
        )
        if not destino:
            return await inter.response.send_message(
                "❌ Indica un canal.", ephemeral=True
            )
        await destino.send(
            embed=embed_panel_apelaciones(), view=PanelApelacionesView()
        )
        await inter.response.send_message(
            f"✅ Panel en {destino.mention}", ephemeral=True
        )

    @bot.tree.command(
        name="sancionar",
        description="[Staff] Advertencia / sanción / ban + MD con Apelar",
    )
    @app_commands.describe(
        usuario="Miembro",
        tipo="Tipo",
        motivo="Motivo",
        duracion="Duración opcional",
    )
    @app_commands.choices(
        tipo=[
            app_commands.Choice(name="Advertencia", value="advertencia"),
            app_commands.Choice(name="Sanción", value="sancion"),
            app_commands.Choice(name="Ban (cuarentena)", value="ban"),
        ]
    )
    async def sancionar(
        inter: discord.Interaction,
        usuario: discord.Member,
        tipo: app_commands.Choice[str],
        motivo: str,
        duracion: str = "",
    ):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _es_staff(inter.user):
            return await inter.response.send_message(
                "❌ Solo staff.", ephemeral=True
            )
        if sanc is None:
            return await inter.response.send_message(
                "❌ Módulo sanciones no cargado.", ephemeral=True
            )

        await inter.response.defer(ephemeral=True)
        try:
            reg = sanc.registrar_sancion(
                usuario.id,
                tipo.value,
                motivo,
                inter.user.id,
                duracion=duracion or "",
            )
        except TypeError:
            reg = sanc.registrar_sancion(
                usuario.id, tipo.value, motivo, inter.user.id
            )

        dm_ok = await notificar_usuario(bot, inter.guild, reg)
        try:
            await sanc.enviar_log_sancion(
                bot, sanc.embed_sancion(reg, inter.guild)
            )
        except Exception:
            pass

        activa = bool(reg.get("activa")) and not bool(reg.get("anulada"))
        await inter.followup.send(
            f"✅ **{tipo.name}** · `#{reg.get('id')}` · "
            f"{'✅ Activa' if activa else '❌'} · MD: {'sí' if dm_ok else 'no'}",
            ephemeral=True,
        )

    # ── Estado por menú (sin ID) ──────────────────────────────────────────

    class EstadoSancionSelect(ui.Select):
        def __init__(self, opciones: list):
            opts = []
            for s in opciones[:25]:
                sid = int(s.get("id") or 0)
                tipo = str(s.get("tipo") or "?")[:40]
                activa = bool(s.get("activa")) and not bool(s.get("anulada"))
                est = "Activa" if activa else "Inactiva"
                opts.append(
                    discord.SelectOption(
                        label=f"#{sid} · {tipo} · {est}"[:100],
                        value=str(sid),
                        description=(s.get("motivo") or "—")[:100],
                        emoji="✅" if activa else "❌",
                    )
                )
            super().__init__(
                placeholder="Elige la sanción…",
                min_values=1,
                max_values=1,
                options=opts,
            )

        async def callback(self, interaction: discord.Interaction):
            if sanc is None:
                return await interaction.response.send_message(
                    "❌ Sistema no disponible.", ephemeral=True
                )
            reg = sanc.obtener_sancion(int(self.values[0]))
            if not reg:
                return await interaction.response.send_message(
                    "❌ No encontrada.", ephemeral=True
                )
            activa = bool(reg.get("activa")) and not bool(reg.get("anulada"))
            emb = discord.Embed(
                title=f"Sanción #{reg.get('id')}",
                description=(
                    f"**Tipo:** {reg.get('tipo')}\n"
                    f"**Estado:** {'✅ Activa' if activa else '❌ No activa / anulada'}\n"
                    f"**Motivo:** {reg.get('motivo') or '—'}\n"
                    f"**Usuario:** <@{reg.get('usuario_id')}>\n"
                    f"**Fecha:** {str(reg.get('fecha') or '—')[:19]}"
                ),
                color=0x2ECC71 if activa else 0x95A5A6,
            )
            await interaction.response.edit_message(
                content=None, embed=emb, view=None
            )

    class EstadoSancionView(ui.View):
        def __init__(self, opciones: list):
            super().__init__(timeout=120)
            self.add_item(EstadoSancionSelect(opciones))

    @bot.tree.command(
        name="estado_sancion",
        description="Consulta estado de sanciones (menú, sin escribir ID)",
    )
    @app_commands.describe(usuario="Opcional: otro miembro (solo staff)")
    async def estado_sancion(
        inter: discord.Interaction,
        usuario: Optional[discord.Member] = None,
    ):
        if sanc is None:
            return await inter.response.send_message(
                "❌ Sistema no disponible.", ephemeral=True
            )

        if usuario is not None and usuario.id != inter.user.id:
            if not isinstance(inter.user, discord.Member) or not _es_staff(
                inter.user
            ):
                return await inter.response.send_message(
                    "❌ Solo staff puede consultar a otros.", ephemeral=True
                )
            target = usuario
        else:
            if not isinstance(inter.user, discord.Member):
                return await inter.response.send_message(
                    "❌ Solo en el servidor.", ephemeral=True
                )
            target = inter.user

        lista = sanc.sanciones_de(target.id)
        if not lista:
            return await inter.response.send_message(
                f"Sin sanciones para {target.mention}.",
                ephemeral=True,
            )

        lista = sorted(
            lista, key=lambda s: int(s.get("id") or 0), reverse=True
        )
        await inter.response.send_message(
            embed=discord.Embed(
                title=f"📜 Sanciones de {target.display_name}",
                description=(
                    f"**{len(lista)}** registro(s).\n"
                    f"Elige una en el menú para ver el **estado**."
                ),
                color=0x5D6D7E,
            ),
            view=EstadoSancionView(lista),
            ephemeral=True,
        )

    print(
        "[sanciones_apelacion_ui] ACTIVO — log apelaciones + entrevista + estado menú"
    )
