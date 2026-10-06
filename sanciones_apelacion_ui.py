# -*- coding: utf-8 -*-
"""
MD sanción limpio + Apelar.
Log apelaciones: UN mensaje + Aceptar / Negar / Entrevista (sin spam de embeds).
Estado por menú.
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
    tipo = (reg.get("tipo") or "").lower()
    labels = {
        "advertencia": ("⚠️ Advertencia", 0xF1C40F),
        "disciplinaria": ("🔨 Sanción disciplinaria", 0xE67E22),
        "administrativa": ("📋 Sanción administrativa", 0x8E44AD),
        "sancion": ("🔨 Sanción disciplinaria", 0xE67E22),
        "sanción": ("🔨 Sanción disciplinaria", 0xE67E22),
        "ban": ("🚫 Ban (cuarentena)", 0xC0392B),
    }
    titulo, color = labels.get(tipo, ("📋 Medida", 0xE74C3C))
    activa = bool(reg.get("activa")) and not bool(reg.get("anulada"))
    return discord.Embed(
        title=titulo,
        description=(
            f"**ID** `#{reg.get('id')}` · **{'Activa' if activa else 'Inactiva'}**\n\n"
            f"{reg.get('motivo') or '—'}\n\n"
            f"Si no estás de acuerdo → **Apelar**."
        ),
        color=color,
        timestamp=datetime.now(timezone.utc),
    ).set_footer(text=_hospital())


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
        if not reg or reg.get("anulada") or not reg.get("activa", True):
            return await inter.response.send_message(
                "❌ No hay sanción activa para apelar.", ephemeral=True
            )
        await inter.response.defer(ephemeral=True)
        guild = inter.guild
        if guild is None:
            for g in inter.client.guilds:
                if g.get_member(inter.user.id):
                    guild = g
                    break
        if not guild:
            return await inter.followup.send(
                "❌ Servidor no encontrado.", ephemeral=True
            )
        member = guild.get_member(inter.user.id)
        if not member:
            return await inter.followup.send(
                "❌ No estás en el servidor.", ephemeral=True
            )
        canal = await sanc.abrir_ticket_apelacion(guild, member, reg)
        if not canal:
            return await inter.followup.send(
                "❌ No se pudo abrir la apelación.", ephemeral=True
            )
        await inter.followup.send(
            f"✅ Apelación: {canal.mention}", ephemeral=True
        )


async def notificar_usuario(
    bot: commands.Bot, guild: discord.Guild, reg: dict
) -> bool:
    # Solo tipos permitidos
    tipo = (reg.get("tipo") or "").lower()
    if tipo not in (
        "advertencia",
        "disciplinaria",
        "administrativa",
        "sancion",
        "sanción",
        "ban",
    ):
        return False

    uid = int(reg.get("usuario_id") or 0)
    member = guild.get_member(uid)
    if not member:
        return False

    if tipo == "ban":
        rol = await _rol_cuarentena(guild)
        if rol and rol not in member.roles:
            try:
                await member.add_roles(
                    rol, reason=f"Ban #{reg.get('id')}"
                )
            except Exception:
                pass

    try:
        await member.send(
            embed=embed_dm_sancion(reg),
            view=ApelarSancionView(int(reg.get("id") or 0)),
        )
        return True
    except Exception as e:
        print(f"[sanciones_apelacion] dm: {e}")
        return False


# ── Log de apelaciones: 1 mensaje, botones Aceptar / Negar / Entrevista ────


class LogApelacionView(ui.View):
    def __init__(self, user_id: int = 0, sancion_id: int = 0):
        super().__init__(timeout=None)
        self.user_id = int(user_id or 0)
        self.sancion_id = int(sancion_id or 0)

    def _ids(self, inter: discord.Interaction):
        uid, sid = self.user_id, self.sancion_id
        if inter.message and inter.message.embeds:
            desc = inter.message.embeds[0].description or ""
            title = inter.message.embeds[0].title or ""
            m = re.search(r"\((\d{15,20})\)", desc)
            if m:
                uid = int(m.group(1))
            m2 = re.search(r"#(\d+)", title) or re.search(r"#(\d+)", desc)
            if m2:
                sid = int(m2.group(1))
        return uid, sid

    @ui.button(
        label="Aceptar apelación",
        style=discord.ButtonStyle.success,
        emoji="✅",
        custom_id="apelacion_log:aceptar",
    )
    async def aceptar(self, inter: discord.Interaction, button: ui.Button):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en servidor.", ephemeral=True
            )
        if not _es_staff(inter.user):
            return await inter.response.send_message(
                "❌ Solo staff.", ephemeral=True
            )
        if sanc is None:
            return await inter.response.send_message(
                "❌ Sistema no disponible.", ephemeral=True
            )
        uid, sid = self._ids(inter)
        reg = sanc.obtener_sancion(sid) if sid else None
        if not reg:
            return await inter.response.send_message(
                "❌ Sanción no encontrada.", ephemeral=True
            )
        try:
            sanc.anular_sancion(
                sid, inter.user.id, f"Apelación aceptada por {inter.user}"
            )
        except Exception as e:
            return await inter.response.send_message(
                f"❌ {e}", ephemeral=True
            )

        # Quitar cuarentena si ban
        member = inter.guild.get_member(uid)
        if member:
            for r in list(member.roles):
                if "cuarentena" in (r.name or "").lower():
                    try:
                        await member.remove_roles(
                            r, reason="Apelación aceptada"
                        )
                    except Exception:
                        pass
            try:
                await member.send(
                    f"✅ Tu apelación de la medida `#{sid}` fue **aceptada**. "
                    f"La sanción queda anulada."
                )
            except Exception:
                pass

        # Editar el mismo mensaje (sin embeds nuevos)
        emb = inter.message.embeds[0] if inter.message.embeds else None
        if emb:
            emb = emb.copy()
            emb.color = 0x2ECC71
            emb.title = f"✅ Apelación aceptada · #{sid}"
            emb.set_footer(
                text=f"Aceptada por {inter.user.display_name} · {_hospital()}"
            )
            await inter.response.edit_message(embed=emb, view=None)
        else:
            await inter.response.send_message(
                f"✅ Apelación #{sid} aceptada.", ephemeral=True
            )

    @ui.button(
        label="Negar apelación",
        style=discord.ButtonStyle.danger,
        emoji="❌",
        custom_id="apelacion_log:negar",
    )
    async def negar(self, inter: discord.Interaction, button: ui.Button):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en servidor.", ephemeral=True
            )
        if not _es_staff(inter.user):
            return await inter.response.send_message(
                "❌ Solo staff.", ephemeral=True
            )
        uid, sid = self._ids(inter)
        member = inter.guild.get_member(uid)
        if member:
            try:
                await member.send(
                    f"❌ Tu apelación de la medida `#{sid}` fue **negada**. "
                    f"La sanción se mantiene."
                )
            except Exception:
                pass
        emb = inter.message.embeds[0] if inter.message and inter.message.embeds else None
        if emb:
            emb = emb.copy()
            emb.color = 0xE74C3C
            emb.title = f"❌ Apelación negada · #{sid}"
            emb.set_footer(
                text=f"Negada por {inter.user.display_name} · {_hospital()}"
            )
            await inter.response.edit_message(embed=emb, view=None)
        else:
            await inter.response.send_message(
                f"❌ Apelación #{sid} negada.", ephemeral=True
            )

    @ui.button(
        label="Entrevista",
        style=discord.ButtonStyle.secondary,
        emoji="🎤",
        custom_id="apelacion_log:entrevista",
    )
    async def entrevista(self, inter: discord.Interaction, button: ui.Button):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en servidor.", ephemeral=True
            )
        if not _es_staff(inter.user):
            return await inter.response.send_message(
                "❌ Solo staff.", ephemeral=True
            )
        uid, sid = self._ids(inter)
        member = inter.guild.get_member(uid)
        if not member:
            return await inter.response.send_message(
                "❌ Usuario no está en el servidor.", ephemeral=True
            )
        await inter.response.defer(ephemeral=True)
        cat = _categoria_tickets(inter.guild)
        overwrites = {
            inter.guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),
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
        for r in inter.guild.roles:
            if r.permissions.administrator and r != inter.guild.default_role:
                overwrites[r] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True
                )
        name = f"entrevista-apelacion-{member.name}"[:90].lower().replace(
            " ", "-"
        )
        try:
            canal = await inter.guild.create_text_channel(
                name,
                category=cat,
                overwrites=overwrites,
                topic=f"Entrevista apelación #{sid}",
                reason=f"Entrevista por {inter.user}",
            )
        except Exception as e:
            return await inter.followup.send(f"❌ {e}", ephemeral=True)

        view_cierre = None
        if _paneles is not None:
            try:
                view_cierre = _paneles.CerrarTicketView()
            except Exception:
                pass
        texto = (
            f"🎤 **Entrevista de apelación** `#{sid}`\n"
            f"Apelante: {member.mention} · Staff: {inter.user.mention}"
        )
        kw = {"content": texto}
        if view_cierre:
            kw["view"] = view_cierre
        await canal.send(**kw)
        await inter.followup.send(
            f"✅ Entrevista: {canal.mention}", ephemeral=True
        )


async def enviar_log_apelacion(
    bot: commands.Bot,
    guild: discord.Guild,
    member: discord.Member,
    reg: dict,
    ticket: Optional[discord.TextChannel],
) -> None:
    canal = _canal_log_apelaciones(bot, guild)
    if not canal:
        return
    # Un solo embed corto
    emb = discord.Embed(
        title=f"⚖️ Apelación #{reg.get('id')}",
        description=(
            f"{member.mention} (`{member.id}`)\n"
            f"**Tipo:** {reg.get('tipo')} · **Ticket:** {ticket.mention if ticket else '—'}\n"
            f"**Motivo:** {(reg.get('motivo') or '—')[:300]}"
        ),
        color=0x5D6D7E,
        timestamp=datetime.now(timezone.utc),
    )
    view = LogApelacionView(member.id, int(reg.get("id") or 0))
    try:
        await canal.send(embed=emb, view=view)
    except Exception as e:
        print(f"[apelacion] log: {e}")


def embed_panel_apelaciones() -> discord.Embed:
    return discord.Embed(
        title=f"⚖️ Apelaciones · {_hospital()}",
        description=(
            "Si tienes una **advertencia**, **sanción disciplinaria** "
            "o **administrativa** activa, puedes apelar.\n\n"
            "Administración verá la solicitud en el log y podrá "
            "**aceptar**, **negar** o abrir **entrevista**."
        ),
        color=0x5D6D7E,
    ).set_footer(text=_hospital())


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
                "No tienes sanciones activas.", ephemeral=True
            )
        reg = lista[-1]
        await inter.response.defer(ephemeral=True)
        canal = await sanc.abrir_ticket_apelacion(
            inter.guild, inter.user, reg
        )
        if not canal:
            return await inter.followup.send(
                "❌ No se pudo crear el ticket.", ephemeral=True
            )
        await inter.followup.send(
            f"✅ {canal.mention}", ephemeral=True
        )

    @ui.button(
        label="Mis sanciones activas",
        style=discord.ButtonStyle.secondary,
        emoji="📜",
        custom_id="panel_apelaciones:estado",
    )
    async def estado(self, inter: discord.Interaction, button: ui.Button):
        if sanc is None:
            return await inter.response.send_message(
                "❌ Sistema no disponible.", ephemeral=True
            )
        lista = [
            s
            for s in sanc.sanciones_de(inter.user.id)
            if s.get("activa") and not s.get("anulada")
        ]
        if not lista:
            return await inter.response.send_message(
                "✅ Sin sanciones activas.", ephemeral=True
            )
        lineas = [
            f"`#{s.get('id')}` · {s.get('tipo')} · {(s.get('motivo') or '')[:80]}"
            for s in lista[-10:]
        ]
        await inter.response.send_message(
            "\n".join(lineas), ephemeral=True
        )


def registrar(bot: commands.Bot) -> None:
    try:
        bot.add_view(ApelarSancionView(0))
        bot.add_view(PanelApelacionesView())
        bot.add_view(LogApelacionView(0, 0))
    except Exception:
        pass

    # Wrap registrar_sancion: solo notifica si no viene del hook (skip)
    if sanc is not None and not getattr(sanc, "_apelacion_hook_v3", False):
        _orig = sanc.registrar_sancion

        def _wrapped(*args, **kwargs):
            reg = _orig(*args, **kwargs)
            if getattr(sanc, "_skip_notify", False):
                return reg
            # Solo tipos permitidos
            tipo = (reg.get("tipo") or "").lower()
            if tipo not in (
                "advertencia",
                "disciplinaria",
                "administrativa",
                "sancion",
                "sanción",
                "ban",
            ):
                return reg
            try:

                async def _task():
                    await asyncio.sleep(0.3)
                    for g in bot.guilds:
                        if await notificar_usuario(bot, g, reg):
                            break

                bot.loop.create_task(_task())
            except Exception:
                pass
            return reg

        sanc.registrar_sancion = _wrapped  # type: ignore
        sanc._apelacion_hook_v3 = True  # type: ignore

    @bot.tree.command(
        name="configurar_log_apelaciones",
        description="[Staff] Canal de logs de apelaciones",
    )
    @app_commands.describe(canal="Canal")
    async def configurar_log_apelaciones(
        inter: discord.Interaction, canal: discord.TextChannel
    ):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en servidor.", ephemeral=True
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
            f"✅ Log apelaciones: {canal.mention}", ephemeral=True
        )

    @bot.tree.command(
        name="panel_apelaciones",
        description="[Staff] Panel de apelaciones",
    )
    @app_commands.describe(canal="Canal")
    async def panel_apelaciones(
        inter: discord.Interaction,
        canal: Optional[discord.TextChannel] = None,
    ):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en servidor.", ephemeral=True
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
                "❌ Indica canal.", ephemeral=True
            )
        await destino.send(
            embed=embed_panel_apelaciones(), view=PanelApelacionesView()
        )
        await inter.response.send_message(
            f"✅ {destino.mention}", ephemeral=True
        )

    class EstadoSancionSelect(ui.Select):
        def __init__(self, opciones: list):
            opts = []
            for s in opciones[:25]:
                sid = int(s.get("id") or 0)
                tipo = str(s.get("tipo") or "?")[:30]
                activa = bool(s.get("activa")) and not bool(s.get("anulada"))
                opts.append(
                    discord.SelectOption(
                        label=f"#{sid} · {tipo} · {'Activa' if activa else 'Inactiva'}"[
                            :100
                        ],
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
                    "❌ No disponible.", ephemeral=True
                )
            reg = sanc.obtener_sancion(int(self.values[0]))
            if not reg:
                return await interaction.response.send_message(
                    "❌ No encontrada.", ephemeral=True
                )
            activa = bool(reg.get("activa")) and not bool(reg.get("anulada"))
            texto = (
                f"**#{reg.get('id')}** · {reg.get('tipo')} · "
                f"{'✅ Activa' if activa else '❌ Inactiva'}\n"
                f"{reg.get('motivo') or '—'}\n"
                f"Usuario: <@{reg.get('usuario_id')}>"
            )
            await interaction.response.edit_message(
                content=texto, embed=None, view=None
            )

    class EstadoSancionView(ui.View):
        def __init__(self, opciones: list):
            super().__init__(timeout=120)
            self.add_item(EstadoSancionSelect(opciones))

    @bot.tree.command(
        name="estado_sancion",
        description="Estado de sanciones (menú)",
    )
    @app_commands.describe(usuario="Otro miembro (solo staff)")
    async def estado_sancion(
        inter: discord.Interaction,
        usuario: Optional[discord.Member] = None,
    ):
        if sanc is None:
            return await inter.response.send_message(
                "❌ No disponible.", ephemeral=True
            )
        if usuario and usuario.id != inter.user.id:
            if not isinstance(inter.user, discord.Member) or not _es_staff(
                inter.user
            ):
                return await inter.response.send_message(
                    "❌ Solo staff.", ephemeral=True
                )
            target = usuario
        else:
            if not isinstance(inter.user, discord.Member):
                return await inter.response.send_message(
                    "❌ Solo en servidor.", ephemeral=True
                )
            target = inter.user
        lista = sanc.sanciones_de(target.id)
        if not lista:
            return await inter.response.send_message(
                f"Sin sanciones para {target.mention}.", ephemeral=True
            )
        lista = sorted(
            lista, key=lambda s: int(s.get("id") or 0), reverse=True
        )
        await inter.response.send_message(
            content=f"Sanciones de **{target.display_name}** — elige una:",
            view=EstadoSancionView(lista),
            ephemeral=True,
        )

    print(
        "[sanciones_apelacion_ui] v3 — 1 MD · log 1 mensaje · Aceptar/Negar/Entrevista"
    )
