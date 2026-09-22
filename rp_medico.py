# -*- coding: utf-8 -*
"""rp_medico — ensambla partes b64 y carga el módulo RP médico completo."""
from __future__ import annotations
import base64, pathlib, sys
_dir = pathlib.Path(__file__).parent
_parts = []
for i in range(10):
    p = _dir / f"rp_medico.b64.{i}"
    if not p.is_file():
        break
    _parts.append(p.read_text(encoding="ascii"))
if not _parts:
    raise RuntimeError("Faltan archivos rp_medico.b64.*")
_src = base64.b64decode("".join(_parts)).decode("utf-8")
exec(compile(_src, "rp_medico_full.py", "exec"), globals())
