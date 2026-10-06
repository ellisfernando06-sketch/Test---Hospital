# -*- coding: utf-8 -*-
"""
Engancha los comandos YA existentes del núcleo:
  /advertencia, /ooc_advertencia, /sancion_interna (al aprobar),
  /ooc_timeout, /ooc_kick, /ooc_ban
con el sistema de sanciones + MD (motivo + Apelar) + log apelaciones + entrevista.

No reemplaza esos comandos: intercepta registros.* y sanciones.abrir_ticket_apelacion.
"""
from __future__ import annotations

import asyncio
from typing import Any, Optional

import discord
from discord.ext import commands

_bot: Optional[commands.Bot] = None


def _map_tipo(evento: str) -> str:
    e = (evento or "").lower()
    if "advert" in e:
        return "advertencia"
    if "ban" in e:
        return "ban"
    if "timeout" in e or "kick" in e:
        return "sancion"
    if e in ("sancion", "sanción", "sancion_interna"):
        return "sancion"
    return "sancion"


async def _notificar_reg(reg: dict) -> None:
    """Usa notificar_usuario de sanciones_apelacion_ui si está."""
    global _bot
    if _bot is None:
        return
    try:
        from sanciones_apelacion_ui import notificar_usuario
    except Exception as e:
        print(f"[sanciones_comandos_hook] import notify: {e}")
        return
    await asyncio.sleep(0.3)
    for g in _bot.guilds:
        try:
            if await notificar_usuario(_bot, g, reg):
                return
        except Exception as e:
            print(f"[sanciones_comandos_hook] notify guild: {e}")
    # Usuario baneado: intentar MD por fetch_user
    try:
        from sanciones_apelacion_ui import embed_dm_sancion, ApelarSancionView

        uid = int(reg.get("usuario_id") or 0)
        user = await _bot.fetch_user(uid)
        await user.send(
            embed=embed_dm_sancion(reg),
            view=ApelarSancionView(int(reg.get("id") or 0)),
        )
    except Exception:
        pass


def _registrar_en_sanciones(
    uid: int, tipo: str, motivo: str, autor_id: int, duracion: str = ""
) -> Optional[dict]:
    try:
        import sanciones as sanc
    except Exception:
        return None
    try:
        return sanc.registrar_sancion(
            uid, tipo, motivo, autor_id, duracion=duracion or ""
        )
    except TypeError:
        return sanc.registrar_sancion(uid, tipo, motivo, autor_id)
    except Exception as e:
        print(f"[sanciones_comandos_hook] registrar: {e}")
        return None


def _hook_registros() -> None:
    try:
        import registros
    except Exception as e:
        print(f"[sanciones_comandos_hook] sin registros: {e}")
        return

    if getattr(registros, "_sanciones_hook", False):
        return

    _orig_adv = registros.registrar_advertencia
    _orig_ev = registros.registrar_evento_cargo

    def registrar_advertencia(uid: int, motivo: str, autor_id: int) -> None:
        _orig_adv(uid, motivo, autor_id)
        reg = _registrar_en_sanciones(uid, "advertencia", motivo, autor_id)
        if reg is not None and _bot is not None:
            try:
                _bot.loop.create_task(_notificar_reg(reg))
            except Exception as e:
                print(f"[sanciones_comandos_hook] task adv: {e}")

    def registrar_evento_cargo(
        uid: int, tipo: str, detalle: str, autor_id: int
    ) -> None:
        _orig_ev(uid, tipo, detalle, autor_id)
        t = (tipo or "").lower()
        # Solo medidas disciplinarias
        if t not in (
            "sancion",
            "sanción",
            "ooc_ban",
            "ooc_timeout",
            "ooc_kick",
            "ooc_advertencia",
        ) and "sancion" not in t and "ban" not in t:
            return
        mapped = _map_tipo(t)
        duracion = ""
        if "timeout" in t and "min" in (detalle or "").lower():
            duracion = (detalle or "").split(":")[0].strip()
        reg = _registrar_en_sanciones(
            uid, mapped, detalle or tipo, autor_id, duracion=duracion
        )
        if reg is not None and _bot is not None:
            try:
                _bot.loop.create_task(_notificar_reg(reg))
            except Exception as e:
                print(f"[sanciones_comandos_hook] task evento: {e}")

    registros.registrar_advertencia = registrar_advertencia  # type: ignore
    registros.registrar_evento_cargo = registrar_evento_cargo  # type: ignore
    registros._sanciones_hook = True  # type: ignore
    print("[sanciones_comandos_hook] registros.registrar_* enganchados")


def _hook_abrir_apelacion() -> None:
    """Tras abrir ticket de apelación → log + botones entrevista."""
    try:
        import sanciones as sanc
    except Exception:
        return
    if getattr(sanc, "_log_apelacion_hook", False):
        return

    _orig = sanc.abrir_ticket_apelacion

    async def abrir_ticket_apelacion(guild, usuario, sancion, *a, **kw):
        canal = await _orig(guild, usuario, sancion, *a, **kw)
        try:
            from sanciones_apelacion_ui import enviar_log_apelacion

            if _bot is not None:
                await enviar_log_apelacion(_bot, guild, usuario, sancion, canal)
        except Exception as e:
            print(f"[sanciones_comandos_hook] log apelacion: {e}")
        return canal

    sanc.abrir_ticket_apelacion = abrir_ticket_apelacion  # type: ignore
    sanc._log_apelacion_hook = True  # type: ignore
    print("[sanciones_comandos_hook] abrir_ticket_apelacion enganchado")


def _asegurar_apelar_sancion(bot: commands.Bot) -> None:
    """Si no existe /apelar_sancion en el árbol, no inventamos lógica nueva:
    el panel y el botón del MD ya llaman a abrir_ticket_apelacion.
    Si el núcleo lo define más tarde, el hook de abrir_ticket sigue activo.
    """
    names = {c.name for c in bot.tree.get_commands()}
    if "apelar_sancion" in names:
        print("[sanciones_comandos_hook] /apelar_sancion ya en el árbol")
        return
    # No duplicamos: Apelar del MD + panel_apelaciones + ticket tipo Apelación
    print(
        "[sanciones_comandos_hook] sin /apelar_sancion en núcleo — "
        "usar botón MD / panel_apelaciones / ticket Apelación"
    )


def registrar(bot: commands.Bot) -> None:
    global _bot
    _bot = bot
    _hook_registros()
    _hook_abrir_apelacion()
    _asegurar_apelar_sancion(bot)

    # Ban → cuarentena si el miembro sigue en el guild (antes del ban real a veces no)
    # ooc_ban banea primero; el hook de evento ya registra tipo ban + intenta MD

    print(
        "[sanciones_comandos_hook] ACTIVO — "
        "/advertencia /ooc_* /sancion_interna(aprobada) → sanciones+MD+Apelar"
    )
