# -*- coding: utf-8 -*-
"""
limpiar_roles.py
================
/limpiar_roles_viejos — solo Fundador y Owner / Co-Owner

1. Guarda respaldo JSON de TODOS los roles del servidor.
2. Lista roles que NO pertenecen al organigrama oficial ni a roles
   conservados (docencia/seguridad/uniformes/separadores).
3. Pide confirmación con botón antes de borrar nada.
4. Elimina solo los listados (nunca @everyone, managed, ni roles del bot).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List, Optional, Set

import discord
from discord import app_commands, ui
from discord.ext import commands

import permisos
import roles_config
from estilos import crear_embed

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def _nombres_protegidos() -> Set[str]:
    """Nombres exactos que NUNCA se borran."""
    names: Set[str] = set()
    for key, (nombre, _) in roles_config.KEYS_NOMBRES.items():
        names.add(nombre)
        names.add(nombre.lower())
    for _, nombre, _ in roles_config.SEPARADORES_ROLES:
        names.add(nombre)
        names.add(nombre.lower())
    for _, (nombre, _) in roles_config.ROLES_OTORGADOS_CONSERVAR.items():
        names.add(nombre)
        names.add(nombre.lower())
    # Alias / nombres históricos que se migran, no se borran
    extras = [
        "👑 Fundador y Owner",
        "🛠️ Gerente Developer",
        "Gerente Developer",
        "Fundador y Owner",
        "👑 Owner",
        "Owner",
        "🤝 Co-Owner",
        "Co-Owner",
        "⛔ Suspendido",
        "Suspendido",
        "⏸️ Inactividad Justificada",
        "Inactividad Justificada",
    ]
    for n in extras:
        names.add(n)
        names.add(n.lower())
    return names


def _es_protegido(role: discord.Role, protegidos: Set[str]) -> bool:
    if role.is_default() or role.managed:
        return True
    if role.name in protegidos or role.name.lower() in protegidos:
        return True
    # Separadores del organigrama (contienen 『 )
    if "『" in (role.name or "") and "』" in (role.name or ""):
        # Solo proteger si es uno de los oficiales; otros separadores viejos se pueden borrar
        for _, nombre, _ in roles_config.SEPARADORES_ROLES:
            if role.name == nombre:
                return True
    return False


def _roles_a_eliminar(guild: discord.Guild) -> List[discord.Role]:
    protegidos = _nombres_protegidos()
    me = guild.me
    top = me.top_role if me else None
    out: List[discord.Role] = []
    for role in guild.roles:
        if _es_protegido(role, protegidos):
            continue
        # No se puede borrar roles >= al del bot
        if top and role >= top:
            continue
        out.append(role)
    # Orden: de abajo hacia arriba (más seguro al borrar)
    out.sort(key=lambda r: r.position)
    return out


def _respaldo_path() -> str:
    os.makedirs(_DATA_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return os.path.join(_DATA_DIR, f"roles_backup_{ts}.json")


def _guardar_respaldo(guild: discord.Guild) -> str:
    data = {
        "guild_id": guild.id,
        "guild_name": guild.name,
        "backed_up_at": datetime.now(timezone.utc).isoformat(),
        "roles": [
            {
                "id": r.id,
                "name": r.name,
                "position": r.position,
                "color": str(r.colour),
                "permissions": r.permissions.value,
                "hoist": r.hoist,
                "mentionable": r.mentionable,
                "managed": r.managed,
                "member_count": len(r.members),
            }
            for r in sorted(guild.roles, key=lambda x: x.position, reverse=True)
        ],
    }
    path = _respaldo_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


class ConfirmarBorradoView(ui.View):
    def __init__(self, role_ids: List[int], backup_path: str, author_id: int):
        super().__init__(timeout=120)
        self.role_ids = role_ids
        self.backup_path = backup_path
        self.author_id = author_id
        self.done = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ Solo quien ejecutó el comando puede confirmar.", ephemeral=True
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

        if not interaction.guild:
            await interaction.followup.send("❌ Solo en servidor.", ephemeral=True)
            return

        borrados = []
        errores = []
        for rid in self.role_ids:
            role = interaction.guild.get_role(rid)
            if not role:
                continue
            name = role.name
            try:
                await role.delete(reason=f"Limpieza organigrama — respaldo {self.backup_path}")
                borrados.append(name)
            except Exception as e:
                errores.append(f"{name}: {e}")

        emb = crear_embed(
            "exito" if borrados else "aviso",
            "Limpieza de roles completada",
            (
                f"**Respaldo:** `{os.path.basename(self.backup_path)}`\n"
                f"**Eliminados:** {len(borrados)}\n"
                f"**Errores:** {len(errores)}"
            ),
            autor=interaction.user,
        )
        if borrados:
            emb.add_field(
                name="Roles eliminados",
                value="\n".join(f"• {n}" for n in borrados[:40])
                + ("\n…" if len(borrados) > 40 else ""),
                inline=False,
            )
        if errores:
            emb.add_field(
                name="No se pudieron borrar",
                value="\n".join(errores[:15]),
                inline=False,
            )
        await interaction.followup.send(embed=emb)

    @ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: ui.Button):
        self.done = True
        for c in self.children:
            c.disabled = True
        await interaction.response.edit_message(
            content="❎ Borrado cancelado. Respaldo conservado; no se eliminó ningún rol.",
            embed=None,
            view=self,
        )


def registrar(bot: commands.Bot) -> None:
    @bot.tree.command(
        name="limpiar_roles_viejos",
        description="[Fundador] Respaldo + borra roles que no están en el organigrama",
    )
    @permisos.require_key("FUNDADOR_OWNER", "OWNER", "CO_OWNER")
    async def limpiar_roles_viejos(inter: discord.Interaction):
        if not inter.guild:
            return await inter.response.send_message("❌ Solo en servidor.", ephemeral=True)

        await inter.response.defer(ephemeral=True)

        path = _guardar_respaldo(inter.guild)
        candidatos = _roles_a_eliminar(inter.guild)

        if not candidatos:
            emb = crear_embed(
                "info",
                "Sin roles viejos",
                f"No hay roles fuera del organigrama.\n**Respaldo guardado:** `{os.path.basename(path)}`",
                autor=inter.user,
            )
            return await inter.followup.send(embed=emb, ephemeral=True)

        lista = "\n".join(
            f"• **{r.name}** (`{r.id}`) — {len(r.members)} miembros"
            for r in candidatos[:50]
        )
        if len(candidatos) > 50:
            lista += f"\n… y {len(candidatos) - 50} más"

        emb = crear_embed(
            "aviso",
            f"⚠️ {len(candidatos)} roles a eliminar",
            (
                f"Se guardó respaldo en `{os.path.basename(path)}`.\n\n"
                f"**Se eliminarán** los roles que no están en el organigrama oficial.\n"
                f"**NO se tocan:** organigrama, separadores oficiales, docencia/seguridad/uniformes, "
                f"@everyone, roles managed.\n\n"
                f"Confirma con el botón en **2 minutos**."
            ),
            autor=inter.user,
        )
        emb.add_field(name="Lista", value=lista[:1000], inline=False)

        view = ConfirmarBorradoView(
            [r.id for r in candidatos], path, inter.user.id
        )
        await inter.followup.send(embed=emb, view=view, ephemeral=True)

    print("[limpiar_roles] OK — /limpiar_roles_viejos")
