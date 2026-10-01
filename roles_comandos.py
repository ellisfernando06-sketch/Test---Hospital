# -*- coding: utf-8 -*-
"""
roles_comandos.py — /configurar_roles /ordenar_roles /organigrama
+ !configurar_roles (prefijo) por si el slash aún no sincronizó.

Permiso: administrador del servidor O owner O key Fundador/Co-Owner.
(Así no hace falta la key antes de crear los roles.)
"""
from __future__ import annotations

from typing import List

import discord
from discord.ext import commands

import roles_config
import roles_setup
from estilos import crear_embed


def _puede_configurar(member: discord.Member) -> bool:
    """Admin / dueño del server siempre; si hay keys, Fundador/Co-Owner."""
    if member.guild_permissions.administrator:
        return True
    if member.guild and member.id == member.guild.owner_id:
        return True
    try:
        import permisos
        if permisos.member_tiene_alguna_key(
            member, "FUNDADOR_OWNER", "CO_OWNER", "OWNER"
        ):
            return True
    except Exception:
        pass
    return False


def _partir(texto: str, max_len: int = 3800) -> List[str]:
    if not texto.strip():
        return ["*(sin cambios)*"]
    return [texto[i : i + max_len] for i in range(0, len(texto), max_len)]


async def _enviar_resumen_inter(inter: discord.Interaction, titulo: str, lineas: List[str], tipo: str = "exito"):
    texto = "\n".join(lineas) if lineas else "*(sin cambios)*"
    for i, bloque in enumerate(_partir(texto)):
        emb = crear_embed(
            tipo,
            titulo if i == 0 else f"{titulo} (cont.)",
            bloque,
            autor=inter.user,
            footer_extra="Organigrama oficial",
        )
        await inter.followup.send(embed=emb, ephemeral=True)


async def _enviar_resumen_ctx(ctx: commands.Context, titulo: str, lineas: List[str], tipo: str = "exito"):
    texto = "\n".join(lineas) if lineas else "*(sin cambios)*"
    for i, bloque in enumerate(_partir(texto)):
        emb = crear_embed(
            tipo,
            titulo if i == 0 else f"{titulo} (cont.)",
            bloque,
            autor=ctx.author,
            footer_extra="Organigrama oficial",
        )
        await ctx.send(embed=emb)


def registrar(bot: commands.Bot) -> None:
    for name in ("configurar_roles", "ordenar_roles", "organigrama"):
        try:
            bot.tree.remove_command(name)
        except Exception:
            pass
    try:
        bot.remove_command("configurar_roles")
    except Exception:
        pass

    @bot.tree.command(
        name="configurar_roles",
        description="[Admin] Crea/detecta TODOS los roles del organigrama y guarda keys",
    )
    async def configurar_roles(inter: discord.Interaction):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _puede_configurar(inter.user):
            return await inter.response.send_message(
                embed=crear_embed(
                    "error",
                    "Sin permiso",
                    "Necesitas ser **Administrador** del servidor o **Fundador/Co-Owner**.",
                ),
                ephemeral=True,
            )
        await inter.response.defer(ephemeral=True)
        try:
            resumen = await roles_setup.configurar_organigrama(inter.guild)
        except Exception as e:
            return await inter.followup.send(
                embed=crear_embed("error", "Error al configurar roles", f"```{type(e).__name__}: {e}```"),
                ephemeral=True,
            )
        await _enviar_resumen_inter(inter, "✅ Organigrama actualizado", resumen, "exito")

    @bot.tree.command(
        name="ordenar_roles",
        description="[Admin] Reordena roles según el organigrama",
    )
    async def ordenar_roles_cmd(inter: discord.Interaction):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _puede_configurar(inter.user):
            return await inter.response.send_message(
                embed=crear_embed("error", "Sin permiso", "Solo Admin o Fundador/Co-Owner."),
                ephemeral=True,
            )
        await inter.response.defer(ephemeral=True)
        try:
            resumen = await roles_setup.ordenar_roles(inter.guild)
        except Exception as e:
            return await inter.followup.send(
                embed=crear_embed("error", "Error", str(e)), ephemeral=True
            )
        await _enviar_resumen_inter(inter, "📑 Roles ordenados", resumen, "info")

    @bot.tree.command(
        name="organigrama",
        description="Muestra el organigrama oficial del hospital",
    )
    async def organigrama_cmd(inter: discord.Interaction):
        await inter.response.defer(ephemeral=True)
        emb = crear_embed(
            "info",
            "Organigrama oficial",
            "Jerarquía del hospital (mayor → menor).",
            autor=inter.user,
        )
        for sec_key, sec in roles_config.SECCIONES.items():
            lineas = [
                f"• **{roles_config.nombre_key(k)}**" for k in sec.get("keys", [])
            ]
            emb.add_field(
                name=f"{sec.get('emoji', '')} {sec.get('nombre', sec_key)}",
                value="\n".join(lineas)[:1020] or "—",
                inline=False,
            )
        # Sistema
        if "INACTIVIDAD_JUSTIFICADA" in roles_config.KEYS_NOMBRES:
            emb.add_field(
                name="⚙️ Sistema",
                value=f"• **{roles_config.nombre_key('INACTIVIDAD_JUSTIFICADA')}**",
                inline=False,
            )
        await inter.followup.send(embed=emb, ephemeral=True)

    # Respaldo por prefijo (si el slash no aparece aún)
    @bot.command(name="configurar_roles")
    async def configurar_roles_prefijo(ctx: commands.Context):
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return
        if not _puede_configurar(ctx.author):
            return await ctx.reply("❌ Solo **Administrador** o Fundador/Co-Owner.")
        msg = await ctx.reply("🔄 Escaneando y actualizando roles del organigrama…")
        try:
            resumen = await roles_setup.configurar_organigrama(ctx.guild)
        except Exception as e:
            return await msg.edit(content=f"❌ Error: `{type(e).__name__}: {e}`")
        await msg.edit(content="✅ Organigrama actualizado (detalle abajo).")
        await _enviar_resumen_ctx(ctx, "✅ Organigrama actualizado", resumen, "exito")

    print("[roles_comandos] OK — /configurar_roles + !configurar_roles")
