# -*- coding: utf-8 -*-
"""Carga renombre de autoridades."""
from __future__ import annotations


def registrar(bot) -> None:
    try:
        import roles_nombres_autoridades as m

        if hasattr(m, "registrar"):
            m.registrar(bot)
        print("[roles_nombres_load] OK")
    except Exception as e:
        print(f"[roles_nombres_load] {e}")
