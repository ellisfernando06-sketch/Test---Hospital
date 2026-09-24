# -*- coding: utf-8 -*
"""
docencia.py — Certificados y capacitaciones (solo Roleplay).
Director de Docencia emite certificados bonitos de uso exclusivo en RP.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

import discord
from discord import app_commands, ui
from discord.ext import commands

import config
import permisos

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_CERT_PATH = os.path.join(_DATA_DIR, "certificados.json")

# Tipos de certificado predefinidos (RP)
TIPOS_CERTIFICADO = {
    "rcp": {
        "titulo": "Certificado de RCP / BLS",
        "emoji": "❤️",
        "desc": "Reanimación cardiopulmonar básica y soporte vital.",
    },
    "trauma": {
        "titulo": "Certificado de Atención al Trauma",
        "emoji": "🩹",
        "desc": "Valoración y manejo inicial del paciente politraumatizado.",
    },
    "medicacion": {
        "titulo": "Certificado de Administración de Medicamentos",
        "emoji": "💊",
        "desc": "Protocolos de administración segura de fármacos.",
    },
    "quirurgico": {
        "titulo": "Certificado de Protocolo Quirúrgico",
        "emoji": "🔬",
        "desc": "Normas de asepsia y circulación en quirófano.",
    },
    "emergencias": {
        "titulo": "Certificado de Códigos de Emergencia",
        "emoji": "🚨",
        "desc": "Respuesta coordinada a códigos hospitalarios.",
    },
    "enfermeria": {
        "titulo": "Certificado de Cuidados de Enfermería",
        "emoji": "💉",
        "desc": "Procedimientos básicos y avanzados de enfermería.",
    },
    "docente": {
        "titulo": "Certificado de Instructor Hospitalario",
        "emoji": "📚",
        "desc": "Habilitación para impartir capacitaciones internas.",
    },
    "personalizado": {
        "titulo": "Certificado de Capacitación",
        "emoji": "📜",
        "desc": "Capacitación personalizada del hospital.",
    },
}


def _load() -> dict:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_CERT_PATH):
        return {"certificados": [], "next_id": 1}
    try:
        with open(_CERT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("certificados", [])
        data.setdefault("next_id", 1)
        return data
    except Exception:
        return {"certificados": [], "next_id": 1}


def _save(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_CERT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def emitir(
    uid: int,
    titulo: str,
    tipo: str,
    descripcion: str,
    emitido_por: int,
    notas: str = "",
    departamento: str = "",
) -> dict:
    data = _load()
    cid = data["next_id"]
    data["next_id"] = cid + 1
    reg = {
        "id": cid,
        "uid": uid,
        "titulo": titulo,
        "tipo": tipo or "personalizado",
        "descripcion": descripcion or "",
        "notas": notas or "",
        "departamento": departamento or "",
        "emitido_por": emitido_por,
        "fecha": datetime.now(timezone.utc).isoformat(),
        "solo_rp": True,
    }
    data["certificados"].append(reg)
    _save(data)
    return reg


def certificados_de(uid: int) -> List[dict]:
    data = _load()
    return [c for c in data["certificados"] if c.get("uid") == uid]


def obtener(cid: int) -> Optional[dict]:
    data = _load()
    for c in data["certificados"]:
        if int(c.get("id") or 0) == int(cid):
            return c
    return None


def listar_recientes(n: int = 20) -> List[dict]:
    data = _load()
    return list(reversed(data["certificados"][-n:]))


def _fecha_legible(iso: str = "") -> str:
    if not iso:
        return datetime.now(timezone.utc).strftime("%d/%m/%Y")
    try:
        dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return str(iso)[:10]


def embed_certificado(
    reg: dict,
    guild: Optional[discord.Guild] = None,
    receptor: Optional[discord.abc.User] = None,
    emisor: Optional[discord.abc.User] = None,
) -> discord.Embed:
    """
    Certificado profesional de uso exclusivo en Roleplay.
    Diseño tipo diploma oficial del hospital.
    """
    tipo = TIPOS_CERTIFICADO.get(reg.get("tipo") or "personalizado", TIPOS_CERTIFICADO["personalizado"])
    emoji = tipo.get("emoji", "📜")
    titulo = reg.get("titulo") or tipo.get("titulo") or "Certificado"
    hospital = getattr(config, "NOMBRE_HOSPITAL", "Hospital") or "Hospital"

    nombre_receptor = "—"
    if receptor:
        nombre_receptor = getattr(receptor, "display_name", None) or str(receptor)
    elif guild and reg.get("uid"):
        m = guild.get_member(int(reg["uid"]))
        if m:
            nombre_receptor = m.display_name
            receptor = m
        else:
            nombre_receptor = f"<@{reg['uid']}>"

    nombre_emisor = "Dirección de Docencia"
    if emisor:
        nombre_emisor = getattr(emisor, "display_name", None) or str(emisor)
    elif guild and reg.get("emitido_por"):
        m = guild.get_member(int(reg["emitido_por"]))
        if m:
            nombre_emisor = m.display_name

    desc = (
        f"╔══════════════════════════════════╗\n"
        f"║     **{hospital.upper()}**     ║\n"
        f"║   Dirección de Docencia y Capacitación   ║\n"
        f"╚══════════════════════════════════╝\n\n"
        f"Se certifica que\n\n"
        f"# {nombre_receptor}\n\n"
        f"ha completado satisfactoriamente la capacitación:\n\n"
        f"### {emoji} {titulo}\n\n"
    )

    detalle = (reg.get("descripcion") or tipo.get("desc") or "").strip()
    if detalle:
        desc += f"*{detalle}*\n\n"

    desc += (
        f"---\n"
        f"📌 **Uso exclusivo en Roleplay** — No tiene validez fuera del servidor.\n"
        f"Este documento forma parte del sistema formativo interno del hospital."
    )

    emb = discord.Embed(
        title=f"{emoji}  CERTIFICADO OFICIAL",
        description=desc,
        color=0x8E44AD,
        timestamp=discord.utils.utcnow(),
    )

    if receptor and hasattr(receptor, "display_avatar"):
        emb.set_thumbnail(url=receptor.display_avatar.url)

    emb.add_field(name="📅 Fecha de emisión", value=_fecha_legible(reg.get("fecha")), inline=True)
    emb.add_field(name="🔢 N.º de certificado", value=f"`CERT-{int(reg.get('id') or 0):05d}`", inline=True)
    emb.add_field(name="🏛️ Emitido por", value=nombre_emisor, inline=True)

    if reg.get("departamento"):
        emb.add_field(name="📂 Área / Departamento", value=str(reg["departamento"])[:100], inline=True)

    if reg.get("notas"):
        emb.add_field(name="📝 Observaciones", value=str(reg["notas"])[:300], inline=False)

    logo = getattr(config, "LOGO_URL", None)
    if logo:
        emb.set_image(url=logo)

    emb.set_footer(text=f"{hospital}  •  Solo Roleplay  •  Dirección de Docencia")
    return emb


def _puede_emitir(member: discord.Member) -> bool:
    if not isinstance(member, discord.Member):
        return False
    return permisos.member_tiene_alguna_key(
        member,
        "OWNER", "CO_OWNER",
        "DIRECTOR_DOCENCIA", "DIRECTOR_GENERAL",
        "DIRECTOR_MEDICO", "DIRECTOR_ENFERMERIA",
        "DIRECTOR_ADMINISTRATIVO",
    )


class ModalCertificado(ui.Modal, title="📜 Emitir certificado RP"):
    titulo = ui.TextInput(
        label="Título del certificado",
        placeholder="Ej: Certificado de RCP avanzado",
        max_length=120,
        required=True,
    )
    descripcion = ui.TextInput(
        label="Descripción / contenido",
        style=discord.TextStyle.paragraph,
        placeholder="Qué aprendió o superó el personal…",
        max_length=500,
        required=False,
    )
    departamento = ui.TextInput(
        label="Departamento / área (opcional)",
        placeholder="Cuerpo Médico, Enfermería…",
        max_length=80,
        required=False,
    )
    notas = ui.TextInput(
        label="Observaciones (opcional)",
        style=discord.TextStyle.paragraph,
        placeholder="Calificación, horas, instructor…",
        max_length=300,
        required=False,
    )

    def __init__(self, bot: commands.Bot, usuario: discord.Member, tipo: str = "personalizado"):
        super().__init__()
        self.bot = bot
        self.usuario = usuario
        self.tipo = tipo
        pre = TIPOS_CERTIFICADO.get(tipo, TIPOS_CERTIFICADO["personalizado"])
        self.titulo.default = pre.get("titulo", "Certificado")
        self.descripcion.default = pre.get("desc", "")

    async def on_submit(self, inter: discord.Interaction):
        if not isinstance(inter.user, discord.Member) or not _puede_emitir(inter.user):
            await inter.response.send_message("❌ Sin permiso para emitir certificados.", ephemeral=True)
            return

        reg = emitir(
            uid=self.usuario.id,
            titulo=str(self.titulo),
            tipo=self.tipo,
            descripcion=str(self.descripcion) if self.descripcion.value else "",
            emitido_por=inter.user.id,
            notas=str(self.notas) if self.notas.value else "",
            departamento=str(self.departamento) if self.departamento.value else "",
        )

        # También registrar en capacitaciones legacy
        try:
            import capacitaciones
            capacitaciones.certificar(self.usuario.id, str(self.titulo), inter.user.id)
        except Exception:
            pass

        emb = embed_certificado(reg, inter.guild, receptor=self.usuario, emisor=inter.user)

        await inter.response.send_message(
            content=(
                f"📜 Certificado emitido para {self.usuario.mention}\n"
                f"N.º `CERT-{reg['id']:05d}` · **Solo Roleplay**"
            ),
            embed=emb,
        )

        # DM al receptor
        try:
            await self.usuario.send(
                content=f"🎓 Has recibido un certificado del **{getattr(config, 'NOMBRE_HOSPITAL', 'Hospital')}**:",
                embed=emb,
            )
        except Exception:
            pass

        # Log
        try:
            import logs_store
            ch = logs_store.resolver_canal_log(self.bot, inter.guild, "log_certificados")
            if not ch:
                ch = logs_store.resolver_canal_log(self.bot, inter.guild, "log_capacitaciones")
            if ch:
                await ch.send(
                    content=f"📜 Nuevo certificado · {self.usuario.mention} · por {inter.user.mention}",
                    embed=emb,
                )
        except Exception:
            pass


def registrar(bot: commands.Bot) -> None:

    @bot.tree.command(
        name="crear_certificado",
        description="Emitir un certificado RP (Director de Docencia / dirección)",
    )
    @app_commands.describe(
        usuario="Personal que recibe el certificado",
        tipo="Tipo de certificado",
    )
    @app_commands.choices(tipo=[
        app_commands.Choice(name="❤️ RCP / BLS", value="rcp"),
        app_commands.Choice(name="🩹 Atención al Trauma", value="trauma"),
        app_commands.Choice(name="💊 Administración de Medicamentos", value="medicacion"),
        app_commands.Choice(name="🔬 Protocolo Quirúrgico", value="quirurgico"),
        app_commands.Choice(name="🚨 Códigos de Emergencia", value="emergencias"),
        app_commands.Choice(name="💉 Cuidados de Enfermería", value="enfermeria"),
        app_commands.Choice(name="📚 Instructor Hospitalario", value="docente"),
        app_commands.Choice(name="📜 Personalizado", value="personalizado"),
    ])
    async def crear_certificado(
        inter: discord.Interaction,
        usuario: discord.Member,
        tipo: app_commands.Choice[str],
    ):
        if not isinstance(inter.user, discord.Member) or not _puede_emitir(inter.user):
            await inter.response.send_message(
                "❌ Solo **Director de Docencia**, dirección u OWNER pueden emitir certificados.",
                ephemeral=True,
            )
            return
        await inter.response.send_modal(ModalCertificado(bot, usuario, tipo.value))

    @bot.tree.command(
        name="mis_certificados",
        description="Ver tus certificados RP del hospital",
    )
    async def mis_certificados(inter: discord.Interaction):
        lista = certificados_de(inter.user.id)
        if not lista:
            await inter.response.send_message(
                "📜 Aún no tienes certificados. Participa en capacitaciones de Docencia.",
                ephemeral=True,
            )
            return
        emb = discord.Embed(
            title=f"📜 Certificados de {inter.user.display_name}",
            description=f"Tienes **{len(lista)}** certificado(s) · Solo Roleplay",
            color=0x8E44AD,
            timestamp=discord.utils.utcnow(),
        )
        for c in lista[-15:]:
            tipo = TIPOS_CERTIFICADO.get(c.get("tipo") or "", {})
            emoji = tipo.get("emoji", "📜")
            emb.add_field(
                name=f"{emoji} CERT-{int(c.get('id') or 0):05d} — {c.get('titulo', 'Certificado')}",
                value=f"📅 {_fecha_legible(c.get('fecha'))}",
                inline=False,
            )
        emb.set_footer(text=f"{getattr(config, 'NOMBRE_HOSPITAL', 'Hospital')}  •  Docencia")
        await inter.response.send_message(embed=emb, ephemeral=True)

    @bot.tree.command(
        name="ver_certificados",
        description="Ver certificados RP de un miembro (staff)",
    )
    @app_commands.describe(usuario="Miembro a consultar")
    async def ver_certificados(inter: discord.Interaction, usuario: discord.Member):
        if not isinstance(inter.user, discord.Member) or not permisos.member_tiene_alguna_key(
            inter.user,
            "OWNER", "CO_OWNER", "DIRECTOR_DOCENCIA", "DIRECTOR_GENERAL",
            "DIRECTOR_RRHH", "DIRECTOR_ADMINISTRATIVO", "SUPERVISOR",
        ):
            await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
            return
        lista = certificados_de(usuario.id)
        if not lista:
            await inter.response.send_message(
                f"📜 {usuario.mention} no tiene certificados registrados.",
                ephemeral=True,
            )
            return
        emb = discord.Embed(
            title=f"📜 Certificados de {usuario.display_name}",
            description=f"**{len(lista)}** certificado(s)",
            color=0x8E44AD,
            timestamp=discord.utils.utcnow(),
        )
        for c in lista[-15:]:
            tipo = TIPOS_CERTIFICADO.get(c.get("tipo") or "", {})
            emoji = tipo.get("emoji", "📜")
            emb.add_field(
                name=f"{emoji} CERT-{int(c.get('id') or 0):05d} — {c.get('titulo', 'Certificado')}",
                value=f"📅 {_fecha_legible(c.get('fecha'))}",
                inline=False,
            )
        emb.set_footer(text=f"{getattr(config, 'NOMBRE_HOSPITAL', 'Hospital')}  •  Docencia")
        await inter.response.send_message(embed=emb, ephemeral=True)

    @bot.tree.command(
        name="mostrar_certificado",
        description="Mostrar un certificado por su número (CERT-00001)",
    )
    @app_commands.describe(numero="Número del certificado (ej: 1)")
    async def mostrar_certificado(inter: discord.Interaction, numero: app_commands.Range[int, 1, 99999]):
        reg = obtener(int(numero))
        if not reg:
            await inter.response.send_message("❌ Certificado no encontrado.", ephemeral=True)
            return
        # Público si es el dueño o staff
        es_dueno = inter.user.id == int(reg.get("uid") or 0)
        es_staff = isinstance(inter.user, discord.Member) and permisos.member_tiene_alguna_key(
            inter.user,
            "OWNER", "CO_OWNER", "DIRECTOR_DOCENCIA", "DIRECTOR_GENERAL",
            "DIRECTOR_RRHH", "SUPERVISOR",
        )
        if not es_dueno and not es_staff:
            await inter.response.send_message("❌ Solo el titular o staff pueden mostrar este certificado.", ephemeral=True)
            return
        receptor = inter.guild.get_member(int(reg["uid"])) if inter.guild else None
        emisor = inter.guild.get_member(int(reg["emitido_por"])) if inter.guild and reg.get("emitido_por") else None
        emb = embed_certificado(reg, inter.guild, receptor=receptor, emisor=emisor)
        await inter.response.send_message(embed=emb)

    print("[docencia] OK — certificados RP")
