# -*- coding: utf-8 -*
"""hospital_core.py — núcleo + módulos + sync FIABLE."""
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
    print("[hospital_core] Descargando núcleo…")
    with urllib.request.urlopen(_URL, timeout=60) as resp:
        source = resp.read().decode("utf-8")
    print(f"[hospital_core] Núcleo: {len(source)} bytes")

    # ═══════════════════════════════════════════════════════════════
    # REEMPLAZAR TODO el on_ready remoto por uno que:
    #  1) registra vistas persistentes
    #  2) NO borra ni vacía el árbol de comandos
    #  3) deja el sync a hospital_core (después de cargar módulos)
    # ═══════════════════════════════════════════════════════════════
    on_ready_pattern = re.compile(
        r"@bot\.event\s*\nasync def on_ready\(\):\n"
        r"(?:.*\n)*?"
        r"(?=\n# -{5,}|\n@bot\.tree\.error|\n@bot\.tree\.command)",
        re.MULTILINE,
    )

    new_on_ready = '''@bot.event
async def on_ready():
    """Arranque controlado por hospital_core — no vacía comandos."""
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

    # Sync lo hace hospital_core._hospital_sync_todo tras cargar módulos
    fn = getattr(bot, "_hospital_sync_todo", None)
    if callable(fn):
        try:
            await asyncio.sleep(2)
            names = await fn("on_ready")
            print(f"[on_ready] Sync OK: {len(names or [])} comandos")
        except Exception as _e:
            print("[on_ready] Sync falló:", _e)
    else:
        print("[on_ready] _hospital_sync_todo aún no está listo")

'''

    m = on_ready_pattern.search(source)
    if m:
        source = source[: m.start()] + new_on_ready + source[m.end() :]
        print("[hospital_core] ✓ on_ready remoto REEMPLAZADO")
    else:
        print("[hospital_core] ⚠ No se encontró on_ready — parches sueltos")
        source = source.replace("bot.tree.clear_commands(guild=None)", "pass  # no clear")
        source = source.replace(
            "await bot.tree.sync()  # publica árbol vacío a nivel global (quita duplicados viejos)",
            "pass  # no empty sync",
        )

    # Cortar antes del run/token check
    marker = "if not config.TOKEN:"
    idx = source.find(marker)
    if idx > 0:
        source = source[:idx]

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

    # ── Módulos ──────────────────────────────────────────────────
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

    try:
        names = sorted({c.name for c in bot.tree.get_commands()})
        print(f"[hospital_core] En memoria: {len(names)} → {', '.join(names)}")
    except Exception as e:
        print("[hospital_core] listar:", e)

    async def _sync_todo(reason: str = "") -> list:
        result: list = []
        print(f"[hospital_core] === SYNC ({reason}) ===")
        try:
            # Global
            try:
                gsync = await bot.tree.sync()
                print(f"[hospital_core] GLOBAL: {len(gsync)}")
            except Exception as e:
                print(f"[hospital_core] GLOBAL error: {e}")

            targets = list(bot.guilds) if getattr(bot, "guilds", None) else []
            if not targets:
                targets = [discord.Object(id=_GUILD_ID)]
                print(f"[hospital_core] Sin guilds en cache, uso {_GUILD_ID}")

            for g in targets:
                gid = int(getattr(g, "id", _GUILD_ID))
                obj = discord.Object(id=gid)
                try:
                    bot.tree.copy_global_to(guild=obj)
                    synced = await bot.tree.sync(guild=obj)
                    result = sorted(c.name for c in synced)
                    print(f"[hospital_core] GUILD {gid}: {len(result)} comandos")
                    print(f"[hospital_core] → {', '.join(result[:80])}")
                except Exception as e:
                    print(f"[hospital_core] GUILD {gid} error: {e}")
                    traceback.print_exc()
        except Exception as e:
            print(f"[hospital_core] sync error: {e}")
            traceback.print_exc()
        return result

    bot._hospital_sync_todo = _sync_todo

    # Comando de texto de emergencia (no necesita slash sync)
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
        m = await ctx.reply("🔄 Publicando comandos…")
        try:
            names = await _sync_todo("!forzar_sync")
            await m.edit(
                content=(
                    f"✅ **{len(names)}** slash commands publicados.\n"
                    f"`{'`, `'.join(names[:50])}`"
                    + ("…" if len(names) > 50 else "")
                    + "\nEscribe `/` — deben salir ya."
                )
            )
        except Exception as e:
            await m.edit(content=f"❌ `{e}`")

    # Por si on_ready del núcleo ya pasó (reconnect), reintentar
    @bot.listen("on_ready")
    async def _hc_backup_sync():
        if getattr(bot, "_hc_backup_done", False):
            return
        bot._hc_backup_done = True
        await asyncio.sleep(5)
        try:
            await _sync_todo("backup-listen")
        except Exception as e:
            print("[hospital_core] backup sync:", e)

    return bot


bot = _cargar(globals())
