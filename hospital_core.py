# -*- coding: utf-8 -*
"""hospital_core.py — arranque estable anti-crash."""
from __future__ import annotations

import asyncio
import re
import traceback
import urllib.request

import discord
from discord import app_commands
from discord.ext import commands

_COMMIT = "30a15578af8c1459b0d2dcad8af2881c4a8a326b"
_URL = (
    "https://raw.githubusercontent.com/ellisfernando06-sketch/Test---Hospital/"
    f"{_COMMIT}/Bot_Hospital.py"
)
_GUILD_ID = 1381360019467014184
_MAX_SLASH = 100

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
)

_QUITAR = ("ordenar_roles",)

_BAJA = (
    "ver_canal_logs_tickets", "configurar_logs_tickets", "panel_solicitudes_logs",
    "configurar_canal_logs", "catalogo_tienda", "panel_reglas", "reglas",
    "solicitud_info", "mi_sanciones", "historial_advertencias", "historial_financiero",
    "libro_contable", "registrar_gasto", "registrar_ingreso",
    "ooc_advertencia", "ooc_kick", "ooc_ban", "ooc_timeout",
    "citatorio_admin", "citatorio_disciplina", "citatorio_general",
    "carta_solicitud", "reporte_procedimiento", "solicitud_degrado", "solicitud_descargo",
    "quejas_pendientes", "queja_resolver", "marcar_asistencia", "asignar_tarea",
    "convocar_reunion_departamento",
)

_CRITICOS = {
    "certificar", "registrar_firma", "ver_mi_firma",
    "limpiar", "limpiar_todo", "sincronizar_comandos",
    "panel_solicitudes", "configurar_roles", "otorgar_key", "bootstrap_owner",
    "tienda", "sancionar", "expediente", "capacitacion",
}


def _cargar(module_globals: dict):
    print("[hospital_core] Descargando núcleo…", flush=True)
    with urllib.request.urlopen(_URL, timeout=90) as resp:
        source = resp.read().decode("utf-8")
    print(f"[hospital_core] Núcleo {len(source)} bytes", flush=True)

    on_ready_pattern = re.compile(
        r"@bot\.event\s*\nasync def on_ready\(\):\n"
        r"(?:.*\n)*?"
        r"(?=\n# -{5,}|\n@bot\.tree\.error|\n@bot\.tree\.command)",
        re.MULTILINE,
    )

    new_on_ready = '''@bot.event
async def on_ready():
    try:
        bot.add_view(AbrirTicketView())
        bot.add_view(CerrarTicketView())
        bot.add_view(PanelAccionesView())
        bot.add_view(PanelEstadoView())
        bot.add_view(AprobacionView(key_aprobador="DIRECTOR_RRHH", solicitud_id="persist"))
    except Exception as _e:
        print("[on_ready] vistas:", _e)
    try:
        import verificacion as _verif
        bot.add_view(_verif.VerificarView(staff_id=0, guild_id=0))
    except Exception as _e:
        print("[on_ready] VerificarView:", _e)
    print(f"Conectado como {bot.user} (ID: {bot.user.id})")
    try:
        bot_control.set_mode("online", "Bot reiniciado y operativo.", None)
        await bot_control.publicar_estado(bot)
        print("[on_ready] ONLINE")
    except Exception as _e:
        print("[on_ready] bot_control:", _e)
    fn = getattr(bot, "_hospital_sync_todo", None)
    if callable(fn):
        try:
            await asyncio.sleep(2)
            names = await fn("on_ready")
            print(f"[on_ready] Sync: {len(names or [])} comandos")
        except Exception as _e:
            print("[on_ready] Sync error:", _e)
'''

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

    try:
        source = re.sub(
            r"@bot\.tree\.command\(name=\"ordenar_roles\"[^\n]*\n"
            r"(?:@[^\n]+\n)*"
            r"async def ordenar_roles_cmd\([\s\S]*?\n(?=@bot\.|def |async def |class )",
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
        print("[hospital_core] ERROR núcleo:", flush=True)
        traceback.print_exc()
        raise

    bot = module_globals.get("bot")
    if bot is None:
        raise RuntimeError("bot no definido tras exec")

    for n in _QUITAR:
        try:
            bot.tree.remove_command(n)
        except Exception:
            pass

    print("[hospital_core] Módulos…", flush=True)
    for name in _MODULOS:
        try:
            mod = __import__(name)
            if hasattr(mod, "registrar"):
                mod.registrar(bot)
            print(f"[hospital_core] ✓ {name}", flush=True)
        except Exception:
            print(f"[hospital_core] ✗ {name} (se continúa)", flush=True)
            traceback.print_exc()

    # Comandos críticos solo si faltan (sin pisar)
    try:
        names = {c.name for c in bot.tree.get_commands()}
    except Exception:
        names = set()

    if "registrar_firma" not in names:
        try:
            @bot.tree.command(name="registrar_firma", description="Registra tu firma digitalizada")
            @app_commands.describe(imagen="Imagen de firma", cargo="Cargo")
            @app_commands.choices(cargo=[
                app_commands.Choice(name="Director de Investigación y Docencia", value="DIRECTOR_DOCENCIA"),
                app_commands.Choice(name="Director Médico", value="DIRECTOR_MEDICO"),
                app_commands.Choice(name="Director Administrativo", value="DIRECTOR_ADMINISTRATIVO"),
                app_commands.Choice(name="Director de RRHH", value="DIRECTOR_RRHH"),
                app_commands.Choice(name="Director General", value="DIRECTOR_GENERAL"),
                app_commands.Choice(name="Encargado / Instructor", value="ENCARGADO"),
                app_commands.Choice(name="Otra firma personal", value="PERSONAL"),
            ])
            async def registrar_firma(inter: discord.Interaction, imagen: discord.Attachment, cargo: app_commands.Choice[str]):
                try:
                    import firmas
                    if not imagen.content_type or not str(imagen.content_type).startswith("image/"):
                        return await inter.response.send_message("❌ Debe ser imagen.", ephemeral=True)
                    key = cargo.value
                    if key not in ("ENCARGADO", "PERSONAL") and not firmas._es_key(inter.user, key, "OWNER"):
                        return await inter.response.send_message("❌ Sin ese cargo.", ephemeral=True)
                    await inter.response.defer(ephemeral=True)
                    fname = await firmas.descargar_firma(imagen, inter.user.id)
                    firmas.guardar_firma(inter.user.id, key, fname)
                    await inter.followup.send(f"✅ Firma **{cargo.name}** OK.", ephemeral=True)
                except Exception as e:
                    try:
                        if inter.response.is_done():
                            await inter.followup.send(f"❌ {e}", ephemeral=True)
                        else:
                            await inter.response.send_message(f"❌ {e}", ephemeral=True)
                    except Exception:
                        pass
            print("[hospital_core] + registrar_firma", flush=True)
        except Exception:
            traceback.print_exc()

    if "certificar" not in {c.name for c in bot.tree.get_commands()}:
        try:
            @bot.tree.command(name="certificar", description="Certificado RP con autorización")
            @app_commands.describe(usuario="Receptor del certificado")
            async def certificar(inter: discord.Interaction, usuario: discord.Member):
                try:
                    import capacitacion_cert_ui as ccu
                    if not ccu._puede_iniciar(inter.user):
                        return await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
                    await inter.response.send_modal(ccu.ModalCertificar(bot, usuario))
                except Exception as e:
                    try:
                        await inter.response.send_message(f"❌ {e}", ephemeral=True)
                    except Exception:
                        pass
            print("[hospital_core] + certificar", flush=True)
        except Exception:
            traceback.print_exc()

    def _listar():
        try:
            return sorted({c.name for c in bot.tree.get_commands()})
        except Exception:
            return []

    def _recortar():
        for n in _QUITAR:
            try:
                bot.tree.remove_command(n)
            except Exception:
                pass
        if len(_listar()) <= _MAX_SLASH:
            return _listar()
        for n in _BAJA:
            if len(_listar()) <= _MAX_SLASH:
                break
            if n in _CRITICOS:
                continue
            try:
                bot.tree.remove_command(n)
            except Exception:
                pass
        while len(_listar()) > _MAX_SLASH:
            rest = [n for n in _listar() if n not in _CRITICOS]
            if not rest:
                break
            try:
                bot.tree.remove_command(rest[-1])
            except Exception:
                break
        return _listar()

    try:
        print(f"[hospital_core] Comandos: {len(_recortar())}", flush=True)
    except Exception:
        traceback.print_exc()

    async def _sync_todo(reason: str = "") -> list:
        result = []
        print(f"[hospital_core] SYNC ({reason})", flush=True)
        try:
            _recortar()
        except Exception:
            pass
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
                except Exception as e:
                    print(f"[hospital_core] sync {gid}: {e}", flush=True)
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
        msg = await ctx.reply("🔄 Sync…")
        try:
            names = await _sync_todo("!forzar_sync")
            ok = [c for c in ("registrar_firma", "certificar") if c in names]
            await msg.edit(content=f"✅ {len(names)} comandos. Clave: {', '.join(ok) or '—'}")
        except Exception as e:
            await msg.edit(content=f"❌ {e}")

    @bot.listen("on_ready")
    async def _backup():
        if getattr(bot, "_hc_backup_done", False):
            return
        bot._hc_backup_done = True
        await asyncio.sleep(6)
        try:
            await _sync_todo("backup")
        except Exception as e:
            print("[hospital_core] backup:", e, flush=True)

    print("[hospital_core] LISTO", flush=True)
    return bot


try:
    bot = _cargar(globals())
except Exception:
    print("[hospital_core] FALLO FATAL AL CARGAR:", flush=True)
    traceback.print_exc()
    raise
