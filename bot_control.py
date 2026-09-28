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
    """Comunicado oficial de estado de sistemas (estilo hospitalario)."""
    mode = get_mode()
    custom_msg = (_status.get("message") or "").strip()
    hospital = getattr(config, "NOMBRE_HOSPITAL", None) or "Hospital General"

    if mode == "online":
        color = 0x1E8449
        title = "Sistemas en servicio — Operativo"
        desc = (
            f"**Comunicado de operaciones · {hospital}**\n\n"
            f"Se informa al personal y a la comunidad que la plataforma de gestión "
            f"se encuentra **en servicio pleno**.\n\n"
            f"Los módulos de comandos, verificación, solicitudes, régimen disciplinario "
            f"y registro documental operan con normalidad.\n\n"
            f"**Panel de disponibilidad**\n"
            f"● Núcleo Discord — **Activo**\n"
            f"● Comandos y paneles — **Disponibles**\n"
            f"● Registros y expedientes — **Sincronizados**\n\n"
            f"Ante cualquier incidencia, utilice los canales oficiales de reporte."
        )
        defaults = (
            "Bot operativo.",
            "Bot reiniciado.",
            "Sistemas restaurados y bot plenamente operativo. Todos los módulos disponibles.",
            "Reinicio completado. Bot operativo y sincronizado tras el reinicio del proceso.",
            "Bot reiniciado y operativo.",
        )
        if custom_msg and custom_msg not in defaults:
            desc += f"\n\n**Nota de administración**\n> {custom_msg}"

    elif mode == "mantenimiento":
        color = 0xB7950B
        title = "Mantenimiento técnico programado"
        desc = (
            f"**Comunicado oficial · {hospital}**\n\n"
            f"La plataforma de gestión ingresa a **mantenimiento técnico**. "
            f"El equipo realizará actualizaciones, correcciones y optimizaciones "
            f"para preservar la estabilidad del servicio.\n\n"
            f"**Alcance del trabajo**\n"
            f"• Estabilidad y rendimiento de comandos\n"
            f"• Verificación de roles y permisos\n"
            f"• Depuración de registros\n"
            f"• Preparación de mejoras planificadas\n\n"
            f"**Aviso**\n"
            f"Algunas funciones pueden quedar temporalmente limitadas. "
            f"La reanudación del servicio completo se publicará en este canal."
        )
        if custom_msg:
            desc += f"\n\n**Motivo indicado**\n> {custom_msg}"

    else:
        color = 0x922B21
        title = "Plataforma fuera de servicio"
        desc = (
            f"**Comunicado oficial · {hospital}**\n\n"
            f"La plataforma de gestión permanece **fuera de servicio** hasta nuevo aviso.\n\n"
            f"**Estado**\n"
            f"● Núcleo Discord — **Apagado**\n"
            f"● Comandos y paneles — **No disponibles**\n"
            f"● Expedientes — **Conservados** (se reanudan al reinicio)\n\n"
            f"**Motivo**\n"
            f"> {custom_msg or 'Apagado por decisión de la administración.'}\n\n"
            f"No será posible procesar comandos ni solicitudes mientras el sistema "
            f"permanezca offline. La reactivación se anunciará por este medio."
        )

    embed = discord.Embed(
        title=title,
        description=desc,
        color=color,
        timestamp=discord.utils.utcnow(),
    )
    if getattr(config, "LOGO_URL", None):
        try:
            embed.set_thumbnail(url=config.LOGO_URL)
        except Exception:
            pass

    embed.set_footer(text=f"{hospital}  ·  Centro de operaciones")

    if _status.get("changed_at"):
        fecha = str(_status["changed_at"])[:19].replace("T", " ") + " UTC"
        embed.add_field(name="Última actualización", value=fecha, inline=True)
    if _status.get("changed_by"):
        embed.add_field(
            name="Autorizado por",
            value=f"<@{_status['changed_by']}>",
            inline=True,
        )
    embed.add_field(
        name="Modo actual",
        value=f"`{(mode or 'online').upper()}`",
        inline=True,
    )
    return embed


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
    except discord.Forbidden:
        pass
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
                    "Solo el **Gerente Developer** puede autorizar esta operación de sistemas.",
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
                f"Se aprobó **{self.accion}**. Ejecutando protocolo…",
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
                f"La acción **{self.accion}** fue rechazada por la administración.",
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
            extra
            or "Apagado por decisión de la administración. Se reactivará al completar el proceso técnico correspondiente.",
            por,
        )
        await publicar_estado(bot)
        msg = crear_embed(
            "error",
            "Cierre de sistemas",
            "La plataforma fue marcada **fuera de servicio**. Cerrando conexión…",
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
            extra or "Sistemas restaurados. Plataforma operativa y módulos disponibles.",
            por,
        )
        await publicar_estado(bot)
        msg = crear_embed(
            "exito",
            "Sistemas restablecidos",
            "La plataforma se encuentra nuevamente **en servicio**.",
        )
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(embed=msg)
            else:
                await interaction.response.send_message(embed=msg)

    elif accion == "mantenimiento":
        set_mode(
            "mantenimiento",
            extra
            or "Mantenimiento técnico programado. Optimización de sistemas y preparación de actualizaciones.",
            por,
        )
        await publicar_estado(bot)
        msg = crear_embed(
            "aviso",
            "Modo mantenimiento",
            "La plataforma opera en **mantenimiento técnico**. Algunas funciones pueden limitarse.",
        )
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(embed=msg)
            else:
                await interaction.response.send_message(msg if isinstance(msg, str) else embed=msg)

    elif accion == "reiniciar":
        set_mode(
            "online",
            extra
            or "Reinicio completado. Bot operativo y sincronizado tras el reinicio del proceso.",
            por,
        )
        await publicar_estado(bot)
        msg = crear_embed(
            "aviso",
            "Reinicio de sistemas",
            "Se inició el protocolo de reinicio. Si el servicio está supervisado (Railway/PM2), se reanudará automáticamente.",
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
    """OWNER ejecuta al momento. CO_OWNER solicita aprobación al OWNER."""
    user = interaction.user
    if not isinstance(user, discord.Member):
        await interaction.response.send_message(
            embed=crear_embed("error", "Contexto inválido", "Este procedimiento solo aplica dentro del servidor."),
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
                "Solo **Gerente Developer** o **Co-Owner** pueden gestionar el estado de la plataforma.",
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
        f"Solicitud de {accion} del sistema",
        f"**Solicitante:** {user.mention} (Co-Owner)\n"
        f"**Operación:** `{accion}`\n"
        f"**Detalle:** {mensaje or '—'}\n\n"
        f"Requiere autorización del **Gerente Developer**.",
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
                "Se notificó al **Gerente Developer**. La operación quedará pendiente de autorización.",
            ),
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            embed=crear_embed(
                "error",
                "Sin destinatario",
                "No se pudo contactar a ningún Gerente Developer. "
                "Configure el canal `aprobaciones` o verifique que exista un OWNER en el servidor.",
            ),
            ephemeral=True,
        )


# Alias usado por el núcleo Bot_Hospital.py
async def solicitar_o_ejecutar(
    interaction: discord.Interaction,
    bot: discord.Client,
    accion: str,
    mensaje: str = "",
) -> None:
    await manejar_control_bot(interaction, bot, accion, mensaje)


_load_status()
