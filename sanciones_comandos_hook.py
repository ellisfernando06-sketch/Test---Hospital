# -*- coding: utf-8 -*-
"""
Engancha comandos viejos del núcleo a sanciones+MD.
NO duplica si /sancion (comando único) ya registró (_from_sancion_cmd).
"""
from __future__ import annotations

import asyncio
import time
from typing import Optional, Set, Tuple

from discord.ext import commands

_bot: Optional[commands.Bot] = None
_RECIENTES: Set[Tuple[int, str, str]] = set()
_RECIENTES_TS: dict = {}


def _permitido(tipo_evento: str) -> Optional[str]:
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
    if t.startswith("ooc_"):
        if "ban" in t:
            return "ban"
        if "advert" in t:
            return "advertencia"
        return "disciplinaria"
    return None


def _dedupe(uid: int, tipo: str, motivo: str) -> bool:
    key = (int(uid), tipo, (motivo or "")[:80])
    now = time.time()
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
    except Exception:
        return
    await asyncio.sleep(0.2)
    for g in _bot.guilds:
        try:
            if await notificar_usuario(_bot, g, reg):
                return
        except Exception:
            continue


def _registrar_una(
    uid: int, tipo: str, motivo: str, autor_id: int, duracion: str = ""
) -> Optional[dict]:
    if _dedupe(uid, tipo, motivo):
        return None
    try:
        import sanciones as sanc
    except Exception:
        return None
    try:
        sanc._skip_notify = True  # type: ignore
        try:
            reg = sanc.registrar_sancion(
                uid, tipo, motivo, autor_id, duracion=duracion or ""
            )
        except TypeError:
            reg = sanc.registrar_sancion(uid, tipo, motivo, autor_id)
        finally:
            sanc._skip_notify = False  # type: ignore
        # Por defecto apelable en comandos viejos
        try:
            data = sanc._load()
            for s in data.get("sanciones") or []:
                if int(s.get("id") or 0) == int(reg.get("id") or 0):
                    if "apelable" not in s:
                        s["apelable"] = True
                        reg["apelable"] = True
                    break
            sanc._save(data)
        except Exception:
            reg.setdefault("apelable", True)
        return reg
    except Exception as e:
        print(f"[sanciones_comandos_hook] registrar: {e}")
        return None


def _hook_registros() -> None:
    try:
        import registros
    except Exception:
        return

    # Re-hook siempre (v3)
    _orig_adv = getattr(
        registros, "_orig_adv_v3", registros.registrar_advertencia
    )
    _orig_ev = getattr(
        registros, "_orig_ev_v3", registros.registrar_evento_cargo
    )
    if not hasattr(registros, "_orig_adv_v3"):
        registros._orig_adv_v3 = registros.registrar_advertencia  # type: ignore
        registros._orig_ev_v3 = registros.registrar_evento_cargo  # type: ignore
        _orig_adv = registros._orig_adv_v3
        _orig_ev = registros._orig_ev_v3

    def registrar_advertencia(uid: int, motivo: str, autor_id: int) -> None:
        _orig_adv(uid, motivo, autor_id)
        # Si viene de /sancion, no registrar de nuevo
        if getattr(registros, "_from_sancion_cmd", False):
            return
        reg = _registrar_una(uid, "advertencia", motivo, autor_id)
        if reg is not None and _bot is not None:
            try:
                _bot.loop.create_task(_notificar_una(reg))
            except Exception:
                pass

    def registrar_evento_cargo(
        uid: int, tipo: str, detalle: str, autor_id: int
    ) -> None:
        _orig_ev(uid, tipo, detalle, autor_id)
        if getattr(registros, "_from_sancion_cmd", False):
            return
        mapped = _permitido(tipo)
        if mapped is None or mapped == "advertencia":
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
            except Exception:
                pass

    registros.registrar_advertencia = registrar_advertencia  # type: ignore
    registros.registrar_evento_cargo = registrar_evento_cargo  # type: ignore
    print("[sanciones_comandos_hook] v3 sin duplicar con /sancion")


def _hook_abrir_apelacion() -> None:
    # El ticket limpio lo hace sancion_fix_doble; no envolver de nuevo el log aquí
    pass


def registrar(bot: commands.Bot) -> None:
    global _bot
    _bot = bot
    _hook_registros()
    print(
        "[sanciones_comandos_hook] ACTIVO v3 — sin doble con /sancion"
    )
