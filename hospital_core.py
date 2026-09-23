# -*- coding: utf-8 -*
"""hospital_core.py — núcleo + módulos + sync completo sin vaciar el árbol."""
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
            "pass  # [hospital_core] clear_commands DESACTIVADO",
        )
        source = source.replace(
            "await bot.tree.sync()  # publica árbol vacío a nivel global (quita duplicados viejos)",
            "pass  # [hospital_core] sync global vacío DESACTIVADO",
        )
        source = source.replace(
            "bot.tree.clear_commands(guild=None)",
            "pass  # [hospital_core] clear_commands DESACTIVADO",
        )
        print("[hospital_core] clear_commands desactivado")
    else:
        print("[hospital_core] AVISO: clear_commands no encontrado en núcleo")

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
        print(f"[hospital_core] Comandos en árbol global: {len(glob_names)}")
        for n in ("limpiar", "limpiar_todo", "bootstrap_owner", "configurar_roles", "panel_miembros"):
            print(f"  {'✓' if n in glob_names else '✗'} /{n}")
    except Exception as e:
        print("[hospital_core] listar:", e)

    @bot.listen("on_ready")
    async def _hospital_core_full_sync():
        if getattr(bot, "_hc_full_sync_done", False):
            return
        bot._hc_full_sync_done = True
        await asyncio.sleep(3)
        try:
            g = discord.Object(id=_GUILD_ID)
            bot.tree.copy_global_to(guild=g)
            synced = await bot.tree.sync(guild=g)
            names = sorted(c.name for c in synced)
            print(f"[hospital_core] Sync COMPLETO guild: {len(synced)} comandos")
            for n in (
                "limpiar", "limpiar_todo", "sincronizar_comandos",
                "bootstrap_owner", "configurar_roles", "panel_miembros",
                "otorgar_key", "dar_rol",
            ):
                print(f"  {'✓' if n in names else '✗'} /{n}")
        except Exception as e:
            print("[hospital_core] Sync completo falló:", e)

    return bot


bot = _cargar(globals())
