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
    """Publica el embed de estado en el canal configurado (si existe)."""
    _load_status()
    emb = status_embed()
    canal_id = None
    try:
        canal_id = (getattr(config, "CANALES", {}) or {}).get("estado_bot") or (
            getattr(config, "CANALES", {}) or {}
        ).get("anuncios")
    except Exception:
        canal_id = None

    targets = [guild] if guild else list(bot.guilds)
    for g in targets:
        if not g:
            continue
        ch = None
        if canal_id:
            ch = g.get_channel(int(canal_id))
        if ch:
            try:
                await ch.send(embed=emb)
            except Exception:
                pass


class AprobacionBotView(ui.View):
    def __init__(self, accion: str, solicitante_id: int, bot: discord.Client, extra: str = ""):
        super().__init__(timeout=600)
        self.accion = accion
        self.solicitante_id = solicitante_id
        self.bot = bot
        self.extra = extra or ""

    async def _es_owner(self, interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            return False
        return permisos.member_tiene_alguna_key(interaction.user, "OWNER")

    @ui.button(label="Aprobar", style=discord.ButtonStyle.success)
    async def aprobar(self, interaction: discord.Interaction, button: ui.Button):
        if not await self._es_owner(interaction):
            await interaction.response.send_message(
                embed=crear_embed(
                    "error",
                    "Acceso restringido",
                    "Solo el **Gerente Developer (OWNER)** puede aprobar esta acción de sistemas.",
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
                "Acción autorizada",
                f"Se aprobó la operación **{self.accion}**. Ejecutando protocolo…",
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
                    "Solo el **Gerente Developer (OWNER)** puede denegar esta solicitud.",
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
                "Acción denegada",
                f"La operación **{self.accion}** fue rechazada por la administración.",
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
                await interaction.response.send_message(embed=msg)

    elif accion == "reiniciar":
        set_mode(
            "mantenimiento",
            "Reinicio de proceso en curso. Los servicios se restablecerán en breve.",
            por,
        )
        await publicar_estado(bot)
        msg = crear_embed(
            "aviso",
            "Reinicio de sistemas",
            "Se inició el protocolo de reinicio. El servicio se reanudará automáticamente.",
        )
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(embed=msg)
            else:
                await interaction.response.send_message(embed=msg)
        await asyncio.sleep(1.2)
        await bot.close()


async def _solicitar_o_ejecutar(
    inter: discord.Interaction,
    accion: str,
    mensaje: str = "",
) -> None:
    user = inter.user
    if not isinstance(user, discord.Member):
        await inter.response.send_message(
            embed=crear_embed("error", "Contexto inválido", "Este comando solo puede usarse en el servidor."),
            ephemeral=True,
        )
        return

    if permisos.member_tiene_alguna_key(user, "OWNER"):
        await inter.response.defer(ephemeral=True)
        await _ejecutar_accion(inter.client, accion, user.id, mensaje, inter)
        return

    if permisos.member_tiene_alguna_key(user, "CO_OWNER"):
        emb = crear_embed(
            "aviso",
            f"Solicitud de {accion} del sistema",
            f"**Solicitante:** {user.mention} (Co-Owner)\n"
            f"**Operación:** `{accion}`\n"
            f"**Detalle:** {mensaje or '—'}\n\n"
            f"Requiere autorización del **Gerente Developer**.",
            autor=user,
        )
        view = AprobacionBotView(accion, user.id, inter.client, mensaje)
        # MD a owners
        enviados = 0
        rid = roles_store.obtener_id_key("OWNER")
        if rid and inter.guild:
            rol = inter.guild.get_role(rid)
            if rol:
                for m in rol.members:
                    if m.bot:
                        continue
                    try:
                        await m.send(embed=emb, view=view)
                        enviados += 1
                    except Exception:
                        continue
        await inter.response.send_message(
            embed=crear_embed(
                "info",
                "Solicitud enviada",
                f"Se notificó al Gerente Developer ({enviados} destinatario/s). "
                f"Quedará en espera de autorización.",
            ),
            ephemeral=True,
        )
        return

    await inter.response.send_message(
        embed=crear_embed(
            "error",
            "Acceso restringido",
            "Solo **Gerente Developer** o **Co-Owner** pueden gestionar el estado del sistema.",
        ),
        ephemeral=True,
    )


def registrar(bot: discord.Client) -> None:
    _load_status()

    # Los comandos de control suelen vivir en el núcleo; este módulo
    # expone helpers. Si el núcleo ya registró /estado_bot etc., no duplicamos.
    try:
        presentes = {c.name for c in bot.tree.get_commands()}
    except Exception:
        presentes = set()

    if "estado_bot" not in presentes:

        @bot.tree.command(name="estado_bot", description="Consulta el estado operativo de la plataforma")
        async def estado_bot_cmd(inter: discord.Interaction):
            _load_status()
            await inter.response.send_message(embed=status_embed())

    print("[bot_control] OK — embeds de estado hospitalarios")
