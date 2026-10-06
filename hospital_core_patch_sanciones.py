# -*- coding: utf-8 -*-
"""Asegura carga de panel_tickets_ui y sanciones_apelacion_ui."""
from __future__ import annotations


def registrar(bot) -> None:
    for name in ("panel_tickets_ui", "sanciones_apelacion_ui", "sanciones"):
        try:
            mod = __import__(name)
            if hasattr(mod, "registrar"):
                mod.registrar(bot)
                print(f"[hospital_core_patch_sanciones] ✓ {name}")
        except Exception as e:
            print(f"[hospital_core_patch_sanciones] ✗ {name}: {e}")
