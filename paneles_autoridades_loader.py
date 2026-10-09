# -*- coding: utf-8 -*-
"""/panel + /enviar_panel_mando + canales con diseño →【emoji】."""
from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

import paneles_autoridades_config as cfg
import paneles_permisos_auth as auth
import paneles_store as store
from paneles_autoridades_ui import PanelView, embed_principal

try:
    from paneles_canales_setup import asegurar_canales_autoridades
except Exception:
    asegurar_canales_autoridades = None  # type: ignore


def registrar(bot: commands.Bot) -> None:
    try:
        import roles_cofundadores

        if hasattr(roles_cofundadores, "registrar"):
            roles_cofundadores.registrar(bot)
    except Exception as e:
        print(f"[paneles] roles: {e}")

    try:
        import paneles_canales_setup as pcs

        if hasattr(pcs, "registrar"):
            pcs.registrar(bot)
    except Exception as e:
        print(f"[paneles] canales: {e}")

    @bot.listen("on_ready")
    async def _paneles_ready():
        if getattr(bot, "_paneles_auth_ready2", False):
            return
        bot._paneles_auth_ready2 = True  # type: ignore
        if asegurar_canales_autoridades:
            for g in bot.guilds:
                try:
                    await asegurar_canales_autoridades(g)
                except Exception as e:
                    print(f"[paneles] setup: {e}")

    try:
        bot.tree.remove_command("panel")
    except Exception:
        pass

    @bot.tree.command(
        name="panel",
        description="Abre tu panel de autoridad del Hospital General",
    )
    async def panel_cmd(inter: discord.Interaction):
        try:
            if not inter.guild or not isinstance(inter.user, discord.Member):
                return await inter.response.send_message(
                    embed=discord.Embed(
                        title="❌", description="Solo en el servidor.", color=cfg.COLOR_ERR
                    ),
                    ephemeral=True,
                )
            p = auth.panel_de(inter.user)
            if not p:
                store.auditar(
                    inter.guild.id,
                    inter.user.id,
                    str(inter.user),
                    "—",
                    "panel_intento",
                    resultado="denegado",
                )
                return await inter.response.send_message(
                    embed=discord.Embed(
                        title="❌ Acceso denegado",
                        description="No posees la autoridad requerida",
                        color=cfg.COLOR_ERR,
                    ),
                    ephemeral=True,
                )
            view = PanelView(p, inter.user.id)
            await inter.response.send_message(
                embed=embed_principal(inter.user, p),
                view=view,
                ephemeral=True,
            )
            store.auditar(
                inter.guild.id,
                inter.user.id,
                str(inter.user),
                p,
                "abrir_panel",
                resultado="ok",
            )
        except Exception as e:
            print(f"[paneles] /panel: {e}")
            try:
                msg = f"❌ Error: {e}"
                if inter.response.is_done():
                    await inter.followup.send(msg, ephemeral=True)
                else:
                    await inter.response.send_message(msg, ephemeral=True)
            except Exception:
                pass

    try:
        bot.tree.remove_command("enviar_panel_mando")
    except Exception:
        pass

    @bot.tree.command(
        name="enviar_panel_mando",
        description="[Fundador] Publica panel fijo de autoridades en un canal",
    )
    @app_commands.describe(canal="Canal", cual="Qué panel")
    @app_commands.choices(
        cual=[
            app_commands.Choice(name="Fundador · Mando General", value="fundador"),
            app_commands.Choice(name="Gobernanza", value="gobernanza"),
            app_commands.Choice(name="Interinstitucional", value="interinstitucional"),
            app_commands.Choice(name="Calidad", value="calidad"),
            app_commands.Choice(name="Los 4", value="todos"),
        ]
    )
    async def enviar_panel_mando(
        inter: discord.Interaction,
        canal: discord.TextChannel,
        cual: app_commands.Choice[str],
    ):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message("❌ Solo en servidor.", ephemeral=True)
        if not auth.es_fundador(inter.user):
            return await inter.response.send_message(
                embed=discord.Embed(
                    title="❌ Sin permiso",
                    description="Solo el **Fundador del Hospital**.",
                    color=cfg.COLOR_ERR,
                ),
                ephemeral=True,
            )
        await inter.response.defer(ephemeral=True)
        val = cual.value
        enviados = []

        async def one(kind: str):
            view = PanelView(kind, inter.user.id)
            await canal.send(embed=embed_principal(inter.user, kind), view=view)
            enviados.append(kind)

        try:
            if val == "todos":
                for k in ("fundador", "gobernanza", "interinstitucional", "calidad"):
                    await one(k)
            else:
                await one(val)
        except Exception as e:
            return await inter.followup.send(f"❌ {e}", ephemeral=True)

        store.auditar(
            inter.guild.id,
            inter.user.id,
            str(inter.user),
            "Fundador",
            "enviar_panel_mando",
            canal.mention,
            "ok",
        )
        await inter.followup.send(
            embed=discord.Embed(
                title="✅ Paneles publicados",
                description=f"{canal.mention}\n{', '.join(enviados)}",
                color=cfg.COLOR_OK,
            ),
            ephemeral=True,
        )

    print("[paneles_autoridades] OK — /panel + canales →【emoji】")
