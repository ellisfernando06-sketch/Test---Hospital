# -*- coding: utf-8 -*-
"""
bot_control.py — Core status & OWNER control (visual GOD-TIER).
API compatible con el núcleo. Solo cambia presentación.
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
    line = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if mode == "online":
        color = 0x00F5D4
        title = "『 CORE 』  SYSTEM ONLINE"
        desc = (
            f"{line}\n"
            f"**{hospital.upper()}** · NÚCLEO OPERATIVO\n"
            f"{line}\n\n"
            f"Todos los subsistemas reportan **integridad nominal**.\n"
            f"La matriz de comandos, identidad, solicitudes y régimen "
            f"disciplinario opera en **tiempo real**.\n\n"
            f"```ansi\n"
            f"┌─────────────────────────────────┐\n"
            f"│  CORE ENGINE ..........  ONLINE │\n"
            f"│  COMMAND GRID .........  READY  │\n"
            f"│  DATA VAULT ...........  SYNC   │\n"
            f"│  SECURITY LAYER .......  ACTIVE │\n"
            f"└─────────────────────────────────┘\n"
            f"```\n"
            f"*Incidencias → canales oficiales de reporte.*"
        )
        defaults = (
            "Bot operativo.",
            "Bot reiniciado.",
            "Sistemas restaurados y bot plenamente operativo. Todos los módulos disponibles.",
            "Reinicio completado. Bot operativo y sincronizado tras el reinicio del proceso.",
            "Bot reiniciado y operativo.",
        )
        if custom_msg and custom_msg not in defaults:
            desc += f"\n\n**▸ NOTA DE ADMINISTRACIÓN**\n> *{custom_msg}*"

    elif mode == "mantenimiento":
        color = 0xFFB020
        title = "『 CORE 』  MAINTENANCE MODE"
        desc = (
            f"{line}\n"
            f"**{hospital.upper()}** · VENTANA TÉCNICA\n"
            f"{line}\n\n"
            f"El núcleo entra en **mantenimiento controlado**.\n"
            f"Se ejecutan actualizaciones, depuración y refuerzo de estabilidad.\n\n"
            f"```ansi\n"
            f"┌─────────────────────────────────┐\n"
            f"│  CORE ENGINE ..........  HOLD   │\n"
            f"│  COMMAND GRID .........  LIMITED│\n"
            f"│  DATA VAULT ...........  SAFE   │\n"
            f"│  PATCH PIPELINE .......  RUNNING│\n"
            f"└─────────────────────────────────┘\n"
            f"```\n"
            f"*La reactivación plena se anunciará en este canal.*"
        )
        if custom_msg:
            desc += f"\n\n**▸ MOTIVO**\n> *{custom_msg}*"

    else:
        color = 0xFF4D6D
        title = "『 CORE 』  SYSTEM OFFLINE"
        desc = (
            f"{line}\n"
            f"**{hospital.upper()}** · NÚCLEO DETENIDO\n"
            f"{line}\n\n"
            f"La plataforma permanece **fuera de servicio** hasta nueva orden.\n\n"
            f"```ansi\n"
            f"┌─────────────────────────────────┐\n"
            f"│  CORE ENGINE ..........  OFF    │\n"
            f"│  COMMAND GRID .........  LOCKED │\n"
            f"│  DATA VAULT ...........  FROZEN │\n"
            f"│  RECOVERY .............  STANDBY│\n"
            f"└─────────────────────────────────┘\n"
            f"```\n"
            f"**▸ MOTIVO**\n"
            f"> *{custom_msg or 'Apagado por decisión de la administración.'}*\n\n"
            f"*Comandos y solicitudes no estarán disponibles hasta el reinicio.*"
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

    emb.set_footer(text=f"⬡  {hospital.upper()}  │  CORE STATUS  │  HOSPITAL OS")

    if _status.get("changed_at"):
        fecha = str(_status["changed_at"])[:19].replace("T", " ") + " UTC"
        emb.add_field(name="▸ Timestamp", value=f"`{fecha}`", inline=True)
    if _status.get("changed_by"):
        emb.add_field(name="▸ Operator", value=f"<@{_status['changed_by']}> ", inline=True)
    emb.add_field(
        name="▸ Mode",
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
                    "Privilegios insuficientes",
                    "Solo el **Gerente Developer** puede autorizar operaciones de núcleo.",
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
                "Autorización concedida",
                f"Operación **`{self.accion}`** aprobada. Ejecutando secuencia…",
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
                    "Privilegios insuficientes",
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
                "Autorización denegada",
                f"Operación **`{self.accion}`** rechazada por la administración.",
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
        set_mode("offline", extra or "Apagado por decisión de la administración.", por)
        await publicar_estado(bot)
        msg = crear_embed(
            "error",
            "Core shutdown",
            "Núcleo marcado **OFFLINE**. Cerrando enlace…",
        )
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(embed=msg)
            else:
                await interaction.response.send_message(embed=msg)
        await asyncio.sleep(1.5)
        await bot.close()

    elif accion == "encender":
        set_mode("online", extra or "Sistemas restaurados. Plataforma operativa.", por)
        await publicar_estado(bot)
        msg = crear_embed(
            "exito",
            "Core restored",
            "Núcleo nuevamente en **servicio pleno**.",
        )
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(embed=msg)
            else:
                await interaction.response.send_message(embed=msg)

    elif accion == "mantenimiento":
        set_mode("mantenimiento", extra or "Mantenimiento técnico programado.", por)
        await publicar_estado(bot)
        msg = crear_embed(
            "aviso",
            "Maintenance engaged",
            "Núcleo en **modo mantenimiento**. Capacidad limitada.",
        )
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(embed=msg)
            else:
                await interaction.response.send_message(embed=msg)

    elif accion == "reiniciar":
        set_mode("online", extra or "Reinicio completado. Bot operativo.", por)
        await publicar_estado(bot)
        msg = crear_embed(
            "aviso",
            "Core reboot",
            "Secuencia de reinicio iniciada. Recuperación automática si el proceso está supervisado.",
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
            embed=crear_embed("error", "Contexto inválido", "Ejecute este módulo dentro del servidor."),
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
                "Privilegios insuficientes",
                "Solo **Gerente Developer** o **Co-Owner** pueden operar el núcleo.",
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
        f"Solicitud de núcleo · {accion}",
        f"**Operador:** {user.mention}\n"
        f"**Nivel:** Co-Owner\n"
        f"**Acción:** `{accion}`\n"
        f"**Detalle:** {mensaje or '—'}\n\n"
        f"Requiere firma del **Gerente Developer**.",
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
                "Solicitud en cola",
                "Notificación enviada al **Gerente Developer**. Pendiente de resolución.",
            ),
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            embed=crear_embed(
                "error",
                "Sin operador destino",
                "No se localizó Gerente Developer.\nConfigure `aprobaciones` o asigne un OWNER.",
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
