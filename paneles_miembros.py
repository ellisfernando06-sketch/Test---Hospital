# -*- coding: utf-8 -*
"""paneles_miembros.py — loader desde partes b64 (evita límites de push)."""
from pathlib import Path
import base64
_p = Path(__file__).parent
_parts = sorted(_p.glob("pm_part_*.b64"), key=lambda x: int(x.stem.split("_")[-1]))
_src = base64.b64decode("".join(p.read_text() for p in _parts)).decode("utf-8")
exec(compile(_src, "paneles_miembros_full.py", "exec"), globals())
