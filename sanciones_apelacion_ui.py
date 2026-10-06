# -*- coding: utf-8 -*-
"""
Sanciones → DM con motivo + botón Apelar.
Advertencia / Sanción / Ban (cuarentena) → apelación a administración.
Panel de apelaciones + verificación de estado activo.
"""
from __future__ import annotations

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
        if "cuarentena" in (r.name or "").lower() or "quarantine" in (r.name or "").lower():
            return r
    try:
        return await guild.create_role(
            name="⏳ Cuarentena",
            colour=discord.Colour.dark_grey(),
            hoist=True,
            reason="Ban disciplinario — apelable",
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

    estado = "✅ Activa" if reg.get("activa") and not reg.get("anulada") else "❌ Anulada / inactiva"

    emb = discord.Embed(
        title=titulo,
        description=(
            f"Se ha registrado una medida en **{_hospital()}**.\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"**ID:** `#{reg.get('id')}`\n"
            f"**Tipo:** {(reg.get('tipo') or '—').title()}\n"
            f"**Estado:** {estado}\n"
            f"**Motivo:**\n{reg.get('motivo') or '—'}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Si consideras que es incorrecta, puedes **apelar** con el botón de abajo.\n"
            f"La apelación llega a **administración**."
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
        self.sancion_id = int(sancion_id)

    @ui.button(
        label="Apelar",
        style=discord.ButtonStyle.primary,
        emoji="⚖️",
        custom_id="sancion:apelar",
    )
    async def apelar(self, inter: discord.Interaction, button: ui.Button):
        if not inter.guild and inter.client.guilds:
            # DM: buscar guild y sanción
            pass

        # Desde DM el guild puede ser None — buscar en data
        if sanc is None:
            return await inter.response.send_message(
                "❌ Sistema de sanciones no disponible.", ephemeral=True
            )

        sid = self.sancion_id
        # Si vista persistente sin id, intentar del custom message
        if not sid and inter.message and inter.message.embeds:
            footer = inter.message.embeds[0].footer.text or ""
            # id en description
            import re

            m = re.search(r"#(\d+)", inter.message.embeds[0].description or "")
            if m:
                sid = int(m.group(1))

        reg = sanc.obtener_sancion(sid) if sid else None
        if not reg:
            # última activa del usuario
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

        # Asegurar staff admin ve el ticket (botones cierre ya en abrir_ticket_apelacion)
        await inter.followup.send(
            f"✅ Apelación abierta: **{canal.mention}**\n"
            f"Administración revisará el caso.",
            ephemeral=True,
        )


async def notificar_usuario(
    bot: commands.Bot, guild: discord.Guild, reg: dict
) -> bool:
    """DM con motivo + botón Apelar. Ban → cuarentena."""
    uid = int(reg.get("usuario_id") or 0)
    member = guild.get_member(uid)
    if not member:
        try:
            user = await bot.fetch_user(uid)
        except Exception:
            return False
        member = user  # type: ignore

    tipo = (reg.get("tipo") or "").lower()

    # Ban disciplinario → cuarentena (no saca del server si ya está; si se banea aparte, al volver tiene rol)
    if tipo == "ban" and isinstance(member, discord.Member):
        rol = await _rol_cuarentena(guild)
        if rol and rol not in member.roles:
            try:
                await member.add_roles(rol, reason=f"Ban disciplinario #{reg.get('id')}")
            except Exception as e:
                print(f"[sanciones_apelacion] cuarentena: {e}")

    emb = embed_dm_sancion(reg)
    view = ApelarSancionView(int(reg.get("id") or 0))
    try:
        target = member if hasattr(member, "send") else None
        if target is None:
            return False
        await target.send(embed=emb, view=view)
        return True
    except Exception as e:
        print(f"[sanciones_apelacion] dm: {e}")
        return False


def embed_panel_apelaciones() -> discord.Embed:
    hospital = _hospital()
    return discord.Embed(
        title=f"⚖️  Centro de Apelaciones · {hospital}",
        description=(
            f"Si recibiste una **advertencia**, **sanción** o **ban** (cuarentena),\n"
            f"puedes solicitar una revisión formal.\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"**1.** Usa el botón o el ticket de tipo **Apelación**\n"
            f"**2.** Indica el **ID** de la medida (sale en el MD)\n"
            f"**3.** Expón tus argumentos y pruebas\n"
            f"**4.** Administración resolverá\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"*Solo medidas **activas** pueden apelarse.*"
        ),
        color=0x5D6D7E,
        timestamp=datetime.now(timezone.utc),
    ).set_footer(text=f"{hospital}  ·  Apelaciones formales")


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
            f"✅ Apelación de **#{reg.get('id')}** → {canal.mention}",
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
        lineas = []
        for s in activas[-10:]:
            lineas.append(
                f"• **#{s.get('id')}** · `{s.get('tipo')}` · **Activa**\n"
                f"  Motivo: {(s.get('motivo') or '—')[:120]}"
            )
        emb = discord.Embed(
            title="📜 Tus sanciones activas",
            description="\n\n".join(lineas),
            color=0xE67E22,
        )
        await inter.response.send_message(embed=emb, ephemeral=True)


def registrar(bot: commands.Bot) -> None:
    try:
        bot.add_view(ApelarSancionView(0))
        bot.add_view(PanelApelacionesView())
    except Exception:
        pass

    # Parche: tras registrar_sancion → DM automático
    if sanc is not None and hasattr(sanc, "registrar_sancion"):
        _orig = sanc.registrar_sancion

        def _wrapped(*args, **kwargs):
            reg = _orig(*args, **kwargs)
            # Notificar en background vía bot si está en registry
            try:
                bot_ref = bot

                async def _later():
                    try:
                        await discord.utils.sleep_until(
                            datetime.now(timezone.utc)
                        )  # no-op almost
                    except Exception:
                        pass
                    for g in bot_ref.guilds:
                        try:
                            await notificar_usuario(bot_ref, g, reg)
                            break
                        except Exception:
                            continue

                bot.loop.create_task(_notify_safe(bot, reg))
            except Exception as e:
                print(f"[sanciones_apelacion] wrap: {e}")
            return reg

        sanc.registrar_sancion = _wrapped  # type: ignore

    async def _notify_safe(bot_, reg):
        await discord.utils.sleep_until(datetime.now(timezone.utc))
        import asyncio

        await asyncio.sleep(0.5)
        for g in bot_.guilds:
            ok = await notificar_usuario(bot_, g, reg)
            if ok:
                break

    # Re-bind create_task helper on bot
    bot._sancion_notify = _notify_safe  # type: ignore

    # Fix wrap to use _notify_safe
    if sanc is not None:

        def _wrapped2(*args, **kwargs):
            reg = _orig(*args, **kwargs) if sanc else None
            try:
                bot.loop.create_task(bot._sancion_notify(bot, reg))
            except Exception as e:
                print(f"[sanciones_apelacion] task: {e}")
            return reg

        if hasattr(sanc, "registrar_sancion"):
            # _orig already set
            try:
                sanc.registrar_sancion = _wrapped2  # type: ignore
            except Exception:
                pass

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
        description="[Staff] Advertencia / sanción / ban (cuarentena) + DM con apelación",
    )
    @app_commands.describe(
        usuario="Miembro",
        tipo="Tipo de medida",
        motivo="Motivo (se envía por MD)",
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
        # Usar original sin doble notify si ya parchado — registrar y notificar una vez
        reg = None
        try:
            # Llamar a la función actual (puede estar wrapped)
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

        # Notificar siempre (por si el wrap falló)
        dm_ok = await notificar_usuario(bot, inter.guild, reg)

        # Log embed
        try:
            emb_log = sanc.embed_sancion(reg, inter.guild)
            await sanc.enviar_log_sancion(bot, emb_log)
        except Exception:
            pass

        estado = (
            "✅ **Activa**"
            if reg.get("activa") and not reg.get("anulada")
            else "❌ Inactiva"
        )
        await inter.followup.send(
            f"✅ **{tipo.name}** registrada · ID `#{reg.get('id')}`\n"
            f"Estado: {estado}\n"
            f"MD al usuario: {'sí' if dm_ok else 'no (cerró MDs)'}\n"
            f"Motivo incluido + botón **Apelar**.",
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
                f"❌ No existe la sanción #{id_sancion}.", ephemeral=True
            )
        activa = bool(reg.get("activa")) and not bool(reg.get("anulada"))
        emb = discord.Embed(
            title=f"Sanción #{reg.get('id')}",
            description=(
                f"**Tipo:** {reg.get('tipo')}\n"
                f"**Estado:** {'✅ Activa' if activa else '❌ No activa / anulada'}\n"
                f"**Motivo:** {reg.get('motivo') or '—'}\n"
                f"**Usuario:** <@{reg.get('usuario_id')}>"
            ),
            color=0x2ECC71 if activa else 0x95A5A6,
        )
        await inter.response.send_message(embed=emb, ephemeral=True)

    print(
        "[sanciones_apelacion_ui] OK — DM+Apelar · panel_apelaciones · sancionar · estado activo"
    )
