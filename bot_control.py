# -*- coding: utf-8 -*-
"""
bot_control.py — Estado del bot y control OWNER / CO_OWNER.
Textos en español, estilo tech moderado y fácil de entender.
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

    if mode == "online":
        color = 0x1ABC9C
        title = "🖥️  Sistema del hospital — En línea"
        desc = (
            f"**{hospital}**\n"
            f"Estado del bot de gestión\n\n"
            f"El sistema está **encendido y funcionando**.\n\n"
            f"Puedes usar comandos, solicitudes, verificaciones, "
            f"sanciones y el resto de módulos con normalidad.\n\n"
            f"**Servicios**\n"
            f"🟢 Bot de Discord — **Activo**\n"
            f"🟢 Comandos y paneles — **Disponibles**\n"
            f"🟢 Registros y datos — **Al día**\n"
            f"🟢 Solicitudes — **En marcha**\n\n"
            f"Si algo falla, avisa por los canales de soporte o a la dirección de tu área."
        )
        defaults = (
            "Bot operativo.",
            "Bot reiniciado.",
            "Sistemas restaurados y bot plenamente operativo. Todos los módulos disponibles.",
            "Reinicio completado. Bot operativo y sincronizado tras el reinicio del proceso.",
            "Bot reiniciado y operativo.",
            "Sistemas restaurados. Plataforma operativa para todo el personal.",
            "Sistemas restaurados. Plataforma operativa.",
        )
        if custom_msg and custom_msg not in defaults:
            desc += f"\n\n**Nota de administración**\n> {custom_msg}"

    elif mode == "mantenimiento":
        color = 0xF39C12
        title = "🔧  Sistema del hospital — Mantenimiento"
        desc = (
            f"**{hospital}**\n"
            f"Estado del bot de gestión\n\n"
            f"El sistema está en **mantenimiento**.\n\n"
            f"Se están haciendo mejoras o correcciones. "
            f"Algunas funciones pueden fallar o no estar disponibles un rato.\n\n"
            f"**En curso**\n"
            f"• Revisión de comandos\n"
            f"• Roles y permisos\n"
            f"• Limpieza de registros\n"
            f"• Preparación de actualizaciones\n\n"
            f"Cuando todo vuelva a la normalidad se avisará en este canal."
        )
        if custom_msg:
            desc += f"\n\n**Motivo**\n> {custom_msg}"

    else:
        color = 0xE74C3C
        title = "⛔  Sistema del hospital — Apagado"
        desc = (
            f"**{hospital}**\n"
            f"Estado del bot de gestión\n\n"
            f"El bot está **apagado**. No se pueden usar comandos por ahora.\n\n"
            f"**Estado**\n"
            f"🔴 Bot — **Apagado**\n"
            f"🔴 Comandos — **No disponibles**\n"
            f"🟡 Datos guardados — **Se conservan**\n\n"
            f"**Motivo**\n"
            f"> {custom_msg or 'Apagado por la administración.'}\n\n"
            f"Cuando se encienda de nuevo se publicará aquí."
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

    emb.set_footer(text=f"🖥️ {hospital}  ·  Estado del sistema")

    if _status.get("changed_at"):
        fecha = str(_status["changed_at"])[:19].replace("T", " ") + " UTC"
        emb.add_field(name="Último cambio", value=fecha, inline=True)
    if _status.get("changed_by"):
        emb.add_field(name="Quién lo cambió", value=f"<@{_status['changed_by']}> ", inline=True)
    emb.add_field(
        name="Modo",
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
                    "Sin permiso",
                    "Solo el **Gerente Developer** puede aprobar el control del bot.",
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
                "Aprobado",
                f"Se aprobó **`{self.accion}`**. El sistema lo ejecuta ahora.",
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
                    "Sin permiso",
                    "Solo el **Gerente Developer** puede negar esta solicitud.",
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
                "Negado",
                f"La acción **`{self.accion}`** fue rechazada. No se hizo ningún cambio.",
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
        set_mode("offline", extra or "Apagado por la administración.", por)
        await publicar_estado(bot)
        msg = crear_embed(
            "error",
            "Apagando el bot",
            "El bot se marca como **apagado** y se cierra en unos segundos.\nLos datos del hospital se guardan.",
        )
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(embed=msg)
            else:
                await interaction.response.send_message(embed=msg)
        await asyncio.sleep(1.5)
        await bot.close()

    elif accion == "encender":
        set_mode("online", extra or "Bot encendido. Todo el personal puede usarlo.", por)
        await publicar_estado(bot)
        msg = crear_embed(
            "exito",
            "Bot en línea",
            "El sistema volvió a estar **activo**.\nComandos y registros disponibles otra vez.",
        )
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(embed=msg)
            else:
                await interaction.response.send_message(embed=msg)

    elif accion == "mantenimiento":
        set_mode("mantenimiento", extra or "Mantenimiento del sistema.", por)
        await publicar_estado(bot)
        msg = crear_embed(
            "aviso",
            "Modo mantenimiento",
            "El bot está en **mantenimiento**.\nAlgunas cosas pueden no funcionar hasta que termine.",
        )
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(embed=msg)
            else:
                await interaction.response.send_message(embed=msg)

    elif accion == "reiniciar":
        set_mode("online", extra or "Reinicio listo. Bot operativo.", por)
        await publicar_estado(bot)
        msg = crear_embed(
            "aviso",
            "Reiniciando",
            "Se pidió el reinicio del bot.\nSi está en Railway u otro servicio, debería volver solo en unos momentos.",
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
                "Solo en el servidor",
                "Este comando hay que usarlo **dentro del servidor** del hospital.",
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
                "Sin permiso",
                "Solo el **Gerente Developer** o un **Co-Owner** pueden controlar el bot.\n\n"
                "Si necesitas un reinicio o mantenimiento, pídeselo a ellos.",
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
        f"Pedido de control del bot — {accion}",
        f"Un Co-Owner pide una acción sobre el bot.\n\n"
        f"**Quién pide:** {user.mention}\n"
        f"**Cargo:** Co-Owner\n"
        f"**Acción:** `{accion}`\n"
        f"**Detalle:** {mensaje or 'Sin detalle'}\n\n"
        f"El **Gerente Developer** debe **aprobar** o **negar**.",
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
                "Pedido enviado",
                f"Se avisó al **Gerente Developer** sobre **`{accion}`**.\n"
                f"Queda en espera hasta que apruebe o niegue.",
            ),
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            embed=crear_embed(
                "error",
                "No se pudo avisar",
                "No hay Gerente Developer disponible.\n\n"
                "Revisa que exista alguien con rol OWNER y, si puedes, el canal de aprobaciones.",
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
