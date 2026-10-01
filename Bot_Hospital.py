# -*- coding: utf-8 -*-
"""Bot Hospital — punto de entrada (Railway)."""
import traceback

import config

# Carga registro de comandos y define `bot` (hospital_core no tumba el proceso)
import hospital_core  # noqa: F401

from hospital_core import bot

if not getattr(config, "TOKEN", None):
    raise SystemExit(
        "No hay TOKEN. En Railway → Variables crea TOKEN "
        "(o DISCORD_TOKEN / BOT_TOKEN) con el token del bot."
    )

try:
    bot.run(config.TOKEN)
except Exception:
    traceback.print_exc()
    raise
