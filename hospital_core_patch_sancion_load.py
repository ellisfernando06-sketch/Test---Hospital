# -*- coding: utf-8 -*-
"""Carga forzada: /sancion, apelable y fix doble MD / sin entrevista."""
from __future__ import annotations


def registrar(bot) -> None:
    import sys

    for name in (
        "sanciones_apelacion_ui",
        "sanciones_comandos_hook",
        "sancion_comando_unico",
        "sancion_apelable_check",
        "sancion_fix_doble",  # último: 1 MD, log sin entrevista, ticket limpio
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
                print(f"[sancion_load] ✓ {name}")
        except Exception as e:
            print(f"[sancion_load] ✗ {name}: {e}")
