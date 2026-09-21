# -*- coding: utf-8 -*-
"""
hospital_core.py — Carga el núcleo del bot desde un commit estable en GitHub
y aplica parches (comandos_nuevos, verificacion, centro_solicitudes).
"""
from __future__ import annotations

import urllib.request

_COMMIT = "30a15578af8c1459b0d2dcad8af2881c4a8a326b"
_URL = (
    "https://raw.githubusercontent.com/ellisfernando06-sketch/Test---Hospital/"
    f"{_COMMIT}/Bot_Hospital.py"
)


def _cargar():
    with urllib.request.urlopen(_URL, timeout=45) as resp:
        source = resp.read().decode("utf-8")

    old_import = (
        "from solicitudes import (\n"
        "    CartaSolicitudModal, SolicitudDescargoModal, SolicitudPermisoModal,\n"
        "    enviar_solicitud, enviar_solicitud_con_aprobacion,\n"
        "    CitatorioModal, ReporteProcedimientoModal, AprobacionView,\n"
        "    resolver_ruta, DESTINATARIOS_CHOICES, canal_para_key, nombre_destinatario,\n"
        ")"
    )
    new_import = (
        old_import
        + "\nimport comandos_nuevos\nimport verificacion\nimport centro_solicitudes"
    )
    if old_import in source:
        source = source.replace(old_import, new_import, 1)

    old_bot = 'bot = commands.Bot(command_prefix="!", intents=intents)\n'
    new_bot = (
        'bot = commands.Bot(command_prefix="!", intents=intents)\n\n'
        "comandos_nuevos.registrar(bot)\n"
        "centro_solicitudes.registrar(bot)\n"
    )
    if old_bot in source:
        source = source.replace(old_bot, new_bot, 1)

    old_view = (
        'bot.add_view(AprobacionView(key_aprobador="DIRECTOR_RRHH", '
        'solicitud_id="persist"))'
    )
    new_view = (
        old_view
        + "\n    bot.add_view(verificacion.VerificarView(staff_id=0, guild_id=0))"
    )
    if old_view in source:
        source = source.replace(old_view, new_view, 1)

    marker = "if not config.TOKEN:"
    idx = source.find(marker)
    if idx > 0:
        source = source[:idx]

    g = {"__name__": "hospital_core", "__file__": __file__}
    # Compartir el namespace del módulo actual para que `from hospital_core import bot` funcione
    import hospital_core as self_mod
    g = self_mod.__dict__
    exec(compile(source, "hospital_core_remote.py", "exec"), g)
    return g.get("bot")


bot = _cargar()
