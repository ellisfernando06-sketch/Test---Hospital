# -*- coding: utf-8 -*-
"""hospital_core.py — Arranque a prueba de fallos."""
from __future__ import annotations

import asyncio
import re
import sys
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

_MODULOS_CRITICOS = (
    "roles_comandos",
    "setup_servidor",
    "setup_permisos_protect",
    "limpiar_roles",
    "bienvenida",
    "canales_direccion",
)

_MODULOS = (
    "comandos_nuevos",
    "centro_solicitudes_ui",
    "verificacion",
    "panel_verificacion",
    "verificacion_cuarentena",
    "paneles_direccion",
    "rp_medico",
    "paneles_miembros",
    "tienda",
    "comunidad",
    "limpiar_canal",
    "entrevista_ui",
    "tickets_cierre",
    "panel_tickets_ui",
    "sanciones",
    "sanciones_apelacion_ui",
    "sanciones_comandos_hook",
    "sancion_comando_unico",
    "hospital_core_patch_sanciones",
    "docencia",
    "canales_direccion",
    "canales_crear",
    "firmas",
    "firmas_cargos_extra",
    "firmas_hook",
    "cert_roles",
    "cert_roles_hook",
    "roles_separadores_auto",
    "cert_plantilla_install",
    "certificado_oficial_ui",
    "cert_postulacion",
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
    "reglamento_hospital",
    "reglamento_menu_fix",
    "despidos",
    "inactividad",
)

_QUITAR_DEL_NUCLEO = (
    "licencia", "despedir", "anuncio",
    "configurar_roles", "ordenar_roles", "organigrama",
    "votacion", "formulario", "catalogo_tienda",
    "balance", "balance_general", "depositar", "retirar",
    "transferir", "pagar_salario", "historial_financiero", "mi_inventario",
)

_CRITICOS_SLASH = (
    "configurar_roles", "ordenar_roles", "organigrama",
    "setup_servidor", "limpiar_roles_viejos",
    "configurar_canal_direccion", "ver_canales_direccion",
    "otorgar_rol_certificado", "certificado_oficial", "postular_certificacion",
    "agregar_canal", "panel_verificacion", "enviar_paneles_direccion",
    "reglamento_hospital", "publicar_reglamento_hospital",
    "agregar_reglamento", "publicar_reglamento", "registrar_firma", "panel_tickets",
    "panel_apelaciones", "estado_sancion", "configurar_log_apelaciones", "sancion",
)


def _descargar_nucleo(intentos: int = 6) -> str:
    ultimo = None
    for i in range(intentos):
        try:
            req = urllib.request.Request(_URL, headers={"User-Agent": "HospitalBot/1.1"})
            with urllib.request.urlopen(req, timeout=45) as r:
                data = r.read().decode("utf-8", errors="replace")
            if len(data) < 500:
                raise RuntimeError("núcleo vacío")
            return data
        except Exception as e:
            ultimo = e
            time.sleep(1.0 * (i + 1))
    raise RuntimeError(f"No se pudo descargar el núcleo: {ultimo}")


def _strip_comando(source: str, name: str) -> str:
    try:
        return re.sub(
            rf"@bot\.tree\.command\(name=\"{re.escape(name)}\"[^\n]*\n"
            r"(?:@[^\n]+\n)*"
            rf"async def \w+\([\s\S]*?\n(?=\n@|\n# |\nif |\nasync def |\ndef )",
            "\n", source, count=1,
        )
    except Exception:
        return source


def _listar(bot) -> list:
    try:
        return sorted({c.name for c in bot.tree.get_commands()})
    except Exception:
        return []


def _quitar_tree(bot, name: str) -> None:
    try:
        bot.tree.remove_command(name)
    except Exception:
        pass


def _cargar_modulo(bot, name: str) -> bool:
    try:
        if name in sys.modules and name in _MODULOS_CRITICOS:
            try:
                del sys.modules[name]
            except Exception:
                pass
        mod = __import__(name)
        if hasattr(mod, "registrar"):
            mod.registrar(bot)
        print(f"[hospital_core] ✓ {name}", flush=True)
        return True
    except Exception as e:
        print(f"[hospital_core] ✗ {name}: {type(e).__name__}: {e}", flush=True)
        return False


def _bot_minimo() -> commands.Bot:
    intents = discord.Intents.default()
    try:
        intents.message_content = True
        intents.members = True
        intents.guilds = True
    except Exception:
        pass
    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        print(f"[hospital_core] Fallback online: {bot.user}", flush=True)
        fn = getattr(bot, "_hospital_sync_todo", None)
        if callable(fn):
            try:
                await asyncio.sleep(2)
                await fn("fallback_ready")
            except Exception as e:
                print("[hospital_core] sync:", e, flush=True)
    return bot


def _asegurar_criticos(bot) -> None:
    names = set(_listar(bot))
    faltan = [c for c in _CRITICOS_SLASH if c not in names]
    if not faltan:
        return
    for mod in _MODULOS_CRITICOS:
        if mod in sys.modules:
            try:
                del sys.modules[mod]
            except Exception:
                pass
        _cargar_modulo(bot, mod)
    for m in (
        "sancion_comando_unico",
        "sanciones_apelacion_ui",
        "sanciones_comandos_hook",
        "panel_tickets_ui",
    ):
        _cargar_modulo(bot, m)


def _instalar_sync(bot) -> None:
    async def _sync_todo(reason: str = "") -> list:
        result = []
        try:
            try:
                app_id = bot.application_id
                if not app_id:
                    info = await bot.application_info()
                    app_id = info.id
                await bot.http.bulk_upsert_global_commands(int(app_id), [])
            except Exception:
                pass
            targets = list(bot.guilds) if bot.guilds else [discord.Object(id=_GUILD_ID)]
            for g in targets:
                gid = int(getattr(g, "id", _GUILD_ID))
                obj = discord.Object(id=gid)
                try:
                    bot.tree.copy_global_to(guild=obj)
                except Exception:
                    pass
                synced = await bot.tree.sync(guild=obj)
                result = sorted(c.name for c in synced)
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
            await msg.edit(content=f"✅ **{len(names)}** comandos.")
        except Exception as e:
            await msg.edit(content=f"❌ {e}")

    @bot.listen("on_ready")
    async def _backup_sync():
        if getattr(bot, "_hc_backup_done", False):
            return
        bot._hc_backup_done = True
        await asyncio.sleep(4)
        try:
            await _sync_todo("backup")
        except Exception:
            pass


def _cargar_nucleo(module_globals: dict):
    source = _descargar_nucleo()
    on_ready_pattern = re.compile(
        r"@bot\.event\s*\nasync def on_ready\(\):\n(?:.*\n)*?(?=\n# -{5,}|\n@bot\.tree\.error|\n@bot\.tree\.command)",
        re.MULTILINE,
    )
    new_on_ready = (
        "@bot.event\nasync def on_ready():\n"
        "    if not getattr(bot, \"_hospital_views_ok\", False):\n"
        "        try:\n"
        "            bot.add_view(AbrirTicketView()); bot.add_view(CerrarTicketView())\n"
        "            bot.add_view(PanelAccionesView()); bot.add_view(PanelEstadoView())\n"
        "            bot.add_view(AprobacionView(key_aprobador=\"DIRECTOR_RRHH\", solicitud_id=\"persist\"))\n"
        "            bot._hospital_views_ok = True\n"
        "        except Exception as _e: print(\"[on_ready] vistas:\", _e)\n"
        "    print(f\"Conectado como {bot.user}\")\n"
        "    try:\n"
        "        bot_control.set_mode(\"online\", \"Bot operativo.\", None)\n"
        "        await bot_control.publicar_estado(bot)\n"
        "    except Exception as _e: print(\"[on_ready] bot_control:\", _e)\n"
        "    fn = getattr(bot, \"_hospital_sync_todo\", None)\n"
        "    if callable(fn):\n"
        "        try:\n"
        "            await asyncio.sleep(2)\n"
        "            await fn(\"on_ready\")\n"
        "        except Exception as _e: print(\"[on_ready] Sync:\", _e)\n"
    )
    m = on_ready_pattern.search(source)
    if m:
        source = source[: m.start()] + new_on_ready + source[m.end() :]
    for cmd in _QUITAR_DEL_NUCLEO:
        source = _strip_comando(source, cmd)
    source = source.replace("Gerente Developer", "Fundador y Owner")
    marker = "if not config.TOKEN:"
    idx = source.find(marker)
    if idx > 0:
        source = source[:idx]
    exec(compile(source, "hospital_core_remote.py", "exec"), module_globals)
    bot = module_globals.get("bot")
    if bot is None:
        raise RuntimeError("bot no definido")
    return bot


def _cargar(module_globals: dict):
    try:
        bot = _cargar_nucleo(module_globals)
    except Exception as e:
        print(f"[hospital_core] Núcleo falló: {e}", flush=True)
        traceback.print_exc()
        bot = _bot_minimo()
        module_globals["bot"] = bot
    for cmd in _QUITAR_DEL_NUCLEO:
        _quitar_tree(bot, cmd)
    for name in _MODULOS_CRITICOS:
        _cargar_modulo(bot, name)
    for name in _MODULOS:
        _cargar_modulo(bot, name)
    _asegurar_criticos(bot)
    _instalar_sync(bot)
    print("[hospital_core] LISTO", flush=True)
    return bot


try:
    bot = _cargar(globals())
except Exception as e:
    print(f"[hospital_core] FATAL: {e}", flush=True)
    traceback.print_exc()
    bot = _bot_minimo()
    for name in _MODULOS_CRITICOS:
        _cargar_modulo(bot, name)
    _instalar_sync(bot)
