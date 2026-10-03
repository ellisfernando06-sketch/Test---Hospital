# -*- coding: utf-8 -*-
"""
cert_postulacion.py
Flujo:
  1) /postular_certificacion → elige cert
  2) Bot envía material por MD (docx si existe + resumen)
  3) Botón Evaluarme → cuestionario en MD
  4) Resultados al canal de Docencia (canales_direccion)
  5) Staff Aprobar/Reprobar → rol CERTIFICADOS
"""
from __future__ import annotations

import io
import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import discord
from discord import app_commands, ui
from discord.ext import commands

# estado en memoria (por sesión de evaluación)
_EVALS: Dict[str, Dict[str, Any]] = {}

_ROOT = Path(__file__).resolve().parent
_MATERIAL_DIRS = [
    _ROOT / "materiales_certificacion",
    _ROOT / "assets" / "materiales_certificacion",
    Path(os.environ.get("CERT_MATERIALES_DIR", "")) if os.environ.get("CERT_MATERIALES_DIR") else None,
]


def _load_examenes() -> Dict[str, Any]:
    for p in (
        _ROOT / "cert_examenes.json",
        _ROOT / "data" / "cert_examenes.json",
        Path("/home/workdir/artifacts/cert_examenes.json"),
    ):
        try:
            if p and p.is_file():
                return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    # fallback mínimo embebido
    try:
        import roles_config

        out = {}
        for clave, (nombre, _) in (getattr(roles_config, "CERTIFICADOS", {}) or {}).items():
            out[clave] = {
                "nombre": nombre.replace("🎓 Cert. ", ""),
                "archivo": f"{clave}.docx",
                "resumen_estudio": [
                    "Material de roleplay del Hospital General.",
                    "No acredita competencias médicas reales.",
                    "Respeta protocolo interno y cadena de mando.",
                ],
                "preguntas": [
                    {
                        "q": f"¿El certificado de {nombre} acredita medicina real?",
                        "opciones": [
                            "Sí",
                            "No, es solo roleplay/simulación",
                            "Solo fuera del servidor",
                            "Depende del país",
                        ],
                        "correcta": 1,
                        "puntos": 2,
                    },
                    {
                        "q": "Si dudas de tu límite de rol, ¿qué haces?",
                        "opciones": [
                            "Improvisar otro rango",
                            "Pedir apoyo y seguir la cadena de mando",
                            "Ignorar el reglamento",
                            "Inventar un protocolo",
                        ],
                        "correcta": 1,
                        "puntos": 2,
                    },
                    {
                        "q": "¿Qué prioridad aplica en escena?",
                        "opciones": [
                            "Powergaming",
                            "Protocolo, seguridad simulada y equipo",
                            "Ganar OOC",
                            "Ocultar errores",
                        ],
                        "correcta": 1,
                        "puntos": 2,
                    },
                ],
                "min_puntos": 4,
                "max_puntos": 6,
            }
        return out
    except Exception:
        return {}


def _material_path(clave: str) -> Optional[Path]:
    fname = f"{clave}.docx"
    for d in _MATERIAL_DIRS:
        if not d:
            continue
        p = Path(d) / fname
        if p.is_file():
            return p
    # también buscar por nombre de archivo declarado
    data = _load_examenes().get(clave) or {}
    alt = data.get("archivo")
    if alt:
        for d in _MATERIAL_DIRS:
            if not d:
                continue
            p = Path(d) / alt
            if p.is_file():
                return p
    return None


def _choices_cert() -> List[app_commands.Choice[str]]:
    data = _load_examenes()
    out: List[app_commands.Choice[str]] = []
    for clave, meta in data.items():
        nombre = meta.get("nombre") or clave
        label = f"🎓 {nombre}"
        if len(label) > 100:
            label = label[:97] + "…"
        out.append(app_commands.Choice(name=label, value=clave))
        if len(out) >= 25:
            break
    return out


async def _canal_docencia(guild: discord.Guild) -> Optional[discord.TextChannel]:
    try:
        import canales_direccion

        cid = canales_direccion.obtener_canal_id("docencia")
        if not cid:
            # alias posibles
            for a in ("docencia", "DIR_DOCENCIA", "direccion_docencia"):
                cid = canales_direccion.obtener_canal_id(a)
                if cid:
                    break
        if cid:
            ch = guild.get_channel(int(cid))
            if isinstance(ch, discord.TextChannel):
                return ch
    except Exception:
        pass
    # fallback por nombre
    for ch in guild.text_channels:
        n = (ch.name or "").lower()
        if "docencia" in n and ("log" in n or "solicitud" in n or "cert" in n or "eval" in n):
            return ch
    for ch in guild.text_channels:
        if "docencia" in (ch.name or "").lower():
            return ch
    return None


def _puede_staff_docencia(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    try:
        import permisos

        return permisos.member_tiene_alguna_key(
            member,
            "DIR_DOCENCIA",
            "DIRECTOR_DOCENCIA",
            "FUNDADOR_OWNER",
            "CO_OWNER",
            "OWNER",
            "CANCILLER",
            "DIR_GENERAL",
        )
    except Exception:
        return False


class EvaluarView(ui.View):
    def __init__(self, user_id: int, clave: str, guild_id: int):
        super().__init__(timeout=86400)
        self.user_id = user_id
        self.clave = clave
        self.guild_id = guild_id

    @ui.button(label="Evaluarme", style=discord.ButtonStyle.success, emoji="📝")
    async def evaluar(self, inter: discord.Interaction, button: ui.Button):
        if inter.user.id != self.user_id:
            return await inter.response.send_message(
                "❌ Solo quien se postuló puede evaluarse.", ephemeral=True
            )
        data = _load_examenes().get(self.clave)
        if not data or not data.get("preguntas"):
            return await inter.response.send_message(
                "❌ No hay examen cargado para esta certificación.", ephemeral=True
            )

        eid = uuid.uuid4().hex[:12]
        _EVALS[eid] = {
            "user_id": self.user_id,
            "clave": self.clave,
            "guild_id": self.guild_id,
            "idx": 0,
            "pts": 0,
            "max": int(data.get("max_puntos") or sum(p.get("puntos", 1) for p in data["preguntas"])),
            "min": int(data.get("min_puntos") or 0),
            "respuestas": [],
            "nombre": data.get("nombre", self.clave),
        }
        await inter.response.send_message(
            f"📝 Evaluación de **{data.get('nombre')}** iniciada.\n"
            f"Responde cada pregunta. Al terminar se enviará el resultado a **Docencia**.",
            ephemeral=True,
        )
        await _enviar_pregunta(inter.user, eid)


async def _enviar_pregunta(user: discord.abc.User, eid: str) -> None:
    st = _EVALS.get(eid)
    if not st:
        return
    data = _load_examenes().get(st["clave"]) or {}
    preguntas = data.get("preguntas") or []
    idx = st["idx"]
    if idx >= len(preguntas):
        await _finalizar_eval(user, eid)
        return
    p = preguntas[idx]
    view = RespuestaView(eid, len(p.get("opciones") or []))
    emb = discord.Embed(
        title=f"Pregunta {idx + 1}/{len(preguntas)} · {st['nombre']}",
        description=p.get("q", "—"),
        color=0x9B59B6,
    )
    for i, op in enumerate(p.get("opciones") or []):
        emb.add_field(name=f"{chr(65 + i)}", value=op, inline=False)
    emb.set_footer(text="Hospital General · Evaluación de certificación RP")
    try:
        await user.send(embed=emb, view=view)
    except discord.Forbidden:
        pass


class RespuestaView(ui.View):
    def __init__(self, eid: str, n_opts: int):
        super().__init__(timeout=600)
        self.eid = eid
        for i in range(min(n_opts, 4)):
            self.add_item(_RespButton(eid, i, chr(65 + i)))


class _RespButton(ui.Button):
    def __init__(self, eid: str, idx: int, label: str):
        super().__init__(label=label, style=discord.ButtonStyle.primary, custom_id=f"cert_r_{eid}_{idx}")
        self.eid = eid
        self.idx = idx

    async def callback(self, inter: discord.Interaction):
        st = _EVALS.get(self.eid)
        if not st or inter.user.id != st["user_id"]:
            return await inter.response.send_message("❌ Sesión inválida.", ephemeral=True)
        data = _load_examenes().get(st["clave"]) or {}
        preguntas = data.get("preguntas") or []
        p = preguntas[st["idx"]]
        correcta = int(p.get("correcta", 0))
        pts = int(p.get("puntos", 1)) if self.idx == correcta else 0
        st["pts"] += pts
        st["respuestas"].append(
            {
                "q": p.get("q"),
                "elegida": self.idx,
                "correcta": correcta,
                "pts": pts,
                "opciones": p.get("opciones"),
            }
        )
        st["idx"] += 1
        await inter.response.send_message(
            f"{'✅' if pts else '❌'} Respuesta registrada (+{pts} pts).",
            ephemeral=True,
        )
        # deshabilitar vista
        for c in self.view.children:
            c.disabled = True
        try:
            await inter.message.edit(view=self.view)
        except Exception:
            pass
        await _enviar_pregunta(inter.user, self.eid)


async def _finalizar_eval(user: discord.abc.User, eid: str) -> None:
    st = _EVALS.pop(eid, None)
    if not st:
        return
    pts, mx, mn = st["pts"], st["max"], st["min"]
    auto_ok = pts >= mn if mn else pts >= max(1, mx // 2)
    emb_user = discord.Embed(
        title="📋 Evaluación enviada a Docencia",
        description=(
            f"**Certificación:** {st['nombre']}\n"
            f"**Puntaje:** {pts}/{mx}\n"
            f"**Mínimo orientativo:** {mn}\n\n"
            f"El **Director de Docencia** revisará tus respuestas en el canal de logs.\n"
            f"Recibirás el resultado cuando aprueben o reprendan la solicitud."
        ),
        color=0x3498DB,
    )
    try:
        await user.send(embed=emb_user)
    except Exception:
        pass

    # Localizar guild
    bot = getattr(user, "_state", None)
    # se envía desde registrar con bot reference vía global
    bot_ref = _BOT_REF
    if not bot_ref:
        return
    guild = bot_ref.get_guild(int(st["guild_id"]))
    if not guild:
        return
    ch = await _canal_docencia(guild)
    member = guild.get_member(int(st["user_id"]))

    detalle = []
    for i, r in enumerate(st["respuestas"], 1):
        ops = r.get("opciones") or []
        eleg = ops[r["elegida"]] if 0 <= r["elegida"] < len(ops) else "?"
        corr = ops[r["correcta"]] if 0 <= r["correcta"] < len(ops) else "?"
        marca = "✅" if r["pts"] else "❌"
        detalle.append(f"{marca} **P{i}:** {r.get('q', '')[:120]}\n→ {eleg} _(correcta: {corr})_ +{r['pts']}")

    emb = discord.Embed(
        title="📝 Evaluación de certificación",
        description=(
            f"**Postulante:** {member.mention if member else st['user_id']}\n"
            f"**Certificación:** {st['nombre']} (`{st['clave']}`)\n"
            f"**Puntaje:** **{pts}/{mx}** (mín. orientativo {mn})\n"
            f"**Auto-sugerencia:** {'Aprobar' if auto_ok else 'Revisar / no aprobar'}"
        ),
        color=0x2ECC71 if auto_ok else 0xE67E22,
        timestamp=discord.utils.utcnow(),
    )
    # Discord field limits
    chunk = ""
    for line in detalle:
        if len(chunk) + len(line) > 1000:
            emb.add_field(name="Respuestas", value=chunk, inline=False)
            chunk = line + "\n"
        else:
            chunk += line + "\n"
    if chunk:
        emb.add_field(name="Respuestas", value=chunk[:1020], inline=False)
    emb.set_footer(text="Hospital General · Docencia")

    view = AprobarView(st["user_id"], st["clave"], st["nombre"], pts, mx)
    if ch:
        try:
            await ch.send(embed=emb, view=view)
        except Exception as e:
            print("[cert_postulacion] canal docencia:", e)
    else:
        print("[cert_postulacion] sin canal docencia configurado")
        # DM a staff con key docencia
        try:
            import canales_direccion

            for m in canales_direccion.miembros_con_keys(
                guild, ["DIR_DOCENCIA", "DIRECTOR_DOCENCIA", "FUNDADOR_OWNER"]
            ):
                try:
                    await m.send(
                        content="⚠️ No hay canal de Docencia configurado. Usa `/configurar_canal_direccion`.",
                        embed=emb,
                        view=view,
                    )
                except Exception:
                    pass
        except Exception:
            pass


class AprobarView(ui.View):
    def __init__(self, user_id: int, clave: str, nombre: str, pts: int, mx: int):
        super().__init__(timeout=86400 * 7)
        self.user_id = user_id
        self.clave = clave
        self.nombre = nombre
        self.pts = pts
        self.mx = mx

    @ui.button(label="Aprobar y otorgar rol", style=discord.ButtonStyle.success)
    async def aprobar(self, inter: discord.Interaction, button: ui.Button):
        if not isinstance(inter.user, discord.Member) or not _puede_staff_docencia(inter.user):
            return await inter.response.send_message("❌ Solo Docencia / dirección.", ephemeral=True)
        if not inter.guild:
            return
        member = inter.guild.get_member(self.user_id)
        if not member:
            return await inter.response.send_message("❌ Miembro no encontrado.", ephemeral=True)

        msg_rol = "—"
        try:
            import cert_roles

            ok, msg_rol = await cert_roles.otorgar_rol_certificado(
                member, self.clave, reason=f"Aprobado por {inter.user} ({self.pts}/{self.mx})"
            )
        except Exception as e:
            msg_rol = f"Error rol: {e}"

        try:
            import capacitaciones

            capacitaciones.certificar(member.id, self.nombre, inter.user.id)
        except Exception:
            pass

        await inter.response.send_message(
            f"✅ Aprobado {member.mention} · {msg_rol}", ephemeral=True
        )
        try:
            await member.send(
                embed=discord.Embed(
                    title="🎓 Certificación aprobada",
                    description=(
                        f"**{self.nombre}**\n"
                        f"Puntaje: {self.pts}/{self.mx}\n"
                        f"Revisado por: {inter.user.display_name}\n"
                        f"{msg_rol}"
                    ),
                    color=0x2ECC71,
                )
            )
        except Exception:
            pass
        for c in self.children:
            c.disabled = True
        try:
            await inter.message.edit(
                content=f"✅ **Aprobado** por {inter.user.mention}", view=self
            )
        except Exception:
            pass

    @ui.button(label="Reprobar", style=discord.ButtonStyle.danger)
    async def reprobar(self, inter: discord.Interaction, button: ui.Button):
        if not isinstance(inter.user, discord.Member) or not _puede_staff_docencia(inter.user):
            return await inter.response.send_message("❌ Solo Docencia / dirección.", ephemeral=True)
        await inter.response.send_modal(ReprobarModal(self))


class ReprobarModal(ui.Modal, title="Motivo de reprobación"):
    motivo = ui.TextInput(
        label="Motivo",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500,
    )

    def __init__(self, parent: AprobarView):
        super().__init__()
        self.parent = parent

    async def on_submit(self, inter: discord.Interaction):
        member = inter.guild.get_member(self.parent.user_id) if inter.guild else None
        await inter.response.send_message("✅ Reprobación registrada.", ephemeral=True)
        if member:
            try:
                await member.send(
                    embed=discord.Embed(
                        title="📋 Certificación no aprobada",
                        description=(
                            f"**{self.parent.nombre}**\n"
                            f"Puntaje: {self.parent.pts}/{self.parent.mx}\n"
                            f"**Motivo:** {self.motivo}\n\n"
                            f"Repasa el material y vuelve a postularte cuando estés listo."
                        ),
                        color=0xE74C3C,
                    )
                )
            except Exception:
                pass
        for c in self.parent.children:
            c.disabled = True
        try:
            await inter.message.edit(
                content=f"❌ **Reprobado** por {inter.user.mention}: {self.motivo}",
                view=self.parent,
            )
        except Exception:
            pass


_BOT_REF: Optional[commands.Bot] = None


async def _enviar_material_dm(
    member: discord.Member, clave: str, meta: Dict[str, Any]
) -> str:
    nombre = meta.get("nombre", clave)
    resumen = meta.get("resumen_estudio") or []
    emb = discord.Embed(
        title=f"📚 Material · {nombre}",
        description=(
            f"Has postulado a la certificación **{nombre}**.\n\n"
            f"1. Estudia el material adjunto (o el resumen).\n"
            f"2. Cuando termines, pulsa **Evaluarme**.\n"
            f"3. Tus respuestas irán al canal de **Docencia** para revisión.\n\n"
            f"_Material de roleplay · Hospital General · No acredita competencias reales._"
        ),
        color=0x9B59B6,
    )
    if resumen:
        emb.add_field(
            name="Puntos clave",
            value="\n".join(f"• {x[:180]}" for x in resumen[:6])[:1020],
            inline=False,
        )
    emb.set_footer(text="Hospital General · Docencia")

    path = _material_path(clave)
    files = []
    nota = ""
    if path and path.is_file():
        try:
            data = path.read_bytes()
            if len(data) <= 24 * 1024 * 1024:
                files.append(discord.File(io.BytesIO(data), filename=path.name))
                nota = f"Documento: `{path.name}`"
            else:
                nota = "Documento demasiado grande para Discord; usa el resumen."
        except Exception as e:
            nota = f"No se pudo adjuntar el archivo: {e}"
    else:
        nota = (
            "_(Aún no hay .docx en `materiales_certificacion/` en el host. "
            "Se envió el resumen de estudio. Sube los archivos al servidor del bot.)_"
        )

    view = EvaluarView(member.id, clave, member.guild.id)
    try:
        if files:
            await member.send(content=nota, embed=emb, file=files[0], view=view)
        else:
            await member.send(content=nota, embed=emb, view=view)
        return "ok"
    except discord.Forbidden:
        return "dm_cerrado"
    except Exception as e:
        return f"error:{e}"


def registrar(bot: commands.Bot) -> None:
    global _BOT_REF
    _BOT_REF = bot

    for name in ("postular_certificacion",):
        try:
            bot.tree.remove_command(name)
        except Exception:
            pass

    choices = _choices_cert()
    if not choices:
        print("[cert_postulacion] sin exámenes cargados")
        return

    @bot.tree.command(
        name="postular_certificacion",
        description="Postúlate a una certificación: recibes el material por MD y luego Evaluarme",
    )
    @app_commands.describe(certificacion="Certificación del organigrama")
    @app_commands.choices(certificacion=choices)
    async def postular_cmd(
        inter: discord.Interaction, certificacion: app_commands.Choice[str]
    ):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        clave = certificacion.value
        meta = _load_examenes().get(clave)
        if not meta:
            return await inter.response.send_message(
                "❌ Certificación no encontrada.", ephemeral=True
            )

        await inter.response.defer(ephemeral=True)
        result = await _enviar_material_dm(inter.user, clave, meta)
        if result == "dm_cerrado":
            return await inter.followup.send(
                "❌ No puedo enviarte MD. Abre mensajes directos del servidor e inténtalo de nuevo.",
                ephemeral=True,
            )
        if result.startswith("error:"):
            return await inter.followup.send(f"❌ {result}", ephemeral=True)

        ch = await _canal_docencia(inter.guild)
        extra = (
            f"Canal Docencia: {ch.mention}"
            if ch
            else "⚠️ Configura el canal con `/configurar_canal_direccion` (área Docencia)."
        )
        await inter.followup.send(
            embed=discord.Embed(
                title="✅ Postulación registrada",
                description=(
                    f"**Certificación:** {meta.get('nombre')}\n"
                    f"Revisa tu **MD**: material + botón **Evaluarme**.\n\n{extra}"
                ),
                color=0x2ECC71,
            ),
            ephemeral=True,
        )

    print(f"[cert_postulacion] OK — {len(choices)} certificaciones · /postular_certificacion")
