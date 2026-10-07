# -*- coding: utf-8 -*-
"""Carga examen_direccion + banco 20 preguntas RP."""
from __future__ import annotations


def registrar(bot) -> None:
    import sys

    for name in (
        "examen_direccion_preguntas",
        "examen_direccion",
        "examen_direccion_20",
    ):
        try:
            if name in sys.modules:
                del sys.modules[name]
        except Exception:
            pass
        try:
            mod = __import__(name)
            if hasattr(mod, "registrar"):
                mod.registrar(bot)
                print(f"[examen_load] ✓ {name}")
            else:
                print(f"[examen_load] · {name} (datos)")
        except Exception as e:
            print(f"[examen_load] ✗ {name}: {e}")
