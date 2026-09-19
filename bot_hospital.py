# -*- coding: utf-8 -*-
"""Primer arranque: expande el bot completo. Luego reinicia (Railway redeploy)."""
import base64
import gzip
import pathlib
import sys

_B64 = (
    "SEE_FILE"
)

_path = pathlib.Path(__file__)
_data = gzip.decompress(base64.b64decode("".join(_B64)))
if b"Primer arranque: expande" in _path.read_bytes()[:120]:
    _path.write_bytes(_data)
    print("OK: bot_hospital.py restaurado. REINICIA el bot ahora.")
    sys.exit(0)
exec(compile(_data, str(_path), "exec"), {"__name__": "__main__", "__file__": str(_path)})
