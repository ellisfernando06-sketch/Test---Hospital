# -*- coding: utf-8 -*-
"""
Carga /panel y mantiene /enviar_panel_mando.
Crea canales de paneles en categoría AUTORIDADES si faltan.
"""
from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

import paneles_autoridades_config as cfg
import paneles_permisos_auth as auth
import paneles_store as store
from paneles_autoridades_ui import PanelView, embed_principal


async def _asegurar_canales(guild: discord.Guild) -> None:
    """Crea categoría y canales de paneles si no existen."""
    cat = discord.utils.get(guild.categories, name=cfg.CATEGORIA_PANELES)
    if cat is None:
        # buscar parecido
        for c in guild.categories:
            if "autoridad" in (c.name or "").lower():
                cat = c
                break
    if cat is None:
        try:
            cat = await guild.create_category(
                cfg.CATEGORIA_PANELES,
                reason="Setup paneles de autoridades",
            )
        except Exception as e:
            print(f"[paneles] categoría: {e}")
            return

    existing = {ch.name.lower(): ch for ch in cat.channels if isinstance(ch, discord.TextChannel)}
    for key, nombre in cfg.CANALES_SETUP:
        # nombre limpio sin emoji para match
        short = nombre.split(" ", 1)[-1].lower() if " " in nombre else nombre.lower()
        ch = existing.get(short) or existing.get(nombre.lower())
        if ch is None:
            # buscar en todo el guild
            ch = discord.utils.get(guild.text_channels, name=short)
        if ch is None:
            try:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    guild.me: discord.PermissionOverwrite(
                        view_channel=True, send_messages=True, embed_links=True
                    ),
                }
                ch = await guild.create_text_channel(
                    short,
                    category=cat,
                    overwrites=overwrites,
                    reason="Canal panel autoridades",
                )
            except Exception as e:
                print(f"[paneles] canal {short}: {e}")
                continue
        store.set_canal(guild.id, key, ch.id)


def registrar(bot: commands.Bot) -> None:
    # Roles co-fundadores (sin gerente)
    try:
        import roles_cofundadores

        if hasattr(roles_cofundadores, "registrar"):
            roles_cofundadores.registrar(bot)
    except Exception as e:
        print(f"[paneles] roles_cofund: {e}")

    @bot.listen("on_ready")
    async def _paneles_ready():
        if getattr(bot, "_paneles_auth_ready", False):
            return
        bot._paneles_auth_ready = True  # type: ignore
        for g in bot.guilds:
            try:
                await _asegurar_canales(g)
            except Exception as e:
                print(f"[paneles] setup canales: {e}")

    # ── /panel ──
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
                        title="❌",
                        description="Solo en el servidor.",
                        color=cfg.COLOR_ERR,
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
                if inter.response.is_done():
                    await inter.followup.send(f"❌ Error: {e}", ephemeral=True)
                else:
                    await inter.response.send_message(f"❌ Error: {e}", ephemeral=True)
            except Exception:
                pass

    # ── /enviar_panel_mando (se mantiene) ──
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
            # Panel fijo: owner_id = 0 → cualquiera con el rol correcto (re-check)
            # Usamos el id del fundador como owner de referencia del mensaje público
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

    print("[paneles_autoridades] OK — /panel + /enviar_panel_mando")
