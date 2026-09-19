# -*- coding: utf-8 -*-
"""
inventario.py — Stock de insumos.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "inventario.json")


def _load() -> dict:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_PATH):
        return {"items": {}}
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("items", {})
        return data
    except Exception:
        return {"items": {}}


def _save(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _norm(nombre: str) -> str:
    return nombre.strip().lower()


def agregar_stock(item: str, cantidad: int, categoria: str = "", por: int = 0) -> int:
    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor a 0.")
    data = _load()
    key = _norm(item)
    if key not in data["items"]:
        data["items"][key] = {
            "nombre": item.strip(),
            "cantidad": 0,
            "minimo": 0,
            "categoria": categoria or "General",
            "historial": [],
        }
    it = data["items"][key]
    it["cantidad"] += cantidad
    if categoria:
        it["categoria"] = categoria
    it["historial"].append({
        "fecha": datetime.now(timezone.utc).isoformat(),
        "tipo": "entrada",
        "cantidad": cantidad,
        "por": por,
    })
    _save(data)
    return it["cantidad"]


def retirar_stock(item: str, cantidad: int, por: int = 0, motivo: str = "") -> int:
    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor a 0.")
    data = _load()
    key = _norm(item)
    if key not in data["items"]:
        raise LookupError(f"No existe el ítem '{item}'.")
    it = data["items"][key]
    if it["cantidad"] < cantidad:
        raise ValueError(f"Stock insuficiente de '{it['nombre']}' (disponible: {it['cantidad']}).")
    it["cantidad"] -= cantidad
    it["historial"].append({
        "fecha": datetime.now(timezone.utc).isoformat(),
        "tipo": "salida",
        "cantidad": cantidad,
        "por": por,
        "motivo": motivo,
    })
    _save(data)
    return it["cantidad"]


def set_minimo(item: str, minimo: int) -> None:
    data = _load()
    key = _norm(item)
    if key not in data["items"]:
        raise LookupError(f"No existe el ítem '{item}'.")
    data["items"][key]["minimo"] = max(0, minimo)
    _save(data)


def obtener_item(item: str) -> Optional[dict]:
    data = _load()
    return data["items"].get(_norm(item))


def todos_los_items() -> List[dict]:
    data = _load()
    return list(data["items"].values())
