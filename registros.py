# -*- coding: utf-8 -*-
"""
registros.py — Expedientes, cargos, licencias, advertencias, asistencia.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "registros.json")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> dict:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_PATH):
        return {}
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _user(data: dict, uid: int) -> dict:
    key = str(uid)
    if key not in data:
        data[key] = {
            "cargos": [],
            "licencias": [],
            "advertencias": [],
            "asistencia": [],
        }
    return data[key]


def registrar_evento_cargo(uid: int, tipo: str, detalle: str, autor_id: int) -> None:
    data = _load()
    u = _user(data, uid)
    u["cargos"].append({
        "fecha": _now(),
        "tipo": tipo,
        "detalle": detalle,
        "autor_id": autor_id,
    })
    _save(data)


def registrar_licencia(uid: int, motivo: str, desde: str, hasta: str, autor_id: int) -> None:
    data = _load()
    u = _user(data, uid)
    u["licencias"].append({
        "fecha": _now(),
        "motivo": motivo,
        "desde": desde,
        "hasta": hasta,
        "autor_id": autor_id,
    })
    _save(data)


def registrar_advertencia(uid: int, motivo: str, autor_id: int) -> None:
    data = _load()
    u = _user(data, uid)
    u["advertencias"].append({
        "fecha": _now(),
        "motivo": motivo,
        "autor_id": autor_id,
    })
    _save(data)


def registrar_asistencia(uid: int, tipo: str, detalle: str = "") -> None:
    data = _load()
    u = _user(data, uid)
    u["asistencia"].append({
        "fecha": _now(),
        "tipo": tipo,
        "detalle": detalle,
    })
    _save(data)


def expediente_completo(uid: int) -> Dict[str, Any]:
    data = _load()
    return _user(data, uid)
