# -*- coding: utf-8 -*-
"""Banco difícil 20 preguntas/dirección — opciones casi iguales."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

_DIR = Path(__file__).resolve().parent


def _load() -> Dict[str, List[Tuple[str, List[str], int]]]:
    out: Dict[str, List[Tuple[str, List[str], int]]] = {}
    for i in range(3):
        p = _DIR / f"examen_banco_{i}.json"
        if not p.exists():
            continue
        raw = json.loads(p.read_text(encoding="utf-8"))
        for k, items in raw.items():
            out[k] = [(it["q"], list(it["opts"]), int(it["i"])) for it in items]
    return out


BANCO = _load()
