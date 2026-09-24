# -*- coding: utf-8 -*
"""hospital_core.py — núcleo + módulos + sync FIABLE de todos los comandos."""
from __future__ import annotations

import asyncio
import traceback
import urllib.request

import discord
from discord.ext import commands

_COMMIT = "30a15578af8c1459b0d2dcad8af2881c4a8a326b"
_URL = (
    "https://raw.githubusercontent.com/ellisfernando06-sketch/Test---Hospital/"
    f"{_COMMIT}/Bot_Hospital.py"
)
_GUILD_ID = 1381360019467014184

_MODULOS = (
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
)


def _cargar(module_globals: dict):
    print("[hospital_core] Descargando núcleo del bot…")
    with urllib.request.urlopen(_URL, timeout=60) as resp:
        source = resp.read().decode("utf-8")
    print(f"[hospital_core] Núcleo descargado ({len(source)} bytes)")

    # Bloque exacto del on_ready remoto que vacía los comandos
    old_sync_block = (
        "    # Solo sincronización al servidor (evita comandos duplicados global+guild).\n"
        "    # IMPORTANTE: se copia al guild y se sincroniza ANTES de limpiar el árbol\n"
        "    # global. Si se limpia primero (clear_commands(guild=None)), copy_global_to\n"
        "    # no tiene nada que copiar y el guild queda con la lista de comandos vacía.\n"
        "    try:\n"
        "        MI_SERVIDOR = discord.Object(id=1381360019467014184)\n"
        "        bot.tree.copy_global_to(guild=MI_SERVIDOR)  # copia mientras el global aún tiene comandos\n"
        "        sincronizados_guild = await bot.tree.sync(guild=MI_SERVIDOR)\n"
        "        bot.tree.clear_commands(guild=None)  # limpia registro global en memoria\n"
        "        await bot.tree.sync()  # publica árbol vacío a nivel global (quita duplicados viejos)\n"
        "        print(f\"Sincronizados {len(sincronizados_guild)} comandos slash (solo tu servidor, sin duplicados).\")\n"
        "    except Exception as e:\n"
        "        print(f\"Error al sincronizar comandos: {e}\")\n"
    )

    new_sync_block = (
        "    # [hospital_core] Sync del núcleo REMOTO desactivado.\n"
        "    # hospital_core publica los comandos DESPUÉS de cargar todos los módulos.\n"
        "    print('[hospital_core] Sync del núcleo omitido — lo gestiona hospital_core')\n"
    )

    if old_sync_block in source:
        source = source.replace(old_sync_block, new_sync_block)
        print("[hospital_core] ✓ Bloque sync remoto anulado")
    else:
        print("[hospital_core] ⚠ Bloque exacto no encontrado — aplicando parches sueltos")
        source = source.replace(
            "bot.tree.clear_commands(guild=None)  # limpia registro global en memoria",
            "pass  # [hospital_core] NO vaciar global",
        )
        source = source.replace(
            "await bot.tree.sync()  # publica árbol vacío a nivel global (quita duplicados viejos)",
            "pass  # [hospital_core] NO sync vacío",
        )
        source = source.replace(
            "bot.tree.clear_commands(guild=None)",
            "pass  # [hospital_core] NO vaciar global",
        )
        # Evitar el sync vacío genérico (pero NO el de guild=)
        source = source.replace(
            "await bot.tree.sync()  # publica árbol vacío",
            "pass  # [hospital_core]",
        )

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

    print("[hospital_core] Registrando módulos…")
    ok_mods, fail_mods = [], []
    for mod_name in _MODULOS:
        try:
            mod = __import__(mod_name)
            if hasattr(mod, "registrar"):
                mod.registrar(bot)
                ok_mods.append(mod_name)
                print(f"[hospital_core] ✓ {mod_name}")
            else:
                print(f"[hospital_core] · {mod_name} (sin registrar)")
        except Exception:
            fail_mods.append(mod_name)
            print(f"[hospital_core] ✗ {mod_name}:")
            traceback.print_exc()

    print(f"[hospital_core] OK={ok_mods} FAIL={fail_mods}")

    try:
        glob_names = sorted({c.name for c in bot.tree.get_commands()})
        print(f"[hospital_core] Comandos en memoria: {len(glob_names)}")
        print("[hospital_core]", ", ".join(glob_names) if glob_names else "(ninguno)")
    except Exception as e:
        print("[hospital_core] listar:", e)

    async def _sync_todo(reason: str = "") -> list:
        all_names: list = []
        try:
            try:
                synced_global = await bot.tree.sync()
                print(f"[hospital_core] Sync GLOBAL ({reason}): {len(synced_global)}")
            except Exception as e:
                print(f"[hospital_core] Sync GLOBAL falló ({reason}):", e)

            targets = list(bot.guilds) if bot.guilds else []
            if not targets:
                targets = [discord.Object(id=_GUILD_ID)]

            for g in targets:
                gid = int(getattr(g, "id", _GUILD_ID))
                obj = discord.Object(id=gid)
                try:
                    bot.tree.copy_global_to(guild=obj)
                    synced = await bot.tree.sync(guild=obj)
                    names = sorted(c.name for c in synced)
                    all_names = names
                    preview = ", ".join(names[:50])
                    if len(names) > 50:
                        preview += "…"
                    print(f"[hospital_core] Sync GUILD {gid} ({reason}): {len(names)} → {preview}")
                except Exception as e:
                    print(f"[hospital_core] Sync GUILD {gid} falló ({reason}):", e)
                    traceback.print_exc()
        except Exception as e:
            print(f"[hospital_core] _sync_todo error ({reason}):", e)
            traceback.print_exc()
        return all_names

    @bot.command(name="forzar_sync")
    async def forzar_sync_cmd(ctx: commands.Context):
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return
        if not (ctx.author.guild_permissions.administrator or ctx.author.id == ctx.guild.owner_id):
            await ctx.send("❌ Solo administrador o dueño del servidor.")
            return
        msg = await ctx.send("🔄 Sincronizando todos los slash commands…")
        try:
            names = await _sync_todo("manual-prefix")
            await msg.edit(
                content=(
                    f"✅ **{len(names)}** comandos publicados en el servidor.\n"
                    f"`{'`, `'.join(names[:60])}`"
                    + ("…" if len(names) > 60 else "")
                    + "\n\nEscribe `/` en Discord; deberían aparecer ya."
                )
            )
        except Exception as e:
            await msg.edit(content=f"❌ Error: `{e}`")

    @bot.listen("on_ready")
    async def _hospital_core_full_sync():
        if getattr(bot, "_hc_full_sync_done", False):
            return
        bot._hc_full_sync_done = True
        print(f"[hospital_core] on_ready como {bot.user} | guilds={[g.id for g in bot.guilds]}")
        await asyncio.sleep(2)
        try:
            names = await _sync_todo("arranque")
            print(f"[hospital_core] Arranque: {len(names)} comandos")
        except Exception as e:
            print("[hospital_core] Sync arranque falló:", e)
            traceback.print_exc()
        await asyncio.sleep(10)
        try:
            await _sync_todo("reintento")
        except Exception as e:
            print("[hospital_core] Sync reintento falló:", e)

    bot._hospital_sync_todo = _sync_todo
    return bot


bot = _cargar(globals())
