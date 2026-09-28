# -*- coding: utf-8 -*-
"""
cert_flujo_interno.py
=====================
- Sin anuncios públicos por cada firma: solo solicitudes internas (MD / canal privado).
- Las 3 firmas en cualquier orden; al completar las 3 se emite el certificado.
- Emisión del certificado más discreta (canal de logs, no spam).
- /certificar permite elegir ala/departamento (director del área).
"""
from __future__ import annotations

import traceback
from typing import Optional

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

# Claves de director por departamento / ala
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


async def _dm_role_key(guild: discord.Guild, key: str, embed: discord.Embed, view: ui.View) -> int:
    """Envía MD a miembros con esa key. Devuelve cuántos."""
    import roles_store
    n = 0
    rid = roles_store.obtener_id_key(key)
    if not rid:
        return 0
    rol = guild.get_role(rid)
    if not rol:
        return 0
    for m in rol.members:
        if m.bot:
            continue
        try:
            await m.send(embed=embed, view=view)
            n += 1
        except Exception:
            continue
    return n


def _patch_firmas(bot: commands.Bot) -> None:
    import firmas as F

    async def _try_emit(bot_, inter, aid: int):
        reg = F.obtener_autorizacion(aid)
        if not reg or reg.get("estado") != "pendiente":
            return False
        if not (
            reg.get("aprobado_encargado")
            and reg.get("aprobado_docencia")
            and reg.get("aprobado_director_zona")
        ):
            return False
        try:
            if (reg.get("tipo") or "") == "certificado":
                await F._emitir_certificado_autorizado(bot_, inter, reg)
            F.actualizar_autorizacion(aid, estado="autorizado")
            return True
        except Exception as e:
            print("[cert_interno] emit:", e)
            traceback.print_exc()
            try:
                await inter.followup.send(f"❌ Error al emitir certificado: `{e}`", ephemeral=True)
            except Exception:
                pass
            return False

    class VistaEnc(ui.View):
        def __init__(self, bot_: commands.Bot, aid: int):
            super().__init__(timeout=None)
            self.bot = bot_
            self.aid = int(aid)

        @ui.button(label="✅ Firmar (Encargado)", style=discord.ButtonStyle.success, custom_id="cert_enc_ok")
        async def ok(self, inter: discord.Interaction, _b: ui.Button):
            reg = F.obtener_autorizacion(self.aid)
            if not reg or reg.get("estado") != "pendiente":
                return await inter.response.send_message("Ya resuelta.", ephemeral=True)
            firma = F.obtener_firma_usuario(inter.user.id)
            if not firma:
                return await inter.response.send_message(
                    "❌ Sin firma. Usa `/registrar_firma`.", ephemeral=True
                )
            await inter.response.defer(ephemeral=True)
            F.actualizar_autorizacion(
                self.aid,
                aprobado_encargado=True,
                encargado_id=inter.user.id,
                encargado_nombre=getattr(inter.user, "display_name", str(inter.user)),
                firma_encargado=firma.get("file"),
            )
            done = await _try_emit(self.bot, inter, self.aid)
            if done:
                await inter.followup.send("✅ Tu firma quedó registrada. **Certificado emitido.**", ephemeral=True)
            else:
                await inter.followup.send(
                    "✅ Firma de encargado registrada. Pendientes otras firmas (cualquier orden).",
                    ephemeral=True,
                )
            try:
                await inter.message.edit(view=None)
            except Exception:
                pass

        @ui.button(label="❌ Rechazar", style=discord.ButtonStyle.danger, custom_id="cert_enc_no")
        async def no(self, inter: discord.Interaction, _b: ui.Button):
            F.actualizar_autorizacion(self.aid, estado="rechazado")
            await inter.response.send_message("❌ Certificado rechazado.", ephemeral=True)
            try:
                await inter.message.edit(view=None)
            except Exception:
                pass

    class VistaDoc(ui.View):
        def __init__(self, bot_: commands.Bot, aid: int):
            super().__init__(timeout=None)
            self.bot = bot_
            self.aid = int(aid)

        @ui.button(label="✅ Firmar (Docencia)", style=discord.ButtonStyle.success, custom_id="cert_doc_ok")
        async def ok(self, inter: discord.Interaction, _b: ui.Button):
            reg = F.obtener_autorizacion(self.aid)
            if not reg or reg.get("estado") != "pendiente":
                return await inter.response.send_message("Ya resuelta.", ephemeral=True)
            if not F._es_key(inter.user, F.KEY_DOCENCIA, "OWNER", "CO_OWNER"):
                return await inter.response.send_message(
                    "❌ Solo Director de Docencia / OWNER.", ephemeral=True
                )
            firma = F.obtener_firma_usuario(inter.user.id) or F.obtener_firma_key(F.KEY_DOCENCIA)
            if not firma:
                return await inter.response.send_message(
                    "❌ Sin firma. Usa `/registrar_firma`.", ephemeral=True
                )
            await inter.response.defer(ephemeral=True)
            F.actualizar_autorizacion(
                self.aid,
                aprobado_docencia=True,
                docencia_id=inter.user.id,
                docencia_nombre=getattr(inter.user, "display_name", str(inter.user)),
                firma_docencia=firma.get("file"),
            )
            done = await _try_emit(self.bot, inter, self.aid)
            if done:
                await inter.followup.send("✅ Firma de Docencia registrada. **Certificado emitido.**", ephemeral=True)
            else:
                await inter.followup.send(
                    "✅ Firma de Docencia registrada. Pendientes otras firmas.",
                    ephemeral=True,
                )
            try:
                await inter.message.edit(view=None)
            except Exception:
                pass

        @ui.button(label="❌ Rechazar", style=discord.ButtonStyle.danger, custom_id="cert_doc_no")
        async def no(self, inter: discord.Interaction, _b: ui.Button):
            if not F._es_key(inter.user, F.KEY_DOCENCIA, "OWNER", "CO_OWNER"):
                return await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
            F.actualizar_autorizacion(self.aid, estado="rechazado")
            await inter.response.send_message("❌ Certificado rechazado por Docencia.", ephemeral=True)
            try:
                await inter.message.edit(view=None)
            except Exception:
                pass

    class VistaZona(ui.View):
        def __init__(self, bot_: commands.Bot, aid: int, key_zona: str):
            super().__init__(timeout=None)
            self.bot = bot_
            self.aid = int(aid)
            self.key_zona = key_zona

        @ui.button(label="✅ Firmar (Director del Ala)", style=discord.ButtonStyle.success, custom_id="cert_zona_ok")
        async def ok(self, inter: discord.Interaction, _b: ui.Button):
            reg = F.obtener_autorizacion(self.aid)
            if not reg or reg.get("estado") != "pendiente":
                return await inter.response.send_message("Ya resuelta.", ephemeral=True)
            key = reg.get("key_director_zona") or self.key_zona
            if not F._es_key(inter.user, key, "OWNER", "CO_OWNER", "DIRECTOR_GENERAL"):
                return await inter.response.send_message(
                    f"❌ Solo el director del área (`{key}`).",
                    ephemeral=True,
                )
            firma = F.obtener_firma_usuario(inter.user.id) or F.obtener_firma_key(key)
            if not firma:
                return await inter.response.send_message(
                    "❌ Sin firma. Usa `/registrar_firma`.", ephemeral=True
                )
            await inter.response.defer(ephemeral=True)
            F.actualizar_autorizacion(
                self.aid,
                aprobado_director_zona=True,
                director_zona_id=inter.user.id,
                director_zona_nombre=getattr(inter.user, "display_name", str(inter.user)),
                firma_director_zona=firma.get("file"),
            )
            done = await _try_emit(self.bot, inter, self.aid)
            if done:
                await inter.followup.send("✅ Firma del Ala registrada. **Certificado emitido.**", ephemeral=True)
            else:
                await inter.followup.send(
                    "✅ Firma del Ala registrada. Pendientes otras firmas.",
                    ephemeral=True,
                )
            try:
                await inter.message.edit(view=None)
            except Exception:
                pass

        @ui.button(label="❌ Rechazar", style=discord.ButtonStyle.danger, custom_id="cert_zona_no")
        async def no(self, inter: discord.Interaction, _b: ui.Button):
            F.actualizar_autorizacion(self.aid, estado="rechazado")
            await inter.response.send_message("❌ Certificado rechazado por Director del Ala.", ephemeral=True)
            try:
                await inter.message.edit(view=None)
            except Exception:
                pass

    # Vistas persistentes
    bot.add_view(VistaEnc(bot, 0))
    bot.add_view(VistaDoc(bot, 0))
    bot.add_view(VistaZona(bot, 0, "DIRECTOR_ADMINISTRATIVO"))

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
                notas="pendiente autorización (flujo interno)",
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
                "key_docencia": F.KEY_DOCENCIA,
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
                "canal_id": inter.channel.id if inter.channel else None,
                "numero": num,
            }
        )

        base_desc = (
            f"**Graduado:** {receptor.mention}\n"
            f"**Certificación:** {certificacion.get('nombre', '—')}\n"
            f"**Ala / Depto:** {departamento or nombre_zona}\n"
            f"**ID:** {cedula or '—'}\n"
            f"**Folio:** `{num}` · **Solicitud #{aid}**\n"
            f"**Instructor:** {inter.user.mention}\n\n"
            f"_Firma en cualquier orden. Al completar las 3 se emite el certificado._"
        )
        if descripcion:
            base_desc += f"\n\n**Obs.:** {descripcion[:400]}"

        emb_enc = discord.Embed(
            title=f"🖋️ Firma requerida · Encargado · #{aid}",
            description=base_desc,
            color=0x2C3E50,
        )
        emb_doc = discord.Embed(
            title=f"🖋️ Firma requerida · Docencia · #{aid}",
            description=base_desc,
            color=0x8E44AD,
        )
        emb_zona = discord.Embed(
            title=f"🖋️ Firma requerida · {nombre_zona} · #{aid}",
            description=base_desc,
            color=0x1ABC9C,
        )

        v1, v2, v3 = VistaEnc(bot_, aid), VistaDoc(bot_, aid), VistaZona(bot_, aid, zona_key)

        # Solo MD a los firmantes + un aviso efímero al instructor (sin spam público)
        guild = inter.guild
        enviados = 0
        if guild:
            # Encargado (quien inicia) — MD propio
            try:
                await inter.user.send(embed=emb_enc, view=v1)
                enviados += 1
            except Exception:
                pass
            enviados += await _dm_role_key(guild, F.KEY_DOCENCIA, emb_doc, v2)
            enviados += await _dm_role_key(guild, zona_key, emb_zona, v3)

            # Si no hubo MD, un solo mensaje en canal de aprobaciones (no 3 anuncios)
            if enviados == 0:
                dest = None
                try:
                    import logs_store

                    dest = logs_store.resolver_canal_log(bot_, guild, "aprobaciones") or logs_store.resolver_canal_log(
                        bot_, guild, "log_certificados"
                    )
                except Exception:
                    dest = None
                if dest:
                    await dest.send(
                        content="**Solicitudes de firma (interno)** — no es anuncio público.",
                        embeds=[emb_enc, emb_doc, emb_zona],
                        view=v1,
                    )
                    # Views extra en mensajes separados mínimos solo si hace falta
                    await dest.send(embed=emb_doc, view=v2)
                    await dest.send(embed=emb_zona, view=v3)

        return aid

    # Silenciar publicación ruidosa del certificado en el canal del comando:
    # solo log_certificados + DM al graduado
    _orig_emit = F._emitir_certificado_autorizado

    async def _emit_silencioso(bot_, inter, reg: dict):
        # Monkey: temporarily null canal_id so no posta en canal de trabajo
        reg = dict(reg)
        canal_trabajo = reg.get("canal_id")
        reg["canal_id"] = None
        # Emitir (genera imagen + DM)
        await _orig_emit(bot_, inter, reg)
        # Publicar solo en log de certificados si existe
        try:
            import logs_store
            from certificado_imagen import generar_certificado

            guild = inter.guild
            dest = logs_store.resolver_canal_log(bot_, guild, "log_certificados") if guild else None
            if dest:
                uid = int(reg.get("receptor_id") or 0)
                cap = reg.get("capacitacion") or "Certificación"
                num = reg.get("numero") or f"CERT-{reg.get('id', 0):05d}"
                await dest.send(
                    content=f"🎓 Certificado emitido · <@{uid}> · **{cap}** · `{num}`",
                )
        except Exception as e:
            print("[cert_interno] log emit:", e)

    F.solicitar_autorizacion_certificado = solicitar_autorizacion_certificado
    F._emitir_certificado_autorizado = _emit_silencioso
    F.VistaAutorizarEncargado = VistaEnc
    F.VistaAutorizarDocencia = VistaDoc
    F.VistaAutorizarDirectorZona = VistaZona
    print("[cert_flujo_interno] firmas parcheadas (interno + cualquier orden)")


def _patch_certificar_ui(bot: commands.Bot) -> None:
    """Reemplaza /certificar con selector de certificación + ala/departamento."""
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
            super().__init__(placeholder="Elige ala / departamento de la certificación…", options=opts)

        async def callback(self, inter: discord.Interaction):
            key = self.values[0]
            nombre = next((n for k, n in _DIR_DEPT if k == key), key)
            # Modal datos
            class ModalDatos(ui.Modal, title="Datos del certificado"):
                cedula = ui.TextInput(label="Identificación / cédula", required=False, max_length=80)
                observ = ui.TextInput(
                    label="Observaciones", style=discord.TextStyle.paragraph, required=False, max_length=500
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
                            f"✅ Solicitud **#{aid}** creada (flujo interno).\n"
                            f"• Certificación: **{cert.get('nombre')}**\n"
                            f"• Ala/Depto: **{nombre}**\n"
                            f"• Firmas pedidas por MD a Encargado, Docencia y Director del área.\n"
                            f"• Sin anuncios públicos por cada firma.",
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
            cert = certificaciones_abiertas.obtener_certificacion(int(val)) if hasattr(
                certificaciones_abiertas, "obtener_certificacion"
            ) else None
            if cert is None:
                # fallback name
                try:
                    cert = certificaciones_abiertas.obtener_certi(int(val))
                except Exception:
                    items = certificaciones_abiertas.listar_certificaciones_activas()
                    cert = next((x for x in items if str(x.get("id")) == val), None)
            if not cert:
                return await inter.response.send_message("❌ Certificación no encontrada.", ephemeral=True)
            view = ui.View(timeout=300)
            view.add_item(DeptSelect(self.bot, self.usuario, cert))
            await inter.response.send_message(
                f"🎓 **{cert.get('nombre')}** para {self.usuario.mention}\n"
                f"Ahora elige el **ala / departamento** de la certificación:",
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
        description="Certifica (interno): elige certificación y ala/departamento",
    )
    @app_commands.describe(usuario="Estudiante / personal a certificar")
    async def certificar(inter: discord.Interaction, usuario: discord.Member):
        if not isinstance(inter.user, discord.Member):
            return await inter.response.send_message("❌ Solo en servidor.", ephemeral=True)
        if not _puede_iniciar(inter.user):
            return await inter.response.send_message("❌ Sin permiso para certificar.", ephemeral=True)
        certificaciones_abiertas.asegurar_defaults()
        if not certificaciones_abiertas.listar_certificaciones_activas():
            return await inter.response.send_message("❌ No hay certificaciones activas.", ephemeral=True)
        await inter.response.send_message(
            f"🎓 Certificar a **{usuario.display_name}**\n"
            f"1) Certificación → 2) Ala/departamento → firmas internas por MD.",
            view=SelView(bot, usuario),
            ephemeral=True,
        )

    print("[cert_flujo_interno] /certificar con ala/departamento")


def registrar(bot: commands.Bot) -> None:
    try:
        _patch_firmas(bot)
    except Exception:
        print("[cert_flujo_interno] error parche firmas:")
        traceback.print_exc()
    try:
        _patch_certificar_ui(bot)
    except Exception:
        print("[cert_flujo_interno] error certificar ui:")
        traceback.print_exc()
    print("[cert_flujo_interno] OK")
