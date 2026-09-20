# -*- coding: utf-8 -*-
"""
Punto de entrada del bot.
Railway / Linux distinguen mayúsculas: debe existir bot_hospital.py.
Si el código está en Bot_Hospital.py (subido con mayúsculas), lo carga igual.
"""
from pathlib import Path
import runpy
import sys

_HERE = Path(__file__).resolve().parent

# Preferir este mismo archivo si tiene el bot completo; si no, cargar variantes
_candidates = [
    _HERE / "Bot_Hospital.py",   # nombre que a veces se sube desde Windows
    _HERE / "bot_Hospital.py",
    _HERE / "Bot_hospital.py",
]

# Si este archivo solo es el launcher (menos de ~5 KB de lógica), delegar
_self = Path(__file__).read_text(encoding="utf-8", errors="replace")
_is_launcher_only = "commands.Bot" not in _self and "bot.run" not in _self

if _is_launcher_only:
    target = None
    for p in _candidates:
        if p.is_file():
            target = p
            break
    if target is None:
        sys.stderr.write(
            "ERROR: No se encontró el código del bot.\n"
            "Sube el archivo como bot_hospital.py (todo en minúsculas).\n"
        )
        raise SystemExit(1)
    runpy.run_path(str(target), run_name="__main__")
else:
    # Este archivo YA es el bot completo (no debería llegar aquí en el launcher)
    pass
