# -*- coding: utf-8 -*-
"""
turnos.py — Turnos programados y en servicio.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "turnos.json")


def _load() -> dict:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_PATH):
        return {"programados": [], "en_servicio": {}, "next_id": 1}
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("programados", [])
        data.setdefault("en_servicio", {})
        data.setdefault("next_id", 1)
        return data
    except Exception:
        return {"programados": [], "en_servicio": {}, "next_id": 1}


def _save(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def asignar_turno(uid: int, dia: str, hora_inicio: str, hora_fin: str, area: str, por: int) -> int:
    data = _load()
    tid = data["next_id"]
    data["next_id"] = tid + 1
    data["programados"].append({
        "id": tid,
        "uid": uid,
        "dia": dia,
        "hora_inicio": hora_inicio,
        "hora_fin": hora_fin,
        "area": area or None,
        "asignado_por": por,
        "fecha": datetime.now(timezone.utc).isoformat(),
    })
    _save(data)
    return tid


def marcar_entrada(uid: int, area: str = "") -> bool:
    data = _load()
    key = str(uid)
    if key in data["en_servicio"]:
        return False
    data["en_servicio"][key] = {
        "entrada": datetime.now(timezone.utc).isoformat(),
        "area": area or None,
    }
    _save(data)
    return True


def marcar_salida(uid: int) -> Optional[dict]:
    data = _load()
    key = str(uid)
    reg = data["en_servicio"].pop(key, None)
    if reg:
        reg["salida"] = datetime.now(timezone.utc).isoformat()
        _save(data)
    return reg


def en_servicio_lista() -> List[Tuple[int, dict]]:
    data = _load()
    return [(int(k), v) for k, v in data["en_servicio"].items()]


def turnos_de(uid: int) -> List[dict]:
    data = _load()
    return [t for t in data["programados"] if t.get("uid") == uid]
