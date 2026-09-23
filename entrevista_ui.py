# -*- coding: utf-8 -*
"""entrevista_ui.py — Botón Hacer entrevista + transcripción."""
from __future__ import annotations

import json
import os
import asyncio
from datetime import datetime, timezone

import discord
from discord import ui
from discord.ext import commands

import config

try:
    import permisos
except Exception:
    permisos = None


def _puede(member) -> bool:
    if not isinstance(member, discord.Member):
        return False
    if member.guild_permissions.manage_channels:
        return True
    if permisos is None:
        return False
    try:
        return permisos.member_tiene_alguna_key(
            member, "OWNER", "CO_OWNER", "DIRECTOR_GENERAL", "DIRECTOR_RRHH",
            "DIRECTOR_MEDICO", "DIRECTOR_ENFERMERIA", "DIRECTOR_SEGURIDAD",
            "DIRECTOR_ADMINISTRATIVO", "SUPERVISOR", "STAFF_SERVIDOR",
        )
    except Exception:
        return False


def _next_num() -> int:
    path = os.path.join(os.path.dirname(__file__), "data", "entrevistas.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {"n": 0}
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {"n": 0}
    data["n"] = int(data.get("n") or 0) + 1
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return int(data["n"])


def _ping_director(guild, slug: str) -> str:
    dep = (getattr(config, "DEPARTAMENTOS", None) or {}).get(slug) or {}
    dkey = dep.get("director_key")
    if not dkey or not guild:
        return ""
    try:
        import roles_store
        rid = roles_store.obtener_id_key(dkey)
        if rid:
            r = guild.get_role(int(rid))
            if r:
                return r.mention
    except Exception:
        pass
    return ""


class ConfirmarCierreEntrevista(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=90)
        self.bot = bot

    @ui.button(label="Transcribir y cerrar", style=discord.ButtonStyle.danger, emoji="📜")
    async def ok(self, inter: discord.Interaction, btn: ui.Button):
        if not _puede(inter.user):
            return await inter.response.send_message("Sin permiso.", ephemeral=True)
        await inter.response.edit_message(content=f"Cerrando… {inter.user.mention}", view=None)
        ch = inter.channel
        if not isinstance(ch, discord.TextChannel):
            return
        try:
            from ticket_transcript import collect_messages, render_html, html_to_file, embed_resumen
            msgs = await collect_messages(ch, limit=500)
            html_str = render_html(
                titulo=ch.name, canal_nombre=ch.name, abierto_por="—",
                cerrado_por=inter.user.mention,
                categoria=ch.category.name if ch.category else "—",
                creado=msgs[0].created_at if msgs else ch.created_at,
                cerrado=datetime.now(timezone.utc), messages=msgs, guild=ch.guild,
            )
            archivo = html_to_file(html_str, filename=f"{ch.name}.html")
            emb = embed_resumen(
                titulo=ch.name, canal_nombre=ch.name, abierto_por="—",
                cerrado_por=inter.user.mention,
                categoria=ch.category.name if ch.category else "—",
                n_msgs=len(msgs), color=0x3498DB,
            )
            dest = None
            try:
                import logs_store
                cid = logs_store.get_canal_id("log_tickets") or logs_store.get_canal_id("log_solicitudes")
                if cid:
                    dest = inter.client.get_channel(int(cid))
            except Exception:
                pass
            if dest:
                await dest.send(embed=emb, file=archivo)
            else:
                await ch.send(embed=emb, file=archivo)
        except Exception as e:
            print("[entrevista] transcript:", e)
        try:
            await asyncio.sleep(4)
            await ch.delete(reason="Entrevista cerrada")
        except Exception:
            pass

    @ui.button(label="Cancelar", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel(self, inter: discord.Interaction, btn: ui.Button):
        await inter.response.edit_message(content="Cancelado.", view=None)


class EntrevistaView(ui.View):
    def __init__(self, bot, num: int = 0):
        super().__init__(timeout=None)
        self.bot = bot
        self.num = num

    @ui.button(label="Transcribir y cerrar", style=discord.ButtonStyle.danger, emoji="📜", custom_id="entrevista_cerrar_v1")
    async def cerrar(self, inter: discord.Interaction, btn: ui.Button):
        if not _puede(inter.user):
            return await inter.response.send_message("Solo staff.", ephemeral=True)
        await inter.response.send_message(
            "¿Cerrar entrevista con transcripción?",
            view=ConfirmarCierreEntrevista(self.bot),
            ephemeral=True,
        )


class BotonEntrevista(ui.Button):
    def __init__(self, bot, solicitud_id: int):
        super().__init__(
            label="Hacer entrevista",
            style=discord.ButtonStyle.primary,
            emoji="🎤",
            custom_id=f"sol_entrevista_{solicitud_id}",
        )
        self.bot = bot
        self.solicitud_id = solicitud_id

    async def callback(self, inter: discord.Interaction):
        if not _puede(inter.user):
            return await inter.response.send_message("Solo staff.", ephemeral=True)
        guild = inter.guild
        if not guild:
            return
        await inter.response.defer(ephemeral=True)
        reg = {}
        try:
            import centro_solicitudes as cs
            reg = cs.obtener_solicitud(self.solicitud_id) or {}
        except Exception:
            pass
        num = _next_num()
        nombre = f"entrevista-{num:03d}"
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
            inter.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        uid = reg.get("usuario_id")
        solicitante = guild.get_member(int(uid)) if uid else None
        if solicitante:
            overwrites[solicitante] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        try:
            import roles_store
            for key in getattr(config, "TICKET_STAFF_KEYS", []) or []:
                rid = roles_store.obtener_id_key(key)
                if rid:
                    rol = guild.get_role(int(rid))
                    if rol:
                        overwrites[rol] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        except Exception:
            pass
        category = inter.channel.category if inter.channel else None
        try:
            canal = await guild.create_text_channel(
                nombre, category=category, overwrites=overwrites,
                reason=f"Entrevista solicitud #{self.solicitud_id}",
            )
        except Exception as e:
            return await inter.followup.send(f"No pude crear el canal: {e}", ephemeral=True)

        menciones = [inter.user.mention]
        if solicitante:
            menciones.append(solicitante.mention)
        try:
            campos = reg.get("campos") or {}
            deps = getattr(config, "DEPARTAMENTOS", {}) or {}
            for v in campos.values():
                vv = str(v).lower()
                for sk, sd in deps.items():
                    if sk in vv or (sd.get("nombre") or "").lower() in vv:
                        p = _ping_director(guild, sk)
                        if p:
                            menciones.append(p)
                        break
        except Exception:
            pass

        emb = None
        try:
            import centro_solicitudes as cs
            emb = cs.embed_ticket(reg, guild)
        except Exception:
            emb = discord.Embed(title=f"Entrevista #{num:03d}", color=0x3498DB)

        await canal.send(
            " ".join(menciones)
            + f"\n🎤 **Entrevista #{num:03d}** · Solicitud **#{self.solicitud_id:04d}**\n"
            "Usen este canal para la entrevista. Al terminar: **Transcribir y cerrar**.",
            embed=emb,
            view=EntrevistaView(self.bot, num),
        )
        await inter.followup.send(f"Entrevista creada: {canal.mention}", ephemeral=True)


def registrar(bot: commands.Bot) -> None:
    try:
        import centro_solicitudes_ui as cs_ui
        Old = getattr(cs_ui, "TicketSolicitudView", None)
        if Old is not None:
            _old_init = Old.__init__

            def _new_init(self, bot_arg, solicitud_id: int):
                _old_init(self, bot_arg, solicitud_id)
                labels = [getattr(i, "label", None) for i in self.children]
                if "Hacer entrevista" not in labels:
                    self.add_item(BotonEntrevista(bot_arg, solicitud_id))

            Old.__init__ = _new_init
            print("[entrevista_ui] Botón añadido a TicketSolicitudView")
    except Exception as e:
        print("[entrevista_ui] No se pudo parchear TicketSolicitudView:", e)

    bot.add_view(EntrevistaView(bot, 0))
    print("[entrevista_ui] OK")
