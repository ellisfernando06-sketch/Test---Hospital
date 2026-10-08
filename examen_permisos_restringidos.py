# -*- coding: utf-8 -*-
"""/examen_direccion solo: Owner, Co-Owner, Admin en jefe."""
from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

try:
    import permisos
except Exception:
    permisos = None

_KEYS_CMD = ("FUNDADOR_OWNER", "CO_OWNER", "OWNER", "ADMIN_JEFE")


def _puede_lanzar_examen(m: discord.Member) -> bool:
    if m.guild and m.id == m.guild.owner_id:
        return True
    if permisos is None:
        return False
    try:
        return bool(permisos.member_tiene_alguna_key(m, *_KEYS_CMD))
    except Exception:
        return False


def registrar(bot: commands.Bot) -> None:
    try:
        import examen_direccion as ed

        try:
            bot.tree.remove_command("examen_direccion")
        except Exception:
            pass

        @bot.tree.command(
            name="examen_direccion",
            description="[Owner/Co-Owner/Admin en jefe] Examen escrito de postulación",
        )
        @app_commands.describe(canal_log="Canal de logs de las respuestas")
        async def examen_direccion(
            inter: discord.Interaction, canal_log: discord.TextChannel
        ):
            if not inter.guild or not isinstance(inter.user, discord.Member):
                return await inter.response.send_message(
                    "❌ Solo en el servidor.", ephemeral=True
                )
            if not _puede_lanzar_examen(inter.user):
                return await inter.response.send_message(
                    "❌ Sin permiso.\nSolo **Owner**, **Co-Owner** o **Admin en jefe**.",
                    ephemeral=True,
                )

            emb = discord.Embed(
                title="🏛️  Exámenes de Dirección · Hospital General",
                description=(
                    "Elige la **dirección** en el menú.\n\n"
                    "El bot detecta quién tiene el **rol** de esa dirección "
                    "y le envía el examen **escrito** por MD.\n\n"
                    f"**Log:** {canal_log.mention}\n\n"
                    "Respuestas con palabras propias → revisión en el log."
                ),
                color=0x1A5276,
            ).set_footer(text="Solo Owner · Co-Owner · Admin en jefe")

            await inter.response.send_message(
                embed=emb,
                view=ed.DireccionMenuView(canal_log),
                ephemeral=True,
            )

        print("[examen_perm] /examen_direccion → Owner/Co-Owner/Admin en jefe")
    except Exception as e:
        print(f"[examen_perm] {e}")
