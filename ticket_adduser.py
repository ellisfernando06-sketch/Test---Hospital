# -*- coding: utf-8 -*
"""ticket_adduser.py — Menús para añadir personas a tickets/solicitudes."""
from __future__ import annotations

from typing import Optional

import discord
from discord import ui
from discord.ext import commands

import config
import permisos
import roles_store

try:
    from centro_solicitudes import (
        obtener_solicitud,
        actualizar_solicitud,
        embed_log_accion,
        enviar_log_solicitud,
    )
except Exception:
    obtener_solicitud = None
    actualizar_solicitud = None
    embed_log_accion = None
    enviar_log_solicitud = None


def _puede_gestionar(user: discord.abc.User) -> bool:
    if not isinstance(user, discord.Member):
        return False
    return permisos.member_tiene_alguna_key(
        user,
        "OWNER", "CO_OWNER", "DIRECTOR", "DIRECTOR_ADMINISTRATIVO",
        "DIRECTOR_DISCIPLINA", "DIRECTOR_GENERAL", "DIRECTOR_RRHH",
        "SUPERVISOR", "STAFF_SERVIDOR",
    )


def _miembros_autorizados(guild: discord.Guild) -> list:
    """Miembros con roles/keys de staff o personal del hospital (máx. 25 para el menú)."""
    keys_ok = set(getattr(config, "TICKET_STAFF_KEYS", []) or [])
    keys_ok.update({"OWNER", "CO_OWNER", "STAFF", "STAFF_SERVIDOR", "SUPERVISOR", "RESIDENTE"})
    for dk in getattr(config, "DIRECTOR_KEYS", []) or []:
        keys_ok.add(dk)

    role_ids = set()
    for key in keys_ok:
        rid = roles_store.obtener_id_key(key)
        if rid:
            role_ids.add(rid)

    for rol in guild.roles:
        n = (rol.name or "").lower()
        if any(x in n for x in ("director", "supervisor", "staff", "rrhh", "médico", "medico", "enfermer")):
            role_ids.add(rol.id)

    vistos = set()
    miembros = []
    for member in guild.members:
        if member.bot or member.id in vistos:
            continue
        if any(r.id in role_ids for r in member.roles):
            vistos.add(member.id)
            miembros.append(member)
            if len(miembros) >= 25:
                break
    miembros.sort(key=lambda m: (m.display_name or m.name).lower())
    return miembros


async def _añadir_miembro_al_canal(
    interaction: discord.Interaction,
    member: discord.Member,
    bot: commands.Bot,
    solicitud_id: Optional[int] = None,
) -> bool:
    """Da permisos al miembro en el canal actual y actualiza el registro si hay solicitud."""
    try:
        await interaction.channel.set_permissions(
            member, view_channel=True, send_messages=True, attach_files=True
        )
    except discord.Forbidden:
        await interaction.response.send_message("❌ No puedo modificar permisos.", ephemeral=True)
        return False

    if solicitud_id is not None and obtener_solicitud and actualizar_solicitud:
        reg = obtener_solicitud(solicitud_id)
        extras = list((reg or {}).get("usuarios_extra") or [])
        if member.id not in extras:
            extras.append(member.id)
            actualizar_solicitud(solicitud_id, usuarios_extra=extras)
        await interaction.response.send_message(f"✅ {member.mention} añadido al ticket.")
        if reg and embed_log_accion and enviar_log_solicitud:
            log = embed_log_accion(reg, "Usuario añadido", interaction.user, member.mention)
            await enviar_log_solicitud(bot, log)
    else:
        await interaction.response.send_message(f"✅ {member.mention} añadido al ticket.")
    return True


class AnadirUsuarioSelect(ui.Select):
    """Menú desplegable con personas autorizadas (roles de staff/personal)."""

    def __init__(self, bot: commands.Bot, solicitud_id: int, guild: discord.Guild):
        self.bot = bot
        self.solicitud_id = solicitud_id
        miembros = _miembros_autorizados(guild)
        options = []
        for m in miembros:
            label = (m.display_name or m.name)[:100]
            desc = f"@{m.name}"[:100]
            options.append(
                discord.SelectOption(
                    label=label,
                    value=str(m.id),
                    description=desc,
                    emoji="👤",
                )
            )
        if not options:
            options = [
                discord.SelectOption(
                    label="No hay personal autorizado detectado",
                    value="none",
                    description="Configura roles/keys o usa el selector libre",
                )
            ]
        super().__init__(
            placeholder="👥 Elige una persona autorizada…",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"sol_adduser_select_{solicitud_id}",
        )

    async def callback(self, interaction: discord.Interaction):
        if not _puede_gestionar(interaction.user):
            await interaction.response.send_message("❌ Solo staff autorizado.", ephemeral=True)
            return
        val = self.values[0] if self.values else None
        if not val or val == "none":
            await interaction.response.send_message(
                "❌ No hay personas disponibles. Usa el selector libre de usuarios.",
                ephemeral=True,
            )
            return
        try:
            uid = int(val)
        except ValueError:
            await interaction.response.send_message("❌ ID inválido.", ephemeral=True)
            return
        member = interaction.guild.get_member(uid) if interaction.guild else None
        if not member:
            await interaction.response.send_message("❌ Usuario no encontrado.", ephemeral=True)
            return
        await _añadir_miembro_al_canal(interaction, member, self.bot, self.solicitud_id)


class AnadirUsuarioUserSelect(ui.UserSelect):
    """Selector nativo de Discord (cualquier usuario del servidor)."""

    def __init__(self, bot: commands.Bot, solicitud_id: int):
        self.bot = bot
        self.solicitud_id = solicitud_id
        super().__init__(
            placeholder="🔍 O busca cualquier usuario del servidor…",
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction):
        if not _puede_gestionar(interaction.user):
            await interaction.response.send_message("❌ Solo staff autorizado.", ephemeral=True)
            return
        users = self.values
        if not users:
            await interaction.response.send_message("❌ No seleccionaste a nadie.", ephemeral=True)
            return
        user = users[0]
        member = interaction.guild.get_member(user.id) if interaction.guild else None
        if not member:
            await interaction.response.send_message(
                "❌ Ese usuario no está en el servidor.", ephemeral=True
            )
            return
        await _añadir_miembro_al_canal(interaction, member, self.bot, self.solicitud_id)


class AnadirUsuarioView(ui.View):
    """Vista con menú de personal autorizado + selector libre de usuarios."""

    def __init__(self, bot: commands.Bot, solicitud_id: int, guild: discord.Guild):
        super().__init__(timeout=120)
        self.add_item(AnadirUsuarioSelect(bot, solicitud_id, guild))
        self.add_item(AnadirUsuarioUserSelect(bot, solicitud_id))
