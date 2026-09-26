# -*- coding: utf-8 -*
"""
licencia_medica.py — /licencia: otorga licencia médica con firma de
Director Médico + Director General.
"""
from __future__ import annotations

import json
import os
import traceback
from datetime import datetime, timezone
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "licencias_medicas.json")
_PEND = {}

KEY_MEDICO = "DIRECTOR_MEDICO"
KEY_GENERAL = "DIRECTOR_GENERAL"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> dict:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_PATH):
        return {"items": [], "next_id": 1}
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            d = json.load(f)
        d.setdefault("items", [])
        d.setdefault("next_id", 1)
        return d
    except Exception:
        return {"items": [], "next_id": 1}


def _save(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _registrar_licencia(reg: dict) -> int:
    data = _load()
    lid = int(data.get("next_id") or 1)
    data["next_id"] = lid + 1
    reg = dict(reg)
    reg["id"] = lid
    reg["fecha_emision"] = _now()
    reg["estado"] = "activa"
    data["items"].append(reg)
    _save(data)
    return lid


def embed_solicitud(reg: dict) -> discord.Embed:
    emb = discord.Embed(
        title=f"📋 Solicitud de licencia médica · #{reg.get('sid', '?')}",
        description="Requiere **firma del Director Médico** y del **Director General**.",
        color=0xF39C12,
    )
    emb.add_field(name="1. Solicitante", value=f"<@{reg['solicitante_id']}>", inline=True)
    emb.add_field(name="2. Beneficiario", value=f"<@{reg['receptor_id']}> ({reg.get('nombre_receptor')})", inline=True)
    emb.add_field(name="3. Cédula / ID", value=reg.get("cedula") or "—", inline=True)
    emb.add_field(name="4. Especialidad / área", value=reg.get("especialidad") or "—", inline=True)
    emb.add_field(name="5. N.º propuesto", value=reg.get("numero") or "(auto)", inline=True)
    emb.add_field(name="6. Vigencia", value=reg.get("vigencia") or "Indefinida / RP", inline=True)
    if reg.get("institucion"):
        emb.add_field(name="7. Institución / universidad", value=reg["institucion"][:200], inline=False)
    if reg.get("observaciones"):
        emb.add_field(name="8. Observaciones", value=reg["observaciones"][:500], inline=False)

    med = "✅" if reg.get("firma_medico") else "⏳ Pendiente"
    gen = "✅" if reg.get("firma_general") else "⏳ Pendiente"
    emb.add_field(name="Director Médico", value=med, inline=True)
    emb.add_field(name="Director General", value=gen, inline=True)
    emb.set_footer(text="Ambas firmas son obligatorias para emitir la licencia.")
    return emb


async def _safe(inter: discord.Interaction, content: str = None, *, embed=None, ephemeral=True, view=None):
    try:
        kw = dict(content=content, embed=embed, ephemeral=ephemeral, view=view)
        if inter.response.is_done():
            await inter.followup.send(**{k: v for k, v in kw.items() if v is not None})
        else:
            await inter.response.send_message(**{k: v for k, v in kw.items() if v is not None})
    except Exception as e:
        print("[licencia] safe:", e)


class FirmaLicenciaView(discord.ui.View):
    def __init__(self, sid: str):
        super().__init__(timeout=86400 * 3)
        self.sid = sid

    def _reg(self) -> Optional[dict]:
        return _PEND.get(self.sid)

    async def _check_key(self, inter: discord.Interaction, key: str) -> bool:
        if not isinstance(inter.user, discord.Member):
            await _safe(inter, "❌ Solo en el servidor.")
            return False
        try:
            import permisos
            if permisos.member_tiene_alguna_key(inter.user, key, "OWNER", "CO_OWNER"):
                return True
        except Exception:
            pass
        await _safe(inter, f"❌ Se requiere key **{key}** (o OWNER/CO_OWNER).")
        return False

    async def _refresh(self, inter: discord.Interaction, reg: dict):
        emb = embed_solicitud(reg)
        if reg.get("firma_medico") and reg.get("firma_general"):
            emb.color = discord.Colour.green()
        try:
            if inter.response.is_done():
                await inter.message.edit(embed=emb, view=self)
            else:
                await inter.response.edit_message(embed=emb, view=self)
        except Exception:
            try:
                await inter.message.edit(embed=emb, view=self)
            except Exception:
                pass

    async def _emitir_si_completo(self, inter: discord.Interaction, reg: dict):
        if not (reg.get("firma_medico") and reg.get("firma_general")):
            return
        for c in self.children:
            c.disabled = True

        guild = inter.guild
        member = guild.get_member(int(reg["receptor_id"])) if guild else None
        if not member and guild:
            try:
                member = await guild.fetch_member(int(reg["receptor_id"]))
            except Exception:
                member = None

        data = _load()
        num = reg.get("numero") or f"LM-{int(data.get('next_id') or 1):05d}"
        lid = _registrar_licencia({
            "receptor_id": reg["receptor_id"],
            "nombre_receptor": reg.get("nombre_receptor"),
            "cedula": reg.get("cedula"),
            "especialidad": reg.get("especialidad"),
            "numero": num,
            "vigencia": reg.get("vigencia"),
            "institucion": reg.get("institucion"),
            "observaciones": reg.get("observaciones"),
            "solicitante_id": reg["solicitante_id"],
            "firma_medico_id": reg.get("firma_medico_id"),
            "firma_general_id": reg.get("firma_general_id"),
            "firma_medico_nombre": reg.get("firma_medico_nombre"),
            "firma_general_nombre": reg.get("firma_general_nombre"),
        })

        # Rol licencia médica
        rol_msg = ""
        if member:
            try:
                from roles_otorgados import asignar_clave
                ok, msg = await asignar_clave(member, "licencia_medica", reason=f"Licencia médica #{lid}")
                rol_msg = msg
            except Exception as e:
                rol_msg = f"(rol: {e})"

        emb = discord.Embed(
            title="✅ Licencia médica emitida",
            description=(
                f"**Titular:** <@{reg['receptor_id']}>\n"
                f"**N.º:** `{num}` · Registro **#{lid}**\n"
                f"**Especialidad:** {reg.get('especialidad') or '—'}\n"
                f"**Cédula:** {reg.get('cedula') or '—'}\n"
                f"**Vigencia:** {reg.get('vigencia') or 'Indefinida / RP'}\n\n"
                f"**Firmas:**\n"
                f"• Director Médico: {reg.get('firma_medico_nombre', '—')}\n"
                f"• Director General: {reg.get('firma_general_nombre', '—')}\n"
                f"\n🎭 {rol_msg}"
            ),
            color=0x2ECC71,
        )
        try:
            await inter.message.edit(embed=embed_solicitud(reg), view=self)
        except Exception:
            pass
        try:
            await inter.followup.send(embed=emb)
        except Exception:
            await _safe(inter, embed=emb, ephemeral=False)

        _PEND.pop(self.sid, None)

    @discord.ui.button(label="✍️ Firmar (Dir. Médico)", style=discord.ButtonStyle.primary)
    async def firmar_medico(self, inter: discord.Interaction, btn: discord.ui.Button):
        if not await self._check_key(inter, KEY_MEDICO):
            return
        reg = self._reg()
        if not reg:
            return await _safe(inter, "Esta solicitud ya fue resuelta.")
        if reg.get("firma_medico"):
            return await _safe(inter, "El Director Médico ya firmó.")
        reg["firma_medico"] = True
        reg["firma_medico_id"] = inter.user.id
        reg["firma_medico_nombre"] = inter.user.display_name
        await self._refresh(inter, reg)
        if not inter.response.is_done():
            await inter.response.defer()
        await inter.followup.send(f"✅ Firma del **Director Médico** registrada por {inter.user.mention}.", ephemeral=True)
        await self._emitir_si_completo(inter, reg)

    @discord.ui.button(label="✍️ Firmar (Dir. General)", style=discord.ButtonStyle.success)
    async def firmar_general(self, inter: discord.Interaction, btn: discord.ui.Button):
        if not await self._check_key(inter, KEY_GENERAL):
            return
        reg = self._reg()
        if not reg:
            return await _safe(inter, "Esta solicitud ya fue resuelta.")
        if reg.get("firma_general"):
            return await _safe(inter, "El Director General ya firmó.")
        reg["firma_general"] = True
        reg["firma_general_id"] = inter.user.id
        reg["firma_general_nombre"] = inter.user.display_name
        await self._refresh(inter, reg)
        if not inter.response.is_done():
            await inter.response.defer()
        await inter.followup.send(f"✅ Firma del **Director General** registrada por {inter.user.mention}.", ephemeral=True)
        await self._emitir_si_completo(inter, reg)

    @discord.ui.button(label="❌ Rechazar", style=discord.ButtonStyle.danger)
    async def rechazar(self, inter: discord.Interaction, btn: discord.ui.Button):
        if not await self._check_key(inter, KEY_MEDICO):
            # también puede rechazar DG
            if not await self._check_key(inter, KEY_GENERAL):
                return
        reg = self._reg()
        if not reg:
            return await _safe(inter, "Ya fue resuelta.")
        _PEND.pop(self.sid, None)
        for c in self.children:
            c.disabled = True
        emb = embed_solicitud(reg)
        emb.color = discord.Colour.red()
        emb.title = f"❌ Licencia rechazada · #{reg.get('sid')}"
        try:
            await inter.response.edit_message(embed=emb, view=self)
        except Exception:
            await _safe(inter, f"Rechazada por {inter.user.mention}.")


def registrar(bot: commands.Bot) -> None:
    print("[licencia_medica] cargando…")
    try:
        _reg(bot)
        print("[licencia_medica] ✓ OK")
    except Exception:
        print("[licencia_medica] ✗ error:")
        traceback.print_exc()


def _reg(bot: commands.Bot) -> None:
    import permisos
    import roles_store

    # Si existe /licencia viejo del núcleo, lo quitamos para este
    try:
        bot.tree.remove_command("licencia")
    except Exception:
        pass

    @bot.tree.command(
        name="licencia",
        description="Solicitar licencia médica (firma Dir. Médico + Dir. General)",
    )
    @app_commands.describe(
        usuario="Persona a quien se otorga la licencia",
        cedula="Cédula / identificación del titular",
        especialidad="Especialidad o área médica",
        vigencia="Vigencia (ej. 1 año, indefinida RP)",
        numero="N.º de licencia (opcional; si vacío se genera)",
        institucion="Universidad / institución de origen (opcional)",
        observaciones="Notas adicionales (opcional)",
    )
    async def licencia_cmd(
        inter: discord.Interaction,
        usuario: discord.Member,
        cedula: str,
        especialidad: str,
        vigencia: str = "Indefinida (RP)",
        numero: str = "",
        institucion: str = "",
        observaciones: str = "",
    ):
        try:
            if not isinstance(inter.user, discord.Member) or not inter.guild:
                return await _safe(inter, "❌ Solo usable en el servidor.")

            # Quién puede solicitar: mandos médicos / RRHH / docencia / altos
            if not permisos.member_tiene_alguna_key(
                inter.user,
                "DIRECTOR_MEDICO", "DIRECTOR_GENERAL", "DIRECTOR_RRHH",
                "DIRECTOR_DOCENCIA", "DIRECTOR", "JEFE_DEPARTAMENTO",
                "ENCARGADO_AREA", "SUPERVISOR", "OWNER", "CO_OWNER",
            ):
                return await _safe(
                    inter,
                    "❌ Sin permiso para solicitar licencia médica.\n"
                    "Se requiere mando médico, RRHH, Docencia o superior.",
                )

            if not (cedula or "").strip():
                return await _safe(inter, "❌ La **cédula / identificación** es obligatoria.")
            if not (especialidad or "").strip():
                return await _safe(inter, "❌ La **especialidad** es obligatoria.")

            sid = f"lic_{inter.user.id}_{int(datetime.now(timezone.utc).timestamp())}"
            reg = {
                "sid": sid,
                "solicitante_id": inter.user.id,
                "receptor_id": usuario.id,
                "nombre_receptor": usuario.display_name,
                "cedula": cedula.strip()[:80],
                "especialidad": especialidad.strip()[:120],
                "vigencia": (vigencia or "Indefinida (RP)").strip()[:80],
                "numero": (numero or "").strip()[:40],
                "institucion": (institucion or "").strip()[:200],
                "observaciones": (observaciones or "").strip()[:500],
                "firma_medico": False,
                "firma_general": False,
            }
            _PEND[sid] = reg

            emb = embed_solicitud(reg)
            view = FirmaLicenciaView(sid)

            # Mencionar roles aprobadores
            menciones = []
            for k in (KEY_MEDICO, KEY_GENERAL):
                rid = roles_store.obtener_id_key(k)
                if rid:
                    rol = inter.guild.get_role(rid)
                    if rol:
                        menciones.append(rol.mention)

            await _safe(
                inter,
                content=(
                    f"📋 Solicitud de **licencia médica** para {usuario.mention}.\n"
                    f"Deben firmar: {' '.join(menciones) or '**Director Médico** y **Director General**'}"
                ),
                embed=emb,
                view=view,
                ephemeral=False,
            )
        except Exception as e:
            traceback.print_exc()
            await _safe(inter, f"❌ Error: `{e}`")
