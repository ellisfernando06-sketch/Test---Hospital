# -*- coding: utf-8 -*-
"""anuncios_largos.py — Anuncios y varios reglamentos (guardar / publicar)."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

import discord
from discord import app_commands, ui
from discord.ext import commands

import config
from permisos import require_key

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_REGLAMENTO_PATH = os.path.join(_DATA_DIR, "reglamento.json")

_MAX_EMBED_DESC = 3900


def _split_text(text: str, max_len: int = _MAX_EMBED_DESC) -> List[str]:
    text = (text or "").strip()
    if not text:
        return [""]
    if len(text) <= max_len:
        return [text]
    chunks: List[str] = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        cut = text.rfind("\n", 0, max_len)
        if cut < max_len // 3:
            cut = max_len
        chunks.append(text[:cut].rstrip())
        text = text[cut:].lstrip("\n")
    return chunks


def _slug(titulo: str) -> str:
    t = (titulo or "").strip().lower()
    t = re.sub(r"[^a-z0-9áéíóúüñ\s\-]", "", t, flags=re.I)
    t = re.sub(r"\s+", "-", t).strip("-")
    return (t or "reglamento")[:80]


def _embeds_anuncio(
    titulo: str,
    cuerpo: str,
    autor: discord.abc.User,
    color: int = 0x2C3E50,
    subtitulo: str = "",
) -> List[discord.Embed]:
    partes = _split_text(cuerpo)
    total = len(partes)
    embeds: List[discord.Embed] = []
    for i, parte in enumerate(partes):
        if i == 0:
            title = f"📢 {titulo}"
            if subtitulo:
                title = f"📢 {subtitulo} · {titulo}"
        else:
            title = f"📢 {titulo} (parte {i + 1}/{total})"
        emb = discord.Embed(
            title=title,
            description=parte or "_Sin contenido_",
            color=color,
            timestamp=datetime.now(timezone.utc),
        )
        if i == 0:
            emb.set_author(
                name=f"Publicado por {getattr(autor, 'display_name', autor)}",
                icon_url=getattr(getattr(autor, "display_avatar", None), "url", None),
            )
        footer = f"{getattr(config, 'NOMBRE_HOSPITAL', 'Hospital')}  ·  Anuncios oficiales"
        if total > 1:
            footer += f"  ·  {i + 1}/{total}"
        emb.set_footer(text=footer)
        embeds.append(emb)
    return embeds


def _embeds_reglamento(
    titulo: str, cuerpo: str, autor: discord.abc.User
) -> List[discord.Embed]:
    embeds = _embeds_anuncio(
        titulo, cuerpo, autor, color=0x5865F2, subtitulo="Reglamento"
    )
    total = len(embeds)
    for i, emb in enumerate(embeds):
        if i == 0:
            emb.title = f"📜 {titulo}"
        else:
            emb.title = f"📜 {titulo} (parte {i + 1}/{total})"
        emb.color = 0x5865F2
    return embeds


async def _enviar_embeds(
    canal: discord.abc.Messageable, embeds: List[discord.Embed]
) -> None:
    for emb in embeds:
        await canal.send(embed=emb)


async def _publicar_en_canal(
    interaction: discord.Interaction,
    embeds: List[discord.Embed],
    prefer_keys: tuple = ("anuncios", "log_general", "bot_status"),
) -> discord.abc.Messageable:
    canal = None
    guild = interaction.guild
    if guild:
        for key in prefer_keys:
            cid = (getattr(config, "CANALES", None) or {}).get(key)
            if cid:
                c = guild.get_channel(cid)
                if c and isinstance(c, discord.TextChannel):
                    canal = c
                    break
    if canal is None:
        canal = interaction.channel
    await _enviar_embeds(canal, embeds)
    return canal


# ─── Varios reglamentos ───────────────────────────────────────────────────────


def _load_all() -> dict:
    """Estructura: {\"items\": {id: {id, titulo, texto, ...}}}"""
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_REGLAMENTO_PATH):
        return {"items": {}}
    try:
        with open(_REGLAMENTO_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {"items": {}}

    # Migrar formato antiguo (un solo reglamento)
    if isinstance(data, dict) and "items" not in data and data.get("titulo"):
        sid = _slug(str(data["titulo"]))
        data = {
            "items": {
                sid: {
                    "id": sid,
                    "titulo": data.get("titulo") or "Reglamento",
                    "texto": data.get("texto") or "",
                    "actualizado_por": data.get("actualizado_por"),
                    "actualizado_at": data.get("actualizado_at"),
                }
            }
        }
        _write_all(data)
        return data

    if not isinstance(data, dict):
        return {"items": {}}
    data.setdefault("items", {})
    if not isinstance(data["items"], dict):
        data["items"] = {}
    return data


def _write_all(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_REGLAMENTO_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _listar_items() -> List[dict]:
    items = _load_all().get("items") or {}
    out = list(items.values())
    out.sort(key=lambda x: (x.get("titulo") or "").lower())
    return out


def _obtener(rid: str) -> Optional[dict]:
    return (_load_all().get("items") or {}).get(rid)


def _guardar_item(titulo: str, texto: str, por: int, rid: Optional[str] = None) -> dict:
    data = _load_all()
    items = data.setdefault("items", {})
    sid = rid or _slug(titulo)
    # si ya existe otro con mismo slug, no pisar salvo mismo id
    base = sid
    n = 2
    while sid in items and (items[sid].get("titulo") or "").lower() != (titulo or "").lower():
        sid = f"{base}-{n}"
        n += 1
        if n > 50:
            break
    # actualizar si mismo título/slug
    for k, v in list(items.items()):
        if (v.get("titulo") or "").strip().lower() == (titulo or "").strip().lower():
            sid = k
            break
    reg = {
        "id": sid,
        "titulo": (titulo or "Reglamento").strip()[:120],
        "texto": texto or "",
        "actualizado_por": int(por),
        "actualizado_at": datetime.now(timezone.utc).isoformat(),
    }
    items[sid] = reg
    data["items"] = items
    _write_all(data)
    try:
        config.REGLAS_TEXTO = texto
    except Exception:
        pass
    return reg


def _eliminar_item(rid: str) -> bool:
    data = _load_all()
    items = data.get("items") or {}
    if rid not in items:
        return False
    del items[rid]
    data["items"] = items
    _write_all(data)
    return True


def _opciones_select() -> List[discord.SelectOption]:
    opts: List[discord.SelectOption] = []
    for it in _listar_items()[:25]:
        rid = str(it.get("id") or "")
        titulo = str(it.get("titulo") or rid)[:100]
        chars = len(it.get("texto") or "")
        opts.append(
            discord.SelectOption(
                label=titulo,
                value=rid,
                description=f"{chars} caracteres"[:100],
            )
        )
    return opts


class PublicarReglamentoView(ui.View):
    def __init__(self, author_id: int, canal: discord.TextChannel):
        super().__init__(timeout=180)
        self.author_id = author_id
        self.canal = canal
        opts = _opciones_select()
        if not opts:
            opts = [
                discord.SelectOption(
                    label="(Sin reglamentos)",
                    value="_none",
                    description="Usa /agregar_reglamento antes",
                )
            ]
        sel = ui.Select(
            placeholder="Elige el reglamento a publicar…",
            min_values=1,
            max_values=1,
            options=opts,
        )
        sel.callback = self._on_select
        self.add_item(sel)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ Solo quien ejecutó el comando.", ephemeral=True
            )
            return False
        return True

    async def _on_select(self, interaction: discord.Interaction):
        sel = interaction.data.get("values", ["_none"])[0] if interaction.data else "_none"
        if sel == "_none":
            return await interaction.response.send_message(
                "❌ No hay reglamentos guardados. Usa `/agregar_reglamento`.",
                ephemeral=True,
            )
        reg = _obtener(sel)
        if not reg:
            return await interaction.response.send_message(
                "❌ Ese reglamento ya no existe.", ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)
        embeds = _embeds_reglamento(
            reg.get("titulo") or "Reglamento",
            reg.get("texto") or "",
            interaction.user,
        )
        try:
            await _enviar_embeds(self.canal, embeds)
        except Exception as e:
            return await interaction.followup.send(
                f"❌ No se pudo publicar en {self.canal.mention}: `{e}`",
                ephemeral=True,
            )

        partes = len(embeds)
        extra = f" ({partes} mensajes)" if partes > 1 else ""
        await interaction.followup.send(
            f"✅ **{reg.get('titulo')}** publicado en {self.canal.mention}{extra}.",
            ephemeral=True,
        )
        try:
            for child in self.children:
                child.disabled = True
            await interaction.edit_original_response(view=self)
        except Exception:
            pass
        self.stop()


def registrar(bot: commands.Bot) -> None:
    for nombre in (
        "anuncio",
        "anuncio_direccion",
        "agregar_reglamento",
        "publicar_reglamento",
        "listar_reglamentos",
        "eliminar_reglamento",
    ):
        try:
            bot.tree.remove_command(nombre)
        except Exception:
            pass

    @bot.tree.command(
        name="anuncio",
        description="Publica un anuncio largo (sin límite de tamaño)",
    )
    @app_commands.describe(
        titulo="Título del anuncio",
        mensaje="Texto completo (puede ser muy largo)",
    )
    @require_key(
        "OWNER",
        "CO_OWNER",
        "FUNDADOR_OWNER",
        "DIRECTOR_GENERAL",
        "DIR_GENERAL",
        "CANCILLER",
        "ADMIN",
        "ADMIN_JEFE",
    )
    async def anuncio(
        interaction: discord.Interaction, titulo: str, mensaje: str
    ):
        await interaction.response.defer(ephemeral=True)
        try:
            embeds = _embeds_anuncio(titulo, mensaje, interaction.user)
            canal = await _publicar_en_canal(interaction, embeds)
            partes = len(embeds)
            where = canal.mention if hasattr(canal, "mention") else "este canal"
            extra = f" ({partes} mensajes)" if partes > 1 else ""
            await interaction.followup.send(
                f"✅ Anuncio publicado en {where}{extra}.",
                ephemeral=True,
            )
        except Exception as e:
            print(f"[anuncio] error: {e}")
            await interaction.followup.send(
                f"❌ No se pudo publicar el anuncio: `{e}`",
                ephemeral=True,
            )

    @bot.tree.command(
        name="anuncio_direccion",
        description="Anuncio de una dirección / área",
    )
    @app_commands.describe(
        direccion="Nombre del área (ej: Docencia)",
        titulo="Título",
        mensaje="Texto completo",
    )
    @require_key(
        "OWNER",
        "CO_OWNER",
        "FUNDADOR_OWNER",
        "DIRECTOR_GENERAL",
        "DIR_GENERAL",
        "CANCILLER",
        "DIR_DOCENCIA",
        "DIRECTOR_DOCENCIA",
        "DIR_RRHH",
        "DIRECTOR_RRHH",
        "ADMIN",
    )
    async def anuncio_direccion(
        interaction: discord.Interaction,
        direccion: str,
        titulo: str,
        mensaje: str,
    ):
        await interaction.response.defer(ephemeral=True)
        try:
            embeds = _embeds_anuncio(
                titulo,
                mensaje,
                interaction.user,
                color=0x1ABC9C,
                subtitulo=direccion,
            )
            canal = await _publicar_en_canal(interaction, embeds)
            partes = len(embeds)
            where = canal.mention if hasattr(canal, "mention") else "este canal"
            extra = f" ({partes} mensajes)" if partes > 1 else ""
            await interaction.followup.send(
                f"✅ Anuncio de **{direccion}** publicado en {where}{extra}.",
                ephemeral=True,
            )
        except Exception as e:
            print(f"[anuncio_direccion] error: {e}")
            await interaction.followup.send(
                f"❌ No se pudo publicar: `{e}`",
                ephemeral=True,
            )

    @bot.tree.command(
        name="agregar_reglamento",
        description="Guarda un reglamento (puedes tener varios). No publica solo.",
    )
    @app_commands.describe(
        titulo="Nombre del reglamento (ej: RP, Discord, General)",
        texto="Texto completo (sin límite práctico)",
    )
    @require_key(
        "OWNER",
        "CO_OWNER",
        "FUNDADOR_OWNER",
        "DIRECTOR_GENERAL",
        "DIR_GENERAL",
        "DIRECTOR_ADMINISTRATIVO",
        "CANCILLER",
    )
    async def agregar_reglamento(
        interaction: discord.Interaction,
        titulo: str,
        texto: str,
    ):
        await interaction.response.defer(ephemeral=True)
        try:
            reg = _guardar_item(titulo, texto, interaction.user.id)
            total = len(_listar_items())
            await interaction.followup.send(
                (
                    f"✅ Reglamento **{reg['titulo']}** guardado "
                    f"(`{reg['id']}`, {len(texto)} caracteres).\n"
                    f"Total guardados: **{total}**.\n"
                    f"Publícalo con `/publicar_reglamento` eligiendo canal y el menú."
                ),
                ephemeral=True,
            )
        except Exception as e:
            print(f"[agregar_reglamento] error: {e}")
            await interaction.followup.send(
                f"❌ Error al guardar: `{e}`",
                ephemeral=True,
            )

    @bot.tree.command(
        name="publicar_reglamento",
        description="Publica un reglamento guardado: elige canal y luego el menú",
    )
    @app_commands.describe(
        canal="Canal donde se publicará el reglamento",
    )
    @require_key(
        "OWNER",
        "CO_OWNER",
        "FUNDADOR_OWNER",
        "DIRECTOR_GENERAL",
        "DIR_GENERAL",
        "DIRECTOR_ADMINISTRATIVO",
        "CANCILLER",
        "ADMIN",
        "ADMIN_JEFE",
    )
    async def publicar_reglamento(
        interaction: discord.Interaction,
        canal: discord.TextChannel,
    ):
        items = _listar_items()
        if not items:
            return await interaction.response.send_message(
                "❌ No hay reglamentos guardados. Usa `/agregar_reglamento` primero.",
                ephemeral=True,
            )
        view = PublicarReglamentoView(interaction.user.id, canal)
        lista = "\n".join(
            f"• **{it.get('titulo')}** (`{it.get('id')}`) — {len(it.get('texto') or '')} car."
            for it in items[:15]
        )
        if len(items) > 15:
            lista += f"\n… y {len(items) - 15} más"
        emb = discord.Embed(
            title="📜 Publicar reglamento",
            description=(
                f"Canal destino: {canal.mention}\n\n"
                f"**Guardados:**\n{lista}\n\n"
                f"Elige en el menú cuál publicar."
            ),
            color=0x5865F2,
        )
        await interaction.response.send_message(
            embed=emb, view=view, ephemeral=True
        )

    @bot.tree.command(
        name="listar_reglamentos",
        description="Lista todos los reglamentos guardados",
    )
    @require_key(
        "OWNER",
        "CO_OWNER",
        "FUNDADOR_OWNER",
        "DIRECTOR_GENERAL",
        "DIR_GENERAL",
        "CANCILLER",
        "ADMIN",
    )
    async def listar_reglamentos(interaction: discord.Interaction):
        items = _listar_items()
        if not items:
            return await interaction.response.send_message(
                "No hay reglamentos guardados.", ephemeral=True
            )
        lines = []
        for it in items:
            lines.append(
                f"• **{it.get('titulo')}** — `{it.get('id')}` — "
                f"{len(it.get('texto') or '')} caracteres"
            )
        emb = discord.Embed(
            title=f"📜 Reglamentos ({len(items)})",
            description="\n".join(lines)[:4000],
            color=0x5865F2,
        )
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @bot.tree.command(
        name="eliminar_reglamento",
        description="Elimina un reglamento guardado por su id o título",
    )
    @app_commands.describe(identificador="Id o título exacto del reglamento")
    @require_key(
        "OWNER",
        "CO_OWNER",
        "FUNDADOR_OWNER",
        "DIRECTOR_GENERAL",
        "DIR_GENERAL",
    )
    async def eliminar_reglamento(
        interaction: discord.Interaction, identificador: str
    ):
        ident = (identificador or "").strip()
        rid = None
        for it in _listar_items():
            if it.get("id") == ident or (it.get("titulo") or "").lower() == ident.lower():
                rid = it.get("id")
                break
        if not rid:
            return await interaction.response.send_message(
                f"❌ No encontré `{ident}`. Usa `/listar_reglamentos`.",
                ephemeral=True,
            )
        _eliminar_item(rid)
        await interaction.response.send_message(
            f"🗑️ Reglamento `{rid}` eliminado.", ephemeral=True
        )

    print(
        "[anuncios_largos] OK — agregar/publicar/listar/eliminar reglamento (varios)"
    )
