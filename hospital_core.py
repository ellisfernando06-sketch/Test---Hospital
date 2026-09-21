# -*- coding: utf-8 -*-
"""
hospital_core.py — Carga el núcleo del bot desde un commit estable y
registra SIEMPRE los módulos nuevos (comandos_nuevos, centro_solicitudes_ui, verificacion).
"""
from __future__ import annotations

import traceback
import urllib.request

_COMMIT = "30a15578af8c1459b0d2dcad8af2881c4a8a326b"
_URL = (
    "https://raw.githubusercontent.com/ellisfernando06-sketch/Test---Hospital/"
    f"{_COMMIT}/Bot_Hospital.py"
)


def _cargar(module_globals: dict):
    print("[hospital_core] Descargando núcleo del bot…")
    with urllib.request.urlopen(_URL, timeout=45) as resp:
        source = resp.read().decode("utf-8")
    print(f"[hospital_core] Núcleo descargado ({len(source)} bytes)")

    # --- Parches de import (opcionales, el registro real se hace después) ---
    old_import = (
        "from solicitudes import (\n"
        "    CartaSolicitudModal, SolicitudDescargoModal, SolicitudPermisoModal,\n"
        "    enviar_solicitud, enviar_solicitud_con_aprobacion,\n"
        "    CitatorioModal, ReporteProcedimientoModal, AprobacionView,\n"
        "    resolver_ruta, DESTINATARIOS_CHOICES, canal_para_key, nombre_destinatario,\n"
        ")"
    )
    if old_import in source:
        source = source.replace(
            old_import,
            old_import + "\nimport comandos_nuevos\nimport verificacion\nimport centro_solicitudes_ui",
            1,
        )
        print("[hospital_core] Imports nuevos inyectados en el núcleo")
    else:
        print("[hospital_core] AVISO: bloque de import solicitudes no encontrado")

    # Insertar llamadas registrar justo después de crear el bot
    old_bot = 'bot = commands.Bot(command_prefix="!", intents=intents)'
    if old_bot in source:
        source = source.replace(
            old_bot,
            old_bot
            + "\n\n"
            + "# --- Registro módulos nuevos (inyectado) ---\n"
            + "try:\n"
            + "    comandos_nuevos.registrar(bot)\n"
            + "    print('[hospital_core] comandos_nuevos OK')\n"
            + "except Exception as _e:\n"
            + "    print('[hospital_core] ERROR comandos_nuevos:', _e)\n"
            + "try:\n"
            + "    centro_solicitudes_ui.registrar(bot)\n"
            + "    print('[hospital_core] centro_solicitudes_ui OK')\n"
            + "except Exception as _e:\n"
            + "    print('[hospital_core] ERROR centro_solicitudes_ui:', _e)\n",
            1,
        )
        print("[hospital_core] Llamadas registrar() inyectadas")
    else:
        print("[hospital_core] AVISO: línea bot = commands.Bot no encontrada")

    # Vista persistente de verificación
    old_view = (
        'bot.add_view(AprobacionView(key_aprobador="DIRECTOR_RRHH", '
        'solicitud_id="persist"))'
    )
    if old_view in source:
        source = source.replace(
            old_view,
            old_view
            + "\n    try:\n"
            + "        bot.add_view(verificacion.VerificarView(staff_id=0, guild_id=0))\n"
            + "    except Exception as _e:\n"
            + "        print('[hospital_core] ERROR VerificarView:', _e)",
            1,
        )

    # No ejecutar el bot.run del archivo remoto
    marker = "if not config.TOKEN:"
    idx = source.find(marker)
    if idx > 0:
        source = source[:idx]

    print("[hospital_core] Ejecutando núcleo…")
    try:
        exec(compile(source, "hospital_core_remote.py", "exec"), module_globals)
    except Exception:
        print("[hospital_core] ERROR al ejecutar el núcleo:")
        traceback.print_exc()
        raise

    bot = module_globals.get("bot")
    if bot is None:
        raise RuntimeError("hospital_core: el núcleo no definió 'bot'")

    # --- Registro FORZADO después del exec (por si el parche falló) ---
    print("[hospital_core] Registro forzado de módulos nuevos…")
    try:
        import comandos_nuevos
        comandos_nuevos.registrar(bot)
        print("[hospital_core] ✓ comandos_nuevos.registrar OK")
    except Exception:
        print("[hospital_core] ✗ comandos_nuevos.registrar FALLÓ:")
        traceback.print_exc()

    try:
        import centro_solicitudes_ui
        centro_solicitudes_ui.registrar(bot)
        print("[hospital_core] ✓ centro_solicitudes_ui.registrar OK")
    except Exception:
        print("[hospital_core] ✗ centro_solicitudes_ui.registrar FALLÓ:")
        traceback.print_exc()

    try:
        import verificacion  # noqa: F401
        print("[hospital_core] ✓ verificacion importado")
    except Exception:
        print("[hospital_core] ✗ verificacion FALLÓ:")
        traceback.print_exc()

    # Contar comandos en el árbol
    try:
        cmds = list(bot.tree.get_commands())
        print(f"[hospital_core] Comandos en el árbol: {len(cmds)}")
        nombres = sorted(c.name for c in cmds)
        for n in (
            "sancionar", "quitar_sancion", "apelar_sancion", "historial_sanciones",
            "banear", "expulsar", "silenciar", "verificar_roblox",
            "panel_solicitudes", "registrar_gasto", "libro_contable",
        ):
            marca = "✓" if n in nombres else "✗"
            print(f"  {marca} /{n}")
    except Exception as e:
        print("[hospital_core] No se pudo listar comandos:", e)

    return bot


bot = _cargar(globals())
