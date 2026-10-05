# -*- coding: utf-8 -*-
from __future__ import annotations
import base64, pathlib, sys, zlib

def _go():
    parts = []
    for i in range(8):
        m = __import__(f"cp{i}")
        parts.append(m.PART)
        sys.modules.pop(f"cp{i}", None)
    data = zlib.decompress(base64.b64decode("".join(parts)))
    a = pathlib.Path(__file__).resolve().parent / "assets"
    a.mkdir(exist_ok=True)
    t = a / "cuarentena.jpg"
    t.write_bytes(data)
    print(f"[cuarentena_img] {t} ({len(data)})")

_go()

def registrar(bot):
    print("[cuarentena_img_install] OK")
