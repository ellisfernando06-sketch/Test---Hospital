# -*- coding: utf-8 -*-
"""firmas.py — Firmas digitales + sistema de autorización triple (encargado, docencia, director_zona)."""
from __future__ import annotations
import json, os
from datetime import datetime, timezone
from typing import Optional
import discord
from discord import app_commands, ui
from discord.ext import commands
import config, roles_store

try:
    import permisos
except Exception:
    permisos = None

_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
_FIRMAS_PATH = os.path.join(_DATA, "firmas.json")
_PEND_PATH = os.path.join(_DATA, "autorizaciones_pendientes.json")
_FIRMAS_DIR = os.path.join(_DATA, "firmas_img")

KEY_DOCENCIA = "DIRECTOR_DOCENCIA"

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _load_json(path: str, default):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    except Exception:
        pass
    if not os.path.isfile(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _save_json(path: str, data) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("[firmas] save:", e)

# ══════════════════════════════════════════════════════════════════════════════
# Gestión de Firmas Digitalizadas
# ══════════════════════════════════════════════════════════════════════════════

def guardar_firma(uid: int, key_cargo: str, filename: str) -> None:
    """Guarda firma digitalizada de un usuario con su cargo."""
    data = _load_json(_FIRMAS_PATH, {})
    data[str(uid)] = {"uid": uid, "key": key_cargo, "file": filename, "fecha": _now()}
    data.setdefault("por_key", {})[key_cargo] = str(uid)
    _save_json(_FIRMAS_PATH, data)

def obtener_firma_usuario(uid: int) -> Optional[dict]:
    """Obtiene la firma registrada de un usuario."""
    return _load_json(_FIRMAS_PATH, {}).get(str(uid))

def obtener_firma_key(key: str) -> Optional[dict]:
    """Obtiene la firma del director de una clave/rol."""
    data = _load_json(_FIRMAS_PATH, {})
    uid = (data.get("por_key") or {}).get(key)
    return data.get(str(uid)) if uid else None

def ruta_firma(filename: str) -> str:
    """Retorna la ruta completa de una firma guardada."""
    return os.path.join(_FIRMAS_DIR, filename)

async def descargar_firma(attachment: discord.Attachment, uid: int) -> str:
    """Descarga y guarda una firma desde un attachment."""
    os.makedirs(_FIRMAS_DIR, exist_ok=True)
    ext = "png"
    if attachment.filename and "." in attachment.filename:
        e = attachment.filename.rsplit(".", 1)[-1].lower()[:4]
        if e in ("png", "jpg", "jpeg", "webp"):
            ext = e
    fname = f"firma_{uid}.{ext}"
    await attachment.save(ruta_firma(fname))
    return fname

# ══════════════════════════════════════════════════════════════════════════════
# Gestión de Autorizaciones (Sistema Triple)
# ══════════════════════════════════════════════════════════════════════════════

def nueva_autorizacion(reg: dict) -> int:
    """Crea una solicitud de autorización (triple: encargado, docencia, director_zona)."""
    data = _load_json(_PEND_PATH, {"items": [], "next_id": 1})
    aid = int(data.get("next_id") or 1)
    data["next_id"] = aid + 1
    reg = dict(reg)
    reg["id"] = aid
    reg["estado"] = "pendiente"
    reg["fecha"] = _now()
    # Estados de aprobación: inicialmente sin autorizar
    reg["aprobado_encargado"] = False
    reg["aprobado_docencia"] = False
    reg["aprobado_director_zona"] = False
    reg["firma_encargado"] = reg.get("firma_encargado")
    reg["firma_docencia"] = None
    reg["firma_director_zona"] = None
    data.setdefault("items", []).append(reg)
    _save_json(_PEND_PATH, data)
    return aid

def obtener_autorizacion(aid: int) -> Optional[dict]:
    """Obtiene una autorización por ID."""
    for it in _load_json(_PEND_PATH, {"items": []}).get("items") or []:
        if int(it.get("id") or 0) == int(aid):
            return it
    return None

def actualizar_autorizacion(aid: int, **kwargs) -> Optional[dict]:
    """Actualiza una autorización existente."""
    data = _load_json(_PEND_PATH, {"items": []})
    out = None
    for it in data.get("items") or []:
        if int(it.get("id") or 0) == int(aid):
            it.update(kwargs)
            out = it
            break
    _save_json(_PEND_PATH, data)
    return out

def _es_key(member: discord.Member, *keys: str) -> bool:
    """Verifica si un miembro tiene alguna de las claves."""
    if not isinstance(member, discord.Member):
        return False
    if member.guild_permissions.administrator:
        return True
    if permisos is None:
        return False
    try:
        return permisos.member_tiene_alguna_key(member, *keys)
    except Exception:
        return False

# ══════════════════════════════════════════════════════════════════════════════
# Vistas de Autorización (Triple)
# ══════════════════════════════════════════════════════════════════════════════

class VistaAutorizarEncargado(ui.View):
    """Vista para que el encargado/instructor confirme el certificado."""
    def __init__(self, bot: commands.Bot, aid: int):
        super().__init__(timeout=3600)
        self.bot = bot
        self.aid = int(aid)

    @ui.button(label="✅ Confirmar (Encargado)", style=discord.ButtonStyle.success)
    async def confirmar(self, inter: discord.Interaction, _btn: ui.Button):
        reg = obtener_autorizacion(self.aid)
        if not reg or reg.get("estado") != "pendiente":
            return await inter.response.send_message("Ya resuelta o no existe.", ephemeral=True)
        
        firma = obtener_firma_usuario(inter.user.id)
        if not firma:
            return await inter.response.send_message("❌ Sin firma. Usa `/registrar_firma`.", ephemeral=True)
        
        await inter.response.defer()
        reg = actualizar_autorizacion(
            self.aid,
            aprobado_encargado=True,
            encargado_id=inter.user.id,
            encargado_nombre=getattr(inter.user, "display_name", str(inter.user)),
            firma_encargado=firma.get("file"),
        ) or reg
        
        await inter.followup.send(
            f"✅ **{inter.user.mention}** (Encargado) confirmó el certificado.\n"
            f"⏳ Esperando firma de **Director de Investigación y Docencia** y **Director del ala**.",
            ephemeral=True
        )
        try:
            await inter.message.edit(view=None)
        except Exception:
            pass
        self.stop()

    @ui.button(label="❌ Rechazar", style=discord.ButtonStyle.danger)
    async def rechazar(self, inter: discord.Interaction, _btn: ui.Button):
        reg = obtener_autorizacion(self.aid)
        if not reg or reg.get("estado") != "pendiente":
            return await inter.response.send_message("Ya resuelta.", ephemeral=True)
        
        actualizar_autorizacion(self.aid, estado="rechazado", encargado_id=inter.user.id)
        await inter.response.send_message(f"❌ #{self.aid} rechazada por encargado.", ephemeral=True)
        try:
            await inter.message.edit(view=None)
        except Exception:
            pass
        self.stop()


class VistaAutorizarDocencia(ui.View):
    """Vista para que el Director de Docencia autorice."""
    def __init__(self, bot: commands.Bot, aid: int):
        super().__init__(timeout=3600)
        self.bot = bot
        self.aid = int(aid)

    @ui.button(label="✅ Autorizar (Docencia)", style=discord.ButtonStyle.success)
    async def autorizar(self, inter: discord.Interaction, _btn: ui.Button):
        reg = obtener_autorizacion(self.aid)
        if not reg or reg.get("estado") != "pendiente":
            return await inter.response.send_message("Ya resuelta o no existe.", ephemeral=True)
        
        if not _es_key(inter.user, KEY_DOCENCIA, "OWNER"):
            return await inter.response.send_message(
                "❌ Solo el Director de Investigación y Docencia.",
                ephemeral=True
            )
        
        firma = obtener_firma_usuario(inter.user.id) or obtener_firma_key(KEY_DOCENCIA)
        if not firma:
            return await inter.response.send_message(
                "❌ Sin firma. Usa `/registrar_firma`.", ephemeral=True
            )
        
        await inter.response.defer()
        reg = actualizar_autorizacion(
            self.aid,
            aprobado_docencia=True,
            docencia_id=inter.user.id,
            docencia_nombre=getattr(inter.user, "display_name", str(inter.user)),
            firma_docencia=firma.get("file"),
        ) or reg
        
        await inter.followup.send(
            f"✅ **{inter.user.mention}** (Docencia) autorizó el certificado.\n"
            f"⏳ Esperando firma del **Director del ala/departamento**.",
            ephemeral=True
        )
        try:
            await inter.message.edit(view=None)
        except Exception:
            pass
        self.stop()

    @ui.button(label="❌ Rechazar", style=discord.ButtonStyle.danger)
    async def rechazar(self, inter: discord.Interaction, _btn: ui.Button):
        reg = obtener_autorizacion(self.aid)
        if not reg or reg.get("estado") != "pendiente":
            return await inter.response.send_message("Ya resuelta.", ephemeral=True)
        
        if not _es_key(inter.user, KEY_DOCENCIA, "OWNER"):
            return await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
        
        actualizar_autorizacion(self.aid, estado="rechazado_docencia", docencia_id=inter.user.id)
        await inter.response.send_message(f"❌ #{self.aid} rechazada por Docencia.", ephemeral=True)
        try:
            await inter.message.edit(view=None)
        except Exception:
            pass
        self.stop()


class VistaAutorizarDirectorZona(ui.View):
    """Vista para que el Director del Ala/Departamento autorice."""
    def __init__(self, bot: commands.Bot, aid: int, director_zona_key: str):
        super().__init__(timeout=3600)
        self.bot = bot
        self.aid = int(aid)
        self.director_zona_key = director_zona_key

    @ui.button(label="✅ Autorizar (Director del Ala)", style=discord.ButtonStyle.success)
    async def autorizar(self, inter: discord.Interaction, _btn: ui.Button):
        reg = obtener_autorizacion(self.aid)
        if not reg or reg.get("estado") != "pendiente":
            return await inter.response.send_message("Ya resuelta o no existe.", ephemeral=True)
        
        if not _es_key(inter.user, self.director_zona_key, "OWNER"):
            return await inter.response.send_message(
                f"❌ Solo Director de {self.director_zona_key.replace('DIRECTOR_', '')}.",
                ephemeral=True
            )
        
        firma = obtener_firma_usuario(inter.user.id) or obtener_firma_key(self.director_zona_key)
        if not firma:
            return await inter.response.send_message(
                "❌ Sin firma. Usa `/registrar_firma`.", ephemeral=True
            )
        
        await inter.response.defer()
        reg = actualizar_autorizacion(
            self.aid,
            aprobado_director_zona=True,
            director_zona_id=inter.user.id,
            director_zona_nombre=getattr(inter.user, "display_name", str(inter.user)),
            firma_director_zona=firma.get("file"),
        ) or reg
        
        # Verificar si todas las autorizaciones están completas
        if reg.get("aprobado_encargado") and reg.get("aprobado_docencia") and reg.get("aprobado_director_zona"):
            try:
                if (reg.get("tipo") or "") == "certificado":
                    await _emitir_certificado_autorizado(self.bot, inter, reg)
                    actualizar_autorizacion(self.aid, estado="autorizado")
                else:
                    await inter.followup.send(f"✅ Documento **#{self.aid}** autorizado completamente.")
            except Exception as e:
                print("[firmas] emitir:", e)
                await inter.followup.send(f"❌ Error al emitir: {e}", ephemeral=True)
        else:
            await inter.followup.send(
                f"✅ **{inter.user.mention}** (Director del Ala) autorizó.\n"
                f"✅ Las tres firmas han sido recolectadas. Generando certificado...",
                ephemeral=True
            )
        
        try:
            await inter.message.edit(view=None)
        except Exception:
            pass
        self.stop()

    @ui.button(label="❌ Rechazar", style=discord.ButtonStyle.danger)
    async def rechazar(self, inter: discord.Interaction, _btn: ui.Button):
        reg = obtener_autorizacion(self.aid)
        if not reg or reg.get("estado") != "pendiente":
            return await inter.response.send_message("Ya resuelta.", ephemeral=True)
        
        if not _es_key(inter.user, self.director_zona_key, "OWNER"):
            return await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
        
        actualizar_autorizacion(self.aid, estado="rechazado_zona", director_zona_id=inter.user.id)
        await inter.response.send_message(f"❌ #{self.aid} rechazada por Director del Ala.", ephemeral=True)
        try:
            await inter.message.edit(view=None)
        except Exception:
            pass
        self.stop()


async def _emitir_certificado_autorizado(bot, inter: discord.Interaction, reg: dict):
    """Emite el certificado cuando todas las tres firmas están autorizadas."""
    from certificado_imagen import generar_certificado
    
    uid = int(reg.get("receptor_id") or 0)
    receptor = inter.guild.get_member(uid) if inter.guild else None
    nombre = reg.get("nombre_receptor") or (receptor.display_name if receptor else str(uid))
    cap = reg.get("capacitacion") or "Certificación"
    hospital = getattr(config, "NOMBRE_HOSPITAL", "Hospital General") or "Hospital General"
    emisor = reg.get("encargado_nombre") or "Encargado"
    num = reg.get("numero") or f"CERT-{reg.get('id', 0):05d}"
    cedula = reg.get("cedula") or ""
    
    firma_enc = reg.get("firma_encargado")
    firma_doc = reg.get("firma_docencia")
    firma_zona = reg.get("firma_director_zona")
    
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
        firma_encargado_path=ruta_firma(firma_enc) if firma_enc else None,
        firma_director_path=ruta_firma(firma_doc) if firma_doc else None,
        firma_director_zona_path=ruta_firma(firma_zona) if firma_zona else None,
        label_encargado="Otorgado por / Encargado",
        label_director="Director de Investigación y Docencia",
        label_director_zona="Director del Ala / Departamento",
    )
    
    archivo = discord.File(buf, filename=f"certificado_{uid}.png")
    emb = discord.Embed(
        title="🎓 Certificado Autorizado",
        description=(
            f"**Graduado:** <@{uid}>\n"
            f"**Certificación:** {cap}\n"
            f"**Identificación:** {cedula}\n"
            f"**N.º:** `{num}`\n"
            f"**Encargado:** {reg.get('encargado_nombre', emisor)}\n"
            f"**Autorizado por:** {reg.get('docencia_nombre', 'Docencia')} y {reg.get('director_zona_nombre', 'Director del Ala')}\n"
            f"📌 Solo Roleplay"
        ),
        color=0x8E44AD,
        timestamp=discord.utils.utcnow(),
    )
    
    ch = None
    if reg.get("canal_id"):
        ch = bot.get_channel(int(reg["canal_id"]))
    ch = ch or inter.channel
    if ch:
        await ch.send(content=f"🎓 <@{uid}> — certificado en **{cap}**", embed=emb, file=archivo)
    
    if receptor:
        try:
            buf2 = generar_certificado(
                nombre_receptor=nombre, titulo=cap, capacitacion=cap, hospital=hospital,
                emisor=emisor, numero=num, cedula=cedula, descripcion=reg.get("descripcion") or "",
                departamento=reg.get("departamento") or "",
                firma_encargado_path=ruta_firma(firma_enc) if firma_enc else None,
                firma_director_path=ruta_firma(firma_doc) if firma_doc else None,
                firma_director_zona_path=ruta_firma(firma_zona) if firma_zona else None,
                label_encargado="Otorgado por / Encargado",
                label_director="Director de Investigación y Docencia",
                label_director_zona="Director del Ala / Departamento",
            )
            await receptor.send(
                content=f"🎓 Certificado de **{cap}** autorizado:",
                file=discord.File(buf2, filename=f"certificado_{uid}.png"),
            )
        except Exception:
            pass
    
    await inter.followup.send(f"✅ Certificado **{num}** emitido exitosamente.", ephemeral=True)


async def solicitar_autorizacion_certificado(
    bot, inter, *, receptor, certificacion, cedula="", descripcion="", departamento="", firma_encargado_file=None,
) -> int:
    """Inicia el flujo de autorización triple para un certificado."""
    num = "CERT-PEND"
    try:
        import docencia as _doc
        reg_d = _doc.emitir(
            receptor.id, certificacion.get("nombre"), "personalizado", descripcion,
            inter.user.id, notas="pendiente autorización triple", departamento=departamento,
        )
        num = f"CERT-{int(reg_d.get('id') or 0):05d}"
    except Exception as e:
        print("[firmas] docencia.emitir:", e)
    
    director_zona_key = certificacion.get("director_zona_key", "DIRECTOR_ADMINISTRATIVO")
    
    aid = nueva_autorizacion({
        "tipo": "certificado",
        "key_docencia": KEY_DOCENCIA,
        "key_director_zona": director_zona_key,
        "receptor_id": receptor.id,
        "nombre_receptor": getattr(receptor, "display_name", str(receptor)),
        "capacitacion": certificacion.get("nombre", "Certificación"),
        "descripcion": descripcion,
        "departamento": departamento,
        "cedula": cedula,
        "certificacion_id": certificacion.get("id"),
        "encargado_id": inter.user.id,
        "encargado_nombre": getattr(inter.user, "display_name", str(inter.user)),
        "firma_encargado": firma_encargado_file,
        "canal_id": inter.channel.id if inter.channel else None,
        "numero": num,
    })
    
    # EMBED 1: Para el Encargado (confirmación)
    emb1 = discord.Embed(
        title=f"🖋️ Certificado · #{aid} — Confirmación del Encargado",
        description=(
            f"**Graduado:** {receptor.mention}\n"
            f"**Certificación:** {certificacion.get('nombre', 'Certificación')}\n"
            f"**Identificación:** {cedula}\n"
            f"**N.º:** `{num}`\n\n"
            f"Por favor **confirma** que el estudiante completó la certificación."
        ),
        color=0xF39C12,
        timestamp=discord.utils.utcnow(),
    )
    if departamento:
        emb1.add_field(name="Área", value=departamento, inline=True)
    if descripcion:
        emb1.add_field(name="Observaciones", value=descripcion[:300], inline=False)
    
    # EMBED 2: Para Director de Docencia
    emb2 = discord.Embed(
        title=f"🖋️ Certificado · #{aid} — Autorización de Docencia",
        description=(
            f"**Graduado:** {receptor.mention}\n"
            f"**Certificación:** {certificacion.get('nombre', 'Certificación')}\n"
            f"**Encargado:** {inter.user.mention}\n"
            f"**N.º:** `{num}`\n\n"
            f"**Director de Investigación y Docencia** → Autorizar."
        ),
        color=0xF39C12,
        timestamp=discord.utils.utcnow(),
    )
    
    # EMBED 3: Para Director del Ala/Departamento
    emb3 = discord.Embed(
        title=f"🖋️ Certificado · #{aid} — Autorización del Ala / Departamento",
        description=(
            f"**Graduado:** {receptor.mention}\n"
            f"**Certificación:** {certificacion.get('nombre', 'Certificación')}\n"
            f"**Área:** {departamento or certificacion.get('departamento', 'Sin especificar')}\n"
            f"**N.º:** `{num}`\n\n"
            f"**Director del Ala/Departamento** → Autorizar."
        ),
        color=0xF39C12,
        timestamp=discord.utils.utcnow(),
    )
    
    view1 = VistaAutorizarEncargado(bot, aid)
    view2 = VistaAutorizarDocencia(bot, aid)
    view3 = VistaAutorizarDirectorZona(bot, aid, director_zona_key)
    
    try:
        import logs_store
        dest = logs_store.resolver_canal_log(bot, inter.guild, "aprobaciones")
        if not dest:
            dest = logs_store.resolver_canal_log(bot, inter.guild, "log_certificados")
    except Exception:
        dest = inter.channel
    
    if dest:
        await dest.send(embed=emb1, view=view1)
        await dest.send(embed=emb2, view=view2)
        await dest.send(embed=emb3, view=view3)
    else:
        await inter.followup.send(embed=emb1, view=view1)
        await inter.followup.send(embed=emb2, view=view2)
        await inter.followup.send(embed=emb3, view=view3)
    
    return aid


def registrar(bot: commands.Bot) -> None:
    """Registra comandos de firma sin romper el bot."""
    try:
        presentes = {c.name for c in bot.tree.get_commands()}
    except Exception:
        presentes = set()
    
    if "registrar_firma" not in presentes:
        try:
            @bot.tree.command(name="registrar_firma", description="Registra tu firma digitalizada (imagen)")
            @app_commands.describe(imagen="Imagen de tu firma", cargo="Cargo")
            @app_commands.choices(cargo=[
                app_commands.Choice(name="Director de Investigación y Docencia", value="DIRECTOR_DOCENCIA"),
                app_commands.Choice(name="Director Médico", value="DIRECTOR_MEDICO"),
                app_commands.Choice(name="Director Administrativo", value="DIRECTOR_ADMINISTRATIVO"),
                app_commands.Choice(name="Director de Logística", value="DIRECTOR_LOGISTICA"),
                app_commands.Choice(name="Director de RRHH", value="DIRECTOR_RRHH"),
                app_commands.Choice(name="Director General", value="DIRECTOR_GENERAL"),
                app_commands.Choice(name="Encargado / Instructor", value="ENCARGADO"),
                app_commands.Choice(name="Otra firma personal", value="PERSONAL"),
            ])
            async def registrar_firma(inter: discord.Interaction, imagen: discord.Attachment, cargo: app_commands.Choice[str]):
                if not isinstance(inter.user, discord.Member):
                    return await inter.response.send_message("Solo en servidor.", ephemeral=True)
                if not imagen.content_type or not str(imagen.content_type).startswith("image/"):
                    return await inter.response.send_message("❌ Debe ser imagen.", ephemeral=True)
                key = cargo.value
                if key not in ("ENCARGADO", "PERSONAL") and not _es_key(inter.user, key, "OWNER"):
                    return await inter.response.send_message(f"❌ No tienes **{cargo.name}**.", ephemeral=True)
                await inter.response.defer(ephemeral=True)
                try:
                    fname = await descargar_firma(imagen, inter.user.id)
                    guardar_firma(inter.user.id, key, fname)
                    await inter.followup.send(f"✅ Firma **{cargo.name}** registrada.", ephemeral=True)
                except Exception as e:
                    await inter.followup.send(f"❌ {e}", ephemeral=True)
            print("[firmas] ✓ /registrar_firma")
        except Exception as e:
            print("[firmas] registrar_firma omitido:", e)
    
    if "ver_mi_firma" not in presentes:
        try:
            @bot.tree.command(name="ver_mi_firma", description="Muestra tu firma digitalizada")
            async def ver_mi_firma(inter: discord.Interaction):
                reg = obtener_firma_usuario(inter.user.id)
                if not reg:
                    return await inter.response.send_message("Sin firma. Usa `/registrar_firma`.", ephemeral=True)
                path = ruta_firma(reg["file"])
                if not os.path.isfile(path):
                    return await inter.response.send_message("Archivo no encontrado.", ephemeral=True)
                await inter.response.send_message(
                    file=discord.File(path, filename=reg["file"]), ephemeral=True
                )
            print("[firmas] ✓ /ver_mi_firma")
        except Exception as e:
            print("[firmas] ver_mi_firma omitido:", e)
    
    print("[firmas] OK")
