# -*- coding: utf-8 -*-
"""
Crea/renombra canales de autoridades con diseño →【emoji】nombre
y el chat de fundación.
"""
from __future__ import annotations

import discord
from discord.ext import commands

import paneles_autoridades_config as cfg
import paneles_store as store


def _norm(s: str) -> str:
    return (s or "").lower().strip()


async def asegurar_canales_autoridades(guild: discord.Guild) -> list:
    """Crea categoría + canales; renombra los viejos al diseño oficial."""
    hechos = []

    # Categoría
    cat = discord.utils.get(guild.categories, name=cfg.CATEGORIA_PANELES)
    if cat is None:
        for c in guild.categories:
            n = _norm(c.name)
            if "autoridad" in n or ("👑" in (c.name or "") and "autor" in n):
                cat = c
                break
    if cat is None:
        try:
            cat = await guild.create_category(
                cfg.CATEGORIA_PANELES,
                reason="Setup autoridades Hospital General",
            )
            hechos.append(f"categoría {cfg.CATEGORIA_PANELES}")
        except Exception as e:
            print(f"[paneles_canales] cat: {e}")
            return hechos
    elif cat.name != cfg.CATEGORIA_PANELES:
        try:
            await cat.edit(name=cfg.CATEGORIA_PANELES, reason="Diseño canales autoridades")
            hechos.append(f"categoría renombrada → {cfg.CATEGORIA_PANELES}")
        except Exception as e:
            print(f"[paneles_canales] rename cat: {e}")

    # Mapa de todos los text channels
    by_name = {_norm(ch.name): ch for ch in guild.text_channels}

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        guild.me: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, embed_links=True, manage_messages=True
        ),
    }

    for item in cfg.CANALES_SETUP:
        if len(item) == 3:
            key, nombre_oficial, aliases = item
        else:
            key, nombre_oficial = item[0], item[1]
            aliases = [key]

        ch = None
        # por ID guardado
        rid = store.get_canal(guild.id, key)
        if rid:
            ch = guild.get_channel(int(rid))

        # por nombre oficial
        if ch is None:
            ch = by_name.get(_norm(nombre_oficial))

        # por aliases / nombres viejos
        if ch is None:
            for a in aliases:
                ch = by_name.get(_norm(a))
                if ch:
                    break
                # match parcial
                for nm, channel in by_name.items():
                    if _norm(a) in nm or nm in _norm(a):
                        ch = channel
                        break
                if ch:
                    break

        if ch is None:
            try:
                ch = await guild.create_text_channel(
                    nombre_oficial,
                    category=cat,
                    overwrites=overwrites,
                    reason="Canal autoridades · diseño Hospital General",
                )
                hechos.append(f"creado {nombre_oficial}")
                by_name[_norm(nombre_oficial)] = ch
            except Exception as e:
                print(f"[paneles_canales] create {key}: {e}")
                continue
        else:
            # Renombrar al diseño oficial
            if ch.name != nombre_oficial:
                try:
                    await ch.edit(name=nombre_oficial, reason="Diseño →【emoji】canales")
                    hechos.append(f"renombrado → {nombre_oficial}")
                except Exception as e:
                    print(f"[paneles_canales] rename {ch.name}: {e}")
            # Mover a la categoría correcta
            if cat and ch.category_id != cat.id:
                try:
                    await ch.edit(category=cat, reason="Organizar en AUTORIDADES")
                    hechos.append(f"movido a categoría: {nombre_oficial}")
                except Exception as e:
                    print(f"[paneles_canales] move {ch.name}: {e}")

        if ch:
            store.set_canal(guild.id, key, ch.id)

    return hechos


def registrar(bot: commands.Bot) -> None:
    @bot.listen("on_ready")
    async def _canales_auth_ready():
        if getattr(bot, "_paneles_canales_done", False):
            return
        bot._paneles_canales_done = True  # type: ignore
        for g in bot.guilds:
            try:
                hechos = await asegurar_canales_autoridades(g)
                if hechos:
                    print(f"[paneles_canales] {g.name}: {', '.join(hechos)}")
            except Exception as e:
                print(f"[paneles_canales] {g.name}: {e}")

    print("[paneles_canales] OK — diseño →【emoji】 + chat-fundacion")
