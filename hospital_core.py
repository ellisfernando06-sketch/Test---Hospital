# -*- coding: utf-8 -*-
"""hospital_core.py — arranque robusto. Roles y setup prioritarios."""
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

# Críticos primero
_MODULOS_PRIORITARIOS = (
    "roles_comandos",   # /configurar_roles /ordenar_roles /organigrama
    "setup_servidor",
    "limpiar_roles",
    "bienvenida",
)

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
)

# Quitar del núcleo (reemplazados localmente o sin key)
_REEMPLAZADOS_POR_LOCAL = (
    "licencia",
    "despedir",
    "anuncio",
    "votacion",
    "formulario",
    "catalogo_tienda",
    "configurar_roles",
    "ordenar_roles",
    "organigrama",
)

_QUITAR_DEL_TREE = (
    "votacion",
    "formulario",
    "catalogo_tienda",
    "configurar_roles",
    "ordenar_roles",
    "organigrama",
)

_QUITAR_EXTRA_SI_FALTA_SETUP = (
    "balance",
    "mi_inventario",
    "historial_financiero",
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


def _listar_nombres(bot) -> list:
    try:
        return sorted({c.name for c in bot.tree.get_commands()})
    except Exception:
        return []


def _quitar_cmd(bot, name: str) -> None:
    try:
        bot.tree.remove_command(name)
        print(f"[hospital_core] liberado: /{name}", flush=True)
    except Exception:
        pass


def _cargar_modulo(bot, name: str) -> bool:
    try:
        mod = __import__(name)
        if hasattr(mod, "registrar"):
            mod.registrar(bot)
        print(f"[hospital_core] ✓ {name}", flush=True)
        return True
    except Exception:
        print(f"[hospital_core] ✗ {name} (ignorado)", flush=True)
        traceback.print_exc()
        return False


def _asegurar_criticos(bot) -> None:
    names = _listar_nombres(bot)
    faltan = [c for c in ("setup_servidor", "configurar_roles") if c not in names]
    if not faltan:
        print("[hospital_core] ✅ críticos OK", flush=True)
        return

    print(f"[hospital_core] ⚠️ faltan {faltan} — liberando cupos…", flush=True)
    for cmd in _QUITAR_EXTRA_SI_FALTA_SETUP:
        _quitar_cmd(bot, cmd)

    import sys
    for mod_name in ("roles_comandos", "setup_servidor", "limpiar_roles"):
        if mod_name in sys.modules:
            del sys.modules[mod_name]
        _cargar_modulo(bot, mod_name)

    names = _listar_nombres(bot)
    for c in ("setup_servidor", "configurar_roles", "ordenar_roles", "organigrama"):
        print(f"[hospital_core] {c}={'OK' if c in names else 'FALTA'}", flush=True)


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
            print(f"[hospital_core] núcleo: quitado '{_cmd}'", flush=True)
        except Exception:
            pass

    source = source.replace(
        'description="[Solo primer uso] Te asigna la key OWNER para poder configurar el bot"',
        'description="[Solo primer uso] Te asigna Fundador y Owner"',
    )
    source = source.replace("la key OWNER", "la key Fundador y Owner")
    source = source.replace("Gerente Developer", "Fundador y Owner")

    marker = "if not config.TOKEN:"
    idx = source.find(marker)
    if idx > 0:
        source = source[:idx]

    print("[hospital_core] Exec núcleo…", flush=True)
    try:
        exec(compile(source, "hospital_core_remote.py", "exec"), module_globals)
    except Exception:
        print("[hospital_core] ERROR núcleo:", flush=True)
        traceback.print_exc()
        raise

    bot = module_globals.get("bot")
    if bot is None:
        raise RuntimeError("bot no definido tras exec del núcleo")

    for _cmd in _QUITAR_DEL_TREE:
        _quitar_cmd(bot, _cmd)

    print("[hospital_core] Prioritarios…", flush=True)
    for name in _MODULOS_PRIORITARIOS:
        _cargar_modulo(bot, name)

    print("[hospital_core] Módulos…", flush=True)
    for name in _MODULOS:
        _cargar_modulo(bot, name)

    _asegurar_criticos(bot)

    names = _listar_nombres(bot)
    print(f"[hospital_core] Comandos: {len(names)}", flush=True)
    print(f"[hospital_core] Lista: {', '.join(names)}", flush=True)

    async def _sync_todo(reason: str = "") -> list:
        result = []
        print(f"[hospital_core] SYNC ({reason})", flush=True)
        try:
            try:
                app_id = bot.application_id or (await bot.application_info()).id
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
                    print(f"[hospital_core] guild {gid}: {len(result)}", flush=True)
                    for c in ("configurar_roles", "setup_servidor", "organigrama"):
                        print(
                            f"[hospital_core] {c}={'OK' if c in result else 'FALTA'}",
                            flush=True,
                        )
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
        msg = await ctx.reply("🔄 Sincronizando…")
        try:
            names = await _sync_todo("!forzar_sync")
            checks = []
            for c in ("configurar_roles", "setup_servidor"):
                checks.append(f"{'✅' if c in (names or []) else '❌'} /{c}")
            await msg.edit(
                content=(
                    f"✅ **{len(names)}** comandos.\n"
                    f"{' · '.join(checks)}\n"
                    f"`{', '.join(names[:25])}{'…' if len(names) > 25 else ''}`"
                )
            )
        except Exception as e:
            await msg.edit(content=f"❌ {e}")

    @bot.listen("on_ready")
    async def _backup():
        if getattr(bot, "_hc_backup_done", False):
            return
        bot._hc_backup_done = True
        await asyncio.sleep(4)
        try:
            await _sync_todo("backup")
        except Exception as e:
            print("[hospital_core] backup:", e, flush=True)

    print("[hospital_core] LISTO", flush=True)
    return bot


bot = _cargar(globals())
