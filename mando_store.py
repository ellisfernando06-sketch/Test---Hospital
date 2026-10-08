# -*- coding: utf-8 -*-
"""Persistencia: auditoría, cola de aprobaciones, delegaciones, datos de paneles."""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

_DATA = Path(__file__).resolve().parent / "mando_data.json"


def _empty() -> dict:
    return {
        "auditoria": [],
        "cola_aprobaciones": [],
        "delegaciones": [],
        "politicas": [],
        "actas": [],
        "casos_etica": [],
        "convenios": [],
        "aliados": [],
        "campanas": [],
        "eventos_adversos": [],
        "planes_mejora": [],
        "acreditaciones": [],
        "emergencia": None,
        "prioridades": [],
        "objetivos": [],
    }


def load() -> dict:
    if not _DATA.exists():
        return _empty()
    try:
        data = json.loads(_DATA.read_text(encoding="utf-8"))
        base = _empty()
        base.update(data)
        return base
    except Exception:
        return _empty()


def save(data: dict) -> None:
    try:
        _DATA.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception as e:
        print(f"[mando_store] save: {e}")


def nuevo_id(prefijo: str = "M") -> str:
    return f"{prefijo}-{uuid.uuid4().hex[:8].upper()}"


def auditar(
    *,
    guild_id: int,
    actor_id: int,
    actor_name: str,
    rol: str,
    accion: str,
    afectado: str = "—",
    resultado: str = "ok",
    extra: Optional[dict] = None,
) -> dict:
    data = load()
    entry = {
        "id": nuevo_id("AUD"),
        "guild_id": guild_id,
        "ts": int(time.time()),
        "actor_id": actor_id,
        "actor_name": actor_name,
        "rol": rol,
        "accion": accion,
        "afectado": afectado,
        "resultado": resultado,
        "extra": extra or {},
    }
    data.setdefault("auditoria", []).insert(0, entry)
    data["auditoria"] = data["auditoria"][:500]
    save(data)
    return entry


def encolar_aprobacion(
    *,
    guild_id: int,
    origen_id: int,
    origen_zona: str,
    titulo: str,
    detalle: str,
    payload: Optional[dict] = None,
) -> dict:
    data = load()
    item = {
        "id": nuevo_id("APR"),
        "guild_id": guild_id,
        "ts": int(time.time()),
        "origen_id": origen_id,
        "origen_zona": origen_zona,
        "titulo": titulo,
        "detalle": detalle,
        "payload": payload or {},
        "estado": "pendiente",  # pendiente | aprobado | vetado | devuelto
    }
    data.setdefault("cola_aprobaciones", []).insert(0, item)
    save(data)
    return item


def listar_pendientes(guild_id: int, zona: Optional[str] = None) -> List[dict]:
    data = load()
    out = []
    for it in data.get("cola_aprobaciones") or []:
        if int(it.get("guild_id") or 0) != guild_id:
            continue
        if it.get("estado") != "pendiente":
            continue
        if zona and it.get("origen_zona") != zona:
            continue
        out.append(it)
    return out


def actualizar_pendiente(item_id: str, estado: str, comentario: str = "") -> Optional[dict]:
    data = load()
    for it in data.get("cola_aprobaciones") or []:
        if it.get("id") == item_id:
            it["estado"] = estado
            it["comentario"] = comentario
            it["resuelto_ts"] = int(time.time())
            save(data)
            return it
    return None


def delegacion_activa(guild_id: int, user_id: int, poder: str) -> bool:
    now = int(time.time())
    data = load()
    for d in data.get("delegaciones") or []:
        if int(d.get("guild_id") or 0) != guild_id:
            continue
        if int(d.get("user_id") or 0) != user_id:
            continue
        if d.get("revocada"):
            continue
        if int(d.get("vence_ts") or 0) < now:
            continue
        if poder and d.get("poder") != poder and d.get("poder") != "*":
            continue
        return True
    return False


def listar_delegaciones(guild_id: int, solo_activas: bool = True) -> List[dict]:
    now = int(time.time())
    data = load()
    out = []
    for d in data.get("delegaciones") or []:
        if int(d.get("guild_id") or 0) != guild_id:
            continue
        if solo_activas:
            if d.get("revocada") or int(d.get("vence_ts") or 0) < now:
                continue
        out.append(d)
    return out


def emergencia_activa(guild_id: int) -> Optional[dict]:
    data = load()
    em = data.get("emergencia")
    if em and int(em.get("guild_id") or 0) == guild_id and em.get("activa"):
        return em
    return None
