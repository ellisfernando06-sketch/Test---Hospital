# -*- coding: utf-8 -*-
"""
logs_store.py — Persistencia de canales de log/evaluación por tipo.
Se actualiza al publicar paneles con el parámetro canal_logs.
"""
from __future__ import annotations

import json
import os
from typing import Dict, Optional

import config

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "canales_logs.json")

TIPOS_LOG = (
    "log_solicitudes",
    "log_postulaciones",
    "log_quejas",
    "log_sanciones",
    "log_investigaciones",
    "aprobaciones_rrhh",
    "aprobaciones",
    "log_personal",
    "log_general",
    "staff_disciplina",
)


def _ensure() -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)


def _load() -> dict:
    _ensure()
    if not os.path.isfile(_PATH):
        return {}
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save(data: dict) -> None:
    _ensure()
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def set_canal(tipo: str, channel_id: int) -> None:
    data = _load()
    data[str(tipo)] = int(channel_id)
    _save(data)
    if isinstance(getattr(config, "CANALES", None), dict):
        config.CANALES[str(tipo)] = int(channel_id)


def get_canal_id(tipo: str) -> Optional[int]:
    data = _load()
    cid = data.get(str(tipo))
    if cid:
        return int(cid)
    canales = getattr(config, "CANALES", None) or {}
    if isinstance(canales, dict):
        v = canales.get(tipo)
        return int(v) if v else None
    return None


def todos() -> Dict[str, int]:
    data = _load()
    out = {k: int(v) for k, v in data.items() if v}
    canales = getattr(config, "CANALES", None) or {}
    if isinstance(canales, dict):
        for k, v in canales.items():
            if v and k not in out:
                out[k] = int(v)
    return out
