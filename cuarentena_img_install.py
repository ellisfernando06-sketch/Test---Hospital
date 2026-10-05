# -*- coding: utf-8 -*-
"""cuarentena_img_install.py — escribe assets/cuarentena.jpg"""
from __future__ import annotations
import base64, pathlib, sys, zlib

def _go():
    a = __import__("cuarentena_p0").PART
    b = __import__("cuarentena_p1").PART
    for n in ("cuarentena_p0", "cuarentena_p1"):
        sys.modules.pop(n, None)
    data = zlib.decompress(base64.b64decode(a + b))
    assets = pathlib.Path(__file__).resolve().parent / "assets"
    assets.mkdir(exist_ok=True)
    t = assets / "cuarentena.jpg"
    t.write_bytes(data)
    print(f"[cuarentena_img] {t} ({len(data)} bytes)")

_go()

def registrar(bot):
    print("[cuarentena_img_install] OK")
