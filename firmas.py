# -*- coding: utf-8 -*-
"""firmas.py — Firmas digitales + autorización triple (encargado, docencia, director_zona).
Keys según organigrama oficial.
"""
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

KEY_DOCENCIA = "DIR_DOCENCIA"

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

def guardar_firma(uid: int, key_cargo: str, filename: str) -> None:
    data = _load_json(_FIRMAS_PATH, {})
    data[str(uid)] = {"uid": uid, "key": key_cargo, "file": filename, "fecha": _now()}
    data.setdefault("por_key", {})[key_cargo] = str(uid)
    _save_json(_FIRMAS_PATH, data)

def obtener_firma_usuario(uid: int) -> Optional[dict]:
    return _load_json(_FIRMAS_PATH, {}).get(str(uid))

def obtener_firma_key(key: str) -> Optional[dict]:
    data = _load_json(_FIRMAS_PATH, {})
    uid = (data.get("por_key") or {}).get(key)
    return data.get(str(uid)) if uid else None

def ruta_firma(filename: str) -> str:
    return os.path.join(_FIRMAS_DIR, filename)

async def descargar_firma(attachment: discord.Attachment, uid: int) -> str:
    os.makedirs(_FIRMAS_DIR, exist_ok=True)
    ext = "png"
    if attachment.filename and "." in attachment.filename:
        e = attachment.filename.rsplit(".", 1)[-1].lower()[:4]
        if e in ("png", "jpg", "jpeg", "webp"):
            ext = e
    fname = f"firma_{uid}.{ext}"
    await attachment.save(ruta_firma(fname))
    return fname

def nueva_autorizacion(reg: dict) -> int:
    data = _load_json(_PEND_PATH, {"items": [], "next_id": 1})
    aid = int(data.get("next_id") or 1)
    data["next_id"] = aid + 1
    reg = dict(reg)
    reg["id"] = aid
    reg["estado"] = "pendiente"
    reg["fecha"] = _now()
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
    for it in _load_json(_PEND_PATH, {"items": []}).get("items") or []:
        if int(it.get("id") or 0) == int(aid):
            return it
    return None

def actualizar_autorizacion(aid: int, **kwargs) -> Optional[dict]:
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

class VistaAutorizarEncargado(ui.View):
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
        actualizar_autorizacion(
            self.aid, aprobado_encargado=True, encargado_id=inter.user.id,
            encargado_nombre=getattr(inter.user, "display_name", str(inter.user)),
            firma_encargado=firma.get("file"),
        )
        await inter.followup.send(
            f"✅ **{inter.user.mention}** (Encargado) confirmó.\n"
            f"⏳ Esperando **Director de Docencia** y **Director del ala**.", ephemeral=True)
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
    def __init__(self, bot: commands.Bot, aid: int):
        super().__init__(timeout=3600)
        self.bot = bot
        self.aid = int(aid)

    @ui.button(label="✅ Autorizar (Docencia)", style=discord.ButtonStyle.success)
    async def autorizar(self, inter: discord.Interaction, _btn: ui.Button):
        reg = obtener_autorizacion(self.aid)
        if not reg or reg.get("estado") != "pendiente":
            return await inter.response.send_message("Ya resuelta o no existe.", ephemeral=True)
        if not _es_key(inter.user, KEY_DOCENCIA, "FUNDADOR_OWNER", "CO_OWNER", "PREFECTO_OPERACIONES"):
            return await inter.response.send_message(
                "❌ Solo Director de Docencia, Prefecto o Autoridades.", ephemeral=True)
        firma = obtener_firma_usuario(inter.user.id) or obtener_firma_key(KEY_DOCENCIA)
        if not firma:
            return await inter.response.send_message("❌ Sin firma. Usa `/registrar_firma`.", ephemeral=True)
        await inter.response.defer()
        actualizar_autorizacion(
            self.aid, aprobado_docencia=True, docencia_id=inter.user.id,
            docencia_nombre=getattr(inter.user, "display_name", str(inter.user)),
            firma_docencia=firma.get("file"),
        )
        await inter.followup.send(
            f"✅ **{inter.user.mention}** (Docencia) autorizó.\n⏳ Esperando Director del ala.", ephemeral=True)
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
        if not _es_key(inter.user, KEY_DOCENCIA, "FUNDADOR_OWNER", "CO_OWNER", "PREFECTO_OPERACIONES"):
            return await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
        actualizar_autorizacion(self.aid, estado="rechazado_docencia", docencia_id=inter.user.id)
        await inter.response.send_message(f"❌ #{self.aid} rechazada por Docencia.", ephemeral=True)
        try:
            await inter.message.edit(view=None)
        except Exception:
            pass
        self.stop()

class VistaAutorizarDirectorZona(ui.View):
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
        if not _es_key(inter.user, self.director_zona_key, "FUNDADOR_OWNER", "CO_OWNER"):
            label = self.director_zona_key.replace("DIR_", "").replace("DIRECTOR_", "")
            return await inter.response.send_message(f"❌ Solo Director de {label}.", ephemeral=True)
        firma = obtener_firma_usuario(inter.user.id) or obtener_firma_key(self.director_zona_key)
        if not firma:
            return await inter.response.send_message("❌ Sin firma. Usa `/registrar_firma`.", ephemeral=True)
        await inter.response.defer()
        reg = actualizar_autorizacion(
            self.aid, aprobado_director_zona=True, director_zona_id=inter.user.id,
            director_zona_nombre=getattr(inter.user, "display_name", str(inter.user)),
            firma_director_zona=firma.get("file"),
        ) or reg
        if reg.get("aprobado_encargado") and reg.get("aprobado_docencia") and reg.get("aprobado_director_zona"):
            try:
                if (reg.get("tipo") or "") == "certificado":
                    await _emitir_certificado_autorizado(self.bot, inter, reg)
                    actualizar_autorizacion(self.aid, estado="autorizado")
                else:
                    await inter.followup.send(f"✅ Documento **#{self.aid}** autorizado.")
            except Exception as e:
                print("[firmas] emitir:", e)
                await inter.followup.send(f"❌ Error al emitir: {e}", ephemeral=True)
        else:
            await inter.followup.send(f"✅ **{inter.user.mention}** (Director del Ala) autorizó.", ephemeral=True)
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
        if not _es_key(inter.user, self.director_zona_key, "FUNDADOR_OWNER", "CO_OWNER"):
            return await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
        actualizar_autorizacion(self.aid, estado="rechazado_zona", director_zona_id=inter.user.id)
        await inter.response.send_message(f"❌ #{self.aid} rechazada por Director del Ala.", ephemeral=True)
        try:
            await inter.message.edit(view=None)
        except Exception:
            pass
        self.stop()

async def _emitir_certificado_autorizado(bot, inter: discord.Interaction, reg: dict):
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
        nombre_receptor=nombre, titulo=cap, capacitacion=cap, hospital=hospital,
        emisor=emisor, numero=num, cedula=cedula,
        descripcion=reg.get("descripcion") or "", departamento=reg.get("departamento") or "",
        firma_encargado_path=ruta_firma(firma_enc) if firma_enc else None,
        firma_director_path=ruta_firma(firma_doc) if firma_doc else None,
        firma_director_zona_path=ruta_firma(firma_zona) if firma_zona else None,
        label_encargado="Otorgado por / Encargado",
        label_director="Director de Docencia e Investigación",
        label_director_zona="Director del Ala / Departamento",
    )
    archivo = discord.File(buf, filename=f"certificado_{uid}.png")
    emb = discord.Embed(
        title="🎓 Certificado Autorizado",
        description=(
            f"**Graduado:** <@{uid}>\n**Certificación:** {cap}\n**Identificación:** {cedula}\n"
            f"**N.º:** `{num}`\n**Encargado:** {reg.get('encargado_nombre', emisor)}\n"
            f"**Autorizado por:** {reg.get('docencia_nombre', 'Docencia')} y {reg.get('director_zona_nombre', 'Director del Ala')}\n"
            f"📌 Solo Roleplay"
        ),
        color=0x8E44AD, timestamp=discord.utils.utcnow(),
    )
    ch = bot.get_channel(int(reg["canal_id"])) if reg.get("canal_id") else None
    ch = ch or inter.channel
    if ch:
        await ch.send(content=f"🎓 <@{uid}> — certificado en **{cap}**", embed=emb, file=archivo)
    if receptor:
        try:
            buf2 = generar_certificado(
                nombre_receptor=nombre, titulo=cap, capacitacion=cap, hospital=hospital,
                emisor=emisor, numero=num, cedula=cedula,
                descripcion=reg.get("descripcion") or "", departamento=reg.get("departamento") or "",
                firma_encargado_path=ruta_firma(firma_enc) if firma_enc else None,
                firma_director_path=ruta_firma(firma_doc) if firma_doc else None,
                firma_director_zona_path=ruta_firma(firma_zona) if firma_zona else None,
                label_encargado="Otorgado por / Encargado",
                label_director="Director de Docencia e Investigación",
                label_director_zona="Director del Ala / Departamento",
            )
            await receptor.send(content=f"🎓 Certificado de **{cap}** autorizado:",
                file=discord.File(buf2, filename=f"certificado_{uid}.png"))
        except Exception:
            pass
    await inter.followup.send(f"✅ Certificado **{num}** emitido exitosamente.", ephemeral=True)

async def solicitar_autorizacion_certificado(
    bot, inter, *, receptor, certificacion, cedula="", descripcion="", departamento="", firma_encargado_file=None,
) -> int:
    director_zona_key = certificacion.get("director_zona_key", "DIR_MEDICO")
    # Normalizar keys antiguas si vienen del catálogo
    _map = {
        "DIRECTOR_MEDICO": "DIR_MEDICO", "DIRECTOR_LOGISTICA": "DIR_LOGISTICA",
        "DIRECTOR_RRHH": "DIR_RRHH", "DIRECTOR_GENERAL": "DIR_GENERAL",
        "DIRECTOR_DOCENCIA": "DIR_DOCENCIA", "DIRECTOR_ADMINISTRATIVO": "DIR_GENERAL",
    }
    director_zona_key = _map.get(director_zona_key, director_zona_key)
    aid = nueva_autorizacion({
        "tipo": "certificado",
        "receptor_id": receptor.id,
        "nombre_receptor": getattr(receptor, "display_name", str(receptor)),
        "capacitacion": certificacion.get("nombre") or "Certificación",
        "cedula": cedula,
        "descripcion": descripcion,
        "departamento": departamento,
        "canal_id": inter.channel.id if inter.channel else None,
        "firma_encargado": firma_encargado_file,
        "director_zona_key": director_zona_key,
        "key_docencia": KEY_DOCENCIA,
    })
    return aid

def registrar(bot: commands.Bot) -> None:
    @bot.tree.command(name="registrar_firma", description="Registra tu firma digital (directores / jefes)")
    @app_commands.describe(imagen="Imagen de tu firma (PNG/JPG)")
    async def registrar_firma(inter: discord.Interaction, imagen: discord.Attachment):
        if not isinstance(inter.user, discord.Member):
            return await inter.response.send_message("❌ Solo en servidor.", ephemeral=True)
        if not permisos or not permisos.member_puede_firmar_encargado(inter.user):
            return await inter.response.send_message(
                "❌ Solo jefes, médicos, directores y autoridades pueden registrar firma.", ephemeral=True)
        if not imagen.content_type or not imagen.content_type.startswith("image/"):
            return await inter.response.send_message("❌ Debe ser una imagen.", ephemeral=True)
        await inter.response.defer(ephemeral=True)
        fname = await descargar_firma(imagen, inter.user.id)
        keys = permisos.keys_del_member(inter.user) if permisos else []
        key_cargo = keys[0] if keys else "STAFF"
        guardar_firma(inter.user.id, key_cargo, fname)
        await inter.followup.send(f"✅ Firma registrada como `{key_cargo}`.", ephemeral=True)

    print("[firmas] OK — keys organigrama (DIR_DOCENCIA / FUNDADOR_OWNER)")
