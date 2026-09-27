# -*- coding: utf-8 -*-
"""
inactividad.py
==============
- Registra última actividad de miembros (mensajes / comandos).
- Si un miembro está inactivo X días SIN rol "Inactividad Justificada"
  y sin solicitud pendiente, el bot quita roles de cargo/hospital.
- /solicitar_inactividad: el miembro pide justificación; se envía por MD
  a Gerente Developer (OWNER) y Co-Owner para aprobar/negar.
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

# Días sin actividad para considerar inactivo (configurable)
DIAS_INACTIVIDAD = int(getattr(config, "DIAS_INACTIVIDAD", 7) or 7)
# Intervalo del chequeo automático (horas)
HORAS_CHEQUEO = int(getattr(config, "HORAS_CHEQUEO_INACTIVIDAD", 12) or 12)

NOMBRE_ROL_JUSTIFICADA = getattr(
    config, "ROL_INACTIVIDAD_JUSTIFICADA_NOMBRE", "⏸️ Inactividad Justificada"
)
COLOR_ROL_JUSTIFICADA = getattr(config, "ROL_INACTIVIDAD_JUSTIFICADA_COLOR", "#95A5A6")


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
        return float(DIAS_INACTIVIDAD + 1)  # sin registro = tratado como inactivo
    return (_now() - last).total_seconds() / 86400.0


def tiene_justificacion(uid: int, guild: Optional[discord.Guild] = None) -> bool:
    data = _load(_JUST_PATH)
    entry = data.get(str(uid))
    if entry:
        hasta = _parse_iso(entry.get("hasta", ""))
        if hasta and hasta > _now():
            return True
        if not hasta:
            return True  # sin fecha fin = vigente
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
        "motivo": motivo,
        "por": por,
        "desde": _iso(),
        "hasta": _iso(hasta),
        "dias": dias,
    }
    _save(_JUST_PATH, data)


def quitar_justificacion(uid: int) -> None:
    data = _load(_JUST_PATH)
    data.pop(str(uid), None)
    _save(_JUST_PATH, data)


def detectar_rol_justificada(guild: discord.Guild) -> Optional[discord.Role]:
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
    # Intentar crear
    try:
        color = discord.Color.from_str(COLOR_ROL_JUSTIFICADA) if COLOR_ROL_JUSTIFICADA.startswith("#") else discord.Color.greyple()
    except Exception:
        color = discord.Color.greyple()
    try:
        rol = await guild.create_role(
            name=NOMBRE_ROL_JUSTIFICADA,
            color=color,
            reason="Rol de inactividad justificada (auto)",
            mentionable=False,
        )
        return rol
    except discord.Forbidden:
        return None
    except Exception:
        return None


def roles_hospital_de(member: discord.Member, guild: discord.Guild) -> List[discord.Role]:
    """Roles de cargo/keys y escalafones (no quita comunidad ni @everyone)."""
    out: List[discord.Role] = []
    seen: Set[int] = set()
    for key in getattr(config, "KEYS_NOMBRES", {}):
        rid = roles_store.obtener_id_key(key)
        if not rid or rid in seen:
            continue
        rol = guild.get_role(rid)
        if rol and rol in member.roles:
            out.append(rol)
            seen.add(rol.id)
    for slug, data in getattr(config, "DEPARTAMENTOS", {}).items():
        try:
            ids = roles_store.escalafon_ids(slug, len(data.get("escalafon_nombres", [])))
        except Exception:
            ids = []
        for rid in ids:
            if not rid or rid in seen:
                continue
            rol = guild.get_role(rid)
            if rol and rol in member.roles:
                out.append(rol)
                seen.add(rol.id)
    # También roles de ROLES_OTORGADOS (certificados, etc.) si se desea quitar
    for _slug, tup in getattr(config, "ROLES_OTORGADOS", {}).items():
        nombre = tup[0] if isinstance(tup, (list, tuple)) else None
        if not nombre:
            continue
        for r in member.roles:
            if r.id in seen:
                continue
            if (r.name or "") == nombre:
                out.append(r)
                seen.add(r.id)
    return out


async def aplicar_inactividad(member: discord.Member, motivo: str = "Inactividad sin justificación") -> int:
    """Quita roles de hospital. Devuelve cantidad quitados."""
    guild = member.guild
    roles = roles_hospital_de(member, guild)
    # No quitar el rol de justificada si lo tuviera (caso raro)
    rol_j = detectar_rol_justificada(guild)
    if rol_j and rol_j in roles:
        roles = [r for r in roles if r.id != rol_j.id]
    if not roles:
        return 0
    try:
        await member.remove_roles(*roles, reason=motivo)
    except discord.Forbidden:
        return -1
    except Exception:
        return -1
    try:
        registros.registrar_evento_cargo(member.id, "inactividad", motivo, 0)
    except Exception:
        pass
    return len(roles)


# ---------------------------------------------------------------------------
# Vista de aprobación por MD (Owner / Co-Owner)
# ---------------------------------------------------------------------------
class AprobacionInactividadView(ui.View):
    def __init__(self, solicitud_id: str, uid: int, motivo: str, dias: int):
        super().__init__(timeout=None)
        self.solicitud_id = solicitud_id
        self.uid = uid
        self.motivo = motivo
        self.dias = dias

    async def _es_autorizado(self, inter: discord.Interaction) -> bool:
        if not isinstance(inter.user, discord.Member):
            # En MD el user no es Member; validar por keys guardadas / ID en pendiente
            # Permitimos si es el destinatario del MD (OWNER/CO_OWNER que recibió el mensaje)
            return True
        return permisos.member_tiene_alguna_key(
            inter.user, "OWNER", "CO_OWNER", "DIRECTOR_GENERAL"
        )

    @ui.button(label="✅ Aprobar inactividad", style=discord.ButtonStyle.success, custom_id="inact_aprobar")
    async def aprobar(self, inter: discord.Interaction, button: ui.Button):
        pend = _load(_PEND_PATH)
        info = pend.get(self.solicitud_id)
        if not info:
            # Recuperar de custom si se reinició
            info = {"uid": self.uid, "motivo": self.motivo, "dias": self.dias}
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
            except discord.Forbidden:
                await inter.followup.send(
                    f"✅ Justificación guardada, pero no pude asignar el rol {rol.mention} (jerarquía).",
                    ephemeral=True,
                )
            else:
                await inter.followup.send(
                    f"✅ Inactividad de {member.mention} **aprobada**. Rol **{rol.name}** asignado por {dias} días.",
                    ephemeral=True,
                )
        else:
            await inter.followup.send(
                f"✅ Inactividad de {member.mention} **aprobada** ({dias} días). "
                f"Crea el rol **{NOMBRE_ROL_JUSTIFICADA}** o sube permisos del bot.",
                ephemeral=True,
            )

        try:
            await member.send(
                embed=crear_embed(
                    "exito",
                    "⏸️ Inactividad justificada aprobada",
                    f"Tu solicitud fue **aprobada**.\n**Motivo:** {motivo}\n**Duración:** {dias} días.\n"
                    f"No se te quitarán los roles de cargo durante este período.",
                )
            )
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
                await member.send(
                    embed=crear_embed(
                        "error",
                        "❌ Solicitud de inactividad negada",
                        "Tu solicitud de inactividad justificada fue **rechazada**. "
                        "Si permaneces inactivo sin justificación, el bot podrá retirar tus roles de cargo.",
                    )
                )
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


async def _enviar_md_aprobadores(
    bot: discord.Client,
    guild: discord.Guild,
    embed: discord.Embed,
    view: ui.View,
) -> int:
    """Envía MD a miembros con key OWNER o CO_OWNER. Devuelve cuántos MD se enviaron."""
    enviados = 0
    ids_enviados: Set[int] = set()
    for key in ("OWNER", "CO_OWNER"):
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
            except discord.Forbidden:
                continue
            except Exception:
                continue
    # Fallback: dueño del servidor
    if enviados == 0 and guild.owner_id:
        owner = guild.get_member(guild.owner_id)
        if owner and not owner.bot:
            try:
                await owner.send(embed=embed, view=view)
                enviados = 1
            except Exception:
                pass
    return enviados


# ---------------------------------------------------------------------------
# Chequeo periódico
# ---------------------------------------------------------------------------
async def revisar_inactivos(bot: discord.Client, guild: discord.Guild, dry_run: bool = False) -> dict:
    """
    Revisa miembros con roles de hospital.
    Si llevan DIAS_INACTIVIDAD sin actividad y sin justificación → quita roles.
    """
    resumen = {"revisados": 0, "inactivos": 0, "quitados": 0, "justificados": 0, "errores": 0}
    umbral = DIAS_INACTIVIDAD

    for member in list(guild.members):
        if member.bot:
            continue
        roles_h = roles_hospital_de(member, guild)
        if not roles_h:
            continue  # solo personal con cargo
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
                await member.send(
                    embed=crear_embed(
                        "aviso",
                        "⚠️ Roles retirados por inactividad",
                        f"Llevabas más de **{umbral} días** sin actividad y **sin solicitud de inactividad justificada**.\n"
                        f"Se te retiraron **{n}** roles de cargo.\n\n"
                        f"Si fue un error, contacta a Gerente Developer / Co-Owner o usa `/solicitar_inactividad` "
                        f"antes de volver a estar ausente.",
                    )
                )
            except discord.Forbidden:
                pass
            # Log
            canal_id = config.CANALES.get("log_personal") or config.CANALES.get("log_roles")
            if canal_id:
                canal = guild.get_channel(canal_id)
                if canal:
                    try:
                        await canal.send(
                            embed=crear_embed(
                                "aviso",
                                "⏸️ Inactividad — roles retirados",
                                f"**Usuario:** {member.mention}\n**Días inactivo:** {dias:.0f}\n**Roles quitados:** {n}",
                            )
                        )
                    except Exception:
                        pass
    return resumen


def registrar(bot: commands.Bot) -> None:
    # Vista persistente (tras reinicio los botones siguen, pero necesitan datos en pendiente)
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
        description="Solicita inactividad justificada (Owner/Co-Owner aprueban por MD)",
    )
    @app_commands.describe(
        motivo="Razón de la inactividad",
        dias="Días de ausencia estimados (1-60)",
    )
    async def solicitar_inactividad(
        interaction: discord.Interaction,
        motivo: str,
        dias: app_commands.Range[int, 1, 60] = 14,
    ):
        if not isinstance(interaction.user, discord.Member) or not interaction.guild:
            await interaction.response.send_message("❌ Solo en el servidor.", ephemeral=True)
            return

        if tiene_justificacion(interaction.user.id, interaction.guild):
            await interaction.response.send_message(
                "Ya tienes **inactividad justificada** activa.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        sid = f"inact_{interaction.user.id}_{int(_now().timestamp())}"
        pend = _load(_PEND_PATH)
        pend[sid] = {
            "uid": interaction.user.id,
            "motivo": motivo,
            "dias": int(dias),
            "guild_id": interaction.guild.id,
            "fecha": _iso(),
        }
        _save(_PEND_PATH, pend)

        embed = crear_embed(
            "aviso",
            "⏸️ Solicitud de inactividad justificada",
            f"**Usuario:** {interaction.user.mention} (`{interaction.user.id}`)\n"
            f"**Motivo:** {motivo}\n"
            f"**Días solicitados:** {dias}\n\n"
            f"Si **apruebas**, se asignará el rol **{NOMBRE_ROL_JUSTIFICADA}** y "
            f"**no** se le quitarán los roles de cargo durante ese período.\n"
            f"Si **niegas**, el sistema de inactividad podrá retirar roles si sigue ausente.",
            autor=interaction.user,
        )
        view = AprobacionInactividadView(sid, interaction.user.id, motivo, int(dias))
        n = await _enviar_md_aprobadores(bot, interaction.guild, embed, view)

        if n > 0:
            await interaction.followup.send(
                f"✅ Solicitud enviada por **MD** a Gerente Developer / Co-Owner ({n} destinatario(s)). "
                f"Te avisaremos cuando respondan.",
                ephemeral=True,
            )
        else:
            # Fallback: canal de aprobaciones
            canal_id = config.CANALES.get("aprobaciones") or config.CANALES.get("log_personal")
            canal = interaction.guild.get_channel(canal_id) if canal_id else None
            if canal:
                await canal.send(embed=embed, view=view)
                await interaction.followup.send(
                    f"⚠️ No pude enviar MD a Owner/Co-Owner. Solicitud publicada en {canal.mention}.",
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(
                    "❌ No hay Owner/Co-Owner con MD abiertos ni canal de aprobaciones configurado.",
                    ephemeral=True,
                )

    @bot.tree.command(
        name="revisar_inactividad",
        description="Revisa miembros inactivos y retira roles si no tienen justificación",
    )
    @app_commands.describe(simular="Si es True, solo lista sin quitar roles")
    @require_key("OWNER", "CO_OWNER", "DIRECTOR_GENERAL", "DIRECTOR_RRHH")
    async def revisar_inactividad(
        interaction: discord.Interaction,
        simular: bool = False,
    ):
        if not interaction.guild:
            await interaction.response.send_message("❌ Solo en servidor.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        res = await revisar_inactivos(bot, interaction.guild, dry_run=simular)
        modo = "(simulación)" if simular else ""
        await interaction.followup.send(
            f"✅ Revisión de inactividad {modo}\n"
            f"• Personal revisado: **{res['revisados']}**\n"
            f"• Con justificación: **{res['justificados']}**\n"
            f"• Inactivos detectados: **{res['inactivos']}**\n"
            f"• Roles retirados: **{res['quitados']}**\n"
            f"• Errores: **{res['errores']}**\n"
            f"• Umbral: **{DIAS_INACTIVIDAD} días**",
            ephemeral=True,
        )

    @bot.tree.command(
        name="quitar_inactividad",
        description="Quita la justificación de inactividad a un miembro",
    )
    @app_commands.describe(usuario="Usuario")
    @require_key("OWNER", "CO_OWNER", "DIRECTOR_GENERAL", "DIRECTOR_RRHH")
    async def quitar_inactividad_cmd(
        interaction: discord.Interaction,
        usuario: discord.Member,
    ):
        quitar_justificacion(usuario.id)
        rol = detectar_rol_justificada(interaction.guild) if interaction.guild else None
        if rol and rol in usuario.roles:
            try:
                await usuario.remove_roles(rol, reason=f"Justificación retirada por {interaction.user}")
            except discord.Forbidden:
                pass
        await interaction.response.send_message(
            f"✅ Justificación de inactividad retirada a {usuario.mention}.",
            ephemeral=True,
        )

    # Tarea periódica
    @tasks.loop(hours=max(1, HORAS_CHEQUEO))
    async def _loop_inactividad():
        await bot.wait_until_ready()
        for g in bot.guilds:
            try:
                await revisar_inactivos(bot, g, dry_run=False)
            except Exception as e:
                print(f"[inactividad] error guild {g.id}: {e}")

    @_loop_inactividad.before_loop
    async def _before():
        await bot.wait_until_ready()
        await asyncio.sleep(30)

    if not _loop_inactividad.is_running():
        _loop_inactividad.start()

    print(f"[inactividad] OK — umbral {DIAS_INACTIVIDAD}d, chequeo cada {HORAS_CHEQUEO}h")
