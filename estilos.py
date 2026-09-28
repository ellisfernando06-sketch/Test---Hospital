# -*- coding: utf-8 -*-
"""
estilos.py — Sistema visual del hospital.
Muy tecnológico, todo en español, fácil de entender.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Tuple

import discord

import config

COLORES: Dict[str, int] = {
    "exito": 0x00D2A0,
    "error": 0xFF4757,
    "aviso": 0xFFA502,
    "info": 0x2E86DE,
    "neutral": 0x747D8C,
    "medico": 0x00D2A0,
    "finanzas": 0xFFC048,
    "sancion": 0xA55EEA,
    "investigacion": 0x8C7AE6,
    "rrhh": 0x54A0FF,
    "logistica": 0xFF7F50,
    "seguridad": 0x2F3542,
    "admin": 0x1E272E,
    "anuncio": 0x2E86DE,
    "ticket": 0x54A0FF,
    "citatorio": 0xFF7F50,
    "certificacion": 0x00D2A0,
    "inactividad": 0x747D8C,
    "licencia": 0x2E86DE,
    "estado": 0x00D2A0,
    "roblox": 0x2E86DE,
    "whitelist": 0x00D2A0,
    "aprobado": 0x00D2A0,
    "rechazado": 0xFF4757,
    "pendiente": 0xFFA502,
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
    "exito": "Módulo · Operaciones",
    "error": "Módulo · Errores",
    "aviso": "Módulo · Alertas",
    "info": "Módulo · Información",
    "neutral": "Sistema hospitalario",
    "medico": "Módulo · Clínica",
    "finanzas": "Módulo · Finanzas",
    "sancion": "Módulo · Disciplina",
    "investigacion": "Módulo · Docencia",
    "rrhh": "Módulo · RRHH",
    "logistica": "Módulo · Logística",
    "seguridad": "Módulo · Seguridad",
    "admin": "Módulo · Dirección",
    "anuncio": "Módulo · Comunicados",
    "ticket": "Módulo · Soporte",
    "citatorio": "Módulo · Citatorios",
    "certificacion": "Módulo · Certificados",
    "inactividad": "Módulo · Personal",
    "licencia": "Módulo · Licencias",
    "estado": "Panel de control",
    "roblox": "Módulo · Verificación",
    "whitelist": "Módulo · Admisión",
    "aprobado": "Módulo · Resoluciones",
    "rechazado": "Módulo · Resoluciones",
    "pendiente": "Módulo · Cola",
}

_MARCAS = tuple(EMOJI_TIPO.values())


def _hospital() -> str:
    return getattr(config, "NOMBRE_HOSPITAL", None) or "Hospital General"


def _footer(tipo: str = "neutral", extra: str = "") -> str:
    parts = [f"🖥️  {_hospital()}  ·  Sistema de gestión"]
    area = _AREA.get(tipo)
    if area:
        parts.append(area)
    if extra and str(extra).strip():
        parts.append(str(extra).strip())
    return "  │  ".join(parts)


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
            emb.set_author(name=f"Operador · {nombre}", icon_url=icon)
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
        descripcion
        or (
            "**Estado:** exitoso\n\n"
            "La acción se registró bien en el sistema del hospital.\n"
            "Ya puedes seguir con el siguiente paso."
        ),
        autor=autor,
    )


def embed_error_rapido(titulo: str, descripcion: str) -> discord.Embed:
    return crear_embed(
        "error",
        titulo or "Operación detenida",
        descripcion
        or (
            "**Estado:** error\n\n"
            "El sistema no pudo terminar esta acción.\n\n"
            "**Qué hacer**\n"
            "1️⃣ Revisa que los datos estén bien\n"
            "2️⃣ Confirma que tienes permiso\n"
            "3️⃣ Inténtalo de nuevo\n\n"
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
        "**Estado:** acceso denegado\n\n"
        "Tu cuenta no tiene permiso para este módulo del sistema.\n"
        "Solo personal autorizado puede usarlo."
    )
    if requerido:
        cuerpo += f"\n\n**Permiso necesario**\n`{requerido}`"
    cuerpo += (
        "\n\nSi crees que es un error, habla con RRHH, tu superior "
        "o la Dirección General."
    )
    return crear_embed("error", "Acceso denegado", cuerpo)


def embed_validacion(mensaje: str) -> discord.Embed:
    return crear_embed(
        "aviso",
        "Datos no válidos",
        mensaje
        or (
            "**Estado:** validación fallida\n\n"
            "Falta información o algún dato está mal escrito.\n"
            "Corrige el formulario y vuelve a enviarlo."
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
        titulo = "Verificación completada"
        desc = (
            f"**Estado:** aprobado\n\n"
            f"La cuenta de Roblox quedó **vinculada** al personal del hospital.\n"
            f"Bienvenido/a a **{_hospital()}**."
        )
        tipo = "whitelist"
        estado = "✅ Aprobado"
    else:
        titulo = "Verificación rechazada"
        desc = (
            f"**Estado:** rechazado\n\n"
            f"La verificación no pasó.\n"
            f"Corrige los datos y vuelve a postularte según las reglas."
        )
        tipo = "rechazado"
        estado = "❌ Rechazado"

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
            ("ID sistema", f"`{user_id}`", True),
        ],
    )

    if created and created != "—":
        try:
            from datetime import datetime

            dt = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
            created_fmt = dt.strftime("%d/%m/%Y")
        except Exception:
            created_fmt = str(created)[:10]
        embed_campo(emb, "Alta de cuenta", created_fmt)

    embed_campo(emb, "Resultado", f"**{estado}**")
    if staff:
        embed_campo(emb, "Revisado por", staff.mention)

    if profile_url:
        emb.add_field(
            name="Enlace",
            value=f"[Abrir perfil Roblox]({profile_url})",
            inline=False,
        )

    emb.set_footer(text=_footer("whitelist", "Admisión"))
    return emb
