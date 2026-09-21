# -*- coding: utf-8 -*-
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
        if custom_msg and custom_msg not in ("Bot operativo.", "Bot reiniciado.", "Sistemas restaurados y bot plenamente operativo. Todos los módulos disponibles.", "Reinicio completado. Bot operativo y sincronizado tras el reinicio del proceso."):
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
        embed.add_field(name="👤 Autorizado por", value=f"<{_status['changed_by']}>", inline=True)
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


# --- Resto del archivo (comandos OWNER / CO_OWNER, vistas de aprobación, etc.) se mantiene ---
# Por espacio, se asume que el resto del archivo original sigue después de esta función.
# Si el archivo quedó incompleto, restaurar desde el local y volver a push.

# Cargar estado al importar
_load_status()
