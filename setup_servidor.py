# -*- coding: utf-8 -*-
"""
setup_servidor.py — Roles + canales texto/voz con diseño →【emoji】nombre
Voces y oficinas: solo roles de su sección.
NO toca reglamentos guardados.
"""
from __future__ import annotations

import asyncio
import re
from typing import Dict, List, Optional, Sequence, Set, Tuple

import discord
from discord import app_commands
from discord.ext import commands

import roles_setup
from estilos import crear_embed

# ═══════════════════════════════════════════════════════════════════════════════
# TEXTO: (categoría, [(nombre, base, descripción), ...])
# ═══════════════════════════════════════════════════════════════════════════════

ESTRUCTURA: List[Tuple[str, List[Tuple[str, str, str]]]] = [
    (
        "→【👋🏻】INGRESO",
        [
            ("→【👋🏻】bienvenida", "bienvenida", "Bienvenida automática."),
            ("→【✅】verificacion", "verificacion", "Verificación Roblox."),
            ("→【📋】aceptar-reglas", "aceptar-reglas", "Aceptar reglas → Miembro."),
        ],
    ),
    (
        "→【📜】NORMATIVAS",
        [
            ("→【📜】normativa-rp", "normativa-rp", "Normativa de RP."),
            ("→【📜】normativa-discord", "normativa-discord", "Normativa de Discord."),
            ("→【📜】normativa-general", "normativa-general", "Normativa general."),
            ("→【📜】normativa-hospitalaria", "normativa-hospitalaria", "Normativa hospitalaria."),
            ("→【📜】normativa-seguridad", "normativa-seguridad", "Normativa de seguridad."),
        ],
    ),
    (
        "→【💬】COMUNIDAD",
        [
            ("→【💬】general", "general", "Chat general."),
            ("→【📢】anuncios", "anuncios", "Anuncios públicos."),
            ("→【🆘】ayuda", "ayuda", "Ayuda."),
            ("→【💡】sugerencias", "sugerencias", "Sugerencias."),
        ],
    ),
    (
        "→【🎭】ROLEPLAY",
        [
            ("→【🏥】rp-hospital", "rp-hospital", "RP hospital."),
            ("→【🚑】rp-urgencias", "rp-urgencias", "RP urgencias."),
            ("→【🛏️】rp-plantas", "rp-plantas", "RP plantas."),
            ("→【📝】rp-reportes", "rp-reportes", "Reportes RP."),
            ("→【📡】rp-radio", "rp-radio", "Radio RP."),
        ],
    ),
    (
        "→【🎫】TICKETS Y REPORTES",
        [
            ("→【🎫】abrir-ticket", "abrir-ticket", "Abrir tickets."),
            ("→【🚨】reportar", "reportar", "Reportar."),
            ("→【🐛】bugs", "bugs", "Bugs."),
            ("→【😠】quejas", "quejas", "Quejas."),
        ],
    ),
    (
        "→【🖥️】DIRECCIÓN GENERAL",
        [
            ("→【🖥️】dir-general", "dir-general", "Dirección General."),
            ("→【📢】anuncios-direcciones", "anuncios-direcciones", "Anuncios direcciones."),
        ],
    ),
    (
        "→【🏛️】CANCILLERÍA",
        [
            ("→【🏛️】dir-cancilleria", "dir-cancilleria", "Cancillería."),
            ("→【👔】ejecutivos", "ejecutivos", "Ejecutivos."),
            ("→【⚜️】canciller", "canciller", "Canciller."),
            ("→【🔰】vice-canciller", "vice-canciller", "Vice Canciller."),
            ("→【📡】operaciones", "operaciones", "Operaciones."),
            ("→【📨】citatorios", "citatorios", "Citatorios."),
            ("→【📜】ordenes-ejecutivas", "ordenes-ejecutivas", "Órdenes ejecutivas."),
            ("→【📅】agenda-ejecutiva", "agenda-ejecutiva", "Agenda ejecutiva."),
        ],
    ),
    (
        "→【📚】DOCENCIA",
        [
            ("→【📚】dir-docencia", "dir-docencia", "Docencia."),
            ("→【🎓】solicitudes-certificados", "solicitudes-certificados", "Certificados."),
            ("→【✍️】firmas-pendientes", "firmas-pendientes", "Firmas."),
            ("→【📖】materiales-estudio", "materiales-estudio", "Materiales."),
            ("→【📘】capacitaciones", "capacitaciones", "Capacitaciones."),
        ],
    ),
    (
        "→【🩺】DIRECCIÓN MÉDICA",
        [
            ("→【🩺】dir-medica", "dir-medica", "Dirección Médica."),
            ("→【📂】expedientes", "expedientes", "Expedientes."),
            ("→【🏥】licencias-medicas", "licencias-medicas", "Licencias."),
            ("→【🧑‍⚕️】pacientes", "pacientes", "Pacientes."),
        ],
    ),
    (
        "→【💉】ENFERMERÍA",
        [
            ("→【💉】dir-enfermeria", "dir-enfermeria", "Enfermería."),
            ("→【🗓️】turnos-enfermeria", "turnos-enfermeria", "Turnos."),
        ],
    ),
    (
        "→【👥】RECURSOS HUMANOS",
        [
            ("→【👥】dir-rrhh", "dir-rrhh", "RRHH."),
            ("→【⏸️】solicitudes-inactividad", "solicitudes-inactividad", "Inactividad."),
            ("→【🎤】entrevistas", "entrevistas", "Entrevistas."),
            ("→【🚪】despidos", "despidos", "Despidos."),
            ("→【⚠️】sanciones", "sanciones", "Sanciones."),
            ("→【🔍】investigaciones", "investigaciones", "Investigaciones."),
        ],
    ),
    (
        "→【📦】LOGÍSTICA",
        [
            ("→【📦】dir-logistica", "dir-logistica", "Logística."),
            ("→【📦】inventario", "inventario", "Inventario."),
        ],
    ),
    (
        "→【🛡️】SEGURIDAD",
        [
            ("→【🛡️】dir-seguridad", "dir-seguridad", "Seguridad."),
            ("→【🚨】codigos-seguridad", "codigos-seguridad", "Códigos."),
        ],
    ),
    (
        "→【📝】POSTULACIONES",
        [
            ("→【🩺】postulaciones-medica", "postulaciones-medica", "Postulaciones médicas."),
            ("→【🔬】postulaciones-especialidad", "postulaciones-especialidad", "Especialidades."),
            ("→【📋】postulaciones-administrativa", "postulaciones-administrativa", "Administrativas."),
        ],
    ),
    (
        "→【🛒】ECONOMÍA Y TIENDA",
        [
            ("→【🛒】tienda", "tienda", "Tienda."),
            ("→【💰】economia", "economia", "Economía."),
        ],
    ),
    (
        "→【📅】REUNIONES",
        [
            ("→【📅】reuniones", "reuniones", "Convocatorias."),
            ("→【📄】actas-reuniones", "actas-reuniones", "Actas."),
        ],
    ),
    (
        "→【📁】LOGS",
        [
            ("→【🎫】log-tickets", "log-tickets", "Log tickets."),
            ("→【✅】log-verificaciones", "log-verificaciones", "Log verificaciones."),
            ("→【📥】log-solicitudes", "log-solicitudes", "Log solicitudes."),
            ("→【✔️】aprobaciones-rrhh", "aprobaciones-rrhh", "Aprobaciones RRHH."),
            ("→【📝】log-postulaciones", "log-postulaciones", "Log postulaciones."),
            ("→【😠】log-quejas", "log-quejas", "Log quejas."),
            ("→【⚠️】log-sanciones", "log-sanciones", "Log sanciones."),
            ("→【🔍】log-investigaciones", "log-investigaciones", "Log investigaciones."),
            ("→【🎓】log-certificados", "log-certificados", "Log certificados."),
            ("→【⏸️】log-inactividad", "log-inactividad", "Log inactividad."),
            ("→【🚪】log-despidos", "log-despidos", "Log despidos."),
            ("→【🐛】log-reportes", "log-reportes", "Log reportes."),
            ("→【💰】log-economia", "log-economia", "Log economía."),
            ("→【🤖】log-general", "log-general", "Log general."),
        ],
    ),
    (
        "→【🛡️】STAFF",
        [
            ("→【🛡️】staff-general", "staff-general", "Staff chat."),
            ("→【📢】staff-anuncios", "staff-anuncios", "Staff anuncios."),
            ("→【🚨】staff-alertas", "staff-alertas", "Staff alertas."),
        ],
    ),
    (
        "→【⚙️】ADMINISTRACIÓN",
        [
            ("→【⚙️】admin-only", "admin-only", "Solo admin."),
            ("→【🤖】bot-comandos", "bot-comandos", "Bot comandos."),
            ("→【📡】bot-status", "bot-status", "Bot status."),
        ],
    ),
]

# ═══════════════════════════════════════════════════════════════════════════════
# VOZ / ESCENARIO
# tipo: "voice" | "stage"
# keys: claves de roles que pueden ver/conectar (además de owner/admin/bot)
# ═══════════════════════════════════════════════════════════════════════════════

ESTRUCTURA_VOZ: List[Tuple[str, List[Tuple[str, str, str, Sequence[str]]]]] = [
    # (categoría, [(nombre, base, tipo, keys_roles), ...])
    (
        "→【🎙️】VOZ ROLEPLAY",
        [
            ("→【🎙️】rp-voz-hospital", "rp-voz-hospital", "voice", ("MIEMBRO", "COMUNIDAD")),
            ("→【🚑】rp-voz-urgencias", "rp-voz-urgencias", "voice", ("MIEMBRO", "COMUNIDAD")),
            ("→【🛏️】rp-voz-plantas", "rp-voz-plantas", "voice", ("MIEMBRO", "COMUNIDAD")),
            ("→【🔬】rp-voz-quirofano", "rp-voz-quirofano", "voice", ("MIEMBRO", "COMUNIDAD")),
            ("→【📡】rp-voz-radio", "rp-voz-radio", "voice", ("MIEMBRO", "COMUNIDAD")),
        ],
    ),
    (
        "→【🛡️】VOZ STAFF",
        [
            ("→【🛡️】staff-voz", "staff-voz", "voice",
             ("ADMIN", "ADMIN_JEFE", "CANCILLER", "VICE_CANCILLER", "DIR_GENERAL", "DIRECTOR_GENERAL")),
            ("→【📢】staff-briefing", "staff-briefing", "voice",
             ("ADMIN", "ADMIN_JEFE", "CANCILLER", "VICE_CANCILLER")),
            ("→【🚨】staff-alerta-voz", "staff-alerta-voz", "voice",
             ("ADMIN", "ADMIN_JEFE", "CANCILLER", "JEFE_SEGURIDAD")),
        ],
    ),
    (
        "→【🏢】OFICINAS DIRECTIVOS",
        [
            ("→【🖥️】oficina-dir-general", "oficina-dir-general", "voice",
             ("DIR_GENERAL", "DIRECTOR_GENERAL")),
            ("→【📚】oficina-dir-docencia", "oficina-dir-docencia", "voice",
             ("DIR_DOCENCIA", "DIRECTOR_DOCENCIA")),
            ("→【🩺】oficina-dir-medica", "oficina-dir-medica", "voice",
             ("DIR_MEDICO", "DIRECTOR_MEDICO")),
            ("→【💉】oficina-dir-enfermeria", "oficina-dir-enfermeria", "voice",
             ("DIR_ENFERMERIA", "DIRECTOR_ENFERMERIA")),
            ("→【👥】oficina-dir-rrhh", "oficina-dir-rrhh", "voice",
             ("DIR_RRHH", "DIRECTOR_RRHH")),
            ("→【📦】oficina-dir-logistica", "oficina-dir-logistica", "voice",
             ("DIR_LOGISTICA", "DIRECTOR_LOGISTICA")),
            ("→【🛡️】oficina-dir-seguridad", "oficina-dir-seguridad", "voice",
             ("JEFE_SEGURIDAD", "SUPERVISOR_SEGURIDAD")),
        ],
    ),
    (
        "→【🏛️】OFICINAS EJECUTIVAS",
        [
            ("→【⚜️】oficina-canciller", "oficina-canciller", "voice",
             ("CANCILLER", "PREFECTO_OPERACIONES")),
            ("→【🔰】oficina-vice-canciller", "oficina-vice-canciller", "voice",
             ("VICE_CANCILLER", "CANCILLER")),
            ("→【👔】sala-ejecutivos", "sala-ejecutivos", "voice",
             ("CANCILLER", "VICE_CANCILLER", "DIR_GENERAL", "DIRECTOR_GENERAL",
              "FUNDADOR_OWNER", "CO_OWNER", "OWNER")),
            ("→【📡】operaciones-voz", "operaciones-voz", "voice",
             ("CANCILLER", "VICE_CANCILLER", "DIR_GENERAL")),
        ],
    ),
    (
        "→【🎤】REUNIONES VOZ",
        [
            # Escenario (Stage): reunión general
            ("→【🎤】reunion-general", "reunion-general", "stage",
             ("MIEMBRO", "COMUNIDAD", "ADMIN", "CANCILLER", "DIR_GENERAL",
              "DIR_DOCENCIA", "DIR_MEDICO", "DIR_RRHH")),
            ("→【📅】reunion-staff", "reunion-staff", "voice",
             ("ADMIN", "ADMIN_JEFE", "CANCILLER", "VICE_CANCILLER", "DIR_GENERAL")),
            ("→【🏛️】reunion-ejecutiva", "reunion-ejecutiva", "voice",
             ("CANCILLER", "VICE_CANCILLER", "DIR_GENERAL", "FUNDADOR_OWNER", "CO_OWNER")),
            ("→【📚】reunion-docencia", "reunion-docencia", "voice",
             ("DIR_DOCENCIA", "DIRECTOR_DOCENCIA", "CANCILLER")),
        ],
    ),
]

_MAPA_DIRECCION: Dict[str, str] = {
    "dir-docencia": "docencia",
    "dir-medica": "medico",
    "dir-enfermeria": "enfermeria",
    "dir-rrhh": "rrhh",
    "dir-logistica": "logistica",
    "dir-general": "general",
    "dir-cancilleria": "cancilleria",
    "dir-seguridad": "seguridad",
    "solicitudes-inactividad": "inactividad",
    "log-verificaciones": "verificacion",
    "staff-general": "staff",
}

_MAPA_LOG: Dict[str, str] = {
    "log-tickets": "log_tickets",
    "log-solicitudes": "log_solicitudes",
    "aprobaciones-rrhh": "aprobaciones_rrhh",
    "log-postulaciones": "log_postulaciones",
    "log-quejas": "log_quejas",
    "log-sanciones": "log_sanciones",
    "log-investigaciones": "log_investigaciones",
    "log-general": "log_general",
}

_CATS_TEXTO_PRIVADAS = {
    "→【🖥️】DIRECCIÓN GENERAL",
    "→【🏛️】CANCILLERÍA",
    "→【📚】DOCENCIA",
    "→【🩺】DIRECCIÓN MÉDICA",
    "→【💉】ENFERMERÍA",
    "→【👥】RECURSOS HUMANOS",
    "→【📦】LOGÍSTICA",
    "→【🛡️】SEGURIDAD",
    "→【📁】LOGS",
    "→【🛡️】STAFF",
    "→【⚙️】ADMINISTRACIÓN",
    "→【📅】REUNIONES",
}

# Keys siempre con acceso a zonas privadas / voz restringida
_KEYS_SUPERIORES = (
    "FUNDADOR_OWNER",
    "CO_OWNER",
    "OWNER",
    "CANCILLER",
    "ADMIN_JEFE",
    "ADMIN",
)


def _base_de_nombre(nombre: str) -> str:
    n = (nombre or "").strip()
    n = re.sub(r"^→\s*", "", n)
    n = re.sub(r"【[^】]*】\s*", "", n)
    return n.strip().lower()


def _roles_por_keys(guild: discord.Guild, keys: Sequence[str]) -> List[discord.Role]:
    found: List[discord.Role] = []
    seen: Set[int] = set()
    try:
        import roles_store

        for k in keys:
            rid = None
            try:
                rid = roles_store.obtener_id_key(k)
            except Exception:
                pass
            if rid:
                r = guild.get_role(int(rid))
                if r and r.id not in seen:
                    found.append(r)
                    seen.add(r.id)
    except Exception:
        pass
    try:
        import roles_config

        nombres = getattr(roles_config, "KEYS_NOMBRES", {}) or {}
        for k in keys:
            nom = nombres.get(k)
            if not nom:
                continue
            nombre = nom[0] if isinstance(nom, (list, tuple)) else str(nom)
            for r in guild.roles:
                if r.id in seen:
                    continue
                if r.name == nombre or nombre.lower() in (r.name or "").lower():
                    found.append(r)
                    seen.add(r.id)
    except Exception:
        pass
    return found


def _ow_bot(guild: discord.Guild) -> Dict:
    ow: Dict = {}
    me = guild.me
    if me:
        ow[me] = discord.PermissionOverwrite(
            view_channel=True,
            connect=True,
            speak=True,
            send_messages=True,
            manage_messages=True,
            manage_channels=True,
            embed_links=True,
            attach_files=True,
            read_message_history=True,
            move_members=True,
            mute_members=True,
        )
    return ow


def _ow_seccion(
    guild: discord.Guild,
    keys: Sequence[str],
    *,
    voz: bool = False,
) -> Dict:
    """@everyone denegado; solo keys de la sección + superiores + bot."""
    ow: Dict = {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=False,
            connect=False,
            speak=False,
            send_messages=False,
        )
    }
    ow.update(_ow_bot(guild))

    keys_all = list(keys) + list(_KEYS_SUPERIORES)
    roles = _roles_por_keys(guild, keys_all)
    for r in roles:
        if voz:
            ow[r] = discord.PermissionOverwrite(
                view_channel=True,
                connect=True,
                speak=True,
                stream=True,
                use_voice_activation=True,
            )
        else:
            ow[r] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True,
            )
    return ow


def _ow_publica_texto(guild: discord.Guild) -> Optional[Dict]:
    return None  # defaults del servidor


async def _asegurar_categoria(
    guild: discord.Guild,
    nombre: str,
    overwrites: Optional[Dict] = None,
) -> discord.CategoryChannel:
    base_cat = _base_de_nombre(nombre).lower()
    for c in guild.categories:
        if c.name == nombre:
            if overwrites:
                try:
                    await c.edit(overwrites=overwrites, reason="Permisos sección")
                except Exception:
                    pass
            return c
        if _base_de_nombre(c.name).lower() == base_cat:
            try:
                await c.edit(
                    name=nombre,
                    overwrites=overwrites,
                    reason="Diseño →【emoji】nombre",
                )
            except Exception:
                try:
                    await c.edit(name=nombre, reason="Diseño →【emoji】nombre")
                except Exception:
                    pass
            return c
    kwargs = {"reason": "Setup servidor"}
    if overwrites:
        kwargs["overwrites"] = overwrites
    return await guild.create_category(nombre, **kwargs)


async def _asegurar_canal_texto(
    guild: discord.Guild,
    nombre: str,
    base: str,
    category: discord.CategoryChannel,
    overwrites: Optional[Dict] = None,
) -> discord.TextChannel:
    base_l = (base or _base_de_nombre(nombre)).lower()

    for ch in guild.text_channels:
        if ch.name == nombre and ch.category_id == category.id:
            if overwrites:
                try:
                    await ch.edit(overwrites=overwrites, reason="Permisos sección")
                except Exception:
                    pass
            return ch

    for ch in guild.text_channels:
        if ch.category_id == category.id and (
            _base_de_nombre(ch.name) == base_l or (ch.name or "").lower() == base_l
        ):
            try:
                await ch.edit(
                    name=nombre, overwrites=overwrites, reason="Diseño + permisos"
                )
            except Exception:
                try:
                    await ch.edit(name=nombre, reason="Diseño")
                except Exception:
                    pass
            return ch

    for ch in guild.text_channels:
        if _base_de_nombre(ch.name) == base_l or (ch.name or "").lower() == base_l:
            try:
                await ch.edit(
                    name=nombre,
                    category=category,
                    overwrites=overwrites,
                    reason="Diseño + permisos",
                )
            except Exception:
                pass
            return ch

    kwargs = {"category": category, "reason": "Setup servidor"}
    if overwrites:
        kwargs["overwrites"] = overwrites
    return await guild.create_text_channel(nombre, **kwargs)


async def _asegurar_voz(
    guild: discord.Guild,
    nombre: str,
    base: str,
    category: discord.CategoryChannel,
    tipo: str,
    overwrites: Optional[Dict] = None,
) -> discord.abc.GuildChannel:
    base_l = (base or _base_de_nombre(nombre)).lower()

    # Buscar en voz y stage
    candidatos = list(guild.voice_channels) + list(
        getattr(guild, "stage_channels", []) or []
    )

    for ch in candidatos:
        if ch.name == nombre and ch.category_id == category.id:
            if overwrites:
                try:
                    await ch.edit(overwrites=overwrites, reason="Permisos sección")
                except Exception:
                    pass
            return ch

    for ch in candidatos:
        if _base_de_nombre(ch.name) == base_l or (ch.name or "").lower() == base_l:
            try:
                await ch.edit(
                    name=nombre,
                    category=category,
                    overwrites=overwrites,
                    reason="Diseño + permisos voz",
                )
            except Exception:
                try:
                    await ch.edit(name=nombre, reason="Diseño voz")
                except Exception:
                    pass
            return ch

    kwargs = {"category": category, "reason": "Setup servidor voz"}
    if overwrites:
        kwargs["overwrites"] = overwrites

    if tipo == "stage":
        try:
            return await guild.create_stage_channel(nombre, **kwargs)
        except Exception:
            # Fallback a voz si el servidor no permite stage
            return await guild.create_voice_channel(nombre, **kwargs)
    return await guild.create_voice_channel(nombre, **kwargs)


async def crear_estructura_canales(guild: discord.Guild) -> List[str]:
    lineas: List[str] = []
    creados = renombrados = existentes = 0

    for cat_nombre, canales in ESTRUCTURA:
        try:
            privada = cat_nombre in _CATS_TEXTO_PRIVADAS
            # Texto privado: solo superiores por defecto en categoría;
            # canales de dirección se afinan al registrar (bot + staff con rol)
            ow_cat = (
                _ow_seccion(guild, (), voz=False) if privada else _ow_publica_texto(guild)
            )
            cat = await _asegurar_categoria(guild, cat_nombre, overwrites=ow_cat)
            lineas.append(f"**{cat_nombre}**")
            await asyncio.sleep(0.25)

            for nombre, base, desc in canales:
                try:
                    ow_ch = ow_cat if privada else None
                    # Canales de dirección: keys específicas
                    if base in _MAPA_DIRECCION:
                        area = _MAPA_DIRECCION[base]
                        keys_area = {
                            "docencia": ("DIR_DOCENCIA", "DIRECTOR_DOCENCIA"),
                            "medico": ("DIR_MEDICO", "DIRECTOR_MEDICO"),
                            "enfermeria": ("DIR_ENFERMERIA", "DIRECTOR_ENFERMERIA"),
                            "rrhh": ("DIR_RRHH", "DIRECTOR_RRHH"),
                            "logistica": ("DIR_LOGISTICA", "DIRECTOR_LOGISTICA"),
                            "general": ("DIR_GENERAL", "DIRECTOR_GENERAL"),
                            "cancilleria": ("CANCILLER", "VICE_CANCILLER"),
                            "seguridad": ("JEFE_SEGURIDAD", "SUPERVISOR_SEGURIDAD"),
                            "inactividad": ("DIR_RRHH", "DIRECTOR_RRHH", "CANCILLER"),
                            "verificacion": ("DIR_RRHH", "CANCILLER"),
                            "staff": ("ADMIN", "ADMIN_JEFE"),
                        }.get(area, ())
                        ow_ch = _ow_seccion(guild, keys_area, voz=False)

                    antes = {c.id: c.name for c in guild.text_channels}
                    ch = await _asegurar_canal_texto(
                        guild, nombre, base, cat, overwrites=ow_ch
                    )
                    prev = antes.get(ch.id)
                    if prev is None:
                        creados += 1
                        lineas.append(f"  · {ch.mention} — {desc}")
                        try:
                            await ch.send(
                                embed=crear_embed(
                                    "info", base.replace("-", " ").title(), desc
                                )
                            )
                        except Exception:
                            pass
                    elif prev != nombre:
                        renombrados += 1
                        lineas.append(f"  · {ch.mention} _(diseño)_")
                    else:
                        existentes += 1
                        lineas.append(f"  · {ch.mention} _(ok)_")

                    if base in _MAPA_DIRECCION:
                        try:
                            import canales_direccion

                            canales_direccion.guardar_canal(
                                _MAPA_DIRECCION[base], ch.id, guild.id
                            )
                        except Exception:
                            pass
                    if base in _MAPA_LOG:
                        try:
                            import logs_store

                            logs_store.set_canal(_MAPA_LOG[base], ch.id)
                        except Exception:
                            pass

                    await asyncio.sleep(0.3)
                except Exception as e:
                    lineas.append(f"  · ❌ `{nombre}`: {e}")
        except Exception as e:
            lineas.append(f"❌ `{cat_nombre}`: {e}")

    lineas.append("")
    lineas.append(
        f"**Texto:** 🆕 {creados} · ✏️ {renombrados} · ✓ {existentes}"
    )
    return lineas


async def crear_estructura_voz(guild: discord.Guild) -> List[str]:
    lineas: List[str] = []
    creados = existentes = 0

    for cat_nombre, canales in ESTRUCTURA_VOZ:
        try:
            # Categoría: denegar everyone; permitir unión de todas las keys de sus canales
            keys_cat: List[str] = []
            for _, _, _, keys in canales:
                keys_cat.extend(keys)
            ow_cat = _ow_seccion(guild, keys_cat, voz=True)
            cat = await _asegurar_categoria(guild, cat_nombre, overwrites=ow_cat)
            lineas.append(f"**{cat_nombre}**")
            await asyncio.sleep(0.3)

            for nombre, base, tipo, keys in canales:
                try:
                    ow = _ow_seccion(guild, keys, voz=True)
                    antes_ids = {c.id for c in guild.voice_channels} | {
                        c.id for c in getattr(guild, "stage_channels", []) or []
                    }
                    ch = await _asegurar_voz(
                        guild, nombre, base, cat, tipo, overwrites=ow
                    )
                    if ch.id not in antes_ids:
                        creados += 1
                        tag = "🎤 escenario" if tipo == "stage" else "🎙️ voz"
                        lineas.append(f"  · **{ch.name}** ({tag}) — solo roles de sección")
                    else:
                        existentes += 1
                        lineas.append(f"  · **{ch.name}** _(ok / permisos)_")
                    await asyncio.sleep(0.35)
                except Exception as e:
                    lineas.append(f"  · ❌ `{nombre}`: {e}")
        except Exception as e:
            lineas.append(f"❌ `{cat_nombre}`: {e}")

    lineas.append("")
    lineas.append(f"**Voz/Escenario:** 🆕 {creados} · ✓ {existentes}")
    lineas.append("_Solo acceden los roles de cada sección (+ Owner/Admin/Canciller)._")
    return lineas


def _preview_texto() -> str:
    parts = []
    t = v = 0
    for cat, canales in ESTRUCTURA:
        parts.append(f"**{cat}** ({len(canales)} texto)")
        t += len(canales)
        for n, _, _ in canales:
            parts.append(f"  · `{n}`")
    for cat, canales in ESTRUCTURA_VOZ:
        parts.append(f"**{cat}** ({len(canales)} voz)")
        v += len(canales)
        for n, _, tipo, _ in canales:
            tag = "escenario" if tipo == "stage" else "voz"
            parts.append(f"  · `{n}` ({tag})")
    parts.append("")
    parts.append(f"Texto: {t} · Voz/Stage: {v}")
    parts.append("Acceso voz/oficinas: solo roles de su sección.")
    return "\n".join(parts)[:3900]


def registrar(bot: commands.Bot) -> None:
    try:
        bot.tree.remove_command("setup_servidor")
    except Exception:
        pass

    @bot.tree.command(
        name="setup_servidor",
        description="[Fundador] Roles + canales texto/voz (acceso por sección)",
    )
    @app_commands.describe(dry_run="Vista previa sin crear nada")
    async def setup_servidor(
        interaction: discord.Interaction, dry_run: bool = False
    ):
        if not isinstance(interaction.user, discord.Member) or not interaction.guild:
            return await interaction.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )

        autorizado = False
        try:
            import permisos

            autorizado = permisos.member_tiene_alguna_key(
                interaction.user, "FUNDADOR_OWNER", "CO_OWNER", "OWNER"
            )
        except Exception:
            autorizado = interaction.user.guild_permissions.administrator

        if not autorizado:
            return await interaction.response.send_message(
                "❌ Solo **Fundador y Owner** o **Co-Owner**.", ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        if dry_run:
            return await interaction.followup.send(
                embed=crear_embed("info", "Vista previa", _preview_texto()),
                ephemeral=True,
            )

        lineas: List[str] = []
        try:
            lineas.append("**—— Roles ——**")
            lineas.extend(await roles_setup.configurar_organigrama(interaction.guild))
        except Exception as e:
            lineas.append(f"❌ Roles: {e}")

        try:
            lineas.append("")
            lineas.append("**—— Canales de texto ——**")
            lineas.extend(await crear_estructura_canales(interaction.guild))
        except Exception as e:
            lineas.append(f"❌ Texto: {e}")

        try:
            lineas.append("")
            lineas.append("**—— Voz / Escenario ——**")
            lineas.extend(await crear_estructura_voz(interaction.guild))
        except Exception as e:
            lineas.append(f"❌ Voz: {e}")

        lineas.append("")
        lineas.append("_Reglamentos guardados no se modifican._")

        texto = "\n".join(lineas)
        if len(texto) <= 3800:
            await interaction.followup.send(
                embed=crear_embed(
                    "exito", "✅ Setup completado", texto, autor=interaction.user
                ),
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                embed=crear_embed(
                    "exito", "✅ Setup (1/2)", texto[:3800], autor=interaction.user
                ),
                ephemeral=True,
            )
            await interaction.followup.send(
                embed=crear_embed("info", "Setup (2/2)", texto[3800:7600]),
                ephemeral=True,
            )

    print("[setup_servidor] OK — texto+voz+stage · permisos por sección")
