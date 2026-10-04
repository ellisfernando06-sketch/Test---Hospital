# -*- coding: utf-8 -*-
"""
setup_permisos_protect.py
El staff manda en permisos de canales/categorías.
El bot NO reescribe overwrites de lo que ya existe.
"""
from __future__ import annotations

from typing import Dict, Optional

import discord


def registrar(bot) -> None:
    try:
        import setup_servidor as ss
    except Exception as e:
        print(f"[setup_permisos_protect] sin setup_servidor: {e}")
        return

    _base = ss._base_de_nombre

    async def _asegurar_categoria(
        guild: discord.Guild,
        nombre: str,
        overwrites: Optional[Dict] = None,
    ) -> discord.CategoryChannel:
        base_cat = _base(nombre).lower()
        for c in guild.categories:
            if c.name == nombre:
                return c  # no tocar permisos
            if _base(c.name).lower() == base_cat:
                try:
                    if c.name != nombre:
                        await c.edit(name=nombre, reason="Diseño (sin tocar permisos)")
                except Exception:
                    pass
                return c
        kwargs = {"reason": "Setup servidor"}
        if overwrites:
            kwargs["overwrites"] = overwrites
        return await guild.create_category(nombre, **kwargs)

    async def _asegurar_canal_texto(
        guild: discord.Guild,
        nombre: str,
        base: str,
        category: discord.CategoryChannel,
        overwrites: Optional[Dict] = None,
    ) -> discord.TextChannel:
        base_l = (base or _base(nombre)).lower()
        for ch in guild.text_channels:
            if ch.name == nombre and ch.category_id == category.id:
                return ch
        for ch in guild.text_channels:
            if ch.category_id == category.id and (
                _base(ch.name) == base_l or (ch.name or "").lower() == base_l
            ):
                try:
                    if ch.name != nombre:
                        await ch.edit(name=nombre, reason="Diseño (sin tocar permisos)")
                except Exception:
                    pass
                return ch
        for ch in guild.text_channels:
            if _base(ch.name) == base_l or (ch.name or "").lower() == base_l:
                try:
                    kw = {"reason": "Diseño/categoría (sin permisos)"}
                    if ch.name != nombre:
                        kw["name"] = nombre
                    if ch.category_id != category.id:
                        kw["category"] = category
                    if len(kw) > 1:
                        await ch.edit(**kw)
                except Exception:
                    pass
                return ch
        kwargs = {"category": category, "reason": "Setup servidor"}
        if overwrites:
            kwargs["overwrites"] = overwrites
        return await guild.create_text_channel(nombre, **kwargs)

    async def _asegurar_voz(
        guild: discord.Guild,
        nombre: str,
        base: str,
        category: discord.CategoryChannel,
        tipo: str,
        overwrites: Optional[Dict] = None,
    ) -> discord.abc.GuildChannel:
        base_l = (base or _base(nombre)).lower()
        candidatos = list(guild.voice_channels) + list(
            getattr(guild, "stage_channels", []) or []
        )
        for ch in candidatos:
            if ch.name == nombre and ch.category_id == category.id:
                return ch
        for ch in candidatos:
            if _base(ch.name) == base_l or (ch.name or "").lower() == base_l:
                try:
                    kw = {"reason": "Diseño voz (sin tocar permisos)"}
                    if ch.name != nombre:
                        kw["name"] = nombre
                    if ch.category_id != category.id:
                        kw["category"] = category
                    if len(kw) > 1:
                        await ch.edit(**kw)
                except Exception:
                    pass
                return ch
        kwargs = {"category": category, "reason": "Setup servidor voz"}
        if overwrites:
            kwargs["overwrites"] = overwrites
        if tipo == "stage":
            try:
                return await guild.create_stage_channel(nombre, **kwargs)
            except Exception:
                return await guild.create_voice_channel(nombre, **kwargs)
        return await guild.create_voice_channel(nombre, **kwargs)

    ss._asegurar_categoria = _asegurar_categoria
    ss._asegurar_canal_texto = _asegurar_canal_texto
    ss._asegurar_voz = _asegurar_voz
    print("[setup_permisos_protect] OK — permisos de canales: manda el staff")
