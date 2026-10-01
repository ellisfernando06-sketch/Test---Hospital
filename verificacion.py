# -*- coding: utf-8 -*-
"""
verificacion.py — Verificación Roblox.
/verificar_roblox @user | /verificar_all (DM a todos)
Al aprobar: Comunidad + Miembro, renombre username Roblox.
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import aiohttp
import discord
from discord import app_commands, ui
from discord.ext import commands

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
    lower = {n.lower() for n in nombres}
    for rol in guild.roles:
        if (rol.name or "").lower() in lower or rol.name in nombres:
            return rol
    for rol in guild.roles:
        rn = (rol.name or "").lower()
        for n in nombres:
            if n.lower() in rn:
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
                timeout=aiohttp.ClientTimeout(total=12),
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
                timeout=aiohttp.ClientTimeout(total=12),
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


async def _renombrar_roblox(member: discord.Member, roblox_name: str) -> str:
    nick = (roblox_name or "")[:32]
    if not nick:
        return "sin nombre"
    try:
        if member.nick == nick or member.display_name == nick:
            return f"ya era `{nick}`"
        await member.edit(nick=nick, reason=f"Verificación Roblox → {nick}")
        return f"renombrado a `{nick}`"
    except discord.Forbidden:
        return f"sin permiso renombre `{nick}`"
    except Exception as e:
        return f"error renombre: {e}"


async def _aplicar_roles_verificacion(
    member: discord.Member, roblox_name: str
) -> tuple:
    guild = member.guild
    ok, err = [], []
    try:
        import roles_acceso

        await roles_acceso.asegurar_roles_acceso(guild)
    except Exception:
        pass
    r_vis = rol_visitante(guild)
    r_com = rol_comunidad(guild)
    r_miem = rol_miembro(guild)
    try:
        if r_vis and r_vis in member.roles:
            await member.remove_roles(r_vis, reason=f"Verificado Roblox: {roblox_name}")
            ok.append(f"− {r_vis.name}")
    except Exception as e:
        err.append(f"Visitante: {e}")
    for rol, label in ((r_com, "Comunidad"), (r_miem, "Miembro")):
        if not rol:
            err.append(f"No existe {label}")
            continue
        if rol in member.roles:
            ok.append(f"ya tenía {rol.name}")
            continue
        try:
            await member.add_roles(rol, reason=f"Verificado Roblox: {roblox_name}")
            ok.append(f"+ {rol.name}")
        except Exception as e:
            err.append(f"{label}: {e}")
    return ok, err


class RobloxModal(ui.Modal, title="🎮 Verificación Roblox"):
    usuario_roblox = ui.TextInput(
        label="Tu usuario de Roblox (exacto)",
        placeholder="Ej: Builderman  (sin espacios)",
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
                "❌ Usuario inválido (sin espacios).", ephemeral=True
            )
            return
        await interaction.response.defer(ephemeral=True)
        roblox_data = await buscar_usuario_roblox(roblox_input)
        if not roblox_data:
            await interaction.followup.send(
                embed=crear_embed(
                    "error",
                    "Usuario Roblox no encontrado",
                    f"No existe **`{roblox_input}`**.",
                ),
                ephemeral=True,
            )
            return
        guild = interaction.client.get_guild(self.guild_id)
        if not guild:
            await interaction.followup.send(
                "❌ Servidor no encontrado.", ephemeral=True
            )
            return
        member = guild.get_member(interaction.user.id)
        if not member:
            await interaction.followup.send(
                "❌ No estás en el servidor.", ephemeral=True
            )
            return
        roblox_name = roblox_data.get("name") or roblox_input
        roles_ok, roles_err = await _aplicar_roles_verificacion(member, roblox_name)
        nick_msg = await _renombrar_roblox(member, roblox_name)
        guardar_verificado(
            member.id,
            roblox_name,
            self.staff_id,
            roblox_id=roblox_data.get("id"),
            extra={
                "displayName": roblox_data.get("displayName"),
                "avatar_url": roblox_data.get("avatar_url"),
                "nick": nick_msg,
            },
        )
        staff_member = guild.get_member(self.staff_id)
        embed_verif = embed_roblox_verificacion(
            discord_user=member,
            roblox_data=roblox_data,
            staff=staff_member,
            aprobado=True,
        )
        embed_verif.add_field(
            name="Roles", value="\n".join(roles_ok) or "—", inline=True
        )
        if roles_err:
            embed_verif.add_field(
                name="Avisos", value="\n".join(roles_err)[:500], inline=True
            )
        embed_verif.add_field(name="Apodo", value=nick_msg, inline=False)
        await interaction.followup.send(
            content="🎉 **Verificación exitosa**", embed=embed_verif, ephemeral=True
        )
        try:
            await member.send(
                content=f"🏆 Verificación aprobada · `{roblox_name}` · {nick_msg}",
                embed=embed_verif,
            )
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
        custom_id="verif_roblox_btn",
    )
    async def verificar(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(
            RobloxModal(self.staff_id, self.guild_id)
        )


async def enviar_dm_verificacion(member: discord.Member, staff: discord.Member) -> bool:
    hospital = getattr(config, "NOMBRE_HOSPITAL", None) or "Hospital"
    embed = crear_embed(
        "roblox",
        "Verificación de cuenta Roblox",
        f"¡Hola **{member.display_name}**!\n\n"
        f"Staff de **{hospital}** solicita verificar tu Roblox.\n\n"
        f"• Rol **Comunidad** (+ Miembro si aplica)\n"
        f"• Apodo = username Roblox\n\n"
        f"**Solicitado por:** {staff.mention}\n⏱️ 24 horas.",
        autor=staff,
    )
    view = VerificarView(staff.id, member.guild.id)
    try:
        await member.send(embed=embed, view=view)
        return True
    except discord.Forbidden:
        return False


def _puede_staff(member: discord.Member) -> bool:
    if member.guild_permissions.manage_roles or member.guild_permissions.administrator:
        return True
    try:
        import permisos

        return permisos.member_tiene_alguna_key(
            member,
            "FUNDADOR_OWNER",
            "CO_OWNER",
            "OWNER",
            "DIR_RRHH",
            "PREFECTO_OPERACIONES",
        )
    except Exception:
        return False


def registrar(bot: commands.Bot) -> None:
    for name in ("verificar_roblox", "verificar", "verificar_all"):
        try:
            bot.tree.remove_command(name)
        except Exception:
            pass

    @bot.tree.command(
        name="verificar_roblox",
        description="[Staff] Verificación Roblox a un miembro (roles + renombre)",
    )
    @app_commands.describe(miembro="Usuario a verificar")
    async def verificar_roblox_cmd(
        inter: discord.Interaction, miembro: discord.Member
    ):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _puede_staff(inter.user):
            return await inter.response.send_message(
                "❌ Solo staff.", ephemeral=True
            )
        if miembro.bot:
            return await inter.response.send_message(
                "❌ No bots.", ephemeral=True
            )
        ok = await enviar_dm_verificacion(miembro, inter.user)
        if ok:
            await inter.response.send_message(
                embed=crear_embed(
                    "exito",
                    "Verificación enviada",
                    f"DM enviado a {miembro.mention}.",
                ),
                ephemeral=True,
            )
        else:
            await inter.response.send_message(
                embed=crear_embed(
                    "aviso",
                    "DM cerrado",
                    f"{miembro.mention} no acepta MD. Usa el botón abajo.",
                ),
                view=VerificarView(inter.user.id, inter.guild.id),
                ephemeral=True,
            )
        data = _load()
        data["pendientes"][str(miembro.id)] = {
            "staff_id": inter.user.id,
            "guild_id": inter.guild.id,
            "at": _now(),
        }
        _save(data)

    @bot.tree.command(
        name="verificar", description="[Staff] Alias de /verificar_roblox"
    )
    @app_commands.describe(miembro="Usuario a verificar")
    async def verificar_alias(inter: discord.Interaction, miembro: discord.Member):
        await verificar_roblox_cmd.callback(inter, miembro)

    @bot.tree.command(
        name="verificar_all",
        description="[Staff] Envía por DM la verificación Roblox a TODOS los miembros",
    )
    async def verificar_all_cmd(inter: discord.Interaction):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _puede_staff(inter.user):
            return await inter.response.send_message(
                "❌ Solo staff.", ephemeral=True
            )
        await inter.response.defer(ephemeral=True)
        miembros = [m for m in inter.guild.members if not m.bot]
        enviados = fallidos = 0
        data = _load()
        for m in miembros:
            if await enviar_dm_verificacion(m, inter.user):
                enviados += 1
                data["pendientes"][str(m.id)] = {
                    "staff_id": inter.user.id,
                    "guild_id": inter.guild.id,
                    "at": _now(),
                    "masivo": True,
                }
            else:
                fallidos += 1
            await asyncio.sleep(0.35)
        _save(data)
        await inter.followup.send(
            embed=crear_embed(
                "exito" if enviados else "aviso",
                "Verificación masiva",
                f"**Miembros:** {len(miembros)}\n"
                f"**DM enviados:** {enviados}\n"
                f"**DM cerrados:** {fallidos}\n\n"
                f"Al completar: **Comunidad** + apodo Roblox.",
            ),
            ephemeral=True,
        )

    print("[verificacion] OK — /verificar_roblox + /verificar_all")
