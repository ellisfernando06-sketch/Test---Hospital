# -*- coding: utf-8 -*
from __future__ import annotations
import base64, zlib
from pathlib import Path
_ROOT = Path(__file__).resolve().parent
_TARGET = _ROOT / "assets" / "certificado_plantilla.jpg"
_N = 21
def ensure_plantilla():
    try:
        if _TARGET.is_file() and _TARGET.stat().st_size > 40000:
            return _TARGET
    except Exception:
        pass
    chunks = []
    for i in range(_N):
        try:
            chunks.extend(__import__(f"_cert_tpl_pack{i}").CHUNKS)
        except Exception as e:
            print(f"[cert_plantilla] pack {i}: {e}", flush=True)
            return None
    try:
        raw = zlib.decompress(base64.b64decode("".join(chunks)))
        _TARGET.parent.mkdir(parents=True, exist_ok=True)
        _TARGET.write_bytes(raw)
        print(f"[cert_plantilla] OK {len(raw)} bytes", flush=True)
        return _TARGET
    except Exception as e:
        print("[cert_plantilla]", e, flush=True)
        return None
try:
    ensure_plantilla()
except Exception as e:
    print("[cert_plantilla]", e, flush=True)
