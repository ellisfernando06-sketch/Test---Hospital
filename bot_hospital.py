# -*- coding: utf-8 -*-
"""Carga el bot desde chunks bh_p0.b64 .. bh_p3.b64 (gzip+base64)."""
import base64
import gzip
import pathlib

base = pathlib.Path(__file__).parent
parts = []
for i in range(4):
    p = base / f"bh_p{i}.b64"
    if not p.exists():
        raise SystemExit(f"Falta {p.name} en el repo")
    parts.append(p.read_text().strip())
code = gzip.decompress(base64.b64decode("".join(parts)))
ns = {"__name__": "__main__", "__file__": str(pathlib.Path(__file__).resolve())}
exec(compile(code, "bot_hospital.py", "exec"), ns)
