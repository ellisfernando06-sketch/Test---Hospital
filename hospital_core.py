# -*- coding: utf-8 -*-
"""hospital_core.py — arranque completo. NO elimina comandos del núcleo."""
from __future__ import annotations

import asyncio
import re
import time
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

# Módulos locales (se suman / sustituyen al núcleo remoto)
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
    "firmas",
    "capacitacion_cert_ui",
    "cert_flujo_interno",
    "cert_dg_fix",
    "capacitacion_postular",
    "mejoras_ui",
    "reuniones_voice",
    "citatorio_acceso",
    "expedientes",
    "roles_otorgados",
    "licencia_medica",
    "anuncios_largos",
    "despidos",
    "inactividad",
    "bienvenida",
    "setup_servidor",  # organigrama + normativas + pedir canales
)

# Solo quitar si el módulo local lo vuelve a registrar (evitar duplicados rotos del remoto)
_REEMPLAZADOS_POR_LOCAL = (
    "licencia",  # licencia_medica
    "despedir",  # despidos
    "anuncio",   # anuncios_largos / mejoras_ui
)


def _descargar_nucleo(intentos: int = 8) -> str:
    ultimo = None
    for i in range(intentos):
        try:
            req = urllib.request.Request(_URL, headers={"User-Agent": "HospitalBot/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            ultimo = e
            time.sleep(1.2 * (i + 1))
    raise RuntimeError(f"No se pudo descargar el núcleo: {ultimo}")


def _cargar(module_globals: dict):
    source = _descargar_nucleo()

    on_ready_pattern = re.compile(
        r"@bot\.event\s*\nasync def on_ready\(\):\n"
        r"(?:.*\n)*?"
        r"(?=\n# -{5,}|\n@bot\.tree\.error|\n@bot\.tree\.command)",
        re.MULTILINE,
    )

    new_on_ready = (
        "@bot.event\n"
        "async def on_ready():\n"
        "    if not getattr(bot, \"_hospital_views_ok\", False):\n"
        "        try:\n"
        "            bot.add_view(AbrirTicketView())\n"
        "            bot.add_view(CerrarTicketView())\n"
        "            bot.add_view(PanelAccionesView())\n"
        "            bot.add_view(PanelEstadoView())\n"
        "            bot.add_view(AprobacionView(key_aprobador=\"DIRECTOR_RRHH\", solicitud_id=\"persist\"))\n"
        "            bot._hospital_views_ok = True\n"
        "        except Exception as _e:\n"
        "            print(\"[on_ready] vistas:\", _e)\n"
        "    try:\n"
        "        import verificacion as _verif\n"
        "        if not getattr(bot, \"_verif_view_ok\", False):\n"
        "            bot.add_view(_verif.VerificarView(staff_id=0, guild_id=0))\n"
        "            bot._verif_view_ok = True\n"
        "    except Exception as _e:\n"
        "        print(\"[on_ready] VerificarView:\", _e)\n"
        "    try:\n"
        "        import capacitacion_postular as _capp\n"
        "        if not getattr(bot, \"_cap_postular_view_ok\", False):\n"
        "            bot.add_view(_capp.PostularCapView())\n"
        "            bot._cap_postular_view_ok = True\n"
        "    except Exception as _e:\n"
        "        print(\"[on_ready] PostularCapView:\", _e)\n"
        "    print(f\"Conectado como {bot.user} (ID: {bot.user.id})\")\n"
        "    try:\n"
        "        bot_control.set_mode(\"online\", \"Bot reiniciado y operativo.\", None)\n"
        "        await bot_control.publicar_estado(bot)\n"
        "        print(\"[on_ready] ONLINE\")\n"
        "    except Exception as _e:\n"
        "        print(\"[on_ready] bot_control:\", _e)\n"
        "    fn = getattr(bot, \"_hospital_sync_todo\", None)\n"
        "    if callable(fn):\n"
        "        try:\n"
        "            await asyncio.sleep(2)\n"
        "            names = await fn(\"on_ready\")\n"
        "            print(f\"[on_ready] Sync: {len(names or [])} comandos\")\n"
        "        except Exception as _e:\n"
        "            print(\"[on_ready] Sync error:\", _e)\n"
    )

    m = on_ready_pattern.search(source)
    if m:
        source = source[: m.start()] + new_on_ready + source[m.end() :]
        print("[hospital_core] on_ready OK", flush=True)
    else:
        source = source.replace("bot.tree.clear_commands(guild=None)", "pass")
        source = source.replace(
            "await bot.tree.sync()  # publica árbol vacío a nivel global (quita duplicados viejos)",
            "pass",
        )

    # Quitar del CÓDIGO fuente solo comandos que el módulo local sustituye
    for _cmd in _REEMPLAZADOS_POR_LOCAL:
        try:
            source = re.sub(
                rf"@bot\.tree\.command\(name=\"{_cmd}\"[^\n]*\n"
                r"(?:@[^\n]+\n)*"
                rf"async def \w+\([\s\S]*?\n(?=\n@|\n# |\nif |\nasync def |\ndef )",
                "\n",
                source,
                count=1,
            )
        except Exception:
            pass

    source = source.replace(
        'description="[Solo primer uso] Te asigna la key OWNER para poder configurar el bot"',
        'description="[Solo primer uso] Te asigna Gerente Developer"',
    )
    source = source.replace("la key OWNER", "la key Gerente Developer")

    marker = "if not config.TOKEN:"
    idx = source.find(marker)
    if idx > 0:
        source = source[:idx]

    print("[hospital_core] Exec núcleo…", flush=True)
    try:
        exec(compile(source, "hospital_core_remote.py", "exec"), module_globals)
    except Exception:
        print("[hospital_core] ERROR al ejecutar núcleo:", flush=True)
        traceback.print_exc()
        raise

    bot = module_globals.get("bot")
    if bot is None:
        raise RuntimeError("bot no definido tras exec del núcleo")

    # Cargar TODOS los módulos locales (añaden / sobrescriben comandos)
    print("[hospital_core] Módulos…", flush=True)
    for name in _MODULOS:
        try:
            mod = __import__(name)
            if hasattr(mod, "registrar"):
                mod.registrar(bot)
            print(f"[hospital_core] ✓ {name}", flush=True)
        except Exception:
            print(f"[hospital_core] ✗ {name} (ignorado)", flush=True)
            traceback.print_exc()

    def _listar():
        try:
            return sorted({c.name for c in bot.tree.get_commands()})
        except Exception:
            return []

    names = _listar()
    print(f"[hospital_core] Comandos en memoria: {len(names)}", flush=True)
    print(f"[hospital_core] Lista: {', '.join(names)}", flush=True)

    async def _sync_todo(reason: str = "") -> list:
        result = []
        print(f"[hospital_core] SYNC ({reason}) — se publican TODOS los comandos", flush=True)
        try:
            try:
                app_id = bot.application_id or (await bot.application_info()).id
                # limpiar solo globales viejos; los de guild se reescriben abajo
                await bot.http.bulk_upsert_global_commands(int(app_id), [])
            except Exception as e:
                print("[hospital_core] globales:", e, flush=True)

            targets = list(bot.guilds) if bot.guilds else [discord.Object(id=_GUILD_ID)]
            for g in targets:
                gid = int(getattr(g, "id", _GUILD_ID))
                try:
                    obj = discord.Object(id=gid)
                    bot.tree.copy_global_to(guild=obj)
                    synced = await bot.tree.sync(guild=obj)
                    result = sorted(c.name for c in synced)
                    print(f"[hospital_core] guild {gid}: {len(result)} comandos", flush=True)
                    print(f"[hospital_core] sync lista: {', '.join(result)}", flush=True)
                except Exception as e:
                    print(f"[hospital_core] sync {gid}: {e}", flush=True)
                    traceback.print_exc()
        except Exception:
            traceback.print_exc()
        return result

    bot._hospital_sync_todo = _sync_todo

    try:
        bot.remove_command("forzar_sync")
    except Exception:
        pass

    @bot.command(name="forzar_sync")
    async def _forzar_sync(ctx: commands.Context):
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return
        if not (ctx.author.guild_permissions.administrator or ctx.author.id == ctx.guild.owner_id):
            return await ctx.reply("❌ Solo admin.")
        msg = await ctx.reply("🔄 Sincronizando TODOS los comandos…")
        try:
            names = await _sync_todo("!forzar_sync")
            await msg.edit(
                content=f"✅ **{len(names)}** comandos sincronizados.\n`{', '.join(names[:40])}{'…' if len(names) > 40 else ''}`"
            )
        except Exception as e:
            await msg.edit(content=f"❌ {e}")

    @bot.listen("on_ready")
    async def _backup():
        if getattr(bot, "_hc_backup_done", False):
            return
        bot._hc_backup_done = True
        await asyncio.sleep(5)
        try:
            await _sync_todo("backup")
        except Exception as e:
            print("[hospital_core] backup:", e, flush=True)

    print("[hospital_core] LISTO — sin recorte de comandos", flush=True)
    return bot


bot = _cargar(globals())
