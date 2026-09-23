# -*- coding: utf-8 -*
"""cs_ui_patches — aplica parches de aprobación e involucrados."""
from __future__ import annotations
from pathlib import Path

def apply(mod):
    base = Path(__file__).parent
    ns = {"__name__": "cs_ui_patches_ns"}
    for name in ("cs_ui_p1.py", "cs_ui_p2a.py", "cs_ui_p2b.py"):
        code = (base / name).read_text(encoding="utf-8")
        exec(compile(code, name, "exec"), ns)
    ns["_patch_all"](mod)
