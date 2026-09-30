# -*- coding: utf-8 -*-
"""
roles_comandos.py
=================
Sustituye los comandos de roles del núcleo con versiones que:
- Aceptan Fundador y Owner / Co-Owner (y OWNER legado)
- Usan el organigrama oficial (roles_config)
- Responden con embeds profesionales
"""
from __future__ import annotations

from typing import List

import discord
from discord import app_commands
from discord.ext import commands

import roles_config
import roles_setup
from estilos import crear_embed


def _es_autoridad(member: discord.Member) -> bool:
    try:
        import permisos
        return permisos.member_tiene_alguna_key(
            member, "FUNDADOR_OWNER", "CO_OWNER", "OWNER"
        )
    except Exception:
        return bool(member.guild_permissions.administrator)


def _partir(texto: str, max_len: int = 3800) -> List[str]:
    if not texto.strip():
        return ["*(sin cambios registrados)*"]
    return [texto[i : i + max_len] for i in range(0, len(texto), max_len)]


async def _enviar_resumen(
    inter: discord.Interaction,
    titulo: str,
    lineas: List[str],
    tipo: str = "exito",
) -> None:
    texto = "\n".join(lineas) if lineas else "*(sin cambios)*"
    bloques = _partir(texto)
    for i, bloque in enumerate(bloques):
        emb = crear_embed(
            tipo,
            titulo if i == 0 else f"{titulo} (cont.)",
            bloque,
            autor=inter.user,
            footer_extra="Organigrama oficial",
        )
        if i == 0:
            emb.add_field(
                name="📌 Fuente",
                value="`roles_config` · organigrama único",
                inline=True,
            )
            emb.add_field(
                name="👤 Ejecutado por",
                value=inter.user.mention,
                inline=True,
            )
        await inter.followup.send(embed=emb, ephemeral=True)


def registrar(bot: commands.Bot) -> None:
    # Quitar versiones viejas del núcleo para no duplicar / fallar por límite
    for name in ("configurar_roles", "ordenar_roles", "organigrama"):
        try:
            bot.tree.remove_command(name)
        except Exception:
            pass

    @bot.tree.command(
        name="configurar_roles",
        description="[Fundador] Crea/detecta roles del organigrama y guarda keys",
    )
    async def configurar_roles(inter: discord.Interaction):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _es_autoridad(inter.user):
            emb = crear_embed(
                "error",
                "Sin permiso",
                "Solo **Fundador y Owner** o **Co-Owner** pueden configurar roles.",
            )
            return await inter.response.send_message(embed=emb, ephemeral=True)

        await inter.response.defer(ephemeral=True)
        try:
            resumen = await roles_setup.configurar_organigrama(inter.guild)
        except Exception as e:
            emb = crear_embed(
                "error",
                "Error al configurar roles",
                f"```{type(e).__name__}: {e}```\n"
                "Revisa que el bot tenga **Gestionar roles** y su rol esté arriba.",
                autor=inter.user,
            )
            return await inter.followup.send(embed=emb, ephemeral=True)

        await _enviar_resumen(
            inter,
            "✅ Organigrama configurado",
            resumen,
            "exito",
        )

    @bot.tree.command(
        name="ordenar_roles",
        description="[Fundador] Reordena roles según el organigrama oficial",
    )
    async def ordenar_roles_cmd(inter: discord.Interaction):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _es_autoridad(inter.user):
            emb = crear_embed(
                "error",
                "Sin permiso",
                "Solo **Fundador y Owner** o **Co-Owner** pueden ordenar roles.",
            )
            return await inter.response.send_message(embed=emb, ephemeral=True)

        await inter.response.defer(ephemeral=True)
        try:
            resumen = await roles_setup.ordenar_roles(inter.guild)
        except Exception as e:
            emb = crear_embed(
                "error",
                "Error al ordenar roles",
                f"```{type(e).__name__}: {e}```",
                autor=inter.user,
            )
            return await inter.followup.send(embed=emb, ephemeral=True)

        await _enviar_resumen(inter, "📑 Roles ordenados", resumen, "info")

    @bot.tree.command(
        name="organigrama",
        description="Muestra el organigrama oficial del hospital",
    )
    async def organigrama_cmd(inter: discord.Interaction):
        await inter.response.defer(ephemeral=True)

        secciones = [
            ("👑 Autoridades Competentes", ["FUNDADOR_OWNER", "CO_OWNER"]),
            ("🛡️ Staff del Server", ["ADMIN_JEFE", "ADMIN", "ADMIN_PRUEBA"]),
            (
                "🏛️ Gerencia",
                [
                    "PREFECTO_OPERACIONES",
                    "DIR_GENERAL",
                    "DIR_MEDICO",
                    "DIR_RRHH",
                    "DIR_DOCENCIA",
                    "DIR_LOGISTICA",
                ],
            ),
            ("⭐ Jefatura", ["JEFE_DEPARTAMENTO"]),
            (
                "🩺 Área Médica",
                [
                    "JEFE_SERVICIO",
                    "MEDICO_ESPECIALISTA",
                    "MEDICO_GENERAL",
                    "JEFE_GUIA_RESIDENTES",
                    "RESIDENTE",
                    "INTERNO",
                ],
            ),
            (
                "📋 Área Administrativa",
                ["ADMINISTRATIVO_SENIOR", "ADMINISTRATIVO_JUNIOR"],
            ),
            ("⚙️ Sistema", ["INACTIVIDAD_JUSTIFICADA"]),
        ]

        emb = crear_embed(
            "info",
            "Organigrama oficial",
            "Jerarquía de cargos del hospital (mayor → menor).\n"
            "Fuente: **roles_config**",
            autor=inter.user,
            footer_extra="Consulta pública",
        )

        for titulo, keys in secciones:
            lineas = []
            for k in keys:
                nombre = roles_config.nombre_key(k)
                lineas.append(f"• `{k}` — **{nombre}**")
            emb.add_field(
                name=titulo,
                value="\n".join(lineas)[:1020],
                inline=False,
            )

        await inter.followup.send(embed=emb, ephemeral=True)

    print("[roles_comandos] OK — /configurar_roles /ordenar_roles /organigrama")
