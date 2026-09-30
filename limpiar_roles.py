# -*- coding: utf-8 -*-
"""limpiar_roles.py — /limpiar_roles_viejos con respaldo JSON."""
from __future__ import annotations
import json, os
from datetime import datetime, timezone
from typing import List, Set
import discord
from discord import ui
from discord.ext import commands
import permisos
import roles_config
from estilos import crear_embed

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def _nombres_protegidos() -> Set[str]:
    names: Set[str] = set()
    for _, (nombre, _) in roles_config.KEYS_NOMBRES.items():
        names.add(nombre); names.add(nombre.lower())
    for _, nombre, _ in roles_config.SEPARADORES_ROLES:
        names.add(nombre); names.add(nombre.lower())
    for _, (nombre, _) in roles_config.ROLES_OTORGADOS_CONSERVAR.items():
        names.add(nombre); names.add(nombre.lower())
    for n in ["Gerente Developer", "Fundador y Owner", "Owner", "Co-Owner", "Suspendido", "Inactividad Justificada"]:
        names.add(n); names.add(n.lower())
    return names

def _roles_a_eliminar(guild: discord.Guild) -> List[discord.Role]:
    prot = _nombres_protegidos()
    top = guild.me.top_role if guild.me else None
    out = []
    for role in guild.roles:
        if role.is_default() or role.managed:
            continue
        if role.name in prot or role.name.lower() in prot:
            continue
        if top and role >= top:
            continue
        out.append(role)
    out.sort(key=lambda r: r.position)
    return out

def _guardar_respaldo(guild: discord.Guild) -> str:
    os.makedirs(_DATA_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = os.path.join(_DATA_DIR, f"roles_backup_{ts}.json")
    data = {"guild_id": guild.id, "roles": [{"id": r.id, "name": r.name, "position": r.position} for r in guild.roles]}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path

class ConfirmarBorradoView(ui.View):
    def __init__(self, role_ids, backup_path, author_id):
        super().__init__(timeout=120)
        self.role_ids = role_ids
        self.backup_path = backup_path
        self.author_id = author_id
        self.done = False

    async def interaction_check(self, interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Solo quien ejecutó el comando.", ephemeral=True)
            return False
        return True

    @ui.button(label="✅ Confirmar borrado", style=discord.ButtonStyle.danger)
    async def confirmar(self, interaction: discord.Interaction, button: ui.Button):
        if self.done: return
        self.done = True
        for c in self.children: c.disabled = True
        await interaction.response.edit_message(view=self)
        borrados, errores = [], []
        for rid in self.role_ids:
            role = interaction.guild.get_role(rid) if interaction.guild else None
            if not role: continue
            try:
                await role.delete(reason="Limpieza organigrama")
                borrados.append(role.name)
            except Exception as e:
                errores.append(f"{role.name}: {e}")
        emb = crear_embed("exito" if borrados else "aviso", "Limpieza completada", f"Eliminados: {len(borrados)} · Errores: {len(errores)}")
        if borrados:
            emb.add_field(name="Eliminados", value="\n".join(f"• {n}" for n in borrados[:30]), inline=False)
        await interaction.followup.send(embed=emb)

    @ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: ui.Button):
        self.done = True
        for c in self.children: c.disabled = True
        await interaction.response.edit_message(content="❎ Cancelado.", embed=None, view=self)

def registrar(bot: commands.Bot) -> None:
    @bot.tree.command(name="limpiar_roles_viejos", description="[Fundador] Respaldo + borra roles fuera del organigrama")
    @permisos.require_key("FUNDADOR_OWNER", "OWNER", "CO_OWNER")
    async def limpiar_roles_viejos(inter: discord.Interaction):
        if not inter.guild:
            return await inter.response.send_message("❌ Solo en servidor.", ephemeral=True)
        await inter.response.defer(ephemeral=True)
        path = _guardar_respaldo(inter.guild)
        candidatos = _roles_a_eliminar(inter.guild)
        if not candidatos:
            return await inter.followup.send(embed=crear_embed("info", "Sin roles viejos", f"Respaldo: `{os.path.basename(path)}`"), ephemeral=True)
        lista = "\n".join(f"• **{r.name}**" for r in candidatos[:40])
        emb = crear_embed("aviso", f"⚠️ {len(candidatos)} roles a eliminar", f"Respaldo: `{os.path.basename(path)}`\nConfirma en 2 min.")
        emb.add_field(name="Lista", value=lista[:1000], inline=False)
        await inter.followup.send(embed=emb, view=ConfirmarBorradoView([r.id for r in candidatos], path, inter.user.id), ephemeral=True)
    print("[limpiar_roles] OK")
