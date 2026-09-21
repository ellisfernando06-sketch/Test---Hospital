# -*- coding: utf-8 -*-
"""
centro_solicitudes.py — Sistema General de Solicitudes

Diseño institucional: panel principal, menú, formularios, tickets,
estados, prioridad, logs y almacenamiento persistente.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import discord
from discord import ui, app_commands
from discord.ext import commands

import config
import permisos
import roles_store
from estilos import crear_embed

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "centro_solicitudes.json")

# ---------------------------------------------------------------------------
# Constantes de diseño / estados / categorías
# ---------------------------------------------------------------------------

ESTADOS = {
    "en_revision": ("🟡 En revisión", 0xF1C40F),
    "en_investigacion": ("🔵 En investigación", 0x3498DB),
    "info_requerida": ("🟠 Información requerida", 0xE67E22),
    "en_espera": ("🟣 En espera", 0x9B59B6),
    "resuelta": ("🟢 Resuelta", 0x2ECC71),
    "rechazada": ("🔴 Rechazada", 0xE74C3C),
    "cerrada": ("⚫ Cerrada", 0x95A5A6),
}

PRIORIDADES = {
    "normal": ("🟢 Normal", 0x2ECC71),
    "media": ("🟡 Media", 0xF1C40F),
    "alta": ("🟠 Alta", 0xE67E22),
    "urgente": ("🔴 Urgente", 0xE74C3C),
}

CATEGORIAS = {
    "sancion": {
        "emoji": "🛡️",
        "nombre": "Sanciones",
        "descripcion": "Solicitudes relacionadas con sanciones, infracciones y medidas administrativas.",
        "menu_desc": "Solicitar revisión, aplicación o información relacionada con una sanción.",
        "prefijo": "sancion",
        "color": 0x8E44AD,
    },
    "apelacion": {
        "emoji": "⚖️",
        "nombre": "Apelaciones",
        "descripcion": "Solicita la revisión de una sanción o decisión administrativa.",
        "menu_desc": "Apelar una sanción o decisión administrativa.",
        "prefijo": "apelacion",
        "color": 0x2980B9,
    },
    "investigacion": {
        "emoji": "🔎",
        "nombre": "Investigaciones",
        "descripcion": "Solicita una investigación sobre un usuario, situación o incidente.",
        "menu_desc": "Solicitar una investigación.",
        "prefijo": "investigacion",
        "color": 0x16A085,
    },
    "reporte": {
        "emoji": "🚨",
        "nombre": "Reportes",
        "descripcion": "Reporta comportamientos, incumplimientos o situaciones que requieran intervención.",
        "menu_desc": "Reportar a un usuario o situación.",
        "prefijo": "reporte",
        "color": 0xC0392B,
    },
    "general": {
        "emoji": "📩",
        "nombre": "Solicitud General",
        "descripcion": "Utiliza esta opción cuando tu solicitud no corresponda a ninguna de las categorías anteriores.",
        "menu_desc": "Realizar una solicitud que no pertenece a otra categoría.",
        "prefijo": "solicitud",
        "color": 0x3498DB,
    },
    "consulta": {
        "emoji": "📋",
        "nombre": "Consultas",
        "descripcion": "Para realizar consultas o solicitar información al equipo correspondiente.",
        "menu_desc": "Realizar una consulta administrativa.",
        "prefijo": "consulta",
        "color": 0x1ABC9C,
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fecha_legible(iso: Optional[str] = None) -> str:
    if not iso:
        iso = _now()
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(iso)[:16]


def _load() -> dict:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_PATH):
        return {"contador": 0, "solicitudes": {}}
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("contador", 0)
        data.setdefault("solicitudes", {})
        return data
    except Exception:
        return {"contador": 0, "solicitudes": {}}


def _save(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _siguiente_numero() -> int:
    data = _load()
    data["contador"] = int(data.get("contador", 0)) + 1
    _save(data)
    return data["contador"]


def guardar_solicitud(reg: dict) -> None:
    data = _load()
    data["solicitudes"][str(reg["id"])] = reg
    _save(data)


def obtener_solicitud(sid: int) -> Optional[dict]:
    data = _load()
    return data["solicitudes"].get(str(sid))


def actualizar_solicitud(sid: int, **kwargs) -> Optional[dict]:
    data = _load()
    key = str(sid)
    if key not in data["solicitudes"]:
        return None
    data["solicitudes"][key].update(kwargs)
    data["solicitudes"][key]["fecha_actualizacion"] = _now()
    _save(data)
    return data["solicitudes"][key]


def _rol_staff(guild: discord.Guild) -> Optional[discord.Role]:
    nombres = ["🖥️ Staff del Servidor", "Staff del Servidor", "Staff", "STAFF"]
    for n in nombres:
        r = discord.utils.get(guild.roles, name=n)
        if r:
            return r
    rid = roles_store.obtener_id_key("STAFF_SERVIDOR")
    if rid:
        return guild.get_role(rid)
    return None


def _categoria_canal(guild: discord.Guild) -> Optional[discord.CategoryChannel]:
    cid = getattr(config, "TICKET_CATEGORIA_ID", None)
    if cid:
        ch = guild.get_channel(cid)
        if isinstance(ch, discord.CategoryChannel):
            return ch
    return None


async def enviar_log_solicitud(bot: discord.Client, embed: discord.Embed) -> None:
    canal_id = config.CANALES.get("log_solicitudes") or config.CANALES.get("log_general")
    if not canal_id:
        return
    canal = bot.get_channel(canal_id)
    if canal:
        try:
            await canal.send(embed=embed)
        except discord.Forbidden:
            pass


# ---------------------------------------------------------------------------
# Embeds de diseño
# ---------------------------------------------------------------------------

def embed_panel_principal() -> discord.Embed:
    desc = (
        "Bienvenido al **Centro de Solicitudes**.\n"
        "Desde este apartado podrás realizar diferentes tipos de solicitudes "
        "para que el equipo administrativo pueda revisarlas y darles seguimiento.\n\n"
        "Selecciona a continuación el tipo de solicitud que deseas realizar."
    )
    embed = discord.Embed(
        title="🏛️ CENTRO DE SOLICITUDES",
        description=desc,
        color=0x2C3E50,
        timestamp=discord.utils.utcnow(),
    )
    for key, cat in CATEGORIAS.items():
        embed.add_field(
            name=f"{cat['emoji']} {cat['nombre']}",
            value=cat["descripcion"],
            inline=False,
        )
    embed.set_footer(text=f"{config.NOMBRE_HOSPITAL} · Sistema de Solicitudes")
    if config.LOGO_URL:
        embed.set_thumbnail(url=config.LOGO_URL)
    return embed


def embed_ticket(reg: dict, guild: Optional[discord.Guild] = None) -> discord.Embed:
    cat = CATEGORIAS.get(reg.get("categoria", "general"), CATEGORIAS["general"])
    estado_key = reg.get("estado", "en_revision")
    estado_txt, color = ESTADOS.get(estado_key, ESTADOS["en_revision"])
    prio_key = reg.get("prioridad", "normal")
    prio_txt, _ = PRIORIDADES.get(prio_key, PRIORIDADES["normal"])

    num = reg.get("numero", reg.get("id", 0))
    embed = discord.Embed(
        title=f"📋 SOLICITUD #{num:04d}",
        description=(
            "La solicitud ha sido creada correctamente.\n"
            "Un miembro del equipo correspondiente revisará el caso.\n\n"
            "Por favor, proporciona toda la información adicional que sea solicitada "
            "y evita enviar mensajes innecesarios."
        ),
        color=color,
        timestamp=discord.utils.utcnow(),
    )

    solicitante = f"<@{reg.get('usuario_id')}>"
    embed.add_field(name="👤 Solicitante", value=solicitante, inline=True)
    embed.add_field(name="📂 Categoría", value=f"{cat['emoji']} {cat['nombre']}", inline=True)
    embed.add_field(name="🆔 Número", value=f"#{num:04d}", inline=True)
    embed.add_field(name="Estado", value=estado_txt, inline=True)
    embed.add_field(name="Prioridad", value=prio_txt, inline=True)
    embed.add_field(name="📅 Creada", value=_fecha_legible(reg.get("fecha_creacion")), inline=True)

    resp = reg.get("responsable_id")
    embed.add_field(
        name="👮 Responsable",
        value=f"<@{resp}>" if resp else "— Sin asignar",
        inline=True,
    )

    campos = reg.get("campos") or {}
    if campos:
        lineas = []
        for k, v in campos.items():
            if v:
                lineas.append(f"**{k}:** {v}")
        if lineas:
            texto = "\n".join(lineas)
            if len(texto) > 1000:
                texto = texto[:997] + "…"
            embed.add_field(name="📝 Información proporcionada", value=texto, inline=False)

    if reg.get("resolucion"):
        embed.add_field(name="✅ Resolución", value=reg["resolucion"][:500], inline=False)

    if reg.get("motivo_cierre"):
        embed.add_field(
            name="🔒 Cierre",
            value=f"{reg['motivo_cierre']}\n{_fecha_legible(reg.get('fecha_cierre'))}",
            inline=False,
        )

    embed.set_footer(text=f"{config.NOMBRE_HOSPITAL} · ID interno {reg.get('id')}")
    return embed


def embed_log_accion(reg: dict, accion: str, autor: discord.abc.User, detalle: str = "") -> discord.Embed:
    cat = CATEGORIAS.get(reg.get("categoria", "general"), CATEGORIAS["general"])
    num = reg.get("numero", reg.get("id", 0))
    embed = discord.Embed(
        title="📋 SOLICITUD ACTUALIZADA",
        color=0x2C3E50,
        timestamp=discord.utils.utcnow(),
    )
    embed.add_field(name="ID", value=f"#{num:04d}", inline=True)
    embed.add_field(name="Categoría", value=f"{cat['emoji']} {cat['nombre']}", inline=True)
    embed.add_field(name="Usuario", value=f"<@{reg.get('usuario_id')}>", inline=True)
    resp = reg.get("responsable_id")
    embed.add_field(name="Responsable", value=f"<@{resp}>" if resp else "—", inline=True)
    embed.add_field(name="Acción", value=accion, inline=True)
    embed.add_field(name="Realizada por", value=autor.mention if hasattr(autor, "mention") else str(autor), inline=True)
    if detalle:
        embed.add_field(name="Detalle", value=detalle[:500], inline=False)
    embed.add_field(name="Fecha", value=_fecha_legible(), inline=True)
    embed.set_footer(text=config.NOMBRE_HOSPITAL)
    return embed


# ---------------------------------------------------------------------------
# Formularios (Modals)
# ---------------------------------------------------------------------------

class FormSancion(ui.Modal, title="🛡️ Solicitud de Sanción"):
    usuario_inv = ui.TextInput(label="Usuario involucrado", placeholder="ID o mención", max_length=100)
    motivo = ui.TextInput(label="Motivo", style=discord.TextStyle.paragraph, max_length=500)
    descripcion = ui.TextInput(label="Descripción", style=discord.TextStyle.paragraph, max_length=1000)
    evidencias = ui.TextInput(label="Evidencias", style=discord.TextStyle.paragraph, max_length=800, required=False)
    info_extra = ui.TextInput(label="Información adicional", style=discord.TextStyle.paragraph, max_length=500, required=False)

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        campos = {
            "Usuario involucrado": str(self.usuario_inv),
            "Motivo": str(self.motivo),
            "Descripción": str(self.descripcion),
            "Evidencias": str(self.evidencias) if self.evidencias.value else "—",
            "Información adicional": str(self.info_extra) if self.info_extra.value else "—",
        }
        await crear_ticket_solicitud(self.bot, interaction, "sancion", campos)


class FormApelacion(ui.Modal, title="⚖️ Apelación de Sanción"):
    usuario_sanc = ui.TextInput(label="Usuario sancionado", placeholder="ID o mención", max_length=100)
    sancion = ui.TextInput(label="Sanción recibida", max_length=200)
    motivo = ui.TextInput(label="Motivo de la apelación", style=discord.TextStyle.paragraph, max_length=800)
    hechos = ui.TextInput(label="Explicación de los hechos", style=discord.TextStyle.paragraph, max_length=1000)
    evidencias = ui.TextInput(label="Evidencias adicionales", style=discord.TextStyle.paragraph, max_length=800, required=False)

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        campos = {
            "Usuario sancionado": str(self.usuario_sanc),
            "Sanción recibida": str(self.sancion),
            "Motivo de la apelación": str(self.motivo),
            "Explicación de los hechos": str(self.hechos),
            "Evidencias adicionales": str(self.evidencias) if self.evidencias.value else "—",
        }
        await crear_ticket_solicitud(self.bot, interaction, "apelacion", campos)


class FormInvestigacion(ui.Modal, title="🔎 Solicitud de Investigación"):
    usuarios = ui.TextInput(label="Usuario/s involucrado/s", placeholder="ID o mención", max_length=200)
    motivo = ui.TextInput(label="Motivo de la investigación", style=discord.TextStyle.paragraph, max_length=500)
    descripcion = ui.TextInput(label="Descripción del caso", style=discord.TextStyle.paragraph, max_length=1000)
    evidencias = ui.TextInput(label="Evidencias", style=discord.TextStyle.paragraph, max_length=800, required=False)
    info_extra = ui.TextInput(label="Información adicional", style=discord.TextStyle.paragraph, max_length=500, required=False)

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        campos = {
            "Usuario/s involucrado/s": str(self.usuarios),
            "Motivo": str(self.motivo),
            "Descripción del caso": str(self.descripcion),
            "Evidencias": str(self.evidencias) if self.evidencias.value else "—",
            "Información adicional": str(self.info_extra) if self.info_extra.value else "—",
        }
        await crear_ticket_solicitud(self.bot, interaction, "investigacion", campos)


class FormReporte(ui.Modal, title="🚨 Reporte"):
    usuario = ui.TextInput(label="Usuario reportado", placeholder="ID o mención", max_length=100)
    motivo = ui.TextInput(label="Motivo del reporte", max_length=200)
    descripcion = ui.TextInput(label="Descripción", style=discord.TextStyle.paragraph, max_length=1000)
    fecha_hora = ui.TextInput(label="Fecha y hora aproximada", placeholder="Ej: 20/09/2026 18:00", max_length=80)
    evidencias = ui.TextInput(label="Evidencias / Testigos", style=discord.TextStyle.paragraph, max_length=800, required=False)

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        campos = {
            "Usuario reportado": str(self.usuario),
            "Motivo del reporte": str(self.motivo),
            "Descripción": str(self.descripcion),
            "Fecha y hora aproximada": str(self.fecha_hora),
            "Evidencias / Testigos": str(self.evidencias) if self.evidencias.value else "—",
        }
        await crear_ticket_solicitud(self.bot, interaction, "reporte", campos)


class FormGeneral(ui.Modal, title="📩 Solicitud General"):
    asunto = ui.TextInput(label="Asunto", max_length=120)
    descripcion = ui.TextInput(label="Descripción", style=discord.TextStyle.paragraph, max_length=1500)
    area = ui.TextInput(label="Área relacionada", placeholder="Ej: RRHH, Médico, Finanzas…", max_length=100)
    evidencias = ui.TextInput(label="Evidencias / documentos", style=discord.TextStyle.paragraph, max_length=800, required=False)
    info_extra = ui.TextInput(label="Información adicional", style=discord.TextStyle.paragraph, max_length=500, required=False)

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        campos = {
            "Asunto": str(self.asunto),
            "Descripción": str(self.descripcion),
            "Área relacionada": str(self.area),
            "Evidencias/documentos": str(self.evidencias) if self.evidencias.value else "—",
            "Información adicional": str(self.info_extra) if self.info_extra.value else "—",
        }
        await crear_ticket_solicitud(self.bot, interaction, "general", campos)


class FormConsulta(ui.Modal, title="📋 Consulta"):
    asunto = ui.TextInput(label="Asunto", max_length=120)
    pregunta = ui.TextInput(label="Pregunta", style=discord.TextStyle.paragraph, max_length=1500)
    info_extra = ui.TextInput(label="Información adicional", style=discord.TextStyle.paragraph, max_length=500, required=False)

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        campos = {
            "Asunto": str(self.asunto),
            "Pregunta": str(self.pregunta),
            "Información adicional": str(self.info_extra) if self.info_extra.value else "—",
        }
        await crear_ticket_solicitud(self.bot, interaction, "consulta", campos)


# ---------------------------------------------------------------------------
# Crear ticket
# ---------------------------------------------------------------------------

async def crear_ticket_solicitud(
    bot: commands.Bot,
    interaction: discord.Interaction,
    categoria: str,
    campos: Dict[str, str],
) -> None:
    guild = interaction.guild
    if not guild or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("❌ Solo disponible en el servidor.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    numero = _siguiente_numero()
    cat = CATEGORIAS.get(categoria, CATEGORIAS["general"])
    nombre_canal = f"{cat['prefijo']}-{numero:04d}"[:90]

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, attach_files=True, embed_links=True
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, manage_channels=True, manage_messages=True
        ),
    }

    staff_role = _rol_staff(guild)
    if staff_role:
        overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

    for key in getattr(config, "TICKET_STAFF_KEYS", []):
        if key == "DIRECTOR":
            for dk in config.DIRECTOR_KEYS:
                rid = roles_store.obtener_id_key(dk)
                if rid:
                    rol = guild.get_role(rid)
                    if rol:
                        overwrites[rol] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        else:
            rid = roles_store.obtener_id_key(key)
            if rid:
                rol = guild.get_role(rid)
                if rol:
                    overwrites[rol] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

    category = _categoria_canal(guild)
    try:
        canal = await guild.create_text_channel(
            nombre_canal,
            category=category,
            overwrites=overwrites,
            reason=f"Solicitud #{numero:04d} — {cat['nombre']} por {interaction.user}",
        )
    except discord.Forbidden:
        await interaction.followup.send("❌ No tengo permisos para crear canales.", ephemeral=True)
        return

    reg = {
        "id": numero,
        "numero": numero,
        "usuario_id": interaction.user.id,
        "categoria": categoria,
        "estado": "en_revision",
        "prioridad": "normal",
        "responsable_id": None,
        "fecha_creacion": _now(),
        "fecha_actualizacion": _now(),
        "fecha_cierre": None,
        "motivo_cierre": None,
        "campos": campos,
        "resolucion": None,
        "canal_id": canal.id,
        "usuarios_extra": [],
    }
    guardar_solicitud(reg)

    embed = embed_ticket(reg, guild)
    menciones = [interaction.user.mention]
    if staff_role:
        menciones.append(staff_role.mention)

    view = TicketSolicitudView(bot, numero)
    await canal.send(content=" ".join(menciones), embed=embed, view=view)

    await interaction.followup.send(
        f"✅ Solicitud **#{numero:04d}** creada: {canal.mention}",
        ephemeral=True,
    )

    log = embed_log_accion(reg, "Creación de solicitud", interaction.user, f"Canal: {canal.mention}")
    await enviar_log_solicitud(bot, log)


# ---------------------------------------------------------------------------
# Vistas: panel + menú + botones de ticket
# ---------------------------------------------------------------------------

class MenuCategorias(ui.Select):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        options = [
            discord.SelectOption(
                label=cat["nombre"],
                value=key,
                description=cat["menu_desc"][:100],
                emoji=cat["emoji"],
            )
            for key, cat in CATEGORIAS.items()
        ]
        super().__init__(
            placeholder="📂 Selecciona el tipo de solicitud",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="centro_menu_categorias",
        )

    async def callback(self, interaction: discord.Interaction):
        cat = self.values[0]
        formularios = {
            "sancion": FormSancion,
            "apelacion": FormApelacion,
            "investigacion": FormInvestigacion,
            "reporte": FormReporte,
            "general": FormGeneral,
            "consulta": FormConsulta,
        }
        cls = formularios.get(cat)
        if not cls:
            await interaction.response.send_message("❌ Categoría no válida.", ephemeral=True)
            return
        await interaction.response.send_modal(cls(self.bot))


class PanelSolicitudesView(ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.add_item(MenuCategorias(bot))


class ConfirmarCierreView(ui.View):
    def __init__(self, bot: commands.Bot, solicitud_id: int):
        super().__init__(timeout=60)
        self.bot = bot
        self.solicitud_id = solicitud_id

    @ui.button(label="Confirmar", style=discord.ButtonStyle.danger, emoji="✅")
    async def confirmar(self, interaction: discord.Interaction, button: ui.Button):
        reg = obtener_solicitud(self.solicitud_id)
        if not reg:
            await interaction.response.send_message("❌ Solicitud no encontrada.", ephemeral=True)
            return
        if not _puede_gestionar(interaction.user):
            await interaction.response.send_message("❌ No tienes permiso.", ephemeral=True)
            return

        motivo = "Cerrada por el staff"
        actualizar_solicitud(
            self.solicitud_id,
            estado="cerrada",
            motivo_cierre=motivo,
            fecha_cierre=_now(),
        )
        reg = obtener_solicitud(self.solicitud_id)
        embed = embed_ticket(reg, interaction.guild)
        await interaction.response.edit_message(
            content=f"🔒 Solicitud cerrada por {interaction.user.mention}",
            embed=embed,
            view=None,
        )
        log = embed_log_accion(reg, "Cierre", interaction.user, motivo)
        await enviar_log_solicitud(self.bot, log)

        # Borrar canal tras aviso
        if interaction.channel:
            try:
                await interaction.channel.send("🔒 Este canal se eliminará en 5 segundos…")
                import asyncio
                await asyncio.sleep(5)
                await interaction.channel.delete(reason=f"Solicitud #{self.solicitud_id} cerrada")
            except Exception:
                pass

    @ui.button(label="Cancelar", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancelar(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="Cierre cancelado.", embed=None, view=None)


class PrioridadSelect(ui.Select):
    def __init__(self, bot: commands.Bot, solicitud_id: int):
        self.bot = bot
        self.solicitud_id = solicitud_id
        options = [
            discord.SelectOption(label="Normal", value="normal", emoji="🟢"),
            discord.SelectOption(label="Media", value="media", emoji="🟡"),
            discord.SelectOption(label="Alta", value="alta", emoji="🟠"),
            discord.SelectOption(label="Urgente", value="urgente", emoji="🔴"),
        ]
        super().__init__(placeholder="Selecciona prioridad", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if not _puede_gestionar(interaction.user):
            await interaction.response.send_message("❌ Solo staff autorizado.", ephemeral=True)
            return
        prio = self.values[0]
        reg = actualizar_solicitud(self.solicitud_id, prioridad=prio)
        if not reg:
            await interaction.response.send_message("❌ Solicitud no encontrada.", ephemeral=True)
            return
        embed = embed_ticket(reg, interaction.guild)
        # Actualizar mensaje original del ticket si es posible
        await interaction.response.send_message(
            f"✅ Prioridad actualizada a **{PRIORIDADES[prio][0]}**.", ephemeral=True
        )
        try:
            async for msg in interaction.channel.history(limit=20):
                if msg.author == interaction.client.user and msg.embeds:
                    await msg.edit(embed=embed, view=TicketSolicitudView(self.bot, self.solicitud_id))
                    break
        except Exception:
            pass
        log = embed_log_accion(reg, "Cambio de prioridad", interaction.user, PRIORIDADES[prio][0])
        await enviar_log_solicitud(self.bot, log)


class PrioridadView(ui.View):
    def __init__(self, bot: commands.Bot, solicitud_id: int):
        super().__init__(timeout=60)
        self.add_item(PrioridadSelect(bot, solicitud_id))


class AnadirUsuarioModal(ui.Modal, title="👥 Añadir usuario al ticket"):
    usuario = ui.TextInput(label="ID o mención del usuario", max_length=100)

    def __init__(self, bot: commands.Bot, solicitud_id: int):
        super().__init__()
        self.bot = bot
        self.solicitud_id = solicitud_id

    async def on_submit(self, interaction: discord.Interaction):
        if not _puede_gestionar(interaction.user):
            await interaction.response.send_message("❌ Solo staff autorizado.", ephemeral=True)
            return
        raw = str(self.usuario).strip().replace("<@", "").replace("!", "").replace(">", "")
        try:
            uid = int(raw)
        except ValueError:
            await interaction.response.send_message("❌ ID inválido.", ephemeral=True)
            return
        member = interaction.guild.get_member(uid) if interaction.guild else None
        if not member:
            await interaction.response.send_message("❌ Usuario no encontrado en el servidor.", ephemeral=True)
            return
        try:
            await interaction.channel.set_permissions(
                member, view_channel=True, send_messages=True, attach_files=True
            )
        except discord.Forbidden:
            await interaction.response.send_message("❌ No puedo modificar permisos.", ephemeral=True)
            return

        reg = obtener_solicitud(self.solicitud_id)
        extras = list(reg.get("usuarios_extra") or []) if reg else []
        if uid not in extras:
            extras.append(uid)
            actualizar_solicitud(self.solicitud_id, usuarios_extra=extras)

        await interaction.response.send_message(f"✅ {member.mention} añadido al ticket.")
        if reg:
            log = embed_log_accion(reg, "Usuario añadido", interaction.user, member.mention)
            await enviar_log_solicitud(self.bot, log)


class EstadoSelect(ui.Select):
    def __init__(self, bot: commands.Bot, solicitud_id: int):
        self.bot = bot
        self.solicitud_id = solicitud_id
        options = [
            discord.SelectOption(label=v[0], value=k, emoji=v[0][0] if v[0] else None)
            for k, v in ESTADOS.items()
        ]
        super().__init__(placeholder="Cambiar estado", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if not _puede_gestionar(interaction.user):
            await interaction.response.send_message("❌ Solo staff autorizado.", ephemeral=True)
            return
        nuevo = self.values[0]
        reg_old = obtener_solicitud(self.solicitud_id)
        old_txt = ESTADOS.get((reg_old or {}).get("estado", ""), ("?", 0))[0]
        reg = actualizar_solicitud(self.solicitud_id, estado=nuevo)
        if not reg:
            await interaction.response.send_message("❌ Solicitud no encontrada.", ephemeral=True)
            return
        embed = embed_ticket(reg, interaction.guild)
        await interaction.response.send_message(
            f"✅ Estado: **{old_txt}** → **{ESTADOS[nuevo][0]}**", ephemeral=True
        )
        try:
            async for msg in interaction.channel.history(limit=20):
                if msg.author == interaction.client.user and msg.embeds:
                    await msg.edit(embed=embed, view=TicketSolicitudView(self.bot, self.solicitud_id))
                    break
        except Exception:
            pass
        log = embed_log_accion(reg, "Cambio de estado", interaction.user, f"{old_txt} → {ESTADOS[nuevo][0]}")
        await enviar_log_solicitud(self.bot, log)


class EstadoView(ui.View):
    def __init__(self, bot: commands.Bot, solicitud_id: int):
        super().__init__(timeout=60)
        self.add_item(EstadoSelect(bot, solicitud_id))


def _puede_gestionar(user: discord.abc.User) -> bool:
    if not isinstance(user, discord.Member):
        return False
    return permisos.member_tiene_alguna_key(
        user,
        "OWNER", "CO_OWNER", "DIRECTOR", "DIRECTOR_ADMINISTRATIVO",
        "DIRECTOR_DISCIPLINA", "DIRECTOR_GENERAL", "DIRECTOR_RRHH",
        "SUPERVISOR", "STAFF_SERVIDOR",
    )


class TicketSolicitudView(ui.View):
    def __init__(self, bot: commands.Bot, solicitud_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.solicitud_id = solicitud_id

    @ui.button(label="Reclamar", style=discord.ButtonStyle.primary, emoji="👋", custom_id="sol_reclamar")
    async def reclamar(self, interaction: discord.Interaction, button: ui.Button):
        if not _puede_gestionar(interaction.user):
            await interaction.response.send_message("❌ Solo staff autorizado.", ephemeral=True)
            return
        reg = actualizar_solicitud(self.solicitud_id, responsable_id=interaction.user.id, estado="en_revision")
        if not reg:
            # Recuperar id desde custom context — fallback
            await interaction.response.send_message("❌ Solicitud no encontrada.", ephemeral=True)
            return
        embed = embed_ticket(reg, interaction.guild)
        await interaction.response.edit_message(embed=embed, view=self)
        log = embed_log_accion(reg, "Reclamado", interaction.user)
        await enviar_log_solicitud(self.bot, log)

    @ui.button(label="Cerrar", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="sol_cerrar")
    async def cerrar(self, interaction: discord.Interaction, button: ui.Button):
        if not _puede_gestionar(interaction.user):
            await interaction.response.send_message("❌ Solo staff autorizado.", ephemeral=True)
            return
        await interaction.response.send_message(
            "⚠️ ¿Estás seguro de que deseas cerrar esta solicitud?",
            view=ConfirmarCierreView(self.bot, self.solicitud_id),
            ephemeral=True,
        )

    @ui.button(label="Prioridad", style=discord.ButtonStyle.secondary, emoji="📌", custom_id="sol_prioridad")
    async def prioridad(self, interaction: discord.Interaction, button: ui.Button):
        if not _puede_gestionar(interaction.user):
            await interaction.response.send_message("❌ Solo staff autorizado.", ephemeral=True)
            return
        await interaction.response.send_message(
            "Selecciona la prioridad:",
            view=PrioridadView(self.bot, self.solicitud_id),
            ephemeral=True,
        )

    @ui.button(label="Añadir usuario", style=discord.ButtonStyle.secondary, emoji="👥", custom_id="sol_adduser")
    async def adduser(self, interaction: discord.Interaction, button: ui.Button):
        if not _puede_gestionar(interaction.user):
            await interaction.response.send_message("❌ Solo staff autorizado.", ephemeral=True)
            return
        await interaction.response.send_modal(AnadirUsuarioModal(self.bot, self.solicitud_id))

    @ui.button(label="Estado", style=discord.ButtonStyle.secondary, emoji="📝", custom_id="sol_estado")
    async def estado(self, interaction: discord.Interaction, button: ui.Button):
        if not _puede_gestionar(interaction.user):
            await interaction.response.send_message("❌ Solo staff autorizado.", ephemeral=True)
            return
        await interaction.response.send_message(
            "Selecciona el nuevo estado:",
            view=EstadoView(self.bot, self.solicitud_id),
            ephemeral=True,
        )


# ---------------------------------------------------------------------------
# Registro de comandos
# ---------------------------------------------------------------------------

def registrar(bot: commands.Bot) -> None:
    """Registra el panel y vistas persistentes del centro de solicitudes."""

    @bot.tree.command(
        name="panel_solicitudes",
        description="Publica el Centro de Solicitudes (panel profesional)",
    )
    @app_commands.describe(canal="Canal donde publicar el panel (opcional)")
    async def panel_solicitudes(
        interaction: discord.Interaction,
        canal: Optional[discord.TextChannel] = None,
    ):
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("❌ Solo en servidor.", ephemeral=True)
            return
        if not permisos.member_tiene_alguna_key(
            interaction.user, "OWNER", "CO_OWNER", "DIRECTOR_ADMINISTRATIVO", "DIRECTOR_GENERAL"
        ):
            await interaction.response.send_message(
                "❌ Solo Owner / Director Administrativo / Director General.", ephemeral=True
            )
            return

        destino = canal or interaction.channel
        if not isinstance(destino, discord.TextChannel):
            await interaction.response.send_message("❌ Canal inválido.", ephemeral=True)
            return

        embed = embed_panel_principal()
        view = PanelSolicitudesView(bot)
        await destino.send(embed=embed, view=view)
        await interaction.response.send_message(
            f"✅ Panel de solicitudes publicado en {destino.mention}.", ephemeral=True
        )

    # Vistas persistentes (custom_id fijos del menú y botones genéricos)
    # Nota: los botones de ticket llevan solicitud_id en memoria; tras reinicio
    # el staff puede usar /panel_solicitudes de nuevo. Para persistencia total
    # se registra una vista plantilla.
    bot.add_view(PanelSolicitudesView(bot))
