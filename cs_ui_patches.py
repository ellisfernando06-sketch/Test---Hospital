# -*- coding: utf-8 -*
import base64
from pathlib import Path
_p = Path(__file__).parent
_raw = b"".join(base64.b64decode((_p / f"cs_ui_b{i}.txt").read_text()) for i in range(3))
exec(compile(_raw.decode("utf-8"), "cs_ui_patches_full.py", "exec"), globals())
