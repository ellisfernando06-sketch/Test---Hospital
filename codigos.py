# -*- coding: utf-8 -*-
"""
codigos.py — Códigos de emergencia activos.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "codigos.json")


def _load() -> dict:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_PATH):
        return {"activos": []}
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("activos", [])
        return data
    except Exception:
        return {"activos": []}


def _save(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def activar(codigo: str, ubicacion: str, detalles: str, por: int) -> None:
    data = _load()
    data["activos"].append({
        "codigo": codigo,
        "ubicacion": ubicacion,
        "detalles": detalles,
        "por": por,
        "fecha": datetime.now(timezone.utc).isoformat(),
        "activo": True,
    })
    _save(data)


def cancelar_todos(codigo: str) -> int:
    data = _load()
    cerradas = 0
    for c in data["activos"]:
        if c.get("codigo") == codigo and c.get("activo"):
            c["activo"] = False
            c["cerrado"] = datetime.now(timezone.utc).isoformat()
            cerradas += 1
    _save(data)
    return cerradas


def activos() -> List[dict]:
    data = _load()
    return [c for c in data["activos"] if c.get("activo")]
