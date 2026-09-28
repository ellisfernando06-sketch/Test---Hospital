# -*- coding: utf-8 -*-
"""
estilos.py — Identidad visual premium del hospital.

Diseño sofisticado, clínico y coherente por área funcional.
Solo presentación: no altera lógica de negocio.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import discord

import config

# ═══════════════════════════════════════════════════════════════════════════
# Paleta institucional premium (armónica, sobria, con carácter)
# ═══════════════════════════════════════════════════════════════════════════
COLORES: Dict[str, int] = {
    # Semántica operativa
    "exito": 0x1F8A5B,        # Verde quirófano profundo
    "error": 0xA93226,        # Rojo clínico
    "aviso": 0xD68910,        # Ámbar institucional
    "info": 0x1F618D,         # Azul expediente
    "neutral": 0x5D6D7E,      # Acero
    # Áreas clínicas / administrativas
    "medico": 0x117A65,       # Teal médico
    "finanzas": 0xB7950B,     # Oro contable
    "sancion": 0x6C3483,      # Violeta régimen
    "investigacion": 0x5B2C6F,# Amatista docencia
    "rrhh": 0x2E86AB,         # Azul personal
    "logistica": 0xCA6F1E,    # Cobre logístico
    "seguridad": 0x2C3E50,    # Pizarra
    "admin": 0x1B2631,        # Carbón dirección
    "anuncio": 0x1A5276,      # Azul comunicado
    "ticket": 0x2874A6,       # Azul mesa de ayuda
    "citatorio": 0xA04000,    # Terracota formal
    "certificacion": 0x0E6655,# Verde diploma
    "inactividad": 0x707B7C,  # Gris control
    "licencia": 0x2471A3,     # Azul licencia
    "estado": 0x0E6655,       # Sistemas
    "roblox": 0x1F618D,
    "whitelist": 0x1F8A5B,
    "aprobado": 0x1F8A5B,
    "rechazado": 0xA93226,
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

_AREA_LABEL: Dict[str, str] = {
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

_MARCAS = (
    "✅", "❌", "⚠️", "ℹ️", "🩺", "💰", "⚖️", "📢", "🎓", "⏸️",
    "🏥", "🎫", "📨", "📋", "🔗", "⏳", "📚", "👥", "📦", "🛡️",
    "🏛️", "📄",
)


def _hospital() -> str:
    return getattr(config, "NOMBRE_HOSPITAL", None) or "Hospital General"


def _footer(tipo: str = "neutral", extra: str = "") -> str:
    parts = [f"🏥  {_hospital()}"]
    label = _AREA_LABEL.get(tipo)
    if label:
        parts.append(label)
    if extra and extra.strip():
        parts.append(extra.strip())
    return "  ·  ".join(parts)


def _titulo(titulo: str, emoji: str) -> str:
    if any(m in titulo for m in _MARCAS):
        return titulo
    return f"{emoji}  {titulo}"


def _safe(valor: Any, default: str = "—") -> str:
    if valor is None:
        return default
    s = str(valor).strip()
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
    """
    Fábrica principal de embeds (compatible con todo el bot).
    """
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
    """campos = [(nombre, valor, inline), ...]"""
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
        or "La operación se registró correctamente en el sistema hospitalario.",
        autor=autor,
    )


def embed_error_rapido(titulo: str, descripcion: str) -> discord.Embed:
    return crear_embed(
        "error",
        titulo or "No fue posible completar la solicitud",
        descripcion
        or (
            "El sistema interrumpió la operación por una validación pendiente.\n\n"
            "*Revise los datos e intente nuevamente. Si el inconveniente persiste, "
            "eleve el caso a la dirección correspondiente.*"
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
        "No dispone de la **autorización jerárquica** necesaria para este procedimiento."
    )
    if requerido:
        cuerpo += f"\n\n**Competencia requerida:** `{requerido}`"
    cuerpo += (
        "\n\nSi considera que se trata de un error de asignación de roles, "
        "consulte con su superior inmediato o con la Dirección General."
    )
    return crear_embed("error", "Acceso restringido", cuerpo)


def embed_validacion(mensaje: str) -> discord.Embed:
    return crear_embed(
        "aviso",
        "Validación de formulario",
        mensaje
        or (
            "Uno o más campos no cumplen los requisitos del protocolo.\n"
            "Corrija la información e intente el envío nuevamente."
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
    """Confirmación rica con campos opcionales."""
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
        titulo = "Admisión confirmada"
        desc = (
            f"La verificación de identidad del postulante ha sido **aprobada**.\n\n"
            f"La cuenta de Roblox quedó vinculada al **expediente digital** de personal.\n"
            f"Bienvenido/a al cuerpo del **{_hospital()}**."
        )
        tipo = "whitelist"
        estado = "✅  Aprobado"
    else:
        titulo = "Admisión no concedida"
        desc = (
            f"La verificación de identidad **no fue aprobada**.\n\n"
            f"El postulante podrá corregir los datos y presentar una nueva solicitud "
            f"conforme al protocolo de ingreso."
        )
        tipo = "rechazado"
        estado = "❌  No aprobado"

    emb = crear_embed(tipo, titulo, desc, autor=discord_user)
    if profile_url:
        emb.url = profile_url
    if avatar_url:
        emb.set_thumbnail(url=avatar_url)

    embed_campos(
        emb,
        [
            ("🎮  Usuario Roblox", f"`{username}`", True),
            ("📛  Nombre visible", f"**{display}**", True),
            ("🆔  ID de cuenta", f"`{user_id}`", True),
        ],
    )

    if created and created != "—":
        try:
            from datetime import datetime

            dt = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
            created_fmt = dt.strftime("%d/%m/%Y")
        except Exception:
            created_fmt = str(created)[:10]
        embed_campo(emb, "📅  Alta de cuenta", created_fmt)

    embed_campo(emb, "📊  Resolución", f"**{estado}**")
    if staff:
        embed_campo(emb, "👤  Evaluado por", staff.mention)

    if profile_url:
        emb.add_field(
            name="🔗  Expediente externo",
            value=f"[Consultar perfil en Roblox]({profile_url})",
            inline=False,
        )

    emb.set_footer(text=_footer("whitelist", "Unidad de admisión"))
    return emb
