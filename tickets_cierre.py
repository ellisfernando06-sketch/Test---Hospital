# -*- coding: utf-8 -*
"""tickets_cierre.py — Transcripción al cerrar tickets + canal de logs."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Optional

import discord
from discord import app_commands, ui
from discord.ext import commands

import config

try:
    import permisos
except Exception:
    permisos = None

try:
    import logs_store
except Exception:
    logs_store = None


def _puede_cerrar(member: discord.Member) -> bool:
    if member.guild_permissions.manage_channels or member.guild_permissions.administrator:
        return True
    if permisos is None:
        return False
    keys = list(getattr(config, "TICKET_STAFF_KEYS", []) or []) + ["OWNER", "CO_OWNER"]
    try:
        return permisos.member_tiene_alguna_key(member, *keys)
    except Exception:
        return False


def _canal_logs_tickets(bot, guild: Optional[discord.Guild]) -> Optional[discord.TextChannel]:
    if logs_store is None:
        return None
    try:
        ch = logs_store.resolver_canal_log(bot, guild, "log_tickets") if guild else None
        if ch:
            return ch
    except Exception:
        pass
    cid = None
    try:
        cid = logs_store.get_canal_id("log_tickets")
    except Exception:
        pass
    if not cid and isinstance(getattr(config, "CANALES", None), dict):
        cid = config.CANALES.get("log_tickets")
    if cid and bot:
        ch = bot.get_channel(int(cid))
        if isinstance(ch, discord.TextChannel):
            return ch
    return None


async def hacer_transcripcion_y_enviar(
    channel: discord.TextChannel,
    bot,
    cerrado_por: str,
    *,
    abierto_por: str = "—",
) -> bool:
    try:
        from ticket_transcript import collect_messages, render_html, html_to_file, embed_resumen
    except Exception as e:
        print("[tickets_cierre] transcript import:", e)
        return False
    try:
        msgs = await collect_messages(channel, limit=800)
    except Exception as e:
        print("[tickets_cierre] collect:", e)
        msgs = []
    titulo = f"Ticket · {channel.name}"
    cat = channel.category.name if channel.category else "—"
    try:
        html_str = render_html(
            titulo=titulo, canal_nombre=channel.name, abierto_por=abierto_por,
            cerrado_por=cerrado_por, categoria=cat,
            creado=msgs[0].created_at if msgs else channel.created_at,
            cerrado=datetime.now(timezone.utc), messages=msgs, guild=channel.guild,
        )
        archivo = html_to_file(html_str, filename=f"{channel.name}.html")
        emb = embed_resumen(
            titulo=titulo, canal_nombre=channel.name, abierto_por=abierto_por,
            cerrado_por=cerrado_por, categoria=cat, n_msgs=len(msgs), color=0x5B8DEF,
        )
    except Exception as e:
        print("[tickets_cierre] render:", e)
        return False
    dest = _canal_logs_tickets(bot, channel.guild)
    try:
        if dest:
            await dest.send(embed=emb, file=archivo)
            return True
        await channel.send(embed=emb, file=archivo)
        await asyncio.sleep(2)
        return True
    except Exception as e:
        print("[tickets_cierre] send:", e)
        return False


class ConfirmarCierreTicket(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=60)
        self.bot = bot

    @ui.button(label="Transcribir y cerrar", style=discord.ButtonStyle.danger, emoji="📜")
    async def confirmar(self, inter: discord.Interaction, button: ui.Button):
        if not isinstance(inter.user, discord.Member) or not _puede_cerrar(inter.user):
            return await inter.response.send_message("Sin permiso.", ephemeral=True)
        ch = inter.channel
        if not isinstance(ch, discord.TextChannel):
            return await inter.response.send_message("Solo canales de texto.", ephemeral=True)
        await inter.response.edit_message(
            content=f"📜 Generando transcripción… (cerrado por {inter.user.mention})", view=None)
        ok = await hacer_transcripcion_y_enviar(ch, self.bot, inter.user.mention)
        dest = _canal_logs_tickets(self.bot, inter.guild)
        if ok and dest:
            await ch.send(f"✅ Transcripción enviada a {dest.mention}. Cerrando en 5 s…")
        elif ok:
            await ch.send("⚠️ Transcripción generada (sin canal de logs). Cerrando en 5 s…")
        else:
            await ch.send("⚠️ No se pudo generar la transcripción. Cerrando de todos modos…")
        await asyncio.sleep(5)
        try:
            await ch.delete(reason=f"Ticket cerrado por {inter.user}")
        except Exception:
            pass

    @ui.button(label="Cancelar", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancelar(self, inter: discord.Interaction, button: ui.Button):
        await inter.response.edit_message(content="Cierre cancelado.", view=None)


def registrar(bot: commands.Bot) -> None:
    try:
        import paneles

        async def cerrar_con_transcripcion(self, interaction: discord.Interaction, button: ui.Button):
            if not isinstance(interaction.user, discord.Member):
                return
            if not _puede_cerrar(interaction.user):
                name = getattr(interaction.channel, "name", "") or ""
                if not name.startswith(("ticket-", "apelacion-", "solicitud-", "sancion-", "reporte-", "consulta-")):
                    await interaction.response.send_message(
                        "❌ Solo staff puede cerrar tickets.", ephemeral=True)
                    return
            await interaction.response.send_message(
                "🔒 ¿Cerrar este ticket?\nSe generará una **transcripción** y se enviará al canal de logs configurado.",
                view=ConfirmarCierreTicket(bot),
                ephemeral=True,
            )

        paneles.CerrarTicketView.cerrar = cerrar_con_transcripcion
        print("[tickets_cierre] CerrarTicketView parcheado con transcripción")
    except Exception as e:
        print("[tickets_cierre] No se pudo parchear paneles:", e)

    @bot.tree.command(
        name="configurar_logs_tickets",
        description="Elige el canal donde se guardan transcripciones y logs de tickets",
    )
    @app_commands.describe(canal="Canal de texto para guardar transcripciones / logs de tickets")
    async def configurar_logs_tickets(inter: discord.Interaction, canal: discord.TextChannel):
        if not isinstance(inter.user, discord.Member):
            await inter.response.send_message("Solo en el servidor.", ephemeral=True)
            return
        ok = inter.user.guild_permissions.administrator
        if not ok and permisos is not None:
            try:
                ok = permisos.member_tiene_alguna_key(
                    inter.user, "OWNER", "CO_OWNER", "DIRECTOR_GENERAL", "DIRECTOR_ADMINISTRATIVO")
            except Exception:
                ok = False
        if not ok:
            await inter.response.send_message("Solo administración / owner.", ephemeral=True)
            return
        if logs_store is None:
            await inter.response.send_message("logs_store no disponible.", ephemeral=True)
            return
        logs_store.set_canal("log_tickets", canal.id)
        await inter.response.send_message(
            embed=discord.Embed(
                title="Canal de logs de tickets guardado",
                description=(
                    f"Las **transcripciones** de tickets se enviarán a {canal.mention}.\n\n"
                    f"Al **cerrar un ticket** se genera el HTML y se publica aquí automáticamente."
                ),
                color=0x2ECC71,
            ),
            ephemeral=True,
        )

    @bot.tree.command(
        name="ver_canal_logs_tickets",
        description="Muestra el canal configurado para transcripciones de tickets",
    )
    async def ver_canal_logs_tickets(inter: discord.Interaction):
        ch = _canal_logs_tickets(bot, inter.guild)
        if ch:
            await inter.response.send_message(
                f"Canal de transcripciones / logs de tickets: {ch.mention}", ephemeral=True)
        else:
            await inter.response.send_message(
                "No hay canal configurado. Usa `/configurar_logs_tickets`.\n"
                "También se busca: `log-tickets`, `transcripciones`, `logs-tickets`.",
                ephemeral=True,
            )

    @bot.listen("on_ready")
    async def _tickets_cierre_ready():
        if getattr(bot, "_tickets_cierre_view", False):
            return
        bot._tickets_cierre_view = True
        try:
            import paneles
            bot.add_view(paneles.CerrarTicketView())
            print("[tickets_cierre] Vista CerrarTicketView re-registrada")
        except Exception as e:
            print("[tickets_cierre] re-register view:", e)

    print("[tickets_cierre] OK — /configurar_logs_tickets + cierre con transcripción")
