# -*- coding: utf-8 -*
"""cs_ui_patches — aprobación, involucrados, logs a RRHH por nombre."""
from __future__ import annotations
import re
from typing import List

_CAT_MAP = {
    "sancion": ["staff", "disciplina", "sanciones", "rrhh"],
    "apelacion": ["staff", "apelaciones", "disciplina"],
    "investigacion": ["staff", "investigaciones", "rrhh", "disciplina"],
    "reporte": ["staff", "reportes", "disciplina"],
    "general": ["información general", "informacion general", "información", "informacion", "general", "info"],
    "consulta": ["información general", "informacion general", "información", "consultas", "info"],
}

def _resolver_cat(guild, key):
    import discord, config
    nombres = _CAT_MAP.get(key) or _CAT_MAP["general"]
    mapa = getattr(config, "TICKET_CATEGORIAS", None) or {}
    for k in (key, "staff" if key in ("sancion","apelacion","investigacion","reporte") else "general"):
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
    fb = getattr(config, "TICKET_CATEGORIA_ID", None)
    if fb:
        ch = guild.get_channel(int(fb))
        if isinstance(ch, discord.CategoryChannel):
            return ch
    return None

def _ids_campos(campos):
    ids = []
    for v in (campos or {}).values():
        for m in re.finditer(r"<@!?(\d+)>", str(v)):
            ids.append(int(m.group(1)))
        for m in re.finditer(r"\b(\d{15,20})\b", str(v)):
            ids.append(int(m.group(1)))
    return list(dict.fromkeys(ids))

def apply(mod):
    import discord
    from discord import ui
    import config

    _puede = mod._puede_gestionar
    actualizar = mod.actualizar_solicitud
    obtener = mod.obtener_solicitud
    embed_ticket = mod.embed_ticket
    embed_log = mod.embed_log_accion
    enviar_log = mod.enviar_log_solicitud
    _now = mod._now
    TSV = mod.TicketSolicitudView

    class MotivoRechazo(ui.Modal, title="Rechazar solicitud"):
        motivo = ui.TextInput(label="Motivo", style=discord.TextStyle.paragraph, max_length=800)
        def __init__(self, bot, sid):
            super().__init__()
            self.bot, self.sid = bot, sid
        async def on_submit(self, inter):
            if not _puede(inter.user):
                return await inter.response.send_message("Sin permiso.", ephemeral=True)
            reg = actualizar(self.sid, estado="rechazada", resolucion=str(self.motivo),
                             responsable_id=inter.user.id, fecha_actualizacion=_now()) or obtener(self.sid)
            await inter.response.send_message(
                f"Solicitud #{self.sid:04d} rechazada por {inter.user.mention}\nMotivo: {self.motivo}",
                embed=embed_ticket(reg or {}, inter.guild))
            if reg:
                try: await enviar_log(self.bot, embed_log(reg, "Rechazo", inter.user, str(self.motivo)))
                except Exception: pass
            if reg and reg.get("usuario_id"):
                try:
                    u = inter.client.get_user(int(reg["usuario_id"]))
                    if u: await u.send(f"Tu solicitud #{self.sid:04d} fue rechazada.\nMotivo: {self.motivo}")
                except Exception: pass

    class PanelDecision(ui.View):
        def __init__(self, bot, sid):
            super().__init__(timeout=None)
            self.bot, self.sid = bot, sid
        @ui.button(label="Aprobar", style=discord.ButtonStyle.success, emoji="✅", custom_id="sol_ap_v3")
        async def ap(self, inter, btn):
            if not _puede(inter.user):
                return await inter.response.send_message("Solo staff.", ephemeral=True)
            reg = actualizar(self.sid, estado="resuelta", resolucion="Aprobada",
                             responsable_id=inter.user.id, fecha_actualizacion=_now()) or obtener(self.sid)
            await inter.response.send_message(
                f"Solicitud #{self.sid:04d} aprobada por {inter.user.mention}",
                embed=embed_ticket(reg or {}, inter.guild))
            if reg:
                try: await enviar_log(self.bot, embed_log(reg, "Aprobacion", inter.user, "Aprobada"))
                except Exception: pass
            if reg and reg.get("usuario_id"):
                try:
                    u = inter.client.get_user(int(reg["usuario_id"]))
                    if u: await u.send(f"Tu solicitud #{self.sid:04d} fue aprobada.")
                except Exception: pass
        @ui.button(label="Rechazar", style=discord.ButtonStyle.danger, emoji="❌", custom_id="sol_re_v3")
        async def re(self, inter, btn):
            if not _puede(inter.user):
                return await inter.response.send_message("Solo staff.", ephemeral=True)
            await inter.response.send_modal(MotivoRechazo(self.bot, self.sid))
        @ui.button(label="Ir al ticket", style=discord.ButtonStyle.secondary, emoji="🎫", custom_id="sol_go_v3")
        async def go(self, inter, btn):
            reg = obtener(self.sid)
            if not reg or not reg.get("canal_id"):
                return await inter.response.send_message("Ticket no encontrado.", ephemeral=True)
            ch = inter.client.get_channel(int(reg["canal_id"]))
            await inter.response.send_message(f"Ticket: {ch.mention}" if ch else "Canal eliminado.", ephemeral=True)

    mod.PanelDecisionView = PanelDecision

    try:
        from ticket_adduser import AnadirUsuarioView
        async def adduser(self, inter, btn):
            if not _puede(inter.user):
                return await inter.response.send_message("Solo staff.", ephemeral=True)
            if not inter.guild: return
            await inter.response.send_message(
                "Añadir persona al ticket:",
                view=AnadirUsuarioView(self.bot, self.solicitud_id, inter.guild), ephemeral=True)
        TSV.adduser = adduser
    except Exception as e:
        print("adduser patch:", e)

    async def _aprobar(self, inter, btn=None):
        if not _puede(inter.user):
            return await inter.response.send_message("Solo staff.", ephemeral=True)
        reg = actualizar(self.solicitud_id, estado="resuelta", resolucion="Aprobada",
                         responsable_id=inter.user.id, fecha_actualizacion=_now()) or obtener(self.solicitud_id)
        await inter.response.send_message(f"Aprobada por {inter.user.mention}", embed=embed_ticket(reg or {}, inter.guild))
        if reg and reg.get("usuario_id"):
            try:
                u = inter.client.get_user(int(reg["usuario_id"]))
                if u: await u.send(f"Tu solicitud #{self.solicitud_id:04d} fue aprobada.")
            except Exception: pass

    async def _rechazar(self, inter, btn=None):
        if not _puede(inter.user):
            return await inter.response.send_message("Solo staff.", ephemeral=True)
        await inter.response.send_modal(MotivoRechazo(self.bot, self.solicitud_id))

    def _new_init(self, bot, solicitud_id):
        ui.View.__init__(self, timeout=None)
        self.bot = bot
        self.solicitud_id = solicitud_id
        for label, style, emoji, cb in (
            ("Aprobar", discord.ButtonStyle.success, "✅", _aprobar),
            ("Rechazar", discord.ButtonStyle.danger, "❌", _rechazar),
        ):
            b = ui.Button(label=label, style=style, emoji=emoji)
            async def make_cb(inter, _cb=cb, _self=self):
                await _cb(_self, inter)
            b.callback = make_cb
            self.add_item(b)
        for name, label, style, emoji in (
            ("reclamar", "Reclamar", discord.ButtonStyle.primary, "👋"),
            ("adduser", "Añadir personas", discord.ButtonStyle.secondary, "👥"),
            ("cerrar", "Cerrar", discord.ButtonStyle.secondary, "🔒"),
        ):
            meth = getattr(TSV, name, None)
            if not callable(meth):
                continue
            b = ui.Button(label=label, style=style, emoji=emoji)
            async def make_cb2(inter, _m=meth, _self=self, _b=b):
                await _m(_self, inter, _b)
            b.callback = make_cb2
            self.add_item(b)

    TSV.__init__ = _new_init
    print("[cs_ui] Ticket Aprobar/Rechazar OK")

    orig = mod.crear_ticket_solicitud
    async def crear(bot, inter, categoria, campos):
        import centro_solicitudes as cs
        old = getattr(cs, "_categoria_canal", None)
        def catg(g):
            return _resolver_cat(g, categoria) or (old(g) if old else None)
        cs._categoria_canal = catg
        try:
            await orig(bot, inter, categoria, campos)
        finally:
            if old: cs._categoria_canal = old
        try:
            uid = inter.user.id
            reg = None
            try:
                todas = cs.listar_solicitudes() if hasattr(cs, "listar_solicitudes") else []
                mias = [r for r in (todas or []) if r.get("usuario_id") == uid]
                if mias:
                    reg = max(mias, key=lambda r: int(r.get("id") or 0))
            except Exception:
                pass
            if not reg:
                return
            guild = inter.guild
            canal = bot.get_channel(int(reg["canal_id"])) if reg.get("canal_id") else None
            if canal and guild:
                inv = [i for i in _ids_campos(campos) if i != uid][:10]
                menc = []
                for iid in inv:
                    m = guild.get_member(iid)
                    if m:
                        try:
                            await canal.set_permissions(m, view_channel=True, send_messages=True, attach_files=True)
                            menc.append(m.mention)
                        except Exception: pass
                if menc:
                    await canal.send("Involucrados en el ticket: " + " ".join(menc))
                await canal.send("**Decisión del staff:**", view=PanelDecision(bot, int(reg["id"])))
            log_ch = None
            try:
                import logs_store
                log_ch = logs_store.resolver_canal_log(bot, guild, "log_solicitudes")
                if not log_ch:
                    log_ch = logs_store.resolver_canal_log(bot, guild, "aprobaciones_rrhh")
            except Exception as e:
                print("[cs_ui] resolver log:", e)
            rrhh_ping = ""
            try:
                import roles_store
                rid = roles_store.obtener_id_key("DIRECTOR_RRHH") or roles_store.obtener_id_key("RRHH")
                if rid and guild:
                    rol = guild.get_role(int(rid))
                    if rol:
                        rrhh_ping = rol.mention + " "
                if not rrhh_ping and guild:
                    for r in guild.roles:
                        rn = (r.name or "").lower()
                        if "rrhh" in rn or "recursos humanos" in rn:
                            rrhh_ping = r.mention + " "
                            break
            except Exception:
                pass
            if log_ch:
                emb = embed_ticket(reg, guild)
                emb.title = f"Nueva solicitud #{int(reg['id']):04d} · RRHH"
                chm = canal.mention if canal else "—"
                await log_ch.send(
                    content=f"{rrhh_ping}Nueva solicitud para **RRHH** · ticket {chm}",
                    embed=emb,
                    view=PanelDecision(bot, int(reg["id"])),
                )
            else:
                print("[cs_ui] No hay canal RRHH. Crea: rrhh / solicitudes / recursos-humanos")
        except Exception as e:
            print("[cs_ui] post-crear:", e)

    mod.crear_ticket_solicitud = crear
    print("[cs_ui] crear + panel RRHH OK")

    try:
        import logs_store as _ls
        async def enviar_log_solicitud(bot, embed):
            guild = next(iter(bot.guilds), None)
            ch = _ls.resolver_canal_log(bot, guild, "log_solicitudes") if guild else None
            if not ch and guild:
                ch = _ls.resolver_canal_log(bot, guild, "aprobaciones_rrhh")
            if ch:
                try:
                    await ch.send(embed=embed)
                except Exception as e:
                    print("[cs_ui] enviar_log:", e)
            else:
                print("[cs_ui] Sin canal RRHH para log")
        mod.enviar_log_solicitud = enviar_log_solicitud
        print("[cs_ui] enviar_log → RRHH OK")
    except Exception as e:
        print("[cs_ui] parche enviar_log:", e)

    if hasattr(mod, "registrar"):
        _or = mod.registrar
        def registrar(bot):
            _or(bot)
            try: bot.add_view(PanelDecision(bot, 0))
            except Exception: pass
        mod.registrar = registrar
    print("[cs_ui] patches applied")
