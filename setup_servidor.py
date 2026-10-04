# -*- coding: utf-8 -*-
"""
setup_servidor.py — Organigrama + categorías y canales del hospital.
Direcciones en categorías separadas (sin aglomerar).
"""
from __future__ import annotations

import asyncio
from typing import Dict, List, Optional, Sequence, Tuple

import discord
from discord import app_commands
from discord.ext import commands

import roles_setup
from estilos import crear_embed

# ── Estructura oficial (categorías → canales) ─────────────────────────────────
# Cada dirección va en su propia categoría para no llenar una sola.

ESTRUCTURA: List[Tuple[str, List[Tuple[str, str]]]] = [
    (
        "【👋🏻】 ingreso",
        [
            ("bienvenida", "Mensaje de bienvenida automático del bot."),
            ("verificacion", "Panel y flujo de verificación / whitelist."),
            ("aceptar-reglas", "Aceptar reglas → rol Miembro."),
        ],
    ),
    (
        "【📜】 normativas",
        [
            ("normativa-rp", "Normativa de roleplay."),
            ("normativa-discord", "Normativa de Discord."),
            ("normativa-general", "Normativa general del servidor."),
            ("normativa-hospitalaria", "Normativa hospitalaria institucional."),
            ("normativa-seguridad", "Normativa del departamento de seguridad."),
        ],
    ),
    (
        "【💬】 comunidad",
        [
            ("general", "Chat general de la comunidad."),
            ("anuncios", "Anuncios públicos del hospital."),
            ("ayuda", "Dudas y orientación para miembros."),
        ],
    ),
    (
        "【🎭】 roleplay",
        [
            ("rp-hospital", "Roleplay principal del hospital."),
            ("rp-urgencias", "Roleplay de urgencias."),
            ("rp-reportes", "Reportes y bitácora de RP."),
        ],
    ),
    (
        "【🎫】 tickets",
        [
            ("abrir-ticket", "Panel para abrir tickets de soporte."),
        ],
    ),
    # Direcciones: una categoría por área (lo necesario, sin relleno)
    (
        "【🖥️】 dirección general",
        [
            ("dir-general", "Canal de la Dirección General."),
            ("anuncios-direcciones", "Anuncios internos entre direcciones."),
        ],
    ),
    (
        "【🏛️】 cancillería",
        [
            ("dir-cancilleria", "Operaciones / Canciller y Vice Canciller."),
        ],
    ),
    (
        "【📚】 docencia",
        [
            ("dir-docencia", "Dirección de Docencia y certificaciones."),
            ("solicitudes-certificados", "Solicitudes de certificados / firmas."),
            ("materiales-estudio", "Material de estudio para certificaciones."),
        ],
    ),
    (
        "【🩺】 dirección médica",
        [
            ("dir-medica", "Dirección Médica."),
        ],
    ),
    (
        "【💉】 enfermería",
        [
            ("dir-enfermeria", "Dirección de Enfermería."),
        ],
    ),
    (
        "【👥】 recursos humanos",
        [
            ("dir-rrhh", "Recursos Humanos."),
            ("solicitudes-inactividad", "Solicitudes de inactividad justificada."),
        ],
    ),
    (
        "【📦】 logística",
        [
            ("dir-logistica", "Dirección de Logística."),
        ],
    ),
    (
        "【🛡️】 seguridad",
        [
            ("dir-seguridad", "Departamento de Seguridad."),
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
        "【📁】 logs",
        [
            ("log-tickets", "Transcripciones de tickets."),
            ("log-verificaciones", "Resultados de verificación / whitelist."),
            ("log-solicitudes", "Registro de solicitudes."),
            ("aprobaciones-rrhh", "Aprobaciones de RRHH."),
            ("log-postulaciones", "Registro de postulaciones."),
            ("log-sanciones", "Registro de sanciones."),
            ("log-certificados", "Registro de certificados emitidos."),
            ("log-inactividad", "Registro de inactividades."),
            ("log-general", "Logs generales del bot."),
        ],
    ),
    (
        "【🛡️】 staff",
        [
            ("staff-general", "Chat interno del staff."),
            ("staff-anuncios", "Anuncios solo staff."),
        ],
    ),
    (
        "【⚙️】 administración",
        [
            ("admin-only", "Solo administración / owners."),
            ("bot-comandos", "Canal técnico del bot (opcional)."),
        ],
    ),
]

# Canal de dirección → área de canales_direccion.py
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
}

# Canal de log → tipo logs_store
_MAPA_LOG: Dict[str, str] = {
    "log-tickets": "log_tickets",
    "log-solicitudes": "log_solicitudes",
    "aprobaciones-rrhh": "aprobaciones_rrhh",
    "log-postulaciones": "log_postulaciones",
    "log-sanciones": "log_sanciones",
    "log-general": "log_general",
    "log-verificaciones": "log_solicitudes",  # fallback útil; área verificacion ya mapeada
}

# Categorías privadas (staff / dirección / logs / admin)
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
    """@everyone no ve; el bot sí."""
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

    for cat_nombre, canales in ESTRUCTURA:
        try:
            privada = cat_nombre in _CATS_PRIVADAS
            ow = _overwrites_privada(guild) if privada else None
            cat = await _asegurar_categoria(guild, cat_nombre, overwrites=ow)
            lineas.append(f"**{cat_nombre}**")
            await asyncio.sleep(0.35)

            for slug, desc in canales:
                try:
                    # ¿ya existía?
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
                            emb = crear_embed("info", slug.replace("-", " ").title(), desc)
                            await ch.send(embed=emb)
                        except Exception:
                            pass

                    # Registrar dirección
                    area = _MAPA_DIRECCION.get(slug)
                    if area:
                        try:
                            import canales_direccion

                            canales_direccion.guardar_canal(area, ch.id, guild.id)
                        except Exception:
                            pass

                    # Registrar logs
                    tipo_log = _MAPA_LOG.get(slug)
                    if tipo_log:
                        try:
                            import logs_store

                            logs_store.set_canal(tipo_log, ch.id)
                        except Exception:
                            pass

                    await asyncio.sleep(0.4)
                except Exception as e:
                    lineas.append(f"  · ❌ `{slug}`: {e}")
        except Exception as e:
            lineas.append(f"❌ Categoría `{cat_nombre}`: {e}")

    lineas.append("")
    lineas.append(f"**Resumen canales:** 🆕 {creados} creados · ✓ {existentes} ya existían")
    return lineas


def _preview_texto() -> str:
    parts = []
    for cat, canales in ESTRUCTURA:
        parts.append(f"**{cat}** ({len(canales)} canales)")
        for slug, _ in canales:
            parts.append(f"  · `#{slug}`")
    parts.append("")
    parts.append("También: organigrama de roles + separadores.")
    return "\n".join(parts)[:3900]


def registrar(bot: commands.Bot) -> None:
    try:
        bot.tree.remove_command("setup_servidor")
    except Exception:
        pass

    @bot.tree.command(
        name="setup_servidor",
        description="[Fundador] Roles + categorías y canales del hospital",
    )
    @app_commands.describe(dry_run="Solo muestra lo que se crearía, sin tocar nada")
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
            emb = crear_embed(
                "info",
                "Vista previa /setup_servidor",
                _preview_texto(),
            )
            return await interaction.followup.send(embed=emb, ephemeral=True)

        lineas: List[str] = []

        # 1) Roles
        try:
            lineas.append("**—— Roles ——**")
            lineas.extend(await roles_setup.configurar_organigrama(interaction.guild))
        except Exception as e:
            lineas.append(f"❌ Roles: {e}")

        # 2) Categorías y canales
        try:
            lineas.append("")
            lineas.append("**—— Canales ——**")
            lineas.extend(await crear_estructura_canales(interaction.guild))
        except Exception as e:
            lineas.append(f"❌ Canales: {e}")

        texto = "\n".join(lineas)
        # Discord embed limit — partir si hace falta
        if len(texto) <= 3800:
            emb = crear_embed(
                "exito", "✅ Setup completado", texto, autor=interaction.user
            )
            await interaction.followup.send(embed=emb, ephemeral=True)
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

    print("[setup_servidor] OK — roles + categorías/canales completos")
