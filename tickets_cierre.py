# -*- coding: utf-8 -*
"""tickets_cierre.py — Cierre de tickets CON transcripción + canal de logs."""
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
    if not isinstance(member, discord.Member):
        return False
    if member.guild_permissions.manage_channels or member.guild_permissions.administrator:
        return True
    if permisos is None:
        return False
    keys = list(getattr(config, "TICKET_STAFF_KEYS", []) or []) + ["OWNER", "CO_OWNER"]
    try:
        return permisos.member_tiene_alguna_key(member, *keys)
    except Exception:
        return False


def _canal_logs(bot, guild) -> Optional[discord.TextChannel]:
    if logs_store is None or guild is None:
        return None
    try:
        ch = logs_store.resolver_canal_log(bot, guild, "log_tickets")
        if ch:
            return ch
    except Exception:
        pass
    try:
        cid = logs_store.get_canal_id("log_tickets")
        if cid:
            ch = bot.get_channel(int(cid))
            if isinstance(ch, discord.TextChannel):
                return ch
    except Exception:
        pass
    return None


async def _transcribir(channel: discord.TextChannel, bot, cerrado_por: str) -> bool:
    try:
        from ticket_transcript import collect_messages, render_html, html_to_file, embed_resumen
    except Exception as e:
        print("[tickets_cierre] import transcript:", e)
        return False
    try:
        msgs = await collect_messages(channel, limit=800)
    except Exception as e:
        print("[tickets_cierre] collect:", e)
        msgs = []
    try:
        cat = channel.category.name if channel.category else "—"
        html_str = render_html(
            titulo=f"Ticket · {channel.name}",
            canal_nombre=channel.name,
            abierto_por="—",
            cerrado_por=cerrado_por,
            categoria=cat,
            creado=msgs[0].created_at if msgs else channel.created_at,
            cerrado=datetime.now(timezone.utc),
            messages=msgs,
            guild=channel.guild,
        )
        archivo = html_to_file(html_str, filename=f"{channel.name}.html")
        emb = embed_resumen(
            titulo=f"Ticket · {channel.name}",
            canal_nombre=channel.name,
            abierto_por="—",
            cerrado_por=cerrado_por,
            categoria=cat,
            n_msgs=len(msgs),
            color=0x5B8DEF,
        )
    except Exception as e:
        print("[tickets_cierre] render:", e)
        return False
    dest = _canal_logs(bot, channel.guild)
    try:
        if dest:
            await dest.send(embed=emb, file=archivo)
        else:
            await channel.send(embed=emb, file=archivo)
            await asyncio.sleep(1.5)
        return True
    except Exception as e:
        print("[tickets_cierre] send:", e)
        return False


class ConfirmarCierreTicket(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=90)
        self.bot = bot

    @ui.button(label="Transcribir y cerrar", style=discord.ButtonStyle.danger, emoji="📜")
    async def confirmar(self, inter: discord.Interaction, button: ui.Button):
        if not _puede_cerrar(inter.user):
            return await inter.response.send_message("Sin permiso.", ephemeral=True)
        ch = inter.channel
        if not isinstance(ch, discord.TextChannel):
            return await inter.response.send_message("Solo canales de texto.", ephemeral=True)
        await inter.response.edit_message(
            content=f"📜 Generando transcripción… ({inter.user.mention})", view=None
        )
        ok = await _transcribir(ch, self.bot, inter.user.mention)
        dest = _canal_logs(self.bot, inter.guild)
        if ok and dest:
            try:
                await ch.send(f"✅ Transcripción en {dest.mention}. Cerrando en 5 s…")
            except Exception:
                pass
        elif ok:
            try:
                await ch.send("⚠️ Transcripción lista (usa `/configurar_logs_tickets`). Cerrando…")
            except Exception:
                pass
        else:
            try:
                await ch.send("⚠️ Sin transcripción. Cerrando de todos modos…")
            except Exception:
                pass
        await asyncio.sleep(5)
        try:
            await ch.delete(reason=f"Cerrado por {inter.user}")
        except Exception:
            pass

    @ui.button(label="Cancelar", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancelar(self, inter: discord.Interaction, button: ui.Button):
        await inter.response.edit_message(content="Cierre cancelado.", view=None)


def _make_cerrar_view_class(bot_ref):
    class CerrarTicketView(ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        @ui.button(
            label="Añadir usuario",
            style=discord.ButtonStyle.secondary,
            emoji="👥",
            custom_id="ticket_adduser",
        )
        async def adduser(self, interaction: discord.Interaction, button: ui.Button):
            if not isinstance(interaction.user, discord.Member):
                return
            if not _puede_cerrar(interaction.user):
                await interaction.response.send_message("❌ Solo staff autorizado.", ephemeral=True)
                return
            if not interaction.guild:
                return
            try:
                from ticket_adduser import AnadirUsuarioView
                await interaction.response.send_message(
                    "👥 **Añadir persona al ticket**",
                    view=AnadirUsuarioView(bot_ref, 0, interaction.guild),
                    ephemeral=True,
                )
            except Exception:
                class _Pick(ui.View):
                    @ui.select(cls=ui.UserSelect, placeholder="Elige usuario…")
                    async def pick(self, inter: discord.Interaction, select: ui.UserSelect):
                        user = select.values[0]
                        ch = inter.channel
                        if isinstance(ch, discord.TextChannel) and inter.guild:
                            member = inter.guild.get_member(user.id)
                            if member:
                                await ch.set_permissions(
                                    member, view_channel=True, send_messages=True, attach_files=True
                                )
                                await inter.response.send_message(
                                    f"✅ {member.mention} añadido al ticket.", ephemeral=True
                                )
                                return
                        await inter.response.send_message("No se pudo añadir.", ephemeral=True)

                await interaction.response.send_message(
                    "Elige a quién añadir:", view=_Pick(), ephemeral=True
                )

        @ui.button(
            label="Cerrar ticket",
            style=discord.ButtonStyle.danger,
            emoji="🔒",
            custom_id="ticket_cerrar",
        )
        async def cerrar(self, interaction: discord.Interaction, button: ui.Button):
            if not isinstance(interaction.user, discord.Member):
                return
            name = getattr(interaction.channel, "name", "") or ""
            if not _puede_cerrar(interaction.user):
                if not name.startswith(
                    ("ticket-", "apelacion-", "solicitud-", "sancion-", "reporte-", "consulta-", "entrevista-")
                ):
                    await interaction.response.send_message(
                        "❌ Solo staff puede cerrar tickets.", ephemeral=True
                    )
                    return
            await interaction.response.send_message(
                "🔒 ¿Cerrar este ticket?\nSe generará una **transcripción** y se guardará en el canal de logs.",
                view=ConfirmarCierreTicket(bot_ref),
                ephemeral=True,
            )

    return CerrarTicketView


def registrar(bot: commands.Bot) -> None:
    NewView = _make_cerrar_view_class(bot)

    try:
        import paneles
        paneles.CerrarTicketView = NewView
        print("[tickets_cierre] paneles.CerrarTicketView REEMPLAZADA")
    except Exception as e:
        print("[tickets_cierre] paneles:", e)

    try:
        import sys
        for mod_name in ("hospital_core", "hospital_core_remote"):
            mod = sys.modules.get(mod_name)
            if mod is not None and hasattr(mod, "CerrarTicketView"):
                setattr(mod, "CerrarTicketView", NewView)
                print(f"[tickets_cierre] {mod_name}.CerrarTicketView actualizada")
    except Exception as e:
        print("[tickets_cierre] sys.modules:", e)

    try:
        bot.add_view(NewView())
    except Exception as e:
        print("[tickets_cierre] add_view:", e)

    @bot.listen("on_ready")
    async def _tickets_ready():
        if getattr(bot, "_tickets_cierre_ready", False):
            return
        bot._tickets_cierre_ready = True
        try:
            bot.add_view(NewView())
            print("[tickets_cierre] Vista persistente activa en on_ready")
        except Exception as e:
            print("[tickets_cierre] on_ready view:", e)

    @bot.tree.command(
        name="configurar_logs_tickets",
        description="Elige el canal donde se guardan transcripciones de tickets",
    )
    @app_commands.describe(canal="Canal de texto para transcripciones")
    async def configurar_logs_tickets(inter: discord.Interaction, canal: discord.TextChannel):
        if not isinstance(inter.user, discord.Member):
            await inter.response.send_message("Solo en el servidor.", ephemeral=True)
            return
        ok = inter.user.guild_permissions.administrator
        if not ok and permisos is not None:
            try:
                ok = permisos.member_tiene_alguna_key(
                    inter.user, "OWNER", "CO_OWNER", "DIRECTOR_GENERAL", "DIRECTOR_ADMINISTRATIVO"
                )
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
                title="✅ Canal de logs de tickets guardado",
                description=(
                    f"Las transcripciones se enviarán a {canal.mention}.\n"
                    f"Al **cerrar un ticket** se genera el HTML automáticamente."
                ),
                color=0x2ECC71,
            ),
            ephemeral=True,
        )

    @bot.tree.command(
        name="ver_canal_logs_tickets",
        description="Muestra el canal de transcripciones de tickets",
    )
    async def ver_canal_logs_tickets(inter: discord.Interaction):
        ch = _canal_logs(bot, inter.guild)
        if ch:
            await inter.response.send_message(f"Canal: {ch.mention}", ephemeral=True)
        else:
            await inter.response.send_message(
                "Sin canal. Usa `/configurar_logs_tickets`.\n"
                "O crea un canal: `log-tickets` / `transcripciones`.",
                ephemeral=True,
            )

    print("[tickets_cierre] OK — clase CerrarTicketView nueva + comandos logs")
