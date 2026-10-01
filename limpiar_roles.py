# -*- coding: utf-8 -*-
"""
limpiar_roles.py
- /limpiar_roles — eliges qué roles eliminar (menú desplegable)
- /eliminar_roles_sin_uso — atajo: solo roles con 0 miembros (también eliges)
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List, Optional, Set

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


def _es_protegido(role: discord.Role) -> bool:
    if role.is_default() or role.managed:
        return True
    prot = _nombres_protegidos()
    return role.name in prot or role.name.lower() in prot


def _roles_eliminables(guild: discord.Guild) -> List[discord.Role]:
    """Roles que el bot puede borrar (debajo del bot, no protegidos)."""
    top = guild.me.top_role if guild.me else None
    out: List[discord.Role] = []
    for role in guild.roles:
        if _es_protegido(role):
            continue
        if top and not (role < top):
            continue
        out.append(role)
    out.sort(key=lambda r: (-r.position, r.name))
    return out


def _roles_sin_miembros(guild: discord.Guild) -> List[discord.Role]:
    return [r for r in _roles_eliminables(guild) if len(r.members) == 0]


def _guardar_respaldo(guild: discord.Guild, role_ids: List[int]) -> str:
    os.makedirs(_DATA_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = os.path.join(_DATA_DIR, f"roles_delete_backup_{ts}.json")
    data = {
        "guild_id": guild.id,
        "selected": [],
    }
    for rid in role_ids:
        r = guild.get_role(rid)
        if r:
            data["selected"].append(
                {
                    "id": r.id,
                    "name": r.name,
                    "position": r.position,
                    "members": len(r.members),
                    "colour": str(r.colour),
                }
            )
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


class SelectorRolesView(ui.View):
    """Paso 1: elegir roles. Paso 2: confirmar."""

    def __init__(self, author_id: int, candidatos: List[discord.Role], modo: str):
        super().__init__(timeout=180)
        self.author_id = author_id
        self.modo = modo
        self.seleccionados: List[int] = []
        self.done = False

        # Discord RoleSelect máx. 25 opciones; filtramos a candidatos
        # RoleSelect nativo deja elegir cualquier rol; validamos al confirmar.
        self.ids_validos = {r.id for r in candidatos}

        options = []
        for r in candidatos[:25]:
            miembros = len(r.members)
            label = (r.name or "sin-nombre")[:100]
            desc = f"{miembros} miembro(s) · id {r.id}"[:100]
            options.append(
                discord.SelectOption(
                    label=label,
                    value=str(r.id),
                    description=desc,
                )
            )

        if not options:
            return

        select = ui.Select(
            placeholder="Elige los roles a eliminar (puedes varios)…",
            min_values=1,
            max_values=min(25, len(options)),
            options=options,
            custom_id="limpiar_roles_select",
        )
        select.callback = self._on_select
        self.add_item(select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ Solo quien ejecutó el comando.", ephemeral=True
            )
            return False
        return True

    async def _on_select(self, interaction: discord.Interaction):
        if self.done:
            return
        values = interaction.data.get("values", []) if interaction.data else []
        self.seleccionados = [int(v) for v in values]

        nombres = []
        for rid in self.seleccionados:
            r = interaction.guild.get_role(rid) if interaction.guild else None
            if r:
                nombres.append(f"• **{r.name}** ({len(r.members)} miembros)")

        emb = crear_embed(
            "aviso",
            f"⚠️ Confirmar eliminación ({len(self.seleccionados)})",
            "Se eliminarán **permanentemente** estos roles:\n\n"
            + ("\n".join(nombres) if nombres else "—")
            + "\n\nPulsa **Confirmar** o **Cancelar**.",
        )

        confirm = ConfirmarView(
            self.author_id, self.seleccionados, self.modo
        )
        await interaction.response.edit_message(embed=emb, view=confirm)


class ConfirmarView(ui.View):
    def __init__(self, author_id: int, role_ids: List[int], modo: str):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.role_ids = role_ids
        self.modo = modo
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

        if not interaction.guild:
            return await interaction.response.edit_message(
                content="❌ Sin servidor.", embed=None, view=self
            )

        path = _guardar_respaldo(interaction.guild, self.role_ids)
        await interaction.response.edit_message(
            content=f"🔄 Eliminando… (respaldo `{os.path.basename(path)}`)",
            embed=None,
            view=self,
        )

        borrados: List[str] = []
        errores: List[str] = []
        for rid in self.role_ids:
            role = interaction.guild.get_role(rid)
            if not role:
                continue
            if _es_protegido(role):
                errores.append(f"{role.name}: protegido")
                continue
            top = interaction.guild.me.top_role if interaction.guild.me else None
            if top and not (role < top):
                errores.append(f"{role.name}: por encima del bot")
                continue
            try:
                name = role.name
                await role.delete(reason=f"limpiar_roles ({self.modo})")
                borrados.append(name)
            except Exception as e:
                errores.append(f"{role.name}: {e}")

        emb = crear_embed(
            "exito" if borrados else "aviso",
            "Limpieza de roles",
            f"Eliminados: **{len(borrados)}** · Errores: **{len(errores)}**\n"
            f"Respaldo: `{os.path.basename(path)}`",
        )
        if borrados:
            emb.add_field(
                name="Eliminados",
                value="\n".join(f"• {n}" for n in borrados[:40]),
                inline=False,
            )
        if errores:
            emb.add_field(
                name="No eliminados",
                value="\n".join(errores[:20]),
                inline=False,
            )
        await interaction.followup.send(embed=emb, ephemeral=True)

    @ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: ui.Button):
        self.done = True
        for c in self.children:
            c.disabled = True
        await interaction.response.edit_message(
            content="❎ Cancelado. No se eliminó ningún rol.",
            embed=None,
            view=self,
        )


def registrar(bot: commands.Bot) -> None:
    for name in ("limpiar_roles", "limpiar_roles_viejos", "eliminar_roles_sin_uso"):
        try:
            bot.tree.remove_command(name)
        except Exception:
            pass

    @bot.tree.command(
        name="limpiar_roles",
        description="[Admin] Elige qué roles eliminar (menú desplegable + confirmación)",
    )
    async def limpiar_roles(inter: discord.Interaction):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _puede_admin(inter.user):
            return await inter.response.send_message(
                "❌ Solo Administrador o Fundador.", ephemeral=True
            )

        candidatos = _roles_eliminables(inter.guild)
        if not candidatos:
            return await inter.response.send_message(
                embed=crear_embed(
                    "info",
                    "Nada que eliminar",
                    "No hay roles eliminables (protegidos o por encima del bot).",
                ),
                ephemeral=True,
            )

        # Si hay más de 25, tomamos los de más abajo (menos críticos)
        lista = candidatos[:25]
        extra = ""
        if len(candidatos) > 25:
            extra = (
                f"\n\n⚠️ Hay **{len(candidatos)}** roles eliminables; "
                f"el menú muestra **25**. Ejecuta de nuevo para el resto."
            )

        emb = crear_embed(
            "aviso",
            "🗑️ Limpiar roles — elige cuáles",
            "Selecciona en el menú los roles que quieres **eliminar**.\n"
            "Luego confirma con el botón.\n\n"
            "**No se listan:** organigrama, separadores, uniformes, roles del bot/integraciones."
            + extra,
        )
        view = SelectorRolesView(inter.user.id, lista, "limpiar_roles")
        await inter.response.send_message(embed=emb, view=view, ephemeral=True)

    @bot.tree.command(
        name="eliminar_roles_sin_uso",
        description="[Admin] Elige entre roles con 0 miembros cuáles eliminar",
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

        candidatos = _roles_sin_miembros(inter.guild)
        if not candidatos:
            return await inter.response.send_message(
                embed=crear_embed(
                    "info",
                    "Sin roles vacíos",
                    "No hay roles con 0 miembros que se puedan eliminar.",
                ),
                ephemeral=True,
            )

        lista = candidatos[:25]
        emb = crear_embed(
            "aviso",
            "🗑️ Roles sin uso (0 miembros)",
            f"Hay **{len(candidatos)}** roles vacíos. Elige cuáles borrar en el menú.",
        )
        view = SelectorRolesView(inter.user.id, lista, "sin_uso")
        await inter.response.send_message(embed=emb, view=view, ephemeral=True)

    # Alias del nombre antiguo
    @bot.tree.command(
        name="limpiar_roles_viejos",
        description="[Admin] Igual que /limpiar_roles — elige qué roles borrar",
    )
    async def limpiar_roles_viejos(inter: discord.Interaction):
        # reutiliza la misma lógica
        await limpiar_roles.callback(inter)

    print("[limpiar_roles] OK — /limpiar_roles (selección) + /eliminar_roles_sin_uso")
