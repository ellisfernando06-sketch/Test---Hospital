# -*- coding: utf-8 -*-
"""centro_solicitudes.py — Bootstrap desde commit conocido."""
from __future__ import annotations
import urllib.request
import sys

_GOOD = "f20e635067a95dbf3a8b14139e2003e6ca455e7d"
_URL = f"https://raw.githubusercontent.com/ellisfernando06-sketch/Test---Hospital/{_GOOD}/centro_solicitudes.py"

def _bootstrap():
    print("[centro_solicitudes] Descargando módulo completo…")
    with urllib.request.urlopen(_URL, timeout=45) as resp:
        source = resp.read().decode("utf-8")
    print(f"[centro_solicitudes] Descargado ({len(source)} bytes)")
    mod = sys.modules[__name__]
    exec(compile(source, "centro_solicitudes_remote.py", "exec"), mod.__dict__)
    print("[centro_solicitudes] Módulo completo cargado")

_bootstrap()
