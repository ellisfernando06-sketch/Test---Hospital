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

    # ── Anular por completo el bloque de sync del on_ready remoto ──
    # Ese bloque hacía clear global + sync vacío y dejaba Discord sin comandos.
    old_sync_block = '''    # global. Si se limpia primero (clear_commands(guild=None)), copy_global_to
    # no tiene nada que copiar y el servidor se queda sin slash commands.
        MI_SERVIDOR = discord.Object(id=1381360019467014184)
        bot.tree.copy_global_to(guild=MI_SERVIDOR)  # copia mientras el global aún tiene comandos
        sincronizados_guild = await bot.tree.sync(guild=MI_SERVIDOR)
        bot.tree.clear_commands(guild=None)  # limpia registro global en memoria
        await bot.tree.sync()  # publica árbol vacío a nivel global (quita duplicados viejos)'''

    new_sync_block = '''    # [hospital_core] Sync gestionado fuera del núcleo remoto
        pass'''

    if old_sync_block in source:
        source = source.replace(old_sync_block, new_sync_block)
        print("[hospital_core] Bloque sync remoto anulado (match exacto)")
    else:
        # Fallback por líneas sueltas
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
        # No tocar sync(guild=...) del remoto si existiera; lo rehacemos nosotros
        print("[hospital_core] Parches de sync aplicados (fallback)")

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

    # ── Registrar módulos locales ──
    print("[hospital_core] Registrando módulos…")
    ok_mods = []
    fail_mods = []
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

    print(f"[hospital_core] Módulos OK: {ok_mods}")
    if fail_mods:
        print(f"[hospital_core] Módulos FALLIDOS: {fail_mods}")

    try:
        glob_names = sorted({c.name for c in bot.tree.get_commands()})
        print(f"[hospital_core] Comandos en memoria: {len(glob_names)}")
        print("[hospital_core]", ", ".join(glob_names) if glob_names else "(ninguno)")
    except Exception as e:
        print("[hospital_core] listar:", e)

    async def _sync_todo(reason: str = "") -> list:
        """Publica todos los slash commands en cada servidor del bot."""
        all_names: list = []
        try:
            # 1) Sync global (puede tardar en propagarse en clientes Discord)
            try:
                synced_global = await bot.tree.sync()
                print(f"[hospital_core] Sync GLOBAL ({reason}): {len(synced_global)}")
            except Exception as e:
                print(f"[hospital_core] Sync GLOBAL falló ({reason}):", e)

            # 2) Sync por guild (aparece al instante)
            guilds = list(bot.guilds) if bot.guilds else []
            if not guilds:
                # Fallback al ID conocido
                guilds_objs = [discord.Object(id=_GUILD_ID)]
            else:
                guilds_objs = guilds

            for g in guilds_objs:
                gid = getattr(g, "id", None) or _GUILD_ID
                obj = discord.Object(id=int(gid))
                try:
                    bot.tree.copy_global_to(guild=obj)
                    synced = await bot.tree.sync(guild=obj)
                    names = sorted(c.name for c in synced)
                    all_names = names
                    print(
                        f"[hospital_core] Sync GUILD {gid} ({reason}): "
                        f"{len(names)} → {', '.join(names[:40])}{'…' if len(names) > 40 else ''}"
                    )
                except Exception as e:
                    print(f"[hospital_core] Sync GUILD {gid} falló ({reason}):", e)
                    traceback.print_exc()
        except Exception as e:
            print(f"[hospital_core] _sync_todo error ({reason}):", e)
            traceback.print_exc()
        return all_names

    # Prefijo de emergencia (siempre disponible sin sync de Discord)
    @bot.command(name="forzar_sync")
    async def forzar_sync_cmd(ctx: commands.Context):
        """!forzar_sync — republica todos los slash commands."""
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return
        if not (
            ctx.author.guild_permissions.administrator
            or ctx.author.id == ctx.guild.owner_id
        ):
            await ctx.send("❌ Solo administrador o dueño del servidor.")
            return
        msg = await ctx.send("🔄 Sincronizando comandos…")
        try:
            names = await _sync_todo("manual-prefix")
            await msg.edit(
                content=(
                    f"✅ **{len(names)}** comandos publicados.\n"
                    f"`{'`, `'.join(names[:50])}`"
                    + ("…" if len(names) > 50 else "")
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
            print(f"[hospital_core] Arranque terminado: {len(names)} comandos")
        except Exception as e:
            print("[hospital_core] Sync arranque falló:", e)
            traceback.print_exc()
        await asyncio.sleep(8)
        try:
            await _sync_todo("reintento")
        except Exception as e:
            print("[hospital_core] Sync reintento falló:", e)

    bot._hospital_sync_todo = _sync_todo
    return bot


bot = _cargar(globals())
