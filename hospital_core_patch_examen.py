# -*- coding: utf-8 -*-
"""Carga forzada de examen_direccion."""
from __future__ import annotations


def registrar(bot) -> None:
    import sys

    name = "examen_direccion"
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
    except Exception as e:
        print(f"[examen_load] ✗ {name}: {e}")
