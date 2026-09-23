# -*- coding: utf-8 -*
"""centro_solicitudes_ui.py — bootstrap + apply patches from cs_ui_patches."""
from __future__ import annotations
import urllib.request
import sys

_GOOD = "a6e30cbaefe3ab422f1b108b42dbe5a6c83d1f92"
_URL = f"https://raw.githubusercontent.com/ellisfernando06-sketch/Test---Hospital/{_GOOD}/centro_solicitudes_ui.py"

def _bootstrap():
    print("[centro_solicitudes_ui] Descargando módulo completo…")
    with urllib.request.urlopen(_URL, timeout=45) as resp:
        source = resp.read().decode("utf-8")
    print(f"[centro_solicitudes_ui] Descargado ({len(source)} bytes)")
    mod = sys.modules[__name__]
    exec(compile(source, "centro_solicitudes_ui_remote.py", "exec"), mod.__dict__)
    print("[centro_solicitudes_ui] Módulo completo cargado")
    try:
        import cs_ui_patches
        cs_ui_patches.apply(mod)
        print("[centro_solicitudes_ui] Parches OK")
    except Exception as e:
        print("[centro_solicitudes_ui] Parches FALLARON:", e)
        import traceback
        traceback.print_exc()

_bootstrap()
