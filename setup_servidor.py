# -*- coding: utf-8 -*-
"""
setup_servidor.py — Organigrama + canales con diseño →【emoji】nombre
NO toca reglamentos guardados.
"""
from __future__ import annotations

import asyncio
import re
from typing import Dict, List, Optional, Tuple

import discord
from discord import app_commands
from discord.ext import commands

import roles_setup
from estilos import crear_embed

# Diseño oficial: →【emoji】nombre

ESTRUCTURA: List[Tuple[str, List[Tuple[str, str, str]]]] = [
    # (categoría, [(nombre_completo, base_slug, descripción), ...])
    (
        "→【👋🏻】INGRESO",
        [
            ("→【👋🏻】bienvenida", "bienvenida", "Bienvenida automática al entrar."),
            ("→【✅】verificacion", "verificacion", "Verificación Roblox / whitelist."),
            ("→【📋】aceptar-reglas", "aceptar-reglas", "Aceptar reglas → rol Miembro."),
        ],
    ),
    (
        "→【📜】NORMATIVAS",
        [
            ("→【📜】normativa-rp", "normativa-rp", "Normativa de roleplay."),
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
            ("→【🆘】ayuda", "ayuda", "Dudas y orientación."),
            ("→【💡】sugerencias", "sugerencias", "Sugerencias de la comunidad."),
        ],
    ),
    (
        "→【🎭】ROLEPLAY",
        [
            ("→【🏥】rp-hospital", "rp-hospital", "RP principal del hospital."),
            ("→【🚑】rp-urgencias", "rp-urgencias", "RP de urgencias."),
            ("→【🛏️】rp-plantas", "rp-plantas", "RP de plantas / hospitalización."),
            ("→【📝】rp-reportes", "rp-reportes", "Reportes y bitácora de RP."),
            ("→【📡】rp-radio", "rp-radio", "Radio / códigos RP."),
        ],
    ),
    (
        "→【🎫】TICKETS Y REPORTES",
        [
            ("→【🎫】abrir-ticket", "abrir-ticket", "Panel para abrir tickets."),
            ("→【🚨】reportar", "reportar", "Reportar usuarios o incidencias."),
            ("→【🐛】bugs", "bugs", "Reportar bugs del bot o del servidor."),
            ("→【😠】quejas", "quejas", "Quejas formales."),
        ],
    ),
    (
        "→【🖥️】DIRECCIÓN GENERAL",
        [
            ("→【🖥️】dir-general", "dir-general", "Dirección General."),
            ("→【📢】anuncios-direcciones", "anuncios-direcciones", "Anuncios entre direcciones."),
        ],
    ),
    (
        "→【🏛️】CANCILLERÍA",
        [
            ("→【🏛️】dir-cancilleria", "dir-cancilleria", "Canal oficial de Cancillería."),
            ("→【👔】ejecutivos", "ejecutivos", "Sala de ejecutivos / alta dirección."),
            ("→【⚜️】canciller", "canciller", "Canal operativo del Canciller."),
            ("→【🔰】vice-canciller", "vice-canciller", "Canal operativo del Vice Canciller."),
            ("→【📡】operaciones", "operaciones", "Coordinación de operaciones."),
            ("→【📨】citatorios", "citatorios", "Citatorios y accesos especiales."),
            ("→【📜】ordenes-ejecutivas", "ordenes-ejecutivas", "Órdenes y directivas."),
            ("→【📅】agenda-ejecutiva", "agenda-ejecutiva", "Agenda y prioridades ejecutivas."),
        ],
    ),
    (
        "→【📚】DOCENCIA",
        [
            ("→【📚】dir-docencia", "dir-docencia", "Dirección de Docencia."),
            ("→【🎓】solicitudes-certificados", "solicitudes-certificados", "Solicitudes de certificados."),
            ("→【✍️】firmas-pendientes", "firmas-pendientes", "Firmas pendientes."),
            ("→【📖】materiales-estudio", "materiales-estudio", "Material de certificaciones."),
            ("→【📘】capacitaciones", "capacitaciones", "Capacitaciones / postulación."),
        ],
    ),
    (
        "→【🩺】DIRECCIÓN MÉDICA",
        [
            ("→【🩺】dir-medica", "dir-medica", "Dirección Médica."),
            ("→【📂】expedientes", "expedientes", "Expedientes clínicos (staff)."),
            ("→【🏥】licencias-medicas", "licencias-medicas", "Licencias médicas."),
            ("→【🧑‍⚕️】pacientes", "pacientes", "Gestión de pacientes RP."),
        ],
    ),
    (
        "→【💉】ENFERMERÍA",
        [
            ("→【💉】dir-enfermeria", "dir-enfermeria", "Dirección de Enfermería."),
            ("→【🗓️】turnos-enfermeria", "turnos-enfermeria", "Turnos de enfermería."),
        ],
    ),
    (
        "→【👥】RECURSOS HUMANOS",
        [
            ("→【👥】dir-rrhh", "dir-rrhh", "Recursos Humanos."),
            ("→【⏸️】solicitudes-inactividad", "solicitudes-inactividad", "Inactividad justificada."),
            ("→【🎤】entrevistas", "entrevistas", "Entrevistas de ingreso."),
            ("→【🚪】despidos", "despidos", "Procesos de despido."),
            ("→【⚠️】sanciones", "sanciones", "Sanciones de personal."),
            ("→【🔍】investigaciones", "investigaciones", "Investigaciones internas."),
        ],
    ),
    (
        "→【📦】LOGÍSTICA",
        [
            ("→【📦】dir-logistica", "dir-logistica", "Dirección de Logística."),
            ("→【📦】inventario", "inventario", "Inventario / suministros."),
        ],
    ),
    (
        "→【🛡️】SEGURIDAD",
        [
            ("→【🛡️】dir-seguridad", "dir-seguridad", "Departamento de Seguridad."),
            ("→【🚨】codigos-seguridad", "codigos-seguridad", "Códigos y alertas."),
        ],
    ),
    (
        "→【📝】POSTULACIONES",
        [
            ("→【🩺】postulaciones-medica", "postulaciones-medica", "Postulaciones área médica."),
            ("→【🔬】postulaciones-especialidad", "postulaciones-especialidad", "Postulaciones a especialidades."),
            ("→【📋】postulaciones-administrativa", "postulaciones-administrativa", "Postulaciones administrativas."),
        ],
    ),
    (
        "→【🛒】ECONOMÍA Y TIENDA",
        [
            ("→【🛒】tienda", "tienda", "Catálogo / tienda."),
            ("→【💰】economia", "economia", "Economía y salarios."),
        ],
    ),
    (
        "→【📅】REUNIONES",
        [
            ("→【📅】reuniones", "reuniones", "Convocatorias de reuniones."),
            ("→【📄】actas-reuniones", "actas-reuniones", "Actas y resúmenes."),
        ],
    ),
    (
        "→【📁】LOGS",
        [
            ("→【🎫】log-tickets", "log-tickets", "Transcripciones de tickets."),
            ("→【✅】log-verificaciones", "log-verificaciones", "Verificaciones / whitelist."),
            ("→【📥】log-solicitudes", "log-solicitudes", "Solicitudes generales."),
            ("→【✔️】aprobaciones-rrhh", "aprobaciones-rrhh", "Aprobaciones RRHH."),
            ("→【📝】log-postulaciones", "log-postulaciones", "Postulaciones registradas."),
            ("→【😠】log-quejas", "log-quejas", "Registro de quejas."),
            ("→【⚠️】log-sanciones", "log-sanciones", "Registro de sanciones."),
            ("→【🔍】log-investigaciones", "log-investigaciones", "Registro de investigaciones."),
            ("→【🎓】log-certificados", "log-certificados", "Certificados emitidos."),
            ("→【⏸️】log-inactividad", "log-inactividad", "Inactividades."),
            ("→【🚪】log-despidos", "log-despidos", "Despidos registrados."),
            ("→【🐛】log-reportes", "log-reportes", "Reportes y bugs."),
            ("→【💰】log-economia", "log-economia", "Movimientos económicos."),
            ("→【🤖】log-general", "log-general", "Logs generales del bot."),
        ],
    ),
    (
        "→【🛡️】STAFF",
        [
            ("→【🛡️】staff-general", "staff-general", "Chat del staff."),
            ("→【📢】staff-anuncios", "staff-anuncios", "Anuncios solo staff."),
            ("→【🚨】staff-alertas", "staff-alertas", "Alertas urgentes staff."),
        ],
    ),
    (
        "→【⚙️】ADMINISTRACIÓN",
        [
            ("→【⚙️】admin-only", "admin-only", "Solo Owner / Admin."),
            ("→【🤖】bot-comandos", "bot-comandos", "Canal técnico del bot."),
            ("→【📡】bot-status", "bot-status", "Estado / control del bot."),
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

_CATS_PRIVADAS = {
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


def _base_de_nombre(nombre: str) -> str:
    """Extrae el slug base: '→【👋🏻】bienvenida' → 'bienvenida'."""
    n = (nombre or "").strip()
    # quitar flecha y bloque 【...】
    n = re.sub(r"^→\s*", "", n)
    n = re.sub(r"【[^】]*】\s*", "", n)
    return n.strip().lower()


async def _asegurar_categoria(
    guild: discord.Guild,
    nombre: str,
    overwrites: Optional[Dict] = None,
) -> discord.CategoryChannel:
    # Match exacto o por texto sin flecha/emoji
    base_cat = _base_de_nombre(nombre).lower()
    for c in guild.categories:
        if c.name == nombre:
            return c
        if _base_de_nombre(c.name).lower() == base_cat:
            try:
                await c.edit(name=nombre, reason="Diseño →【emoji】nombre")
            except Exception:
                pass
            return c
    kwargs = {"reason": "Setup servidor"}
    if overwrites:
        kwargs["overwrites"] = overwrites
    return await guild.create_category(nombre, **kwargs)


async def _asegurar_canal(
    guild: discord.Guild,
    nombre: str,
    base: str,
    category: discord.CategoryChannel,
    overwrites: Optional[Dict] = None,
) -> discord.TextChannel:
    base_l = (base or _base_de_nombre(nombre)).lower()

    # 1) Nombre exacto en la categoría
    for ch in guild.text_channels:
        if ch.name == nombre and ch.category_id == category.id:
            return ch

    # 2) Mismo base en la categoría → renombrar al diseño
    for ch in guild.text_channels:
        if ch.category_id != category.id:
            continue
        if _base_de_nombre(ch.name) == base_l or (ch.name or "").lower() == base_l:
            try:
                await ch.edit(name=nombre, reason="Diseño →【emoji】nombre")
            except Exception:
                pass
            return ch

    # 3) Mismo base en cualquier categoría → mover + renombrar
    for ch in guild.text_channels:
        if _base_de_nombre(ch.name) == base_l or (ch.name or "").lower() == base_l:
            try:
                await ch.edit(
                    name=nombre,
                    category=category,
                    reason="Diseño →【emoji】nombre",
                )
            except Exception:
                try:
                    await ch.edit(name=nombre, reason="Diseño →【emoji】nombre")
                except Exception:
                    pass
            return ch

    kwargs = {"category": category, "reason": "Setup servidor"}
    if overwrites:
        kwargs["overwrites"] = overwrites
    return await guild.create_text_channel(nombre, **kwargs)


def _overwrites_privada(guild: discord.Guild) -> Dict:
    ow: Dict = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
    }
    me = guild.me
    if me:
        ow[me] = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            manage_messages=True,
            embed_links=True,
            attach_files=True,
            read_message_history=True,
        )
    return ow


async def crear_estructura_canales(guild: discord.Guild) -> List[str]:
    lineas: List[str] = []
    creados = 0
    existentes = 0
    renombrados = 0

    for cat_nombre, canales in ESTRUCTURA:
        try:
            privada = cat_nombre in _CATS_PRIVADAS
            ow = _overwrites_privada(guild) if privada else None
            cat = await _asegurar_categoria(guild, cat_nombre, overwrites=ow)
            lineas.append(f"**{cat_nombre}**")
            await asyncio.sleep(0.3)

            for nombre, base, desc in canales:
                try:
                    antes_nombres = {ch.id: ch.name for ch in guild.text_channels}
                    ch = await _asegurar_canal(
                        guild,
                        nombre,
                        base,
                        cat,
                        overwrites=ow if privada else None,
                    )
                    prev = antes_nombres.get(ch.id)
                    if prev is None:
                        creados += 1
                        lineas.append(f"  · {ch.mention} — {desc}")
                        try:
                            emb = crear_embed("info", base.replace("-", " ").title(), desc)
                            await ch.send(embed=emb)
                        except Exception:
                            pass
                    elif prev != nombre:
                        renombrados += 1
                        lineas.append(f"  · {ch.mention} _(diseño aplicado)_")
                    else:
                        existentes += 1
                        lineas.append(f"  · {ch.mention} _(ok)_")

                    area = _MAPA_DIRECCION.get(base)
                    if area:
                        try:
                            import canales_direccion

                            canales_direccion.guardar_canal(area, ch.id, guild.id)
                        except Exception:
                            pass

                    tipo_log = _MAPA_LOG.get(base)
                    if tipo_log:
                        try:
                            import logs_store

                            logs_store.set_canal(tipo_log, ch.id)
                        except Exception:
                            pass

                    await asyncio.sleep(0.35)
                except Exception as e:
                    lineas.append(f"  · ❌ `{nombre}`: {e}")
        except Exception as e:
            lineas.append(f"❌ Categoría `{cat_nombre}`: {e}")

    lineas.append("")
    lineas.append(
        f"**Resumen:** 🆕 {creados} · ✏️ {renombrados} diseño · ✓ {existentes} ok"
    )
    lineas.append("_Reglamentos guardados no se modifican._")
    return lineas


def _preview_texto() -> str:
    parts = []
    total = 0
    for cat, canales in ESTRUCTURA:
        parts.append(f"**{cat}** ({len(canales)})")
        total += len(canales)
        for nombre, _, _ in canales:
            parts.append(f"  · `{nombre}`")
    parts.append("")
    parts.append(f"Total: **{len(ESTRUCTURA)}** categorías · **{total}** canales")
    parts.append("Diseño: `→【emoji】nombre`")
    return "\n".join(parts)[:3900]


def registrar(bot: commands.Bot) -> None:
    try:
        bot.tree.remove_command("setup_servidor")
    except Exception:
        pass

    @bot.tree.command(
        name="setup_servidor",
        description="[Fundador] Roles + canales con diseño →【emoji】nombre",
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
                embed=crear_embed(
                    "info", "Vista previa /setup_servidor", _preview_texto()
                ),
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
            lineas.append("**—— Canales ——**")
            lineas.extend(await crear_estructura_canales(interaction.guild))
        except Exception as e:
            lineas.append(f"❌ Canales: {e}")

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

    print("[setup_servidor] OK — diseño →【emoji】nombre")
