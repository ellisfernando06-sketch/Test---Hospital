# -*- coding: utf-8 -*-
"""Carga examen + permisos + nombres autoridades."""
from __future__ import annotations


def registrar(bot) -> None:
    import sys

    for name in (
        "roles_nombres_autoridades",
        "examen_preguntas_a",
        "examen_preguntas_b",
        "examen_direccion_preguntas",
        "examen_direccion",
        "examen_direccion_20",
        "examen_direccion_escrito",
        "examen_aprobacion_msg",
        "examen_aprobacion_hook",
        "examen_permisos_restringidos",
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
                print(f"[examen_load] · {name}")
        except Exception as e:
            print(f"[examen_load] ✗ {name}: {e}")
