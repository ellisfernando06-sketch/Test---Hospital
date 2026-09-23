# -*- coding: utf-8 -*
from pathlib import Path
_p = Path(__file__).parent
_src = (_p/"tienda1.py").read_text(encoding="utf-8")+(_p/"tienda2.py").read_text(encoding="utf-8")
exec(compile(_src, "tienda_full.py", "exec"), globals())
