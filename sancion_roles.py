# -*- coding: utf-8 -*-
"""
Roles de sanción en el perfil del miembro.

Al aplicar una medida se añade el rol correspondiente (separador visual, sin permisos).
Al anular / aceptar apelación se quita.

Tipos → roles:
  advertencia     → ⚠️ Advertencia
  disciplinaria   → 🔨 Sanción Disciplinaria
  administrativa  → 📋 Sanción Administrativa
  ban             → ⏳ Cuarentena
  (timeout/kick se mapean a disciplinaria para el rol de perfil)
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

import discord
from discord.ext import commands

# tipo canónico → (nombre del rol, color hex o None = sin color)
_ROLES_SANCION: Dict[str, Tuple[str, Optional[int]]] = {
    "advertencia": ("⚠️ Advertencia", 0xF1C40F),
    "disciplinaria": ("🔨 Sanción Disciplinaria", 0xE67E22),
    "sancion": ("🔨 Sanción Disciplinaria", 0xE67E22),
    "sanción": ("🔨 Sanción Disciplinaria", 0xE67E22),
    "administrativa": ("📋 Sanción Administrativa", 0x8E44AD),
    "ban": ("⏳ Cuarentena", 0x95A5A6),
}


async def _obtener_o_crear_rol(
    guild: discord.Guild, nombre: str, color: Optional[int]
) -> Optional[discord.Role]:
    rol = discord.utils.get(guild.roles, name=nombre)
    if rol:
        return rol
    try:
        kwargs = {
            "name": nombre,
            "permissions": discord.Permissions.none(),
            "hoist": False,
            "mentionable": False,
            "reason": "Rol de estado de sanción (separador)",
        }
        if color is not None:
            kwargs["colour"] = discord.Colour(color)
        return await guild.create_role(**kwargs)
    except Exception as e:
        print(f"[sancion_roles] crear {nombre}: {e}")
        return None


async def otorgar_rol_sancion(
    guild: discord.Guild, member: discord.Member, tipo: str
) -> Optional[discord.Role]:
    tipo_n = (tipo or "").lower()
    meta = _ROLES_SANCION.get(tipo_n)
    if not meta:
        return None
    nombre, color = meta
    rol = await _obtener_o_crear_rol(guild, nombre, color)
    if not rol:
        return None
    if rol not in member.roles:
        try:
            await member.add_roles(rol, reason=f"Sanción: {tipo_n}")
        except Exception as e:
            print(f"[sancion_roles] add: {e}")
            return None
    return rol


async def quitar_rol_sancion(
    guild: discord.Guild, member: discord.Member, tipo: str
) -> None:
    tipo_n = (tipo or "").lower()
    meta = _ROLES_SANCION.get(tipo_n)
    if not meta:
        return
    nombre, _ = meta
    rol = discord.utils.get(guild.roles, name=nombre)
    if rol and rol in member.roles:
        try:
            await member.remove_roles(rol, reason="Sanción anulada / apelación aceptada")
        except Exception as e:
            print(f"[sancion_roles] remove: {e}")


async def quitar_todos_roles_sancion(
    guild: discord.Guild, member: discord.Member
) -> None:
    for nombre, _ in _ROLES_SANCION.values():
        rol = discord.utils.get(guild.roles, name=nombre)
        if rol and rol in member.roles:
            try:
                await member.remove_roles(rol, reason="Sanción anulada")
            except Exception:
                pass


def registrar(bot: commands.Bot) -> None:
    try:
        import sanciones_apelacion_ui as ui_mod
    except Exception as e:
        print(f"[sancion_fix_doble] import: {e}")
        return

    _prev = ui_mod.notificar_usuario

    async def notificar_usuario(bot_, guild, reg: dict) -> bool:
        sid = int(reg.get("id") or 0)
        if sid and _ya_notificado(sid):
            print(f"[sancion_fix_doble] MD dup #{sid}")
            return True

        # Rol de perfil según tipo
        uid = int(reg.get("usuario_id") or 0)
        member = guild.get_member(uid)
        if member:
            try:
                await otorgar_rol_sancion(guild, member, reg.get("tipo") or "")
            except Exception as e:
                print(f"[sancion_roles] otorgar en notify: {e}")

        return await _prev(bot_, guild, reg)

    ui_mod.notificar_usuario = notificar_usuario

    # Log sin botón Entrevista
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
                m2 = re.search(r"#(\d+)", title) or re.search(r"#(\d+)", desc)
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
            if member:
                try:
                    await quitar_todos_roles_sancion(guild, member)
                except Exception:
                    pass
                if reg:
                    try:
                        await quitar_rol_sancion(
                            guild, member, reg.get("tipo") or ""
                        )
                    except Exception:
                        pass
                for r in list(member.roles):
                    if "cuarentena" in (r.name or "").lower():
                        try:
                            await member.remove_roles(r, reason="Apelación aceptada")
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

    _prev_log = getattr(ui_mod, "enviar_log_apelacion", None)

    async def enviar_log_apelacion(bot_, guild, member, reg, ticket) -> None:
        canal = ui_mod._canal_log_apelaciones(bot_, guild)
        if not canal:
            return
        if not hasattr(bot_, "_apelacion_logs"):
            bot_._apelacion_logs = {}
        key = f"log_{reg.get('id')}"
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
                view=LogApelacionView(member.id, int(reg.get("id") or 0)),
            )
        except Exception as e:
            print(f"[sancion_fix_doble] log: {e}")

    ui_mod.enviar_log_apelacion = enviar_log_apelacion

    # Ticket limpio (1 mensaje de texto)
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

            try:
                await enviar_log_apelacion(bot, guild, usuario, sancion, canal)
            except Exception:
                pass
            return canal

        sanc.abrir_ticket_apelacion = abrir_ticket_apelacion  # type: ignore
        sanc._ticket_limpio = True  # type: ignore

    print("[sancion_fix_doble] OK — 1 MD · ticket único · sin entrevista")
