# -*- coding: utf-8 -*-
"""
estilos.py — Identidad visual del hospital.
Embeds sobrios, clínicos y profesionales. Sin cambiar lógica de negocio.
"""
from __future__ import annotations

from typing import Optional, List, Dict, Any, Union

import discord

import config

# Paleta institucional (sobria, hospitalaria)
COLORES = {
    # Semánticos
    "exito": 0x1E8449,          # Verde quirófano
    "error": 0x922B21,          # Rojo clínico
    "aviso": 0xB7950B,          # Ámbar institucional
    "info": 0x1A5276,           # Azul expediente
    "neutral": 0x5D6D7E,        # Gris acero
    # Áreas
    "medico": 0x148F77,         # Teal médico
    "finanzas": 0x9A7D0A,       # Oro contable
    "sancion": 0x7B241C,        # Granate disciplina
    "investigacion": 0x4A235A,  # Violeta docencia
    "rrhh": 0x6C3483,           # Púrpura RRHH
    "logistica": 0xAF601A,      # Cobre logística
    "seguridad": 0x2C3E50,      # Azul noche
    "admin": 0x1C2833,          # Carbón administración
    "anuncio": 0x154360,        # Azul comunicado
    "ticket": 0x1B4F72,         # Azul soporte
    "citatorio": 0x6E2C00,      # Marrón formal
    "certificacion": 0x0E6655,  # Verde diploma
    "inactividad": 0x566573,    # Gris inactividad
    "licencia": 0x2874A6,       # Azul licencia
    "estado": 0x1A5276,         # Azul sistemas
    "roblox": 0x1A5276,         # Alineado al hospital
    "whitelist": 0x1E8449,
    "aprobado": 0x1E8449,
    "rechazado": 0x922B21,
    "pendiente": 0xB7950B,
}

EMOJI_TIPO = {
    "exito": "✓",
    "error": "✕",
    "aviso": "◈",
    "info": "◉",
    "medico": "🩺",
    "finanzas": "🧾",
    "sancion": "⚖",
    "investigacion": "📑",
    "rrhh": "👥",
    "logistica": "📦",
    "seguridad": "🛡",
    "admin": "🖥",
    "anuncio": "📢",
    "ticket": "🎫",
    "citatorio": "📨",
    "certificacion": "🎓",
    "inactividad": "⏸",
    "licencia": "📋",
    "estado": "📡",
    "neutral": "📋",
    "roblox": "🔗",
    "whitelist": "✓",
    "aprobado": "✓",
    "rechazado": "✕",
    "pendiente": "⏳",
}

# Títulos de área para footers contextuales
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
    "estado": "Sistemas y operaciones",
    "roblox": "Verificación de identidad",
    "whitelist": "Admisión de personal",
}

_HOSPITAL = lambda: getattr(config, "NOMBRE_HOSPITAL", None) or "Hospital General"


def _footer_base(extra: str = "", area: str = "") -> str:
    parts = [_HOSPITAL()]
    if area and area in _AREA_FOOTER:
        parts.append(_AREA_FOOTER[area])
    elif area:
        parts.append(area)
    if extra:
        parts.append(extra.strip())
    return "  ·  ".join(parts)


def _titulo_con_marca(titulo: str, emoji: str) -> str:
    """Añade emoji solo si el título no trae ya uno reconocible."""
    marcas = (
        "✓", "✕", "⚠", "✅", "❌", "⚠", "ℹ️", "🩺", "🧾", "⚖", "📢",
        "🎓", "⏸", "📡", "🎫", "📨", "📋", "🔗", "⏳", "◈", "◉",
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
    """
    Embed institucional del hospital.
    Compatible con todas las llamadas existentes (misma firma).
    """
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
    """Añade un campo con valor seguro (nunca vacío)."""
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
        descripcion or "El procedimiento se registró correctamente en el sistema.",
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
    extra = f"\n**Nivel requerido:** `{requerido}`" if requerido else ""
    return crear_embed(
        "error",
        "Acceso restringido",
        "No cuenta con la autorización necesaria para este procedimiento."
        + extra
        + "\n\nSi considera que se trata de un error, elevé la consulta a su superior jerárquico "
        "o a la Dirección General.",
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
    """Embed de verificación Roblox — tono de admisión hospitalaria."""
    username = roblox_data.get("username") or "—"
    display = roblox_data.get("displayName") or username
    user_id = roblox_data.get("id") or "—"
    created = roblox_data.get("created") or "—"
    avatar_url = roblox_data.get("avatar_url")
    profile_url = (
        f"https://www.roblox.com/users/{user_id}/profile" if user_id != "—" else None
    )

    if aprobado:
        titulo = "Admisión confirmada — Identidad verificada"
        desc = (
            f"La verificación de identidad del postulante ha sido **aprobada**.\n\n"
            f"La cuenta de Roblox quedó vinculada al expediente digital del personal.\n"
            f"Bienvenido/a al cuerpo del **{_HOSPITAL()}**."
        )
        tipo = "whitelist"
        estado = "✓ Aprobado"
    else:
        titulo = "Admisión no concedida"
        desc = (
            f"La verificación de identidad **no fue aprobada**.\n\n"
            f"El postulante puede corregir los datos y presentar una nueva solicitud "
            f"conforme al protocolo de ingreso."
        )
        tipo = "rechazado"
        estado = "✕ No aprobado"

    embed = crear_embed(tipo, titulo, desc, autor=discord_user)
    if profile_url:
        embed.url = profile_url
    if avatar_url:
        embed.set_thumbnail(url=avatar_url)

    embed_campo(embed, "Usuario Roblox", f"`{username}`")
    embed_campo(embed, "Nombre visible", f"**{display}**")
    embed_campo(embed, "ID de cuenta", f"`{user_id}`")

    if created and created != "—":
        try:
            from datetime import datetime

            dt = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
            created_fmt = dt.strftime("%d/%m/%Y")
        except Exception:
            created_fmt = str(created)[:10]
        embed_campo(embed, "Alta de cuenta", created_fmt)

    embed_campo(embed, "Resolución", f"**{estado}**")
    if staff:
        embed_campo(embed, "Evaluado por", staff.mention)

    if profile_url:
        embed.add_field(
            name="Expediente externo",
            value=f"[Consultar perfil Roblox]({profile_url})",
            inline=False,
        )

    embed.set_footer(text=_footer_base("Unidad de admisión y verificación"))
    return embed
