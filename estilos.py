# -*- coding: utf-8 -*-
"""
estilos.py — Identidad visual del hospital.
Premium, realista y completa: tono institucional, información clara,
acabado profesional. Solo presentación (API compatible).
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Tuple

import discord

import config

# Paleta institucional realista (elegante, con color, sin neón extremo)
COLORES: Dict[str, int] = {
    "exito": 0x1E8449,
    "error": 0xC0392B,
    "aviso": 0xD68910,
    "info": 0x1A5276,
    "neutral": 0x5D6D7E,
    "medico": 0x0E6655,
    "finanzas": 0xB7950B,
    "sancion": 0x6C3483,
    "investigacion": 0x5B2C6F,
    "rrhh": 0x1F618D,
    "logistica": 0xCA6F1E,
    "seguridad": 0x2C3E50,
    "admin": 0x1B2631,
    "anuncio": 0x1A5276,
    "ticket": 0x2874A6,
    "citatorio": 0xA04000,
    "certificacion": 0x0E6655,
    "inactividad": 0x566573,
    "licencia": 0x2471A3,
    "estado": 0x0E6655,
    "roblox": 0x1A5276,
    "whitelist": 0x1E8449,
    "aprobado": 0x1E8449,
    "rechazado": 0xC0392B,
    "pendiente": 0xD68910,
}

EMOJI_TIPO: Dict[str, str] = {
    "exito": "✅",
    "error": "❌",
    "aviso": "⚠️",
    "info": "ℹ️",
    "medico": "🩺",
    "finanzas": "💰",
    "sancion": "⚖️",
    "investigacion": "📚",
    "rrhh": "👥",
    "logistica": "📦",
    "seguridad": "🛡️",
    "admin": "🏛️",
    "anuncio": "📢",
    "ticket": "🎫",
    "citatorio": "📨",
    "certificacion": "🎓",
    "inactividad": "⏸️",
    "licencia": "📋",
    "estado": "🏥",
    "neutral": "📄",
    "roblox": "🔗",
    "whitelist": "✅",
    "aprobado": "✅",
    "rechazado": "❌",
    "pendiente": "⏳",
}

_AREA: Dict[str, str] = {
    "exito": "Registro de operaciones",
    "error": "Control de incidencias",
    "aviso": "Alertas institucionales",
    "info": "Información general",
    "neutral": "Gestión hospitalaria",
    "medico": "Área clínica",
    "finanzas": "Dirección financiera",
    "sancion": "Régimen disciplinario",
    "investigacion": "Investigación y docencia",
    "rrhh": "Recursos humanos",
    "logistica": "Logística e insumos",
    "seguridad": "Seguridad hospitalaria",
    "admin": "Dirección general",
    "anuncio": "Comunicados oficiales",
    "ticket": "Mesa de ayuda",
    "citatorio": "Convocatorias formales",
    "certificacion": "Formación y acreditación",
    "inactividad": "Control de personal",
    "licencia": "Licencias médicas",
    "estado": "Centro de operaciones",
    "roblox": "Verificación de identidad",
    "whitelist": "Admisión de personal",
    "aprobado": "Resoluciones",
    "rechazado": "Resoluciones",
    "pendiente": "Trámites en curso",
}

_MARCAS = tuple(EMOJI_TIPO.values()) + ("🏥",)


def _hospital() -> str:
    return getattr(config, "NOMBRE_HOSPITAL", None) or "Hospital General"


def _footer(tipo: str = "neutral", extra: str = "") -> str:
    parts = [f"🏥 {_hospital()}"]
    area = _AREA.get(tipo)
    if area:
        parts.append(area)
    if extra and str(extra).strip():
        parts.append(str(extra).strip())
    return "  ·  ".join(parts)


def _titulo(titulo: str, emoji: str) -> str:
    if any(m in titulo for m in _MARCAS):
        return titulo
    return f"{emoji}  {titulo}"


def _safe(v: Any, default: str = "—") -> str:
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default


def crear_embed(
    tipo: str,
    titulo: str,
    descripcion: str = "",
    autor: Optional[discord.abc.User] = None,
    footer_extra: str = "",
    thumbnail_url: Optional[str] = None,
    image_url: Optional[str] = None,
) -> discord.Embed:
    """Fábrica principal de embeds (compatible con todo el bot)."""
    key = (tipo or "neutral").lower().strip()
    color = COLORES.get(key, COLORES["neutral"])
    emoji = EMOJI_TIPO.get(key, "📄")

    emb = discord.Embed(
        title=_titulo(titulo, emoji),
        description=(descripcion.strip() if descripcion else None),
        color=color,
        timestamp=discord.utils.utcnow(),
    )

    if autor is not None:
        try:
            nombre = getattr(autor, "display_name", None) or str(autor)
            icon = getattr(getattr(autor, "display_avatar", None), "url", None)
            emb.set_author(name=str(nombre), icon_url=icon)
        except Exception:
            pass

    thumb = thumbnail_url or getattr(config, "LOGO_URL", None)
    if thumb:
        try:
            emb.set_thumbnail(url=thumb)
        except Exception:
            pass

    if image_url:
        try:
            emb.set_image(url=image_url)
        except Exception:
            pass

    emb.set_footer(text=_footer(key, footer_extra))
    return emb


def embed_campo(
    emb: discord.Embed,
    nombre: str,
    valor: Any,
    inline: bool = True,
) -> discord.Embed:
    emb.add_field(name=nombre, value=_safe(valor)[:1024], inline=inline)
    return emb


def embed_campos(
    emb: discord.Embed,
    campos: Sequence[Tuple[str, Any, bool]],
) -> discord.Embed:
    for nombre, valor, inline in campos:
        embed_campo(emb, nombre, valor, inline)
    return emb


def embed_exito_rapido(
    titulo: str,
    descripcion: str,
    autor: Optional[discord.abc.User] = None,
) -> discord.Embed:
    return crear_embed(
        "exito",
        titulo or "Procedimiento completado",
        descripcion
        or (
            "La operación se registró correctamente en el sistema del hospital.\n"
            "Puede consultar el historial correspondiente si requiere constancia."
        ),
        autor=autor,
    )


def embed_error_rapido(titulo: str, descripcion: str) -> discord.Embed:
    return crear_embed(
        "error",
        titulo or "No se pudo completar la solicitud",
        descripcion
        or (
            "El sistema interrumpió la operación por una validación pendiente.\n\n"
            "**Qué puede hacer**\n"
            "• Revisar que todos los datos estén correctos\n"
            "• Verificar que cuenta con el permiso adecuado\n"
            "• Intentar nuevamente en unos momentos\n\n"
            "Si el problema continúa, contacte a la dirección de su área o a Sistemas."
        ),
    )


def embed_aviso(
    titulo: str,
    descripcion: str,
    autor: Optional[discord.abc.User] = None,
) -> discord.Embed:
    return crear_embed("aviso", titulo, descripcion, autor=autor)


def embed_info(
    titulo: str,
    descripcion: str,
    autor: Optional[discord.abc.User] = None,
) -> discord.Embed:
    return crear_embed("info", titulo, descripcion, autor=autor)


def embed_permiso_denegado(requerido: str = "") -> discord.Embed:
    cuerpo = (
        "No dispone de la **autorización** necesaria para este procedimiento.\n\n"
        "Este módulo está reservado al personal con la competencia jerárquica correspondiente."
    )
    if requerido:
        cuerpo += f"\n\n**Nivel o cargo requerido:** `{requerido}`"
    cuerpo += (
        "\n\nSi considera que se trata de un error en la asignación de roles, "
        "consulte con su superior inmediato, con Recursos Humanos o con la Dirección General."
    )
    return crear_embed("error", "Acceso restringido", cuerpo)


def embed_validacion(mensaje: str) -> discord.Embed:
    return crear_embed(
        "aviso",
        "Validación de datos",
        mensaje
        or (
            "Uno o más campos del formulario no cumplen los requisitos.\n\n"
            "**Revisar:**\n"
            "• Campos obligatorios completos\n"
            "• Formato de fechas, identificaciones o montos\n"
            "• Que el usuario o canal indicado exista en el servidor\n\n"
            "Corrija la información e intente el envío otra vez."
        ),
    )


def embed_confirmacion(
    titulo: str,
    descripcion: str,
    *,
    campos: Optional[Sequence[Tuple[str, Any, bool]]] = None,
    autor: Optional[discord.abc.User] = None,
    tipo: str = "exito",
) -> discord.Embed:
    emb = crear_embed(tipo, titulo, descripcion, autor=autor)
    if campos:
        embed_campos(emb, campos)
    return emb


def embed_whitelist_roblox(
    discord_user: discord.abc.User,
    roblox_data: Dict[str, Any],
    aprobado: bool = True,
    staff: Optional[discord.abc.User] = None,
) -> discord.Embed:
    username = roblox_data.get("username") or "—"
    display = roblox_data.get("displayName") or username
    user_id = roblox_data.get("id") or "—"
    created = roblox_data.get("created") or "—"
    avatar_url = roblox_data.get("avatar_url")
    profile_url = (
        f"https://www.roblox.com/users/{user_id}/profile" if user_id != "—" else None
    )

    if aprobado:
        titulo = "Verificación de identidad aprobada"
        desc = (
            f"La verificación del personaje ha sido **aprobada** conforme al protocolo de ingreso.\n\n"
            f"La cuenta de Roblox quedó **vinculada** al expediente digital de personal del hospital.\n"
            f"Bienvenido/a al equipo de **{_hospital()}**."
        )
        tipo = "whitelist"
        estado = "✅ Aprobado"
    else:
        titulo = "Verificación de identidad no aprobada"
        desc = (
            f"La verificación **no fue aprobada** en esta instancia.\n\n"
            f"El postulante puede corregir los datos (usuario, captura o requisitos) "
            f"y presentar una **nueva solicitud** según el protocolo de admisión."
        )
        tipo = "rechazado"
        estado = "❌ No aprobado"

    emb = crear_embed(tipo, titulo, desc, autor=discord_user)
    if profile_url:
        emb.url = profile_url
    if avatar_url:
        emb.set_thumbnail(url=avatar_url)

    embed_campos(
        emb,
        [
            ("Usuario Roblox", f"`{username}`", True),
            ("Nombre visible", f"**{display}**", True),
            ("ID de cuenta", f"`{user_id}`", True),
        ],
    )

    if created and created != "—":
        try:
            from datetime import datetime

            dt = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
            created_fmt = dt.strftime("%d/%m/%Y")
        except Exception:
            created_fmt = str(created)[:10]
        embed_campo(emb, "Cuenta creada", created_fmt)

    embed_campo(emb, "Resolución", f"**{estado}**")
    if staff:
        embed_campo(emb, "Evaluado por", staff.mention)

    if profile_url:
        emb.add_field(
            name="Perfil externo",
            value=f"[Abrir perfil en Roblox]({profile_url})",
            inline=False,
        )

    emb.set_footer(text=_footer("whitelist", "Unidad de admisión"))
    return emb
