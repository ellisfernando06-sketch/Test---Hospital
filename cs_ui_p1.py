# -*- coding: utf-8 -*
"""cs_ui_patches helpers."""
from __future__ import annotations
import re
import asyncio
from datetime import datetime, timezone
from typing import List

_CAT_MAP = {
    "sancion": ["staff", "disciplina", "sanciones", "rrhh"],
    "apelacion": ["staff", "apelaciones", "disciplina"],
    "investigacion": ["staff", "investigaciones", "rrhh", "disciplina"],
    "reporte": ["staff", "reportes", "disciplina"],
    "general": ["información general", "informacion general", "información", "informacion", "general", "info"],
    "consulta": ["información general", "informacion general", "información", "consultas", "info"],
}

def _resolver_cat(guild, categoria_key: str):
    import discord
    import config
    nombres = _CAT_MAP.get(categoria_key) or _CAT_MAP["general"]
    mapa = getattr(config, "TICKET_CATEGORIAS", None) or {}
    for k in (categoria_key, "staff" if categoria_key in ("sancion", "apelacion", "investigacion", "reporte") else "general"):
        cid = mapa.get(k) if isinstance(mapa, dict) else None
        if cid:
            ch = guild.get_channel(int(cid))
            if isinstance(ch, discord.CategoryChannel):
                return ch
    for cat in guild.categories:
        cn = (cat.name or "").lower()
        for n in nombres:
            if n and n in cn:
                return cat
    fallback = getattr(config, "TICKET_CATEGORIA_ID", None)
    if fallback:
        ch = guild.get_channel(int(fallback))
        if isinstance(ch, discord.CategoryChannel):
            return ch
    return None


def _parse_user_ids(texto: str) -> List[int]:
    ids = []
    for m in re.finditer(r"<@!?(\d+)>", texto or ""):
        ids.append(int(m.group(1)))
    for m in re.finditer(r"\b(\d{15,20})\b", texto or ""):
        ids.append(int(m.group(1)))
    return list(dict.fromkeys(ids))


def _ids_desde_campos(campos: dict) -> List[int]:
    ids = []
    for k, v in (campos or {}).items():
        kl = str(k).lower()
        if any(x in kl for x in ("usuario", "involucrad", "sancionad", "reportad", "acusad")):
            ids.extend(_parse_user_ids(str(v)))
        else:
            ids.extend(_parse_user_ids(str(v)))
    return list(dict.fromkeys(ids))


async def _hacer_transcripcion(channel, bot, solicitud_id, reg, cerrado_por):
    from ticket_transcript import collect_messages, render_html, html_to_file, embed_resumen
    msgs = await collect_messages(channel, limit=500)
    cat_name = channel.category.name if channel.category else "—"
    opener = "—"
    if reg and reg.get("usuario_id") and channel.guild:
        m = channel.guild.get_member(int(reg["usuario_id"]))
        opener = m.mention if m else str(reg["usuario_id"])
    titulo = f"Solicitud #{int(solicitud_id):04d}"
    if reg and reg.get("categoria"):
        titulo += f" · {reg['categoria']}"
    html_str = render_html(
        titulo=titulo, canal_nombre=channel.name, abierto_por=opener,
        cerrado_por=cerrado_por, categoria=cat_name,
        creado=msgs[0].created_at if msgs else channel.created_at,
        cerrado=datetime.now(timezone.utc), messages=msgs, guild=channel.guild,
    )
    archivo = html_to_file(html_str, filename=f"solicitud-{int(solicitud_id):04d}.html")
    emb = embed_resumen(
        titulo=titulo, canal_nombre=channel.name, abierto_por=opener,
        cerrado_por=cerrado_por, categoria=cat_name, n_msgs=len(msgs), color=0x8E44AD,
    )
    dest = None
    try:
        import logs_store
        cid = logs_store.get_canal_id("log_tickets") or logs_store.get_canal_id("log_solicitudes")
        if cid:
            dest = bot.get_channel(int(cid))
    except Exception:
        pass
    if not dest:
        import config
        canales = getattr(config, "CANALES", {}) or {}
        cid = canales.get("log_tickets") or canales.get("log_solicitudes")
        if cid:
            dest = bot.get_channel(int(cid))
    if dest:
        await dest.send(embed=emb, file=archivo)
    else:
        await channel.send(embed=emb, file=archivo)
    return len(msgs)
