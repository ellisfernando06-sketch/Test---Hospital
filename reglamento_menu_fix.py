# -*- coding: utf-8 -*-
"""
Asegura que el Reglamento del Hospital se lista primero en
/publicar_reglamento y que /agregar_reglamento lo puede guardar igual.
"""
from __future__ import annotations

from typing import List


def registrar(bot) -> None:
    try:
        import anuncios_largos as al
    except Exception as e:
        print(f"[reglamento_menu_fix] sin anuncios_largos: {e}")
        return

    _orig_listar = al._listar_items

    def _listar_items() -> List[dict]:
        out = _orig_listar()
        # Hospital primero
        def _prio(it: dict) -> tuple:
            t = (it.get("titulo") or "").lower()
            rid = (it.get("id") or "").lower()
            if "reglamento del hospital" in t or rid == "reglamento-del-hospital":
                return (0, t)
            if "hospital" in t:
                return (1, t)
            return (2, t)

        out.sort(key=_prio)
        return out

    al._listar_items = _listar_items

    # Si PublicarReglamentoView ya está definida, no hace falta más:
    # usa _opciones_select → _listar_items en cada apertura.

    print("[reglamento_menu_fix] OK — Hospital prioritario en /publicar_reglamento")
