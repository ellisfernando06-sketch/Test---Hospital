# -*- coding: utf-8 -*
"""hospital_core.py — núcleo + módulos + sync de TODOS los comandos."""
from __future__ import annotations

import asyncio
import traceback
import urllib.request

import discord

_COMMIT = "30a15578af8c1459b0d2dcad8af2881c4a8a326b"
_URL = (
    "https://raw.githubusercontent.com/ellisfernando06-sketch/Test---Hospital/"
    f"{_COMMIT}/Bot_Hospital.py"
)
_GUILD_ID = 1381360019467014184


def _cargar(module_globals: dict):
    print("[hospital_core] Descargando núcleo del bot…")
    with urllib.request.urlopen(_URL, timeout=45) as resp:
        source = resp.read().decode("utf-8")
    print(f"[hospital_core] Núcleo descargado ({len(source)} bytes)")

    if "bot.tree.clear_commands(guild=None)" in source:
        source = source.replace(
            "bot.tree.clear_commands(guild=None)  # limpia registro global en memoria",
            "pass  # [hospital_core] NO vaciar global",
        )
        source = source.replace(
            "await bot.tree.sync()  # publica árbol vacío a nivel global (quita duplicados viejos)",
            "pass  # [hospital_core] NO sync global vacío",
        )
        source = source.replace(
            "bot.tree.clear_commands(guild=None)",
            "pass  # [hospital_core] NO vaciar global",
        )
        print("[hospital_core] clear_commands global DESACTIVADO")

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
        "limpiar_canal",
        "entrevista_ui",
        "tickets_cierre",
        "docencia",
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
        glob_names = sorted(c.name for c in bot.tree.get_commands())
        print(f"[hospital_core] TOTAL en memoria (global): {len(glob_names)}")
        print("[hospital_core] Lista:", ", ".join(glob_names))
    except Exception as e:
        print("[hospital_core] listar:", e)

    async def _sync_todo(reason: str = ""):
        g = discord.Object(id=_GUILD_ID)
        try:
            bot.tree.clear_commands(guild=g)
        except Exception:
            pass
        bot.tree.copy_global_to(guild=g)
        synced = await bot.tree.sync(guild=g)
        names = sorted(c.name for c in synced)
        print(f"[hospital_core] Sync {reason}: {len(synced)} comandos → servidor")
        print("[hospital_core] Comandos publicados:", ", ".join(names))
        return names

    @bot.listen("on_ready")
    async def _hospital_core_full_sync():
        if getattr(bot, "_hc_full_sync_done", False):
            return
        bot._hc_full_sync_done = True
        await asyncio.sleep(4)
        try:
            await _sync_todo("COMPLETO")
        except Exception as e:
            print("[hospital_core] Sync COMPLETO falló:", e)
            traceback.print_exc()
        await asyncio.sleep(8)
        try:
            await _sync_todo("REINTENTO")
        except Exception as e:
            print("[hospital_core] Sync REINTENTO falló:", e)

    bot._hospital_sync_todo = _sync_todo
    return bot


bot = _cargar(globals())
