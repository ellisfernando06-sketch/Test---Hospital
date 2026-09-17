# -*- coding: utf-8 -*-
"""
ficha_personal.py — Campos administrativos de personal.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict

import config

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "ficha_personal.json")


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


def set_campo(uid: int, campo: str, valor: str) -> None:
    data = _load()
    key = str(uid)
    if key not in data:
        data[key] = {k: "" for k in config.FICHA_CAMPOS}
    data[key][campo] = valor
    _save(data)


def obtener(uid: int) -> Dict[str, Any]:
    data = _load()
    key = str(uid)
    base = {k: "" for k in config.FICHA_CAMPOS}
    base.update(data.get(key, {}))
    return base
