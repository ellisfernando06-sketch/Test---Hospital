# -*- coding: utf-8 -*-
"""Instala assets/certificado_plantilla.jpg (plantilla oficial)."""
from __future__ import annotations

import base64
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_TARGET = _ROOT / "assets" / "certificado_plantilla.jpg"


def ensure_plantilla():
    try:
        if _TARGET.is_file() and _TARGET.stat().st_size > 20000:
            return _TARGET
    except Exception:
        pass
    chunks = []
    for i in range(2):
        try:
            mod = __import__(f"_cert_tpl_part{i}")
            chunks.append(getattr(mod, "PART", "") or "")
        except Exception:
            chunks.append("")
    if not all(chunks):
        return None
    try:
        raw = base64.b64decode("".join(chunks))
        _TARGET.parent.mkdir(parents=True, exist_ok=True)
        _TARGET.write_bytes(raw)
        print(f"[cert_plantilla] OK {len(raw)} bytes -> {_TARGET}", flush=True)
        return _TARGET
    except Exception as e:
        print("[cert_plantilla] error:", e, flush=True)
        return None


try:
    ensure_plantilla()
except Exception as e:
    print("[cert_plantilla]", e, flush=True)
