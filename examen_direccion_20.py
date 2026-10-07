# -*- coding: utf-8 -*-
"""Parche: cada examen de dirección usa exactamente 20 preguntas RP."""
from __future__ import annotations


def registrar(bot) -> None:
    try:
        import examen_direccion as ed
    except Exception as e:
        print(f"[examen_20] sin examen_direccion: {e}")
        return

    try:
        from examen_direccion_preguntas import BANCO
    except Exception as e:
        print(f"[examen_20] sin banco: {e}")
        BANCO = {}

    ed._PREGUNTAS_POR_EXAMEN = 20  # type: ignore
    if hasattr(ed, "_MINIMO"):
        # mantener mínimo RP accesible
        ed._MINIMO = max(int(getattr(ed, "_MINIMO", 60) or 60), 50)  # type: ignore

    def _preguntas_para(key: str):
        import time

        banco = list(BANCO.get(key) or getattr(ed, "_BANCO", {}).get(key) or [])
        if not banco:
            return []
        n = 20
        if len(banco) < n:
            extra = []
            i = 0
            while len(banco) + len(extra) < n:
                extra.append(banco[i % len(banco)])
                i += 1
            banco = banco + extra
        start = int(time.time()) % len(banco)
        rot = banco[start:] + banco[:start]
        return rot[:n]

    ed._preguntas_para = _preguntas_para  # type: ignore
    # si el módulo ya registró el comando, basta con el parche de funciones
    print("[examen_20] OK — 20 preguntas por dirección")
