# -*- coding: utf-8 -*-
"""Al terminar el examen → rol Cuarentena. Al aprobar → se quita."""
from __future__ import annotations

from typing import Optional

import discord

_NOMBRES = ("⏳ Cuarentena", "Cuarentena", "cuarentena", "Quarantine")


async def rol_cuarentena(guild: discord.Guild) -> Optional[discord.Role]:
    for r in guild.roles:
        rn = (r.name or "").lower()
        if "cuarentena" in rn or "quarantine" in rn:
            return r
    try:
        return await guild.create_role(
            name="⏳ Cuarentena",
            colour=discord.Colour.dark_grey(),
            hoist=True,
            mentionable=False,
            reason="Verificación hospitalaria",
        )
    except Exception:
        return None


async def poner(member: discord.Member) -> None:
    rol = await rol_cuarentena(member.guild)
    if rol and rol not in member.roles:
        try:
            await member.add_roles(rol, reason="Examen enviado — espera staff")
        except Exception as e:
            print(f"[cuarentena] add: {e}")


async def quitar(member: discord.Member) -> None:
    for r in list(member.roles):
        rn = (r.name or "").lower()
        if "cuarentena" in rn or "quarantine" in rn:
            try:
                await member.remove_roles(r, reason="Verificación resuelta")
            except Exception:
                pass


def registrar(bot) -> None:
    try:
        import verificacion as ver
    except Exception as e:
        print(f"[verificacion_cuarentena] no ver: {e}")
        return

    cls = getattr(ver, "ExamenView", None)
    if cls is None:
        return

    # Encontrar método que finaliza (nombre puede variar)
    finish_name = None
    for name in ("_finalizar", "_finish", "_enviar_a_staff", "_terminar"):
        if hasattr(cls, name):
            finish_name = name
            break

    # Parche via _on_answer: cuando idx llega al final
    if hasattr(cls, "_on_answer"):
        _orig = cls._on_answer

        async def _on_answer_wrapped(self, interaction, *args, **kwargs):
            await _orig(self, interaction, *args, **kwargs)
            # Si ya no hay más preguntas, cuarentena
            try:
                if getattr(self, "idx", 0) >= len(getattr(ver, "PREGUNTAS", []) or []):
                    guild = interaction.client.get_guild(self.guild_id)
                    if guild:
                        member = guild.get_member(self.user_id)
                        if member:
                            await poner(member)
                            try:
                                await member.send(
                                    embed=discord.Embed(
                                        title="⏳ Modo cuarentena",
                                        description=(
                                            "Tu examen fue enviado.\n"
                                            "Estás en **cuarentena** hasta que el staff "
                                            "**apruebe** o **niegue** tu entrada al servidor."
                                        ),
                                        color=0x95A5A6,
                                    )
                                )
                            except Exception:
                                pass
            except Exception as e:
                print(f"[cuarentena] wrap: {e}")

        cls._on_answer = _on_answer_wrapped

    # Aprobar / Negar: quitar cuarentena
    staff_cls = getattr(ver, "StaffDecisionView", None)
    if staff_cls is not None:
        for method_name in list(dir(staff_cls)):
            pass
        # Parche botones por callback names comunes
        for attr in ("aprobar", "negar", "approve", "deny"):
            if hasattr(staff_cls, attr):
                pass

        # Hook interaction on children after init — patch class methods if exist
        if hasattr(staff_cls, "interaction_check"):
            pass

        # Wrap approve/deny by scanning Button callbacks in __init__ is hard;
        # instead patch a known method from source: look for async methods
        for name, fn in list(vars(staff_cls).items()):
            if not callable(fn) or name.startswith("_"):
                continue

    # Patch via StaffDecisionView custom: add listener on bot for button ids
    # Simpler: wrap verificacion StaffDecisionView callbacks after module load
    try:
        # Re-read approve flow from verificacion — methods are nested in buttons
        # Use bot event on_interaction for custom_id containing approve
        @bot.listen("on_interaction")
        async def _cuarentena_on_decision(inter: discord.Interaction):
            if inter.type != discord.InteractionType.component:
                return
            data = getattr(inter, "data", None) or {}
            cid = str(data.get("custom_id") or "")
            if not any(x in cid.lower() for x in ("aprob", "approv", "negar", "deny", "staff")):
                return
            if not inter.guild or not isinstance(inter.user, discord.Member):
                return
            # Tras decisión staff, intentar quitar cuarentena del target en embed footer exam
            # Best effort: quitar de member mencionado en message
            try:
                msg = inter.message
                if not msg or not msg.embeds:
                    return
                emb = msg.embeds[0]
                # buscar mention en description
                import re

                m = re.search(r"<@!?(\d+)>" , emb.description or "")
                if not m:
                    return
                member = inter.guild.get_member(int(m.group(1)))
                if member and any(
                    x in cid.lower() for x in ("aprob", "approv", "negar", "deny")
                ):
                    await quitar(member)
            except Exception:
                pass

    except Exception as e:
        print(f"[cuarentena] listener: {e}")

    print("[verificacion_cuarentena] OK")
