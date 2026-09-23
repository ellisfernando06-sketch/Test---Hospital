# -*- coding: utf-8 -*
"""
hospital_core.py — Carga el núcleo del bot y registra módulos nuevos
(comandos_nuevos, centro_solicitudes_ui, verificacion, rp_medico, paneles_miembros, tienda, comunidad).
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

    old_view = (
        'bot.add_view(AprobacionView(key_aprobador="DIRECTOR_RRHH", '
        'solicitud_id="persist"))'
    )
    if old_view in source:
        source = source.replace(
            old_view,
            old_view
            + "\n    try:\n"
            + "        import verificacion as _verif\n"
            + "        bot.add_view(_verif.VerificarView(staff_id=0, guild_id=0))\n"
            + "    except Exception as _e:\n"
            + "        print('[hospital_core] ERROR VerificarView:', _e)",
            1,
        )

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

    print("[hospital_core] Registrando módulos nuevos…")

    for mod_name in (
        "comandos_nuevos",
        "centro_solicitudes_ui",
        "verificacion",
        "rp_medico",
        "paneles_miembros",
        "tienda",
        "comunidad",
    ):
        try:
            mod = __import__(mod_name)
            if hasattr(mod, "registrar"):
                mod.registrar(bot)
            print(f"[hospital_core] ✓ {mod_name} OK")
        except Exception:
            print(f"[hospital_core] ✗ {mod_name} FALLÓ:")
            traceback.print_exc()

    try:
        cmds = list(bot.tree.get_commands())
        nombres = sorted(c.name for c in cmds)
        print(f"[hospital_core] Total comandos en árbol: {len(nombres)}")
        for n in (
            "panel_miembros", "panel_tienda", "tienda", "bienvenida", "reglas",
            "panel_reglas", "mi_inventario", "panel_staff_disciplina",
        ):
            marca = "✓" if n in nombres else "✗ FALTA"
            print(f"  {marca} /{n}")
    except Exception as e:
        print("[hospital_core] No se pudo listar comandos:", e)

    return bot


bot = _cargar(globals())
