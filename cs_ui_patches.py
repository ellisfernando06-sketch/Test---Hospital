# -*- coding: utf-8 -*
from pathlib import Path
_p = Path(__file__).parent
_src = "".join((_p/f"cs_ui_part{i}.py").read_text(encoding="utf-8") for i in range(3))
exec(compile(_src, "cs_ui_full.py", "exec"), globals())
