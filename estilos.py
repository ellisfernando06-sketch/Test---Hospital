# -*- coding: utf-8 -*-
"""
estilos.py — Sistema visual del hospital.
Tecnológico, limpio, en español y fácil de leer.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Tuple

import discord

import config

COLORES: Dict[str, int] = {
    "exito": 0x2ECC71,
    "error": 0xE74C3C,
    "aviso": 0xF39C12,
    "info": 0x3498DB,
    "neutral": 0x95A5A6,
    "medico": 0x1ABC9C,
    "finanzas": 0xF1C40F,
    "sancion": 0x9B59B6,
    "investigacion": 0x8E44AD,
    "rrhh": 0x5DADE2,
    "logistica": 0xE67E22,
    "seguridad": 0x34495E,
    "admin": 0x2C3E50,
    "anuncio": 0x3498DB,
    "ticket": 0x5DADE2,
    "citatorio": 0xE67E22,
    "certificacion": 0x1ABC9C,
    "inactividad": 0x95A5A6,
    "licencia": 0x3498DB,
    "estado": 0x1ABC9C,
    "roblox": 0x3498DB,
    "whitelist": 0x2ECC71,
    "aprobado": 0x2ECC71,
    "rechazado": 0xE74C3C,
    "pendiente": 0xF39C12,
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
    "estado": "🖥️",
    "neutral": "📄",
    "roblox": "🔗",
    "whitelist": "✅",
    "aprobado": "✅",
    "rechazado": "❌",
    "pendiente": "⏳",
}

_AREA: Dict[str, str] = {
    "exito": "Operaciones",
    "error": "Errores",
    "aviso": "Alertas",
    "info": "Información",
    "neutral": "Sistema",
    "medico": "Clínica",
    "finanzas": "Finanzas",
    "sancion": "Disciplina",
    "investigacion": "Docencia",
    "rrhh": "RRHH",
    "logistica": "Logística",
    "seguridad": "Seguridad",
    "admin": "Dirección",
    "anuncio": "Comunicados",
    "ticket": "Soporte",
    "citatorio": "Citatorios",
    "certificacion": "Certificados",
    "inactividad": "Personal",
    "licencia": "Licencias",
    "estado": "Panel de control",
    "roblox": "Verificación",
    "whitelist": "Admisión",
    "aprobado": "Resoluciones",
    "rechazado": "Resoluciones",
    "pendiente": "En espera",
}

_MARCAS = tuple(EMOJI_TIPO.values())


def _hospital() -> str:
    return getattr(config, "NOMBRE_HOSPITAL", None) or "Hospital General"


def _footer(tipo: str = "neutral", extra: str = "") -> str:
    parts = [f"🖥️ {_hospital()}"]
    area = _AREA.get(tipo)
    if area:
        parts.append(area)
    if extra and str(extra).strip():
        parts.append(str(extra).strip())
    return " · ".join(parts)


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
        titulo or "Operación completada",
        descripcion or "La acción se guardó correctamente en el sistema.",
        autor=autor,
    )


def embed_error_rapido(titulo: str, descripcion: str) -> discord.Embed:
    return crear_embed(
        "error",
        titulo or "No se pudo completar",
        descripcion
        or (
            "El sistema no pudo terminar esta acción.\n\n"
            "Revisa los datos, tus permisos e inténtalo de nuevo.\n"
            "Si sigue fallando, avisa a Sistemas o a la dirección de tu área."
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
        "No tienes permiso para usar esta función del sistema.\n"
        "Está reservada al personal autorizado."
    )
    if requerido:
        cuerpo += f"\n\n**Se necesita:** `{requerido}`"
    cuerpo += "\n\nSi crees que es un error, habla con RRHH o con Dirección."
    return crear_embed("error", "Acceso denegado", cuerpo)


def embed_validacion(mensaje: str) -> discord.Embed:
    return crear_embed(
        "aviso",
        "Datos incompletos",
        mensaje or "Falta información o algún dato no es válido. Corrige e inténtalo otra vez.",
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
        titulo = "Verificación aprobada"
        desc = (
            f"La cuenta de Roblox quedó **vinculada** al personal.\n"
            f"Bienvenido/a a **{_hospital()}**."
        )
        tipo = "whitelist"
        estado = "✅ Aprobado"
    else:
        titulo = "Verificación no aprobada"
        desc = "La verificación no pasó. Corrige los datos y vuelve a postularte."
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
            ("Nombre", f"**{display}**", True),
            ("ID", f"`{user_id}`", True),
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

    embed_campo(emb, "Resultado", f"**{estado}**")
    if staff:
        embed_campo(emb, "Revisado por", staff.mention)

    if profile_url:
        emb.add_field(name="Perfil", value=f"[Ver en Roblox]({profile_url})", inline=False)

    emb.set_footer(text=_footer("whitelist", "Admisión"))
    return emb
