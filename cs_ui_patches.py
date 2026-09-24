# -*- coding: utf-8 -*
"""cs_ui_patches — vistas limpias de solicitudes + logs RRHH + entrevista."""
from __future__ import annotations
import re
import asyncio
from datetime import datetime, timezone

_CAT_MAP = {
    "sancion": ["staff", "disciplina", "sanciones", "rrhh"],
    "apelacion": ["staff", "apelaciones", "disciplina"],
    "investigacion": ["staff", "investigaciones", "rrhh"],
    "reporte": ["staff", "reportes", "disciplina"],
    "general": ["información general", "informacion general", "información", "general", "info"],
    "consulta": ["información general", "consultas", "info"],
}


def _resolver_cat(guild, key):
    import discord, config
    nombres = _CAT_MAP.get(key) or _CAT_MAP["general"]
    mapa = getattr(config, "TICKET_CATEGORIAS", None) or {}
    for k in (key, "staff" if key in ("sancion", "apelacion", "investigacion", "reporte") else "general"):
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

    # CO_OWNER puede gestionar (añadir, entrevista, cerrar, solicitar aprobación)
    # pero NO puede aprobar ni rechazar. Solo OWNER (y directores autorizados) aprueban.
    def _es_co_owner(member) -> bool:
        if not isinstance(member, discord.Member):
            return False
        try:
            import permisos
            return permisos.member_tiene_key(member, "CO_OWNER") and not permisos.member_tiene_key(member, "OWNER")
        except Exception:
            return False

    def _puede_aprobar(member) -> bool:
        """Solo OWNER y cargos de dirección/staff operativo (excluye CO_OWNER puro)."""
        if not isinstance(member, discord.Member):
            return False
        if _es_co_owner(member):
            return False
        try:
            import permisos
            return permisos.member_tiene_alguna_key(
                member,
                "OWNER",
                "DIRECTOR", "DIRECTOR_GENERAL", "DIRECTOR_ADMINISTRATIVO",
                "DIRECTOR_DISCIPLINA", "DIRECTOR_RRHH", "DIRECTOR_MEDICO",
                "DIRECTOR_ENFERMERIA", "DIRECTOR_SEGURIDAD", "DIRECTOR_DOCENCIA",
                "SUPERVISOR", "STAFF_SERVIDOR",
            )
        except Exception:
            return _puede(member) and not _es_co_owner(member)

    async def _solicitar_aprobacion_owner(bot, inter, sid: int):
        """CO_OWNER (u otros sin poder de aprobación) pide decisión al OWNER."""
        if not isinstance(inter.user, discord.Member):
            return await inter.response.send_message("Solo en el servidor.", ephemeral=True)
        if not (_es_co_owner(inter.user) or _puede(inter.user)):
            return await inter.response.send_message("Sin permiso.", ephemeral=True)
        if _puede_aprobar(inter.user):
            return await inter.response.send_message(
                "Ya puedes aprobar o rechazar directamente. No hace falta solicitar al OWNER.",
                ephemeral=True,
            )
        reg = obtener(sid) or {}
        guild = inter.guild
        emb = discord.Embed(
            title=f"🔐 Solicitud de aprobación · #{sid:04d}",
            description=(
                f"**Solicitado por:** {inter.user.mention} (**CO-OWNER**)\n"
                f"**Acción:** Revisar y decidir sobre esta solicitud.\n"
                f"**Nota:** El CO-OWNER no puede aprobar ni rechazar; requiere decisión del **OWNER**.\n\n"
                f"Use los botones del ticket o del log para **Aprobar** / **Rechazar**."
            ),
            color=0xF39C12,
            timestamp=discord.utils.utcnow(),
        )
        try:
            emb_t = embed_ticket(reg, guild)
            if emb_t and emb_t.description:
                emb.add_field(name="Resumen", value=(emb_t.description or "—")[:1000], inline=False)
        except Exception:
            pass
        emb.set_footer(text=getattr(config, "NOMBRE_HOSPITAL", "Hospital") + "  •  Escalado a OWNER")

        enviado = False
        content = ""
        try:
            import roles_store
            rid = roles_store.obtener_id_key("OWNER")
            if rid and guild:
                rol = guild.get_role(int(rid))
                if rol:
                    content = rol.mention + " "
        except Exception:
            pass

        dest = None
        try:
            import logs_store
            dest = logs_store.resolver_canal_log(bot, guild, "aprobaciones")
            if not dest:
                dest = logs_store.resolver_canal_log(bot, guild, "log_solicitudes")
        except Exception:
            pass
        if not dest and guild:
            cid = (getattr(config, "CANALES", {}) or {}).get("aprobaciones")
            if cid:
                dest = guild.get_channel(int(cid))

        view = PanelDecisionLog(bot, sid)
        if dest:
            await dest.send(content=content or None, embed=emb, view=view)
            enviado = True
        elif guild:
            try:
                import roles_store
                rid = roles_store.obtener_id_key("OWNER")
                if rid:
                    rol = guild.get_role(int(rid))
                    if rol:
                        for m in rol.members[:3]:
                            try:
                                await m.send(embed=emb, view=view)
                                enviado = True
                                break
                            except Exception:
                                continue
            except Exception:
                pass

        if enviado:
            try:
                actualizar(sid, estado="escalada", resolucion=f"Escalada a OWNER por {inter.user}", fecha_actualizacion=_now())
            except Exception:
                pass
            await inter.response.send_message(
                "📨 Solicitud de aprobación enviada al **OWNER**. "
                "Como **CO-OWNER** no puedes aprobar ni rechazar; el OWNER debe decidir.",
                ephemeral=True,
            )
            try:
                if inter.channel:
                    await inter.channel.send(
                        f"🔐 {inter.user.mention} (**CO-OWNER**) solicitó aprobación del **OWNER** "
                        f"para la solicitud **#{sid:04d}**."
                    )
            except Exception:
                pass
        else:
            await inter.response.send_message(
                "❌ No se pudo contactar al OWNER. Configura el canal `aprobaciones` o asegúrate de que haya un OWNER.",
                ephemeral=True,
            )

    # ── Entrevista helpers (integrado) ──────────────────────────────
    def _puede_entrevista(member) -> bool:
        if not isinstance(member, discord.Member):
            return False
        if member.guild_permissions.manage_channels:
            return True
        try:
            import permisos
            return permisos.member_tiene_alguna_key(
                member,
                "OWNER", "CO_OWNER", "DIRECTOR_GENERAL", "DIRECTOR_RRHH",
                "DIRECTOR_MEDICO", "DIRECTOR_ENFERMERIA", "DIRECTOR_SEGURIDAD",
                "DIRECTOR_ADMINISTRATIVO", "DIRECTOR_DOCENCIA", "SUPERVISOR", "STAFF_SERVIDOR",
            )
        except Exception:
            return False

    def _next_entrevista_num() -> int:
        import os, json
        path = os.path.join(os.path.dirname(__file__), "data", "entrevistas.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = {"n": 0}
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {"n": 0}
        data["n"] = int(data.get("n") or 0) + 1
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return int(data["n"])

    def _ping_director(guild, slug: str) -> str:
        dep = (getattr(config, "DEPARTAMENTOS", None) or {}).get(slug) or {}
        dkey = dep.get("director_key")
        if not dkey or not guild:
            return ""
        try:
            import roles_store
            rid = roles_store.obtener_id_key(dkey)
            if rid:
                r = guild.get_role(int(rid))
                if r:
                    return r.mention
        except Exception:
            pass
        return ""

    class ConfirmarCierreEntrevista(ui.View):
        def __init__(self, bot):
            super().__init__(timeout=90)
            self.bot = bot

        @ui.button(label="Transcribir y cerrar", style=discord.ButtonStyle.danger, emoji="📜")
        async def ok(self, inter: discord.Interaction, btn: ui.Button):
            if not _puede_entrevista(inter.user):
                return await inter.response.send_message("Sin permiso.", ephemeral=True)
            await inter.response.edit_message(content=f"Cerrando… {inter.user.mention}", view=None)
            ch = inter.channel
            if not isinstance(ch, discord.TextChannel):
                return
            try:
                from ticket_transcript import collect_messages, render_html, html_to_file, embed_resumen
                msgs = await collect_messages(ch, limit=500)
                html_str = render_html(
                    titulo=ch.name, canal_nombre=ch.name, abierto_por="—",
                    cerrado_por=inter.user.mention,
                    categoria=ch.category.name if ch.category else "—",
                    creado=msgs[0].created_at if msgs else ch.created_at,
                    cerrado=datetime.now(timezone.utc), messages=msgs, guild=ch.guild,
                )
                archivo = html_to_file(html_str, filename=f"{ch.name}.html")
                emb = embed_resumen(
                    titulo=ch.name, canal_nombre=ch.name, abierto_por="—",
                    cerrado_por=inter.user.mention,
                    categoria=ch.category.name if ch.category else "—",
                    n_msgs=len(msgs), color=0x3498DB,
                )
                dest = None
                try:
                    import logs_store
                    cid = logs_store.get_canal_id("log_tickets") or logs_store.get_canal_id("log_solicitudes")
                    if cid:
                        dest = inter.client.get_channel(int(cid))
                except Exception:
                    pass
                if dest:
                    await dest.send(embed=emb, file=archivo)
                else:
                    await ch.send(embed=emb, file=archivo)
            except Exception as e:
                print("[cs_ui] entrevista transcript:", e)
            try:
                await asyncio.sleep(4)
                await ch.delete(reason="Entrevista cerrada")
            except Exception:
                pass

        @ui.button(label="Cancelar", style=discord.ButtonStyle.secondary, emoji="❌")
        async def cancel(self, inter: discord.Interaction, btn: ui.Button):
            await inter.response.edit_message(content="Cancelado.", view=None)

    class EntrevistaCanalView(ui.View):
        def __init__(self, bot, num: int = 0):
            super().__init__(timeout=None)
            self.bot = bot
            self.num = num

        @ui.button(label="Transcribir y cerrar", style=discord.ButtonStyle.danger, emoji="📜", custom_id="entrevista_cerrar_v2")
        async def cerrar(self, inter: discord.Interaction, btn: ui.Button):
            if not _puede_entrevista(inter.user):
                return await inter.response.send_message("Solo staff.", ephemeral=True)
            await inter.response.send_message(
                "¿Cerrar entrevista con transcripción?",
                view=ConfirmarCierreEntrevista(self.bot),
                ephemeral=True,
            )

    async def _crear_entrevista(bot, inter: discord.Interaction, solicitud_id: int):
        if not _puede_entrevista(inter.user):
            return await inter.response.send_message("Solo staff autorizado puede abrir entrevistas.", ephemeral=True)
        guild = inter.guild
        if not guild:
            return
        await inter.response.defer(ephemeral=True)
        reg = obtener(solicitud_id) or {}
        num = _next_entrevista_num()
        nombre = f"entrevista-{num:03d}"
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
            inter.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        uid = reg.get("usuario_id")
        solicitante = guild.get_member(int(uid)) if uid else None
        if solicitante:
            overwrites[solicitante] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        try:
            import roles_store
            for key in getattr(config, "TICKET_STAFF_KEYS", []) or []:
                rid = roles_store.obtener_id_key(key)
                if rid:
                    rol = guild.get_role(int(rid))
                    if rol:
                        overwrites[rol] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
            for extra_key in ("DIRECTOR_RRHH", "DIRECTOR_DOCENCIA"):
                rid = roles_store.obtener_id_key(extra_key)
                if rid:
                    rol = guild.get_role(int(rid))
                    if rol:
                        overwrites[rol] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        except Exception:
            pass
        category = inter.channel.category if inter.channel else None
        try:
            canal = await guild.create_text_channel(
                nombre, category=category, overwrites=overwrites,
                reason=f"Entrevista solicitud #{solicitud_id}",
            )
        except Exception as e:
            return await inter.followup.send(f"No pude crear el canal: {e}", ephemeral=True)

        menciones = [inter.user.mention]
        if solicitante:
            menciones.append(solicitante.mention)
        try:
            campos = reg.get("campos") or {}
            deps = getattr(config, "DEPARTAMENTOS", {}) or {}
            for v in campos.values():
                vv = str(v).lower()
                for sk, sd in deps.items():
                    if sk in vv or (sd.get("nombre") or "").lower() in vv:
                        p = _ping_director(guild, sk)
                        if p:
                            menciones.append(p)
                        break
        except Exception:
            pass

        try:
            emb = embed_ticket(reg, guild)
        except Exception:
            emb = discord.Embed(
                title=f"🎤 Entrevista #{num:03d}",
                description=f"Vinculada a solicitud **#{solicitud_id:04d}**",
                color=0x3498DB,
            )

        await canal.send(
            " ".join(menciones)
            + f"\n\n🎤 **Entrevista #{num:03d}** · Solicitud **#{solicitud_id:04d}**\n"
            "Usen este canal para realizar la entrevista.\n"
            "Al finalizar, pulse **Transcribir y cerrar**.",
            embed=emb,
            view=EntrevistaCanalView(bot, num),
        )
        await inter.followup.send(f"✅ Entrevista creada: {canal.mention}", ephemeral=True)

    # ── Modales y vistas de solicitud ─────────────────────────────────

    class MotivoRechazo(ui.Modal, title="Rechazar solicitud"):
        motivo = ui.TextInput(label="Motivo", style=discord.TextStyle.paragraph, max_length=800)
        def __init__(self, bot, sid):
            super().__init__()
            self.bot, self.sid = bot, sid
        async def on_submit(self, inter):
            if _es_co_owner(inter.user) or not _puede_aprobar(inter.user):
                return await inter.response.send_message(
                    "Sin permiso para rechazar. Como CO-OWNER debes solicitar aprobación al OWNER.",
                    ephemeral=True,
                )
            reg = actualizar(self.sid, estado="rechazada", resolucion=str(self.motivo),
                             responsable_id=inter.user.id, fecha_actualizacion=_now()) or obtener(self.sid)
            await inter.response.send_message(
                f"Rechazada por {inter.user.mention}\nMotivo: {self.motivo}",
                embed=embed_ticket(reg or {}, inter.guild))
            if reg and reg.get("usuario_id"):
                try:
                    u = inter.client.get_user(int(reg["usuario_id"]))
                    if u:
                        await u.send(f"Tu solicitud #{self.sid:04d} fue rechazada.\nMotivo: {self.motivo}")
                except Exception:
                    pass

    class ConfirmarCierre(ui.View):
        def __init__(self, bot, sid):
            super().__init__(timeout=90)
            self.bot, self.sid = bot, sid
        @ui.button(label="Transcribir y cerrar", style=discord.ButtonStyle.danger, emoji="📜")
        async def confirmar(self, inter, btn):
            if not _puede(inter.user):
                return await inter.response.send_message("Sin permiso.", ephemeral=True)
            actualizar(self.sid, estado="cerrada", motivo_cierre="Cerrada", fecha_cierre=_now())
            reg = obtener(self.sid)
            await inter.response.edit_message(content=f"Cerrada por {inter.user.mention}", view=None)
            ch = inter.channel
            if ch:
                try:
                    from ticket_transcript import collect_messages, render_html, html_to_file, embed_resumen
                    msgs = await collect_messages(ch, limit=500)
                    html_str = render_html(
                        titulo=ch.name, canal_nombre=ch.name, abierto_por="—",
                        cerrado_por=inter.user.mention,
                        categoria=ch.category.name if ch.category else "—",
                        creado=msgs[0].created_at if msgs else ch.created_at,
                        cerrado=datetime.now(timezone.utc), messages=msgs, guild=ch.guild,
                    )
                    archivo = html_to_file(html_str, filename=f"{ch.name}.html")
                    emb = embed_resumen(
                        titulo=ch.name, canal_nombre=ch.name, abierto_por="—",
                        cerrado_por=inter.user.mention,
                        categoria=ch.category.name if ch.category else "—",
                        n_msgs=len(msgs), color=0x8E44AD,
                    )
                    dest = None
                    try:
                        import logs_store
                        cid = logs_store.get_canal_id("log_tickets") or logs_store.get_canal_id("log_solicitudes")
                        if cid:
                            dest = inter.client.get_channel(int(cid))
                    except Exception:
                        pass
                    if dest:
                        await dest.send(embed=emb, file=archivo)
                    else:
                        await ch.send(embed=emb, file=archivo)
                except Exception as e:
                    print("[cs_ui] transcript:", e)
                try:
                    await asyncio.sleep(4)
                    await ch.delete(reason=f"Solicitud #{self.sid}")
                except Exception:
                    pass
        @ui.button(label="Cancelar", style=discord.ButtonStyle.secondary, emoji="❌")
        async def cancelar(self, inter, btn):
            await inter.response.edit_message(content="Cancelado.", view=None)

    class TicketSolicitudView(ui.View):
        """Vista en ticket: Aprobar | Rechazar | Entrevista | Solicitar OWNER | Añadir | Cerrar."""
        def __init__(self, bot, solicitud_id: int):
            super().__init__(timeout=None)
            self.bot = bot
            self.solicitud_id = solicitud_id

        @ui.button(label="Aprobar", style=discord.ButtonStyle.success, emoji="✅", custom_id="sol_ok_v7", row=0)
        async def aprobar(self, inter, btn):
            if _es_co_owner(inter.user):
                return await inter.response.send_message(
                    "❌ Como **CO-OWNER** no puedes aprobar solicitudes.\n"
                    "Usa el botón **Solicitar aprobación OWNER** para escalar la decisión.",
                    ephemeral=True,
                )
            if not _puede_aprobar(inter.user):
                return await inter.response.send_message("Solo staff autorizado puede aprobar.", ephemeral=True)
            reg = actualizar(self.solicitud_id, estado="resuelta", resolucion="Aprobada",
                             responsable_id=inter.user.id, fecha_actualizacion=_now()) or obtener(self.solicitud_id)
            await inter.response.send_message(
                f"Aprobada por {inter.user.mention}",
                embed=embed_ticket(reg or {}, inter.guild))
            if reg and reg.get("usuario_id"):
                try:
                    u = inter.client.get_user(int(reg["usuario_id"]))
                    if u:
                        await u.send(f"Tu solicitud #{self.solicitud_id:04d} fue aprobada.")
                except Exception:
                    pass

        @ui.button(label="Rechazar", style=discord.ButtonStyle.danger, emoji="❌", custom_id="sol_no_v7", row=0)
        async def rechazar(self, inter, btn):
            if _es_co_owner(inter.user):
                return await inter.response.send_message(
                    "❌ Como **CO-OWNER** no puedes rechazar solicitudes.\n"
                    "Usa el botón **Solicitar aprobación OWNER** para escalar la decisión.",
                    ephemeral=True,
                )
            if not _puede_aprobar(inter.user):
                return await inter.response.send_message("Solo staff autorizado puede rechazar.", ephemeral=True)
            await inter.response.send_modal(MotivoRechazo(self.bot, self.solicitud_id))

        @ui.button(label="Hacer entrevista", style=discord.ButtonStyle.primary, emoji="🎤", custom_id="sol_ent_v7", row=0)
        async def entrevista(self, inter, btn):
            await _crear_entrevista(self.bot, inter, self.solicitud_id)

        @ui.button(label="Solicitar aprobación OWNER", style=discord.ButtonStyle.secondary, emoji="🔐", custom_id="sol_esc_v7", row=1)
        async def solicitar_owner(self, inter, btn):
            await _solicitar_aprobacion_owner(self.bot, inter, self.solicitud_id)

        @ui.button(label="Añadir personas", style=discord.ButtonStyle.secondary, emoji="👥", custom_id="sol_add_v7", row=1)
        async def adduser(self, inter, btn):
            if not _puede(inter.user):
                return await inter.response.send_message("Solo staff.", ephemeral=True)
            if not inter.guild:
                return
            try:
                from ticket_adduser import AnadirUsuarioView
                await inter.response.send_message(
                    "Añadir persona:",
                    view=AnadirUsuarioView(self.bot, self.solicitud_id, inter.guild),
                    ephemeral=True)
            except Exception as e:
                await inter.response.send_message(f"Error: {e}", ephemeral=True)

        @ui.button(label="Transcribir y cerrar", style=discord.ButtonStyle.secondary, emoji="📜", custom_id="sol_cls_v7", row=1)
        async def cerrar(self, inter, btn):
            if not _puede(inter.user):
                return await inter.response.send_message("Solo staff.", ephemeral=True)
            await inter.response.send_message(
                "¿Cerrar con transcripción?",
                view=ConfirmarCierre(self.bot, self.solicitud_id),
                ephemeral=True)

    mod.TicketSolicitudView = TicketSolicitudView

    class PanelDecisionLog(ui.View):
        """Panel en log RRHH: Aprobar | Rechazar | Entrevista | Solicitar OWNER | Ir al ticket."""
        def __init__(self, bot, sid):
            super().__init__(timeout=None)
            self.bot, self.sid = bot, sid

        @ui.button(label="Aprobar", style=discord.ButtonStyle.success, emoji="✅", custom_id="sol_log_ok_v7", row=0)
        async def ap(self, inter, btn):
            v = TicketSolicitudView(self.bot, self.sid)
            await v.aprobar(inter, btn)

        @ui.button(label="Rechazar", style=discord.ButtonStyle.danger, emoji="❌", custom_id="sol_log_no_v7", row=0)
        async def re(self, inter, btn):
            if _es_co_owner(inter.user):
                return await inter.response.send_message(
                    "❌ Como **CO-OWNER** no puedes rechazar. Usa **Solicitar aprobación OWNER**.",
                    ephemeral=True,
                )
            if not _puede_aprobar(inter.user):
                return await inter.response.send_message("Solo staff autorizado.", ephemeral=True)
            await inter.response.send_modal(MotivoRechazo(self.bot, self.sid))

        @ui.button(label="Hacer entrevista", style=discord.ButtonStyle.primary, emoji="🎤", custom_id="sol_log_ent_v7", row=0)
        async def entrevista(self, inter, btn):
            await _crear_entrevista(self.bot, inter, self.sid)

        @ui.button(label="Solicitar aprobación OWNER", style=discord.ButtonStyle.secondary, emoji="🔐", custom_id="sol_log_esc_v7", row=1)
        async def solicitar_owner(self, inter, btn):
            await _solicitar_aprobacion_owner(self.bot, inter, self.sid)

        @ui.button(label="Ir al ticket", style=discord.ButtonStyle.secondary, emoji="🎫", custom_id="sol_log_go_v7", row=1)
        async def go(self, inter, btn):
            reg = obtener(self.sid)
            if not reg or not reg.get("canal_id"):
                return await inter.response.send_message("No encontrado.", ephemeral=True)
            ch = inter.client.get_channel(int(reg["canal_id"]))
            await inter.response.send_message(f"{ch.mention}" if ch else "Eliminado.", ephemeral=True)

    mod.PanelDecisionView = PanelDecisionLog

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
            if old:
                cs._categoria_canal = old
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
                        except Exception:
                            pass
                if menc:
                    await canal.send("Involucrados: " + " ".join(menc))
            log_ch = None
            try:
                import logs_store
                log_ch = logs_store.resolver_canal_log(bot, guild, "log_solicitudes")
                if not log_ch:
                    log_ch = logs_store.resolver_canal_log(bot, guild, "aprobaciones_rrhh")
            except Exception:
                pass
            rrhh_ping = ""
            try:
                import roles_store
                rid = roles_store.obtener_id_key("DIRECTOR_RRHH") or roles_store.obtener_id_key("RRHH")
                if rid and guild:
                    rol = guild.get_role(int(rid))
                    if rol:
                        rrhh_ping = rol.mention + " "
            except Exception:
                pass
            if log_ch and reg:
                emb = embed_ticket(reg, guild)
                emb.title = f"Nueva solicitud #{int(reg['id']):04d}"
                chm = canal.mention if canal else "—"
                await log_ch.send(
                    content=f"{rrhh_ping}Nueva solicitud · {chm}",
                    embed=emb, view=PanelDecisionLog(bot, int(reg["id"])))
        except Exception as e:
            print("[cs_ui] post-crear:", e)

    mod.crear_ticket_solicitud = crear

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

        mod.enviar_log_solicitud = enviar_log_solicitud
    except Exception as e:
        print("[cs_ui] enviar_log patch:", e)

    if hasattr(mod, "registrar"):
        _or = mod.registrar

        def registrar(bot):
            _or(bot)
            try:
                bot.add_view(TicketSolicitudView(bot, 0))
                bot.add_view(PanelDecisionLog(bot, 0))
                bot.add_view(EntrevistaCanalView(bot, 0))
            except Exception:
                pass

        mod.registrar = registrar

    print("[cs_ui] OK — Aprobar|Rechazar|Entrevista|Solicitar OWNER|Añadir|Cerrar (CO_OWNER no aprueba)")
