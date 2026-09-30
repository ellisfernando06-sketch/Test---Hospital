# -*- coding: utf-8 -*-
"""roles_comandos.py — /configurar_roles /ordenar_roles /organigrama"""
from __future__ import annotations
from typing import List
import discord
from discord.ext import commands
import roles_config
import roles_setup
from estilos import crear_embed

def _es_autoridad(member: discord.Member) -> bool:
    try:
        import permisos
        return permisos.member_tiene_alguna_key(member, "FUNDADOR_OWNER", "CO_OWNER", "OWNER")
    except Exception:
        return bool(member.guild_permissions.administrator)

def _partir(texto: str, max_len: int = 3800) -> List[str]:
    if not texto.strip():
        return ["*(sin cambios)*"]
    return [texto[i:i + max_len] for i in range(0, len(texto), max_len)]

async def _enviar_resumen(inter, titulo, lineas, tipo="exito"):
    texto = "\n".join(lineas) if lineas else "*(sin cambios)*"
    for i, bloque in enumerate(_partir(texto)):
        emb = crear_embed(tipo, titulo if i == 0 else f"{titulo} (cont.)", bloque, autor=inter.user, footer_extra="Organigrama oficial")
        await inter.followup.send(embed=emb, ephemeral=True)

def registrar(bot: commands.Bot) -> None:
    for name in ("configurar_roles", "ordenar_roles", "organigrama"):
        try:
            bot.tree.remove_command(name)
        except Exception:
            pass

    @bot.tree.command(name="configurar_roles", description="[Fundador] Crea/detecta roles del organigrama y guarda keys")
    async def configurar_roles(inter: discord.Interaction):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message("❌ Solo en el servidor.", ephemeral=True)
        if not _es_autoridad(inter.user):
            return await inter.response.send_message(embed=crear_embed("error", "Sin permiso", "Solo **Fundador y Owner** o **Co-Owner**."), ephemeral=True)
        await inter.response.defer(ephemeral=True)
        try:
            resumen = await roles_setup.configurar_organigrama(inter.guild)
        except Exception as e:
            return await inter.followup.send(embed=crear_embed("error", "Error", f"```{type(e).__name__}: {e}```"), ephemeral=True)
        await _enviar_resumen(inter, "✅ Organigrama configurado", resumen, "exito")

    @bot.tree.command(name="ordenar_roles", description="[Fundador] Reordena roles según organigrama")
    async def ordenar_roles_cmd(inter: discord.Interaction):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message("❌ Solo en el servidor.", ephemeral=True)
        if not _es_autoridad(inter.user):
            return await inter.response.send_message(embed=crear_embed("error", "Sin permiso", "Solo Fundador/Co-Owner."), ephemeral=True)
        await inter.response.defer(ephemeral=True)
        try:
            resumen = await roles_setup.ordenar_roles(inter.guild)
        except Exception as e:
            return await inter.followup.send(embed=crear_embed("error", "Error", str(e)), ephemeral=True)
        await _enviar_resumen(inter, "📑 Roles ordenados", resumen, "info")

    @bot.tree.command(name="organigrama", description="Muestra el organigrama oficial")
    async def organigrama_cmd(inter: discord.Interaction):
        await inter.response.defer(ephemeral=True)
        emb = crear_embed("info", "Organigrama oficial", "Jerarquía del hospital (mayor → menor).", autor=inter.user)
        for sec_key, sec in roles_config.SECCIONES.items():
            lineas = [f"• **{roles_config.nombre_key(k)}**" for k in sec.get("keys", [])]
            emb.add_field(name=f"{sec.get('emoji','')} {sec.get('nombre', sec_key)}", value="\n".join(lineas)[:1020] or "—", inline=False)
        await inter.followup.send(embed=emb, ephemeral=True)

    print("[roles_comandos] OK")
