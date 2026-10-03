# -*- coding: utf-8 -*-
"""
ticket_transcript.py — Transcripciones legibles del chat.
Solo conversación, embeds legibles y archivos; sin bloques de código ni metadatos técnicos.
"""
from __future__ import annotations

import html
import io
import re
from datetime import datetime, timezone
from typing import List, Optional, Sequence

import discord
import config

_CSS = """
:root {
  --bg: #0b0f19; --surface: #121826; --border: #2a3548;
  --text: #e8eef7; --muted: #8b9bb4; --accent: #5b8def;
  --staff: #3dd6c6; --bot: #f0b429; --user: #5b8def;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: "Segoe UI", system-ui, sans-serif;
  background: radial-gradient(ellipse at top, #152038 0%, var(--bg) 55%);
  color: var(--text); min-height: 100vh; line-height: 1.55;
}
.wrap { max-width: 860px; margin: 0 auto; padding: 32px 20px 64px; }
.hero {
  background: linear-gradient(135deg, #1e3a6e 0%, #2d1f5c 50%, #0f2847 100%);
  border: 1px solid rgba(255,255,255,.08); border-radius: 20px;
  padding: 28px 32px; box-shadow: 0 8px 32px rgba(0,0,0,.45); margin-bottom: 28px;
}
.hero-badge {
  display: inline-flex; background: rgba(255,255,255,.1);
  border-radius: 999px; padding: 4px 14px; font-size: 12px;
  letter-spacing: .06em; text-transform: uppercase; color: #c5d4f0; margin-bottom: 12px;
}
.hero h1 { font-size: 1.65rem; font-weight: 700; margin-bottom: 6px; }
.hero .sub { color: #a8b8d8; font-size: .95rem; }
.meta { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-top: 20px; }
.meta-card {
  background: rgba(0,0,0,.25); border: 1px solid rgba(255,255,255,.06);
  border-radius: 12px; padding: 12px 14px;
}
.meta-card .label { font-size: 11px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); }
.meta-card .value { font-size: .95rem; font-weight: 600; margin-top: 2px; word-break: break-word; }
.timeline {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 20px; padding: 8px 0; box-shadow: 0 8px 32px rgba(0,0,0,.45);
}
.msg { display: flex; gap: 14px; padding: 16px 22px; border-bottom: 1px solid rgba(255,255,255,.04); }
.msg:last-child { border-bottom: none; }
.avatar {
  width: 42px; height: 42px; border-radius: 50%; flex-shrink: 0;
  background: linear-gradient(135deg, var(--accent), #7c5cff);
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 15px; color: #fff; overflow: hidden;
}
.avatar img { width: 100%; height: 100%; object-fit: cover; }
.avatar.staff { background: linear-gradient(135deg, #2a9d8f, #3dd6c6); }
.avatar.bot { background: linear-gradient(135deg, #c9a227, #f0b429); }
.body { flex: 1; min-width: 0; }
.head { display: flex; flex-wrap: wrap; align-items: baseline; gap: 8px; margin-bottom: 4px; }
.name { font-weight: 700; font-size: .95rem; }
.tag {
  font-size: 11px; padding: 2px 8px; border-radius: 999px;
  background: rgba(91,141,239,.15); color: var(--user);
}
.tag.staff { background: rgba(61,214,198,.15); color: var(--staff); }
.tag.bot { background: rgba(240,180,41,.15); color: var(--bot); }
.time { margin-left: auto; font-size: 12px; color: var(--muted); }
.content { color: #d0dae8; font-size: .92rem; white-space: pre-wrap; word-break: break-word; }
.quote {
  margin-top: 8px; padding: 10px 12px; background: #1a2234;
  border-radius: 10px; border-left: 3px solid #5b8def; color: #c5d0e0; font-size: .9rem;
}
.attach { margin-top: 8px; display: flex; flex-direction: column; gap: 6px; }
.attach img { max-width: 100%; border-radius: 10px; margin-top: 4px; }
.attach a { color: var(--accent); text-decoration: none; }
.stats { display: flex; justify-content: center; gap: 24px; margin: 16px 0 8px; flex-wrap: wrap; }
.stat { text-align: center; }
.stat span { display: block; font-size: 1.4rem; font-weight: 700; color: var(--accent); }
.stat small { color: var(--muted); font-size: 12px; }
.footer { text-align: center; margin-top: 28px; color: var(--muted); font-size: 13px; }
"""


def _esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def _initials(name: str) -> str:
    parts = [p for p in re.split(r"\s+", (name or "?").strip()) if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def _fmt_dt(dt: Optional[datetime]) -> str:
    if not dt:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")


def _role_kind(author: discord.abc.User, guild: Optional[discord.Guild]) -> str:
    if getattr(author, "bot", False):
        return "bot"
    if guild and isinstance(author, discord.Member):
        if author.guild_permissions.manage_channels or author.guild_permissions.administrator:
            return "staff"
        try:
            import permisos

            if permisos.member_tiene_alguna_key(
                author,
                "FUNDADOR_OWNER",
                "CO_OWNER",
                "CANCILLER",
                "DIR_GENERAL",
                "DIR_DOCENCIA",
                "ADMIN",
            ):
                return "staff"
        except Exception:
            pass
    return "user"


def _texto_limpio(raw: str) -> str:
    """
    Convierte el mensaje en texto de conversación legible.
    Quita cercas de código, backticks y ruido técnico; deja el contenido hablado.
    """
    if not raw:
        return ""
    text = raw.replace("\r\n", "\n").replace("\r", "\n")

    # Bloques ```...``` → solo el interior, como párrafo normal
    def _bloque(m: re.Match) -> str:
        inner = m.group(2) or ""
        # quitar etiqueta de lenguaje (python, json, etc.)
        inner = re.sub(r"^\s*[a-zA-Z0-9_+-]+\s*\n", "", inner, count=1)
        return inner.strip()

    text = re.sub(r"```([a-zA-Z0-9_+-]*)\n?([\s\S]*?)```", _bloque, text)

    # Inline `code` → texto normal
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # Spoilers ||text|| → text
    text = re.sub(r"\|\|(.+?)\|\|", r"\1", text)

    # Enlaces markdown [label](url) → label (url)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)

    # Quitar basura típica de logs técnicos
    ruido = [
        r"custom_id[=:]\S+",
        r"interaction_id[=:]\S+",
        r"application_id[=:]\S+",
        r"\"type\"\s*:\s*\d+",
        r"\"components\"\s*:\s*\[[\s\S]*?\]",
    ]
    for pat in ruido:
        text = re.sub(pat, "", text, flags=re.IGNORECASE)

    # Colapsar líneas vacías excesivas
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _embed_legible(e: discord.Embed) -> str:
    partes: List[str] = []
    if e.author and e.author.name:
        partes.append(e.author.name)
    if e.title:
        partes.append(e.title)
    if e.description:
        partes.append(_texto_limpio(e.description))
    for f in e.fields[:15]:
        nombre = (f.name or "").strip()
        valor = _texto_limpio(f.value or "")
        if nombre or valor:
            partes.append(f"{nombre}: {valor}".strip(": "))
    if e.footer and e.footer.text:
        partes.append(_texto_limpio(e.footer.text))
    return "\n".join(p for p in partes if p).strip()


async def collect_messages(channel: discord.TextChannel, limit: int = 500) -> List[discord.Message]:
    msgs: List[discord.Message] = []
    async for m in channel.history(limit=limit, oldest_first=True):
        msgs.append(m)
    return msgs


def render_html(
    *,
    titulo: str,
    canal_nombre: str,
    abierto_por: str,
    cerrado_por: str,
    categoria: str,
    creado: Optional[datetime],
    cerrado: Optional[datetime],
    messages: Sequence[discord.Message],
    guild: Optional[discord.Guild] = None,
) -> str:
    hospital = getattr(config, "NOMBRE_HOSPITAL", None) or "Hospital"
    rows = []
    for m in messages:
        kind = _role_kind(m.author, guild or getattr(m, "guild", None))
        tag = {"staff": "Staff", "bot": "Bot", "user": "Usuario"}.get(kind, "Usuario")
        name = _esc(getattr(m.author, "display_name", None) or m.author.name)

        limpio = _texto_limpio(m.content or "")
        content_html = _esc(limpio).replace("\n", "<br/>") if limpio else ""

        # Embeds como texto de conversación (sin aspecto de código)
        for e in m.embeds:
            leg = _embed_legible(e)
            if leg:
                block = _esc(leg).replace("\n", "<br/>")
                content_html += f'<div class="quote">{block}</div>'

        # Stickers
        try:
            for st in m.stickers:
                content_html += f'<div class="quote">Sticker: {_esc(st.name)}</div>'
        except Exception:
            pass

        if not content_html:
            content_html = "<em style='color:#8b9bb4'>(sin texto)</em>"

        avatar_html = f'<div class="avatar {kind}">{_esc(_initials(getattr(m.author, "display_name", None) or m.author.name))}</div>'
        try:
            url = m.author.display_avatar.url
            avatar_html = f'<div class="avatar {kind}"><img src="{_esc(url)}" alt=""/></div>'
        except Exception:
            pass

        attaches = []
        for a in m.attachments:
            if a.content_type and a.content_type.startswith("image/"):
                attaches.append(f'<img src="{_esc(a.url)}" alt="{_esc(a.filename)}"/>')
            else:
                attaches.append(
                    f'<a href="{_esc(a.url)}" target="_blank" rel="noopener">📎 {_esc(a.filename)}</a>'
                )
        att_html = f'<div class="attach">{("".join(attaches))}</div>' if attaches else ""

        rows.append(
            f'<div class="msg">{avatar_html}<div class="body">'
            f'<div class="head"><span class="name">{name}</span>'
            f'<span class="tag {kind}">{tag}</span>'
            f'<span class="time">{_esc(_fmt_dt(m.created_at))}</span></div>'
            f'<div class="content">{content_html}</div>{att_html}</div></div>'
        )

    body_msgs = "\n".join(rows) if rows else '<div class="msg"><div class="body"><div class="content"><em>Sin mensajes.</em></div></div></div>'
    n_staff = sum(1 for m in messages if _role_kind(m.author, guild) == "staff")
    n_user = sum(1 for m in messages if _role_kind(m.author, guild) == "user")

    return f"""<!DOCTYPE html>
<html lang="es"><head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{_esc(titulo)} · Transcripción</title>
<style>{_CSS}</style></head><body>
<div class="wrap">
<header class="hero">
  <div class="hero-badge">🏥 {_esc(hospital)} · Transcripción</div>
  <h1>{_esc(titulo)}</h1>
  <p class="sub">Canal <strong>#{_esc(canal_nombre)}</strong> · {_esc(categoria)}</p>
  <div class="meta">
    <div class="meta-card"><div class="label">Abierto por</div><div class="value">{_esc(abierto_por)}</div></div>
    <div class="meta-card"><div class="label">Cerrado por</div><div class="value">{_esc(cerrado_por)}</div></div>
    <div class="meta-card"><div class="label">Creado</div><div class="value">{_esc(_fmt_dt(creado))}</div></div>
    <div class="meta-card"><div class="label">Cerrado</div><div class="value">{_esc(_fmt_dt(cerrado))}</div></div>
  </div>
</header>
<div class="stats">
  <div class="stat"><span>{len(messages)}</span><small>Mensajes</small></div>
  <div class="stat"><span>{n_user}</span><small>Usuario</small></div>
  <div class="stat"><span>{n_staff}</span><small>Staff</small></div>
</div>
<section class="timeline">{body_msgs}</section>
<footer class="footer">
  <p>Transcripción del chat · <strong>{_esc(hospital)}</strong></p>
  <p>{_esc(_fmt_dt(datetime.now(timezone.utc)))}</p>
</footer>
</div></body></html>"""


def render_texto_plano(
    *,
    titulo: str,
    canal_nombre: str,
    abierto_por: str,
    cerrado_por: str,
    messages: Sequence[discord.Message],
    guild: Optional[discord.Guild] = None,
) -> str:
    """Transcripción .txt solo conversación."""
    lineas = [
        f"Transcripción: {titulo}",
        f"Canal: #{canal_nombre}",
        f"Abierto por: {abierto_por}",
        f"Cerrado por: {cerrado_por}",
        "-" * 40,
        "",
    ]
    for m in messages:
        quien = getattr(m.author, "display_name", None) or m.author.name
        cuando = _fmt_dt(m.created_at)
        cuerpo = _texto_limpio(m.content or "")
        for e in m.embeds:
            leg = _embed_legible(e)
            if leg:
                cuerpo = (cuerpo + "\n" + leg).strip()
        for a in m.attachments:
            cuerpo = (cuerpo + f"\n[Archivo: {a.filename}]").strip()
        if not cuerpo:
            cuerpo = "(sin texto)"
        lineas.append(f"[{cuando}] {quien}:")
        lineas.append(cuerpo)
        lineas.append("")
    return "\n".join(lineas)


def html_to_file(html_str: str, filename: str = "transcripcion.html") -> discord.File:
    return discord.File(io.BytesIO(html_str.encode("utf-8")), filename=filename)


def texto_to_file(text: str, filename: str = "transcripcion.txt") -> discord.File:
    return discord.File(io.BytesIO(text.encode("utf-8")), filename=filename)


def embed_resumen(
    *,
    titulo: str,
    canal_nombre: str,
    abierto_por: str,
    cerrado_por: str,
    categoria: str,
    n_msgs: int,
    color: int = 0x5B8DEF,
) -> discord.Embed:
    emb = discord.Embed(
        title=f"📜 Transcripción · {titulo}",
        description=(
            f"Ticket **#{(canal_nombre or '—')[:80]}** archivado.\n"
            f"Adjunto: conversación del chat (sin bloques de código)."
        ),
        color=color,
        timestamp=datetime.now(timezone.utc),
    )
    emb.add_field(name="📂 Categoría", value=categoria or "—", inline=True)
    emb.add_field(name="💬 Mensajes", value=str(n_msgs), inline=True)
    emb.add_field(name="👤 Abierto por", value=abierto_por or "—", inline=True)
    emb.add_field(name="🔒 Cerrado por", value=cerrado_por or "—", inline=True)
    emb.set_footer(text=f"{getattr(config, 'NOMBRE_HOSPITAL', 'Hospital')} · Transcripción")
    return emb
