# -*- coding: utf-8 -*-
"""
reglamento_hospital.py — Reglamento del Hospital General.

Se guarda en el MISMO almacén que /agregar_reglamento,
para que aparezca en el menú de /publicar_reglamento.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

import discord
from discord import app_commands
from discord.ext import commands

import config

_TITULO = "Reglamento del Hospital"
_ID = "reglamento-del-hospital"


def _es_autoridad(member: discord.Member) -> bool:
    if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
        return True
    try:
        import permisos

        return permisos.member_tiene_alguna_key(
            member,
            "FUNDADOR_OWNER",
            "CO_OWNER",
            "OWNER",
            "CANCILLER",
            "DIR_GENERAL",
            "DIRECTOR_GENERAL",
            "ADMIN_JEFE",
            "ADMIN",
        )
    except Exception:
        return False


def _guardar(texto: str, por: int) -> dict:
    import anuncios_largos as al

    # Mismo almacén → visible en /publicar_reglamento
    return al._guardar_item(_TITULO, texto, por, rid=_ID)


def _obtener() -> Optional[dict]:
    import anuncios_largos as al

    it = al._obtener(_ID)
    if it:
        return it
    for x in al._listar_items():
        if (x.get("titulo") or "").lower() == _TITULO.lower():
            return x
        if (x.get("id") or "") == _ID:
            return x
    return None


def _embeds(texto: str, autor: discord.abc.User) -> List[discord.Embed]:
    hospital = getattr(config, "NOMBRE_HOSPITAL", None) or "Hospital General"
    partes: List[str] = []
    t = (texto or "").strip()
    max_len = 3900
    while t:
        if len(t) <= max_len:
            partes.append(t)
            break
        cut = t.rfind("\n", 0, max_len)
        if cut < max_len // 3:
            cut = max_len
        partes.append(t[:cut].rstrip())
        t = t[cut:].lstrip("\n")
    if not partes:
        partes = ["_Sin contenido_"]

    embeds: List[discord.Embed] = []
    total = len(partes)
    for i, parte in enumerate(partes):
        title = f"📜 {_TITULO}" if i == 0 else f"📜 {_TITULO} ({i + 1}/{total})"
        emb = discord.Embed(
            title=title,
            description=parte,
            color=0x1A5276,
            timestamp=datetime.now(timezone.utc),
        )
        if i == 0:
            emb.set_author(
                name=f"{hospital} · Normativa institucional",
                icon_url=getattr(getattr(autor, "display_avatar", None), "url", None),
            )
        emb.set_footer(
            text=f"{hospital}  ·  Reglamento oficial"
            + (f"  ·  {i + 1}/{total}" if total > 1 else "")
        )
        embeds.append(emb)
    return embeds


def registrar(bot: commands.Bot) -> None:
    for n in ("reglamento_hospital", "publicar_reglamento_hospital"):
        try:
            bot.tree.remove_command(n)
        except Exception:
            pass

    @bot.tree.command(
        name="reglamento_hospital",
        description="[Autoridad] Guarda el Reglamento del Hospital (sale en /publicar_reglamento)",
    )
    @app_commands.describe(
        texto="Texto completo del reglamento del hospital",
        publicar_en="Canal opcional para publicarlo ya",
    )
    async def reglamento_hospital(
        inter: discord.Interaction,
        texto: str,
        publicar_en: Optional[discord.TextChannel] = None,
    ):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _es_autoridad(inter.user):
            return await inter.response.send_message(
                "❌ Solo autoridades (Owner, Canciller, Dir. General, Admin).",
                ephemeral=True,
            )
        await inter.response.defer(ephemeral=True)
        reg = _guardar(texto, inter.user.id)
        msg = (
            f"✅ **{_TITULO}** guardado "
            f"(`{reg.get('id')}`, {len(texto)} caracteres).\n"
            f"Aparece en el menú de `/publicar_reglamento`.\n"
            f"También: `/publicar_reglamento_hospital`."
        )
        if publicar_en:
            embeds = _embeds(texto, inter.user)
            for emb in embeds:
                await publicar_en.send(embed=emb)
            msg += f"\n📢 Publicado en {publicar_en.mention}."
        await inter.followup.send(msg, ephemeral=True)

    @bot.tree.command(
        name="publicar_reglamento_hospital",
        description="[Autoridad] Publica el Reglamento del Hospital guardado",
    )
    @app_commands.describe(canal="Canal donde se publica")
    async def publicar_reglamento_hospital(
        inter: discord.Interaction, canal: discord.TextChannel
    ):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _es_autoridad(inter.user):
            return await inter.response.send_message(
                "❌ Solo autoridades.", ephemeral=True
            )
        reg = _obtener()
        if not reg or not (reg.get("texto") or "").strip():
            return await inter.response.send_message(
                "❌ No hay Reglamento del Hospital guardado.\n"
                "Usa `/reglamento_hospital` o `/agregar_reglamento` "
                "con título **Reglamento del Hospital**.",
                ephemeral=True,
            )
        await inter.response.defer(ephemeral=True)
        embeds = _embeds(reg["texto"], inter.user)
        for emb in embeds:
            await canal.send(embed=emb)
        await inter.followup.send(
            f"✅ **{_TITULO}** publicado en {canal.mention} "
            f"({len(embeds)} mensaje(s)).",
            ephemeral=True,
        )

    print("[reglamento_hospital] OK — mismo almacén que /publicar_reglamento")
