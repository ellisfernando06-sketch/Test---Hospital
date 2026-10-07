# -*- coding: utf-8 -*-
"""Al aprobar: felicitación profesional al puesto + explicación de criterios."""
from __future__ import annotations

import json
from pathlib import Path

import discord
from discord.ext import commands

from examen_aprobacion_msg import embed_felicitacion

_DATA = Path(__file__).resolve().parent / "examen_direccion_data.json"


def _load() -> dict:
    if not _DATA.exists():
        return {"sesiones": {}}
    try:
        return json.loads(_DATA.read_text(encoding="utf-8"))
    except Exception:
        return {"sesiones": {}}


def _sesion(session_id: str) -> dict:
    return (_load().get("sesiones") or {}).get(session_id) or {}


async def _enviar_felicitacion(
    member: discord.Member,
    *,
    session_id: str = "",
    dir_nombre: str = "",
    aprobado_por: str = "Staff",
) -> None:
    ses = _sesion(session_id) if session_id else {}
    dir_key = str(ses.get("dir_key") or "")
    dir_n = str(ses.get("dir_nombre") or dir_nombre or "Dirección")
    emoji = str(ses.get("emoji") or "🏛️")
    emb = embed_felicitacion(
        dir_key=dir_key,
        dir_nombre=dir_n,
        aprobado_por=aprobado_por,
        emoji=emoji,
    )
    try:
        await member.send(embed=emb)
    except Exception as e:
        print(f"[examen_aprobacion] DM: {e}")


def registrar(bot: commands.Bot) -> None:
    # Parche examen escrito
    try:
        import examen_direccion_escrito as escrito

        if hasattr(escrito, "LogEscritoView"):

            class LogEscritoView(escrito.LogEscritoView):
                @discord.ui.button(
                    label="Aprobar postulación",
                    style=discord.ButtonStyle.success,
                    emoji="✅",
                    custom_id="examen_escrito:aprobar",
                )
                async def aprobar(self, inter: discord.Interaction, button: discord.ui.Button):
                    try:
                        await inter.response.defer()
                    except Exception:
                        pass
                    if not inter.guild or not isinstance(inter.user, discord.Member):
                        return await inter.followup.send(
                            "❌ Solo en servidor.", ephemeral=True
                        )
                    if not escrito._es_staff(inter.user):
                        return await inter.followup.send(
                            "❌ Solo staff.", ephemeral=True
                        )

                    ses = _sesion(self.session_id)
                    uid = int(ses.get("user_id") or self.user_id)
                    dir_n = ses.get("dir_nombre") or self.dir_nombre
                    member = inter.guild.get_member(uid)
                    if member:
                        await _enviar_felicitacion(
                            member,
                            session_id=self.session_id,
                            dir_nombre=dir_n,
                            aprobado_por=str(inter.user),
                        )

                    emb = (
                        inter.message.embeds[0].copy()
                        if inter.message and inter.message.embeds
                        else discord.Embed()
                    )
                    emb.color = 0x2ECC71
                    emb.title = f"✅ Aprobado · {dir_n}"
                    emb.description = (
                        (emb.description or "")
                        + f"\n\n**Aprobado por** {inter.user.mention}\n"
                        f"Se envió felicitación profesional al postulante."
                    )
                    try:
                        await inter.edit_original_response(embed=emb, view=None)
                    except Exception:
                        try:
                            if inter.message:
                                await inter.message.edit(embed=emb, view=None)
                        except Exception:
                            pass

            escrito.LogEscritoView = LogEscritoView
            try:
                bot.add_view(LogEscritoView())
            except Exception:
                pass
    except Exception as e:
        print(f"[examen_aprobacion] escrito: {e}")

    # Parche examen multiple choice (si sigue activo)
    try:
        import examen_direccion as ed

        if hasattr(ed, "LogExamenView"):
            Orig = ed.LogExamenView

            class LogExamenView(Orig):
                @discord.ui.button(
                    label="Aprobar postulación",
                    style=discord.ButtonStyle.success,
                    emoji="✅",
                    custom_id="examen_dir:aprobar",
                )
                async def aprobar(self, inter: discord.Interaction, button: discord.ui.Button):
                    if not inter.guild or not isinstance(inter.user, discord.Member):
                        return await inter.response.send_message(
                            "❌ Solo en servidor.", ephemeral=True
                        )
                    if not ed._es_staff(inter.user):
                        return await inter.response.send_message(
                            "❌ Solo staff.", ephemeral=True
                        )

                    data = ed._load()
                    ses = data.get("sesiones", {}).get(self.session_id) or {}
                    pct = int(ses.get("pct") or self.pct or 0)
                    minimo = int(getattr(ed, "_MINIMO", 70) or 70)
                    if pct < minimo:
                        return await inter.response.send_message(
                            f"❌ Tiene **{pct}%** (mínimo {minimo}%). Debes **Rechazar**.",
                            ephemeral=True,
                        )

                    await inter.response.defer()
                    uid = int(ses.get("user_id") or self.user_id)
                    dir_n = ses.get("dir_nombre") or self.dir_nombre
                    member = inter.guild.get_member(uid)
                    if member:
                        # guardar dir_key en sesión si falta
                        await _enviar_felicitacion(
                            member,
                            session_id=self.session_id,
                            dir_nombre=dir_n,
                            aprobado_por=str(inter.user),
                        )

                    emb = (
                        inter.message.embeds[0].copy()
                        if inter.message and inter.message.embeds
                        else discord.Embed()
                    )
                    emb.color = 0x2ECC71
                    emb.title = f"✅ Aprobado · {dir_n}"
                    emb.description = (
                        (emb.description or "")
                        + f"\n\n**Aprobado por** {inter.user.mention}"
                    )
                    try:
                        await inter.edit_original_response(embed=emb, view=None)
                    except Exception:
                        try:
                            if inter.message:
                                await inter.message.edit(embed=emb, view=None)
                        except Exception:
                            pass

            ed.LogExamenView = LogExamenView
            try:
                bot.add_view(LogExamenView())
            except Exception:
                pass
    except Exception as e:
        print(f"[examen_aprobacion] mc: {e}")

    print("[examen_aprobacion] OK — felicitación + explicación de criterios")
