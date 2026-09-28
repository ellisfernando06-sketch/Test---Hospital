# -*- coding: utf-8 -*-
"""
bot_control.py — Estado del bot (online / mantenimiento / offline) y
comandos exclusivos de OWNER. CO_OWNER pide aprobación al OWNER.
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Optional

import discord
from discord import ui

import config
import permisos
import roles_store
from estilos import crear_embed

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_STATUS_PATH = os.path.join(_DATA_DIR, "bot_status.json")

_status = {
    "mode": "online",
    "message": "Bot operativo.",
    "changed_by": None,
    "changed_at": None,
}


def _load_status() -> None:
    global _status
    os.makedirs(_DATA_DIR, exist_ok=True)
    if os.path.isfile(_STATUS_PATH):
        try:
            with open(_STATUS_PATH, "r", encoding="utf-8") as f:
                _status.update(json.load(f))
        except Exception:
            pass


def _save_status() -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_STATUS_PATH, "w", encoding="utf-8") as f:
        json.dump(_status, f, ensure_ascii=False, indent=2)


def get_mode() -> str:
    return _status.get("mode", "online")


def set_mode(mode: str, message: str, by: Optional[int] = None) -> None:
    _status["mode"] = mode
    _status["message"] = message
    _status["changed_by"] = by
    _status["changed_at"] = datetime.now(timezone.utc).isoformat()
    _save_status()


def status_embed() -> discord.Embed:
    mode = get_mode()
    custom_msg = (_status.get("message") or "").strip()
    hospital = getattr(config, "NOMBRE_HOSPITAL", None) or "Hospital General"

    defaults = (
        "Bot operativo.", "Bot reiniciado.",
        "Sistemas restaurados y bot plenamente operativo. Todos los módulos disponibles.",
        "Reinicio completado. Bot operativo y sincronizado tras el reinicio del proceso.",
        "Bot reiniciado y operativo.",
        "Sistemas restaurados. Plataforma operativa para todo el personal.",
        "Sistemas restaurados. Plataforma operativa.",
        "Bot encendido. Todo el personal puede usarlo.",
        "Reinicio listo. Bot operativo.",
        "Apagado por la administración.",
        "Mantenimiento del sistema.",
        "Apagado por decisión de la administración / OWNER.",
    )

    if mode == "online":
        color = 0x2ECC71
        title = "🟢 Sistema operativo — Bot activo"
        desc = (
            f"**{hospital}**\n\n"
            f"El bot de gestión está **operativo**.\n"
            f"Comandos, verificaciones, solicitudes y registros disponibles.\n\n"
            f"🟢 Bot Discord: **Activo**\n"
            f"🟢 Comandos: **Disponibles**\n"
            f"🟢 Registros: **Sincronizados**"
        )
        if custom_msg and custom_msg not in defaults:
            desc += f"\n\n**Nota:** {custom_msg}"
    elif mode == "mantenimiento":
        color = 0xF39C12
        title = "🟡 Mantenimiento técnico"
        desc = (
            f"**{hospital}**\n\n"
            f"El bot está en **mantenimiento**. Algunas funciones pueden limitarse.\n\n"
            f"Se anunciará la reactivación en este canal."
        )
        if custom_msg and custom_msg not in defaults:
            desc += f"\n\n**Motivo:** {custom_msg}"
    else:
        color = 0xE74C3C
        title = "🔴 Bot fuera de servicio"
        desc = (
            f"**{hospital}**\n\n"
            f"El bot está **apagado**. Los comandos no están disponibles.\n\n"
            f"**Motivo:** {custom_msg or 'Apagado por la administración.'}"
        )

    embed = discord.Embed(title=title, description=desc, color=color, timestamp=discord.utils.utcnow())
    embed.set_footer(text=f"{hospital}  •  Administración del Sistema")
    if _status.get("changed_at"):
        fecha = str(_status["changed_at"])[:19].replace("T", " ") + " UTC"
        embed.add_field(name="📅 Último cambio", value=fecha, inline=True)
    if _status.get("changed_by"):
        embed.add_field(name="👤 Autorizado por", value=f"<@{_status['changed_by']}> ", inline=True)
    return embed


async def publicar_estado(bot: discord.Client, guild: Optional[discord.Guild] = None) -> None:
    canal_id = (getattr(config, "CANALES", {}) or {}).get("bot_status")
    if not canal_id:
        return
    canal = bot.get_channel(int(canal_id))
    if not canal:
        return
    try:
        await canal.send(embed=status_embed())
    except Exception:
        pass


class AprobacionBotView(ui.View):
    def __init__(self, accion: str, solicitante_id: int, bot: discord.Client, extra: str = ""):
        super().__init__(timeout=3600)
        self.accion = accion
        self.solicitante_id = solicitante_id
        self.bot = bot
        self.extra = extra

    async def _es_owner(self, interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            return False
        try:
            return permisos.member_tiene_key(interaction.user, "OWNER")
        except Exception:
            return permisos.member_tiene_alguna_key(interaction.user, "OWNER")

    @ui.button(label="✅ Aprobar", style=discord.ButtonStyle.success)
    async def aprobar(self, interaction: discord.Interaction, button: ui.Button):
        if not await self._es_owner(interaction):
            await interaction.response.send_message("❌ Solo el **OWNER** puede aprobar.", ephemeral=True)
            return
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(f"✅ Acción **{self.accion}** aprobada. Ejecutando…", ephemeral=True)
        await _ejecutar_accion(self.bot, self.accion, interaction.user.id, self.extra, interaction)

    @ui.button(label="❌ Negar", style=discord.ButtonStyle.danger)
    async def negar(self, interaction: discord.Interaction, button: ui.Button):
        if not await self._es_owner(interaction):
            await interaction.response.send_message("❌ Solo el **OWNER** puede negar.", ephemeral=True)
            return
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(f"❌ Acción **{self.accion}** denegada.", ephemeral=True)


async def _ejecutar_accion(
    bot: discord.Client, accion: str, por: int, extra: str,
    interaction: Optional[discord.Interaction] = None,
) -> None:
    if accion == "apagar":
        set_mode("offline", extra or "Apagado por decisión de la administración.", por)
        await publicar_estado(bot)
        msg = "🔴 Bot marcado como **offline**. Cerrando conexión…"
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(msg)
            else:
                await interaction.response.send_message(msg)
        await asyncio.sleep(1.5)
        await bot.close()
    elif accion == "encender":
        set_mode("online", extra or "Sistemas restaurados y bot plenamente operativo.", por)
        await publicar_estado(bot)
        msg = "🟢 Bot en modo **online**."
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(msg)
            else:
                await interaction.response.send_message(msg)
    elif accion == "mantenimiento":
        set_mode("mantenimiento", extra or "Mantenimiento técnico programado.", por)
        await publicar_estado(bot)
        msg = "🟡 Bot en modo **mantenimiento**."
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(msg)
            else:
                await interaction.response.send_message(msg)
    elif accion == "reiniciar":
        set_mode("online", extra or "Reinicio completado. Bot operativo.", por)
        await publicar_estado(bot)
        msg = "🔄 Reinicio solicitado. Cerrando…"
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(msg)
            else:
                await interaction.response.send_message(msg)
        await asyncio.sleep(1.5)
        await bot.close()


async def manejar_control_bot(
    interaction: discord.Interaction, bot: discord.Client, accion: str, mensaje: str = "",
) -> None:
    user = interaction.user
    if not isinstance(user, discord.Member):
        await interaction.response.send_message("❌ Solo en servidor.", ephemeral=True)
        return
    try:
        es_owner = permisos.member_tiene_key(user, "OWNER")
        es_co = permisos.member_tiene_key(user, "CO_OWNER")
    except Exception:
        es_owner = permisos.member_tiene_alguna_key(user, "OWNER")
        es_co = permisos.member_tiene_alguna_key(user, "CO_OWNER")

    if not es_owner and not es_co:
        await interaction.response.send_message(
            "❌ Solo **OWNER** o **CO_OWNER** pueden usar este comando.", ephemeral=True
        )
        return

    if es_owner:
        await interaction.response.defer(ephemeral=True)
        await _ejecutar_accion(bot, accion, user.id, mensaje, interaction)
        return

    embed = crear_embed(
        "aviso",
        f"🔐 Solicitud de {accion.upper()} del bot",
        f"**Solicitante:** {user.mention} (CO-OWNER)\n**Acción:** `{accion}`\n**Mensaje:** {mensaje or '—'}",
        autor=user,
    )
    view = AprobacionBotView(accion, user.id, bot, mensaje)
    enviado = False
    canal_id = (getattr(config, "CANALES", {}) or {}).get("aprobaciones")
    if canal_id and interaction.guild:
        canal = interaction.guild.get_channel(int(canal_id))
        if canal:
            owner_rid = roles_store.obtener_id_key("OWNER")
            mencion = ""
            if owner_rid:
                rol = interaction.guild.get_role(owner_rid)
                if rol:
                    mencion = rol.mention
            await canal.send(content=mencion or None, embed=embed, view=view)
            enviado = True
    if not enviado and interaction.guild:
        owner_rid = roles_store.obtener_id_key("OWNER")
        if owner_rid:
            rol = interaction.guild.get_role(owner_rid)
            if rol:
                for m in rol.members:
                    if m.bot:
                        continue
                    try:
                        await m.send(embed=embed, view=view)
                        enviado = True
                        break
                    except discord.Forbidden:
                        continue
    if enviado:
        await interaction.response.send_message(
            "📨 Solicitud enviada al **OWNER**. Debe aprobarla para ejecutar la acción.",
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            "❌ No se pudo contactar a ningún OWNER.",
            ephemeral=True,
        )


async def solicitar_o_ejecutar(
    interaction: discord.Interaction, bot: discord.Client, accion: str, mensaje: str = "",
) -> None:
    await manejar_control_bot(interaction, bot, accion, mensaje)


_load_status()
