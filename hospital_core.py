# -*- coding: utf-8 -*
"""hospital_core.py — núcleo + módulos + sync FIABLE."""
from __future__ import annotations

import asyncio
import re
import traceback
import urllib.request

import discord
from discord import app_commands, ui
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

# Se eliminan siempre (poco uso / redundantes) para hacer sitio
_ELIMINAR_SIEMPRE = (
    "ooc_advertencia",
    "ooc_kick",
    "ooc_ban",
    "ooc_timeout",
    "citatorio_admin",
    "citatorio_disciplina",
    "citatorio_general",
    "carta_solicitud",
    "reporte_procedimiento",
    "solicitud_degrado",
    "solicitud_descargo",
    "quejas_pendientes",
    "queja_resolver",
    "marcar_asistencia",
    "asignar_tarea",
    "convocar_reunion_departamento",
    "historial_advertencias",
    "historial_financiero",
    "libro_contable",
    "registrar_gasto",
    "registrar_ingreso",
    "mi_sanciones",
    "catalogo_tienda",
    "panel_reglas",
    "reglas",
    "ver_canal_logs_tickets",
    "configurar_logs_tickets",
    "panel_solicitudes_logs",
    "configurar_canal_logs",
    "solicitud_info",
)

_CRITICOS = {
    "certificar", "registrar_firma", "ver_mi_firma",
    "limpiar", "limpiar_todo", "sincronizar_comandos",
    "panel_solicitudes", "configurar_roles", "otorgar_key",
    "tienda", "sancionar", "expediente",
}


def _cargar(module_globals: dict):
    print("[hospital_core] Descargando núcleo…")
    with urllib.request.urlopen(_URL, timeout=60) as resp:
        source = resp.read().decode("utf-8")
    print(f"[hospital_core] Núcleo: {len(source)} bytes")

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
        if bot_control.get_mode() == "offline":
            bot_control.set_mode("online", "Bot reiniciado y operativo.", None)
        await bot_control.publicar_estado(bot)
    except Exception as _e:
        print("[on_ready] bot_control:", _e)
    fn = getattr(bot, "_hospital_sync_todo", None)
    if callable(fn):
        try:
            await asyncio.sleep(2)
            names = await fn("on_ready")
            print(f"[on_ready] Sync OK: {len(names or [])} comandos")
        except Exception as _e:
            print("[on_ready] Sync falló:", _e)
'''

    m = on_ready_pattern.search(source)
    if m:
        source = source[: m.start()] + new_on_ready + source[m.end() :]
        print("[hospital_core] ✓ on_ready reemplazado")
    else:
        source = source.replace("bot.tree.clear_commands(guild=None)", "pass")
        source = source.replace(
            "await bot.tree.sync()  # publica árbol vacío a nivel global (quita duplicados viejos)",
            "pass",
        )

    marker = "if not config.TOKEN:"
    idx = source.find(marker)
    if idx > 0:
        source = source[:idx]

    print("[hospital_core] Ejecutando núcleo…")
    try:
        exec(compile(source, "hospital_core_remote.py", "exec"), module_globals)
    except Exception:
        traceback.print_exc()
        raise

    bot = module_globals.get("bot")
    if bot is None:
        raise RuntimeError("bot no definido")

    # ── Módulos ──────────────────────────────────────────────────
    print("[hospital_core] Registrando módulos…")
    for name in _MODULOS:
        try:
            mod = __import__(name)
            if hasattr(mod, "registrar"):
                mod.registrar(bot)
                print(f"[hospital_core] ✓ {name}")
        except Exception:
            print(f"[hospital_core] ✗ {name}")
            traceback.print_exc()

    # ── FORZAR comandos de certificado (aunque fallen los módulos) ──
    def _forzar_comandos_certificado():
        for n in ("certificar", "registrar_firma", "ver_mi_firma"):
            try:
                bot.tree.remove_command(n)
            except Exception:
                pass

        @bot.tree.command(name="certificar", description="Certificado RP: formulario → autorización Director Investigación y Docencia")
        @app_commands.describe(usuario="Quién recibe el certificado")
        async def cmd_certificar(inter: discord.Interaction, usuario: discord.Member):
            # Reutilizar lógica del módulo si está
            try:
                import capacitacion_cert_ui as ccu
                if not ccu._puede_iniciar(inter.user):
                    return await inter.response.send_message(
                        "❌ Sin permiso para certificar.", ephemeral=True
                    )
                await inter.response.send_modal(ccu.ModalCertificar(bot, usuario))
            except Exception as e:
                print("[certificar] fallback error:", e)
                await inter.response.send_message(
                    f"❌ Error al abrir formulario: `{e}`", ephemeral=True
                )

        @bot.tree.command(name="registrar_firma", description="Registra tu firma digitalizada (imagen PNG/JPG)")
        @app_commands.describe(
            imagen="Imagen de tu firma",
            cargo="Cargo de la firma",
        )
        @app_commands.choices(cargo=[
            app_commands.Choice(name="Director de Investigación y Docencia", value="DIRECTOR_DOCENCIA"),
            app_commands.Choice(name="Director Médico", value="DIRECTOR_MEDICO"),
            app_commands.Choice(name="Director Administrativo", value="DIRECTOR_ADMINISTRATIVO"),
            app_commands.Choice(name="Director de RRHH", value="DIRECTOR_RRHH"),
            app_commands.Choice(name="Director General", value="DIRECTOR_GENERAL"),
            app_commands.Choice(name="Encargado / Instructor", value="ENCARGADO"),
            app_commands.Choice(name="Otra firma personal", value="PERSONAL"),
        ])
        async def cmd_registrar_firma(
            inter: discord.Interaction,
            imagen: discord.Attachment,
            cargo: app_commands.Choice[str],
        ):
            try:
                import firmas
                if not imagen.content_type or not imagen.content_type.startswith("image/"):
                    return await inter.response.send_message("❌ Debe ser imagen.", ephemeral=True)
                key = cargo.value
                if key not in ("ENCARGADO", "PERSONAL") and not firmas._es_key(inter.user, key, "OWNER"):
                    return await inter.response.send_message(
                        f"❌ No tienes el cargo **{cargo.name}**.", ephemeral=True
                    )
                await inter.response.defer(ephemeral=True)
                fname = await firmas.descargar_firma(imagen, inter.user.id)
                firmas.guardar_firma(inter.user.id, key, fname)
                await inter.followup.send(
                    f"✅ Firma registrada como **{cargo.name}** (`{fname}`).",
                    ephemeral=True,
                )
            except Exception as e:
                print("[registrar_firma]", e)
                if inter.response.is_done():
                    await inter.followup.send(f"❌ `{e}`", ephemeral=True)
                else:
                    await inter.response.send_message(f"❌ `{e}`", ephemeral=True)

        @bot.tree.command(name="ver_mi_firma", description="Muestra tu firma digitalizada")
        async def cmd_ver_mi_firma(inter: discord.Interaction):
            try:
                import firmas
                import os
                reg = firmas.obtener_firma_usuario(inter.user.id)
                if not reg:
                    return await inter.response.send_message(
                        "Sin firma. Usa `/registrar_firma`.", ephemeral=True
                    )
                path = firmas.ruta_firma(reg["file"])
                if not os.path.isfile(path):
                    return await inter.response.send_message("Archivo no encontrado.", ephemeral=True)
                await inter.response.send_message(
                    file=discord.File(path, filename=reg["file"]),
                    ephemeral=True,
                )
            except Exception as e:
                await inter.response.send_message(f"❌ `{e}`", ephemeral=True)

        print("[hospital_core] ✓ FORZADOS: /certificar /registrar_firma /ver_mi_firma")

    _forzar_comandos_certificado()

    def _listar():
        return sorted({c.name for c in bot.tree.get_commands()})

    def _limpiar_arbol():
        # Borrar comandos inútiles siempre
        for n in _ELIMINAR_SIEMPRE:
            try:
                bot.tree.remove_command(n)
            except Exception:
                pass
        names = _listar()
        print(f"[hospital_core] Tras limpiar inútiles: {len(names)}")
        if len(names) <= _MAX_SLASH:
            return names
        # Recorte extra
        for n in list(names):
            if len(_listar()) <= _MAX_SLASH:
                break
            if n in _CRITICOS:
                continue
            try:
                bot.tree.remove_command(n)
            except Exception:
                pass
        final = _listar()
        print(f"[hospital_core] Tras recorte: {len(final)} → {final}")
        return final

    _limpiar_arbol()

    async def _sync_todo(reason: str = "") -> list:
        result = []
        print(f"[hospital_core] === SYNC ({reason}) ===")
        # Re-forzar por si algo los borró
        names_now = _listar()
        if "certificar" not in names_now or "registrar_firma" not in names_now:
            print("[hospital_core] Re-inyectando comandos certificado…")
            _forzar_comandos_certificado()
        _limpiar_arbol()
        try:
            # Vaciar globales (evitar duplicados)
            try:
                app_id = bot.application_id
                if app_id is None:
                    app_id = (await bot.application_info()).id
                await bot.http.bulk_upsert_global_commands(int(app_id), [])
            except Exception as e:
                print("[hospital_core] vaciar globales:", e)

            targets = list(bot.guilds) if bot.guilds else [discord.Object(id=_GUILD_ID)]
            for g in targets:
                gid = int(getattr(g, "id", _GUILD_ID))
                obj = discord.Object(id=gid)
                try:
                    bot.tree.copy_global_to(guild=obj)
                    synced = await bot.tree.sync(guild=obj)
                    result = sorted(c.name for c in synced)
                    print(f"[hospital_core] GUILD {gid}: {len(result)}")
                    for need in ("certificar", "registrar_firma", "ver_mi_firma"):
                        print(f"[hospital_core]   {need}: {'SÍ' if need in result else 'NO'}")
                except Exception as e:
                    print(f"[hospital_core] sync guild {gid}:", e)
                    traceback.print_exc()
        except Exception as e:
            print("[hospital_core] sync:", e)
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
            await ctx.reply("❌ Solo admin.")
            return
        m = await ctx.reply("🔄 Sync…")
        names = await _sync_todo("!forzar_sync")
        ok = [c for c in ("certificar", "registrar_firma", "ver_mi_firma") if c in names]
        await m.edit(
            content=(
                f"✅ **{len(names)}** comandos.\n"
                f"Certificados: `{', '.join(ok) or 'FALTAN'}`\n"
                f"Prueba `/certificar` y `/registrar_firma`."
            )
        )

    @bot.listen("on_ready")
    async def _hc_backup():
        if getattr(bot, "_hc_backup_done", False):
            return
        bot._hc_backup_done = True
        await asyncio.sleep(5)
        try:
            await _sync_todo("backup")
        except Exception as e:
            print("[hospital_core] backup:", e)

    return bot


bot = _cargar(globals())
