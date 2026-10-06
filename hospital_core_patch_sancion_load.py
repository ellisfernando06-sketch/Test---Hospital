# -*- coding: utf-8 -*-
"""Carga forzada de /sancion y chequeo apelable."""
from __future__ import annotations


def registrar(bot) -> None:
    for name in (
        "sancion_comando_unico",
        "sancion_apelable_check",
        "sanciones_comandos_hook",
        "sanciones_apelacion_ui",
    ):
        try:
            if name in __import__("sys").modules:
                del __import__("sys").modules[name]
        except Exception:
            pass
        try:
            mod = __import__(name)
            if hasattr(mod, "registrar"):
                mod.registrar(bot)
                print(f"[sancion_load] ✓ {name}")
        except Exception as e:
            print(f"[sancion_load] ✗ {name}: {e}")
