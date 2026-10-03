# -*- coding: utf-8 -*-
from __future__ import annotations
import base64
from pathlib import Path
_ROOT = Path(__file__).resolve().parent
_TARGET = _ROOT / "assets" / "certificado_plantilla.jpg"

def ensure_plantilla():
    try:
        if _TARGET.is_file() and _TARGET.stat().st_size > 10000:
            return _TARGET
    except Exception:
        pass
    chunks = []
    for i in range(3):
        try:
            chunks.append(__import__(f"_cert_tpl_part{i}").PART)
        except Exception:
            return None
    try:
        raw = base64.b64decode("".join(chunks))
        _TARGET.parent.mkdir(parents=True, exist_ok=True)
        _TARGET.write_bytes(raw)
        print("[cert_plantilla] OK", len(raw), flush=True)
        return _TARGET
    except Exception as e:
        print("[cert_plantilla]", e, flush=True)
        return None

try:
    ensure_plantilla()
except Exception as e:
    print("[cert_plantilla]", e, flush=True)
