# -*- coding: utf-8 -*-
"""roles_setup_restore.py — reconstruye roles_setup.py al arrancar."""
from __future__ import annotations
import pathlib, sys

def _go():
    parts = []
    for i in range(4):
        mod = __import__(f"rs_data_{i}")
        parts.append(mod.PART)
        del sys.modules[f"rs_data_{i}"]
    text = "".join(parts)
    target = pathlib.Path(__file__).with_name("roles_setup.py")
    target.write_text(text, encoding="utf-8")
    if "roles_setup" in sys.modules:
        del sys.modules["roles_setup"]
    import roles_setup  # noqa
    print("[roles_setup_restore] roles_setup OK", len(text))

_go()

def registrar(bot):
    print("[roles_setup_restore] listo — hoist/@mention respetados")
