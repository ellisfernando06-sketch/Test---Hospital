# -*- coding: utf-8 -*-
"""Amplía /registrar_firma con Canciller y Vice Canciller."""
from __future__ import annotations

import os

import discord
from discord import app_commands
from discord.ext import commands


def registrar(bot: commands.Bot) -> None:
    try:
        import firmas as fm
    except Exception as e:
        print(f"[firmas_cargos_extra] sin firmas: {e}")
        return

    # Quitar el comando viejo y re-registrar con más cargos
    try:
        bot.tree.remove_command("registrar_firma")
    except Exception:
        pass

    @bot.tree.command(
        name="registrar_firma",
        description="Registra tu firma digitalizada (imagen)",
    )
    @app_commands.describe(imagen="Imagen de tu firma", cargo="Cargo")
    @app_commands.choices(
        cargo=[
            app_commands.Choice(
                name="Canciller", value="CANCILLER"
            ),
            app_commands.Choice(
                name="Vice Canciller", value="VICE_CANCILLER"
            ),
            app_commands.Choice(
                name="Director de Investigación y Docencia",
                value="DIRECTOR_DOCENCIA",
            ),
            app_commands.Choice(
                name="Director Médico", value="DIRECTOR_MEDICO"
            ),
            app_commands.Choice(
                name="Director de Enfermería", value="DIRECTOR_ENFERMERIA"
            ),
            app_commands.Choice(
                name="Director de RRHH", value="DIRECTOR_RRHH"
            ),
            app_commands.Choice(
                name="Director de Logística", value="DIRECTOR_LOGISTICA"
            ),
            app_commands.Choice(
                name="Director General", value="DIRECTOR_GENERAL"
            ),
            app_commands.Choice(
                name="Jefe de Seguridad", value="JEFE_SEGURIDAD"
            ),
            app_commands.Choice(
                name="Encargado / Instructor", value="ENCARGADO"
            ),
            app_commands.Choice(
                name="Otra firma personal", value="PERSONAL"
            ),
        ]
    )
    async def registrar_firma(
        inter: discord.Interaction,
        imagen: discord.Attachment,
        cargo: app_commands.Choice[str],
    ):
        if not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "Solo en servidor.", ephemeral=True
            )
        if not imagen.content_type or not str(imagen.content_type).startswith(
            "image/"
        ):
            return await inter.response.send_message(
                "❌ Debe ser imagen.", ephemeral=True
            )

        key = cargo.value
        # Aliases de keys del organigrama
        aliases = {
            "DIRECTOR_DOCENCIA": ("DIR_DOCENCIA", "DIRECTOR_DOCENCIA"),
            "DIRECTOR_MEDICO": ("DIR_MEDICO", "DIRECTOR_MEDICO"),
            "DIRECTOR_ENFERMERIA": ("DIR_ENFERMERIA", "DIRECTOR_ENFERMERIA"),
            "DIRECTOR_RRHH": ("DIR_RRHH", "DIRECTOR_RRHH"),
            "DIRECTOR_LOGISTICA": ("DIR_LOGISTICA", "DIRECTOR_LOGISTICA"),
            "DIRECTOR_GENERAL": ("DIR_GENERAL", "DIRECTOR_GENERAL"),
            "CANCILLER": ("CANCILLER", "PREFECTO_OPERACIONES"),
            "VICE_CANCILLER": ("VICE_CANCILLER",),
            "JEFE_SEGURIDAD": ("JEFE_SEGURIDAD",),
        }
        keys_ok = aliases.get(key, (key,))

        if key not in ("ENCARGADO", "PERSONAL"):
            if not fm._es_key(inter.user, *keys_ok, "OWNER", "FUNDADOR_OWNER", "CO_OWNER"):
                return await inter.response.send_message(
                    f"❌ No tienes el cargo **{cargo.name}**.",
                    ephemeral=True,
                )

        await inter.response.defer(ephemeral=True)
        try:
            fname = await fm.descargar_firma(imagen, inter.user.id)
            fm.guardar_firma(inter.user.id, key, fname)
            # Guardar también bajo alias para búsqueda por key
            for ak in keys_ok:
                try:
                    data = fm._load_json(fm._FIRMAS_PATH, {})
                    data.setdefault("por_key", {})[ak] = str(inter.user.id)
                    fm._save_json(fm._FIRMAS_PATH, data)
                except Exception:
                    pass
            await inter.followup.send(
                f"✅ Firma de **{cargo.name}** registrada.",
                ephemeral=True,
            )
        except Exception as e:
            await inter.followup.send(f"❌ {e}", ephemeral=True)

    print("[firmas_cargos_extra] OK — Canciller + Vice Canciller en /registrar_firma")
