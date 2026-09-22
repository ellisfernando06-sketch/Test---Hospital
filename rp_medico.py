# -*- coding: utf-8 -*
from pathlib import Path
_p = Path(__file__).parent
_src = (_p / "rpm1.py").read_text(encoding="utf-8") + (_p / "rpm2.py").read_text(encoding="utf-8")
exec(compile(_src, "rp_medico_full.py", "exec"), globals())
