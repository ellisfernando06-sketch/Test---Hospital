# -*- coding: utf-8 -*-
"""
estilos.py — Identidad visual del hospital.
Profesional, elegante y con color institucional (sin recargar).
"""
from __future__ import annotations

from typing import Optional, Dict, Any

import discord

import config

# Paleta: profesional + elegante + color vivo pero contenido
COLORES = {
    "exito": 0x27AE60,          # Esmeralda
    "error": 0xC0392B,          # Carmín elegante
    "aviso": 0xE67E22,          # Ámbar cálido
    "info": 0x2980B9,           # Azul hospital
    "neutral": 0x7F8C8D,        # Gris perla
    "medico": 0x1ABC9C,         # Turquesa clínico
    "finanzas": 0xF39C12,       # Oro suave
    "sancion": 0x8E44AD,        # Violeta disciplina
    "investigacion": 0x9B59B6,  # Amatista docencia
    "rrhh": 0x5DADE2,           # Azul cielo RRHH
    "logistica": 0xE67E22,      # Cobre
    "seguridad": 0x34495E,      # Azul pizarra
    "admin": 0x2C3E50,          # Azul noche
    "anuncio": 0x3498DB,        # Azul comunicado
    "ticket": 0x5DADE2,         # Celeste soporte
    "citatorio": 0xD35400,      # Naranja formal
    "certificacion": 0x16A085,  # Verde diploma
    "inactividad": 0x95A5A6,    # Gris suave
    "licencia": 0x3498DB,       # Azul licencia
    "estado": 0x1ABC9C,         # Turquesa sistemas
    "roblox": 0x3498DB,
    "whitelist": 0x27AE60,
    "aprobado": 0x27AE60,
    "rechazado": 0xC0392B,
    "pendiente": 0xF39C12,
}

EMOJI_TIPO = {
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
    "admin": "🖥️",
    "anuncio": "📢",
    "ticket": "🎫",
    "citatorio": "📨",
    "certificacion": "🎓",
    "inactividad": "⏸️",
    "licencia": "📋",
    "estado": "🏥",
    "neutral": "📋",
    "roblox": "🔗",
    "whitelist": "✅",
    "aprobado": "✅",
    "rechazado": "❌",
    "pendiente": "⏳",
}

_AREA_FOOTER = {
    "medico": "Área clínica",
    "finanzas": "Dirección financiera",
    "sancion": "Disciplina y régimen interno",
    "investigacion": "Investigación y docencia",
    "rrhh": "Recursos humanos",
    "logistica": "Logística e insumos",
    "seguridad": "Seguridad hospitalaria",
    "admin": "Administración general",
    "anuncio": "Comunicados oficiales",
    "ticket": "Mesa de ayuda",
    "citatorio": "Convocatorias formales",
    "certificacion": "Formación y acreditación",
    "inactividad": "Control de personal",
    "licencia": "Licencias médicas",
    "estado": "Centro de operaciones",
    "roblox": "Verificación de identidad",
    "whitelist": "Admisión de personal",
    "exito": "Gestión hospitalaria",
    "error": "Gestión hospitalaria",
    "aviso": "Gestión hospitalaria",
    "info": "Gestión hospitalaria",
}


def _hospital() -> str:
    return getattr(config, "NOMBRE_HOSPITAL", None) or "Hospital General"


def _footer_base(extra: str = "", area: str = "") -> str:
    parts = [f"🏥 {_hospital()}"]
    if area and area in _AREA_FOOTER:
        parts.append(_AREA_FOOTER[area])
    elif area:
        parts.append(area)
    if extra:
        parts.append(extra.strip())
    return "  ·  ".join(parts)


def _titulo_con_marca(titulo: str, emoji: str) -> str:
    marcas = (
        "✅", "❌", "⚠️", "ℹ️", "🩺", "💰", "⚖️", "📢", "🎓", "⏸️",
        "🏥", "🎫", "📨", "📋", "🔗", "⏳", "📚", "👥", "📦", "🛡️", "🖥️",
    )
    if any(m in titulo for m in marcas):
        return titulo
    return f"{emoji}  {titulo}"


def crear_embed(
    tipo: str,
    titulo: str,
    descripcion: str = "",
    autor: Optional[discord.abc.User] = None,
    footer_extra: str = "",
    thumbnail_url: Optional[str] = None,
    image_url: Optional[str] = None,
) -> discord.Embed:
    tipo_key = (tipo or "neutral").lower().strip()
    color = COLORES.get(tipo_key, COLORES["neutral"])
    emoji = EMOJI_TIPO.get(tipo_key, "📋")

    embed = discord.Embed(
        title=_titulo_con_marca(titulo, emoji),
        description=(descripcion.strip() if descripcion else None),
        color=color,
        timestamp=discord.utils.utcnow(),
    )

    if autor is not None:
        try:
            nombre = getattr(autor, "display_name", None) or str(autor)
            avatar = getattr(getattr(autor, "display_avatar", None), "url", None)
            embed.set_author(name=str(nombre), icon_url=avatar)
        except Exception:
            pass

    thumb = thumbnail_url or getattr(config, "LOGO_URL", None)
    if thumb:
        try:
            embed.set_thumbnail(url=thumb)
        except Exception:
            pass

    if image_url:
        try:
            embed.set_image(url=image_url)
        except Exception:
            pass

    embed.set_footer(text=_footer_base(footer_extra, area=tipo_key))
    return embed


def embed_campo(
    embed: discord.Embed,
    nombre: str,
    valor: Any,
    inline: bool = True,
) -> discord.Embed:
    v = str(valor) if valor is not None else "—"
    if not v.strip():
        v = "—"
    embed.add_field(name=nombre, value=v[:1024], inline=inline)
    return embed


def embed_exito_rapido(
    titulo: str,
    descripcion: str,
    autor: Optional[discord.abc.User] = None,
) -> discord.Embed:
    return crear_embed(
        "exito",
        titulo or "Operación completada",
        descripcion or "El procedimiento se registró correctamente en el sistema hospitalario.",
        autor=autor,
    )


def embed_error_rapido(titulo: str, descripcion: str) -> discord.Embed:
    return crear_embed(
        "error",
        titulo or "No se pudo completar la solicitud",
        descripcion
        or (
            "La operación fue interrumpida por una validación del sistema.\n"
            "Revise los datos e intente nuevamente. Si el inconveniente persiste, "
            "contacte a la dirección correspondiente."
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
    extra = f"\n\n**Nivel requerido:** `{requerido}`" if requerido else ""
    return crear_embed(
        "error",
        "Acceso restringido",
        "No cuenta con la autorización necesaria para este procedimiento."
        + extra
        + "\n\nSi considera que se trata de un error, consulte con su superior "
        "jerárquico o con la Dirección General.",
    )


def embed_validacion(mensaje: str) -> discord.Embed:
    return crear_embed(
        "aviso",
        "Validación de datos",
        mensaje
        or "Uno o más campos no cumplen los requisitos del formulario. Corrija e intente de nuevo.",
    )


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
        titulo = "Admisión confirmada"
        desc = (
            f"La verificación de identidad ha sido **aprobada** con éxito.\n\n"
            f"La cuenta de Roblox quedó vinculada al expediente digital.\n"
            f"Bienvenido/a al equipo del **{_hospital()}**."
        )
        tipo = "whitelist"
        estado = "✅ Aprobado"
    else:
        titulo = "Admisión no concedida"
        desc = (
            f"La verificación de identidad **no fue aprobada**.\n\n"
            f"Puede corregir los datos y presentar una nueva solicitud "
            f"según el protocolo de ingreso."
        )
        tipo = "rechazado"
        estado = "❌ No aprobado"

    embed = crear_embed(tipo, titulo, desc, autor=discord_user)
    if profile_url:
        embed.url = profile_url
    if avatar_url:
        embed.set_thumbnail(url=avatar_url)

    embed_campo(embed, "🎮 Usuario Roblox", f"`{username}`")
    embed_campo(embed, "📛 Nombre visible", f"**{display}**")
    embed_campo(embed, "🆔 ID de cuenta", f"`{user_id}`")

    if created and created != "—":
        try:
            from datetime import datetime

            dt = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
            created_fmt = dt.strftime("%d/%m/%Y")
        except Exception:
            created_fmt = str(created)[:10]
        embed_campo(embed, "📅 Alta de cuenta", created_fmt)

    embed_campo(embed, "📊 Resolución", f"**{estado}**")
    if staff:
        embed_campo(embed, "👤 Evaluado por", staff.mention)

    if profile_url:
        embed.add_field(
            name="🔗 Perfil",
            value=f"[Abrir en Roblox]({profile_url})",
            inline=False,
        )

    embed.set_footer(text=_footer_base("Unidad de admisión y verificación"))
    return embed
