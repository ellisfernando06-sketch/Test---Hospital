# -*- coding: utf-8 -*-
"""bot_control.py — bootstrap desde main; OWNER se resuelve a FUNDADOR_OWNER vía permisos._ALIAS_KEYS."""
from __future__ import annotations
import urllib.request
import sys

_URL = "https://raw.githubusercontent.com/ellisfernando06-sketch/Test---Hospital/main/bot_control.py"

def _bootstrap():
    print("[bot_control] Descargando módulo desde main…")
    with urllib.request.urlopen(_URL, timeout=45) as resp:
        source = resp.read().decode("utf-8")
    # Mapear OWNER a FUNDADOR_OWNER en el código cargado (permisos ya tiene alias, pero unificamos)
    source = source.replace('"OWNER"', '"FUNDADOR_OWNER"')
    # No tocar CO_OWNER (ya es correcto)
    source = source.replace('"FUNDADOR_OWNER_CO"', '"CO_OWNER"')  # safety no-op
    mod = sys.modules[__name__]
    exec(compile(source, "bot_control_remote.py", "exec"), mod.__dict__)
    print("[bot_control] Módulo cargado (keys organigrama)")

_bootstrap()
