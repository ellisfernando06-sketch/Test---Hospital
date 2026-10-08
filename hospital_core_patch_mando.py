# -*- coding: utf-8 -*-
"""Carga segura: roles co-fundadores + paneles de mando."""
from __future__ import annotations


def registrar(bot) -> None:
    import sys

    for name in ("roles_cofundadores", "mando_store", "paneles_mando"):
        try:
            if name in sys.modules:
                del sys.modules[name]
        except Exception:
            pass
        try:
            mod = __import__(name)
            if hasattr(mod, "registrar"):
                mod.registrar(bot)
                print(f"[mando_load] ✓ {name}")
            else:
                print(f"[mando_load] · {name}")
        except Exception as e:
            print(f"[mando_load] ✗ {name}: {e}")
