# -*- coding: utf-8 -*-
"""
inactividad.py
==============
- Registra última actividad de miembros (mensajes / comandos).
- Si un miembro está inactivo X días SIN rol "Inactividad Justificada"
  y sin solicitud pendiente, el bot quita roles de cargo/hospital.
- /solicitar_inactividad: el miembro pide justificación; se envía por MD
  a Fundador y Owner, Co-Owner, Prefecto, Director General y Director de RRHH para aprobar/negar.
- Aprobado → se asigna rol "Inactividad Justificada" y NO se quitan roles.
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set

import discord
from discord import app_commands, ui
from discord.ext import commands, tasks

import config
import permisos
import registros
import roles_store
from estilos import crear_embed
from permisos import require_key

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_ACT_PATH = os.path.join(_DATA_DIR, "actividad.json")
_JUST_PATH = os.path.join(_DATA_DIR, "inactividad_justificada.json")
_PEND_PATH = os.path.join(_DATA_DIR, "inactividad_pendientes.json")

DIAS_INACTIVIDAD = int(getattr(config, "DIAS_INACTIVIDAD", 7) or 7)
HORAS_CHEQUEO = int(getattr(config, "HORAS_CHEQUEO_INACTIVIDAD", 12) or 12)

NOMBRE_ROL_JUSTIFICADA = getattr(
    config, "ROL_INACTIVIDAD_JUSTIFICADA_NOMBRE", "⏸️ Inactividad Justificada"
)
COLOR_ROL_JUSTIFICADA = getattr(config, "ROL_INACTIVIDAD_JUSTIFICADA_COLOR", "#95A5A6")

# NOTE: Full module restored — approval keys use organigrama:
# FUNDADOR_OWNER, CO_OWNER, PREFECTO_OPERACIONES, DIR_GENERAL, DIR_RRHH
# See commit history for complete logic; this is a recovery push.

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _iso(dt: Optional[datetime] = None) -> str:
    return (dt or _now()).isoformat()

def _parse_iso(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None

def _load(path: str) -> dict:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save(path: str, data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def registrar_actividad(uid: int) -> None:
    data = _load(_ACT_PATH)
    data[str(uid)] = _iso()
    _save(_ACT_PATH, data)

def ultima_actividad(uid: int) -> Optional[datetime]:
    data = _load(_ACT_PATH)
    return _parse_iso(data.get(str(uid), ""))

def dias_inactivo(uid: int) -> float:
    last = ultima_actividad(uid)
    if not last:
        return float(DIAS_INACTIVIDAD + 1)
    return (_now() - last).total_seconds() / 86400.0

def tiene_justificacion(uid: int, guild: Optional[discord.Guild] = None) -> bool:
    data = _load(_JUST_PATH)
    entry = data.get(str(uid))
    if entry:
        hasta = _parse_iso(entry.get("hasta", ""))
        if hasta and hasta > _now():
            return True
        if not hasta:
            return True
    if guild:
        rol = detectar_rol_justificada(guild)
        if rol:
            m = guild.get_member(uid)
            if m and rol in m.roles:
                return True
    return False

def marcar_justificado(uid: int, por: int, motivo: str, dias: int = 14) -> None:
    data = _load(_JUST_PATH)
    hasta = _now() + timedelta(days=max(1, dias))
    data[str(uid)] = {
        "motivo": motivo, "por": por, "desde": _iso(),
        "hasta": _iso(hasta), "dias": dias,
    }
    _save(_JUST_PATH, data)

def quitar_justificacion(uid: int) -> None:
    data = _load(_JUST_PATH)
    data.pop(str(uid), None)
    _save(_JUST_PATH, data)

def detectar_rol_justificada(guild: discord.Guild) -> Optional[discord.Role]:
    rid = roles_store.obtener_id_key("INACTIVIDAD_JUSTIFICADA")
    if rid:
        r = guild.get_role(int(rid))
        if r:
            return r
    rid = getattr(config, "ROL_INACTIVIDAD_JUSTIFICADA_ID", None)
    if rid:
        r = guild.get_role(int(rid))
        if r:
            return r
    nombre = NOMBRE_ROL_JUSTIFICADA.lower()
    for r in guild.roles:
        n = (r.name or "").lower()
        if "inactividad justificada" in n or n == nombre:
            return r
    return None

async def asegurar_rol_justificada(guild: discord.Guild) -> Optional[discord.Role]:
    rol = detectar_rol_justificada(guild)
    if rol:
        return rol
    try:
        color = (
            discord.Color.from_str(COLOR_ROL_JUSTIFICADA)
            if str(COLOR_ROL_JUSTIFICADA).startswith("#")
            else discord.Color.greyple()
        )
    except Exception:
        color = discord.Color.greyple()
    try:
        rol = await guild.create_role(
            name=NOMBRE_ROL_JUSTIFICADA, color=color,
            reason="Rol de inactividad justificada (auto)", mentionable=False,
        )
        roles_store.guardar_key("INACTIVIDAD_JUSTIFICADA", rol.id)
        return rol
    except Exception:
        return None

def roles_hospital_de(member: discord.Member, guild: discord.Guild) -> List[discord.Role]:
    out: List[discord.Role] = []
    seen: Set[int] = set()
    try:
        import roles_config
        keys_iter = roles_config.KEYS_NOMBRES
    except Exception:
        keys_iter = getattr(config, "KEYS_NOMBRES", {})
    for key in keys_iter:
        if key == "INACTIVIDAD_JUSTIFICADA":
            continue
        rid = roles_store.obtener_id_key(key)
        if not rid or rid in seen:
            continue
        rol = guild.get_role(rid)
        if rol and rol in member.roles:
            out.append(rol)
            seen.add(rol.id)
    for key in getattr(config, "KEYS_NOMBRES", {}):
        rid = roles_store.obtener_id_key(key)
        if not rid or rid in seen:
            continue
        rol = guild.get_role(rid)
        if rol and rol in member.roles:
            out.append(rol)
            seen.add(rol.id)
    return out

async def aplicar_inactividad(member: discord.Member, motivo: str = "Inactividad sin justificación") -> int:
    guild = member.guild
    roles = roles_hospital_de(member, guild)
    rol_j = detectar_rol_justificada(guild)
    if rol_j and rol_j in roles:
        roles = [r for r in roles if r.id != rol_j.id]
    if not roles:
        return 0
    try:
        await member.remove_roles(*roles, reason=motivo)
    except Exception:
        return -1
    try:
        registros.registrar_evento_cargo(member.id, "inactividad", motivo, 0)
    except Exception:
        pass
    return len(roles)

class AprobacionInactividadView(ui.View):
    def __init__(self, solicitud_id: str, uid: int, motivo: str, dias: int):
        super().__init__(timeout=None)
        self.solicitud_id = solicitud_id
        self.uid = uid
        self.motivo = motivo
        self.dias = dias

    async def _es_autorizado(self, inter: discord.Interaction) -> bool:
        if not isinstance(inter.user, discord.Member):
            return True
        return permisos.member_tiene_alguna_key(
            inter.user,
            "FUNDADOR_OWNER", "CO_OWNER", "PREFECTO_OPERACIONES", "DIR_GENERAL", "DIR_RRHH",
        )

    @ui.button(label="✅ Aprobar inactividad", style=discord.ButtonStyle.success, custom_id="inact_aprobar")
    async def aprobar(self, inter: discord.Interaction, button: ui.Button):
        if not await self._es_autorizado(inter):
            return await inter.response.send_message("❌ Sin permiso para aprobar.", ephemeral=True)
        if inter.user.id == self.uid:
            return await inter.response.send_message("❌ No puedes aprobar tu propia solicitud.", ephemeral=True)
        pend = _load(_PEND_PATH)
        info = pend.get(self.solicitud_id) or {"uid": self.uid, "motivo": self.motivo, "dias": self.dias}
        uid = int(info.get("uid", self.uid))
        motivo = info.get("motivo", self.motivo)
        dias = int(info.get("dias", self.dias) or 14)
        guild_id = int(info.get("guild_id", 0))
        await inter.response.defer(ephemeral=True)
        guild = inter.client.get_guild(guild_id) if guild_id else None
        if not guild and inter.client.guilds:
            guild = inter.client.guilds[0]
        if not guild:
            await inter.followup.send("❌ No se encontró el servidor.", ephemeral=True)
            return
        member = guild.get_member(uid)
        if not member:
            try:
                member = await guild.fetch_member(uid)
            except Exception:
                member = None
        if not member:
            await inter.followup.send("⚠️ Usuario ya no está en el servidor.", ephemeral=True)
            pend.pop(self.solicitud_id, None)
            _save(_PEND_PATH, pend)
            return
        marcar_justificado(uid, inter.user.id, motivo, dias)
        rol = await asegurar_rol_justificada(guild)
        if rol:
            try:
                await member.add_roles(rol, reason=f"Inactividad justificada por {inter.user}")
                await inter.followup.send(
                    f"✅ Inactividad de {member.mention} **aprobada**. Rol **{rol.name}** por {dias} días.",
                    ephemeral=True)
            except discord.Forbidden:
                await inter.followup.send(
                    f"✅ Justificación guardada, pero no pude asignar el rol (jerarquía).",
                    ephemeral=True)
        else:
            await inter.followup.send(
                f"✅ Inactividad de {member.mention} **aprobada** ({dias} días).",
                ephemeral=True)
        try:
            await member.send(embed=crear_embed(
                "exito", "⏸️ Inactividad justificada aprobada",
                f"Tu solicitud fue **aprobada**.\n**Motivo:** {motivo}\n**Duración:** {dias} días.\n"
                f"No se te quitarán los roles de cargo durante este período.",
            ))
        except discord.Forbidden:
            pass
        pend.pop(self.solicitud_id, None)
        _save(_PEND_PATH, pend)
        for c in self.children:
            c.disabled = True
        try:
            await inter.message.edit(view=self)
        except Exception:
            pass

    @ui.button(label="❌ Negar", style=discord.ButtonStyle.danger, custom_id="inact_negar")
    async def negar(self, inter: discord.Interaction, button: ui.Button):
        if not await self._es_autorizado(inter):
            return await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
        pend = _load(_PEND_PATH)
        info = pend.get(self.solicitud_id) or {"uid": self.uid, "motivo": self.motivo}
        uid = int(info.get("uid", self.uid))
        guild_id = int(info.get("guild_id", 0))
        await inter.response.defer(ephemeral=True)
        guild = inter.client.get_guild(guild_id) if guild_id else (inter.client.guilds[0] if inter.client.guilds else None)
        member = guild.get_member(uid) if guild else None
        await inter.followup.send("❌ Solicitud de inactividad **negada**.", ephemeral=True)
        if member:
            try:
                await member.send(embed=crear_embed(
                    "error", "❌ Solicitud de inactividad negada",
                    "Tu solicitud fue **rechazada**. Si permaneces inactivo sin justificación, "
                    "el bot podrá retirar tus roles de cargo.",
                ))
            except discord.Forbidden:
                pass
        pend.pop(self.solicitud_id, None)
        _save(_PEND_PATH, pend)
        for c in self.children:
            c.disabled = True
        try:
            await inter.message.edit(view=self)
        except Exception:
            pass

async def _enviar_md_aprobadores(bot, guild, embed, view) -> int:
    """Envía MD a FUNDADOR_OWNER, CO_OWNER, PREFECTO y DIR_RRHH."""
    enviados = 0
    ids_enviados: Set[int] = set()
    for key in ("FUNDADOR_OWNER", "CO_OWNER", "PREFECTO_OPERACIONES", "DIR_RRHH"):
        rid = roles_store.obtener_id_key(key)
        if not rid:
            continue
        rol = guild.get_role(rid)
        if not rol:
            continue
        for m in rol.members:
            if m.bot or m.id in ids_enviados:
                continue
            try:
                await m.send(embed=embed, view=view)
                enviados += 1
                ids_enviados.add(m.id)
            except Exception:
                continue
    canal = None
    for ck in ("aprobaciones_rrhh", "aprobaciones", "log_personal"):
        cid = config.CANALES.get(ck)
        if cid:
            canal = guild.get_channel(cid)
            if canal:
                break
    if canal:
        mention = ""
        rid_rrhh = roles_store.obtener_id_key("DIR_RRHH")
        if rid_rrhh:
            rol_rrhh = guild.get_role(rid_rrhh)
            if rol_rrhh:
                mention = rol_rrhh.mention
        try:
            await canal.send(content=mention or None, embed=embed, view=view)
            enviados += 1
        except Exception:
            pass
    return enviados

async def revisar_inactivos(bot, guild, dry_run: bool = False) -> dict:
    resumen = {"revisados": 0, "inactivos": 0, "quitados": 0, "justificados": 0, "errores": 0}
    umbral = DIAS_INACTIVIDAD
    for member in list(guild.members):
        if member.bot:
            continue
        roles_h = roles_hospital_de(member, guild)
        if not roles_h:
            continue
        # Eximir autoridades
        if permisos.member_tiene_alguna_key(member, "FUNDADOR_OWNER", "CO_OWNER"):
            continue
        resumen["revisados"] += 1
        if tiene_justificacion(member.id, guild):
            resumen["justificados"] += 1
            continue
        dias = dias_inactivo(member.id)
        if dias < umbral:
            continue
        resumen["inactivos"] += 1
        if dry_run:
            continue
        n = await aplicar_inactividad(
            member,
            motivo=f"Inactividad automática ({dias:.0f} días sin actividad, sin justificación)",
        )
        if n < 0:
            resumen["errores"] += 1
        elif n > 0:
            resumen["quitados"] += 1
            try:
                await member.send(embed=crear_embed(
                    "aviso", "⚠️ Roles retirados por inactividad",
                    f"Llevabas más de **{umbral} días** sin actividad y sin justificación.\n"
                    f"Se te retiraron **{n}** roles de cargo.\nUsa `/solicitar_inactividad` antes de ausentarte.",
                ))
            except discord.Forbidden:
                pass
    return resumen

def registrar(bot: commands.Bot) -> None:
    bot.add_view(AprobacionInactividadView("persist", 0, "", 14))

    @bot.listen("on_message")
    async def _track_msg(message: discord.Message):
        if message.author.bot or not message.guild:
            return
        registrar_actividad(message.author.id)

    @bot.listen("on_interaction")
    async def _track_inter(interaction: discord.Interaction):
        if interaction.user and not interaction.user.bot:
            registrar_actividad(interaction.user.id)

    @bot.tree.command(
        name="solicitar_inactividad",
        description="Solicita inactividad justificada (Gerencia/RRHH aprueban)",
    )
    @app_commands.describe(motivo="Razón de la inactividad", dias="Días de ausencia (1-10)")
    async def solicitar_inactividad(
        interaction: discord.Interaction,
        motivo: str,
        dias: app_commands.Range[int, 1, 10] = 7,
    ):
        if not isinstance(interaction.user, discord.Member) or not interaction.guild:
            await interaction.response.send_message("❌ Solo en el servidor.", ephemeral=True)
            return
        if tiene_justificacion(interaction.user.id, interaction.guild):
            await interaction.response.send_message("Ya tienes **inactividad justificada** activa.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        sid = f"inact_{interaction.user.id}_{int(_now().timestamp())}"
        pend = _load(_PEND_PATH)
        pend[sid] = {
            "uid": interaction.user.id, "motivo": motivo, "dias": int(dias),
            "guild_id": interaction.guild.id, "fecha": _iso(),
        }
        _save(_PEND_PATH, pend)
        embed = crear_embed(
            "aviso", "⏸️ Solicitud de inactividad justificada",
            f"**Usuario:** {interaction.user.mention} (`{interaction.user.id}`)\n"
            f"**Motivo:** {motivo}\n**Días solicitados:** {dias}\n\n"
            f"Si **apruebas**, se asignará el rol **{NOMBRE_ROL_JUSTIFICADA}**.\n"
            f"_Aprobadores: Fundador y Owner, Co-Owner, Prefecto, Dir. General, Dir. RRHH._",
            autor=interaction.user,
        )
        view = AprobacionInactividadView(sid, interaction.user.id, motivo, int(dias))
        n = await _enviar_md_aprobadores(bot, interaction.guild, embed, view)
        if n > 0:
            await interaction.followup.send(
                f"✅ Solicitud enviada a **{n}** aprobador(es). Máximo 10 días por solicitud.",
                ephemeral=True)
        else:
            await interaction.followup.send(
                "⚠️ Solicitud guardada, pero no pude contactar aprobadores (sin rol o DM cerrado).",
                ephemeral=True)

    @bot.tree.command(name="inactividad", description="Consulta estado de inactividad")
    @app_commands.describe(usuario="Usuario (opcional; staff ve otros)")
    async def cmd_inactividad(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
        target = usuario or interaction.user
        if usuario and usuario.id != interaction.user.id:
            if not isinstance(interaction.user, discord.Member) or not permisos.member_tiene_alguna_key(
                interaction.user,
                "FUNDADOR_OWNER", "CO_OWNER", "PREFECTO_OPERACIONES", "DIR_GENERAL", "DIR_RRHH",
            ):
                await interaction.response.send_message("❌ Sin permiso para consultar a otros.", ephemeral=True)
                return
        dias = dias_inactivo(target.id)
        just = tiene_justificacion(target.id, interaction.guild)
        emb = crear_embed(
            "info" if just or dias < DIAS_INACTIVIDAD else "aviso",
            f"⏸️ Inactividad · {getattr(target, 'display_name', target)}",
            f"**Días sin actividad:** {dias:.1f}\n"
            f"**Justificada:** {'✅ Sí' if just else '❌ No'}\n"
            f"**Umbral:** {DIAS_INACTIVIDAD} días",
        )
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @bot.tree.command(name="reporte_inactividad", description="Lista inactivos y justificadas (Gerencia)")
    @require_key("FUNDADOR_OWNER", "CO_OWNER", "PREFECTO_OPERACIONES", "DIR_GENERAL", "DIR_RRHH")
    async def reporte_inactividad(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not interaction.guild:
            return await interaction.followup.send("❌ Solo en servidor.", ephemeral=True)
        inactivos = []
        justificadas = []
        for m in interaction.guild.members:
            if m.bot:
                continue
            if not roles_hospital_de(m, interaction.guild):
                continue
            if tiene_justificacion(m.id, interaction.guild):
                justificadas.append(m)
            elif dias_inactivo(m.id) >= DIAS_INACTIVIDAD:
                inactivos.append((m, dias_inactivo(m.id)))
        lines = [f"**Inactivos (≥{DIAS_INACTIVIDAD}d):** {len(inactivos)}"]
        for m, d in sorted(inactivos, key=lambda x: -x[1])[:20]:
            lines.append(f"• {m.mention} — {d:.0f}d")
        lines.append(f"\n**Justificadas activas:** {len(justificadas)}")
        for m in justificadas[:15]:
            lines.append(f"• {m.mention}")
        await interaction.followup.send(embed=crear_embed("info", "📋 Reporte de inactividad", "\n".join(lines)), ephemeral=True)

    print(f"[inactividad] OK — umbral {DIAS_INACTIVIDAD}d (Prefecto/DIR_RRHH/DIR_GENERAL/Autoridades)")
