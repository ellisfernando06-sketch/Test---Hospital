# -*- coding: utf-8 -*-
"""
limpiar_roles.py
- /limpiar_roles_viejos — borra roles fuera del organigrama (con respaldo)
- /eliminar_roles_sin_uso — borra roles con 0 miembros (no protegidos)
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List, Set

import discord
from discord import ui
from discord.ext import commands

import roles_config
from estilos import crear_embed

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def _puede_admin(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    if member.guild and member.id == member.guild.owner_id:
        return True
    try:
        import permisos

        return permisos.member_tiene_alguna_key(
            member, "FUNDADOR_OWNER", "CO_OWNER", "OWNER"
        )
    except Exception:
        return False


def _nombres_protegidos() -> Set[str]:
    names: Set[str] = set()
    for _, (nombre, _) in roles_config.KEYS_NOMBRES.items():
        names.add(nombre)
        names.add(nombre.lower())
    for _, nombre, _ in roles_config.SEPARADORES_ROLES:
        names.add(nombre)
        names.add(nombre.lower())
    for _, (nombre, _) in roles_config.ROLES_OTORGADOS_CONSERVAR.items():
        names.add(nombre)
        names.add(nombre.lower())
    for n in (
        "Gerente Developer",
        "Fundador y Owner",
        "Owner",
        "Co-Owner",
        "Suspendido",
        "Inactividad Justificada",
        "@everyone",
    ):
        names.add(n)
        names.add(n.lower())
    return names


def _guardar_respaldo(guild: discord.Guild, etiqueta: str = "roles") -> str:
    os.makedirs(_DATA_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = os.path.join(_DATA_DIR, f"{etiqueta}_backup_{ts}.json")
    data = {
        "guild_id": guild.id,
        "roles": [
            {
                "id": r.id,
                "name": r.name,
                "position": r.position,
                "members": len(r.members),
            }
            for r in guild.roles
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def _roles_fuera_organigrama(guild: discord.Guild) -> List[discord.Role]:
    prot = _nombres_protegidos()
    top = guild.me.top_role if guild.me else None
    out: List[discord.Role] = []
    for role in guild.roles:
        if role.is_default() or role.managed:
            continue
        if role.name in prot or role.name.lower() in prot:
            continue
        if top and not (role < top):
            continue
        out.append(role)
    out.sort(key=lambda r: r.position)
    return out


def _roles_sin_miembros(guild: discord.Guild) -> List[discord.Role]:
    """Roles con 0 miembros, no protegidos, gestionables por el bot."""
    prot = _nombres_protegidos()
    top = guild.me.top_role if guild.me else None
    out: List[discord.Role] = []
    for role in guild.roles:
        if role.is_default() or role.managed:
            continue
        if role.name in prot or role.name.lower() in prot:
            continue
        if top and not (role < top):
            continue
        try:
            if len(role.members) > 0:
                continue
        except Exception:
            continue
        out.append(role)
    out.sort(key=lambda r: r.position)
    return out


class ConfirmarBorradoView(ui.View):
    def __init__(self, role_ids: List[int], backup_path: str, author_id: int, titulo: str):
        super().__init__(timeout=120)
        self.role_ids = role_ids
        self.backup_path = backup_path
        self.author_id = author_id
        self.titulo = titulo
        self.done = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ Solo quien ejecutó el comando.", ephemeral=True
            )
            return False
        return True

    @ui.button(label="✅ Confirmar borrado", style=discord.ButtonStyle.danger)
    async def confirmar(self, interaction: discord.Interaction, button: ui.Button):
        if self.done:
            return
        self.done = True
        for c in self.children:
            c.disabled = True
        await interaction.response.edit_message(view=self)

        borrados: List[str] = []
        errores: List[str] = []
        for rid in self.role_ids:
            role = interaction.guild.get_role(rid) if interaction.guild else None
            if not role:
                continue
            try:
                name = role.name
                await role.delete(reason=self.titulo)
                borrados.append(name)
            except Exception as e:
                errores.append(f"{role.name}: {e}")

        emb = crear_embed(
            "exito" if borrados else "aviso",
            "Limpieza completada",
            f"Eliminados: **{len(borrados)}** · Errores: **{len(errores)}**\n"
            f"Respaldo: `{os.path.basename(self.backup_path)}`",
        )
        if borrados:
            emb.add_field(
                name="Eliminados",
                value="\n".join(f"• {n}" for n in borrados[:40]) or "—",
                inline=False,
            )
        if errores:
            emb.add_field(
                name="Errores",
                value="\n".join(errores[:15]),
                inline=False,
            )
        await interaction.followup.send(embed=emb, ephemeral=True)

    @ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: ui.Button):
        self.done = True
        for c in self.children:
            c.disabled = True
        await interaction.response.edit_message(
            content="❎ Cancelado. No se eliminó ningún rol.", embed=None, view=self
        )


def registrar(bot: commands.Bot) -> None:
    for name in ("limpiar_roles_viejos", "eliminar_roles_sin_uso"):
        try:
            bot.tree.remove_command(name)
        except Exception:
            pass

    @bot.tree.command(
        name="limpiar_roles_viejos",
        description="[Admin] Respaldo + elimina roles que NO están en el organigrama",
    )
    async def limpiar_roles_viejos(inter: discord.Interaction):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _puede_admin(inter.user):
            return await inter.response.send_message(
                "❌ Solo Administrador o Fundador.", ephemeral=True
            )
        await inter.response.defer(ephemeral=True)
        path = _guardar_respaldo(inter.guild, "roles_viejos")
        candidatos = _roles_fuera_organigrama(inter.guild)
        if not candidatos:
            return await inter.followup.send(
                embed=crear_embed(
                    "info",
                    "Sin roles viejos",
                    f"No hay roles fuera del organigrama.\nRespaldo: `{os.path.basename(path)}`",
                ),
                ephemeral=True,
            )
        lista = "\n".join(f"• **{r.name}**" for r in candidatos[:40])
        emb = crear_embed(
            "aviso",
            f"⚠️ {len(candidatos)} roles fuera del organigrama",
            f"Respaldo: `{os.path.basename(path)}`\nConfirma en 2 minutos.",
        )
        emb.add_field(name="Lista", value=lista[:1000], inline=False)
        view = ConfirmarBorradoView(
            [r.id for r in candidatos], path, inter.user.id, "Limpieza organigrama"
        )
        await inter.followup.send(embed=emb, view=view, ephemeral=True)

    @bot.tree.command(
        name="eliminar_roles_sin_uso",
        description="[Admin] Respaldo + elimina roles con 0 miembros (no protegidos)",
    )
    async def eliminar_roles_sin_uso(inter: discord.Interaction):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _puede_admin(inter.user):
            return await inter.response.send_message(
                "❌ Solo Administrador o Fundador.", ephemeral=True
            )
        await inter.response.defer(ephemeral=True)
        path = _guardar_respaldo(inter.guild, "roles_sin_uso")
        candidatos = _roles_sin_miembros(inter.guild)
        if not candidatos:
            return await inter.followup.send(
                embed=crear_embed(
                    "info",
                    "Sin roles vacíos",
                    f"No hay roles sin miembros (o están protegidos).\n"
                    f"Respaldo: `{os.path.basename(path)}`",
                ),
                ephemeral=True,
            )
        lista = "\n".join(
            f"• **{r.name}** (`{r.id}`)" for r in candidatos[:40]
        )
        emb = crear_embed(
            "aviso",
            f"⚠️ {len(candidatos)} roles sin uso (0 miembros)",
            f"No se tocan roles del organigrama, separadores ni uniformes.\n"
            f"Respaldo: `{os.path.basename(path)}`\nConfirma en 2 minutos.",
        )
        emb.add_field(name="Lista", value=lista[:1000], inline=False)
        view = ConfirmarBorradoView(
            [r.id for r in candidatos],
            path,
            inter.user.id,
            "Eliminar roles sin uso",
        )
        await inter.followup.send(embed=emb, view=view, ephemeral=True)

    print("[limpiar_roles] OK — /limpiar_roles_viejos + /eliminar_roles_sin_uso")
