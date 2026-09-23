# -*- coding: utf-8 -*
"""ticket_transcript.py — Transcripciones visuales premium de tickets."""
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
  --bg: #0b0f19; --surface: #121826; --surface2: #1a2234; --border: #2a3548;
  --text: #e8eef7; --muted: #8b9bb4; --accent: #5b8def; --accent2: #7c5cff;
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
  display: inline-flex; gap: 8px; background: rgba(255,255,255,.1);
  border: 1px solid rgba(255,255,255,.15); border-radius: 999px;
  padding: 4px 14px; font-size: 12px; letter-spacing: .06em;
  text-transform: uppercase; color: #c5d4f0; margin-bottom: 12px;
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
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 15px; color: #fff; overflow: hidden;
}
.avatar img { width: 100%; height: 100%; object-fit: cover; }
.avatar.staff { background: linear-gradient(135deg, #2a9d8f, #3dd6c6); }
.avatar.bot { background: linear-gradient(135deg, #e9a825, #f0b429); }
.body { flex: 1; min-width: 0; }
.head { display: flex; flex-wrap: wrap; align-items: baseline; gap: 8px; margin-bottom: 4px; }
.name { font-weight: 650; font-size: .95rem; }
.tag { font-size: 10px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; padding: 2px 8px; border-radius: 6px; }
.tag.staff { background: rgba(61,214,198,.15); color: var(--staff); }
.tag.bot { background: rgba(240,180,41,.15); color: var(--bot); }
.tag.user { background: rgba(91,141,239,.15); color: var(--user); }
.time { color: var(--muted); font-size: 12px; margin-left: auto; }
.content { color: #d0dae8; font-size: .92rem; white-space: pre-wrap; word-break: break-word; }
.attach { margin-top: 10px; display: flex; flex-wrap: wrap; gap: 8px; }
.attach a {
  display: inline-flex; gap: 6px; background: var(--surface2); border: 1px solid var(--border);
  border-radius: 10px; padding: 6px 12px; color: var(--accent); text-decoration: none; font-size: 12px;
}
.attach img { max-width: 280px; max-height: 180px; border-radius: 10px; border: 1px solid var(--border); margin-top: 8px; }
.footer { text-align: center; margin-top: 28px; color: var(--muted); font-size: 12px; }
.footer strong { color: #a8b8d8; }
.stats { display: flex; justify-content: center; gap: 24px; margin: 16px 0 8px; flex-wrap: wrap; }
.stat span { display: block; font-size: 1.25rem; font-weight: 700; color: var(--text); }
.stat small { color: var(--muted); text-transform: uppercase; letter-spacing: .06em; font-size: 10px; }
.empty { text-align: center; padding: 48px 20px; color: var(--muted); }
"""


def _esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def _initials(name: str) -> str:
    parts = re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ0-9]+", name or "?")
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()


def _fmt_dt(dt: Optional[datetime]) -> str:
    if not dt:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%d/%m/%Y · %H:%M UTC")


def _role_kind(author: discord.abc.User, guild: Optional[discord.Guild]) -> str:
    if getattr(author, "bot", False):
        return "bot"
    if guild and isinstance(author, discord.Member):
        try:
            import permisos
            if permisos.member_tiene_alguna_key(
                author, "OWNER", "CO_OWNER", "DIRECTOR", "SUPERVISOR",
                "STAFF_SERVIDOR", "STAFF", "JEFE_DEPARTAMENTO",
            ):
                return "staff"
        except Exception:
            pass
        if author.guild_permissions.manage_channels or author.guild_permissions.administrator:
            return "staff"
    return "user"


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
        content = _esc(m.content) if m.content else "<em style='color:#8b9bb4'>(sin texto)</em>"
        avatar_html = f'<div class="avatar {kind}">{_esc(_initials(name))}</div>'
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
                attaches.append(f'<a href="{_esc(a.url)}" target="_blank" rel="noopener">📎 {_esc(a.filename)}</a>')
        emb_bits = []
        for e in m.embeds:
            if e.title:
                emb_bits.append(f"<strong>{_esc(e.title)}</strong>")
            if e.description:
                emb_bits.append(_esc(e.description[:800]))
        if emb_bits:
            content += (
                "<div style='margin-top:8px;padding:10px 12px;background:#1a2234;"
                "border-radius:10px;border-left:3px solid #5b8def'>"
                + "<br/>".join(emb_bits) + "</div>"
            )
        att_html = f'<div class="attach">{("".join(attaches))}</div>' if attaches else ""
        rows.append(
            f'<div class="msg">{avatar_html}<div class="body">'
            f'<div class="head"><span class="name">{name}</span>'
            f'<span class="tag {kind}">{tag}</span>'
            f'<span class="time">{_esc(_fmt_dt(m.created_at))}</span></div>'
            f'<div class="content">{content}</div>{att_html}</div></div>'
        )
    body_msgs = "\n".join(rows) if rows else '<div class="empty">No hay mensajes en este ticket.</div>'
    n_staff = sum(1 for m in messages if _role_kind(m.author, guild) == "staff")
    n_user = sum(1 for m in messages if _role_kind(m.author, guild) == "user")
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{_esc(titulo)} · Transcripción</title>
<style>{_CSS}</style></head><body>
<div class="wrap">
<header class="hero">
  <div class="hero-badge">🏥 {_esc(hospital)} · Transcripción oficial</div>
  <h1>{_esc(titulo)}</h1>
  <p class="sub">Canal <strong>#{_esc(canal_nombre)}</strong> · Categoría <strong>{_esc(categoria)}</strong></p>
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
  <p>Generado por el bot de <strong>{_esc(hospital)}</strong></p>
  <p>{_esc(_fmt_dt(datetime.now(timezone.utc)))}</p>
</footer>
</div></body></html>"""


def html_to_file(html_str: str, filename: str = "transcripcion.html") -> discord.File:
    return discord.File(io.BytesIO(html_str.encode("utf-8")), filename=filename)


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
            f"La transcripción completa está en el archivo **HTML** adjunto."
        ),
        color=color,
        timestamp=datetime.now(timezone.utc),
    )
    emb.add_field(name="📂 Categoría", value=categoria or "—", inline=True)
    emb.add_field(name="💬 Mensajes", value=str(n_msgs), inline=True)
    emb.add_field(name="👤 Abierto por", value=abierto_por or "—", inline=True)
    emb.add_field(name="🔒 Cerrado por", value=cerrado_por or "—", inline=True)
    emb.set_footer(text=f"{getattr(config, 'NOMBRE_HOSPITAL', 'Hospital')} · Archivo oficial")
    return emb
