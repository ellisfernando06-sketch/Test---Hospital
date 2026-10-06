# -*- coding: utf-8 -*-
"""DM sanción + Apelar · panel apelaciones · ban=cuarentena · estado activo."""
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
    import roles_store
except Exception:
    roles_store = None


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

        canal = await sanc.abrir_ticket_apelacion(guild, member, reg)
        if not canal:
            return await inter.followup.send(
                "❌ No se pudo abrir el ticket de apelación.", ephemeral=True
            )
        await inter.followup.send(
            f"✅ Apelación abierta: {canal.mention}\nAdministración revisará el caso.",
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
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"**1.** Botón de abajo o ticket **Apelación**\n"
            f"**2.** Usa el **ID** del MD de la medida\n"
            f"**3.** Argumentos y pruebas\n"
            f"**4.** Administración resuelve\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
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
        canal = await sanc.abrir_ticket_apelacion(inter.guild, inter.user, reg)
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
    except Exception:
        pass

    # Hook único sobre registrar_sancion
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
            f"✅ Panel de apelaciones en {destino.mention}", ephemeral=True
        )

    @bot.tree.command(
        name="sancionar",
        description="[Staff] Advertencia / sanción / ban (cuarentena) + MD con Apelar",
    )
    @app_commands.describe(
        usuario="Miembro",
        tipo="Tipo",
        motivo="Motivo (sale en el MD)",
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

        # Si el hook no corrió, notificar aquí
        dm_ok = await notificar_usuario(bot, inter.guild, reg)

        try:
            emb_log = sanc.embed_sancion(reg, inter.guild)
            await sanc.enviar_log_sancion(bot, emb_log)
        except Exception:
            pass

        activa = bool(reg.get("activa")) and not bool(reg.get("anulada"))
        await inter.followup.send(
            f"✅ **{tipo.name}** · ID `#{reg.get('id')}`\n"
            f"Estado: {'✅ Activa' if activa else '❌ No activa'}\n"
            f"MD: {'enviado' if dm_ok else 'falló (MD cerrado)'} + botón **Apelar**",
            ephemeral=True,
        )

    @bot.tree.command(
        name="estado_sancion",
        description="Consulta si una sanción está activa",
    )
    @app_commands.describe(id_sancion="Número de la sanción")
    async def estado_sancion(inter: discord.Interaction, id_sancion: int):
        if sanc is None:
            return await inter.response.send_message(
                "❌ Sistema no disponible.", ephemeral=True
            )
        reg = sanc.obtener_sancion(id_sancion)
        if not reg:
            return await inter.response.send_message(
                f"❌ No existe #{id_sancion}.", ephemeral=True
            )
        activa = bool(reg.get("activa")) and not bool(reg.get("anulada"))
        await inter.response.send_message(
            embed=discord.Embed(
                title=f"Sanción #{reg.get('id')}",
                description=(
                    f"**Tipo:** {reg.get('tipo')}\n"
                    f"**Estado:** {'✅ Activa' if activa else '❌ No activa / anulada'}\n"
                    f"**Motivo:** {reg.get('motivo') or '—'}\n"
                    f"**Usuario:** <@{reg.get('usuario_id')}>"
                ),
                color=0x2ECC71 if activa else 0x95A5A6,
            ),
            ephemeral=True,
        )

    print(
        "[sanciones_apelacion_ui] ACTIVO — DM+Apelar · panel · sancionar · estado"
    )
