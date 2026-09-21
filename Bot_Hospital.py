# -*- coding: utf-8 -*-
"""Bot Hospital — punto de entrada."""
import config

# Carga todo el registro de comandos y define `bot`
import hospital_core  # noqa: F401 — ejecuta el módulo y registra comandos

from hospital_core import bot

if not config.TOKEN:
    raise SystemExit(
        "No hay TOKEN. En Railway ve a Variables y crea TOKEN "
        "(o DISCORD_TOKEN / BOT_TOKEN) con el token del bot. "
        "No lo pongas en config.py."
    )
bot.run(config.TOKEN)
