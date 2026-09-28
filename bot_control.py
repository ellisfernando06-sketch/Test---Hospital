# -*- coding: utf-8 -*-
"""
bot_control.py — Estado del bot y control OWNER / CO_OWNER.
Presentación institucional completa y realista. API compatible.
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
    """Comunicado completo y realista del estado de la plataforma."""
    mode = get_mode()
    custom_msg = (_status.get("message") or "").strip()
    hospital = getattr(config, "NOMBRE_HOSPITAL", None) or "Hospital General"

    if mode == "online":
        color = 0x1E8449
        title = "🏥  Estado de la plataforma — Operativa"
        desc = (
            f"**{hospital}**\n"
            f"*Comunicado del centro de operaciones*\n\n"
            f"Se informa al personal y a la comunidad que el sistema de gestión "
            f"del hospital se encuentra **en servicio**.\n\n"
            f"Los módulos de comandos, verificación de identidad, solicitudes, "
            f"régimen disciplinario, finanzas y registro documental están "
            f"**disponibles para uso normal**.\n\n"
            f"**Resumen de servicios**\n"
            f"🟢 Bot de Discord — **Activo**\n"
            f"🟢 Comandos y paneles — **Disponibles**\n"
            f"🟢 Expedientes y registros — **Sincronizados**\n"
            f"🟢 Solicitudes y aprobaciones — **En funcionamiento**\n\n"
            f"Ante cualquier incidencia técnica o de personal, utilice los "
            f"canales oficiales de reporte o contacte a la dirección de su área."
        )
        defaults = (
            "Bot operativo.",
            "Bot reiniciado.",
            "Sistemas restaurados y bot plenamente operativo. Todos los módulos disponibles.",
            "Reinicio completado. Bot operativo y sincronizado tras el reinicio del proceso.",
            "Bot reiniciado y operativo.",
        )
        if custom_msg and custom_msg not in defaults:
            desc += f"\n\n**Nota de la administración**\n> {custom_msg}"

    elif mode == "mantenimiento":
        color = 0xD68910
        title = "🔧  Estado de la plataforma — Mantenimiento"
        desc = (
            f"**{hospital}**\n"
            f"*Comunicado del centro de operaciones*\n\n"
            f"La plataforma de gestión se encuentra en **mantenimiento técnico**.\n\n"
            f"Durante este periodo el equipo realizará actualizaciones, corrección "
            f"de incidencias y optimizaciones para mejorar la estabilidad del servicio.\n\n"
            f"**Trabajos previstos**\n"
            f"• Revisión de comandos y paneles\n"
            f"• Verificación de roles y permisos\n"
            f"• Depuración y respaldo de registros\n"
            f"• Preparación de mejoras planificadas\n\n"
            f"**Importante para el personal**\n"
            f"Algunas funciones pueden estar limitadas o no disponibles de forma temporal. "
            f"La reanudación del servicio completo se anunciará en este mismo canal."
        )
        if custom_msg:
            desc += f"\n\n**Motivo indicado por la administración**\n> {custom_msg}"

    else:
        color = 0xC0392B
        title = "⛔  Estado de la plataforma — Fuera de servicio"
        desc = (
            f"**{hospital}**\n"
            f"*Comunicado del centro de operaciones*\n\n"
            f"El sistema de gestión permanece **apagado** hasta nuevo aviso.\n\n"
            f"**Estado actual**\n"
            f"🔴 Bot de Discord — **Apagado**\n"
            f"🔴 Comandos y paneles — **No disponibles**\n"
            f"🟡 Expedientes y datos — **Conservados** (se reanudan al reinicio)\n\n"
            f"**Motivo del apagado**\n"
            f"> {custom_msg or 'Apagado por decisión de la administración del hospital.'}\n\n"
            f"Mientras el bot esté fuera de servicio no será posible usar comandos, "
            f"enviar solicitudes ni procesar verificaciones. "
            f"La reactivación se comunicará por este canal."
        )

    emb = discord.Embed(
        title=title,
        description=desc,
        color=color,
        timestamp=discord.utils.utcnow(),
    )
    if getattr(config, "LOGO_URL", None):
        try:
            emb.set_thumbnail(url=config.LOGO_URL)
        except Exception:
            pass

    emb.set_footer(text=f"🏥 {hospital}  ·  Centro de operaciones")

    if _status.get("changed_at"):
        fecha = str(_status["changed_at"])[:19].replace("T", " ") + " UTC"
        emb.add_field(name="📅 Última actualización", value=fecha, inline=True)
    if _status.get("changed_by"):
        emb.add_field(
            name="👤 Autorizado por",
            value=f"<@{_status['changed_by']}> ",
            inline=True,
        )
    emb.add_field(
        name="📡 Modo actual",
        value=f"**`{(mode or 'online').upper()}`**",
        inline=True,
    )
    return emb


async def publicar_estado(
    bot: discord.Client, guild: Optional[discord.Guild] = None
) -> None:
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

    @ui.button(label="Aprobar", style=discord.ButtonStyle.success)
    async def aprobar(self, interaction: discord.Interaction, button: ui.Button):
        if not await self._es_owner(interaction):
            await interaction.response.send_message(
                embed=crear_embed(
                    "error",
                    "Acceso restringido",
                    "Solo el **Gerente Developer** puede autorizar el control de la plataforma.\n\n"
                    "Esta acción afecta el servicio de todo el hospital.",
                ),
                ephemeral=True,
            )
            return
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            embed=crear_embed(
                "exito",
                "Operación autorizada",
                f"Se aprobó la acción **`{self.accion}`**.\n\n"
                f"El sistema ejecutará el protocolo correspondiente de inmediato.",
            ),
            ephemeral=True,
        )
        await _ejecutar_accion(self.bot, self.accion, interaction.user.id, self.extra, interaction)

    @ui.button(label="Negar", style=discord.ButtonStyle.danger)
    async def negar(self, interaction: discord.Interaction, button: ui.Button):
        if not await self._es_owner(interaction):
            await interaction.response.send_message(
                embed=crear_embed(
                    "error",
                    "Acceso restringido",
                    "Solo el **Gerente Developer** puede denegar esta solicitud.",
                ),
                ephemeral=True,
            )
            return
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            embed=crear_embed(
                "error",
                "Operación denegada",
                f"La acción **`{self.accion}`** fue rechazada por la administración.\n\n"
                f"No se realizó ningún cambio en el estado de la plataforma.",
            ),
            ephemeral=True,
        )


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
            extra or "Apagado por decisión de la administración del hospital.",
            por,
        )
        await publicar_estado(bot)
        msg = crear_embed(
            "error",
            "Plataforma en cierre",
            "El bot fue marcado **fuera de servicio**.\n\n"
            "Se cerrará la conexión en unos segundos. Los datos del hospital se conservan.",
        )
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(embed=msg)
            else:
                await interaction.response.send_message(embed=msg)
        await asyncio.sleep(1.5)
        await bot.close()

    elif accion == "encender":
        set_mode(
            "online",
            extra or "Sistemas restaurados. Plataforma operativa para todo el personal.",
            por,
        )
        await publicar_estado(bot)
        msg = crear_embed(
            "exito",
            "Plataforma restablecida",
            "El sistema se encuentra nuevamente **en servicio**.\n\n"
            "Comandos, paneles y registros están disponibles para el personal autorizado.",
        )
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(embed=msg)
            else:
                await interaction.response.send_message(embed=msg)

    elif accion == "mantenimiento":
        set_mode(
            "mantenimiento",
            extra or "Mantenimiento técnico programado por la administración.",
            por,
        )
        await publicar_estado(bot)
        msg = crear_embed(
            "aviso",
            "Modo mantenimiento activado",
            "La plataforma opera en **mantenimiento técnico**.\n\n"
            "Algunas funciones pueden quedar limitadas hasta que finalice el trabajo.",
        )
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(embed=msg)
            else:
                await interaction.response.send_message(embed=msg)

    elif accion == "reiniciar":
        set_mode(
            "online",
            extra or "Reinicio completado. Bot operativo y sincronizado.",
            por,
        )
        await publicar_estado(bot)
        msg = crear_embed(
            "aviso",
            "Reinicio de la plataforma",
            "Se inició el protocolo de reinicio.\n\n"
            "Si el servicio está supervisado (por ejemplo Railway o PM2), "
            "se reanudará automáticamente en breve.",
        )
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(embed=msg)
            else:
                await interaction.response.send_message(embed=msg)
        await asyncio.sleep(1.5)
        await bot.close()


async def manejar_control_bot(
    interaction: discord.Interaction,
    bot: discord.Client,
    accion: str,
    mensaje: str = "",
) -> None:
    user = interaction.user
    if not isinstance(user, discord.Member):
        await interaction.response.send_message(
            embed=crear_embed(
                "error",
                "Contexto inválido",
                "Este comando solo puede usarse **dentro del servidor** del hospital.",
            ),
            ephemeral=True,
        )
        return

    try:
        es_owner = permisos.member_tiene_key(user, "OWNER")
        es_co = permisos.member_tiene_key(user, "CO_OWNER")
    except Exception:
        es_owner = permisos.member_tiene_alguna_key(user, "OWNER")
        es_co = permisos.member_tiene_alguna_key(user, "CO_OWNER")

    if not es_owner and not es_co:
        await interaction.response.send_message(
            embed=crear_embed(
                "error",
                "Acceso restringido",
                "Solo el **Gerente Developer** o un **Co-Owner** pueden cambiar el estado de la plataforma.\n\n"
                "Si necesita un reinicio o mantenimiento, solicítelo a la administración.",
            ),
            ephemeral=True,
        )
        return

    if es_owner:
        await interaction.response.defer(ephemeral=True)
        await _ejecutar_accion(bot, accion, user.id, mensaje, interaction)
        return

    embed = crear_embed(
        "aviso",
        f"Solicitud de control de plataforma — {accion}",
        f"Un Co-Owner solicita ejecutar una acción sobre el sistema del hospital.\n\n"
        f"**Solicitante:** {user.mention}\n"
        f"**Cargo:** Co-Owner\n"
        f"**Acción solicitada:** `{accion}`\n"
        f"**Detalle / motivo:** {mensaje or 'Sin detalle adicional'}\n\n"
        f"Debe **aprobar** o **negar** esta solicitud. "
        f"Solo el Gerente Developer puede autorizarla.",
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
            embed=crear_embed(
                "info",
                "Solicitud enviada",
                f"Se notificó al **Gerente Developer** sobre la acción `{accion}`.\n\n"
                f"Quedará pendiente hasta que apruebe o niegue la solicitud.",
            ),
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            embed=crear_embed(
                "error",
                "No se pudo notificar",
                "No se encontró un Gerente Developer disponible.\n\n"
                "**Revisar:**\n"
                "• Que exista un miembro con key OWNER\n"
                "• Que el canal `aprobaciones` esté configurado\n"
                "• Que el bot pueda enviar mensajes privados",
            ),
            ephemeral=True,
        )


async def solicitar_o_ejecutar(
    interaction: discord.Interaction,
    bot: discord.Client,
    accion: str,
    mensaje: str = "",
) -> None:
    await manejar_control_bot(interaction, bot, accion, mensaje)


_load_status()
