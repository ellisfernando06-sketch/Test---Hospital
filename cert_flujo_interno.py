# -*- coding: utf-8 -*-
"""
cert_flujo_interno.py
=====================
- UN solo embed completo con todos los datos de la certificación.
- Ese embed pide las firmas (botones); el resto es interno.
- El bot detecta quién tiene los roles de cada firma requerida.
- Si una persona tiene 2 o 3 roles, recibe UNA sola solicitud con todas sus firmas.
- El certificado final solo se envía por MD al Director de Docencia y al graduado.
"""
from __future__ import annotations

import traceback
from typing import Dict, List, Optional, Set, Tuple

import discord
from discord import ui, app_commands
from discord.ext import commands

import config

try:
    import permisos
except Exception:
    permisos = None

try:
    import certificaciones_abiertas
except Exception:
    certificaciones_abiertas = None

try:
    import roles_store
except Exception:
    roles_store = None

_DIR_DEPT = [
    ("DIRECTOR_MEDICO", "🩺 Cuerpo Médico / Ala Médica"),
    ("DIRECTOR_ENFERMERIA", "💉 Enfermería"),
    ("DIRECTOR_ADMINISTRATIVO", "📋 Administración"),
    ("DIRECTOR_RRHH", "👥 Recursos Humanos"),
    ("DIRECTOR_FINANCIERO", "💰 Finanzas"),
    ("DIRECTOR_LOGISTICA", "📦 Logística"),
    ("DIRECTOR_SEGURIDAD", "🛡️ Seguridad"),
    ("DIRECTOR_DOCENCIA", "📚 Investigación y Docencia"),
    ("DIRECTOR_DISCIPLINA", "⚖️ Disciplina"),
    ("DIRECTOR_GENERAL", "🖥️ Dirección General"),
]

KEY_ENC = "ENCARGADO"
KEY_DOC = "DIRECTOR_DOCENCIA"


def _puede_iniciar(member) -> bool:
    if not isinstance(member, discord.Member):
        return False
    if member.guild_permissions.administrator:
        return True
    if not permisos:
        return False
    return bool(
        permisos.member_tiene_alguna_key(
            member,
            "OWNER", "CO_OWNER", "DIRECTOR_DOCENCIA", "DIRECTOR_GENERAL",
            "DIRECTOR", "ENCARGADO_AREA", "JEFE_DEPARTAMENTO", "SUPERVISOR",
            "DIRECTOR_MEDICO", "DIRECTOR_ENFERMERIA", "DIRECTOR_ADMINISTRATIVO",
            "DIRECTOR_RRHH", "DIRECTOR_LOGISTICA",
        )
    )


def _member_keys(member: discord.Member) -> Set[str]:
    """Keys de cargo que tiene el miembro (por roles configurados)."""
    out: Set[str] = set()
    if member.guild_permissions.administrator:
        out.update({"OWNER", "CO_OWNER", KEY_DOC, KEY_ENC, "DIRECTOR_GENERAL"})
    if not roles_store:
        return out
    try:
        keys_map = getattr(config, "KEYS_NOMBRES", {}) or {}
        for key in keys_map:
            rid = roles_store.obtener_id_key(key)
            if not rid:
                continue
            rol = member.guild.get_role(rid)
            if rol and rol in member.roles:
                out.add(key)
    except Exception:
        pass
    if permisos:
        try:
            for key in list(getattr(config, "KEYS_NOMBRES", {}) or {}):
                if permisos.member_tiene_alguna_key(member, key):
                    out.add(key)
        except Exception:
            pass
    return out


def _miembros_por_key(guild: discord.Guild, key: str) -> List[discord.Member]:
    if not roles_store:
        return []
    rid = roles_store.obtener_id_key(key)
    if not rid:
        return []
    rol = guild.get_role(rid)
    if not rol:
        return []
    return [m for m in rol.members if not m.bot]


def _estado_firmas(reg: dict) -> str:
    e = "✅" if reg.get("aprobado_encargado") else "⏳"
    d = "✅" if reg.get("aprobado_docencia") else "⏳"
    z = "✅" if reg.get("aprobado_director_zona") else "⏳"
    return (
        f"{e} Encargado / Instructor\n"
        f"{d} Director de Investigación y Docencia\n"
        f"{z} Director del Ala / Departamento"
    )


def _embed_completo(reg: dict, receptor_mention: str = "") -> discord.Embed:
    """Un único embed con todos los datos de la certificación + estado de firmas."""
    uid = reg.get("receptor_id")
    mention = receptor_mention or (f"<@{uid}>" if uid else "—")
    nombre = reg.get("nombre_receptor") or mention
    cap = reg.get("capacitacion") or "Certificación"
    depto = reg.get("departamento") or "—"
    cedula = reg.get("cedula") or "—"
    num = reg.get("numero") or f"CERT-{reg.get('id', 0):05d}"
    desc = (reg.get("descripcion") or "").strip()
    enc = reg.get("encargado_nombre") or "—"
    zona = reg.get("key_director_zona") or "—"
    nombre_zona = next((n for k, n in _DIR_DEPT if k == zona), zona)

    emb = discord.Embed(
        title=f"🎓 Solicitud de certificación · #{reg.get('id', '?')}",
        description=(
            f"Documento de acreditación hospitalaria (flujo interno).\n"
            f"Firma con el botón que corresponda a **tu cargo**. "
            f"Si tienes varios cargos, puedes firmar todos desde este mismo mensaje."
        ),
        color=0x1A5276,
        timestamp=discord.utils.utcnow(),
    )
    emb.add_field(name="👤 Graduado", value=f"{mention}\n`{nombre}`", inline=True)
    emb.add_field(name="🪪 Identificación", value=str(cedula)[:80], inline=True)
    emb.add_field(name="📋 Folio", value=f"`{num}`", inline=True)
    emb.add_field(name="📜 Certificación / capacitación", value=str(cap)[:200], inline=False)
    emb.add_field(name="🏥 Ala / Departamento", value=str(depto)[:120], inline=True)
    emb.add_field(name="🖋️ Director de zona requerido", value=str(nombre_zona)[:120], inline=True)
    emb.add_field(name="👨‍🏫 Instructor / Encargado", value=str(enc)[:120], inline=True)
    if desc:
        emb.add_field(name="📝 Observaciones", value=desc[:400], inline=False)
    emb.add_field(name="✍️ Estado de firmas", value=_estado_firmas(reg), inline=False)
    emb.set_footer(text="Solo firmantes autorizados · Sin anuncios públicos · RP hospital")
    return emb


def _roles_firma_para(member: discord.Member, reg: dict) -> Set[str]:
    """Qué firmas puede aportar este miembro según sus roles."""
    keys = _member_keys(member)
    puede: Set[str] = set()
    # Encargado: quien inició, ENCARGADO, jefes, o OWNER
    if (
        member.id == int(reg.get("encargado_id") or 0)
        or "ENCARGADO" in keys
        or "ENCARGADO_AREA" in keys
        or "JEFE_DEPARTAMENTO" in keys
        or "SUPERVISOR" in keys
        or "OWNER" in keys
        or "CO_OWNER" in keys
    ):
        puede.add("encargado")
    if KEY_DOC in keys or "OWNER" in keys or "CO_OWNER" in keys:
        puede.add("docencia")
    zona = reg.get("key_director_zona") or "DIRECTOR_ADMINISTRATIVO"
    if zona in keys or "OWNER" in keys or "CO_OWNER" in keys or "DIRECTOR_GENERAL" in keys:
        puede.add("zona")
    return puede


class VistaFirmasUnica(ui.View):
    """Una vista con hasta 3 botones de firma; cada usuario solo usa los de su rol."""

    def __init__(self, bot: commands.Bot, aid: int, allowed_roles: Optional[Set[str]] = None):
        super().__init__(timeout=None)
        self.bot = bot
        self.aid = int(aid)
        self.allowed_roles = allowed_roles  # si None, todos los botones; al interactuar se valida

    async def _refresh_msg(self, inter: discord.Interaction, reg: dict):
        try:
            emb = _embed_completo(reg)
            await inter.message.edit(embed=emb, view=self if reg.get("estado") == "pendiente" else None)
        except Exception:
            pass

    async def _try_emit(self, inter: discord.Interaction, reg: dict) -> bool:
        import firmas as F

        if not (
            reg.get("aprobado_encargado")
            and reg.get("aprobado_docencia")
            and reg.get("aprobado_director_zona")
        ):
            return False
        if reg.get("estado") != "pendiente":
            return False
        try:
            await F._emitir_certificado_autorizado(self.bot, inter, reg)
            F.actualizar_autorizacion(self.aid, estado="autorizado")
            return True
        except Exception as e:
            print("[cert_interno] emit:", e)
            traceback.print_exc()
            try:
                await inter.followup.send(f"❌ Error al emitir: `{e}`", ephemeral=True)
            except Exception:
                pass
            return False

    async def _firmar(
        self,
        inter: discord.Interaction,
        tipo: str,
        flag: str,
        id_field: str,
        nombre_field: str,
        firma_field: str,
        key_firma: Optional[str] = None,
    ):
        import firmas as F

        reg = F.obtener_autorizacion(self.aid)
        if not reg or reg.get("estado") != "pendiente":
            return await inter.response.send_message("Ya resuelta o no existe.", ephemeral=True)

        if not isinstance(inter.user, discord.User):
            return await inter.response.send_message("Error de usuario.", ephemeral=True)

        # Validar rol (en MD no hay Member del guild; intentar resolver)
        guild = None
        member = None
        if inter.guild and isinstance(inter.user, discord.Member):
            guild = inter.guild
            member = inter.user
        else:
            # MD: buscar en guilds del bot
            for g in self.bot.guilds:
                m = g.get_member(inter.user.id)
                if m:
                    guild = g
                    member = m
                    break

        if member:
            puede = _roles_firma_para(member, reg)
            if tipo not in puede:
                return await inter.response.send_message(
                    f"❌ No tienes el rol para firmar como **{tipo}**.",
                    ephemeral=True,
                )
        # Si ya firmó ese tipo
        if reg.get(flag):
            return await inter.response.send_message("Esa firma ya está registrada.", ephemeral=True)

        firma = F.obtener_firma_usuario(inter.user.id)
        if key_firma and not firma:
            firma = F.obtener_firma_key(key_firma)
        if not firma:
            return await inter.response.send_message(
                "❌ Sin firma digital. Usa `/registrar_firma` primero.",
                ephemeral=True,
            )

        await inter.response.defer(ephemeral=True)
        kwargs = {
            flag: True,
            id_field: inter.user.id,
            nombre_field: getattr(inter.user, "display_name", str(inter.user)),
            firma_field: firma.get("file"),
        }
        reg = F.actualizar_autorizacion(self.aid, **kwargs) or reg
        done = await self._try_emit(inter, reg)
        reg = F.obtener_autorizacion(self.aid) or reg
        await self._refresh_msg(inter, reg)

        if done:
            await inter.followup.send(
                "✅ Firma registrada. **Certificado emitido** (enviado a Docencia y al graduado).",
                ephemeral=True,
            )
        else:
            await inter.followup.send(
                f"✅ Firma **{tipo}** registrada.\n{_estado_firmas(reg)}",
                ephemeral=True,
            )

    @ui.button(label="✅ Firmar · Encargado", style=discord.ButtonStyle.success, custom_id="cert1_enc")
    async def btn_enc(self, inter: discord.Interaction, _b: ui.Button):
        await self._firmar(
            inter, "encargado", "aprobado_encargado",
            "encargado_id", "encargado_nombre", "firma_encargado",
        )

    @ui.button(label="✅ Firmar · Docencia", style=discord.ButtonStyle.primary, custom_id="cert1_doc")
    async def btn_doc(self, inter: discord.Interaction, _b: ui.Button):
        await self._firmar(
            inter, "docencia", "aprobado_docencia",
            "docencia_id", "docencia_nombre", "firma_docencia",
            key_firma=KEY_DOC,
        )

    @ui.button(label="✅ Firmar · Director del Ala", style=discord.ButtonStyle.secondary, custom_id="cert1_zona")
    async def btn_zona(self, inter: discord.Interaction, _b: ui.Button):
        import firmas as F

        reg = F.obtener_autorizacion(self.aid) or {}
        await self._firmar(
            inter, "zona", "aprobado_director_zona",
            "director_zona_id", "director_zona_nombre", "firma_director_zona",
            key_firma=reg.get("key_director_zona"),
        )

    @ui.button(label="❌ Rechazar", style=discord.ButtonStyle.danger, custom_id="cert1_no")
    async def btn_no(self, inter: discord.Interaction, _b: ui.Button):
        import firmas as F

        reg = F.obtener_autorizacion(self.aid)
        if not reg or reg.get("estado") != "pendiente":
            return await inter.response.send_message("Ya resuelta.", ephemeral=True)
        F.actualizar_autorizacion(self.aid, estado="rechazado")
        await inter.response.send_message("❌ Certificación rechazada.", ephemeral=True)
        try:
            await inter.message.edit(view=None)
        except Exception:
            pass


async def _enviar_solicitudes_por_roles(
    bot: commands.Bot,
    guild: discord.Guild,
    reg: dict,
    receptor: discord.Member,
) -> int:
    """
    Detecta miembros por rol y envía UN embed por persona.
    Si alguien tiene varios roles de firma, recibe un solo mensaje con los 3 botones.
    """
    aid = int(reg["id"])
    emb = _embed_completo(reg, receptor.mention)

    # Mapa uid -> set de firmas que puede hacer
    destinos: Dict[int, Set[str]] = {}

    def _add(m: discord.Member, tipo: str):
        if m.bot:
            return
        destinos.setdefault(m.id, set()).add(tipo)

    # Encargado (quien inicia) siempre puede firmar de encargado
    enc_id = int(reg.get("encargado_id") or 0)
    if enc_id:
        m = guild.get_member(enc_id)
        if m:
            _add(m, "encargado")

    for m in _miembros_por_key(guild, "ENCARGADO") + _miembros_por_key(guild, "ENCARGADO_AREA"):
        _add(m, "encargado")
    for m in _miembros_por_key(guild, "JEFE_DEPARTAMENTO") + _miembros_por_key(guild, "SUPERVISOR"):
        _add(m, "encargado")

    for m in _miembros_por_key(guild, KEY_DOC):
        _add(m, "docencia")

    zona = reg.get("key_director_zona") or "DIRECTOR_ADMINISTRATIVO"
    for m in _miembros_por_key(guild, zona):
        _add(m, "zona")

    # OWNER / CO_OWNER pueden todo
    for key in ("OWNER", "CO_OWNER", "DIRECTOR_GENERAL"):
        for m in _miembros_por_key(guild, key):
            destinos.setdefault(m.id, set()).update({"encargado", "docencia", "zona"})

    enviados = 0
    for uid, tipos in destinos.items():
        m = guild.get_member(uid)
        if not m:
            continue
        view = VistaFirmasUnica(bot, aid, allowed_roles=tipos)
        try:
            await m.send(
                content=(
                    f"🎓 **Solicitud de firmas** — puedes firmar: "
                    + ", ".join(sorted(tipos))
                ),
                embed=emb,
                view=view,
            )
            enviados += 1
        except discord.Forbidden:
            continue
        except Exception as e:
            print("[cert_interno] DM:", e)
            continue

    return enviados


def _patch_firmas(bot: commands.Bot) -> None:
    import firmas as F

    bot.add_view(VistaFirmasUnica(bot, 0))

    async def solicitar_autorizacion_certificado(
        bot_,
        inter,
        *,
        receptor,
        certificacion,
        cedula="",
        descripcion="",
        departamento="",
        firma_encargado_file=None,
        director_zona_key=None,
    ) -> int:
        num = "CERT-PEND"
        try:
            import docencia as _doc

            reg_d = _doc.emitir(
                receptor.id,
                certificacion.get("nombre"),
                "personalizado",
                descripcion,
                inter.user.id,
                notas="pendiente autorización (embed único)",
                departamento=departamento,
            )
            num = f"CERT-{int(reg_d.get('id') or 0):05d}"
        except Exception as e:
            print("[cert_interno] docencia.emitir:", e)

        zona_key = (
            director_zona_key
            or certificacion.get("director_zona_key")
            or "DIRECTOR_ADMINISTRATIVO"
        )
        nombre_zona = next((n for k, n in _DIR_DEPT if k == zona_key), zona_key)

        aid = F.nueva_autorizacion(
            {
                "tipo": "certificado",
                "key_docencia": KEY_DOC,
                "key_director_zona": zona_key,
                "receptor_id": receptor.id,
                "nombre_receptor": getattr(receptor, "display_name", str(receptor)),
                "capacitacion": certificacion.get("nombre", "Certificación"),
                "descripcion": descripcion,
                "departamento": departamento or nombre_zona,
                "cedula": cedula,
                "certificacion_id": certificacion.get("id"),
                "encargado_id": inter.user.id,
                "encargado_nombre": getattr(inter.user, "display_name", str(inter.user)),
                "firma_encargado": firma_encargado_file,
                "canal_id": None,  # no publicar en canal de trabajo
                "numero": num,
            }
        )
        reg = F.obtener_autorizacion(aid) or {"id": aid, "numero": num}

        guild = inter.guild
        n = 0
        if guild:
            n = await _enviar_solicitudes_por_roles(bot_, guild, reg, receptor)

        return aid

    async def _emit_solo_docencia_y_graduado(bot_, inter, reg: dict):
        """Certificado solo por MD a Docencia + graduado (sin canal público)."""
        from certificado_imagen import generar_certificado

        uid = int(reg.get("receptor_id") or 0)
        guild = inter.guild
        if not guild and bot_.guilds:
            guild = bot_.guilds[0]
        receptor = guild.get_member(uid) if guild else None
        if not receptor and guild:
            try:
                receptor = await guild.fetch_member(uid)
            except Exception:
                receptor = None

        nombre = reg.get("nombre_receptor") or (receptor.display_name if receptor else str(uid))
        cap = reg.get("capacitacion") or "Certificación"
        hospital = getattr(config, "NOMBRE_HOSPITAL", "Hospital General") or "Hospital General"
        emisor = reg.get("encargado_nombre") or "Encargado"
        num = reg.get("numero") or f"CERT-{reg.get('id', 0):05d}"
        cedula = reg.get("cedula") or ""

        def _path(fn):
            return F.ruta_firma(fn) if fn else None

        buf = generar_certificado(
            nombre_receptor=nombre,
            titulo=cap,
            capacitacion=cap,
            hospital=hospital,
            emisor=emisor,
            numero=num,
            cedula=cedula,
            descripcion=reg.get("descripcion") or "",
            departamento=reg.get("departamento") or "",
            firma_encargado_path=_path(reg.get("firma_encargado")),
            firma_director_path=_path(reg.get("firma_docencia")),
            firma_director_zona_path=_path(reg.get("firma_director_zona")),
            label_encargado="Otorgado por / Encargado",
            label_director="Director de Investigación y Docencia",
            label_director_zona="Director del Ala / Departamento",
        )

        emb = discord.Embed(
            title="🎓 Certificado oficial emitido",
            description=(
                f"**Graduado:** <@{uid}>\n"
                f"**Certificación:** {cap}\n"
                f"**Ala / Depto:** {reg.get('departamento') or '—'}\n"
                f"**Identificación:** {cedula or '—'}\n"
                f"**Folio:** `{num}`\n"
                f"**Encargado:** {reg.get('encargado_nombre', emisor)}\n"
                f"**Docencia:** {reg.get('docencia_nombre', '—')}\n"
                f"**Director de zona:** {reg.get('director_zona_nombre', '—')}\n"
                f"📌 Documento de roleplay hospitalario"
            ),
            color=0x1A5276,
            timestamp=discord.utils.utcnow(),
        )

        # 1) Graduado
        if receptor:
            try:
                buf.seek(0)
                await receptor.send(
                    content=f"🎓 Tu certificado de **{cap}** ha sido autorizado.",
                    embed=emb,
                    file=discord.File(buf, filename=f"certificado_{uid}.png"),
                )
            except Exception as e:
                print("[cert_interno] DM graduado:", e)

        # 2) Directores de Docencia (y copia a quien firmó docencia)
        if guild:
            enviados_doc: Set[int] = set()
            for m in _miembros_por_key(guild, KEY_DOC):
                if m.id in enviados_doc or (receptor and m.id == receptor.id):
                    continue
                try:
                    buf2 = generar_certificado(
                        nombre_receptor=nombre,
                        titulo=cap,
                        capacitacion=cap,
                        hospital=hospital,
                        emisor=emisor,
                        numero=num,
                        cedula=cedula,
                        descripcion=reg.get("descripcion") or "",
                        departamento=reg.get("departamento") or "",
                        firma_encargado_path=_path(reg.get("firma_encargado")),
                        firma_director_path=_path(reg.get("firma_docencia")),
                        firma_director_zona_path=_path(reg.get("firma_director_zona")),
                        label_encargado="Otorgado por / Encargado",
                        label_director="Director de Investigación y Docencia",
                        label_director_zona="Director del Ala / Departamento",
                    )
                    await m.send(
                        content=f"🎓 Certificado emitido · **{cap}** · <@{uid}>",
                        embed=emb,
                        file=discord.File(buf2, filename=f"certificado_{uid}.png"),
                    )
                    enviados_doc.add(m.id)
                except Exception:
                    continue
            # Si firmó docencia y no está en el rol, también
            did = int(reg.get("docencia_id") or 0)
            if did and did not in enviados_doc and (not receptor or did != receptor.id):
                m = guild.get_member(did)
                if m:
                    try:
                        buf3 = generar_certificado(
                            nombre_receptor=nombre,
                            titulo=cap,
                            capacitacion=cap,
                            hospital=hospital,
                            emisor=emisor,
                            numero=num,
                            cedula=cedula,
                            descripcion=reg.get("descripcion") or "",
                            departamento=reg.get("departamento") or "",
                            firma_encargado_path=_path(reg.get("firma_encargado")),
                            firma_director_path=_path(reg.get("firma_docencia")),
                            firma_director_zona_path=_path(reg.get("firma_director_zona")),
                        )
                        await m.send(
                            content=f"🎓 Certificado emitido · **{cap}** · <@{uid}>",
                            embed=emb,
                            file=discord.File(buf3, filename=f"certificado_{uid}.png"),
                        )
                    except Exception:
                        pass

        # Sin publicación en canales públicos

    F.solicitar_autorizacion_certificado = solicitar_autorizacion_certificado
    F._emitir_certificado_autorizado = _emit_solo_docencia_y_graduado
    print("[cert_flujo_interno] firmas: 1 embed + detección de roles")


def _patch_certificar_ui(bot: commands.Bot) -> None:
    if not certificaciones_abiertas:
        return

    class DeptSelect(ui.Select):
        def __init__(self, bot_, usuario, cert):
            self.bot = bot_
            self.usuario = usuario
            self.cert = cert
            opts = [
                discord.SelectOption(label=nombre[:100], value=key, description=key[:100])
                for key, nombre in _DIR_DEPT
            ]
            super().__init__(placeholder="Elige ala / departamento…", options=opts)

        async def callback(self, inter: discord.Interaction):
            key = self.values[0]
            nombre = next((n for k, n in _DIR_DEPT if k == key), key)

            class ModalDatos(ui.Modal, title="Datos del certificado"):
                cedula = ui.TextInput(label="Identificación / cédula", required=False, max_length=80)
                observ = ui.TextInput(
                    label="Observaciones",
                    style=discord.TextStyle.paragraph,
                    required=False,
                    max_length=500,
                )

                async def on_submit(self2, inter2: discord.Interaction):
                    await inter2.response.defer(ephemeral=True)
                    import firmas as F

                    cert = dict(self.cert)
                    cert["director_zona_key"] = key
                    try:
                        aid = await F.solicitar_autorizacion_certificado(
                            self.bot,
                            inter2,
                            receptor=self.usuario,
                            certificacion=cert,
                            cedula=str(self2.cedula) if self2.cedula else "",
                            descripcion=str(self2.observ) if self2.observ else "",
                            departamento=nombre,
                            director_zona_key=key,
                        )
                        await inter2.followup.send(
                            f"✅ Solicitud **#{aid}** creada.\n"
                            f"• Se envió **un solo embed** completo a cada firmante según su **rol**.\n"
                            f"• Si alguien tiene varios cargos, recibe **una** solicitud con todas sus firmas.\n"
                            f"• El certificado final solo irá a **Docencia** y al **graduado**.",
                            ephemeral=True,
                        )
                    except Exception as e:
                        traceback.print_exc()
                        await inter2.followup.send(f"❌ {e}", ephemeral=True)

            await inter.response.send_modal(ModalDatos())

    class CertSelect(ui.Select):
        def __init__(self, bot_, usuario):
            self.bot = bot_
            self.usuario = usuario
            certificaciones_abiertas.asegurar_defaults()
            items = certificaciones_abiertas.listar_certificaciones_activas()[:25]
            if not items:
                opts = [discord.SelectOption(label="Sin certificaciones", value="none")]
                dis = True
            else:
                opts = [
                    discord.SelectOption(
                        label=str(x.get("nombre") or f"#{x.get('id')}")[:100],
                        value=str(x["id"]),
                        description=str(x.get("descripcion") or "")[:100],
                    )
                    for x in items
                ]
                dis = False
            super().__init__(placeholder="Elige la certificación…", options=opts, disabled=dis)

        async def callback(self, inter: discord.Interaction):
            val = self.values[0]
            if val in ("", "none"):
                return await inter.response.send_message("❌ Sin certificación.", ephemeral=True)
            cert = None
            for fn in ("obtener_certificacion", "obtener_certi"):
                if hasattr(certificaciones_abiertas, fn):
                    try:
                        cert = getattr(certificaciones_abiertas, fn)(int(val))
                        break
                    except Exception:
                        pass
            if not cert:
                items = certificaciones_abiertas.listar_certificaciones_activas()
                cert = next((x for x in items if str(x.get("id")) == val), None)
            if not cert:
                return await inter.response.send_message("❌ No encontrada.", ephemeral=True)
            view = ui.View(timeout=300)
            view.add_item(DeptSelect(self.bot, self.usuario, cert))
            await inter.response.send_message(
                f"🎓 **{cert.get('nombre')}** → {self.usuario.mention}\nElige **ala / departamento**:",
                view=view,
                ephemeral=True,
            )

    class SelView(ui.View):
        def __init__(self, bot_, usuario):
            super().__init__(timeout=300)
            self.add_item(CertSelect(bot_, usuario))

    try:
        bot.tree.remove_command("certificar")
    except Exception:
        pass

    @bot.tree.command(
        name="certificar",
        description="Certifica (1 embed + firmas por rol; certificado solo Docencia y graduado)",
    )
    @app_commands.describe(usuario="Estudiante / personal a certificar")
    async def certificar(inter: discord.Interaction, usuario: discord.Member):
        if not isinstance(inter.user, discord.Member):
            return await inter.response.send_message("❌ Solo en servidor.", ephemeral=True)
        if not _puede_iniciar(inter.user):
            return await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
        certificaciones_abiertas.asegurar_defaults()
        if not certificaciones_abiertas.listar_certificaciones_activas():
            return await inter.response.send_message("❌ No hay certificaciones activas.", ephemeral=True)
        await inter.response.send_message(
            f"🎓 Certificar a **{usuario.display_name}**\n"
            f"Certificación → Ala/depto → **un embed** a cada firmante según roles.",
            view=SelView(bot, usuario),
            ephemeral=True,
        )

    print("[cert_flujo_interno] /certificar listo")


def registrar(bot: commands.Bot) -> None:
    try:
        _patch_firmas(bot)
    except Exception:
        print("[cert_flujo_interno] error firmas:")
        traceback.print_exc()
    try:
        _patch_certificar_ui(bot)
    except Exception:
        print("[cert_flujo_interno] error ui:")
        traceback.print_exc()
    print("[cert_flujo_interno] OK")
