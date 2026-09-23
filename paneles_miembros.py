# -*- coding: utf-8 -*
from pathlib import Path
_p = Path(__file__).parent
_src = (_p/"pm_a.py").read_text(encoding="utf-8")+(_p/"pm_b.py").read_text(encoding="utf-8")
exec(compile(_src, "paneles_miembros_full.py", "exec"), globals())
