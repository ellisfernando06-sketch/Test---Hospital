# -*- coding: utf-8 -*
"""hospital_core.py — núcleo + módulos + sync FIABLE (máx 100 slash, sin duplicados)."""
from __future__ import annotations

import asyncio
import re
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
)

_BAJA_PRIORIDAD = (
    "ver_canal_logs_tickets",
    "configurar_logs_tickets",
    "catalogo_tienda",
    "panel_reglas",
    "reglas",
    "solicitud_info",
    "mi_sanciones",
    "historial_advertencias",
    "historial_financiero",
    "libro_contable",
    "registrar_gasto",
    "registrar_ingreso",
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
    "panel_solicitudes_logs",
    "configurar_canal_logs",
)


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
    """Arranque controlado — no vacía comandos del guild."""
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
            import traceback as _tb
            _tb.print_exc()
    else:
        print("[on_ready] _hospital_sync_todo no listo")

'''

    m = on_ready_pattern.search(source)
    if m:
        source = source[: m.start()] + new_on_ready + source[m.end() :]
        print("[hospital_core] ✓ on_ready remoto REEMPLAZADO")
    else:
        print("[hospital_core] ⚠ on_ready no encontrado — parches sueltos")
        source = source.replace("bot.tree.clear_commands(guild=None)", "pass")
        source = source.replace(
            "await bot.tree.sync()  # publica árbol vacío a nivel global (quita duplicados viejos)",
            "pass",
        )

    marker = "if not config.TOKEN:"
    idx = source.find(marker)
    if idx > 0:
        source = source[:idx]

    # ── Patch: /capacitacion certificar genera imagen del diploma ──
    old_cert = (
        '@grupo_capacitacion.command(name="certificar", description="Certifica a un usuario como que completó una capacitación")\n'
        '@app_commands.describe(usuario="Usuario", titulo="Título de la capacitación completada")\n'
        '@require_key("SUPERVISOR", "JEFE_DEPARTAMENTO", "DIRECTOR", "OWNER")\n'
        'async def capacitacion_certificar(interaction: discord.Interaction, usuario: discord.Member, titulo: str):\n'
        '    capacitaciones.certificar(usuario.id, titulo, interaction.user.id)\n'
        '    await interaction.response.send_message(f"🎓 {usuario.mention} fue certificado en **{titulo}**.")\n'
        '    await enviar_log("log_capacitaciones", crear_embed(\n'
        '        "exito", "🎓 Capacitación certificada", f"**{interaction.user}** certificó a **{usuario}** en **{titulo}**"))\n'
    )
    new_cert = (
        '@grupo_capacitacion.command(name="certificar", description="Certifica a un usuario y genera diploma en imagen")\n'
        '@app_commands.describe(usuario="Usuario certificado", titulo="Título de la capacitación completada")\n'
        '@require_key("SUPERVISOR", "JEFE_DEPARTAMENTO", "DIRECTOR", "DIRECTOR_DOCENCIA", "OWNER")\n'
        'async def capacitacion_certificar(interaction: discord.Interaction, usuario: discord.Member, titulo: str):\n'
        '    await interaction.response.defer()\n'
        '    capacitaciones.certificar(usuario.id, titulo, interaction.user.id)\n'
        '    num = ""\n'
        '    try:\n'
        '        import docencia as _doc\n'
        '        reg = _doc.emitir(usuario.id, titulo, "personalizado", "", interaction.user.id)\n'
        '        num = f"CERT-{int(reg.get(\'id\') or 0):05d}"\n'
        '    except Exception:\n'
        '        num = "CERT-RP"\n'
        '    hospital = getattr(config, "NOMBRE_HOSPITAL", "Hospital") or "Hospital"\n'
        '    nombre = getattr(usuario, "display_name", None) or str(usuario)\n'
        '    emisor = getattr(interaction.user, "display_name", None) or str(interaction.user)\n'
        '    try:\n'
        '        from certificado_imagen import generar_certificado\n'
        '        buf = generar_certificado(\n'
        '            nombre_receptor=nombre,\n'
        '            titulo=titulo,\n'
        '            hospital=hospital,\n'
        '            emisor=emisor,\n'
        '            numero=num,\n'
        '        )\n'
        '        archivo = discord.File(buf, filename=f"certificado_{usuario.id}.png")\n'
        '        emb = crear_embed(\n'
        '            "exito",\n'
        '            "🎓 Certificado emitido",\n'
        '            f"**{nombre}** ha sido certificado en **{titulo}**.\\n"\n'
        '            f"N.º `{num}` · Solo Roleplay",\n'
        '        )\n'
        '        await interaction.followup.send(\n'
        '            content=f"🎓 {usuario.mention} — certificado en **{titulo}**",\n'
        '            embed=emb,\n'
        '            file=archivo,\n'
        '        )\n'
        '        try:\n'
        '            buf.seek(0)\n'
        '            await usuario.send(\n'
        '                content=f"Has recibido un certificado de **{hospital}**:",\n'
        '                file=discord.File(buf, filename=f"certificado_{usuario.id}.png"),\n'
        '            )\n'
        '        except Exception:\n'
        '            pass\n'
        '    except Exception as e:\n'
        '        print("[certificar] imagen:", e)\n'
        '        await interaction.followup.send(\n'
        '            f"🎓 {usuario.mention} fue certificado en **{titulo}**.\\n"\n'
        '            f"(No se pudo generar la imagen: `{e}`)"\n'
        '        )\n'
        '    await enviar_log("log_capacitaciones", crear_embed(\n'
        '        "exito", "🎓 Capacitación certificada",\n'
        '        f"**{interaction.user}** certificó a **{usuario}** en **{titulo}** (`{num}`)"))\n'
    )
    if old_cert in source:
        source = source.replace(old_cert, new_cert)
        print("[hospital_core] ✓ capacitacion certificar → imagen")
    else:
        print("[hospital_core] ⚠ bloque certificar no encontrado")

    print("[hospital_core] Ejecutando núcleo…")
    try:
        exec(compile(source, "hospital_core_remote.py", "exec"), module_globals)
    except Exception:
        print("[hospital_core] ERROR núcleo:")
        traceback.print_exc()
        raise

    bot = module_globals.get("bot")
    if bot is None:
        raise RuntimeError("hospital_core: bot no definido")

    print("[hospital_core] Registrando módulos…")
    ok, fail = [], []
    for name in _MODULOS:
        try:
            mod = __import__(name)
            if hasattr(mod, "registrar"):
                mod.registrar(bot)
                ok.append(name)
                print(f"[hospital_core] ✓ {name}")
            else:
                print(f"[hospital_core] · {name}")
        except Exception:
            fail.append(name)
            print(f"[hospital_core] ✗ {name}")
            traceback.print_exc()
    print(f"[hospital_core] módulos OK={ok} FAIL={fail}")

    def _listar_nombres():
        return sorted({c.name for c in bot.tree.get_commands()})

    def _recortar_a_limite():
        names = _listar_nombres()
        print(f"[hospital_core] Comandos antes de recorte: {len(names)}")
        if len(names) <= _MAX_SLASH:
            return names
        quitados = []
        for n in _BAJA_PRIORIDAD:
            if len(_listar_nombres()) <= _MAX_SLASH:
                break
            try:
                bot.tree.remove_command(n)
                quitados.append(n)
            except Exception:
                pass
        criticos = {
            "limpiar", "limpiar_todo", "sincronizar_comandos",
            "crear_certificado", "mis_certificados", "ver_certificados", "mostrar_certificado",
            "panel_solicitudes", "configurar_roles", "otorgar_key", "bootstrap_owner",
            "tienda", "panel_tienda", "mi_inventario",
            "sancionar", "verificar_roblox", "expediente",
        }
        while len(_listar_nombres()) > _MAX_SLASH:
            restantes = [n for n in _listar_nombres() if n not in criticos]
            if not restantes:
                break
            n = restantes[-1]
            try:
                bot.tree.remove_command(n)
                quitados.append(n)
            except Exception:
                break
        final = _listar_nombres()
        print(f"[hospital_core] Recortados ({len(quitados)}): {quitados}")
        print(f"[hospital_core] Comandos tras recorte: {len(final)}")
        return final

    names0 = _recortar_a_limite()
    print(f"[hospital_core] En memoria: {len(names0)} → {', '.join(names0)}")

    async def _vaciar_globales():
        try:
            app_id = bot.application_id
            if app_id is None:
                appinfo = await bot.application_info()
                app_id = appinfo.id
            await bot.http.bulk_upsert_global_commands(int(app_id), [])
            print("[hospital_core] Globales vaciados (sin duplicados)")
        except Exception as e:
            print(f"[hospital_core] No se pudieron vaciar globales: {e}")

    async def _sync_todo(reason: str = "") -> list:
        result: list = []
        print(f"[hospital_core] === SYNC ({reason}) ===")
        _recortar_a_limite()
        try:
            await _vaciar_globales()
            targets = list(bot.guilds) if getattr(bot, "guilds", None) else []
            if not targets:
                targets = [discord.Object(id=_GUILD_ID)]
                print(f"[hospital_core] Sin guilds en cache → {_GUILD_ID}")
            for g in targets:
                gid = int(getattr(g, "id", _GUILD_ID))
                obj = discord.Object(id=gid)
                try:
                    bot.tree.copy_global_to(guild=obj)
                    synced = await bot.tree.sync(guild=obj)
                    result = sorted(c.name for c in synced)
                    print(f"[hospital_core] GUILD {gid}: {len(result)} OK (solo servidor)")
                    print(f"[hospital_core] → {', '.join(result)}")
                except discord.HTTPException as e:
                    print(
                        f"[hospital_core] GUILD {gid} HTTP status={e.status} "
                        f"code={getattr(e, 'code', None)}: {e.text}"
                    )
                    traceback.print_exc()
                except Exception as e:
                    print(f"[hospital_core] GUILD {gid} error: {e}")
                    traceback.print_exc()
        except Exception as e:
            print(f"[hospital_core] sync error: {e}")
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
        if not (
            ctx.author.guild_permissions.administrator
            or ctx.author.id == ctx.guild.owner_id
        ):
            await ctx.reply("❌ Solo admin / dueño.")
            return
        m = await ctx.reply("🔄 Publicando comandos (sin duplicados)…")
        try:
            names = await _sync_todo("!forzar_sync")
            await m.edit(
                content=(
                    f"✅ **{len(names)}** comandos (solo este servidor, sin dobles).\n"
                    f"`{'`, `'.join(names[:60])}`"
                    + ("…" if len(names) > 60 else "")
                    + "\nEscribe `/` — ya no deberían estar duplicados."
                )
            )
        except Exception as e:
            await m.edit(content=f"❌ `{e}`")

    @bot.listen("on_ready")
    async def _hc_backup_sync():
        if getattr(bot, "_hc_backup_done", False):
            return
        bot._hc_backup_done = True
        await asyncio.sleep(6)
        try:
            await _sync_todo("backup-listen")
        except Exception as e:
            print("[hospital_core] backup:", e)

    return bot


bot = _cargar(globals())
