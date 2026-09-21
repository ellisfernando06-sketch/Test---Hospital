# -*- coding: utf-8 -*-
"""
verificacion.py — Verificación de usuario Roblox enlazada con la API oficial.

Flujo mejorado:
  1. El staff elige miembros con rol "Visitante".
  2. El bot les envía un DM pidiendo su usuario de Roblox.
  3. Al confirmar, el bot consulta la API de Roblox, obtiene avatar,
     display name, ID y fecha de creación.
  4. Envía un embed rico de verificación del personaje (estilo whitelist).
  5. Se quita Visitante y se pone Miembro.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import aiohttp
import discord
from discord import ui

import config
from estilos import crear_embed, embed_roblox_verificacion

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


def guardar_verificado(uid: int, roblox: str, staff_id: int, roblox_id: Optional[int] = None, extra: Optional[dict] = None) -> None:
    data = _load()
    entry = {
        "roblox": roblox,
        "roblox_id": roblox_id,
        "fecha": _now(),
        "staff_id": staff_id,
    }
    if extra:
        entry.update(extra)
    data["verificados"][str(uid)] = entry
    data["pendientes"].pop(str(uid), None)
    _save(data)


def obtener_roblox(uid: int) -> Optional[str]:
    data = _load()
    info = data["verificados"].get(str(uid))
    return info.get("roblox") if info else None


def obtener_roblox_completo(uid: int) -> Optional[dict]:
    data = _load()
    return data["verificados"].get(str(uid))


# ─────────────────────────────────────────────────────────────
# API de Roblox (pública, sin token)
# ─────────────────────────────────────────────────────────────

async def buscar_usuario_roblox(username: str) -> Optional[Dict[str, Any]]:
    """
    Busca un usuario de Roblox por nombre de usuario.
    Devuelve dict con: id, name, displayName, created, avatar_url, description...
    o None si no existe / error.
    """
    username = username.strip()
    if not username or " " in username:
        return None

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "HospitalBot/1.0 (Discord Verification)",
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        # 1. Resolver username → userId
        payload = {"usernames": [username], "excludeBannedUsers": True}
        try:
            async with session.post(
                "https://users.roblox.com/v1/usernames/users",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                users = data.get("data") or []
                if not users:
                    return None
                user_id = users[0].get("id")
                if not user_id:
                    return None
        except Exception:
            return None

        # 2. Datos completos del usuario
        try:
            async with session.get(
                f"https://users.roblox.com/v1/users/{user_id}",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    return None
                info = await resp.json()
        except Exception:
            return None

        # 3. Avatar headshot
        avatar_url = None
        try:
            async with session.get(
                "https://thumbnails.roblox.com/v1/users/avatar-headshot",
                params={
                    "userIds": str(user_id),
                    "size": "420x420",
                    "format": "Png",
                    "isCircular": "false",
                },
                timeout=aiohttp.ClientTimeout(total=8),
            ) as resp:
                if resp.status == 200:
                    thumb = await resp.json()
                    data_list = thumb.get("data") or []
                    if data_list and data_list[0].get("imageUrl"):
                        avatar_url = data_list[0]["imageUrl"]
        except Exception:
            pass

        info["avatar_url"] = avatar_url
        info["username"] = info.get("name")  # compat
        return info


class RobloxModal(ui.Modal, title="🎮 Verificación Roblox"):
    usuario_roblox = ui.TextInput(
        label="Tu usuario de Roblox (exacto)",
        placeholder="Ej: oficial_salazar16  (sin espacios)",
        max_length=32,
        min_length=3,
    )

    def __init__(self, staff_id: int, guild_id: int):
        super().__init__()
        self.staff_id = staff_id
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        roblox_input = str(self.usuario_roblox).strip()
        if not roblox_input or " " in roblox_input:
            await interaction.response.send_message(
                "❌ El usuario de Roblox no puede estar vacío ni tener espacios.",
                ephemeral=True,
            )
            return

        # Defer porque la API puede tardar
        await interaction.response.defer(ephemeral=True)

        # Consultar Roblox
        roblox_data = await buscar_usuario_roblox(roblox_input)
        if not roblox_data:
            await interaction.followup.send(
                embed=crear_embed(
                    "error",
                    "Usuario Roblox no encontrado",
                    f"No existe ninguna cuenta con el nombre **`{roblox_input}`**.\n"
                    "Verifica que lo escribiste **exactamente** igual (mayúsculas/minúsculas no importan, pero sin espacios ni caracteres extra).\n\n"
                    "Inténtalo de nuevo con el botón.",
                ),
                ephemeral=True,
            )
            return

        guild = interaction.client.get_guild(self.guild_id)
        if not guild:
            await interaction.followup.send(
                "❌ No pude encontrar el servidor. Contacta al staff.",
                ephemeral=True,
            )
            return

        member = guild.get_member(interaction.user.id)
        if not member:
            await interaction.followup.send(
                "❌ No estás en el servidor.",
                ephemeral=True,
            )
            return

        r_vis = rol_visitante(guild)
        r_miem = rol_miembro(guild)

        if not r_miem:
            await interaction.followup.send(
                "❌ El rol **Miembro** no existe en el servidor. Avísale al admin.",
                ephemeral=True,
            )
            return

        # Cambiar roles
        try:
            if r_vis and r_vis in member.roles:
                await member.remove_roles(r_vis, reason=f"Verificado Roblox: {roblox_data.get('name')}")
            if r_miem not in member.roles:
                await member.add_roles(r_miem, reason=f"Verificado Roblox: {roblox_data.get('name')}")
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ El bot no tiene permisos para cambiar roles. Avísale al admin.",
                ephemeral=True,
            )
            return

        # Guardar
        staff_member = guild.get_member(self.staff_id)
        guardar_verificado(
            member.id,
            roblox_data.get("name") or roblox_input,
            self.staff_id,
            roblox_id=roblox_data.get("id"),
            extra={
                "displayName": roblox_data.get("displayName"),
                "avatar_url": roblox_data.get("avatar_url"),
            },
        )

        # Embed rico de verificación del personaje (estilo whitelist)
        embed_verif = embed_roblox_verificacion(
            discord_user=member,
            roblox_data=roblox_data,
            staff=staff_member,
            aprobado=True,
        )

        # Mensaje de confirmación ephemeral + el embed completo
        await interaction.followup.send(
            content="🎉 **¡Verificación exitosa!** Aquí está la ficha de tu personaje:",
            embed=embed_verif,
            ephemeral=True,
        )

        # También enviar el embed al DM del usuario (por si el ephemeral se pierde)
        try:
            await member.send(
                content="🏆 **Tu verificación de personaje Roblox ha sido aprobada**",
                embed=embed_verif,
            )
        except discord.Forbidden:
            pass

        # Log en canal
        canal_id = config.CANALES.get("log_roles") or config.CANALES.get("log_general")
        if canal_id:
            canal = guild.get_channel(canal_id)
            if canal:
                log = crear_embed(
                    "exito",
                    "✅ Usuario verificado (Roblox)",
                    f"**Discord:** {member.mention} (`{member.id}`)\n"
                    f"**Roblox:** `{roblox_data.get('name')}` (ID: `{roblox_data.get('id')}`)\n"
                    f"**Display:** {roblox_data.get('displayName')}\n"
                    f"**Staff que inició:** <@{self.staff_id}>",
                    autor=member,
                    thumbnail_url=roblox_data.get("avatar_url"),
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

    @ui.button(
        label="Ingresar usuario Roblox",
        style=discord.ButtonStyle.success,
        emoji="🎮",
        custom_id="verif_roblox",
    )
    async def verificar(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(RobloxModal(self.staff_id, self.guild_id))


async def enviar_dm_verificacion(
    member: discord.Member,
    staff: discord.Member,
) -> bool:
    """Envía DM de verificación con embed creativo. Devuelve True si se envió."""
    embed = crear_embed(
        "roblox",
        "Verificación de cuenta Roblox",
        f"¡Hola **{member.display_name}**! 👋\n\n"
        f"El staff del **{config.NOMBRE_HOSPITAL}** te solicita verificar tu personaje de Roblox "
        f"para poder otorgarte el rol de **Miembro** y acceder a todas las áreas del servidor.\n\n"
        f"🔹 Pulsa el botón de abajo\n"
        f"🔹 Escribe tu **usuario exacto de Roblox** (sin espacios)\n"
        f"🔹 El bot consultará la API oficial de Roblox y te mostrará la ficha de tu personaje\n\n"
        f"**Solicitado por:** {staff.mention}\n\n"
        f"⏱️ Tienes 24 horas para completar este proceso.",
        autor=staff,
    )
    view = VerificarView(staff.id, member.guild.id)
    try:
        await member.send(embed=embed, view=view)
        return True
    except discord.Forbidden:
        return False
