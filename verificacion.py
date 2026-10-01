# -*- coding: utf-8 -*-
"""
verificacion.py — Verificación Roblox.
Tras verificar: se quita Visitante y se otorga **Comunidad**.
(Miembro se otorga al aceptar las reglas en comunidad.py)
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
ROL_COMUNIDAD_NOMBRES = ["Comunidad", "🌐 Comunidad", "comunidad", "✅ Comunidad"]
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
    lower = {n.lower(): n for n in nombres}
    for rol in guild.roles:
        if rol.name.lower() in lower or rol.name in nombres:
            return rol
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


def rol_comunidad(guild: discord.Guild) -> Optional[discord.Role]:
    try:
        import roles_acceso

        r = roles_acceso.rol_comunidad(guild)
        if r:
            return r
    except Exception:
        pass
    return encontrar_rol(guild, ROL_COMUNIDAD_NOMBRES)


def guardar_verificado(
    uid: int,
    roblox: str,
    staff_id: int,
    roblox_id: Optional[int] = None,
    extra: Optional[dict] = None,
) -> None:
    data = _load()
    entry = {"roblox": roblox, "roblox_id": roblox_id, "fecha": _now(), "staff_id": staff_id}
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


async def buscar_usuario_roblox(username: str) -> Optional[Dict[str, Any]]:
    username = username.strip()
    if not username or " " in username:
        return None
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "HospitalBot/1.0 (Discord Verification)",
    }
    async with aiohttp.ClientSession(headers=headers) as session:
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
        info["username"] = info.get("name")
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

        await interaction.response.defer(ephemeral=True)

        roblox_data = await buscar_usuario_roblox(roblox_input)
        if not roblox_data:
            await interaction.followup.send(
                embed=crear_embed(
                    "error",
                    "Usuario Roblox no encontrado",
                    f"No existe ninguna cuenta con el nombre **`{roblox_input}`**.",
                ),
                ephemeral=True,
            )
            return

        guild = interaction.client.get_guild(self.guild_id)
        if not guild:
            await interaction.followup.send(
                "❌ No pude encontrar el servidor.", ephemeral=True
            )
            return

        member = guild.get_member(interaction.user.id)
        if not member:
            await interaction.followup.send(
                "❌ No estás en el servidor.", ephemeral=True
            )
            return

        r_vis = rol_visitante(guild)
        r_com = rol_comunidad(guild)
        r_miem = rol_miembro(guild)

        if not r_com and not r_miem:
            try:
                import roles_acceso

                created = await roles_acceso.asegurar_roles_acceso(guild)
                r_com = created.get("comunidad") or rol_comunidad(guild)
            except Exception:
                pass
        if not r_com and not r_miem:
            await interaction.followup.send(
                "❌ No existe el rol **Comunidad**. Créalo o usa `/configurar_roles`.",
                ephemeral=True,
            )
            return

        try:
            if r_vis and r_vis in member.roles:
                await member.remove_roles(
                    r_vis, reason=f"Verificado Roblox: {roblox_data.get('name')}"
                )
            target = r_com or r_miem
            if target and target not in member.roles:
                await member.add_roles(
                    target, reason=f"Verificado Roblox: {roblox_data.get('name')}"
                )
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ El bot no tiene permisos para cambiar roles.",
                ephemeral=True,
            )
            return

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

        embed_verif = embed_roblox_verificacion(
            discord_user=member,
            roblox_data=roblox_data,
            staff=staff_member,
            aprobado=True,
        )
        await interaction.followup.send(
            content="🎉 **¡Verificación exitosa!** Ficha de tu personaje:",
            embed=embed_verif,
            ephemeral=True,
        )
        try:
            await member.send(
                content="🏆 **Verificación Roblox aprobada** — rol **Comunidad** otorgado.",
                embed=embed_verif,
            )
        except discord.Forbidden:
            pass

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
                    f"**Staff:** <@{self.staff_id}>\n"
                    f"**Rol:** Comunidad",
                    autor=member,
                    thumbnail_url=roblox_data.get("avatar_url"),
                )
                try:
                    await canal.send(embed=log)
                except discord.Forbidden:
                    pass


class VerificarView(ui.View):
    def __init__(self, staff_id: int, guild_id: int):
        super().__init__(timeout=86400)
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


async def enviar_dm_verificacion(member: discord.Member, staff: discord.Member) -> bool:
    embed = crear_embed(
        "roblox",
        "Verificación de cuenta Roblox",
        f"¡Hola **{member.display_name}**! 👋\n\n"
        f"El staff del **{config.NOMBRE_HOSPITAL}** te solicita verificar tu personaje de Roblox "
        f"para otorgarte el rol de **Comunidad**.\n\n"
        f"🔹 Pulsa el botón\n"
        f"🔹 Escribe tu usuario exacto de Roblox\n"
        f"**Solicitado por:** {staff.mention}\n\n"
        f"⏱️ Tienes 24 horas.",
        autor=staff,
    )
    view = VerificarView(staff.id, member.guild.id)
    try:
        await member.send(embed=embed, view=view)
        return True
    except discord.Forbidden:
        return False
