# -*- coding: utf-8 -*
"""paneles_miembros.py — ensambla pm1+pm2."""
from pathlib import Path
_p = Path(__file__).parent
_src = (_p / "pm1.py").read_text(encoding="utf-8") + (_p / "pm2.py").read_text(encoding="utf-8")
exec(compile(_src, "paneles_miembros_full.py", "exec"), globals())
