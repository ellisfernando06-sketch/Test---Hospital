# -*- coding: utf-8 -*-
"""
setup_servidor.py — Organigrama + categorías y canales del hospital.

- Direcciones en categorías separadas.
- Canales para todo lo que el bot usa (tickets, logs, quejas, bugs, etc.).
- NO toca data/reglamento.json ni reglamentos guardados.
"""
from __future__ import annotations

import asyncio
from typing import Dict, List, Optional, Tuple

import discord
from discord import app_commands
from discord.ext import commands

import roles_setup
from estilos import crear_embed

# ═══════════════════════════════════════════════════════════════════════════════
# Estructura: (nombre categoría, [(slug_canal, descripción), ...])
# ═══════════════════════════════════════════════════════════════════════════════

ESTRUCTURA: List[Tuple[str, List[Tuple[str, str]]]] = [
    (
        "【👋🏻】 ingreso",
        [
            ("bienvenida", "Bienvenida automática al entrar."),
            ("verificacion", "Verificación Roblox / whitelist."),
            ("aceptar-reglas", "Aceptar reglas → rol Miembro."),
        ],
    ),
    (
        "【📜】 normativas",
        [
            ("normativa-rp", "Normativa de roleplay."),
            ("normativa-discord", "Normativa de Discord."),
            ("normativa-general", "Normativa general."),
            ("normativa-hospitalaria", "Normativa hospitalaria."),
            ("normativa-seguridad", "Normativa de seguridad."),
        ],
    ),
    (
        "【💬】 comunidad",
        [
            ("general", "Chat general."),
            ("anuncios", "Anuncios públicos."),
            ("ayuda", "Dudas y orientación."),
            ("sugerencias", "Sugerencias de la comunidad."),
        ],
    ),
    (
        "【🎭】 roleplay",
        [
            ("rp-hospital", "RP principal del hospital."),
            ("rp-urgencias", "RP de urgencias."),
            ("rp-plantas", "RP de plantas / hospitalización."),
            ("rp-reportes", "Reportes y bitácora de RP."),
            ("rp-radio", "Radio / códigos RP."),
        ],
    ),
    (
        "【🎫】 tickets y reportes",
        [
            ("abrir-ticket", "Panel para abrir tickets."),
            ("reportar", "Reportar usuarios o incidencias."),
            ("bugs", "Reportar bugs del bot o del servidor."),
            ("quejas", "Quejas formales."),
        ],
    ),
    (
        "【🖥️】 dirección general",
        [
            ("dir-general", "Dirección General."),
            ("anuncios-direcciones", "Anuncios entre direcciones."),
        ],
    ),
    (
        "【🏛️】 cancillería",
        [
            ("dir-cancilleria", "Canal oficial de Cancillería (Canciller / Vice Canciller)."),
            ("ejecutivos", "Sala de ejecutivos / alta dirección."),
            ("canciller", "Canal operativo del Canciller."),
            ("vice-canciller", "Canal operativo del Vice Canciller."),
            ("operaciones", "Coordinación de operaciones del servidor."),
            ("citatorios", "Citatorios y accesos especiales."),
            ("ordenes-ejecutivas", "Órdenes y directivas de Cancillería."),
            ("agenda-ejecutiva", "Agenda, reuniones y prioridades ejecutivas."),
        ],
    ),
    (
        "【📚】 docencia",
        [
            ("dir-docencia", "Dirección de Docencia."),
            ("solicitudes-certificados", "Solicitudes de certificados."),
            ("firmas-pendientes", "Firmas pendientes de autorización."),
            ("materiales-estudio", "Material de certificaciones."),
            ("capacitaciones", "Capacitaciones abiertas / postulación."),
        ],
    ),
    (
        "【🩺】 dirección médica",
        [
            ("dir-medica", "Dirección Médica."),
            ("expedientes", "Expedientes clínicos (staff)."),
            ("licencias-medicas", "Licencias médicas."),
            ("pacientes", "Registro / gestión de pacientes RP."),
        ],
    ),
    (
        "【💉】 enfermería",
        [
            ("dir-enfermeria", "Dirección de Enfermería."),
            ("turnos-enfermeria", "Turnos de enfermería."),
        ],
    ),
    (
        "【👥】 recursos humanos",
        [
            ("dir-rrhh", "Recursos Humanos."),
            ("solicitudes-inactividad", "Inactividad justificada."),
            ("entrevistas", "Entrevistas de ingreso."),
            ("despidos", "Procesos de despido."),
            ("sanciones", "Sanciones de personal."),
            ("investigaciones", "Investigaciones internas."),
        ],
    ),
    (
        "【📦】 logística",
        [
            ("dir-logistica", "Dirección de Logística."),
            ("inventario", "Inventario / suministros."),
        ],
    ),
    (
        "【🛡️】 seguridad",
        [
            ("dir-seguridad", "Departamento de Seguridad."),
            ("codigos-seguridad", "Códigos y alertas de seguridad."),
        ],
    ),
    (
        "【📝】 postulaciones",
        [
            ("postulaciones-medica", "Postulaciones área médica."),
            ("postulaciones-especialidad", "Postulaciones a especialidades."),
            ("postulaciones-administrativa", "Postulaciones área administrativa."),
        ],
    ),
    (
        "【🛒】 economía y tienda",
        [
            ("tienda", "Catálogo / tienda del servidor."),
            ("economia", "Economía, salarios, transferencias."),
        ],
    ),
    (
        "【📅】 reuniones",
        [
            ("reuniones", "Convocatorias de reuniones."),
            ("actas-reuniones", "Actas y resúmenes."),
        ],
    ),
    (
        "【📁】 logs",
        [
            ("log-tickets", "Transcripciones de tickets."),
            ("log-verificaciones", "Verificaciones / whitelist."),
            ("log-solicitudes", "Solicitudes generales."),
            ("aprobaciones-rrhh", "Aprobaciones RRHH."),
            ("log-postulaciones", "Postulaciones registradas."),
            ("log-quejas", "Registro de quejas."),
            ("log-sanciones", "Registro de sanciones."),
            ("log-investigaciones", "Registro de investigaciones."),
            ("log-certificados", "Certificados emitidos."),
            ("log-inactividad", "Inactividades."),
            ("log-despidos", "Despidos registrados."),
            ("log-reportes", "Reportes y bugs."),
            ("log-economia", "Movimientos económicos."),
            ("log-general", "Logs generales del bot."),
        ],
    ),
    (
        "【🛡️】 staff",
        [
            ("staff-general", "Chat del staff."),
            ("staff-anuncios", "Anuncios solo staff."),
            ("staff-alertas", "Alertas urgentes staff."),
        ],
    ),
    (
        "【⚙️】 administración",
        [
            ("admin-only", "Solo Owner / Admin."),
            ("bot-comandos", "Canal técnico del bot."),
            ("bot-status", "Estado / control del bot."),
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
    "【🖥️】 dirección general",
    "【🏛️】 cancillería",
    "【📚】 docencia",
    "【🩺】 dirección médica",
    "【💉】 enfermería",
    "【👥】 recursos humanos",
    "【📦】 logística",
    "【🛡️】 seguridad",
    "【📁】 logs",
    "【🛡️】 staff",
    "【⚙️】 administración",
    "【📅】 reuniones",
}


async def _asegurar_categoria(
    guild: discord.Guild,
    nombre: str,
    overwrites: Optional[Dict] = None,
) -> discord.CategoryChannel:
    for c in guild.categories:
        if c.name == nombre:
            return c
    kwargs = {"reason": "Setup servidor"}
    if overwrites:
        kwargs["overwrites"] = overwrites
    return await guild.create_category(nombre, **kwargs)


async def _asegurar_canal(
    guild: discord.Guild,
    nombre: str,
    category: discord.CategoryChannel,
    overwrites: Optional[Dict] = None,
) -> discord.TextChannel:
    for ch in guild.text_channels:
        if ch.name == nombre and ch.category_id == category.id:
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
    """Crea categorías/canales. Nunca borra canales ni toca reglamentos."""
    lineas: List[str] = []
    creados = 0
    existentes = 0

    for cat_nombre, canales in ESTRUCTURA:
        try:
            privada = cat_nombre in _CATS_PRIVADAS
            ow = _overwrites_privada(guild) if privada else None
            cat = await _asegurar_categoria(guild, cat_nombre, overwrites=ow)
            lineas.append(f"**{cat_nombre}**")
            await asyncio.sleep(0.3)

            for slug, desc in canales:
                try:
                    antes = any(
                        ch.name == slug and ch.category_id == cat.id
                        for ch in guild.text_channels
                    )
                    ch = await _asegurar_canal(
                        guild, slug, cat, overwrites=ow if privada else None
                    )
                    if antes:
                        existentes += 1
                        lineas.append(f"  · {ch.mention} _(ya existía)_")
                    else:
                        creados += 1
                        lineas.append(f"  · {ch.mention} — {desc}")
                        try:
                            emb = crear_embed(
                                "info", slug.replace("-", " ").title(), desc
                            )
                            await ch.send(embed=emb)
                        except Exception:
                            pass

                    area = _MAPA_DIRECCION.get(slug)
                    if area:
                        try:
                            import canales_direccion

                            canales_direccion.guardar_canal(area, ch.id, guild.id)
                        except Exception:
                            pass

                    tipo_log = _MAPA_LOG.get(slug)
                    if tipo_log:
                        try:
                            import logs_store

                            logs_store.set_canal(tipo_log, ch.id)
                        except Exception:
                            pass

                    await asyncio.sleep(0.35)
                except Exception as e:
                    lineas.append(f"  · ❌ `{slug}`: {e}")
        except Exception as e:
            lineas.append(f"❌ Categoría `{cat_nombre}`: {e}")

    lineas.append("")
    lineas.append(
        f"**Resumen canales:** 🆕 {creados} creados · ✓ {existentes} ya existían"
    )
    lineas.append(
        "_Los reglamentos guardados (`/agregar_reglamento`) no se modifican._"
    )
    return lineas


def _preview_texto() -> str:
    parts = []
    total = 0
    for cat, canales in ESTRUCTURA:
        parts.append(f"**{cat}** ({len(canales)})")
        total += len(canales)
        for slug, _ in canales:
            parts.append(f"  · `#{slug}`")
    parts.append("")
    parts.append(f"Total: **{len(ESTRUCTURA)}** categorías · **{total}** canales")
    parts.append("Organigrama de roles + separadores.")
    parts.append("No borra canales ni reglamentos existentes.")
    return "\n".join(parts)[:3900]


def registrar(bot: commands.Bot) -> None:
    try:
        bot.tree.remove_command("setup_servidor")
    except Exception:
        pass

    @bot.tree.command(
        name="setup_servidor",
        description="[Fundador] Roles + todos los canales del hospital",
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
                    "exito",
                    "✅ Setup completado (1/2)",
                    texto[:3800],
                    autor=interaction.user,
                ),
                ephemeral=True,
            )
            await interaction.followup.send(
                embed=crear_embed("info", "Setup (2/2)", texto[3800:7600]),
                ephemeral=True,
            )

    print("[setup_servidor] OK — canales completos · cancillería ejecutiva")
