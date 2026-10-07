# -*- coding: utf-8 -*-
"""Parche: 20 preguntas RP + mínimo 70% para aprobar."""
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
    ed._MINIMO = 70  # type: ignore

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
    print("[examen_20] OK — 20 preguntas · mínimo 70%")
