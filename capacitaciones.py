# -*- coding: utf-8 -*
"""
capacitaciones.py — Programación, postulaciones y certificaciones.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List, Optional

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "capacitaciones.json")


def _load() -> dict:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_PATH):
        return {"programadas": [], "completadas": [], "next_id": 1}
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("programadas", [])
        data.setdefault("completadas", [])
        data.setdefault("next_id", 1)
        return data
    except Exception:
        return {"programadas": [], "completadas": [], "next_id": 1}


def _save(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def programar(titulo: str, fecha_hora: str, departamento_slug: str, descripcion: str, por: int) -> int:
    data = _load()
    cid = data["next_id"]
    data["next_id"] = cid + 1
    data["programadas"].append({
        "id": cid,
        "titulo": titulo,
        "fecha_hora": fecha_hora,
        "departamento_slug": departamento_slug or "",
        "descripcion": descripcion,
        "por": por,
        "fecha": datetime.now(timezone.utc).isoformat(),
        "postulados": [],
    })
    _save(data)
    return cid


def obtener(cap_id: int) -> Optional[dict]:
    data = _load()
    for c in data["programadas"]:
        if int(c.get("id", 0)) == int(cap_id):
            c.setdefault("postulados", [])
            return c
    return None


def postular(cap_id: int, uid: int) -> tuple:
    """
    Postula a un usuario. Devuelve (ok: bool, mensaje: str).
    """
    data = _load()
    for c in data["programadas"]:
        if int(c.get("id", 0)) != int(cap_id):
            continue
        c.setdefault("postulados", [])
        if uid in c["postulados"]:
            return False, "Ya estás postulado a esta capacitación."
        c["postulados"].append(uid)
        _save(data)
        return True, f"Postulación registrada. Total: **{len(c['postulados'])}**."
    return False, "Capacitación no encontrada o ya no está programada."


def despostular(cap_id: int, uid: int) -> tuple:
    data = _load()
    for c in data["programadas"]:
        if int(c.get("id", 0)) != int(cap_id):
            continue
        c.setdefault("postulados", [])
        if uid not in c["postulados"]:
            return False, "No estabas postulado."
        c["postulados"] = [x for x in c["postulados"] if x != uid]
        _save(data)
        return True, "Postulación cancelada."
    return False, "Capacitación no encontrada."


def postulados_de(cap_id: int) -> List[int]:
    c = obtener(cap_id)
    if not c:
        return []
    return list(c.get("postulados") or [])


def certificar(uid: int, titulo: str, por: int) -> None:
    data = _load()
    data["completadas"].append({
        "uid": uid,
        "titulo": titulo,
        "por": por,
        "fecha": datetime.now(timezone.utc).isoformat(),
    })
    _save(data)


def completadas_de(uid: int) -> List[dict]:
    data = _load()
    return [c for c in data["completadas"] if c.get("uid") == uid]


def listar_programadas() -> List[dict]:
    data = _load()
    for c in data["programadas"]:
        c.setdefault("postulados", [])
    return data["programadas"]
