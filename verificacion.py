# -*- coding: utf-8 -*-
"""
verificacion.py — Whitelist Roblox + examen RP.

Flujo:
1. Staff: /verificar_roblox @user canal_log=...
2. Usuario: ingresa username Roblox (se valida en API)
3. Usuario: responde 15 preguntas (una a una, puntos 2 / 1 / 0)
4. Resultado + respuestas → canal de log con botones Aprobar / Negar
5. Staff aprueba o niega → roles/apodo o rechazo + guardado
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import discord
from discord import app_commands, ui
from discord.ext import commands

import config
from estilos import crear_embed

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "verificaciones.json")

# 15 preguntas · cada opción: (texto, puntos 2|1|0)
# Máx 30 pts · mínimo para recomendación automática: 20
PREGUNTAS: List[Dict[str, Any]] = [
    {
        "q": "En un canal de roleplay médico, ¿qué significa OOC?",
        "opts": [
            ("Fuera de personaje (Out Of Character)", 2),
            ("Orden oficial del hospital", 1),
            ("Operación de quirófano crítica", 0),
        ],
    },
    {
        "q": "¿Qué es metagaming?",
        "opts": [
            ("Usar info de Discord/OOC dentro del RP como si el PJ la supiera", 2),
            ("Hablar solo de temas médicos", 0),
            ("Pedir ayuda al staff por ticket", 1),
        ],
    },
    {
        "q": "¿Qué es powergaming?",
        "opts": [
            ("Forzar acciones/resultados sin dar chance al otro a reaccionar", 2),
            ("Interpretar a un jefe de servicio", 1),
            ("Usar emotes en el chat", 0),
        ],
    },
    {
        "q": "Llegas a urgencias con un paciente grave. ¿Qué haces primero en RP?",
        "opts": [
            ("Valorar ABC / estado y pedir ayuda según protocolo", 2),
            ("Operar de inmediato sin evaluar", 0),
            ("Esperar en silencio sin interactuar", 1),
        ],
    },
    {
        "q": "Un compañero rompe una regla de RP. ¿Qué es más correcto?",
        "opts": [
            ("Avisar por ticket/staff o canal adecuado, sin pelear en RP", 2),
            ("Insultarlo en el chat público", 0),
            ("Ignorarlo siempre, aunque sea grave", 1),
        ],
    },
    {
        "q": "¿Para qué sirve el consentimiento en escenas intensas (código/trauma)?",
        "opts": [
            ("Respetar límites y calidad de la escena entre jugadores", 2),
            ("Evitar usar el bot del hospital", 0),
            ("Solo firmar el reglamento una vez", 1),
        ],
    },
    {
        "q": "En RP hospitalario, un interno/residente normalmente…",
        "opts": [
            ("Actúa con supervisión y no asume jefatura sin rol", 2),
            ("Manda a todos los especialistas", 0),
            ("Solo puede escribir en OOC", 1),
        ],
    },
    {
        "q": "¿Qué evitas al hablar de temas sensibles (muerte, abuso, etc.)?",
        "opts": [
            ("Forzar escenas sin aviso ni respeto a límites del servidor", 2),
            ("Usar el canal de normativas", 0),
            ("Pedir rol de staff", 1),
        ],
    },
    {
        "q": "Un paciente en RP se niega a un procedimiento. ¿Qué haces?",
        "opts": [
            ("Explicas riesgos, respetas negativa salvo protocolo legal/RP del server", 2),
            ("Lo obligas sí o sí", 0),
            ("Abandonas el servidor", 1),
        ],
    },
    {
        "q": "¿Qué NO corresponde en un canal solo de RP?",
        "opts": [
            ("Discusiones largas OOC o spoilers de tramas ajenas", 2),
            ("Describir acciones del personaje", 0),
            ("Usar vocabulario médico básico", 1),
        ],
    },
    {
        "q": "Bioseguridad básica en RP implica…",
        "opts": [
            ("Guantes/mascarilla cuando el protocolo de la escena lo pide", 2),
            ("Ignorar sangre y fluidos siempre", 0),
            ("Solo decorar el lobby", 1),
        ],
    },
    {
        "q": "Si no sabes una técnica médica en RP…",
        "opts": [
            ("Consultas guía/staff o actúas con prudencia según tu rango", 2),
            ("Inventas un milagro sin base", 0),
            ("Cierras el ticket del paciente", 1),
        ],
    },
    {
        "q": "El RDM / muerte injustificada en servidores de RP…",
        "opts": [
            ("Está prohibido: no matas sin rol ni motivo válido", 2),
            ("Es obligatorio en urgencias", 0),
            ("Solo lo decide el paciente", 1),
        ],
    },
    {
        "q": "¿Qué haces con información leída en #staff siendo civil en RP?",
        "opts": [
            ("No la usas en personaje (evitar metagaming)", 2),
            ("La sueltas en el lobby para flexear", 0),
            ("La guardas para venderla en RP", 1),
        ],
    },
    {
        "q": "Al fallar una escena o romper una norma leve…",
        "opts": [
            ("Aceptas corrección, aprendes y sigues la normativa", 2),
            ("Insultas al staff", 0),
            ("Creas otra cuenta para evadir", 0),
        ],
    },
]

PUNTOS_MAX = 30  # 15 * 2
PUNTOS_MIN_RECOMENDADO = 20  # ~67%


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> dict:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_PATH):
        return {"pendientes": {}, "verificados": {}, "rechazados": {}, "examenes": {}}
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in ("pendientes", "verificados", "rechazados", "examenes"):
            data.setdefault(k, {})
        return data
    except Exception:
        return {"pendientes": {}, "verificados": {}, "rechazados": {}, "examenes": {}}


def _save(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def encontrar_rol(guild: discord.Guild, nombres: List[str]) -> Optional[discord.Role]:
    lower = {n.lower() for n in nombres}
    for rol in guild.roles:
        if (rol.name or "").lower() in lower or rol.name in nombres:
            return rol
    for rol in guild.roles:
        rn = (rol.name or "").lower()
        for n in nombres:
            if n.lower() in rn:
                return rol
    return None


def rol_visitante(guild: discord.Guild) -> Optional[discord.Role]:
    try:
        import roles_acceso

        r = roles_acceso.rol_visitante(guild)
        if r:
            return r
    except Exception:
        pass
    return encontrar_rol(guild, ["Visitante", "👤 Visitante", "visitante"])


def rol_miembro(guild: discord.Guild) -> Optional[discord.Role]:
    try:
        import roles_acceso

        r = roles_acceso.rol_miembro(guild)
        if r:
            return r
    except Exception:
        pass
    return encontrar_rol(guild, ["Miembro", "👤 Miembro", "miembro"])


def rol_comunidad(guild: discord.Guild) -> Optional[discord.Role]:
    try:
        import roles_acceso

        r = roles_acceso.rol_comunidad(guild)
        if r:
            return r
    except Exception:
        pass
    return encontrar_rol(guild, ["Comunidad", "🌐 Comunidad", "comunidad"])


async def buscar_usuario_roblox(username: str) -> Optional[Dict[str, Any]]:
    username = username.strip()
    if not username or " " in username:
        return None
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "HospitalBot/1.0",
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.post(
                "https://users.roblox.com/v1/usernames/users",
                json={"usernames": [username], "excludeBannedUsers": True},
                timeout=aiohttp.ClientTimeout(total=12),
            ) as resp:
                if resp.status != 200:
                    return None
                users = (await resp.json()).get("data") or []
                if not users:
                    return None
                user_id = users[0].get("id")
                if not user_id:
                    return None
        except Exception:
            return None
        try:
            async with session.get(
                f"https://users.roblox.com/v1/users/{user_id}",
                timeout=aiohttp.ClientTimeout(total=12),
            ) as resp:
                if resp.status != 200:
                    return None
                info = await resp.json()
        except Exception:
            return None
        avatar_url = None
        try:
            async with session.get(
                "https://thumbnails.roblox.com/v1/users/avatar-headshot",
                params={
                    "userIds": str(user_id),
                    "size": "420x420",
                    "format": "Png",
                    "isCircular": "false",
                },
                timeout=aiohttp.ClientTimeout(total=8),
            ) as resp:
                if resp.status == 200:
                    data_list = (await resp.json()).get("data") or []
                    if data_list:
                        avatar_url = data_list[0].get("imageUrl")
        except Exception:
            pass
        info["avatar_url"] = avatar_url
        return info


async def _renombrar_roblox(member: discord.Member, roblox_name: str) -> str:
    nick = (roblox_name or "")[:32]
    if not nick:
        return "sin nombre"
    try:
        if member.nick == nick:
            return f"ya era `{nick}`"
        await member.edit(nick=nick, reason=f"Verificación aprobada → {nick}")
        return f"renombrado a `{nick}`"
    except Exception as e:
        return f"no se pudo renombrar: {e}"


async def _aplicar_roles(member: discord.Member, reason: str) -> Tuple[List[str], List[str]]:
    ok, err = [], []
    try:
        import roles_acceso

        await roles_acceso.asegurar_roles_acceso(member.guild)
    except Exception:
        pass
    r_vis = rol_visitante(member.guild)
    r_com = rol_comunidad(member.guild)
    r_miem = rol_miembro(member.guild)
    try:
        if r_vis and r_vis in member.roles:
            await member.remove_roles(r_vis, reason=reason)
            ok.append(f"− {r_vis.name}")
    except Exception as e:
        err.append(str(e))
    for rol, label in ((r_com, "Comunidad"), (r_miem, "Miembro")):
        if not rol:
            err.append(f"Falta rol {label}")
            continue
        if rol in member.roles:
            ok.append(f"ya {rol.name}")
            continue
        try:
            await member.add_roles(rol, reason=reason)
            ok.append(f"+ {rol.name}")
        except Exception as e:
            err.append(f"{label}: {e}")
    return ok, err


def _puede_staff(member: discord.Member) -> bool:
    if member.guild_permissions.manage_roles or member.guild_permissions.administrator:
        return True
    try:
        import permisos

        return permisos.member_tiene_alguna_key(
            member,
            "FUNDADOR_OWNER",
            "CO_OWNER",
            "OWNER",
            "DIR_RRHH",
            "PREFECTO_OPERACIONES",
        )
    except Exception:
        return False


# ── Examen interactivo ──────────────────────────────────────────────────

class ExamenView(ui.View):
    """Preguntas una a una; al terminar envía al canal de log con Aprobar/Negar."""

    def __init__(
        self,
        *,
        user_id: int,
        guild_id: int,
        staff_id: int,
        log_channel_id: int,
        roblox_data: dict,
    ):
        super().__init__(timeout=1800)
        self.user_id = user_id
        self.guild_id = guild_id
        self.staff_id = staff_id
        self.log_channel_id = log_channel_id
        self.roblox_data = roblox_data
        self.idx = 0
        self.puntos = 0
        self.respuestas: List[dict] = []
        self._build_buttons()

    def _build_buttons(self) -> None:
        self.clear_items()
        if self.idx >= len(PREGUNTAS):
            return
        pregunta = PREGUNTAS[self.idx]
        for i, (texto, pts) in enumerate(pregunta["opts"]):
            label = texto if len(texto) <= 80 else texto[:77] + "…"
            style = (
                discord.ButtonStyle.primary
                if i == 0
                else discord.ButtonStyle.secondary
            )
            btn = ui.Button(label=label, style=style, custom_id=f"exam_{self.idx}_{i}")

            async def _cb(
                interaction: discord.Interaction,
                _i=i,
                _pts=pts,
                _texto=texto,
            ):
                await self._on_answer(interaction, _i, _pts, _texto)

            btn.callback = _cb
            self.add_item(btn)

    def _embed_pregunta(self) -> discord.Embed:
        p = PREGUNTAS[self.idx]
        emb = discord.Embed(
            title=f"📋 Examen de ingreso · Pregunta {self.idx + 1}/{len(PREGUNTAS)}",
            description=f"**{p['q']}**\n\nElige la opción que consideres correcta.",
            color=0x3498DB,
            timestamp=discord.utils.utcnow(),
        )
        emb.set_footer(
            text=f"Roblox: {self.roblox_data.get('name')} · Puntaje parcial: {self.puntos}/{PUNTOS_MAX}"
        )
        return emb

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Este examen no es tuyo.", ephemeral=True
            )
            return False
        return True

    async def _on_answer(
        self, interaction: discord.Interaction, opt_i: int, pts: int, texto: str
    ):
        p = PREGUNTAS[self.idx]
        self.puntos += pts
        self.respuestas.append(
            {
                "n": self.idx + 1,
                "pregunta": p["q"],
                "respuesta": texto,
                "puntos": pts,
            }
        )
        self.idx += 1

        if self.idx >= len(PREGUNTAS):
            await interaction.response.defer()
            await self._finalizar(interaction)
            return

        self._build_buttons()
        await interaction.response.edit_message(
            embed=self._embed_pregunta(), view=self
        )

    async def _finalizar(self, interaction: discord.Interaction) -> None:
        self.stop()
        recomendado = self.puntos >= PUNTOS_MIN_RECOMENDADO
        pct = int(100 * self.puntos / PUNTOS_MAX)

        # Guardar examen pendiente de staff
        data = _load()
        exam_id = f"{self.guild_id}_{self.user_id}_{int(datetime.now(timezone.utc).timestamp())}"
        data["examenes"][exam_id] = {
            "user_id": self.user_id,
            "guild_id": self.guild_id,
            "staff_id": self.staff_id,
            "log_channel_id": self.log_channel_id,
            "roblox": self.roblox_data.get("name"),
            "roblox_id": self.roblox_data.get("id"),
            "displayName": self.roblox_data.get("displayName"),
            "avatar_url": self.roblox_data.get("avatar_url"),
            "puntos": self.puntos,
            "max": PUNTOS_MAX,
            "recomendado": recomendado,
            "respuestas": self.respuestas,
            "estado": "pendiente_staff",
            "at": _now(),
        }
        data["pendientes"][str(self.user_id)] = {
            "exam_id": exam_id,
            "staff_id": self.staff_id,
            "at": _now(),
        }
        _save(data)

        # DM al usuario: espera revisión
        emb_user = discord.Embed(
            title="📨 Examen enviado a revisión",
            description=(
                f"Completaste las **{len(PREGUNTAS)}** preguntas.\n\n"
                f"**Puntaje:** `{self.puntos}/{PUNTOS_MAX}` ({pct}%)\n"
                f"**Mínimo orientativo:** `{PUNTOS_MIN_RECOMENDADO}` pts\n\n"
                f"El staff revisará tus respuestas en el canal de logs y "
                f"**aprobará o negará** tu verificación.\n"
                f"Te avisaremos por MD."
            ),
            color=0xF39C12,
            timestamp=discord.utils.utcnow(),
        )
        try:
            await interaction.edit_original_response(embed=emb_user, view=None)
        except Exception:
            try:
                await interaction.followup.send(embed=emb_user, ephemeral=True)
            except Exception:
                pass
        try:
            user = interaction.user
            await user.send(embed=emb_user)
        except Exception:
            pass

        # Canal de log: detalle + botones staff
        guild = interaction.client.get_guild(self.guild_id)
        canal = guild.get_channel(self.log_channel_id) if guild else None
        if not canal:
            return

        lineas_resp = []
        for r in self.respuestas:
            icon = "🟢" if r["puntos"] == 2 else ("🟡" if r["puntos"] == 1 else "🔴")
            lineas_resp.append(
                f"{icon} **P{r['n']}** (+{r['puntos']}) {r['respuesta'][:80]}"
            )

        member = guild.get_member(self.user_id) if guild else None
        emb_log = discord.Embed(
            title="🔎 Verificación pendiente de staff",
            description=(
                f"**Usuario:** {member.mention if member else self.user_id}\n"
                f"**Roblox:** `{self.roblox_data.get('name')}` "
                f"(ID `{self.roblox_data.get('id')}`)\n"
                f"**Display:** {self.roblox_data.get('displayName')}\n"
                f"**Puntaje:** **{self.puntos}/{PUNTOS_MAX}** ({pct}%)\n"
                f"**Recomendación automática:** "
                f"{'✅ Apto (≥ mínimo)' if recomendado else '⚠️ Bajo mínimo — revisar'}\n"
                f"**Staff que inició:** <@{self.staff_id}>"
            ),
            color=0x2ECC71 if recomendado else 0xE67E22,
            timestamp=discord.utils.utcnow(),
        )
        if self.roblox_data.get("avatar_url"):
            emb_log.set_thumbnail(url=self.roblox_data["avatar_url"])

        # Partir respuestas en fields (límite 1024)
        bloque = ""
        nfield = 1
        for line in lineas_resp:
            if len(bloque) + len(line) + 1 > 1000:
                emb_log.add_field(
                    name=f"Respuestas ({nfield})",
                    value=bloque,
                    inline=False,
                )
                bloque = line + "\n"
                nfield += 1
            else:
                bloque += line + "\n"
        if bloque:
            emb_log.add_field(
                name=f"Respuestas ({nfield})",
                value=bloque,
                inline=False,
            )

        emb_log.set_footer(text=f"exam_id={exam_id}")

        view = StaffDecisionView(exam_id=exam_id)
        try:
            msg = await canal.send(embed=emb_log, view=view)
            data = _load()
            if exam_id in data["examenes"]:
                data["examenes"][exam_id]["log_message_id"] = msg.id
                _save(data)
        except Exception as e:
            print(f"[verificacion] log channel: {e}", flush=True)


class StaffDecisionView(ui.View):
    def __init__(self, exam_id: str):
        super().__init__(timeout=None)
        self.exam_id = exam_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            return False
        if not _puede_staff(interaction.user):
            await interaction.response.send_message(
                "❌ Solo staff puede aprobar o negar.", ephemeral=True
            )
            return False
        return True

    @ui.button(
        label="✅ Aprobar verificación",
        style=discord.ButtonStyle.success,
        custom_id="verif_staff_aprobar",
    )
    async def aprobar(self, interaction: discord.Interaction, button: ui.Button):
        await self._decidir(interaction, aprobar=True)

    @ui.button(
        label="❌ Negar verificación",
        style=discord.ButtonStyle.danger,
        custom_id="verif_staff_negar",
    )
    async def negar(self, interaction: discord.Interaction, button: ui.Button):
        await self._decidir(interaction, aprobar=False)

    async def _decidir(self, interaction: discord.Interaction, aprobar: bool):
        # exam_id desde footer del embed si la view es persistente genérica
        exam_id = self.exam_id
        if exam_id == "persist" or not exam_id:
            emb = interaction.message.embeds[0] if interaction.message.embeds else None
            if emb and emb.footer and emb.footer.text:
                ft = emb.footer.text
                if "exam_id=" in ft:
                    exam_id = ft.split("exam_id=", 1)[1].strip()

        data = _load()
        exam = data["examenes"].get(exam_id)
        if not exam:
            return await interaction.response.send_message(
                "❌ Examen no encontrado o ya procesado.", ephemeral=True
            )
        if exam.get("estado") not in ("pendiente_staff", None):
            return await interaction.response.send_message(
                f"⚠️ Ya fue **{exam.get('estado')}**.", ephemeral=True
            )

        await interaction.response.defer()
        guild = interaction.guild
        member = guild.get_member(int(exam["user_id"])) if guild else None
        roblox_name = exam.get("roblox") or "?"

        if aprobar:
            roles_ok, roles_err = [], []
            nick_msg = "—"
            if member:
                roles_ok, roles_err = await _aplicar_roles(
                    member, f"Verificación aprobada por {interaction.user}"
                )
                nick_msg = await _renombrar_roblox(member, roblox_name)

            exam["estado"] = "aprobado"
            exam["revisado_por"] = interaction.user.id
            exam["revisado_at"] = _now()
            exam["roles"] = roles_ok
            exam["nick"] = nick_msg
            data["verificados"][str(exam["user_id"])] = {
                "roblox": roblox_name,
                "roblox_id": exam.get("roblox_id"),
                "puntos": exam.get("puntos"),
                "staff_id": interaction.user.id,
                "fecha": _now(),
            }
            data["pendientes"].pop(str(exam["user_id"]), None)
            data["examenes"][exam_id] = exam
            _save(data)

            emb = discord.Embed(
                title="✅ Verificación APROBADA",
                description=(
                    f"**Staff:** {interaction.user.mention}\n"
                    f"**Usuario:** {member.mention if member else exam['user_id']}\n"
                    f"**Roblox:** `{roblox_name}`\n"
                    f"**Puntaje:** {exam.get('puntos')}/{PUNTOS_MAX}\n"
                    f"**Roles:** {', '.join(roles_ok) or '—'}\n"
                    f"**Apodo:** {nick_msg}"
                ),
                color=0x2ECC71,
                timestamp=discord.utils.utcnow(),
            )
            for c in self.children:
                c.disabled = True
            await interaction.message.edit(embed=emb, view=self)

            if member:
                try:
                    await member.send(
                        embed=discord.Embed(
                            title="✅ Verificación aprobada",
                            description=(
                                f"Tu ingreso fue **aprobado** por el staff.\n"
                                f"Roblox: **`{roblox_name}`**\n"
                                f"Puntaje del examen: **{exam.get('puntos')}/{PUNTOS_MAX}**\n"
                                f"Apodo: {nick_msg}\n\n"
                                f"¡Bienvenido/a a la comunidad!"
                            ),
                            color=0x2ECC71,
                        )
                    )
                except Exception:
                    pass
        else:
            exam["estado"] = "rechazado"
            exam["revisado_por"] = interaction.user.id
            exam["revisado_at"] = _now()
            data["rechazados"][str(exam["user_id"])] = exam
            data["pendientes"].pop(str(exam["user_id"]), None)
            data["examenes"][exam_id] = exam
            _save(data)

            emb = discord.Embed(
                title="❌ Verificación NEGADA",
                description=(
                    f"**Staff:** {interaction.user.mention}\n"
                    f"**Usuario:** {member.mention if member else exam['user_id']}\n"
                    f"**Roblox:** `{roblox_name}`\n"
                    f"**Puntaje:** {exam.get('puntos')}/{PUNTOS_MAX}\n\n"
                    f"Revisa la normativa de RP e inténtalo más tarde."
                ),
                color=0xE74C3C,
                timestamp=discord.utils.utcnow(),
            )
            for c in self.children:
                c.disabled = True
            await interaction.message.edit(embed=emb, view=self)

            if member:
                try:
                    await member.send(
                        embed=discord.Embed(
                            title="❌ Verificación no aprobada",
                            description=(
                                f"El staff **no aprobó** tu verificación.\n\n"
                                f"Puntaje: **{exam.get('puntos')}/{PUNTOS_MAX}** "
                                f"(orientativo mínimo {PUNTOS_MIN_RECOMENDADO}).\n\n"
                                f"**Qué hacer:** lee la normativa de RP del servidor, "
                                f"prepárate y solicita de nuevo la verificación al staff."
                            ),
                            color=0xE74C3C,
                        )
                    )
                except Exception:
                    pass


# ── Modal Roblox → inicia examen ────────────────────────────────────────

class RobloxModal(ui.Modal, title="🎮 Verificación Roblox"):
    usuario_roblox = ui.TextInput(
        label="Usuario de Roblox (exacto, sin espacios)",
        placeholder="Ej: Builderman",
        max_length=32,
        min_length=3,
    )

    def __init__(self, staff_id: int, guild_id: int, log_channel_id: int):
        super().__init__()
        self.staff_id = staff_id
        self.guild_id = guild_id
        self.log_channel_id = log_channel_id

    async def on_submit(self, interaction: discord.Interaction):
        roblox_input = str(self.usuario_roblox).strip()
        if not roblox_input or " " in roblox_input:
            return await interaction.response.send_message(
                "❌ Usuario inválido.", ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)
        roblox_data = await buscar_usuario_roblox(roblox_input)
        if not roblox_data:
            return await interaction.followup.send(
                embed=crear_embed(
                    "error",
                    "Cuenta no encontrada",
                    f"No existe Roblox **`{roblox_input}`**. Verifica el nombre.",
                ),
                ephemeral=True,
            )

        view = ExamenView(
            user_id=interaction.user.id,
            guild_id=self.guild_id,
            staff_id=self.staff_id,
            log_channel_id=self.log_channel_id,
            roblox_data=roblox_data,
        )
        emb = view._embed_pregunta()
        emb.description = (
            f"✅ Cuenta **`{roblox_data.get('name')}`** verificada en Roblox.\n\n"
            f"Ahora responde el **examen de RP** ({len(PREGUNTAS)} preguntas).\n"
            + (emb.description or "")
        )
        await interaction.followup.send(embed=emb, view=view, ephemeral=True)


class VerificarView(ui.View):
    def __init__(self, staff_id: int, guild_id: int, log_channel_id: int):
        super().__init__(timeout=86400)
        self.staff_id = staff_id
        self.guild_id = guild_id
        self.log_channel_id = log_channel_id

    @ui.button(
        label="Ingresar usuario Roblox",
        style=discord.ButtonStyle.success,
        emoji="🎮",
    )
    async def abrir(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(
            RobloxModal(self.staff_id, self.guild_id, self.log_channel_id)
        )


async def enviar_dm_verificacion(
    member: discord.Member,
    staff: discord.Member,
    log_channel_id: int,
) -> bool:
    hospital = getattr(config, "NOMBRE_HOSPITAL", None) or "Hospital"
    emb = crear_embed(
        "roblox",
        "Verificación Roblox + examen RP",
        f"Hola **{member.display_name}**.\n\n"
        f"**{hospital}** solicita tu verificación:\n"
        f"1. Usuario de Roblox (cuenta real)\n"
        f"2. Examen de **{len(PREGUNTAS)}** preguntas de normativa/RP\n"
        f"3. Un staff revisará y **aprobará o negará**\n\n"
        f"Solicitado por: {staff.mention}",
        autor=staff,
    )
    view = VerificarView(staff.id, member.guild.id, log_channel_id)
    try:
        await member.send(embed=emb, view=view)
        return True
    except discord.Forbidden:
        return False


def registrar(bot: commands.Bot) -> None:
    for name in ("verificar_roblox", "verificar", "verificar_all"):
        try:
            bot.tree.remove_command(name)
        except Exception:
            pass

    # View persistente para botones tras reinicio (exam_id en footer)
    bot.add_view(StaffDecisionView(exam_id="persist"))

    @bot.tree.command(
        name="verificar_roblox",
        description="[Staff] Roblox + examen; resultado al canal de log para aprobar/negar",
    )
    @app_commands.describe(
        miembro="Usuario a verificar",
        canal_log="Canal donde el staff verá respuestas y aprobará/negará",
    )
    async def verificar_roblox_cmd(
        inter: discord.Interaction,
        miembro: discord.Member,
        canal_log: discord.TextChannel,
    ):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _puede_staff(inter.user):
            return await inter.response.send_message(
                "❌ Solo staff.", ephemeral=True
            )
        if miembro.bot:
            return await inter.response.send_message(
                "❌ No bots.", ephemeral=True
            )

        ok = await enviar_dm_verificacion(miembro, inter.user, canal_log.id)
        data = _load()
        data["pendientes"][str(miembro.id)] = {
            "staff_id": inter.user.id,
            "log_channel_id": canal_log.id,
            "at": _now(),
        }
        _save(data)

        if ok:
            await inter.response.send_message(
                embed=crear_embed(
                    "exito",
                    "Verificación iniciada",
                    f"DM enviado a {miembro.mention}.\n"
                    f"Log/revisión: {canal_log.mention}\n"
                    f"Ahí podrás **aprobar o negar** tras el examen.",
                ),
                ephemeral=True,
            )
        else:
            await inter.response.send_message(
                embed=crear_embed(
                    "aviso",
                    "DM cerrado",
                    f"{miembro.mention} no acepta MD. Comparte el botón con él:",
                ),
                view=VerificarView(inter.user.id, inter.guild.id, canal_log.id),
                ephemeral=True,
            )

    @bot.tree.command(
        name="verificar", description="[Staff] Alias de /verificar_roblox"
    )
    @app_commands.describe(
        miembro="Usuario",
        canal_log="Canal de log para aprobar/negar",
    )
    async def verificar_alias(
        inter: discord.Interaction,
        miembro: discord.Member,
        canal_log: discord.TextChannel,
    ):
        await verificar_roblox_cmd.callback(inter, miembro, canal_log)

    @bot.tree.command(
        name="verificar_all",
        description="[Staff] Envía verificación + examen a todos (mismo canal de log)",
    )
    @app_commands.describe(canal_log="Canal de log para revisar y aprobar/negar")
    async def verificar_all_cmd(
        inter: discord.Interaction, canal_log: discord.TextChannel
    ):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _puede_staff(inter.user):
            return await inter.response.send_message(
                "❌ Solo staff.", ephemeral=True
            )
        await inter.response.defer(ephemeral=True)
        miembros = [m for m in inter.guild.members if not m.bot]
        enviados = fallidos = 0
        data = _load()
        for m in miembros:
            if await enviar_dm_verificacion(m, inter.user, canal_log.id):
                enviados += 1
                data["pendientes"][str(m.id)] = {
                    "staff_id": inter.user.id,
                    "log_channel_id": canal_log.id,
                    "at": _now(),
                    "masivo": True,
                }
            else:
                fallidos += 1
            await asyncio.sleep(0.35)
        _save(data)
        await inter.followup.send(
            embed=crear_embed(
                "exito",
                "Verificación masiva",
                f"**Enviados:** {enviados} · **DM cerrados:** {fallidos}\n"
                f"**Canal de revisión:** {canal_log.mention}",
            ),
            ephemeral=True,
        )

    print("[verificacion] OK — Roblox + examen + log aprobar/negar")
