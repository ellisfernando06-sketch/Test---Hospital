# -*- coding: utf-8 -*
from __future__ import annotations
import base64, pathlib
_dir = pathlib.Path(__file__).parent
_parts = []
for i in range(20):
    p = _dir / f"rpm.b64.{i}"
    if not p.is_file():
        break
    _parts.append(p.read_text(encoding="ascii"))
if not _parts:
    raise RuntimeError("Faltan rpm.b64.* — redeploy incompleto")
exec(compile(base64.b64decode("".join(_parts)).decode("utf-8"), "rp_medico_full.py", "exec"), globals())
