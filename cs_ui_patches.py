# -*- coding: utf-8 -*
from pathlib import Path
_p = Path(__file__).parent
exec(compile((_p/"cs_ui_a.py").read_text()+(_p/"cs_ui_b.py").read_text(), "cs_ui.py", "exec"), globals())
