# -*- coding: utf-8 -*-
"""
roles_store.py — Persistencia de IDs de roles (keys, escalafones, extras).
No crea roles: solo guarda y recupera IDs detectados por nombre.
"""
from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "roles.json")

_default = {
    "keys": {},          # key -> role_id
    "escalafones": {},   # slug -> [role_id, ...]
    "extras": {},        # nombre -> role_id  (ej. SUSPENDIDO)
}


def _ensure_dir():
    os.makedirs(_DATA_DIR, exist_ok=True)


def _load() -> dict:
    _ensure_dir()
    if not os.path.isfile(_PATH):
        return json.loads(json.dumps(_default))
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in _default:
            data.setdefault(k, {})
        return data
    except Exception:
        return json.loads(json.dumps(_default))


def _save(data: dict) -> None:
    _ensure_dir()
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def guardar_key(key: str, role_id: int) -> None:
    data = _load()
    data["keys"][key] = int(role_id)
    _save(data)


def obtener_id_key(key: str) -> Optional[int]:
    data = _load()
    rid = data["keys"].get(key)
    return int(rid) if rid is not None else None


def guardar_escalafon(slug: str, role_ids: List[Optional[int]]) -> None:
    data = _load()
    data["escalafones"][slug] = [int(r) if r else None for r in role_ids]
    _save(data)


def escalafon_ids(slug: str, cantidad: int) -> List[Optional[int]]:
    data = _load()
    ids = data["escalafones"].get(slug, [])
    # Normalizar longitud
    while len(ids) < cantidad:
        ids.append(None)
    return [int(x) if x else None for x in ids[:cantidad]]


def guardar_extra(nombre: str, role_id: int) -> None:
    data = _load()
    data["extras"][nombre] = int(role_id)
    _save(data)


def obtener_extra(nombre: str) -> Optional[int]:
    data = _load()
    rid = data["extras"].get(nombre)
    return int(rid) if rid is not None else None


def todas_las_keys() -> Dict[str, int]:
    data = _load()
    return {k: int(v) for k, v in data["keys"].items() if v}
