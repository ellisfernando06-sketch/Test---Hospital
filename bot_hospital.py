# -*- coding: utf-8 -*
"""Entrada del bot (Railway/Linux: nombre en minúsculas)."""
from pathlib import Path
import runpy
import sys
import os

os.chdir(Path(__file__).resolve().parent)

candidates = [
    Path("Bot_Hospital.py"),
    Path("bot_Hospital.py"),
    Path("Bot_hospital.py"),
]

target = next((p for p in candidates if p.is_file()), None)
if target is None:
    print("ERROR: No se encontro Bot_Hospital.py en el repo.", file=sys.stderr)
    print("Archivos:", sorted(p.name for p in Path('.').glob('*.py')), file=sys.stderr)
    raise SystemExit(1)

print(f"Iniciando bot desde: {target.resolve()}")
runpy.run_path(str(target), run_name="__main__")
