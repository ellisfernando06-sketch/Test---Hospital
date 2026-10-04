# -*- coding: utf-8 -*-
"""
paneles_direccion.py — Paneles de acción por dirección + Canciller / Vice.

/enviar_paneles_direccion — solo Owner/Co-Owner/Admin
Interactúan: Owner, Co-Owner, Admin jefe, Admin, Admin en prueba y el director del área.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Sequence, Set

import discord
from discord import app_commands, ui
from discord.ext import commands

import config

# Keys que pueden usar CUALQUIER panel
_KEYS_GLOBAL = (
    "FUNDADOR_OWNER",
    "CO_OWNER",
    "OWNER",
    "ADMIN_JEFE",
    "ADMIN",
    "ADMIN_PRUEBA",
    "ADMIN_EN_PRUEBA",
)

# area_key → (título, emoji, color, keys del director, líneas de acciones)
PANELES = {
    "docencia": {
        "titulo": "Dirección de Docencia",
        "emoji": "📚",
        "color": 0x9B59B6,
        "keys": ("DIR_DOCENCIA", "DIRECTOR_DOCENCIA"),
        "acciones": [
            "Solicitudes de certificados y firmas",
            "Capacitaciones y material de estudio",
            "Aprobar / rechazar postulaciones a certificación",
            "Emitir certificados oficiales",
            "Coordinar con encargados de capacitación",
        ],
    },
    "medico": {
        "titulo": "Dirección Médica",
        "emoji": "🩺",
        "color": 0xE74C3C,
        "keys": ("DIR_MEDICO", "DIRECTOR_MEDICO"),
        "acciones": [
            "Supervisión del área médica y especialidades",
            "Expedientes y protocolos clínicos",
            "Licencias médicas del personal",
            "Coordinación de urgencias / plantas",
            "Autorizaciones de procedimientos de área",
        ],
    },
    "enfermeria": {
        "titulo": "Dirección de Enfermería",
        "emoji": "💉",
        "color": 0x3498DB,
        "keys": ("DIR_ENFERMERIA", "DIRECTOR_ENFERMERIA"),
        "acciones": [
            "Turnos y dotación de enfermería",
            "Protocolos de cuidados",
            "Reportes del área",
            "Coordinación con Dirección Médica",
            "Capacitación interna de enfermería",
        ],
    },
    "rrhh": {
        "titulo": "Recursos Humanos",
        "emoji": "👥",
        "color": 0x1ABC9C,
        "keys": ("DIR_RRHH", "DIRECTOR_RRHH"),
        "acciones": [
            "Postulaciones y entrevistas",
            "Inactividad justificada",
            "Sanciones y despidos",
            "Investigaciones de personal",
            "Expedientes de personal",
        ],
    },
    "logistica": {
        "titulo": "Dirección de Logística",
        "emoji": "📦",
        "color": 0xF39C12,
        "keys": ("DIR_LOGISTICA", "DIRECTOR_LOGISTICA"),
        "acciones": [
            "Inventario y suministros",
            "Solicitudes de material",
            "Coordinación de entregas",
            "Reportes de stock",
            "Apoyo a áreas clínicas",
        ],
    },
    "general": {
        "titulo": "Dirección General",
        "emoji": "🖥️",
        "color": 0x2C3E50,
        "keys": ("DIR_GENERAL", "DIRECTOR_GENERAL"),
        "acciones": [
            "Supervisión general del hospital",
            "Anuncios entre direcciones",
            "Resolución de conflictos de área",
            "Autorizaciones institucionales",
            "Coordinación con Cancillería",
        ],
    },
    "seguridad": {
        "titulo": "Departamento de Seguridad",
        "emoji": "🛡️",
        "color": 0x95A5A6,
        "keys": ("JEFE_SEGURIDAD", "SUPERVISOR_SEGURIDAD"),
        "acciones": [
            "Códigos y alertas de seguridad",
            "Control de accesos",
            "Incidentes en el servidor / RP",
            "Coordinación con staff",
            "Reportes de seguridad",
        ],
    },
    "canciller": {
        "titulo": "Cancillería · Canciller",
        "emoji": "⚜️",
        "color": 0xF1C40F,
        "keys": ("CANCILLER", "PREFECTO_OPERACIONES"),
        "acciones": [
            "Operaciones generales del servidor",
            "Órdenes ejecutivas",
            "Citatorios y accesos especiales",
            "Supervisión de direcciones",
            "Agenda ejecutiva y reuniones",
            "Coordinación con Owner / Admin",
        ],
    },
    "vice_canciller": {
        "titulo": "Cancillería · Vice Canciller",
        "emoji": "🔰",
        "color": 0xE67E22,
        "keys": ("VICE_CANCILLER", "CANCILLER"),
        "acciones": [
            "Apoyo operativo al Canciller",
            "Seguimiento de órdenes ejecutivas",
            "Cobertura en ausencia del Canciller",
            "Coordinación de operaciones",
            "Enlace con direcciones",
            "Agenda y prioridades ejecutivas",
        ],
    },
}


def _hospital() -> str:
    return getattr(config, "NOMBRE_HOSPITAL", None) or "Hospital General"


def _member_keys(member: discord.Member) -> Set[str]:
    keys: Set[str] = set()
    if member.guild_permissions.administrator:
        keys.update(_KEYS_GLOBAL)
    try:
        import roles_config
        import roles_store

        for k, nom in (getattr(roles_config, "KEYS_NOMBRES", {}) or {}).items():
            nombre = nom[0] if isinstance(nom, (list, tuple)) else str(nom)
            for r in member.roles:
                if r.name == nombre or nombre.lower() in (r.name or "").lower():
                    keys.add(str(k))
        # store ids
        try:
            data = roles_store._load() if hasattr(roles_store, "_load") else {}
        except Exception:
            data = {}
    except Exception:
        pass
    # Admin en prueba por nombre
    for r in member.roles:
        rn = (r.name or "").lower()
        if "admin" in rn and "prueba" in rn:
            keys.add("ADMIN_PRUEBA")
        if rn in ("admin", "administrador"):
            keys.add("ADMIN")
    return keys


def _puede_panel(member: discord.Member, area_keys: Sequence[str]) -> bool:
    if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
        return True
    keys = _member_keys(member)
    if any(k in keys for k in _KEYS_GLOBAL):
        return True
    return any(k in keys for k in area_keys)


def _puede_enviar_comando(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    keys = _member_keys(member)
    return any(
        k in keys
        for k in (
            "FUNDADOR_OWNER",
            "CO_OWNER",
            "OWNER",
            "ADMIN_JEFE",
            "ADMIN",
        )
    )


def embed_panel(area: str) -> discord.Embed:
    info = PANELES[area]
    lineas = "\n".join(f"▸ {a}" for a in info["acciones"])
    emb = discord.Embed(
        title=f"{info['emoji']}  {info['titulo']}",
        description=(
            f"**{_hospital()}** · Panel de dirección\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"**Acciones de esta dirección**\n"
            f"{lineas}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"*Solo autoridades y el director de esta área pueden usar los botones.*"
        ),
        color=info["color"],
        timestamp=datetime.now(timezone.utc),
    )
    emb.set_footer(text=f"{_hospital()} · Gestión institucional · {area}")
    return emb


class PanelDireccionView(ui.View):
    def __init__(self, area: str):
        super().__init__(timeout=None)
        self.area = area
        info = PANELES[area]
        self.area_keys = info["keys"]

    async def interaction_check(self, inter: discord.Interaction) -> bool:
        if not isinstance(inter.user, discord.Member):
            return False
        if _puede_panel(inter.user, self.area_keys):
            return True
        await inter.response.send_message(
            "❌ No autorizado. Solo **Owner / Co-Owner / Admin / Admin en prueba** "
            "y el **director** de esta área.",
            ephemeral=True,
        )
        return False

    @ui.button(
        label="Estado del área",
        style=discord.ButtonStyle.primary,
        emoji="📊",
        custom_id="pdir:estado",
    )
    async def estado(self, inter: discord.Interaction, button: ui.Button):
        info = PANELES[self.area]
        emb = discord.Embed(
            title=f"{info['emoji']} Estado · {info['titulo']}",
            description=(
                f"Panel activo y operativo.\n"
                f"Responsables: {', '.join(f'`{k}`' for k in info['keys'])}\n\n"
                f"Usa los canales de esta dirección para solicitudes formales."
            ),
            color=info["color"],
        )
        await inter.response.send_message(embed=emb, ephemeral=True)

    @ui.button(
        label="Guía de acciones",
        style=discord.ButtonStyle.secondary,
        emoji="📋",
        custom_id="pdir:guia",
    )
    async def guia(self, inter: discord.Interaction, button: ui.Button):
        await inter.response.send_message(embed=embed_panel(self.area), ephemeral=True)

    @ui.button(
        label="Recordatorio staff",
        style=discord.ButtonStyle.success,
        emoji="🔔",
        custom_id="pdir:aviso",
    )
    async def aviso(self, inter: discord.Interaction, button: ui.Button):
        info = PANELES[self.area]
        emb = discord.Embed(
            title=f"🔔 {info['titulo']}",
            description=(
                f"{inter.user.mention} envió un recordatorio desde el panel.\n"
                f"Revisen solicitudes pendientes en este canal."
            ),
            color=info["color"],
        )
        await inter.response.send_message("✅ Recordatorio publicado.", ephemeral=True)
        try:
            await inter.channel.send(embed=emb)
        except Exception:
            pass


# Vistas con custom_id único por área (persistentes)
class PanelDocencia(PanelDireccionView):
    def __init__(self):
        super().__init__("docencia")
        for i, child in enumerate(self.children):
            child.custom_id = f"pdir:docencia:{i}"


class PanelMedico(PanelDireccionView):
    def __init__(self):
        super().__init__("medico")
        for i, child in enumerate(self.children):
            child.custom_id = f"pdir:medico:{i}"


class PanelEnfermeria(PanelDireccionView):
    def __init__(self):
        super().__init__("enfermeria")
        for i, child in enumerate(self.children):
            child.custom_id = f"pdir:enfermeria:{i}"


class PanelRRHH(PanelDireccionView):
    def __init__(self):
        super().__init__("rrhh")
        for i, child in enumerate(self.children):
            child.custom_id = f"pdir:rrhh:{i}"


class PanelLogistica(PanelDireccionView):
    def __init__(self):
        super().__init__("logistica")
        for i, child in enumerate(self.children):
            child.custom_id = f"pdir:logistica:{i}"


class PanelGeneral(PanelDireccionView):
    def __init__(self):
        super().__init__("general")
        for i, child in enumerate(self.children):
            child.custom_id = f"pdir:general:{i}"


class PanelSeguridad(PanelDireccionView):
    def __init__(self):
        super().__init__("seguridad")
        for i, child in enumerate(self.children):
            child.custom_id = f"pdir:seguridad:{i}"


class PanelCanciller(PanelDireccionView):
    def __init__(self):
        super().__init__("canciller")
        for i, child in enumerate(self.children):
            child.custom_id = f"pdir:canciller:{i}"


class PanelVice(PanelDireccionView):
    def __init__(self):
        super().__init__("vice_canciller")
        for i, child in enumerate(self.children):
            child.custom_id = f"pdir:vice:{i}"


_VIEW_MAP = {
    "docencia": PanelDocencia,
    "medico": PanelMedico,
    "enfermeria": PanelEnfermeria,
    "rrhh": PanelRRHH,
    "logistica": PanelLogistica,
    "general": PanelGeneral,
    "seguridad": PanelSeguridad,
    "canciller": PanelCanciller,
    "vice_canciller": PanelVice,
}

# área canales_direccion → panel
_AREA_CANAL = {
    "docencia": "docencia",
    "medico": "medico",
    "enfermeria": "enfermeria",
    "rrhh": "rrhh",
    "logistica": "logistica",
    "general": "general",
    "seguridad": "seguridad",
    "cancilleria": "canciller",
}


def registrar(bot: commands.Bot) -> None:
    for cls in _VIEW_MAP.values():
        try:
            bot.add_view(cls())
        except Exception:
            pass

    @bot.tree.command(
        name="enviar_paneles_direccion",
        description="[Owner/Admin] Envía paneles a cada canal de dirección",
    )
    async def enviar_paneles(inter: discord.Interaction):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _puede_enviar_comando(inter.user):
            return await inter.response.send_message(
                "❌ Solo **Owner, Co-Owner o Admin**.", ephemeral=True
            )

        await inter.response.defer(ephemeral=True)
        enviados = []
        fallidos = []

        try:
            import canales_direccion as cd

            for area_cfg, panel_key in _AREA_CANAL.items():
                cid = cd.obtener_canal_id(area_cfg)
                ch = inter.guild.get_channel(int(cid)) if cid else None
                if not isinstance(ch, discord.TextChannel):
                    fallidos.append(f"`{area_cfg}` sin canal")
                    continue
                cls = _VIEW_MAP[panel_key]
                await ch.send(embed=embed_panel(panel_key), view=cls())
                enviados.append(ch.mention)

            # Vice canciller: mismo canal cancillería o segundo mensaje
            cid = cd.obtener_canal_id("cancilleria")
            ch = inter.guild.get_channel(int(cid)) if cid else None
            if isinstance(ch, discord.TextChannel):
                await ch.send(
                    embed=embed_panel("vice_canciller"), view=PanelVice()
                )
                enviados.append(f"{ch.mention} (Vice)")
        except Exception as e:
            fallidos.append(str(e))

        msg = f"✅ Paneles enviados: {', '.join(enviados) or 'ninguno'}"
        if fallidos:
            msg += f"\n⚠️ {'; '.join(fallidos)}"
        await inter.followup.send(msg, ephemeral=True)

    @bot.tree.command(
        name="panel_direccion",
        description="[Owner/Admin] Publica un panel en el canal actual",
    )
    @app_commands.describe(area="Área del panel")
    @app_commands.choices(
        area=[
            app_commands.Choice(name=v["titulo"], value=k)
            for k, v in PANELES.items()
        ]
    )
    async def panel_uno(
        inter: discord.Interaction, area: app_commands.Choice[str]
    ):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _puede_enviar_comando(inter.user):
            return await inter.response.send_message(
                "❌ Solo Owner / Admin.", ephemeral=True
            )
        if not isinstance(inter.channel, discord.TextChannel):
            return await inter.response.send_message(
                "❌ Canal de texto.", ephemeral=True
            )
        cls = _VIEW_MAP[area.value]
        await inter.channel.send(embed=embed_panel(area.value), view=cls())
        await inter.response.send_message("✅ Panel publicado.", ephemeral=True)

    print("[paneles_direccion] OK — /enviar_paneles_direccion · /panel_direccion")
