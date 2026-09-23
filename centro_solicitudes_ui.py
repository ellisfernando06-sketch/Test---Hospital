# -*- coding: utf-8 -*
"""centro_solicitudes_ui.py — Carga módulo + parches: adduser, categorías, transcripción."""
from __future__ import annotations
import urllib.request
import sys
import asyncio
from datetime import datetime, timezone

_GOOD = "a6e30cbaefe3ab422f1b108b42dbe5a6c83d1f92"
_URL = f"https://raw.githubusercontent.com/ellisfernando06-sketch/Test---Hospital/{_GOOD}/centro_solicitudes_ui.py"

_CAT_MAP = {
    "sancion": ["staff", "disciplina", "sanciones", "rrhh"],
    "apelacion": ["staff", "apelaciones", "disciplina"],
    "investigacion": ["staff", "investigaciones", "rrhh", "disciplina"],
    "reporte": ["staff", "reportes", "disciplina"],
    "general": ["información general", "informacion general", "información", "informacion", "general", "info"],
    "consulta": ["información general", "informacion general", "información", "consultas", "info"],
}


def _bootstrap():
    print("[centro_solicitudes_ui] Descargando módulo completo…")
    with urllib.request.urlopen(_URL, timeout=45) as resp:
        source = resp.read().decode("utf-8")
    print(f"[centro_solicitudes_ui] Descargado ({len(source)} bytes)")
    mod = sys.modules[__name__]
    exec(compile(source, "centro_solicitudes_ui_remote.py", "exec"), mod.__dict__)
    print("[centro_solicitudes_ui] Módulo completo cargado")
    _patch_all(mod)


def _resolver_cat(guild, categoria_key: str):
    import discord
    import config
    nombres = _CAT_MAP.get(categoria_key) or _CAT_MAP["general"]
    mapa = getattr(config, "TICKET_CATEGORIAS", None) or {}
    for k in (categoria_key, "staff" if categoria_key in ("sancion", "apelacion", "investigacion", "reporte") else "general"):
        cid = mapa.get(k) if isinstance(mapa, dict) else None
        if cid:
            ch = guild.get_channel(int(cid))
            if isinstance(ch, discord.CategoryChannel):
                return ch
    for cat in guild.categories:
        cn = (cat.name or "").lower()
        for n in nombres:
            if n and n in cn:
                return cat
    fallback = getattr(config, "TICKET_CATEGORIA_ID", None)
    if fallback:
        ch = guild.get_channel(int(fallback))
        if isinstance(ch, discord.CategoryChannel):
            return ch
    return None


def _patch_all(mod):
    import discord
    from discord import ui

    try:
        from ticket_adduser import AnadirUsuarioView
        TicketSolicitudView = mod.TicketSolicitudView
        _puede_gestionar = mod._puede_gestionar

        async def adduser(self, interaction: discord.Interaction, button: ui.Button):
            if not _puede_gestionar(interaction.user):
                await interaction.response.send_message("❌ Solo staff autorizado.", ephemeral=True)
                return
            if not interaction.guild:
                await interaction.response.send_message("❌ Solo en el servidor.", ephemeral=True)
                return
            await interaction.response.send_message(
                "👥 **Añadir persona al ticket**\n• Menú superior: personal autorizado\n• Menú inferior: buscar usuario",
                view=AnadirUsuarioView(self.bot, self.solicitud_id, interaction.guild),
                ephemeral=True,
            )

        TicketSolicitudView.adduser = adduser
        print("[centro_solicitudes_ui] Parche adduser OK")
    except Exception as e:
        print("[centro_solicitudes_ui] Parche adduser falló:", e)

    try:
        orig_crear = mod.crear_ticket_solicitud

        async def crear_ticket_solicitud(bot, interaction, categoria, campos):
            import centro_solicitudes as cs

            def _cat_for_guild(guild):
                return _resolver_cat(guild, categoria) or cs._categoria_canal(guild)

            old = getattr(cs, "_categoria_canal", None)
            cs._categoria_canal = _cat_for_guild
            if hasattr(mod, "_categoria_canal"):
                mod._categoria_canal = _cat_for_guild
            try:
                return await orig_crear(bot, interaction, categoria, campos)
            finally:
                if old:
                    cs._categoria_canal = old

        mod.crear_ticket_solicitud = crear_ticket_solicitud
        print("[centro_solicitudes_ui] Parche categorías OK")
    except Exception as e:
        print("[centro_solicitudes_ui] Parche categorías falló:", e)

    try:
        ConfirmarCierreView = mod.ConfirmarCierreView
        _puede_gestionar = mod._puede_gestionar
        actualizar_solicitud = mod.actualizar_solicitud
        obtener_solicitud = mod.obtener_solicitud
        embed_ticket = mod.embed_ticket
        embed_log_accion = mod.embed_log_accion
        enviar_log_solicitud = mod.enviar_log_solicitud
        _now = mod._now

        async def confirmar(self, interaction: discord.Interaction, button: ui.Button):
            if not _puede_gestionar(interaction.user):
                await interaction.response.send_message("❌ No tienes permiso.", ephemeral=True)
                return
            motivo = "Cerrada por el staff"
            reg = actualizar_solicitud(
                self.solicitud_id, estado="cerrada", motivo_cierre=motivo, fecha_cierre=_now(),
            )
            if not reg:
                reg = obtener_solicitud(self.solicitud_id)
            embed = embed_ticket(reg or {}, interaction.guild)
            await interaction.response.edit_message(
                content=f"🔒 Cerrada por {interaction.user.mention} · generando transcripción…",
                embed=embed, view=None,
            )
            if reg:
                log = embed_log_accion(reg, "Cierre", interaction.user, motivo)
                await enviar_log_solicitud(self.bot, log)

            if interaction.channel:
                try:
                    from ticket_transcript import collect_messages, render_html, html_to_file, embed_resumen
                    msgs = await collect_messages(interaction.channel, limit=500)
                    cat_name = interaction.channel.category.name if interaction.channel.category else "—"
                    opener = "—"
                    if reg and reg.get("usuario_id") and interaction.guild:
                        m = interaction.guild.get_member(int(reg["usuario_id"]))
                        opener = m.mention if m else str(reg["usuario_id"])
                    titulo = f"Solicitud #{self.solicitud_id:04d}"
                    if reg and reg.get("categoria"):
                        titulo += f" · {reg['categoria']}"
                    html_str = render_html(
                        titulo=titulo, canal_nombre=interaction.channel.name,
                        abierto_por=opener, cerrado_por=interaction.user.mention,
                        categoria=cat_name,
                        creado=msgs[0].created_at if msgs else interaction.channel.created_at,
                        cerrado=datetime.now(timezone.utc), messages=msgs, guild=interaction.guild,
                    )
                    archivo = html_to_file(html_str, filename=f"solicitud-{self.solicitud_id:04d}.html")
                    emb = embed_resumen(
                        titulo=titulo, canal_nombre=interaction.channel.name,
                        abierto_por=opener, cerrado_por=interaction.user.mention,
                        categoria=cat_name, n_msgs=len(msgs), color=0x8E44AD,
                    )
                    dest = None
                    try:
                        import logs_store
                        cid = logs_store.get_canal_id("log_tickets") or logs_store.get_canal_id("log_solicitudes")
                        if cid:
                            dest = interaction.client.get_channel(int(cid))
                    except Exception:
                        pass
                    if not dest:
                        import config
                        canales = getattr(config, "CANALES", {}) or {}
                        cid = canales.get("log_tickets") or canales.get("log_solicitudes")
                        if cid:
                            dest = interaction.client.get_channel(int(cid))
                    if dest:
                        await dest.send(embed=emb, file=archivo)
                    else:
                        await interaction.channel.send(embed=emb, file=archivo)
                except Exception as e:
                    print("[centro_solicitudes_ui] Transcripción error:", e)

                try:
                    await interaction.channel.send("🔒 Canal se eliminará en 5 segundos…")
                    await asyncio.sleep(5)
                    await interaction.channel.delete(reason=f"Solicitud #{self.solicitud_id} cerrada")
                except Exception:
                    pass

        ConfirmarCierreView.confirmar = confirmar
        print("[centro_solicitudes_ui] Parche transcripción cierre OK")
    except Exception as e:
        print("[centro_solicitudes_ui] Parche cierre falló:", e)


_bootstrap()
