# -*- coding: utf-8 -*
"""
firmas.py — Firmas digitalizadas y autorizaciones IC (médicas / administrativas).
Cada cargo puede registrar su firma (imagen). Los documentos pendientes
esperan autorización con botón y el bot estampa la firma.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import discord
from discord import app_commands, ui
from discord.ext import commands

import config

try:
    import permisos
except Exception:
    permisos = None

_DATA = os.path.join(os.path.dirname(__file__), "data")
_FIRMAS_PATH = os.path.join(_DATA, "firmas.json")
_PEND_PATH = os.path.join(_DATA, "autorizaciones_pendientes.json")
_FIRMAS_DIR = os.path.join(_DATA, "firmas_img")

# Clave del Director de Investigación y Docencia (misma KEY, nombre nuevo)
KEY_DOCENCIA = "DIRECTOR_DOCENCIA"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str, default):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.isfile(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def guardar_firma(uid: int, key_cargo: str, filename: str) -> None:
    data = _load_json(_FIRMAS_PATH, {})
    data[str(uid)] = {
        "uid": uid,
        "key": key_cargo,
        "file": filename,
        "fecha": _now(),
    }
    # También indexar por key el último que registró esa key (director actual)
    data.setdefault("por_key", {})[key_cargo] = str(uid)
    _save_json(_FIRMAS_PATH, data)


def obtener_firma_usuario(uid: int) -> Optional[dict]:
    data = _load_json(_FIRMAS_PATH, {})
    return data.get(str(uid))


def obtener_firma_key(key: str) -> Optional[dict]:
    data = _load_json(_FIRMAS_PATH, {})
    uid = (data.get("por_key") or {}).get(key)
    if not uid:
        return None
    return data.get(str(uid))


def ruta_firma(filename: str) -> str:
    return os.path.join(_FIRMAS_DIR, filename)


async def descargar_firma(attachment: discord.Attachment, uid: int) -> str:
    os.makedirs(_FIRMAS_DIR, exist_ok=True)
    ext = "png"
    if attachment.filename and "." in attachment.filename:
        ext = attachment.filename.rsplit(".", 1)[-1].lower()[:4]
        if ext not in ("png", "jpg", "jpeg", "webp"):
            ext = "png"
    fname = f"firma_{uid}.{ext}"
    path = ruta_firma(fname)
    await attachment.save(path)
    return fname


def nueva_autorizacion(reg: dict) -> int:
    data = _load_json(_PEND_PATH, {"items": [], "next_id": 1})
    aid = int(data.get("next_id") or 1)
    data["next_id"] = aid + 1
    reg = dict(reg)
    reg["id"] = aid
    reg["estado"] = "pendiente"
    reg["fecha"] = _now()
    data["items"].append(reg)
    _save_json(_PEND_PATH, data)
    return aid


def obtener_autorizacion(aid: int) -> Optional[dict]:
    data = _load_json(_PEND_PATH, {"items": []})
    for it in data.get("items") or []:
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


class ModalRegistrarFirma(ui.Modal, title="🖋️ Registrar firma digitalizada"):
    # Modal no soporta attachments; el flujo es: comando + attachment
    pass


class VistaAutorizar(ui.View):
    def __init__(self, bot: commands.Bot, aid: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.aid = aid

    @ui.button(label="Autorizar y firmar", style=discord.ButtonStyle.success, emoji="✅", custom_id="firma_auth_ok_v1")
    async def autorizar(self, inter: discord.Interaction, btn: ui.Button):
        reg = obtener_autorizacion(self.aid)
        if not reg or reg.get("estado") != "pendiente":
            return await inter.response.send_message("Esta solicitud ya fue resuelta.", ephemeral=True)

        key_req = reg.get("key_autorizador") or KEY_DOCENCIA
        if not _es_key(inter.user, key_req, "OWNER"):
            nombre = getattr(config, "KEYS_NOMBRES", {}).get(key_req, (key_req,))[0]
            return await inter.response.send_message(
                f"❌ Solo **{nombre}** (u OWNER) puede autorizar.",
                ephemeral=True,
            )

        firma = obtener_firma_usuario(inter.user.id) or obtener_firma_key(key_req)
        if not firma:
            return await inter.response.send_message(
                "❌ No tienes firma registrada.\n"
                "Usa `/registrar_firma` adjuntando tu firma en imagen (PNG/JPG con fondo transparente ideal).",
                ephemeral=True,
            )

        await inter.response.defer()
        reg = actualizar_autorizacion(
            self.aid,
            estado="autorizado",
            autorizador_id=inter.user.id,
            firma_autorizador=firma.get("file"),
            fecha_autorizacion=_now(),
        )

        tipo = reg.get("tipo") or "documento"
        if tipo == "certificado":
            await _emitir_certificado_autorizado(self.bot, inter, reg)
        else:
            await inter.followup.send(
                f"✅ Documento **#{self.aid}** autorizado por {inter.user.mention}.",
            )
            # Callback genérico
            cb = reg.get("callback")
            if cb == "emitir_certificado":
                await _emitir_certificado_autorizado(self.bot, inter, reg)

        try:
            await inter.message.edit(view=None)
        except Exception:
            pass

    @ui.button(label="Rechazar", style=discord.ButtonStyle.danger, emoji="❌", custom_id="firma_auth_no_v1")
    async def rechazar(self, inter: discord.Interaction, btn: ui.Button):
        reg = obtener_autorizacion(self.aid)
        if not reg or reg.get("estado") != "pendiente":
            return await inter.response.send_message("Ya resuelta.", ephemeral=True)
        key_req = reg.get("key_autorizador") or KEY_DOCENCIA
        if not _es_key(inter.user, key_req, "OWNER"):
            return await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
        actualizar_autorizacion(self.aid, estado="rechazado", autorizador_id=inter.user.id)
        await inter.response.send_message(f"❌ Autorización **#{self.aid}** rechazada.", ephemeral=True)
        try:
            await inter.message.edit(content=inter.message.content + "\n\n**Rechazada.**", view=None)
        except Exception:
            pass


async def _emitir_certificado_autorizado(bot, inter: discord.Interaction, reg: dict):
    from certificado_imagen import generar_certificado

    uid = int(reg.get("receptor_id") or 0)
    receptor = inter.guild.get_member(uid) if inter.guild else None
    nombre = reg.get("nombre_receptor") or (receptor.display_name if receptor else str(uid))
    cap = reg.get("capacitacion") or "Capacitación"
    hospital = getattr(config, "NOMBRE_HOSPITAL", "Hospital General") or "Hospital General"
    emisor = reg.get("encargado_nombre") or "Encargado"
    num = reg.get("numero") or f"CERT-{reg.get('id', 0):05d}"

    firma_enc = reg.get("firma_encargado")
    firma_dir = reg.get("firma_autorizador")

    buf = generar_certificado(
        nombre_receptor=nombre,
        titulo=cap,
        capacitacion=cap,
        hospital=hospital,
        emisor=emisor,
        numero=num,
        descripcion=reg.get("descripcion") or "",
        departamento=reg.get("departamento") or "",
        firma_encargado_path=ruta_firma(firma_enc) if firma_enc else None,
        firma_director_path=ruta_firma(firma_dir) if firma_dir else None,
        label_encargado="Firma del encargado",
        label_director="Director de Investigación y Docencia",
    )

    archivo = discord.File(buf, filename=f"certificado_{uid}.png")
    emb = discord.Embed(
        title="🎓 Certificado autorizado",
        description=(
            f"**Graduado:** <@{uid}>\n"
            f"**Capacitación:** {cap}\n"
            f"**N.º:** `{num}`\n"
            f"**Encargado:** {emisor}\n"
            f"**Autorizado por:** {inter.user.mention}\n"
            f"📌 *Solo Roleplay*"
        ),
        color=0x8E44AD,
        timestamp=discord.utils.utcnow(),
    )
    emb.set_footer(text=f"{hospital}  •  Investigación y Docencia")

    canal_id = reg.get("canal_id")
    ch = bot.get_channel(int(canal_id)) if canal_id else inter.channel
    if ch:
        await ch.send(content=f"🎓 <@{uid}> — certificado en **{cap}** (autorizado)", embed=emb, file=archivo)

    if receptor:
        try:
            buf2 = generar_certificado(
                nombre_receptor=nombre,
                titulo=cap,
                capacitacion=cap,
                hospital=hospital,
                emisor=emisor,
                numero=num,
                descripcion=reg.get("descripcion") or "",
                departamento=reg.get("departamento") or "",
                firma_encargado_path=ruta_firma(firma_enc) if firma_enc else None,
                firma_director_path=ruta_firma(firma_dir) if firma_dir else None,
                label_encargado="Firma del encargado",
                label_director="Director de Investigación y Docencia",
            )
            await receptor.send(
                content=f"🎓 Tu certificado de **{cap}** fue autorizado:",
                file=discord.File(buf2, filename=f"certificado_{uid}.png"),
            )
        except Exception:
            pass

    await inter.followup.send(f"✅ Certificado **{num}** emitido y firmado.", ephemeral=True)


async def solicitar_autorizacion_certificado(
    bot: commands.Bot,
    inter: discord.Interaction,
    *,
    receptor: discord.Member,
    capacitacion: str,
    descripcion: str = "",
    departamento: str = "",
    firma_encargado_file: Optional[str] = None,
) -> int:
    """Crea pendiente y notifica al Director de Investigación y Docencia."""
    num = "CERT-PEND"
    try:
        import docencia as _doc
        reg_d = _doc.emitir(
            receptor.id, capacitacion, "personalizado", descripcion,
            inter.user.id, notas="pendiente autorización", departamento=departamento,
        )
        num = f"CERT-{int(reg_d.get('id') or 0):05d}"
    except Exception:
        pass

    aid = nueva_autorizacion({
        "tipo": "certificado",
        "callback": "emitir_certificado",
        "key_autorizador": KEY_DOCENCIA,
        "receptor_id": receptor.id,
        "nombre_receptor": receptor.display_name,
        "capacitacion": capacitacion,
        "descripcion": descripcion,
        "departamento": departamento,
        "encargado_id": inter.user.id,
        "encargado_nombre": inter.user.display_name,
        "firma_encargado": firma_encargado_file,
        "canal_id": inter.channel.id if inter.channel else None,
        "numero": num,
    })

    emb = discord.Embed(
        title=f"🖋️ Autorización de certificado · #{aid}",
        description=(
            f"**Solicitante (encargado):** {inter.user.mention}\n"
            f"**Graduado:** {receptor.mention}\n"
            f"**Capacitación:** {capacitacion}\n"
            f"**N.º provisional:** `{num}`\n\n"
            f"El **Director de Investigación y Docencia** debe **Autorizar y firmar**."
        ),
        color=0xF39C12,
        timestamp=discord.utils.utcnow(),
    )
    if departamento:
        emb.add_field(name="Área", value=departamento, inline=True)
    if descripcion:
        emb.add_field(name="Contenido", value=descripcion[:300], inline=False)

    view = VistaAutorizar(bot, aid)

    # Canal de aprobaciones / log
    dest = None
    try:
        import logs_store
        dest = logs_store.resolver_canal_log(bot, inter.guild, "aprobaciones")
        if not dest:
            dest = logs_store.resolver_canal_log(bot, inter.guild, "log_capacitaciones")
    except Exception:
        pass

    content = ""
    try:
        import roles_store
        rid = roles_store.obtener_id_key(KEY_DOCENCIA)
        if rid and inter.guild:
            rol = inter.guild.get_role(int(rid))
            if rol:
                content = rol.mention + " "
    except Exception:
        pass

    if dest:
        await dest.send(content=content or None, embed=emb, view=view)
    else:
        await inter.followup.send(content=content or None, embed=emb, view=view)

    return aid


def registrar(bot: commands.Bot) -> None:
    try:
        bot.add_view(VistaAutorizar(bot, 0))
    except Exception:
        pass

    @bot.tree.command(
        name="registrar_firma",
        description="Registra tu firma digitalizada (adjunta imagen PNG/JPG)",
    )
    @app_commands.describe(
        imagen="Imagen de tu firma (fondo transparente recomendado)",
        cargo="Cargo de la firma (para documentos IC)",
    )
    @app_commands.choices(cargo=[
        app_commands.Choice(name="Director de Investigación y Docencia", value="DIRECTOR_DOCENCIA"),
        app_commands.Choice(name="Director Médico", value="DIRECTOR_MEDICO"),
        app_commands.Choice(name="Director Administrativo", value="DIRECTOR_ADMINISTRATIVO"),
        app_commands.Choice(name="Director de RRHH", value="DIRECTOR_RRHH"),
        app_commands.Choice(name="Director General", value="DIRECTOR_GENERAL"),
        app_commands.Choice(name="Encargado / Instructor", value="ENCARGADO"),
        app_commands.Choice(name="Otra firma personal", value="PERSONAL"),
    ])
    async def registrar_firma(
        inter: discord.Interaction,
        imagen: discord.Attachment,
        cargo: app_commands.Choice[str],
    ):
        if not isinstance(inter.user, discord.Member):
            return await inter.response.send_message("Solo en servidor.", ephemeral=True)
        if not imagen.content_type or not imagen.content_type.startswith("image/"):
            return await inter.response.send_message("❌ Debe ser una imagen.", ephemeral=True)
        if imagen.size and imagen.size > 4_000_000:
            return await inter.response.send_message("❌ Imagen muy pesada (máx. 4 MB).", ephemeral=True)

        key = cargo.value
        # Validar que tenga el cargo (salvo ENCARGADO/PERSONAL)
        if key not in ("ENCARGADO", "PERSONAL") and not _es_key(inter.user, key, "OWNER"):
            return await inter.response.send_message(
                f"❌ No tienes el cargo **{cargo.name}**.", ephemeral=True
            )

        await inter.response.defer(ephemeral=True)
        fname = await descargar_firma(imagen, inter.user.id)
        guardar_firma(inter.user.id, key, fname)
        await inter.followup.send(
            f"✅ Firma registrada como **{cargo.name}**.\n"
            f"Archivo: `{fname}`\n"
            f"Se usará automáticamente al autorizar documentos IC.",
            ephemeral=True,
        )

    @bot.tree.command(name="ver_mi_firma", description="Muestra tu firma digitalizada registrada")
    async def ver_mi_firma(inter: discord.Interaction):
        reg = obtener_firma_usuario(inter.user.id)
        if not reg:
            return await inter.response.send_message(
                "No tienes firma. Usa `/registrar_firma` con una imagen.", ephemeral=True
            )
        path = ruta_firma(reg["file"])
        if not os.path.isfile(path):
            return await inter.response.send_message("Archivo de firma no encontrado.", ephemeral=True)
        await inter.response.send_message(
            content=f"🖋️ Tu firma ({reg.get('key', '—')})",
            file=discord.File(path, filename=reg["file"]),
            ephemeral=True,
        )

    print("[firmas] OK — registrar_firma / autorizaciones")
