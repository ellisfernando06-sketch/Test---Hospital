# -*- coding: utf-8 -*
"""hospital_core.py — arranque estable con reintentos y módulos aislados."""
from __future__ import annotations

import asyncio
import importlib
import sys
import traceback
import urllib.request
from types import ModuleType

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
    "bot_control",
)

_QUITAR = (
    "ordenar_roles", "mi_expediente", "expediente", "historial_advertencias",
    "mi_sanciones", "solicitud_info", "catalogo_tienda",
    "ver_canal_logs_tickets", "configurar_logs_tickets", "panel_solicitudes_logs",
    "configurar_canal_logs", "libro_contable", "registrar_gasto", "registrar_ingreso",
    "ooc_advertencia", "ooc_kick", "ooc_timeout", "carta_solicitud",
    "reporte_procedimiento", "solicitud_degrado", "solicitud_descargo",
    "quejas_pendientes", "queja_resolver", "marcar_asistencia", "ver_roblox",
    "votacion", "organigrama", "estado_hospital", "formulario", "documento_medico",
    "reporte_departamento", "solicitud_investigacion", "solicitud_permiso",
    "mis_certificados", "mostrar_certificado", "ver_certificados", "crear_certificado",
    "mi_inventario", "panel_tienda",
)

_BAJA = (
    "sancion_interna", "advertencia", "transferir_departamento", "descenso",
    "ascenso", "suspender", "reincorporar", "pagar_salario", "depositar",
    "retirar", "transferir", "solicitud_general", "queja", "asignar_tarea",
    "panel_acciones", "panel_estado",
)


def _fetch() -> str:
    req = urllib.request.Request(_URL, headers={"User-Agent": "HospitalBot/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")


def _cargar_modulos(bot: commands.Bot) -> None:
    for nombre in _MODULOS:
        try:
            mod = importlib.import_module(nombre)
            if hasattr(mod, "registrar") and callable(mod.registrar):
                mod.registrar(bot)
                print(f"[hospital_core] OK {nombre}", flush=True)
            else:
                print(f"[hospital_core] sin registrar: {nombre}", flush=True)
        except Exception:
            print(f"[hospital_core] FALLO {nombre}:", flush=True)
            traceback.print_exc()


def _limpiar_tree(bot: commands.Bot) -> None:
    try:
        for c in list(bot.tree.get_commands()):
            if c.name in _QUITAR or c.name in _BAJA:
                try:
                    bot.tree.remove_command(c.name)
                except Exception:
                    pass
    except Exception:
        pass


async def _sync(bot: commands.Bot) -> list:
    _limpiar_tree(bot)
    names = []
    try:
        g = discord.Object(id=_GUILD_ID)
        bot.tree.copy_global_to(guild=g)
        synced = await bot.tree.sync(guild=g)
        names = [c.name for c in synced]
        print(f"[hospital_core] sync guild {len(names)}", flush=True)
    except Exception as e:
        print("[hospital_core] sync guild error:", e, flush=True)
        try:
            synced = await bot.tree.sync()
            names = [c.name for c in synced]
            print(f"[hospital_core] sync global {len(names)}", flush=True)
        except Exception as e2:
            print("[hospital_core] sync global error:", e2, flush=True)
    return names


def _cargar(g: dict):
    src = _fetch()
    ns = dict(g)
    ns["__name__"] = "Bot_Hospital_remote"
    exec(compile(src, "Bot_Hospital_remote.py", "exec"), ns)

    bot = ns.get("bot")
    if bot is None:
        for v in ns.values():
            if isinstance(v, commands.Bot):
                bot = v
                break
    if bot is None:
        raise RuntimeError("No se encontró bot en el núcleo remoto")

    # Inyectar símbolos útiles al módulo hospital_core
    g["bot"] = bot
    for k, v in ns.items():
        if k.startswith("_"):
            continue
        if k not in g:
            g[k] = v

    original_setup = getattr(bot, "setup_hook", None)

    async def setup_hook():
        if original_setup:
            r = original_setup()
            if asyncio.iscoroutine(r):
                await r
        _cargar_modulos(bot)
        await _sync(bot)

    bot.setup_hook = setup_hook  # type: ignore

    @bot.command(name="forzar_sync")
    async def forzar_sync(ctx):
        if not ctx.author.guild_permissions.administrator:
            return
        msg = await ctx.reply("🔄 Sync…")
        try:
            names = await _sync(bot)
            await msg.edit(content=f"✅ {len(names)} comandos")
        except Exception as e:
            await msg.edit(content=f"❌ {e}")

    @bot.listen("on_ready")
    async def _backup_sync():
        if getattr(bot, "_hc_backup_done", False):
            return
        bot._hc_backup_done = True
        await asyncio.sleep(5)
        try:
            await _sync(bot)
        except Exception as e:
            print("[hospital_core] backup sync:", e, flush=True)

    print("[hospital_core] LISTO", flush=True)
    return bot


bot = _cargar(globals())
