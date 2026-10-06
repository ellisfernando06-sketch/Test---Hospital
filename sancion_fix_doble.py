# -*- coding: utf-8 -*-
"""
- Un solo MD por sanción
- Apelación: solo ticket limpio
- Log y ticket: Aceptar / Negar (sin Entrevista)
- Roles de sanción al aplicar / quitar al aceptar
"""
from __future__ import annotations

import time
from typing import Optional, Set

import discord
from discord import ui
from discord.ext import commands

_NOTIFIED: Set[int] = set()
_NOTIFIED_TS: dict = {}
_LOGGED: Set[int] = set()
_LOGGED_TS: dict = {}


def _ya_visto(store: Set[int], ts_map: dict, key: int, secs: float = 60.0) -> bool:
    now = time.time()
    for k, ts in list(ts_map.items()):
        if now - ts > secs:
            store.discard(k)
            ts_map.pop(k, None)
    if key in store:
        return True
    store.add(key)
    ts_map[key] = now
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

    try:
        import sancion_roles as sroles
    except Exception:
        sroles = None

    _prev_notify = ui_mod.notificar_usuario

    async def notificar_usuario(bot_, guild, reg: dict) -> bool:
        sid = int(reg.get("id") or 0)
        if sid and _ya_visto(_NOTIFIED, _NOTIFIED_TS, sid):
            print(f"[sancion_fix_doble] MD dup #{sid}")
            return True

        # Rol de perfil
        if sroles is not None:
            uid = int(reg.get("usuario_id") or 0)
            member = guild.get_member(uid)
            if member:
                try:
                    await sroles.otorgar_rol_sancion(
                        guild, member, reg.get("tipo") or ""
                    )
                except Exception as e:
                    print(f"[sancion_roles] otorgar: {e}")

        return await _prev_notify(bot_, guild, reg)

    ui_mod.notificar_usuario = notificar_usuario

    # Vista del ticket Y del log: Aceptar / Negar (sin entrevista)
    class TicketApelacionView(ui.View):
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
            # También desde content del ticket
            if inter.message and inter.message.content:
                import re as _re

                m3 = _re.search(r"#(\d+)", inter.message.content)
                if m3 and not sid:
                    sid = int(m3.group(1))
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
                    "STAFF_SERVIDOR",
                )
            except Exception:
                return False

        @ui.button(
            label="Aceptar apelación",
            style=discord.ButtonStyle.success,
            emoji="✅",
            custom_id="apelacion_ticket:aceptar",
        )
        async def aceptar(self, inter: discord.Interaction, button: ui.Button):
            if not inter.guild or not isinstance(inter.user, discord.Member):
                return await inter.response.send_message(
                    "❌ Solo en servidor.", ephemeral=True
                )
            if not self._es_staff(inter.user):
                return await inter.response.send_message(
                    "❌ Solo admin / staff del servidor.", ephemeral=True
                )
            if sanc is None:
                return await inter.response.send_message(
                    "❌ Sistema no disponible.", ephemeral=True
                )
            uid, sid = self._ids(inter)
            reg = sanc.obtener_sancion(sid) if sid else None
            try:
                sanc.anular_sancion(
                    sid, inter.user.id, f"Apelación aceptada por {inter.user}"
                )
            except Exception as e:
                return await inter.response.send_message(
                    f"❌ {e}", ephemeral=True
                )

            member = inter.guild.get_member(uid)
            if member and sroles_ok():
                try:
                    import sancion_roles as sr

                    await sr.quitar_todos_roles_sancion(inter.guild, member)
                except Exception:
                    pass
            if member:
                try:
                    await member.send(
                        f"✅ Tu apelación de `#{sid}` fue **aceptada**."
                    )
                except Exception:
                    pass

            await inter.response.send_message(
                f"✅ Apelación `#{sid}` **aceptada** por {inter.user.mention}.",
            )
            # Desactivar botones
            try:
                await inter.message.edit(view=None)
            except Exception:
                pass

        @ui.button(
            label="Negar apelación",
            style=discord.ButtonStyle.danger,
            emoji="❌",
            custom_id="apelacion_ticket:negar",
        )
        async def negar(self, inter: discord.Interaction, button: ui.Button):
            if not inter.guild or not isinstance(inter.user, discord.Member):
                return await inter.response.send_message(
                    "❌ Solo en servidor.", ephemeral=True
                )
            if not self._es_staff(inter.user):
                return await inter.response.send_message(
                    "❌ Solo admin / staff del servidor.", ephemeral=True
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
            await inter.response.send_message(
                f"❌ Apelación `#{sid}` **negada** por {inter.user.mention}.",
            )
            try:
                await inter.message.edit(view=None)
            except Exception:
                pass

    def sroles_ok() -> bool:
        try:
            import sancion_roles  # noqa: F401

            return True
        except Exception:
            return False

    # Ticket limpio + botones en el MISMO ticket
    if sanc is not None:

        async def abrir_ticket_apelacion(guild, usuario, sancion, *a, **kw):
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
                f"**Usuario:** {usuario.mention} (`{usuario.id}`)\n"
                f"**Tipo:** {sancion.get('tipo')}\n"
                f"**Motivo:** {(sancion.get('motivo') or '—')[:400]}\n\n"
                f"El apelante puede argumentar aquí.\n"
                f"**Solo admin / staff** pueden usar Aceptar o Negar."
            )
            view = TicketYLogView(
                usuario.id, int(sancion.get("id") or 0)
            )
            await canal.send(content=texto, view=view)

            try:
                await enviar_log_apelacion(
                    bot, guild, usuario, sancion, canal
                )
            except Exception:
                pass
            return canal

        # Vista compartida ticket (mismos custom_id que log para persistencia simple)
        # Usamos custom_id distintos para ticket
        class TicketYLogView(LogApelacionView):
            """Misma lógica; custom_id de ticket para no chocar."""

            def __init__(self, user_id: int = 0, sancion_id: int = 0):
                # No llamar super con botones de LogApelacionView duplicados
                ui.View.__init__(self, timeout=None)
                self.user_id = int(user_id or 0)
                self.sancion_id = int(sancion_id or 0)

            @ui.button(
                label="Aceptar apelación",
                style=discord.ButtonStyle.success,
                emoji="✅",
                custom_id="apelacion_ticket:aceptar",
            )
            async def aceptar(
                self, inter: discord.Interaction, button: ui.Button
            ):
                return await LogApelacionView.aceptar.callback(
                    self, inter, button
                )

            @ui.button(
                label="Negar apelación",
                style=discord.ButtonStyle.danger,
                emoji="❌",
                custom_id="apelacion_ticket:negar",
            )
            async def negar(
                self, inter: discord.Interaction, button: ui.Button
            ):
                return await LogApelacionView.negar.callback(
                    self, inter, button
                )

        # Rebind with TicketYLogView in closure - need redefine abrir with TicketYLogView

        async def abrir_ticket_apelacion2(guild, usuario, sancion, *a, **kw):
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
                f"**Usuario:** {usuario.mention} (`{usuario.id}`)\n"
                f"**Tipo:** {sancion.get('tipo')}\n"
                f"**Motivo:** {(sancion.get('motivo') or '—')[:400]}\n\n"
                f"El apelante puede argumentar aquí.\n"
                f"**Solo admin / staff** pueden **Aceptar** o **Negar**."
            )
            view = LogApelacionView(
                usuario.id, int(sancion.get("id") or 0)
            )
            # custom_ids de log sirven en ticket también
            await canal.send(content=texto, view=view)

            try:
                await enviar_log_apelacion(
                    bot, guild, usuario, sancion, canal
                )
            except Exception:
                pass
            return canal

        sanc.abrir_ticket_apelacion = abrir_ticket_apelacion2  # type: ignore
        sanc._ticket_limpio = True  # type: ignore

    print("[sancion_fix_doble] OK — 1 MD · ticket · Aceptar/Negar · sin entrevista")
