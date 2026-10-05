# -*- coding: utf-8 -*-
"""
Cuarentena al terminar el examen de verificación.
Usa assets/cuarentena.jpg (imagen oficial del Hospital General).
"""
from __future__ import annotations

import pathlib
from typing import Optional

import discord

_NOMBRES = ("⏳ Cuarentena", "Cuarentena", "cuarentena", "Quarantine")


def _ruta_imagen() -> Optional[pathlib.Path]:
    base = pathlib.Path(__file__).resolve().parent
    for p in (
        base / "assets" / "cuarentena.jpg",
        base / "assets" / "cuarentena.png",
        base / "cuarentena.jpg",
    ):
        if p.is_file() and p.stat().st_size > 1000:
            return p
    return None


async def rol_cuarentena(guild: discord.Guild) -> Optional[discord.Role]:
    for r in guild.roles:
        rn = (r.name or "").lower()
        if "cuarentena" in rn or "quarantine" in rn:
            return r
    try:
        return await guild.create_role(
            name="⏳ Cuarentena",
            colour=discord.Colour.dark_grey(),
            hoist=True,
            mentionable=False,
            reason="Verificación hospitalaria",
        )
    except Exception:
        return None


def embed_cuarentena() -> discord.Embed:
    emb = discord.Embed(
        title="⏳ Cuarentena de verificación",
        description=(
            "**Hospital General**\n\n"
            "Tu examen fue enviado correctamente.\n"
            "Estás en **cuarentena** hasta que el staff **apruebe** o **niegue** "
            "tu entrada al servidor.\n\n"
            "Por favor permanece a la espera y sigue las indicaciones del personal."
        ),
        color=0x1A5F5A,
    )
    emb.set_footer(text="Hospital General · Salud · Disciplina · Servicio")
    return emb


async def _enviar_aviso_cuarentena(member: discord.Member) -> None:
    emb = embed_cuarentena()
    path = _ruta_imagen()
    file = None
    if path:
        try:
            file = discord.File(str(path), filename="cuarentena.jpg")
            emb.set_image(url="attachment://cuarentena.jpg")
        except Exception as e:
            print(f"[cuarentena] file: {e}")
            file = None
    try:
        if file:
            await member.send(embed=emb, file=file)
        else:
            await member.send(embed=emb)
    except Exception as e:
        print(f"[cuarentena] dm: {e}")


async def poner(member: discord.Member) -> None:
    rol = await rol_cuarentena(member.guild)
    if rol and rol not in member.roles:
        try:
            await member.add_roles(rol, reason="Examen enviado — espera staff")
        except Exception as e:
            print(f"[cuarentena] add: {e}")
    await _enviar_aviso_cuarentena(member)


async def quitar(member: discord.Member) -> None:
    for r in list(member.roles):
        rn = (r.name or "").lower()
        if "cuarentena" in rn or "quarantine" in rn:
            try:
                await member.remove_roles(r, reason="Verificación resuelta")
            except Exception:
                pass


def registrar(bot) -> None:
    try:
        import verificacion as ver
    except Exception as e:
        print(f"[verificacion_cuarentena] no ver: {e}")
        return

    cls = getattr(ver, "ExamenView", None)
    if cls is not None and hasattr(cls, "_on_answer"):
        _orig = cls._on_answer

        async def _on_answer_wrapped(self, interaction, *args, **kwargs):
            await _orig(self, interaction, *args, **kwargs)
            try:
                npreg = len(getattr(ver, "PREGUNTAS", []) or [])
                if getattr(self, "idx", 0) >= npreg:
                    guild = interaction.client.get_guild(self.guild_id)
                    if guild:
                        member = guild.get_member(self.user_id)
                        if member:
                            await poner(member)
            except Exception as e:
                print(f"[cuarentena] wrap: {e}")

        cls._on_answer = _on_answer_wrapped

    @bot.listen("on_interaction")
    async def _cuarentena_on_decision(inter: discord.Interaction):
        if inter.type != discord.InteractionType.component:
            return
        data = getattr(inter, "data", None) or {}
        cid = str(data.get("custom_id") or "")
        if not any(x in cid.lower() for x in ("aprob", "approv", "negar", "deny")):
            return
        if not inter.guild:
            return
        try:
            import re

            msg = inter.message
            if not msg or not msg.embeds:
                return
            m = re.search(r"<@!?(\d+)>" , msg.embeds[0].description or "")
            if not m:
                return
            member = inter.guild.get_member(int(m.group(1)))
            if member:
                await quitar(member)
        except Exception:
            pass

    # Comando staff para publicar la imagen en un canal de espera
    from discord import app_commands

    @bot.tree.command(
        name="imagen_cuarentena",
        description="[Staff] Publica la imagen oficial de cuarentena en un canal",
    )
    @app_commands.describe(canal="Canal donde colocar la imagen")
    async def imagen_cuarentena(
        inter: discord.Interaction, canal: discord.TextChannel
    ):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not (
            inter.user.guild_permissions.administrator
            or inter.user.guild_permissions.manage_guild
        ):
            return await inter.response.send_message(
                "❌ Solo staff.", ephemeral=True
            )
        path = _ruta_imagen()
        if not path:
            return await inter.response.send_message(
                "❌ No está `assets/cuarentena.jpg`. Reinicia el bot para instalarla.",
                ephemeral=True,
            )
        emb = embed_cuarentena()
        emb.set_image(url="attachment://cuarentena.jpg")
        f = discord.File(str(path), filename="cuarentena.jpg")
        await canal.send(embed=emb, file=f)
        await inter.response.send_message(
            f"✅ Imagen de cuarentena en {canal.mention}", ephemeral=True
        )

    print("[verificacion_cuarentena] OK — imagen oficial + /imagen_cuarentena")
