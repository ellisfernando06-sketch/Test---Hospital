# -*- coding: utf-8 -*-
"""bot_control.py — Panel de control del bot (tech limpio)."""
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
    )

    if mode == "online":
        color = 0x00E676
        title = "Sistema en línea"
        desc = (
            f"**{hospital}**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"● **Estado** — `ONLINE`\n"
            f"● **Bot** — operativo\n"
            f"● **Comandos** — disponibles\n"
            f"● **Datos** — sincronizados\n\n"
            f"Todo el personal autorizado puede usar el sistema con normalidad."
        )
        if custom_msg and custom_msg not in defaults:
            desc += f"\n\n**Nota**\n{custom_msg}"

    elif mode == "mantenimiento":
        color = 0xFFAB00
        title = "Mantenimiento en curso"
        desc = (
            f"**{hospital}**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"● **Estado** — `MANTENIMIENTO`\n"
            f"● **Bot** — en pausa parcial\n"
            f"● **Comandos** — limitados\n"
            f"● **Datos** — protegidos\n\n"
            f"Algunas funciones pueden no responder hasta que termine el trabajo."
        )
        if custom_msg and custom_msg not in defaults:
            desc += f"\n\n**Motivo**\n{custom_msg}"

    else:
        color = 0xFF5252
        title = "Sistema fuera de servicio"
        desc = (
            f"**{hospital}**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"● **Estado** — `OFFLINE`\n"
            f"● **Bot** — apagado\n"
            f"● **Comandos** — no disponibles\n"
            f"● **Datos** — conservados\n\n"
            f"**Motivo**\n{custom_msg or 'Apagado por la administración.'}\n\n"
            f"La reactivación se anunciará en este canal."
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

    if _status.get("changed_at"):
        fecha = str(_status["changed_at"])[:19].replace("T", " ") + " UTC"
        emb.add_field(name="Último cambio", value=f"`{fecha}`", inline=True)
    if _status.get("changed_by"):
        emb.add_field(name="Operador", value=f"<@{_status['changed_by']}> ", inline=True)
    emb.add_field(name="Modo", value=f"`{(mode or 'online').upper()}`", inline=True)

    emb.set_footer(text=f"{hospital}  ·  panel de control")
    return emb


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

    @ui.button(label="Aprobar", style=discord.ButtonStyle.success)
    async def aprobar(self, interaction: discord.Interaction, button: ui.Button):
        if not await self._es_owner(interaction):
            await interaction.response.send_message(
                embed=crear_embed("error", "Acceso denegado", "Solo el **Gerente Developer** puede aprobar."),
                ephemeral=True,
            )
            return
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            embed=crear_embed("exito", "Aprobado", f"Acción **`{self.accion}`** autorizada."),
            ephemeral=True,
        )
        await _ejecutar_accion(self.bot, self.accion, interaction.user.id, self.extra, interaction)

    @ui.button(label="Negar", style=discord.ButtonStyle.danger)
    async def negar(self, interaction: discord.Interaction, button: ui.Button):
        if not await self._es_owner(interaction):
            await interaction.response.send_message(
                embed=crear_embed("error", "Acceso denegado", "Solo el **Gerente Developer** puede negar."),
                ephemeral=True,
            )
            return
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            embed=crear_embed("error", "Negado", f"Acción **`{self.accion}`** rechazada."),
            ephemeral=True,
        )


async def _ejecutar_accion(
    bot: discord.Client, accion: str, por: int, extra: str,
    interaction: Optional[discord.Interaction] = None,
) -> None:
    if accion == "apagar":
        set_mode("offline", extra or "Apagado por la administración.", por)
        await publicar_estado(bot)
        msg = crear_embed("error", "Apagando", "El bot se cierra en unos segundos.")
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(embed=msg)
            else:
                await interaction.response.send_message(embed=msg)
        await asyncio.sleep(1.5)
        await bot.close()
    elif accion == "encender":
        set_mode("online", extra or "Bot encendido.", por)
        await publicar_estado(bot)
        msg = crear_embed("exito", "Sistema activo", "El bot está **encendido** otra vez.")
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(embed=msg)
            else:
                await interaction.response.send_message(embed=msg)
    elif accion == "mantenimiento":
        set_mode("mantenimiento", extra or "Mantenimiento del sistema.", por)
        await publicar_estado(bot)
        msg = crear_embed("aviso", "Mantenimiento", "Algunas funciones pueden fallar un rato.")
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(embed=msg)
            else:
                await interaction.response.send_message(embed=msg)
    elif accion == "reiniciar":
        set_mode("online", extra or "Reinicio listo.", por)
        await publicar_estado(bot)
        msg = crear_embed("aviso", "Reiniciando", "El bot debería volver solo en unos momentos.")
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(embed=msg)
            else:
                await interaction.response.send_message(embed=msg)
        await asyncio.sleep(1.5)
        await bot.close()


async def manejar_control_bot(
    interaction: discord.Interaction, bot: discord.Client, accion: str, mensaje: str = "",
) -> None:
    user = interaction.user
    if not isinstance(user, discord.Member):
        await interaction.response.send_message(
            embed=crear_embed("error", "Solo en el servidor", "Usa este comando dentro del servidor."),
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
            embed=crear_embed("error", "Acceso denegado", "Solo **Gerente Developer** o **Co-Owner**."),
            ephemeral=True,
        )
        return

    if es_owner:
        await interaction.response.defer(ephemeral=True)
        await _ejecutar_accion(bot, accion, user.id, mensaje, interaction)
        return

    embed = crear_embed(
        "aviso",
        f"Pedido de control — {accion}",
        f"**Quién pide:** {user.mention}\n**Acción:** `{accion}`\n**Detalle:** {mensaje or '—'}\n\n"
        f"El **Gerente Developer** debe aprobar o negar.",
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
            embed=crear_embed("info", "Pedido enviado", f"Se avisó al Gerente sobre **`{accion}`**."),
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            embed=crear_embed("error", "No se pudo avisar", "No hay Gerente Developer disponible."),
            ephemeral=True,
        )


async def solicitar_o_ejecutar(
    interaction: discord.Interaction, bot: discord.Client, accion: str, mensaje: str = "",
) -> None:
    await manejar_control_bot(interaction, bot, accion, mensaje)


_load_status()
