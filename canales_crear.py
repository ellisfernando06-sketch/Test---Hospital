# -*- coding: utf-8 -*-
"""
canales_crear.py — Directores y autoridades pueden crear canales en categorías.

/agregar_canal  → texto o voz en una categoría existente
Diseño opcional →【emoji】nombre
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Sequence, Set, Tuple

import discord
from discord import app_commands
from discord.ext import commands

# Quién puede crear en qué (keys). Autoridades: cualquier categoría.
_KEYS_AUTORIDAD = (
    "FUNDADOR_OWNER",
    "CO_OWNER",
    "OWNER",
    "CANCILLER",
    "VICE_CANCILLER",
    "ADMIN_JEFE",
    "ADMIN",
)

# Director → keywords de categoría permitidas (minúsculas)
_DIRECTOR_CATS: Dict[str, Tuple[str, ...]] = {
    "DIR_GENERAL": ("dirección general", "direccion general", "general"),
    "DIRECTOR_GENERAL": ("dirección general", "direccion general", "general"),
    "DIR_DOCENCIA": ("docencia",),
    "DIRECTOR_DOCENCIA": ("docencia",),
    "DIR_MEDICO": ("médica", "medica", "médico", "medico"),
    "DIRECTOR_MEDICO": ("médica", "medica", "médico", "medico"),
    "DIR_ENFERMERIA": ("enfermería", "enfermeria"),
    "DIRECTOR_ENFERMERIA": ("enfermería", "enfermeria"),
    "DIR_RRHH": ("recursos humanos", "rrhh"),
    "DIRECTOR_RRHH": ("recursos humanos", "rrhh"),
    "DIR_LOGISTICA": ("logística", "logistica"),
    "DIRECTOR_LOGISTICA": ("logística", "logistica"),
    "JEFE_SEGURIDAD": ("seguridad",),
    "SUPERVISOR_SEGURIDAD": ("seguridad",),
    "CANCILLER": ("cancillería", "cancilleria", "ejecutiv", "oficina"),
    "VICE_CANCILLER": ("cancillería", "cancilleria", "ejecutiv", "oficina"),
}


def _member_keys(member: discord.Member) -> Set[str]:
    keys: Set[str] = set()
    try:
        import roles_store

        # Invertir store: role_id → key
        for attr in ("obtener_todas_keys", "todas_las_keys", "listar_keys"):
            fn = getattr(roles_store, attr, None)
            if callable(fn):
                try:
                    data = fn()
                    if isinstance(data, dict):
                        for k, rid in data.items():
                            if rid and any(r.id == int(rid) for r in member.roles):
                                keys.add(str(k))
                except Exception:
                    pass
    except Exception:
        pass

    try:
        import roles_config

        nombres = getattr(roles_config, "KEYS_NOMBRES", {}) or {}
        for k, nom in nombres.items():
            nombre = nom[0] if isinstance(nom, (list, tuple)) else str(nom)
            for r in member.roles:
                if r.name == nombre or nombre.lower() in (r.name or "").lower():
                    keys.add(str(k))
    except Exception:
        pass

    if member.guild_permissions.administrator:
        keys.update(_KEYS_AUTORIDAD)
    return keys


def _es_autoridad(member: discord.Member) -> bool:
    if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
        return True
    keys = _member_keys(member)
    return any(k in keys for k in _KEYS_AUTORIDAD)


def _es_director_o_autoridad(member: discord.Member) -> bool:
    if _es_autoridad(member):
        return True
    keys = _member_keys(member)
    return any(k in _DIRECTOR_CATS for k in keys)


def _categoria_permitida(member: discord.Member, cat: discord.CategoryChannel) -> bool:
    if _es_autoridad(member):
        return True
    keys = _member_keys(member)
    nombre = (cat.name or "").lower()
    # quitar diseño para comparar
    nombre_limpio = re.sub(r"^→\s*", "", nombre)
    nombre_limpio = re.sub(r"【[^】]*】\s*", "", nombre_limpio).lower()

    for k in keys:
        words = _DIRECTOR_CATS.get(k)
        if not words:
            continue
        for w in words:
            if w in nombre or w in nombre_limpio:
                return True
    return False


def _formatear_nombre(nombre: str, emoji: Optional[str]) -> str:
    n = (nombre or "").strip()
    # si ya trae el diseño, respetarlo
    if n.startswith("→"):
        return n[:100]
    n = re.sub(r"\s+", "-", n.lower())
    n = re.sub(r"[^a-z0-9\-áéíóúüñ]", "", n, flags=re.I)
    n = n.strip("-") or "canal"
    if emoji:
        em = emoji.strip()
        if not em.startswith("【"):
            em = f"【{em}】"
        return f"→{em}{n}"[:100]
    return f"→【📁】{n}"[:100]


async def _crear(
    guild: discord.Guild,
    cat: discord.CategoryChannel,
    nombre: str,
    tipo: str,
    privado: bool,
    member: discord.Member,
) -> discord.abc.GuildChannel:
    overwrites = None
    if privado:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False, connect=False
            ),
            member: discord.PermissionOverwrite(
                view_channel=True,
                connect=True,
                speak=True,
                send_messages=True,
                read_message_history=True,
            ),
        }
        me = guild.me
        if me:
            overwrites[me] = discord.PermissionOverwrite(
                view_channel=True,
                connect=True,
                speak=True,
                send_messages=True,
                manage_channels=True,
                manage_messages=True,
            )
        # heredar visibilidad de roles que ya ven la categoría
        for target, ow in (cat.overwrites or {}).items():
            if isinstance(target, discord.Role) and ow.view_channel is True:
                overwrites[target] = discord.PermissionOverwrite(
                    view_channel=True,
                    connect=True,
                    speak=True,
                    send_messages=True,
                    read_message_history=True,
                )

    kwargs = {"category": cat, "reason": f"Creado por {member} (/agregar_canal)"}
    if overwrites:
        kwargs["overwrites"] = overwrites

    if tipo == "voz":
        return await guild.create_voice_channel(nombre, **kwargs)
    if tipo == "escenario":
        try:
            return await guild.create_stage_channel(nombre, **kwargs)
        except Exception:
            return await guild.create_voice_channel(nombre, **kwargs)
    return await guild.create_text_channel(nombre, **kwargs)


def registrar(bot: commands.Bot) -> None:
    for name in ("agregar_canal",):
        try:
            bot.tree.remove_command(name)
        except Exception:
            pass

    @bot.tree.command(
        name="agregar_canal",
        description="[Director/Autoridad] Crea un canal en una categoría existente",
    )
    @app_commands.describe(
        categoria="Categoría donde se creará",
        nombre="Nombre del canal (sin diseño; se aplica solo)",
        tipo="texto, voz o escenario",
        emoji="Emoji opcional dentro de 【】 (ej: 📚 o 🎙️)",
        privado="Si es True, solo roles de la categoría + tú",
    )
    @app_commands.choices(
        tipo=[
            app_commands.Choice(name="Texto", value="texto"),
            app_commands.Choice(name="Voz", value="voz"),
            app_commands.Choice(name="Escenario", value="escenario"),
        ]
    )
    async def agregar_canal(
        inter: discord.Interaction,
        categoria: discord.CategoryChannel,
        nombre: str,
        tipo: app_commands.Choice[str],
        emoji: Optional[str] = None,
        privado: bool = True,
    ):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )

        if not _es_director_o_autoridad(inter.user):
            return await inter.response.send_message(
                "❌ Solo **directores** o **autoridades** (Owner, Canciller, Admin).",
                ephemeral=True,
            )

        if not _categoria_permitida(inter.user, categoria):
            return await inter.response.send_message(
                (
                    f"❌ No puedes crear canales en **{categoria.name}**.\n"
                    f"Solo en categorías de **tu dirección** "
                    f"(las autoridades pueden en cualquiera)."
                ),
                ephemeral=True,
            )

        nombre_final = _formatear_nombre(nombre, emoji)
        # evitar duplicado exacto en la categoría
        for ch in inter.guild.channels:
            if (
                getattr(ch, "category_id", None) == categoria.id
                and (ch.name or "") == nombre_final
            ):
                return await inter.response.send_message(
                    f"❌ Ya existe `{nombre_final}` en esa categoría.",
                    ephemeral=True,
                )

        await inter.response.defer(ephemeral=True)
        try:
            ch = await _crear(
                inter.guild,
                categoria,
                nombre_final,
                tipo.value,
                privado,
                inter.user,
            )
        except discord.Forbidden:
            return await inter.followup.send(
                "❌ El bot no tiene permiso **Gestionar canales**.",
                ephemeral=True,
            )
        except Exception as e:
            return await inter.followup.send(
                f"❌ No se pudo crear: `{e}`", ephemeral=True
            )

        mention = getattr(ch, "mention", None) or f"**{ch.name}**"
        await inter.followup.send(
            (
                f"✅ Canal creado: {mention}\n"
                f"Categoría: **{categoria.name}**\n"
                f"Tipo: **{tipo.name}** · Privado: **{'sí' if privado else 'no'}**"
            ),
            ephemeral=True,
        )

    print("[canales_crear] OK — /agregar_canal (directores y autoridades)")
