# -*- coding: utf-8 -*
"""
bot_control.py — Estado del bot (online / mantenimiento / offline) y
comandos exclusivos de OWNER. CO_OWNER debe pedir aprobación al OWNER.
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Optional

import discord
from discord import app_commands, ui

import config
import permisos
import roles_store
from estilos import crear_embed

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_STATUS_PATH = os.path.join(_DATA_DIR, "bot_status.json")

# Estado en memoria + persistido
_status = {
    "mode": "online",  # online | mantenimiento | offline
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
    """
    Embed profesional de estado del bot (estilo comunicado oficial).
    online / mantenimiento / offline con textos realistas del hospital.
    """
    mode = get_mode()
    custom_msg = (_status.get("message") or "").strip()

    if mode == "online":
        color = 0x2ECC71
        title = "🟢 SISTEMA OPERATIVO — BOT ACTIVO"
        desc = (
            f"**COMUNICADO DE LA ADMINISTRACIÓN**\n\n"
            f"Se informa a todo el personal y comunidad del **{config.NOMBRE_HOSPITAL}** "
            f"que el bot de gestión se encuentra **plenamente operativo**.\n\n"
            f"Todos los sistemas de comandos, verificaciones, solicitudes, sanciones "
            f"y registros están disponibles con normalidad.\n\n"
            f"**Estado de plataformas**\n"
            f"🟢 Bot Discord: **Activo**\n"
            f"🟢 Comandos y paneles: **Disponibles**\n"
            f"🟢 Base de datos / registros: **Sincronizados**\n\n"
            f"Agradecemos su colaboración y les recordamos seguir los protocolos "
            f"establecidos. Cualquier incidencia puede reportarse por los canales oficiales."
        )
        if custom_msg and custom_msg not in (
            "Bot operativo.",
            "Bot reiniciado.",
            "Sistemas restaurados y bot plenamente operativo. Todos los módulos disponibles.",
            "Reinicio completado. Bot operativo y sincronizado tras el reinicio del proceso.",
        ):
            desc += f"\n\n**Nota de la administración:**\n> {custom_msg}"
    elif mode == "mantenimiento":
        color = 0xF39C12
        title = "🟡 MANTENIMIENTO TÉCNICO EN CURSO"
        desc = (
            f"**COMUNICADO OFICIAL — {config.NOMBRE_HOSPITAL}**\n\n"
            f"Se informa formalmente que el bot de gestión entra a partir de este momento "
            f"en un **proceso de mantenimiento técnico**.\n\n"
            f"Durante este período el equipo administrativo y técnico realizará "
            f"actualizaciones, corrección de incidencias y optimizaciones para "
            f"garantizar un servicio más estable y fluido.\n\n"
            f"**Labores en curso**\n"
            f"• Optimización y estabilidad de comandos\n"
            f"• Actualización de sistemas de verificación y roles\n"
            f"• Sincronización y depuración de registros\n"
            f"• Corrección de errores reportados por el personal\n"
            f"• Preparación de nuevas implementaciones\n\n"
            f"**Aviso importante**\n"
            f"Algunos comandos pueden estar temporalmente limitados o no disponibles. "
            f"Les solicitamos estar atentos a los canales oficiales, donde se anunciará "
            f"la reactivación completa del servicio.\n\n"
            f"Agradecemos de antemano la paciencia y el respaldo de todo el personal."
        )
        if custom_msg:
            desc += f"\n\n**Motivo indicado por la administración:**\n> {custom_msg}"
    else:  # offline
        color = 0xE74C3C
        title = "🔴 BOT FUERA DE SERVICIO — APAGADO"
        desc = (
            f"**COMUNICADO OFICIAL — {config.NOMBRE_HOSPITAL}**\n\n"
            f"Se informa a toda la comunidad y personal que el bot de gestión "
            f"ha sido **apagado** y permanece fuera de servicio hasta nuevo aviso.\n\n"
            f"**Estado general**\n"
            f"🔴 Bot Discord: **Apagado / Fuera de servicio**\n"
            f"🔴 Comandos y paneles: **No disponibles**\n"
            f"🟡 Registros: **Conservados (se reanudarán al reinicio)**\n\n"
            f"**Motivo del apagado**\n"
            f"> {custom_msg or 'Apagado por decisión de la administración / OWNER.'}\n\n"
            f"**Aviso importante**\n"
            f"No será posible utilizar comandos, verificaciones ni sistemas de "
            f"solicitudes mientras el bot permanezca offline. "
            f"La reactivación se anunciará por este mismo canal.\n\n"
            f"Agradecemos la comprensión y el apoyo constante de cada uno de ustedes."
        )

    embed = discord.Embed(
        title=title,
        description=desc,
        color=color,
        timestamp=discord.utils.utcnow(),
    )
    embed.set_footer(text=f"{config.NOMBRE_HOSPITAL}  •  Administración del Sistema")
    if _status.get("changed_at"):
        fecha = str(_status["changed_at"])[:19].replace("T", " ") + " UTC"
        embed.add_field(name="📅 Último cambio de estado", value=fecha, inline=True)
    if _status.get("changed_by"):
        embed.add_field(name="👤 Autorizado por", value=f"<@{_status['changed_by']}>", inline=True)
    return embed


async def publicar_estado(bot: discord.Client, guild: Optional[discord.Guild] = None) -> None:
    canal_id = config.CANALES.get("bot_status")
    if not canal_id:
        return
    canal = bot.get_channel(canal_id)
    if not canal:
        return
    try:
        await canal.send(embed=status_embed())
    except discord.Forbidden:
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
        return permisos.member_tiene_key(interaction.user, "OWNER")

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
    bot: discord.Client,
    accion: str,
    por: int,
    extra: str,
    interaction: Optional[discord.Interaction] = None,
) -> None:
    if accion == "apagar":
        set_mode(
            "offline",
            extra or "Apagado por decisión del OWNER / Administración. Se reactivará cuando se complete el proceso técnico o administrativo correspondiente.",
            por,
        )
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
        set_mode(
            "online",
            extra or "Sistemas restaurados y bot plenamente operativo. Todos los módulos disponibles.",
            por,
        )
        await publicar_estado(bot)
        msg = "🟢 Bot en modo **online**."
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(msg)
            else:
                await interaction.response.send_message(msg)

    elif accion == "mantenimiento":
        set_mode(
            "mantenimiento",
            extra or "Mantenimiento técnico programado. Optimización de sistemas, corrección de incidencias y preparación de actualizaciones.",
            por,
        )
        await publicar_estado(bot)
        msg = "🟡 Bot en modo **mantenimiento**."
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(msg)
            else:
                await interaction.response.send_message(msg)

    elif accion == "reiniciar":
        set_mode(
            "online",
            extra or "Reinicio completado. Bot operativo y sincronizado tras el reinicio del proceso.",
            por,
        )
        await publicar_estado(bot)
        msg = "🔄 Reinicio solicitado. Si el proceso está bajo un supervisor (systemd/PM2/Railway), se reiniciará solo. Cerrando…"
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(msg)
            else:
                await interaction.response.send_message(msg)
        await asyncio.sleep(1.5)
        await bot.close()


async def manejar_control_bot(
    interaction: discord.Interaction,
    bot: discord.Client,
    accion: str,
    mensaje: str = "",
) -> None:
    """
    OWNER ejecuta al momento.
    CO_OWNER envía solicitud de aprobación al OWNER (canal aprobaciones o DM).
    """
    user = interaction.user
    if not isinstance(user, discord.Member):
        await interaction.response.send_message("❌ Solo en servidor.", ephemeral=True)
        return

    es_owner = permisos.member_tiene_key(user, "OWNER")
    es_co = permisos.member_tiene_key(user, "CO_OWNER")

    if not es_owner and not es_co:
        await interaction.response.send_message(
            "❌ Solo **OWNER** o **CO_OWNER** pueden usar este comando.",
            ephemeral=True,
        )
        return

    if es_owner:
        await interaction.response.defer(ephemeral=True)
        await _ejecutar_accion(bot, accion, user.id, mensaje, interaction)
        return

    # CO_OWNER → pedir aprobación
    embed = crear_embed(
        "aviso",
        f"🔐 Solicitud de {accion.upper()} del bot",
        f"**Solicitante:** {user.mention} (CO-OWNER)\n**Acción:** `{accion}`\n**Mensaje:** {mensaje or '—'}",
        autor=user,
    )
    view = AprobacionBotView(accion, user.id, bot, mensaje)

    enviado = False
    canal_id = config.CANALES.get("aprobaciones")
    if canal_id:
        canal = interaction.guild.get_channel(canal_id) if interaction.guild else None
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
            "❌ No se pudo contactar a ningún OWNER. Configura el canal `aprobaciones` o asegúrate de que haya un OWNER en el servidor.",
            ephemeral=True,
        )


# Cargar estado al importar
_load_status()
