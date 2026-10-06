# -*- coding: utf-8 -*-
"""
Engancha comandos existentes SIN duplicar:
  /advertencia, /ooc_advertencia → solo tipo advertencia
  /sancion_interna (aprobada) → disciplinaria o administrativa
  /ooc_timeout, /ooc_kick, /ooc_ban → disciplinaria / ban

Un registro + un MD. No inunda log de apelaciones.
"""
from __future__ import annotations

import asyncio
import time
from typing import Optional, Set, Tuple

from discord.ext import commands

_bot: Optional[commands.Bot] = None
# Anti-duplicado: (uid, tipo, motivo_hash) recientes
_RECIENTES: Set[Tuple[int, str, str]] = set()
_RECIENTES_TS: dict = {}


def _permitido(tipo_evento: str) -> Optional[str]:
    """Devuelve tipo canónico o None si no debe registrarse."""
    t = (tipo_evento or "").lower().strip()
    if "advert" in t:
        return "advertencia"
    if "admin" in t or "administrativ" in t:
        return "administrativa"
    if t in ("sancion", "sanción", "sancion_interna") or "disciplin" in t:
        return "disciplinaria"
    if "ban" in t:
        return "ban"
    if "timeout" in t or "kick" in t:
        return "disciplinaria"
    # ooc genérico no-advertencia ya filtrado arriba
    if t.startswith("ooc_") and "advert" not in t:
        if "ban" in t:
            return "ban"
        return "disciplinaria"
    return None


def _dedupe(uid: int, tipo: str, motivo: str) -> bool:
    """True si es duplicado (ignorar)."""
    key = (int(uid), tipo, (motivo or "")[:80])
    now = time.time()
    # limpiar > 30s
    for k, ts in list(_RECIENTES_TS.items()):
        if now - ts > 30:
            _RECIENTES.discard(k)
            _RECIENTES_TS.pop(k, None)
    if key in _RECIENTES:
        return True
    _RECIENTES.add(key)
    _RECIENTES_TS[key] = now
    return False


async def _notificar_una(reg: dict) -> None:
    global _bot
    if _bot is None:
        return
    try:
        from sanciones_apelacion_ui import notificar_usuario
    except Exception as e:
        print(f"[sanciones_comandos_hook] notify import: {e}")
        return
    await asyncio.sleep(0.25)
    for g in _bot.guilds:
        try:
            if await notificar_usuario(_bot, g, reg):
                return
        except Exception:
            continue
    try:
        from sanciones_apelacion_ui import embed_dm_sancion, ApelarSancionView

        user = await _bot.fetch_user(int(reg.get("usuario_id") or 0))
        await user.send(
            embed=embed_dm_sancion(reg),
            view=ApelarSancionView(int(reg.get("id") or 0)),
        )
    except Exception:
        pass


def _registrar_una(
    uid: int, tipo: str, motivo: str, autor_id: int, duracion: str = ""
) -> Optional[dict]:
    if _dedupe(uid, tipo, motivo):
        print(f"[sanciones_comandos_hook] dup ignorado {tipo} uid={uid}")
        return None
    try:
        import sanciones as sanc
    except Exception:
        return None
    # Evitar que el wrap de registrar_sancion dispare otro MD
    flag = getattr(sanc, "_skip_notify", False)
    try:
        sanc._skip_notify = True  # type: ignore
        try:
            reg = sanc.registrar_sancion(
                uid, tipo, motivo, autor_id, duracion=duracion or ""
            )
        except TypeError:
            reg = sanc.registrar_sancion(uid, tipo, motivo, autor_id)
    except Exception as e:
        print(f"[sanciones_comandos_hook] registrar: {e}")
        return None
    finally:
        try:
            sanc._skip_notify = flag  # type: ignore
        except Exception:
            pass
    return reg


def _hook_registros() -> None:
    try:
        import registros
    except Exception as e:
        print(f"[sanciones_comandos_hook] sin registros: {e}")
        return

    if getattr(registros, "_sanciones_hook_v2", False):
        return

    _orig_adv = registros.registrar_advertencia
    _orig_ev = registros.registrar_evento_cargo

    def registrar_advertencia(uid: int, motivo: str, autor_id: int) -> None:
        _orig_adv(uid, motivo, autor_id)
        reg = _registrar_una(uid, "advertencia", motivo, autor_id)
        if reg is not None and _bot is not None:
            try:
                _bot.loop.create_task(_notificar_una(reg))
            except Exception as e:
                print(f"[sanciones_comandos_hook] task: {e}")

    def registrar_evento_cargo(
        uid: int, tipo: str, detalle: str, autor_id: int
    ) -> None:
        _orig_ev(uid, tipo, detalle, autor_id)
        mapped = _permitido(tipo)
        if mapped is None:
            return
        # No volver a registrar advertencias OOC aquí si ya pasaron por registrar_advertencia
        if mapped == "advertencia":
            return
        duracion = ""
        if "timeout" in (tipo or "").lower():
            duracion = (detalle or "").split(":")[0].strip()[:40]
        reg = _registrar_una(
            uid, mapped, detalle or tipo, autor_id, duracion=duracion
        )
        if reg is not None and _bot is not None:
            try:
                _bot.loop.create_task(_notificar_una(reg))
            except Exception as e:
                print(f"[sanciones_comandos_hook] task ev: {e}")

    registros.registrar_advertencia = registrar_advertencia  # type: ignore
    registros.registrar_evento_cargo = registrar_evento_cargo  # type: ignore
    registros._sanciones_hook_v2 = True  # type: ignore
    print("[sanciones_comandos_hook] v2 registros OK (sin duplicar)")


def _hook_abrir_apelacion() -> None:
    try:
        import sanciones as sanc
    except Exception:
        return
    if getattr(sanc, "_log_apelacion_hook_v2", False):
        return

    _orig = sanc.abrir_ticket_apelacion

    async def abrir_ticket_apelacion(guild, usuario, sancion, *a, **kw):
        canal = await _orig(guild, usuario, sancion, *a, **kw)
        # Un solo aviso al log (sin embeds extra en el ticket)
        try:
            from sanciones_apelacion_ui import enviar_log_apelacion

            if _bot is not None:
                await enviar_log_apelacion(_bot, guild, usuario, sancion, canal)
        except Exception as e:
            print(f"[sanciones_comandos_hook] log: {e}")
        return canal

    sanc.abrir_ticket_apelacion = abrir_ticket_apelacion  # type: ignore
    sanc._log_apelacion_hook_v2 = True  # type: ignore


def registrar(bot: commands.Bot) -> None:
    global _bot
    _bot = bot
    _hook_registros()
    _hook_abrir_apelacion()
    print(
        "[sanciones_comandos_hook] ACTIVO v2 — "
        "solo advertencia / disciplinaria / administrativa / ban · 1 MD"
    )
