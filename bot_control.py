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
    mode = get_mode()
    colores = {"online": 0x2ECC71, "mantenimiento": 0xF39C12, "offline": 0xE74C3C}
    titulos = {
        "online": "🟢 Bot Online",
        "mantenimiento": "🟡 Bot en Mantenimiento",
        "offline": "🔴 Bot Offline / Apagado",
    }
    embed = discord.Embed(
        title=titulos.get(mode, "Estado del bot"),
        description=_status.get("message") or "",
        color=colores.get(mode, 0x95A5A6),
        timestamp=discord.utils.utcnow(),
    )
    embed.set_footer(text=config.NOMBRE_HOSPITAL)
    if _status.get("changed_at"):
        embed.add_field(name="Último cambio", value=_status["changed_at"][:19].replace("T", " ") + " UTC", inline=True)
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
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Aprobación CO_OWNER → OWNER
# ---------------------------------------------------------------------------

class AprobacionBotView(ui.View):
    def __init__(self, accion: str, solicitante_id: int, bot: discord.Client, extra: str = ""):
        super().__init__(timeout=300)
        self.accion = accion  # apagar | encender | mantenimiento | reiniciar
        self.solicitante_id = solicitante_id
        self.bot = bot
        self.extra = extra
        self.respondido = False

    async def _solo_owner(self, interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            return False
        if permisos.member_tiene_key(interaction.user, "OWNER"):
            return True
        await interaction.response.send_message("❌ Solo el OWNER puede aprobar o rechazar.", ephemeral=True)
        return False

    @ui.button(label="Aprobar", style=discord.ButtonStyle.success, emoji="✅")
    async def aprobar(self, interaction: discord.Interaction, button: ui.Button):
        if not await self._solo_owner(interaction):
            return
        if self.respondido:
            await interaction.response.send_message("Ya se respondió esta solicitud.", ephemeral=True)
            return
        self.respondido = True
        await interaction.response.edit_message(
            content=f"✅ Aprobado por {interaction.user.mention}",
            view=None,
        )
        await _ejecutar_accion(self.bot, self.accion, interaction.user.id, self.extra, interaction)

    @ui.button(label="Rechazar", style=discord.ButtonStyle.danger, emoji="❌")
    async def rechazar(self, interaction: discord.Interaction, button: ui.Button):
        if not await self._solo_owner(interaction):
            return
        if self.respondido:
            await interaction.response.send_message("Ya se respondió esta solicitud.", ephemeral=True)
            return
        self.respondido = True
        await interaction.response.edit_message(
            content=f"❌ Rechazado por {interaction.user.mention}",
            view=None,
        )


async def _ejecutar_accion(
    bot: discord.Client,
    accion: str,
    por: int,
    extra: str,
    interaction: Optional[discord.Interaction] = None,
) -> None:
    if accion == "apagar":
        set_mode("offline", extra or "Bot apagado por el OWNER.", por)
        await publicar_estado(bot)
        # BUG CORREGIDO: antes se llamaba a interaction.followup.send() incluso
        # cuando la interacción todavía NO tenía una respuesta inicial enviada
        # (interaction.response.is_done() == False). followup.send() requiere
        # que ya exista una respuesta previa (send_message o defer); si no,
        # Discord devuelve un error (webhook token no válido) y el mensaje
        # nunca llega. Ahora se elige el método correcto según el estado real
        # de la interacción, igual que en las demás acciones.
        msg = "🔴 Bot marcado como **offline**. Cerrando conexión…"
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(msg)
            else:
                await interaction.response.send_message(msg)
        await asyncio.sleep(1.5)
        await bot.close()

    elif accion == "encender":
        set_mode("online", extra or "Bot operativo.", por)
        await publicar_estado(bot)
        msg = "🟢 Bot en modo **online**."
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(msg)
            else:
                await interaction.response.send_message(msg)

    elif accion == "mantenimiento":
        set_mode("mantenimiento", extra or "Bot en mantenimiento. Algunos comandos pueden estar limitados.", por)
        await publicar_estado(bot)
        msg = "🟡 Bot en modo **mantenimiento**."
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(msg)
            else:
                await interaction.response.send_message(msg)

    elif accion == "reiniciar":
        set_mode("online", extra or "Bot reiniciado.", por)
        await publicar_estado(bot)
        msg = "🔄 Reinicio solicitado. Si el proceso está bajo un supervisor (systemd/PM2/Railway), se reiniciará solo. Cerrando…"
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(msg)
            else:
                await interaction.response.send_message(msg)
        await asyncio.sleep(1.5)
        await bot.close()


async def solicitar_o_ejecutar(
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

    # Canal de aprobaciones o DM a OWNERS
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
