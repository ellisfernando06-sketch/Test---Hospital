# -*- coding: utf-8 -*-
"""setup_servidor.py — /setup_servidor: organigrama + normativas."""
from __future__ import annotations
from typing import List
import discord
from discord import app_commands
from discord.ext import commands
import roles_setup
from estilos import crear_embed

async def _asegurar_categoria(guild: discord.Guild, nombre: str) -> discord.CategoryChannel:
    for c in guild.categories:
        if c.name == nombre:
            return c
    return await guild.create_category(nombre, reason="Setup servidor")

async def _asegurar_canal(guild: discord.Guild, nombre: str, category: discord.CategoryChannel) -> discord.TextChannel:
    for ch in guild.text_channels:
        if ch.name == nombre and ch.category_id == category.id:
            return ch
    return await guild.create_text_channel(nombre, category=category, reason="Setup servidor")

async def crear_canales_normativas(guild: discord.Guild) -> List[str]:
    lineas = []
    try:
        cat = await _asegurar_categoria(guild, "【📜】 normativas")
        for slug, titulo, body in [
            ("normativa-rp", "Normativa de RP", "Aquí se publica la **normativa de roleplay** del hospital."),
            ("normativa-discord", "Normativa de Discord", "Aquí se publica la **normativa de Discord** del servidor."),
            ("normativa-general", "Normativa General", "Aquí se publica la **normativa general** del servidor."),
        ]:
            ch = await _asegurar_canal(guild, slug, cat)
            lineas.append(f"✅ Canal {ch.mention} — {titulo}")
            try:
                emb = crear_embed("info", titulo, body)
                await ch.send(embed=emb)
            except Exception:
                pass
    except Exception as e:
        lineas.append(f"❌ Normativas: {e}")
    return lineas

def registrar(bot: commands.Bot) -> None:
    @bot.tree.command(
        name="setup_servidor",
        description="[Fundador] Configura organigrama, roles y canales de normativas",
    )
    @app_commands.describe(dry_run="Solo muestra lo que haría")
    async def setup_servidor(interaction: discord.Interaction, dry_run: bool = False):
        if not isinstance(interaction.user, discord.Member) or not interaction.guild:
            return await interaction.response.send_message("❌ Solo en el servidor.", ephemeral=True)

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
                "Se crearían roles del organigrama, separadores, uniformes y 3 canales de normativas.",
            )
            return await interaction.followup.send(embed=emb, ephemeral=True)

        lineas: List[str] = []
        try:
            lineas.extend(await roles_setup.configurar_organigrama(interaction.guild))
        except Exception as e:
            lineas.append(f"❌ Roles: {e}")

        try:
            lineas.extend(await crear_canales_normativas(interaction.guild))
        except Exception as e:
            lineas.append(f"❌ Canales: {e}")

        texto = "\n".join(lineas)[:3800]
        emb = crear_embed("exito", "✅ Setup completado", texto or "Sin cambios", autor=interaction.user)
        await interaction.followup.send(embed=emb, ephemeral=True)

    print("[setup_servidor] OK — /setup_servidor")
