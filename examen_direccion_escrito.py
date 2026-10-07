# -*- coding: utf-8 -*-
"""
Examen escrito: respuestas libres al MD → log para staff.
Defer inmediato en todas las interacciones (evita "no respondió a tiempo").
"""
from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List

import discord
from discord import ui
from discord.ext import commands

try:
    import examen_direccion as ed
except Exception:
    ed = None  # type: ignore

_DATA = Path(__file__).resolve().parent / "examen_direccion_data.json"
_TIMEOUT_RESPUESTA = 600


def _load() -> dict:
    if not _DATA.exists():
        return {"sesiones": {}, "logs": {}}
    try:
        return json.loads(_DATA.read_text(encoding="utf-8"))
    except Exception:
        return {"sesiones": {}, "logs": {}}


def _save(data: dict) -> None:
    try:
        _DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[examen_escrito] save: {e}")


def _es_staff(m: discord.Member) -> bool:
    if ed is not None and hasattr(ed, "_es_staff"):
        try:
            return bool(ed._es_staff(m))
        except Exception:
            pass
    if m.guild_permissions.administrator or m.guild_permissions.manage_guild:
        return True
    return bool(m.guild and m.id == m.guild.owner_id)


class ComenzarEscritoView(ui.View):
    def __init__(self, session_id: str):
        super().__init__(timeout=900)
        self.session_id = session_id

    @ui.button(
        label="Comenzar examen escrito",
        style=discord.ButtonStyle.primary,
        emoji="✍️",
    )
    async def comenzar(self, inter: discord.Interaction, button: ui.Button):
        # 1) Responder YA (evita timeout de 3s)
        try:
            await inter.response.defer()
        except discord.InteractionResponded:
            pass
        except Exception:
            try:
                await inter.response.send_message("⏳ Iniciando…", ephemeral=True)
            except Exception:
                return

        data = _load()
        ses = data.get("sesiones", {}).get(self.session_id)
        if not ses:
            return await inter.followup.send("❌ Sesión no encontrada.", ephemeral=True)
        if int(ses.get("user_id") or 0) != inter.user.id:
            return await inter.followup.send("❌ Este examen no es tuyo.", ephemeral=True)
        if ses.get("terminado"):
            return await inter.followup.send("❌ Ya finalizaste este examen.", ephemeral=True)
        if ses.get("en_curso"):
            return await inter.followup.send(
                "⏳ Ya estás en el examen. Escribe tu respuesta en este MD.",
                ephemeral=True,
            )

        ses["en_curso"] = True
        ses["respuestas"] = []
        ses["idx"] = 0
        data["sesiones"][self.session_id] = ses
        _save(data)

        emb = discord.Embed(
            title="✍️  Examen escrito iniciado",
            description=(
                f"Responderás **{len(ses.get('preguntas') or [])}** preguntas "
                f"**con tus propias palabras**.\n\n"
                f"• Escribe cada respuesta **en este chat (MD)**\n"
                f"• Tiempo por pregunta: **{_TIMEOUT_RESPUESTA // 60} min**\n"
                f"• Todo se envía al **log** para el staff\n\n"
                f"La primera pregunta llega en un momento…"
            ),
            color=int(ses.get("color") or 0x1A5276),
        )
        try:
            await inter.edit_original_response(embed=emb, view=None)
        except Exception:
            try:
                await inter.followup.send(embed=emb)
            except Exception:
                pass

        asyncio.create_task(
            _correr_examen_escrito(inter.client, inter.user, self.session_id)
        )


async def _correr_examen_escrito(
    bot: commands.Bot, user: discord.abc.User, session_id: str
):
    data = _load()
    ses = data.get("sesiones", {}).get(session_id)
    if not ses:
        return

    preguntas = ses.get("preguntas") or []
    textos: List[str] = []
    for p in preguntas:
        if isinstance(p, (list, tuple)) and p:
            textos.append(str(p[0]))
        else:
            textos.append(str(p))

    total = len(textos)
    dir_nombre = ses.get("dir_nombre") or "Dirección"
    emoji = ses.get("emoji") or "📋"
    color = int(ses.get("color") or 0x1A5276)
    respuestas: List[Dict[str, str]] = list(ses.get("respuestas") or [])

    def check(m: discord.Message) -> bool:
        if m.author.id != user.id:
            return False
        if not (m.content or "").strip():
            return False
        # DM con el bot
        return isinstance(m.channel, discord.DMChannel) or (
            getattr(m.channel, "type", None) == discord.ChannelType.private
        )

    for idx, pregunta in enumerate(textos):
        emb = discord.Embed(
            title=f"{emoji}  {dir_nombre} · Pregunta {idx + 1}/{total}",
            description=(
                f"**{pregunta}**\n\n"
                f"✍️ Escribe tu respuesta **con tus palabras** aquí en el MD.\n"
                f"_(Redacta tu criterio; no uses solo una letra.)_"
            ),
            color=color,
        )
        emb.set_footer(text=f"Tiempo: {_TIMEOUT_RESPUESTA // 60} min · Hospital General")
        try:
            await user.send(embed=emb)
        except Exception as e:
            print(f"[examen_escrito] DM pregunta: {e}")
            break

        try:
            msg = await bot.wait_for("message", check=check, timeout=_TIMEOUT_RESPUESTA)
            texto = (msg.content or "").strip()[:1900]
        except asyncio.TimeoutError:
            texto = "_(Sin respuesta — tiempo agotado)_"
            try:
                await user.send(
                    embed=discord.Embed(
                        title="⏰ Tiempo agotado",
                        description="Se registró sin respuesta y se continúa.",
                        color=0xE67E22,
                    )
                )
            except Exception:
                pass

        respuestas.append({"pregunta": pregunta, "respuesta": texto})
        ses["respuestas"] = respuestas
        ses["idx"] = idx + 1
        data = _load()
        data.setdefault("sesiones", {})[session_id] = ses
        _save(data)

        try:
            await user.send(
                embed=discord.Embed(
                    description=f"✅ Respuesta **{idx + 1}/{total}** registrada.",
                    color=0x2ECC71,
                )
            )
        except Exception:
            pass

    ses["terminado"] = True
    ses["en_curso"] = False
    data = _load()
    data.setdefault("sesiones", {})[session_id] = ses
    _save(data)

    try:
        await user.send(
            embed=discord.Embed(
                title=f"{emoji}  Examen escrito enviado",
                description=(
                    f"Completaste **{len(respuestas)}/{total}** de **{dir_nombre}**.\n\n"
                    f"El staff revisará tus respuestas en el **log** y te avisará."
                ),
                color=0x1A5276,
            ).set_footer(text="Hospital General")
        )
    except Exception:
        pass

    await _enviar_log_escrito(bot, ses, respuestas)


async def _enviar_log_escrito(
    bot: commands.Bot, ses: dict, respuestas: List[Dict[str, str]]
):
    canal_id = int(ses.get("log_channel_id") or 0)
    if not canal_id:
        return
    canal = bot.get_channel(canal_id)
    if not isinstance(canal, discord.TextChannel):
        try:
            canal = await bot.fetch_channel(canal_id)
        except Exception:
            return
    if not isinstance(canal, discord.TextChannel):
        return

    uid = int(ses.get("user_id") or 0)
    dir_nombre = ses.get("dir_nombre") or "—"
    emoji = ses.get("emoji") or "📋"
    sid = str(ses.get("id") or "")

    head = discord.Embed(
        title=f"{emoji}  Log examen escrito · {dir_nombre}",
        description=(
            f"**Candidato:** <@{uid}> (`{uid}`)\n"
            f"**Respuestas:** {len(respuestas)}\n"
            f"El staff lee y **Aprueba** o **Rechaza**."
        ),
        color=0xF1C40F,
    )
    head.set_footer(text=f"Sesión {sid[:16]} · Hospital General")

    view = LogEscritoView(session_id=sid, user_id=uid, dir_nombre=dir_nombre)
    try:
        await canal.send(embed=head, view=view)
    except Exception as e:
        print(f"[examen_escrito] log head: {e}")
        return

    bloque = ""
    num = 0
    for i, item in enumerate(respuestas, start=1):
        q = (item.get("pregunta") or "")[:400]
        r = (item.get("respuesta") or "")[:800]
        pieza = f"**{i}. {q}**\n> {r}\n\n"
        if len(bloque) + len(pieza) > 3800:
            num += 1
            try:
                await canal.send(
                    embed=discord.Embed(
                        title=f"Respuestas · parte {num}",
                        description=bloque,
                        color=0x5D6D7E,
                    )
                )
            except Exception:
                for j in range(0, len(bloque), 1900):
                    try:
                        await canal.send(bloque[j : j + 1900])
                    except Exception:
                        break
            bloque = pieza
        else:
            bloque += pieza

    if bloque.strip():
        num += 1
        try:
            await canal.send(
                embed=discord.Embed(
                    title=f"Respuestas · parte {num}",
                    description=bloque,
                    color=0x5D6D7E,
                )
            )
        except Exception:
            for j in range(0, len(bloque), 1900):
                try:
                    await canal.send(bloque[j : j + 1900])
                except Exception:
                    break


class LogEscritoView(ui.View):
    def __init__(self, session_id: str = "", user_id: int = 0, dir_nombre: str = ""):
        super().__init__(timeout=None)
        self.session_id = session_id
        self.user_id = user_id
        self.dir_nombre = dir_nombre

    @ui.button(
        label="Aprobar postulación",
        style=discord.ButtonStyle.success,
        emoji="✅",
        custom_id="examen_escrito:aprobar",
    )
    async def aprobar(self, inter: discord.Interaction, button: ui.Button):
        try:
            await inter.response.defer()
        except Exception:
            pass
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.followup.send("❌ Solo en servidor.", ephemeral=True)
        if not _es_staff(inter.user):
            return await inter.followup.send("❌ Solo staff.", ephemeral=True)

        data = _load()
        ses = data.get("sesiones", {}).get(self.session_id) or {}
        uid = int(ses.get("user_id") or self.user_id)
        dir_n = ses.get("dir_nombre") or self.dir_nombre
        member = inter.guild.get_member(uid)
        if member:
            try:
                await member.send(
                    embed=discord.Embed(
                        title="✅ Postulación aprobada",
                        description=(
                            f"Tu examen escrito de **{dir_n}** fue **aprobado** "
                            f"por {inter.user.mention}."
                        ),
                        color=0x2ECC71,
                    )
                )
            except Exception:
                pass

        emb = inter.message.embeds[0].copy() if inter.message and inter.message.embeds else discord.Embed()
        emb.color = 0x2ECC71
        emb.title = f"✅ Aprobado · {dir_n}"
        emb.description = (emb.description or "") + f"\n\n**Aprobado por** {inter.user.mention}"
        try:
            await inter.edit_original_response(embed=emb, view=None)
        except Exception:
            try:
                await inter.message.edit(embed=emb, view=None)
            except Exception:
                pass

    @ui.button(
        label="Rechazar",
        style=discord.ButtonStyle.danger,
        emoji="❌",
        custom_id="examen_escrito:rechazar",
    )
    async def rechazar(self, inter: discord.Interaction, button: ui.Button):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message("❌ Solo en servidor.", ephemeral=True)
        if not _es_staff(inter.user):
            return await inter.response.send_message("❌ Solo staff.", ephemeral=True)

        parent = self

        class MotivoModal(ui.Modal, title="Motivo del rechazo"):
            motivo = ui.TextInput(
                label="Motivo",
                style=discord.TextStyle.paragraph,
                required=True,
                max_length=500,
            )

            async def on_submit(self, modal_inter: discord.Interaction):
                try:
                    await modal_inter.response.defer()
                except Exception:
                    pass
                data = _load()
                ses = data.get("sesiones", {}).get(parent.session_id) or {}
                uid = int(ses.get("user_id") or parent.user_id)
                dir_n = ses.get("dir_nombre") or parent.dir_nombre
                motivo_txt = str(self.motivo.value).strip()
                member = (
                    modal_inter.guild.get_member(uid) if modal_inter.guild else None
                )
                if member:
                    try:
                        await member.send(
                            embed=discord.Embed(
                                title="❌ Postulación rechazada",
                                description=(
                                    f"Examen escrito de **{dir_n}** rechazado.\n\n"
                                    f"**Motivo:** {motivo_txt}"
                                ),
                                color=0xE74C3C,
                            )
                        )
                    except Exception:
                        pass
                emb = (
                    modal_inter.message.embeds[0].copy()
                    if modal_inter.message and modal_inter.message.embeds
                    else discord.Embed()
                )
                emb.color = 0xE74C3C
                emb.title = f"❌ Rechazado · {dir_n}"
                emb.description = (
                    (emb.description or "")
                    + f"\n\n**Rechazado por** {modal_inter.user.mention}\n"
                    f"**Motivo:** {motivo_txt}"
                )
                try:
                    await modal_inter.edit_original_response(embed=emb, view=None)
                except Exception:
                    try:
                        if modal_inter.message:
                            await modal_inter.message.edit(embed=emb, view=None)
                    except Exception:
                        pass

        await inter.response.send_modal(MotivoModal())


def _parchear_envio() -> None:
    if ed is None:
        return
    try:
        ed._MINIMO = 70  # type: ignore
        ed._PREGUNTAS_POR_EXAMEN = 20  # type: ignore
    except Exception:
        pass

    if not hasattr(ed, "DireccionSelect"):
        return

    SelectCls = ed.DireccionSelect

    async def callback(self, interaction: discord.Interaction):  # type: ignore
        # DEFER INMEDIATO (antes de buscar roles / preguntas)
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.InteractionResponded:
            pass
        except Exception as e:
            print(f"[examen_escrito] defer select: {e}")
            return

        try:
            key = self.values[0]
            meta = next((d for d in ed._DIRECCIONES if d[0] == key), None)
            if not meta:
                return await interaction.followup.send(
                    "❌ Dirección inválida.", ephemeral=True
                )
            _, nombre, emoji, color = meta
            guild = interaction.guild
            if not guild:
                return await interaction.followup.send(
                    "❌ Solo en servidor.", ephemeral=True
                )

            miembros = ed._miembros_con_rol(guild, key)
            preguntas = ed._preguntas_para(key)
            if not preguntas:
                return await interaction.followup.send(
                    "❌ Sin preguntas para esta dirección.", ephemeral=True
                )
            if not miembros:
                return await interaction.followup.send(
                    f"⚠️ No hay miembros con el rol de **{nombre}**.",
                    ephemeral=True,
                )

            data = _load()
            data.setdefault("sesiones", {})
            enviados = fallos = 0

            for m in miembros:
                sid = f"{m.id}_{key}_{int(time.time())}"
                data["sesiones"][sid] = {
                    "id": sid,
                    "user_id": m.id,
                    "dir_key": key,
                    "dir_nombre": nombre,
                    "emoji": emoji,
                    "color": color,
                    "log_channel_id": self.log_channel.id,
                    "preguntas": [
                        [
                            p[0],
                            p[1] if len(p) > 1 else [],
                            p[2] if len(p) > 2 else 0,
                        ]
                        if isinstance(p, (list, tuple))
                        else [str(p), [], 0]
                        for p in preguntas
                    ],
                    "idx": 0,
                    "respuestas": [],
                    "terminado": False,
                    "en_curso": False,
                    "modo": "escrito",
                }
                try:
                    emb = discord.Embed(
                        title=f"{emoji}  Examen escrito · {nombre}",
                        description=(
                            f"Postulación con **respuestas escritas**.\n\n"
                            f"• **{len(preguntas)}** preguntas\n"
                            f"• Respondes **en el MD** del bot\n"
                            f"• El staff revisa en el **log**\n\n"
                            f"Pulsa **Comenzar examen escrito**."
                        ),
                        color=color,
                    ).set_footer(text="Hospital General")
                    await m.send(embed=emb, view=ComenzarEscritoView(sid))
                    enviados += 1
                except Exception:
                    fallos += 1

            _save(data)
            await interaction.followup.send(
                embed=discord.Embed(
                    title=f"{emoji}  Examen enviado · {nombre}",
                    description=(
                        f"**Log:** {self.log_channel.mention}\n"
                        f"**MD ok:** {enviados}/{len(miembros)} · Fallos: {fallos}\n"
                        f"**Modo:** texto libre"
                    ),
                    color=color,
                ),
                ephemeral=True,
            )
            try:
                await self.log_channel.send(
                    embed=discord.Embed(
                        title=f"{emoji}  Ronda escrita · {nombre}",
                        description=(
                            f"Por {interaction.user.mention}\n"
                            f"Enviados: {enviados}/{len(miembros)}"
                        ),
                        color=color,
                    )
                )
            except Exception:
                pass
        except Exception as e:
            print(f"[examen_escrito] select: {e}")
            try:
                await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
            except Exception:
                pass

    SelectCls.callback = callback  # type: ignore


def registrar(bot: commands.Bot) -> None:
    try:
        bot.add_view(LogEscritoView())
    except Exception:
        pass
    _parchear_envio()

    # También parchear el slash por si responde lento
    if ed is not None:
        try:
            # asegurar que el comando haga defer si tarda — el original ya responde embeds rápido
            pass
        except Exception:
            pass

    print("[examen_escrito] OK — defer inmediato + respuestas libres")
