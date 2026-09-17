# -*- coding: utf-8 -*-
"""
pacientes.py — Fichas clínicas y admisiones.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "pacientes.json")


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


def _ficha(data: dict, uid: int) -> dict:
    key = str(uid)
    if key not in data:
        data[key] = {
            "admitido": False,
            "gravedad": None,
            "motivo": None,
            "area": None,
            "cama": None,
            "fecha_admision": None,
            "admitido_por": None,
            "notas": [],
            "historial": [],
        }
    return data[key]


def esta_admitido(uid: int) -> bool:
    data = _load()
    return bool(_ficha(data, uid).get("admitido"))


def admitir(uid: int, gravedad: str, motivo: str, por: int, cama: str = "", area: str = "") -> None:
    data = _load()
    f = _ficha(data, uid)
    f["admitido"] = True
    f["gravedad"] = gravedad
    f["motivo"] = motivo
    f["cama"] = cama or None
    f["area"] = area or None
    f["fecha_admision"] = _now()
    f["admitido_por"] = por
    _save(data)


def dar_alta(uid: int, resumen: str, por: int) -> None:
    data = _load()
    f = _ficha(data, uid)
    if f.get("admitido"):
        f["historial"].append({
            "fecha_admision": f.get("fecha_admision"),
            "fecha_alta": _now(),
            "motivo": f.get("motivo"),
            "gravedad": f.get("gravedad"),
            "resumen_alta": resumen,
            "alta_por": por,
        })
    f["admitido"] = False
    f["gravedad"] = None
    f["motivo"] = None
    f["area"] = None
    f["cama"] = None
    f["fecha_admision"] = None
    f["admitido_por"] = None
    _save(data)


def agregar_nota(uid: int, texto: str, por: int) -> None:
    data = _load()
    f = _ficha(data, uid)
    f["notas"].append({"fecha": _now(), "texto": texto, "autor_id": por})
    _save(data)


def cambiar_gravedad(uid: int, gravedad: str) -> None:
    data = _load()
    f = _ficha(data, uid)
    f["gravedad"] = gravedad
    _save(data)


def transferir_area(uid: int, area: str, cama: Optional[str] = None) -> None:
    data = _load()
    f = _ficha(data, uid)
    f["area"] = area
    if cama is not None:
        f["cama"] = cama
    _save(data)


def ficha_de(uid: int) -> Optional[dict]:
    data = _load()
    key = str(uid)
    return data.get(key)


def admitidos() -> List[Tuple[int, dict]]:
    data = _load()
    out = []
    for k, f in data.items():
        if f.get("admitido"):
            out.append((int(k), f))
    return out
