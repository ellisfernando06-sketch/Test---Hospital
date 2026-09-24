# -*- coding: utf-8 -*
"""hospital_core.py — núcleo + módulos + sync. Fuerza ONLINE al arrancar."""
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

_QUITAR_SIEMPRE = ("ordenar_roles",)

_BAJA_PRIORIDAD = (
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
    "tienda", "panel_tienda", "mi_inventario",
    "sancionar", "verificar_roblox", "expediente",
    "capacitacion", "crear_certificado", "mis_certificados",
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

    new_on_ready = (
        "@bot.event\n"
        "async def on_ready():\n"
        "    try:\n"
        "        bot.add_view(AbrirTicketView())\n"
        "        bot.add_view(CerrarTicketView())\n"
        "        bot.add_view(PanelAccionesView())\n"
        "        bot.add_view(PanelEstadoView())\n"
        "        bot.add_view(AprobacionView(key_aprobador=\"DIRECTOR_RRHH\", solicitud_id=\"persist\"))\n"
        "    except Exception as _e:\n"
        "        print(\"[on_ready] vistas:\", _e)\n"
        "    try:\n"
        "        import verificacion as _verif\n"
        "        bot.add_view(_verif.VerificarView(staff_id=0, guild_id=0))\n"
        "    except Exception as _e:\n"
        "        print(\"[on_ready] VerificarView:\", _e)\n"
        "    print(f\"Conectado como {bot.user} (ID: {bot.user.id})\")\n"
        "    try:\n"
        "        bot_control.set_mode(\"online\", \"Bot reiniciado y operativo.\", None)\n"
        "        await bot_control.publicar_estado(bot)\n"
        "        print(\"[on_ready] Estado forzado: ONLINE\")\n"
        "    except Exception as _e:\n"
        "        print(\"[on_ready] bot_control:\", _e)\n"
        "    fn = getattr(bot, \"_hospital_sync_todo\", None)\n"
        "    if callable(fn):\n"
        "        try:\n"
        "            await asyncio.sleep(2)\n"
        "            names = await fn(\"on_ready\")\n"
        "            print(f\"[on_ready] Sync OK: {len(names or [])} comandos\")\n"
        "        except Exception as _e:\n"
        "            print(\"[on_ready] Sync falló:\", _e)\n"
    )

    m = on_ready_pattern.search(source)
    if m:
        source = source[: m.start()] + new_on_ready + source[m.end() :]
        print("[hospital_core] ✓ on_ready OK")
    else:
        source = source.replace("bot.tree.clear_commands(guild=None)", "pass")
        source = source.replace(
            "await bot.tree.sync()  # publica árbol vacío a nivel global (quita duplicados viejos)",
            "pass",
        )

    source = re.sub(
        r"@bot\.tree\.command\(name=\"ordenar_roles\"[^\n]*\n"
        r"(?:@[^\n]+\n)*"
        r"async def ordenar_roles_cmd\([\s\S]*?\n(?=@bot\.|def |async def |class )",
        "\n",
        source,
        count=1,
    )

    source = source.replace(
        'description="[Solo primer uso] Te asigna la key OWNER para poder configurar el bot"',
        'description="[Solo primer uso] Te asigna Gerente Developer (máxima autoridad)"',
    )
    source = source.replace("la key OWNER", "la key Gerente Developer")
    source = source.replace("key OWNER configurada", "key Gerente Developer configurada")
    source = source.replace("/configurar_roles una vez (OWNER)", "/configurar_roles una vez (Gerente Developer)")

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

    for n in _QUITAR_SIEMPRE:
        try:
            bot.tree.remove_command(n)
        except Exception:
            pass

    print("[hospital_core] Módulos…")
    for name in _MODULOS:
        try:
            mod = __import__(name)
            if hasattr(mod, "registrar"):
                mod.registrar(bot)
                print(f"[hospital_core] ✓ {name}")
        except Exception:
            print(f"[hospital_core] ✗ {name}")
            traceback.print_exc()

    presentes = {c.name for c in bot.tree.get_commands()}
    if "registrar_firma" not in presentes:
        @bot.tree.command(name="registrar_firma", description="Registra tu firma digitalizada (imagen PNG/JPG)")
        @app_commands.describe(imagen="Imagen de tu firma", cargo="Cargo de la firma")
        @app_commands.choices(cargo=[
            app_commands.Choice(name="Director de Investigación y Docencia", value="DIRECTOR_DOCENCIA"),
            app_commands.Choice(name="Director Médico", value="DIRECTOR_MEDICO"),
            app_commands.Choice(name="Director Administrativo", value="DIRECTOR_ADMINISTRATIVO"),
            app_commands.Choice(name="Director de RRHH", value="DIRECTOR_RRHH"),
            app_commands.Choice(name="Director General", value="DIRECTOR_GENERAL"),
            app_commands.Choice(name="Encargado / Instructor", value="ENCARGADO"),
            app_commands.Choice(name="Otra firma personal", value="PERSONAL"),
        ])
        async def _cmd_reg_firma(inter: discord.Interaction, imagen: discord.Attachment, cargo: app_commands.Choice[str]):
            try:
                import firmas
                if not imagen.content_type or not imagen.content_type.startswith("image/"):
                    return await inter.response.send_message("❌ Debe ser imagen.", ephemeral=True)
                key = cargo.value
                if key not in ("ENCARGADO", "PERSONAL") and not firmas._es_key(inter.user, key, "OWNER"):
                    return await inter.response.send_message(f"❌ No tienes **{cargo.name}**.", ephemeral=True)
                await inter.response.defer(ephemeral=True)
                fname = await firmas.descargar_firma(imagen, inter.user.id)
                firmas.guardar_firma(inter.user.id, key, fname)
                await inter.followup.send(f"✅ Firma **{cargo.name}** registrada.", ephemeral=True)
            except Exception as e:
                if inter.response.is_done():
                    await inter.followup.send(f"❌ `{e}`", ephemeral=True)
                else:
                    await inter.response.send_message(f"❌ `{e}`", ephemeral=True)
        print("[hospital_core] + /registrar_firma")

    if "certificar" not in {c.name for c in bot.tree.get_commands()}:
        @bot.tree.command(name="certificar", description="Certificado RP → autorización Director Investigación y Docencia")
        @app_commands.describe(usuario="Quién recibe el certificado")
        async def _cmd_cert(inter: discord.Interaction, usuario: discord.Member):
            try:
                import capacitacion_cert_ui as ccu
                if not ccu._puede_iniciar(inter.user):
                    return await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
                await inter.response.send_modal(ccu.ModalCertificar(bot, usuario))
            except Exception as e:
                await inter.response.send_message(f"❌ `{e}`", ephemeral=True)
        print("[hospital_core] + /certificar")

    def _nombres():
        return sorted({c.name for c in bot.tree.get_commands()})

    def _recortar():
        for n in _QUITAR_SIEMPRE:
            try:
                bot.tree.remove_command(n)
            except Exception:
                pass
        if len(_nombres()) <= _MAX_SLASH:
            return _nombres()
        for n in _BAJA_PRIORIDAD:
            if len(_nombres()) <= _MAX_SLASH:
                break
            if n in _CRITICOS:
                continue
            try:
                bot.tree.remove_command(n)
            except Exception:
                pass
        while len(_nombres()) > _MAX_SLASH:
            rest = [n for n in _nombres() if n not in _CRITICOS]
            if not rest:
                break
            try:
                bot.tree.remove_command(rest[-1])
            except Exception:
                break
        return _nombres()

    _recortar()

    async def _sync_todo(reason: str = "") -> list:
        result = []
        print(f"[hospital_core] === SYNC ({reason}) ===")
        _recortar()
        try:
            try:
                app_id = bot.application_id or (await bot.application_info()).id
                await bot.http.bulk_upsert_global_commands(int(app_id), [])
            except Exception as e:
                print("[hospital_core] globales:", e)
            targets = list(bot.guilds) if bot.guilds else [discord.Object(id=_GUILD_ID)]
            for g in targets:
                gid = int(getattr(g, "id", _GUILD_ID))
                obj = discord.Object(id=gid)
                try:
                    bot.tree.copy_global_to(guild=obj)
                    synced = await bot.tree.sync(guild=obj)
                    result = sorted(c.name for c in synced)
                    print(f"[hospital_core] GUILD {gid}: {len(result)}")
                except Exception as e:
                    print(f"[hospital_core] sync {gid}: {e}")
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
        msg = await ctx.reply("🔄 Sync…")
        names = await _sync_todo("!forzar_sync")
        ok = [c for c in ("registrar_firma", "certificar", "ver_mi_firma") if c in names]
        await msg.edit(content=f"✅ **{len(names)}** comandos. Firma/cert: `{', '.join(ok) or 'FALTAN'}`")

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

    print("[hospital_core] Listo.")
    return bot


bot = _cargar(globals())
