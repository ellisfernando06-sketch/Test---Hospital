# -*- coding: utf-8 -*-
"""
- Un solo MD por sanción (anti-doble)
- Apelación: solo ticket (sin botón Entrevista)
- Log: un mensaje con Aceptar / Negar únicamente
"""
from __future__ import annotations

import time
from typing import Optional, Set

import discord
from discord import ui
from discord.ext import commands

_NOTIFIED: Set[int] = set()
_NOTIFIED_TS: dict = {}


def _ya_notificado(sid: int) -> bool:
    now = time.time()
    for k, ts in list(_NOTIFIED_TS.items()):
        if now - ts > 60:
            _NOTIFIED.discard(k)
            _NOTIFIED_TS.pop(k, None)
    if sid in _NOTIFIED:
        return True
    _NOTIFIED.add(sid)
    _NOTIFIED_TS[sid] = now
    return False


def registrar(bot: commands.Bot) -> None:
    try:
        import sanciones_apelacion_ui as ui_mod
    except Exception as e:
        print(f"[sancion_fix_doble] sin ui: {e}")
        return

    try:
        import sanciones as sanc
    except Exception:
        sanc = None

    # ── 1) notificar_usuario: una sola vez por id ─────────────────────────
    _prev_notify = ui_mod.notificar_usuario

    async def notificar_usuario(bot_, guild, reg: dict) -> bool:
        sid = int(reg.get("id") or 0)
        if sid and _ya_notificado(sid):
            print(f"[sancion_fix_doble] MD dup ignorado #{sid}")
            return True
        return await _prev_notify(bot_, guild, reg)

    ui_mod.notificar_usuario = notificar_usuario

    # ── 2) Log apelaciones: solo Aceptar / Negar (sin Entrevista) ───────
    class LogApelacionView(ui.View):
        def __init__(self, user_id: int = 0, sancion_id: int = 0):
            super().__init__(timeout=None)
            self.user_id = int(user_id or 0)
            self.sancion_id = int(sancion_id or 0)

        def _ids(self, inter: discord.Interaction):
            import re

            uid, sid = self.user_id, self.sancion_id
            if inter.message and inter.message.embeds:
                desc = inter.message.embeds[0].description or ""
                title = inter.message.embeds[0].title or ""
                m = re.search(r"\((\d{15,20})\)", desc)
                if m:
                    uid = int(m.group(1))
                m2 = re.search(r"#(\d+)", title) or re.search(
                    r"#(\d+)", desc
                )
                if m2:
                    sid = int(m2.group(1))
            return uid, sid

        def _es_staff(self, m: discord.Member) -> bool:
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
                    "DIRECTOR_ADMINISTRATIVO",
                    "DIR_RRHH",
                    "DIRECTOR_RRHH",
                )
            except Exception:
                return False

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
            if not self._es_staff(inter.user):
                return await inter.response.send_message(
                    "❌ Solo staff.", ephemeral=True
                )
            if sanc is None:
                return await inter.response.send_message(
                    "❌ Sistema no disponible.", ephemeral=True
                )
            uid, sid = self._ids(inter)
            try:
                sanc.anular_sancion(
                    sid, inter.user.id, f"Apelación aceptada por {inter.user}"
                )
            except Exception as e:
                return await inter.response.send_message(
                    f"❌ {e}", ephemeral=True
                )
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
                        f"✅ Tu apelación de `#{sid}` fue **aceptada**. "
                        f"La sanción queda anulada."
                    )
                except Exception:
                    pass
            emb = inter.message.embeds[0] if inter.message.embeds else None
            if emb:
                emb = emb.copy()
                emb.color = 0x2ECC71
                emb.title = f"✅ Apelación aceptada · #{sid}"
                await inter.response.edit_message(embed=emb, view=None)
            else:
                await inter.response.send_message(
                    f"✅ #{sid} aceptada.", ephemeral=True
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
            if not self._es_staff(inter.user):
                return await inter.response.send_message(
                    "❌ Solo staff.", ephemeral=True
                )
            uid, sid = self._ids(inter)
            member = inter.guild.get_member(uid)
            if member:
                try:
                    await member.send(
                        f"❌ Tu apelación de `#{sid}` fue **negada**. "
                        f"La sanción se mantiene."
                    )
                except Exception:
                    pass
            emb = (
                inter.message.embeds[0]
                if inter.message and inter.message.embeds
                else None
            )
            if emb:
                emb = emb.copy()
                emb.color = 0xE74C3C
                emb.title = f"❌ Apelación negada · #{sid}"
                await inter.response.edit_message(embed=emb, view=None)
            else:
                await inter.response.send_message(
                    f"❌ #{sid} negada.", ephemeral=True
                )

    ui_mod.LogApelacionView = LogApelacionView
    try:
        bot.add_view(LogApelacionView(0, 0))
    except Exception:
        pass

    # ── 3) enviar_log_apelacion: un mensaje, vista sin entrevista ─────────
    async def enviar_log_apelacion(
        bot_, guild, member, reg, ticket
    ) -> None:
        canal = ui_mod._canal_log_apelaciones(bot_, guild)
        if not canal:
            return
        # anti-doble log por misma sanción en 60s
        key = f"log_{reg.get('id')}"
        if not hasattr(bot_, "_apelacion_logs"):
            bot_._apelacion_logs = {}
        now = time.time()
        if bot_._apelacion_logs.get(key, 0) + 60 > now:
            return
        bot_._apelacion_logs[key] = now

        emb = discord.Embed(
            title=f"⚖️ Apelación #{reg.get('id')}",
            description=(
                f"{member.mention} (`{member.id}`)\n"
                f"**Tipo:** {reg.get('tipo')} · **Ticket:** "
                f"{ticket.mention if ticket else '—'}\n"
                f"**Motivo:** {(reg.get('motivo') or '—')[:300]}"
            ),
            color=0x5D6D7E,
        )
        try:
            await canal.send(
                embed=emb,
                view=LogApelacionView(
                    member.id, int(reg.get("id") or 0)
                ),
            )
        except Exception as e:
            print(f"[sancion_fix_doble] log: {e}")

    ui_mod.enviar_log_apelacion = enviar_log_apelacion

    # ── 4) Ticket de apelación: un solo mensaje limpio ────────────────────
    if sanc is not None and not getattr(sanc, "_ticket_limpio", False):
        _orig_abrir = sanc.abrir_ticket_apelacion

        async def abrir_ticket_apelacion(guild, usuario, sancion, *a, **kw):
            # Crear canal con la lógica original pero sin spam de embeds
            import config
            import roles_store

            cat = (
                guild.get_channel(config.TICKET_CATEGORIA_ID)
                if getattr(config, "TICKET_CATEGORIA_ID", None)
                else None
            )
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    view_channel=False
                ),
                usuario: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    attach_files=True,
                ),
                guild.me: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    manage_channels=True,
                ),
            }
            for key in getattr(config, "TICKET_STAFF_KEYS", []) or []:
                try:
                    rid = roles_store.obtener_id_key(key)
                    if rid:
                        rol = guild.get_role(rid)
                        if rol:
                            overwrites[rol] = discord.PermissionOverwrite(
                                view_channel=True, send_messages=True
                            )
                except Exception:
                    pass
            for r in guild.roles:
                if r.permissions.administrator and r != guild.default_role:
                    overwrites[r] = discord.PermissionOverwrite(
                        view_channel=True, send_messages=True
                    )

            nombre = f"apelacion-{usuario.name}"[:90]
            try:
                canal = await guild.create_text_channel(
                    nombre,
                    category=cat
                    if isinstance(cat, discord.CategoryChannel)
                    else None,
                    overwrites=overwrites,
                    reason=f"Apelación #{sancion.get('id')} · {usuario}",
                )
            except discord.Forbidden:
                return None

            texto = (
                f"⚖️ **Ticket de apelación** `#{sancion.get('id')}`\n"
                f"**Usuario:** {usuario.mention}\n"
                f"**Tipo:** {sancion.get('tipo')}\n"
                f"**Motivo de la sanción:** {(sancion.get('motivo') or '—')[:400]}\n\n"
                f"Describe aquí tus argumentos. El staff revisará el caso."
            )
            view_cierre = None
            try:
                from paneles import CerrarTicketView

                view_cierre = CerrarTicketView()
            except Exception:
                pass
            kw_send = {"content": texto}
            if view_cierre:
                kw_send["view"] = view_cierre
            await canal.send(**kw_send)

            # Un log (si el hook también llama, anti-doble lo frena)
            try:
                await enviar_log_apelacion(
                    bot, guild, usuario, sancion, canal
                )
            except Exception:
                pass
            return canal

        sanc.abrir_ticket_apelacion = abrir_ticket_apelacion  # type: ignore
        sanc._ticket_limpio = True  # type: ignore

    # Desactivar segundo log del hook de comandos si duplica
    try:
        import sanciones_comandos_hook as hook

        # El hook v2 también envuelve abrir_ticket; si _ticket_limpio ya loguea, ok
    except Exception:
        pass

    print(
        "[sancion_fix_doble] OK — 1 MD · ticket único · sin entrevista"
    )
