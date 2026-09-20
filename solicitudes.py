# -*- coding: utf-8 -*-
"""
solicitudes.py — Solicitudes con aprobación/negación por botones.
Cualquier solicitud puede elegir destinatario: Dir. Médico, RRHH, Disciplina, etc.
"""
from __future__ import annotations

from typing import Optional, Callable, Awaitable, Any, Dict
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


DESTINATARIOS_CHOICES = [
    ("🖥️ Director General", "DIRECTOR_GENERAL"),
    ("⚖️ Director de Disciplina", "DIRECTOR_DISCIPLINA"),
    ("📋 Director Administrativo", "DIRECTOR_ADMINISTRATIVO"),
    ("👥 Director de RRHH", "DIRECTOR_RRHH"),
    ("🩺 Director Médico", "DIRECTOR_MEDICO"),
    ("💉 Director de Enfermería", "DIRECTOR_ENFERMERIA"),
    ("💰 Director Financiero", "DIRECTOR_FINANCIERO"),
    ("📦 Director de Logística", "DIRECTOR_LOGISTICA"),
    ("🛡️ Director de Seguridad", "DIRECTOR_SEGURIDAD"),
    ("👑 Owner", "OWNER"),
    ("🤝 Co-Owner", "CO_OWNER"),
]

CANAL_POR_KEY = {
    "DIRECTOR_GENERAL": "citatorio_general",
    "DIRECTOR_DISCIPLINA": "citatorio_disciplina",
    "DIRECTOR_ADMINISTRATIVO": "citatorio_admin",
    "DIRECTOR_RRHH": "aprobaciones_rrhh",
    "DIRECTOR_MEDICO": "log_solicitudes",
    "DIRECTOR_ENFERMERIA": "log_solicitudes",
    "DIRECTOR_FINANCIERO": "log_finanzas",
    "DIRECTOR_LOGISTICA": "log_inventario",
    "DIRECTOR_SEGURIDAD": "log_solicitudes",
    "OWNER": "aprobaciones",
    "CO_OWNER": "aprobaciones",
}


def canal_para_key(key: str) -> str:
    return CANAL_POR_KEY.get(key, "log_solicitudes")


def nombre_destinatario(key: str) -> str:
    for label, k in DESTINATARIOS_CHOICES:
        if k == key:
            return label
    return config.nombre_key(key) if hasattr(config, "nombre_key") else key


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
        pending.pop(self.solicitud_id, None)
        _save_pending(pending)
        for child in self.children:
            child.disabled = True
        embed = interaction.message.embeds[0] if interaction.message.embeds else crear_embed("error", "Negado", "")
        embed.color = discord.Colour.red()
        embed.add_field(name="Estado", value=f"❌ **NEGADO** por {interaction.user.mention}", inline=False)
        await interaction.response.edit_message(embed=embed, view=self)


async def enviar_solicitud_con_aprobacion(
    interaction: discord.Interaction,
    key_aprobador: str,
    embed: discord.Embed,
    tipo: str,
    datos: Dict[str, Any],
    canal_key: Optional[str] = None,
    on_approve: Optional[Callable] = None,
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
    view = AprobacionView(key_aprobador=key_aprobador, solicitud_id=solicitud_id, on_approve=on_approve)
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
    keys_a_probar = [key_destino] + [k for k in config.ESCALADA_SOLICITUDES if k != key_destino]
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


class CartaSolicitudModal(discord.ui.Modal, title="Carta de solicitud"):
    asunto = discord.ui.TextInput(label="Asunto", max_length=100)
    contenido = discord.ui.TextInput(label="Contenido", style=discord.TextStyle.paragraph, max_length=1500)

    def __init__(self, departamento_slug: str, departamento_nombre: str, asunto_sugerido: str = ""):
        super().__init__()
        self.departamento_slug = departamento_slug
        self.departamento_nombre = departamento_nombre
        if asunto_sugerido:
            self.asunto.default = asunto_sugerido[:100]

    async def on_submit(self, interaction: discord.Interaction):
        if self.departamento_slug and self.departamento_slug in config.DEPARTAMENTOS:
            dest = config.DEPARTAMENTOS[self.departamento_slug]["director_key"]
        else:
            dest = config.KEY_SOLICITUD_GENERAL
        embed = crear_embed("info", f"✉️ Solicitud: {self.asunto}", str(self.contenido), autor=interaction.user)
        embed.add_field(name="Destino", value=self.departamento_nombre)
        await enviar_solicitud(interaction, dest, embed, "log_solicitudes")
        await interaction.response.send_message("✅ Solicitud enviada.", ephemeral=True)


class SolicitudDescargoModal(discord.ui.Modal, title="Solicitud de descargo"):
    motivo = discord.ui.TextInput(label="Motivo del descargo", style=discord.TextStyle.paragraph, max_length=1000)

    def __init__(self, usuario: discord.Member, cargo_actual: str, cargo_propuesto: str):
        super().__init__()
        self.usuario = usuario
        self.cargo_actual = cargo_actual
        self.cargo_propuesto = cargo_propuesto

    async def on_submit(self, interaction: discord.Interaction):
        embed = crear_embed("aviso", "📝 Solicitud de descargo", str(self.motivo), autor=interaction.user)
        embed.add_field(name="Afectado", value=self.usuario.mention)
        embed.add_field(name="Cargo actual", value=self.cargo_actual)
        embed.add_field(name="Cargo propuesto", value=self.cargo_propuesto)
        await enviar_solicitud(interaction, config.RRHH_KEY, embed, "log_solicitudes")
        await interaction.response.send_message("✅ Solicitud de descargo enviada a RRHH.", ephemeral=True)


class SolicitudPermisoModal(discord.ui.Modal, title="Solicitud de permiso"):
    desde = discord.ui.TextInput(label="Desde (fecha)", max_length=40)
    hasta = discord.ui.TextInput(label="Hasta (fecha)", max_length=40)
    motivo = discord.ui.TextInput(label="Motivo", style=discord.TextStyle.paragraph, max_length=500)

    def __init__(self, departamento_slug: str, departamento_nombre: str):
        super().__init__()
        self.departamento_slug = departamento_slug
        self.departamento_nombre = departamento_nombre

    async def on_submit(self, interaction: discord.Interaction):
        embed = crear_embed("aviso", "🗓️ Solicitud de permiso", str(self.motivo), autor=interaction.user)
        embed.add_field(name="Desde", value=str(self.desde))
        embed.add_field(name="Hasta", value=str(self.hasta))
        embed.add_field(name="Departamento", value=self.departamento_nombre)
        if self.departamento_slug and self.departamento_slug in config.DEPARTAMENTOS:
            dest = config.DEPARTAMENTOS[self.departamento_slug]["director_key"]
        else:
            dest = config.RRHH_KEY
        await enviar_solicitud(interaction, dest, embed, "log_solicitudes")
        await interaction.response.send_message("✅ Solicitud de permiso enviada.", ephemeral=True)


class CitatorioModal(discord.ui.Modal):
    def __init__(self, direccion: str, key_aprobador: str, canal_key: str, titulo: str):
        super().__init__(title=titulo[:45])
        self.direccion = direccion
        self.key_aprobador = key_aprobador
        self.canal_key = canal_key
        self.usuario_id = discord.ui.TextInput(label="ID o mención del citado", placeholder="Ej: 123456789 o @usuario", max_length=100)
        self.motivo = discord.ui.TextInput(label="Motivo del citatorio", style=discord.TextStyle.paragraph, max_length=1000)
        self.fecha_hora = discord.ui.TextInput(label="Fecha y hora de la cita", placeholder="Ej: 20/09/2026 18:00", max_length=80)
        self.lugar = discord.ui.TextInput(label="Lugar / canal", placeholder="Ej: Oficina de Disciplina", max_length=100, required=False)
        self.observaciones = discord.ui.TextInput(label="Observaciones adicionales", style=discord.TextStyle.paragraph, max_length=500, required=False)
        self.add_item(self.usuario_id)
        self.add_item(self.motivo)
        self.add_item(self.fecha_hora)
        self.add_item(self.lugar)
        self.add_item(self.observaciones)

    async def on_submit(self, interaction: discord.Interaction):
        embed = crear_embed("aviso", f"📢 Citatorio — {self.direccion}", str(self.motivo), autor=interaction.user)
        embed.add_field(name="Citado", value=str(self.usuario_id), inline=True)
        embed.add_field(name="Fecha/hora", value=str(self.fecha_hora), inline=True)
        if self.lugar.value:
            embed.add_field(name="Lugar", value=str(self.lugar), inline=True)
        if self.observaciones.value:
            embed.add_field(name="Observaciones", value=str(self.observaciones), inline=False)
        embed.add_field(name="Estado", value="⏳ Pendiente de autorización", inline=False)
        await enviar_solicitud_con_aprobacion(
            interaction,
            key_aprobador=self.key_aprobador,
            embed=embed,
            tipo=f"citatorio_{self.direccion.lower().replace(' ', '_')}",
            datos={"citado": str(self.usuario_id), "motivo": str(self.motivo), "fecha": str(self.fecha_hora), "lugar": str(self.lugar) if self.lugar.value else ""},
            canal_key=self.canal_key,
        )
        await interaction.response.send_message(f"✅ Citatorio enviado a **{self.direccion}** para aprobación.", ephemeral=True)


class ReporteProcedimientoModal(discord.ui.Modal, title="Reporte de procedimiento"):
    afectado = discord.ui.TextInput(label="Persona afectada (nombre/mención)", max_length=100)
    motivo = discord.ui.TextInput(label="Motivo", style=discord.TextStyle.paragraph, max_length=800)
    sancion = discord.ui.TextInput(label="Sanción / medida aplicada", style=discord.TextStyle.paragraph, max_length=500)
    procedimiento = discord.ui.TextInput(label="Qué ocurrió y cómo se procedió", style=discord.TextStyle.paragraph, max_length=1500)
    observaciones = discord.ui.TextInput(label="Observaciones finales", style=discord.TextStyle.paragraph, max_length=500, required=False)

    def __init__(self, direccion: str):
        super().__init__()
        self.direccion = direccion

    async def on_submit(self, interaction: discord.Interaction):
        embed = crear_embed("info", f"📋 Reporte de procedimiento — {self.direccion}", str(self.procedimiento), autor=interaction.user)
        embed.add_field(name="Afectado", value=str(self.afectado), inline=True)
        embed.add_field(name="Encargado", value=interaction.user.mention, inline=True)
        embed.add_field(name="Dirección", value=self.direccion, inline=True)
        embed.add_field(name="Motivo", value=str(self.motivo), inline=False)
        embed.add_field(name="Sanción / medida", value=str(self.sancion), inline=False)
        if self.observaciones.value:
            embed.add_field(name="Observaciones", value=str(self.observaciones), inline=False)
        guild = interaction.guild
        canal = None
        cid = config.CANALES.get("log_procedimientos") or config.CANALES.get("log_personal")
        if cid and guild:
            canal = guild.get_channel(cid)
        if canal:
            await canal.send(embed=embed)
        else:
            await interaction.channel.send(embed=embed)
        await interaction.response.send_message("✅ Reporte de procedimiento publicado.", ephemeral=True)
