# -*- coding: utf-8 -*-
"""
verificacion.py — Verificación de usuario Roblox.

Flujo:
  1. El staff elige miembros con rol "Visitante".
  2. El bot les envía un DM pidiendo su usuario de Roblox.
  3. Al confirmar, se quita Visitante y se pone Miembro (detectados por nombre).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

import discord
from discord import ui

import config
from estilos import crear_embed

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "verificaciones.json")

ROL_VISITANTE_NOMBRES = ["Visitante", "👤 Visitante", "visitante"]
ROL_MIEMBRO_NOMBRES = ["Miembro", "👤 Miembro", "miembro", "✅ Miembro"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> dict:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_PATH):
        return {"pendientes": {}, "verificados": {}}
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("pendientes", {})
        data.setdefault("verificados", {})
        return data
    except Exception:
        return {"pendientes": {}, "verificados": {}}


def _save(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def encontrar_rol(guild: discord.Guild, nombres: List[str]) -> Optional[discord.Role]:
    """Detecta un rol por nombre exacto (case-insensitive)."""
    lower = {n.lower(): n for n in nombres}
    for rol in guild.roles:
        if rol.name.lower() in lower or rol.name in nombres:
            return rol
    # Búsqueda parcial suave
    for rol in guild.roles:
        rn = rol.name.lower()
        for n in nombres:
            if n.lower() in rn or rn in n.lower():
                return rol
    return None


def rol_visitante(guild: discord.Guild) -> Optional[discord.Role]:
    return encontrar_rol(guild, ROL_VISITANTE_NOMBRES)


def rol_miembro(guild: discord.Guild) -> Optional[discord.Role]:
    return encontrar_rol(guild, ROL_MIEMBRO_NOMBRES)


def guardar_verificado(uid: int, roblox: str, staff_id: int) -> None:
    data = _load()
    data["verificados"][str(uid)] = {
        "roblox": roblox,
        "fecha": _now(),
        "staff_id": staff_id,
    }
    data["pendientes"].pop(str(uid), None)
    _save(data)


def obtener_roblox(uid: int) -> Optional[str]:
    data = _load()
    info = data["verificados"].get(str(uid))
    return info.get("roblox") if info else None


class RobloxModal(ui.Modal, title="Verificación Roblox"):
    usuario_roblox = ui.TextInput(
        label="Tu usuario de Roblox",
        placeholder="Ej: Builderman",
        max_length=32,
        min_length=3,
    )

    def __init__(self, staff_id: int, guild_id: int):
        super().__init__()
        self.staff_id = staff_id
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        roblox = str(self.usuario_roblox).strip()
        if not roblox or " " in roblox:
            await interaction.response.send_message(
                "❌ El usuario de Roblox no puede estar vacío ni tener espacios.",
                ephemeral=True,
            )
            return

        guild = interaction.client.get_guild(self.guild_id)
        if not guild:
            await interaction.response.send_message(
                "❌ No pude encontrar el servidor. Contacta al staff.",
                ephemeral=True,
            )
            return

        member = guild.get_member(interaction.user.id)
        if not member:
            await interaction.response.send_message(
                "❌ No estás en el servidor.",
                ephemeral=True,
            )
            return

        r_vis = rol_visitante(guild)
        r_miem = rol_miembro(guild)

        if not r_miem:
            await interaction.response.send_message(
                "❌ El rol **Miembro** no existe en el servidor. Avísale al admin.",
                ephemeral=True,
            )
            return

        try:
            if r_vis and r_vis in member.roles:
                await member.remove_roles(r_vis, reason=f"Verificado Roblox: {roblox}")
            if r_miem not in member.roles:
                await member.add_roles(r_miem, reason=f"Verificado Roblox: {roblox}")
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ El bot no tiene permisos para cambiar roles. Avísale al admin.",
                ephemeral=True,
            )
            return

        guardar_verificado(member.id, roblox, self.staff_id)

        embed = crear_embed(
            "exito",
            "✅ Verificación completada",
            f"**Usuario Roblox:** `{roblox}`\n"
            f"Se te otorgó el rol **{r_miem.name}**.\n¡Bienvenido al servidor!",
            autor=member,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Log si hay canal
        canal_id = config.CANALES.get("log_roles") or config.CANALES.get("log_general")
        if canal_id:
            canal = guild.get_channel(canal_id)
            if canal:
                log = crear_embed(
                    "exito",
                    "✅ Usuario verificado",
                    f"**Discord:** {member.mention}\n**Roblox:** `{roblox}`\n**Staff que inició:** <@{self.staff_id}>",
                )
                try:
                    await canal.send(embed=log)
                except discord.Forbidden:
                    pass


class VerificarView(ui.View):
    def __init__(self, staff_id: int, guild_id: int):
        super().__init__(timeout=86400)  # 24h
        self.staff_id = staff_id
        self.guild_id = guild_id

    @ui.button(label="Ingresar usuario Roblox", style=discord.ButtonStyle.success, emoji="🎮", custom_id="verif_roblox")
    async def verificar(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(RobloxModal(self.staff_id, self.guild_id))


async def enviar_dm_verificacion(
    member: discord.Member,
    staff: discord.Member,
) -> bool:
    """Envía DM de verificación. Devuelve True si se envió."""
    embed = crear_embed(
        "info",
        "🎮 Verificación de Roblox",
        f"Hola **{member.display_name}**, el staff del **{config.NOMBRE_HOSPITAL}** te pide verificar tu cuenta.\n\n"
        f"Pulsa el botón de abajo e ingresa tu **usuario de Roblox**.\n"
        f"Al confirmar, recibirás el rol de **Miembro** automáticamente.\n\n"
        f"Solicitado por: {staff.mention}",
    )
    view = VerificarView(staff.id, member.guild.id)
    try:
        await member.send(embed=embed, view=view)
        return True
    except discord.Forbidden:
        return False
