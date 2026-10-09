# -*- coding: utf-8 -*-
"""Persistencia no destructiva del sistema de autoridades."""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

_DATA = Path(__file__).resolve().parent / "paneles_autoridades_data.json"


def _empty() -> dict:
    return {
        "canales": {},  # guild_id -> {nombre: channel_id}
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
        "objetivos": [],
        "prioridades": [],
        "emergencia": {},  # guild_id -> dict
        "enlaces": [],
    }


def load() -> dict:
    if not _DATA.exists():
        return _empty()
    try:
        d = json.loads(_DATA.read_text(encoding="utf-8"))
        base = _empty()
        for k, v in d.items():
            base[k] = v
        return base
    except Exception:
        return _empty()


def save(data: dict) -> None:
    try:
        _DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[paneles_store] {e}")


def nid(pref: str = "P") -> str:
    return f"{pref}-{uuid.uuid4().hex[:8].upper()}"


def auditar(
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
    e = {
        "id": nid("AUD"),
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
    data.setdefault("auditoria", []).insert(0, e)
    data["auditoria"] = data["auditoria"][:800]
    save(data)
    return e


def encolar(
    guild_id: int,
    origen_id: int,
    zona: str,
    titulo: str,
    detalle: str,
    payload: Optional[dict] = None,
) -> dict:
    data = load()
    item = {
        "id": nid("APR"),
        "guild_id": guild_id,
        "ts": int(time.time()),
        "origen_id": origen_id,
        "zona": zona,
        "titulo": titulo,
        "detalle": detalle,
        "payload": payload or {},
        "estado": "pendiente",
    }
    data.setdefault("cola_aprobaciones", []).insert(0, item)
    save(data)
    return item


def pendientes(guild_id: int, zona: Optional[str] = None) -> List[dict]:
    out = []
    for it in load().get("cola_aprobaciones") or []:
        if int(it.get("guild_id") or 0) != guild_id:
            continue
        if it.get("estado") != "pendiente":
            continue
        if zona and it.get("zona") != zona:
            continue
        out.append(it)
    return out


def resolver_pendiente(item_id: str, estado: str, comentario: str = "") -> Optional[dict]:
    data = load()
    for it in data.get("cola_aprobaciones") or []:
        if it.get("id") == item_id:
            it["estado"] = estado
            it["comentario"] = comentario
            it["resuelto_ts"] = int(time.time())
            save(data)
            return it
    return None


def delegaciones_activas(guild_id: int, user_id: Optional[int] = None) -> List[dict]:
    now = int(time.time())
    out = []
    for d in load().get("delegaciones") or []:
        if int(d.get("guild_id") or 0) != guild_id:
            continue
        if d.get("revocada"):
            continue
        if int(d.get("vence_ts") or 0) < now:
            continue
        if user_id is not None and int(d.get("user_id") or 0) != user_id:
            continue
        out.append(d)
    return out


def tiene_delegacion(guild_id: int, user_id: int, poder: str = "*") -> bool:
    for d in delegaciones_activas(guild_id, user_id):
        if poder == "*" or d.get("poder") in (poder, "*", "general"):
            return True
    return False


def emergencia(guild_id: int) -> Optional[dict]:
    em = (load().get("emergencia") or {}).get(str(guild_id))
    if em and em.get("activa"):
        return em
    return None


def set_canal(guild_id: int, key: str, channel_id: int) -> None:
    data = load()
    data.setdefault("canales", {}).setdefault(str(guild_id), {})[key] = channel_id
    save(data)


def get_canal(guild_id: int, key: str) -> Optional[int]:
    return (load().get("canales") or {}).get(str(guild_id), {}).get(key)


def add_item(bucket: str, guild_id: int, autor_id: int, **fields) -> dict:
    data = load()
    entry = {
        "id": nid(bucket[:3].upper()),
        "guild_id": guild_id,
        "ts": int(time.time()),
        "autor_id": autor_id,
        "estado": fields.pop("estado", "activo"),
        **fields,
    }
    data.setdefault(bucket, []).insert(0, entry)
    save(data)
    return entry


def list_items(bucket: str, guild_id: int, estado: Optional[str] = None, limit: int = 25) -> List[dict]:
    items = [
        x
        for x in (load().get(bucket) or [])
        if int(x.get("guild_id") or 0) == guild_id
        and (estado is None or x.get("estado") == estado)
    ]
    return items[:limit]
