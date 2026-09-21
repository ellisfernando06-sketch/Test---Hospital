# -*- coding: utf-8 -*-
"""
solicitudes.py — Solicitudes con aprobación/negación por botones.
"""
from __future__ import annotations

from typing import Optional, Callable, Any, Dict
import json
import os
from datetime import datetime, timezone

import discord

import config
import permisos
import roles_store
from estilos import crear_embed

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PENDING_PATH = os.path.join(_DATA_DIR, "solicitudes_pendientes.json")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_pending() -> dict:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_PENDING_PATH):
        return {}
    try:
        with open(_PENDING_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_pending(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_PENDING_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


RUTAS_POR_TIPO = {
    "sancion_administrativa": {"key": "DIRECTOR_ADMINISTRATIVO", "canal": "citatorio_admin", "titulo": "📋 Sanción administrativa"},
    "sancion_disciplinaria": {"key": "DIRECTOR_DISCIPLINA", "canal": "citatorio_disciplina", "titulo": "⚖️ Sanción disciplinaria"},
    "sancion_interna": {"key": "DIRECTOR_RRHH", "canal": "aprobaciones_rrhh", "titulo": "⚠️ Sanción interna (RRHH)"},
    "investigacion_interna": {"key": "DIRECTOR_RRHH", "canal": "aprobaciones_rrhh", "titulo": "🔎 Investigación interna"},
    "investigacion_disciplinaria": {"key": "DIRECTOR_DISCIPLINA", "canal": "citatorio_disciplina", "titulo": "🔎 Investigación disciplinaria"},
    "investigacion_administrativa": {"key": "DIRECTOR_ADMINISTRATIVO", "canal": "citatorio_admin", "titulo": "🔎 Investigación administrativa"},
    "citatorio_general": {"key": "DIRECTOR_GENERAL", "canal": "citatorio_general", "titulo": "📢 Citatorio — Dirección General"},
    "citatorio_disciplina": {"key": "DIRECTOR_DISCIPLINA", "canal": "citatorio_disciplina", "titulo": "📢 Citatorio — Disciplina"},
    "citatorio_admin": {"key": "DIRECTOR_ADMINISTRATIVO", "canal": "citatorio_admin", "titulo": "📢 Citatorio — Administrativo"},
    "despido": {"key": "DIRECTOR_RRHH", "canal": "aprobaciones_rrhh", "titulo": "🚫 Despido"},
    "suspension": {"key": "DIRECTOR_RRHH", "canal": "aprobaciones_rrhh", "titulo": "⛔ Suspensión"},
    "degrado": {"key": "DIRECTOR_RRHH", "canal": "aprobaciones_rrhh", "titulo": "⬇️ Degradado"},
}


def resolver_ruta(tipo: str) -> dict:
    t = (tipo or "").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "sancion_admin": "sancion_administrativa",
        "administrativa": "sancion_administrativa",
        "disciplinaria": "sancion_disciplinaria",
        "sancion_disciplina": "sancion_disciplinaria",
        "investigacion": "investigacion_interna",
        "investigación_interna": "investigacion_interna",
        "investigacion_rrhh": "investigacion_interna",
        "interna": "sancion_interna",
    }
    t = aliases.get(t, t)
    if t in RUTAS_POR_TIPO:
        return RUTAS_POR_TIPO[t]
    if "admin" in t:
        return RUTAS_POR_TIPO["sancion_administrativa"]
    if "disciplin" in t:
        return RUTAS_POR_TIPO["sancion_disciplinaria"]
    if "investig" in t:
        return RUTAS_POR_TIPO["investigacion_interna"]
    return RUTAS_POR_TIPO["sancion_interna"]


class AprobacionView(discord.ui.View):
    def __init__(self, key_aprobador: str, solicitud_id: str, on_approve: Optional[Callable] = None, on_deny: Optional[Callable] = None, timeout: float = None):
        super().__init__(timeout=timeout)
        self.key_aprobador = key_aprobador
        self.solicitud_id = solicitud_id
        self._on_approve = on_approve
        self._on_deny = on_deny

    async def _puede(self, interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            return False
        if permisos.member_tiene_key(interaction.user, "OWNER"):
            return True
        if permisos.member_tiene_key(interaction.user, "CO_OWNER"):
            return True
        return permisos.member_tiene_key(interaction.user, self.key_aprobador)

    @discord.ui.button(label="✅ Aprobar", style=discord.ButtonStyle.success, custom_id="solicitud_aprobar")
    async def aprobar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._puede(interaction):
            await interaction.response.send_message(
                f"❌ Solo **{config.nombre_key(self.key_aprobador)}** (o superior) puede aprobar.", ephemeral=True)
            return
        pending = _load_pending()
        info = pending.pop(self.solicitud_id, None)
        _save_pending(pending)
        for child in self.children:
            child.disabled = True
        embed = interaction.message.embeds[0] if interaction.message.embeds else crear_embed("exito", "Aprobado", "")
        embed.color = discord.Colour.green()
        embed.add_field(name="Estado", value=f"✅ **APROBADO** por {interaction.user.mention}", inline=False)
        await interaction.response.edit_message(embed=embed, view=self)
        if self._on_approve and info:
            try:
                await self._on_approve(interaction, info)
            except Exception as e:
                await interaction.followup.send(f"⚠️ Aprobado, pero error al ejecutar: {e}", ephemeral=True)

    @discord.ui.button(label="❌ Negar", style=discord.ButtonStyle.danger, custom_id="solicitud_negar")
    async def negar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._puede(interaction):
            await interaction.response.send_message(
                f"❌ Solo **{config.nombre_key(self.key_aprobador)}** (o superior) puede negar.", ephemeral=True)
            return
        pending = _load_pending()
        info = pending.pop(self.solicitud_id, None)
        _save_pending(pending)
        for child in self.children:
            child.disabled = True
        embed = interaction.message.embeds[0] if interaction.message.embeds else crear_embed("error", "Negado", "")
        embed.color = discord.Colour.red()
        embed.add_field(name="Estado", value=f"❌ **NEGADO** por {interaction.user.mention}", inline=False)
        await interaction.response.edit_message(embed=embed, view=self)
        if self._on_deny and info:
            try:
                await self._on_deny(interaction, info)
            except Exception as e:
                await interaction.followup.send(f"⚠️ Negado, pero error al ejecutar callback: {e}", ephemeral=True)


async def enviar_solicitud_con_aprobacion(
    interaction: discord.Interaction,
    key_aprobador: str,
    embed: discord.Embed,
    tipo: str,
    datos: Dict[str, Any],
    canal_key: Optional[str] = None,
    on_approve: Optional[Callable] = None,
    on_deny: Optional[Callable] = None,
) -> None:
    guild = interaction.guild
    if not guild:
        return
    solicitud_id = f"{tipo}_{interaction.user.id}_{int(datetime.now(timezone.utc).timestamp())}"
    datos_guardar = {
        "tipo": tipo,
        "autor_id": interaction.user.id,
        "fecha": _now(),
        "datos": {k: (str(v.id) if isinstance(v, discord.Member) else str(v)) for k, v in datos.items()},
    }
    pending = _load_pending()
    pending[solicitud_id] = datos_guardar
    _save_pending(pending)
    view = AprobacionView(key_aprobador=key_aprobador, solicitud_id=solicitud_id, on_approve=on_approve, on_deny=on_deny)
    canal = None
    if canal_key:
        cid = config.CANALES.get(canal_key)
        if cid:
            canal = guild.get_channel(cid)
    if not canal:
        cid = config.CANALES.get("aprobaciones_rrhh") or config.CANALES.get("aprobaciones") or config.CANALES.get("log_solicitudes")
        if cid:
            canal = guild.get_channel(cid)
    mention = ""
    rid = roles_store.obtener_id_key(key_aprobador)
    if rid:
        rol = guild.get_role(rid)
        if rol:
            mention = rol.mention
    if canal:
        try:
            await canal.send(content=mention or None, embed=embed, view=view)
        except discord.Forbidden:
            await interaction.channel.send(content=mention or None, embed=embed, view=view)
    else:
        await interaction.channel.send(content=mention or None, embed=embed, view=view)


async def enviar_solicitud(
    interaction: discord.Interaction,
    key_destino: str,
    embed: discord.Embed,
    canal_log: Optional[str] = None,
) -> None:
    guild = interaction.guild
    if not guild:
        return
    if canal_log:
        canal_id = config.CANALES.get(canal_log)
        if canal_id:
            canal = guild.get_channel(canal_id)
            if canal:
                try:
                    await canal.send(embed=embed)
                except discord.Forbidden:
                    pass
    keys_a_probar = [key_destino] + [k for k in getattr(config, "ESCALADA_SOLICITUDES", []) if k != key_destino]
    mencionado = False
    for key in keys_a_probar:
        rid = roles_store.obtener_id_key(key)
        if not rid:
            continue
        rol = guild.get_role(rid)
        if not rol:
            continue
        miembros = [m for m in guild.members if rol in m.roles]
        if miembros:
            for m in miembros:
                try:
                    await m.send(f"📬 Nueva solicitud dirigida a **{config.nombre_key(key)}**:", embed=embed)
                    mencionado = True
                    break
                except discord.Forbidden:
                    continue
            if not mencionado:
                try:
                    await interaction.channel.send(content=f"{rol.mention} — nueva solicitud", embed=embed)
                    mencionado = True
                except Exception:
                    pass
            break
