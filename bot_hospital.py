# -*- coding: utf-8 -*-
"""bot_hospital.py — carga el bot desde chunks comprimidos."""
import base64
import zlib

def _load():
    parts = []
    from bot_data_0 import CHUNK as _c0
    parts.append(_c0)
    from bot_data_1 import CHUNK as _c1
    parts.append(_c1)
    from bot_data_2 import CHUNK as _c2
    parts.append(_c2)
    from bot_data_3 import CHUNK as _c3
    parts.append(_c3)

    code = zlib.decompress(base64.b64decode("".join(parts))).decode("utf-8")
    exec(compile(code, "bot_hospital_full.py", "exec"), globals())

_load()
