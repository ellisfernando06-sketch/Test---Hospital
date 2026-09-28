# -*- coding: utf-8 -*-
"""
estilos.py — Identidad visual GOD-TIER del hospital.
Acabado tecnológico, elegante y ultra premium.
Solo presentación visual (firma API compatible).
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Tuple

import discord

import config

# ═══════════════════════════════════════════════════════════════════════════
# PALETA GOD-TIER — tech medical (profundos, luminosos, precisos)
# ═══════════════════════════════════════════════════════════════════════════
COLORES: Dict[str, int] = {
    "exito": 0x00C9A7,        # Aqua success
    "error": 0xFF4D6D,        # Neon clinical red
    "aviso": 0xFFB020,        # Gold alert
    "info": 0x3D8BFF,         # Electric blue
    "neutral": 0x8B9CB3,      # Steel mist
    "medico": 0x00E5C0,       # Cyan medical
    "finanzas": 0xFFD166,     # Soft gold
    "sancion": 0xB388FF,      # Violet justice
    "investigacion": 0x9B5DE5,# Purple research
    "rrhh": 0x4CC9F0,         # Sky personnel
    "logistica": 0xF77F00,    # Amber logistics
    "seguridad": 0x4361EE,    # Deep security blue
    "admin": 0x7209B7,        # Royal admin
    "anuncio": 0x4EA8DE,      # Broadcast blue
    "ticket": 0x48CAE4,       # Support cyan
    "citatorio": 0xF72585,    # Magenta formal
    "certificacion": 0x06D6A0,# Emerald cert
    "inactividad": 0x6C757D,  # Soft graphite
    "licencia": 0x4895EF,     # License blue
    "estado": 0x00F5D4,       # System teal
    "roblox": 0x3D8BFF,
    "whitelist": 0x00C9A7,
    "aprobado": 0x00C9A7,
    "rechazado": 0xFF4D6D,
    "pendiente": 0xFFB020,
}

EMOJI_TIPO: Dict[str, str] = {
    "exito": "◈",
    "error": "◇",
    "aviso": "◎",
    "info": "◉",
    "medico": "⚕",
    "finanzas": "◈",
    "sancion": "⚖",
    "investigacion": "◈",
    "rrhh": "◎",
    "logistica": "▣",
    "seguridad": "⬡",
    "admin": "⬢",
    "anuncio": "◈",
    "ticket": "◇",
    "citatorio": "◎",
    "certificacion": "✦",
    "inactividad": "⊘",
    "licencia": "◈",
    "estado": "⬡",
    "neutral": "◇",
    "roblox": "◉",
    "whitelist": "✦",
    "aprobado": "◈",
    "rechazado": "◇",
    "pendiente": "◎",
}

# Prefijos visuales de título (marca tech)
_PREFIX: Dict[str, str] = {
    "exito": "『 OK 』",
    "error": "『 ERR 』",
    "aviso": "『 ALERT 』",
    "info": "『 INFO 』",
    "medico": "『 CLIN 』",
    "finanzas": "『 FIN 』",
    "sancion": "『 REG 』",
    "investigacion": "『 DOC 』",
    "rrhh": "『 HR 』",
    "logistica": "『 LOG 』",
    "seguridad": "『 SEC 』",
    "admin": "『 SYS 』",
    "anuncio": "『 COM 』",
    "ticket": "『 TKT 』",
    "citatorio": "『 CIT 』",
    "certificacion": "『 CERT 』",
    "inactividad": "『 IDLE 』",
    "licencia": "『 MED 』",
    "estado": "『 CORE 』",
    "neutral": "『 HOSP 』",
    "roblox": "『 ID 』",
    "whitelist": "『 ADM 』",
    "aprobado": "『 OK 』",
    "rechazado": "『 DENY 』",
    "pendiente": "『 WAIT 』",
}

_AREA: Dict[str, str] = {
    "exito": "OPERATIONS",
    "error": "INCIDENT CONTROL",
    "aviso": "SYSTEM ALERT",
    "info": "INTELLIGENCE",
    "neutral": "HOSPITAL OS",
    "medico": "CLINICAL UNIT",
    "finanzas": "FINANCE CORE",
    "sancion": "DISCIPLINE MATRIX",
    "investigacion": "RESEARCH & TRAINING",
    "rrhh": "HUMAN RESOURCES",
    "logistica": "SUPPLY CHAIN",
    "seguridad": "SECURITY GRID",
    "admin": "COMMAND BRIDGE",
    "anuncio": "BROADCAST",
    "ticket": "SUPPORT DESK",
    "citatorio": "FORMAL SUMMONS",
    "certificacion": "ACCREDITATION",
    "inactividad": "PERSONNEL MONITOR",
    "licencia": "MEDICAL LEAVE",
    "estado": "CORE STATUS",
    "roblox": "IDENTITY LINK",
    "whitelist": "ADMISSION GATE",
    "aprobado": "RESOLUTION",
    "rechazado": "RESOLUTION",
    "pendiente": "QUEUE",
}


def _hospital() -> str:
    return getattr(config, "NOMBRE_HOSPITAL", None) or "Hospital General"


def _line() -> str:
    return "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


def _footer(tipo: str = "neutral", extra: str = "") -> str:
    area = _AREA.get(tipo, "HOSPITAL OS")
    base = f"⬡  {_hospital().upper()}  │  {area}"
    if extra and extra.strip():
        base += f"  │  {extra.strip()}"
    return base


def _title(titulo: str, tipo: str) -> str:
    # Si ya trae marca 『 』, no duplicar
    if "『" in titulo or "』" in titulo:
        return titulo
    prefix = _PREFIX.get(tipo, "『 HOSP 』")
    return f"{prefix}  {titulo}"


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

    # Descripción con marco tech si hay contenido
    desc = (descripcion or "").strip()
    if desc and not desc.startswith("━") and not desc.startswith("`"):
        desc = f"{_line()}\n{desc}\n{_line()}"

    emb = discord.Embed(
        title=_title(titulo, key),
        description=desc or None,
        color=color,
        timestamp=discord.utils.utcnow(),
    )

    if autor is not None:
        try:
            nombre = getattr(autor, "display_name", None) or str(autor)
            icon = getattr(getattr(autor, "display_avatar", None), "url", None)
            emb.set_author(name=f"▸ {nombre}", icon_url=icon)
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
    for n, v, i in campos:
        embed_campo(emb, n, v, i)
    return emb


def embed_exito_rapido(
    titulo: str,
    descripcion: str,
    autor: Optional[discord.abc.User] = None,
) -> discord.Embed:
    return crear_embed(
        "exito",
        titulo or "Procedimiento sincronizado",
        descripcion
        or "La operación fue registrada en el núcleo hospitalario con integridad verificada.",
        autor=autor,
    )


def embed_error_rapido(titulo: str, descripcion: str) -> discord.Embed:
    return crear_embed(
        "error",
        titulo or "Secuencia interrumpida",
        descripcion
        or (
            "El núcleo detuvo la operación por una validación de seguridad.\n\n"
            "*Revise los parámetros e intente de nuevo. Si el fallo persiste, "
            "eleve el incidente a Dirección de Sistemas.*"
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
        "**Acceso denegado por matriz de privilegios.**\n\n"
        "Su perfil no posee la clave de autorización exigida para este módulo."
    )
    if requerido:
        cuerpo += f"\n\n**Clave requerida**\n```\n{requerido}\n```"
    cuerpo += (
        "\n*Si cree que se trata de un error de asignación, contacte a "
        "Dirección General o al Gerente Developer.*"
    )
    return crear_embed("error", "Privilegios insuficientes", cuerpo)


def embed_validacion(mensaje: str) -> discord.Embed:
    return crear_embed(
        "aviso",
        "Validación de entrada",
        mensaje
        or (
            "Uno o más campos no superaron el protocolo de validación.\n"
            "Corrija los datos y reintente el envío."
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
        titulo = "Identidad vinculada"
        desc = (
            f"**Gate de admisión · RESOLUCIÓN POSITIVA**\n\n"
            f"La identidad externa fue **verificada y enlazada** al expediente digital.\n"
            f"Bienvenido/a al núcleo de **{_hospital()}**."
        )
        tipo = "whitelist"
        estado = "``` PASS ```"
    else:
        titulo = "Identidad rechazada"
        desc = (
            f"**Gate de admisión · RESOLUCIÓN NEGATIVA**\n\n"
            f"La verificación **no superó** el protocolo de ingreso.\n"
            f"Puede corregir datos y reintentar según normativa."
        )
        tipo = "rechazado"
        estado = "``` FAIL ```"

    emb = crear_embed(tipo, titulo, desc, autor=discord_user)
    if profile_url:
        emb.url = profile_url
    if avatar_url:
        emb.set_thumbnail(url=avatar_url)

    embed_campos(
        emb,
        [
            ("▸ Usuario", f"`{username}`", True),
            ("▸ Display", f"**{display}**", True),
            ("▸ UID", f"`{user_id}`", True),
        ],
    )

    if created and created != "—":
        try:
            from datetime import datetime

            dt = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
            created_fmt = dt.strftime("%d/%m/%Y")
        except Exception:
            created_fmt = str(created)[:10]
        embed_campo(emb, "▸ Alta", created_fmt)

    embed_campo(emb, "▸ Resolución", estado)
    if staff:
        embed_campo(emb, "▸ Evaluador", staff.mention)

    if profile_url:
        emb.add_field(
            name="▸ Enlace externo",
            value=f"[Abrir perfil Roblox]({profile_url})",
            inline=False,
        )

    emb.set_footer(text=_footer("whitelist", "ADMISSION GATE"))
    return emb
