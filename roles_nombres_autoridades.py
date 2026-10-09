# -*- coding: utf-8 -*-
"""Solo Fundador del Hospital (CO_OWNER legado ya no se renombra a Gerente)."""
from __future__ import annotations

from discord.ext import commands


def registrar(bot: commands.Bot) -> None:
    try:
        import roles_config as rc

        if hasattr(rc, "KEYS_NOMBRES") and isinstance(rc.KEYS_NOMBRES, dict):
            rc.KEYS_NOMBRES["FUNDADOR_OWNER"] = ("👑 Fundador del Hospital", "#9B59B6")
            # No crear/mostrar Gerente de Fundación
            if "CO_OWNER" in rc.KEYS_NOMBRES:
                rc.KEYS_NOMBRES["CO_OWNER"] = (
                    "🤝 Co-Fundador · Gobernanza",
                    "#3498DB",
                )
    except Exception as e:
        print(f"[roles_nombres] {e}")
    print("[roles_nombres] OK — sin Gerente de Fundación")
