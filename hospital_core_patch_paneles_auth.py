# -*- coding: utf-8 -*-
"""Carga segura del sistema de paneles de autoridades."""
from __future__ import annotations


def registrar(bot) -> None:
    import sys

    for name in (
        "paneles_autoridades_config",
        "paneles_store",
        "paneles_permisos_auth",
        "roles_cofundadores",
        "paneles_autoridades_ui",
        "paneles_autoridades_loader",
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
                print(f"[paneles_auth_load] ✓ {name}")
            else:
                print(f"[paneles_auth_load] · {name}")
        except Exception as e:
            print(f"[paneles_auth_load] ✗ {name}: {e}")
