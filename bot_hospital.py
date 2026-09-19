# -*- coding: utf-8 -*-
"""Carga el bot desde bh_payload.b64 (gzip+base64)."""
import base64, gzip, pathlib, sys
p = pathlib.Path(__file__).with_name("bh_payload.b64")
if not p.exists():
    raise SystemExit("Falta bh_payload.b64 en el repo — sube ese archivo desde el ZIP.")
code = gzip.decompress(base64.b64decode(p.read_text()))
ns = {"__name__": "__main__", "__file__": str(pathlib.Path(__file__).resolve())}
exec(compile(code, "bot_hospital.py", "exec"), ns)
