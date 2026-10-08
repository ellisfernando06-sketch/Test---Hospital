# -*- coding: utf-8 -*-
"""
Restringe /examen_direccion y acciones de envío del examen a:
  · Fundador / Owner
  · Co-Owner
  · Admin en jefe
No basta con Administrador de Discord genérico.
"""
from __future__ import annotations

import discord
from discord.ext import commands

try:
    import permisos
except Exception:
    permisos = None

_KEYS = (
    "FUNDADOR_OWNER",
    "CO_OWNER",
    "OWNER",
    "ADMIN_JEFE",
)


def _puede_examen(m: discord.Member) -> bool:
    if m.guild and m.id == m.guild.owner_id:
        return True
    if permisos is None:
        return False
    try:
        return bool(permisos.member_tiene_alguna_key(m, *_KEYS))
    except Exception:
        return False


def registrar(bot: commands.Bot) -> None:
    # Parche examen_direccion._es_staff (comando + paneles internos de ese módulo)
    try:
        import examen_direccion as ed

        ed._es_staff = _puede_examen  # type: ignore
    except Exception as e:
        print(f"[examen_perm] ed: {e}")

    try:
        import examen_direccion_escrito as ex

        ex._es_staff = _puede_examen  # type: ignore
    except Exception as e:
        print(f"[examen_perm] escrito: {e}")

    # Re-envolver el slash por si quedó con el check viejo
    try:
        import examen_direccion as ed
        from discord import app_commands

        try:
            bot.tree.remove_command("examen_direccion")
        except Exception:
            pass

        @bot.tree.command(
            name="examen_direccion",
            description="[Owner/Co-Owner/Admin en jefe] Examen escrito de postulación a Direcciones",
        )
        @app_commands.describe(canal_log="Canal de logs donde van las respuestas")
        async def examen_direccion(
            inter: discord.Interaction, canal_log: discord.TextChannel
        ):
            if not inter.guild or not isinstance(inter.user, discord.Member):
                return await inter.response.send_message(
                    "❌ Solo en el servidor.", ephemeral=True
                )
            if not _puede_examen(inter.user):
                return await inter.response.send_message(
                    "❌ Sin permiso.\n"
                    "Solo **Owner**, **Co-Owner** o **Admin en jefe**.",
                    ephemeral=True,
                )

            emb = discord.Embed(
                title="🏛️  Exámenes de Dirección · Hospital General",
                description=(
                    "Elige la **dirección** en el menú.\n\n"
                    "El bot detecta a quienes tienen el **rol** de esa dirección "
                    "y les envía el examen **escrito** por MD.\n\n"
                    f"**Log de respuestas:** {canal_log.mention}\n\n"
                    "• El postulante escribe con sus palabras\n"
                    "• Staff revisa en el log → **Aprobar** / **Rechazar**"
                ),
                color=0x1A5276,
            ).set_footer(text="Solo Owner · Co-Owner · Admin en jefe")

            view = ed.DireccionMenuView(canal_log)
            await inter.response.send_message(
                embed=emb, view=view, ephemeral=True
            )

        print("[examen_perm] /examen_direccion restringido")
    except Exception as e:
        print(f"[examen_perm] cmd: {e}")

    print("[examen_perm] OK — Owner / Co-Owner / Admin en jefe")
