# -*- coding: utf-8 -*-
"""hospital_core.py — arranque estable con reintentos y módulos aislados."""
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
_MAX_SLASH = 98

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
)

_QUITAR = (
    "ordenar_roles",
    "mi_expediente",
    "expediente",
    "historial_advertencias",
    "mi_sanciones",
    "solicitud_info",
    "panel_reglas",
    "reglas",
    "catalogo_tienda",
    "bienvenida",
    "ver_canal_logs_tickets",
    "configurar_logs_tickets",
    "panel_solicitudes_logs",
    "configurar_canal_logs",
    "libro_contable",
    "registrar_gasto",
    "registrar_ingreso",
    "ooc_advertencia",
    "ooc_kick",
    "ooc_timeout",
    "carta_solicitud",
    "reporte_procedimiento",
    "solicitud_degrado",
    "solicitud_descargo",
    "quejas_pendientes",
    "queja_resolver",
    "marcar_asistencia",
    "ver_roblox",
    "votacion",
    "organigrama",
    "estado_hospital",
    "formulario",
    "documento_medico",
    "reporte_departamento",
    "solicitud_investigacion",
    "solicitud_permiso",
    "mis_certificados",
    "mostrar_certificado",
    "ver_certificados",
    "crear_certificado",
    "mi_inventario",
    "panel_tienda",
)

_BAJA = (
    "sancion_interna",
    "advertencia",
    "transferir_departamento",
    "descenso",
    "ascenso",
    "suspender",
    "reincorporar",
    "pagar_salario",
    "depositar",
    "retirar",
    "transferir",
    "solicitud_general",
    "queja",
    "asignar_tarea",
    "panel_acciones",
    "panel_estado",
)

_CRITICOS = {
    "certificar", "registrar_firma", "ver_mi_firma",
    "limpiar", "limpiar_todo", "sincronizar_comandos",
    "panel_solicitudes", "configurar_roles", "otorgar_key", "bootstrap_owner",
    "tienda", "sancionar", "capacitacion",
    "balance", "balance_general", "historial_financiero",
    "ooc_ban", "sancion_aplicar",
    "solicitar_insumo", "cap_historial",
    "convocar_directores", "convocar_reunion_departamento",
    "citatorio_general", "citatorio_disciplina", "citatorio_admin",
    "abrir_expediente",
    "mis_otorgados",
    "licencia",
    "paciente", "inventario", "turno", "codigo", "ficha", "postulacion",
}


def _fetch(url: str, intentos: int = 6) -> str:
    ultimo = None
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "HospitalBot/1.0"})
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            ultimo = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"No se pudo descargar el núcleo: {ultimo}")


def _cargar_modulo(bot: commands.Bot, nombre: str) -> None:
    try:
        mod = __import__(nombre)
        if hasattr(mod, "registrar") and callable(mod.registrar):
            mod.registrar(bot)
            print(f"[hospital_core] módulo OK: {nombre}")
        else:
            print(f"[hospital_core] módulo sin registrar(): {nombre}")
    except Exception:
        print(f"[hospital_core] FALLO módulo {nombre}:")
        traceback.print_exc()


async def _setup_hook_extra(bot: commands.Bot) -> None:
    for nombre in _MODULOS:
        _cargar_modulo(bot, nombre)


def _parche_tree(bot: commands.Bot) -> None:
    """Quita comandos duplicados / de baja para no saturar el límite de slash."""
    try:
        cmds = list(bot.tree.get_commands())
    except Exception:
        return
    nombres = {c.name for c in cmds}
    for n in list(nombres):
        if n in _QUITAR or n in _BAJA:
            try:
                bot.tree.remove_command(n)
            except Exception:
                pass


async def _sync_seguro(bot: commands.Bot) -> None:
    _parche_tree(bot)
    try:
        guild = discord.Object(id=_GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"[hospital_core] sync guild OK: {len(synced)} comandos")
    except Exception:
        print("[hospital_core] sync guild falló, intentando global…")
        traceback.print_exc()
        try:
            synced = await bot.tree.sync()
            print(f"[hospital_core] sync global OK: {len(synced)}")
        except Exception:
            traceback.print_exc()


def main() -> None:
    src = _fetch(_URL)
    # Ejecutar núcleo remoto en namespace local
    ns: dict = {"__name__": "__bot_hospital_core__"}
    exec(compile(src, "Bot_Hospital_remote.py", "exec"), ns)

    bot = ns.get("bot") or ns.get("client")
    if bot is None:
        # Buscar instancia Bot en el namespace
        for v in ns.values():
            if isinstance(v, commands.Bot):
                bot = v
                break
    if bot is None:
        raise RuntimeError("No se encontró la instancia Bot en el núcleo")

    original_setup = getattr(bot, "setup_hook", None)

    async def setup_hook():
        if original_setup:
            res = original_setup()
            if asyncio.iscoroutine(res):
                await res
        await _setup_hook_extra(bot)
        await _sync_seguro(bot)

    bot.setup_hook = setup_hook  # type: ignore

    token = None
    try:
        import config as cfg

        token = getattr(cfg, "TOKEN", None)
    except Exception:
        pass
    if not token:
        import os

        token = os.getenv("TOKEN") or os.getenv("DISCORD_TOKEN") or os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("TOKEN no configurado")

    print("[hospital_core] arrancando bot…")
    bot.run(token)


if __name__ == "__main__":
    main()
