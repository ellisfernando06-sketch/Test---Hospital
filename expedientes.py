# -*- coding: utf-8 -*
"""
expedientes.py — plantilla detallada, aprobacion por seccion, multi-usuario.
"""
from __future__ import annotations

import json
import os
import traceback
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Sequence, Tuple

import discord
from discord import app_commands
from discord.ext import commands

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "expedientes_tipo.json")

# Aprobadores cuando el expediente es CONTRA un director (no puede auto-aprobar).
# RRHH y Disciplina son entidades independientes del Director General.
_APROBADORES_CONTRA_DIRECTOR = (
    "DIRECTOR_GENERAL",
    "DIRECTOR_RRHH",
    "DIRECTOR_DISCIPLINA",
    "OWNER",
    "CO_OWNER",
)

TIPOS = {
    "administrativo": {
        "nombre": "Administrativo",
        "accion_default": "despido",
        "keys": ("DIRECTOR_ADMINISTRATIVO", "OWNER", "CO_OWNER"),
        "aprobador": "DIRECTOR_ADMINISTRATIVO",
    },
    "disciplinario": {
        "nombre": "Disciplinario",
        "accion_default": "mute_24h",
        "keys": ("DIRECTOR_DISCIPLINA", "OWNER", "CO_OWNER"),
        "aprobador": "DIRECTOR_DISCIPLINA",
    },
    "investigacion_rrhh": {
        "nombre": "Investigación RRHH",
        "accion_default": "despido",
        "keys": ("DIRECTOR_RRHH", "OWNER", "CO_OWNER"),
        "aprobador": "DIRECTOR_RRHH",
    },
    "dir_medico": {
        "nombre": "Dirección Médica",
        "accion_default": "despido",
        "keys": ("DIRECTOR_MEDICO", "OWNER", "CO_OWNER"),
        "aprobador": "DIRECTOR_MEDICO",
    },
    "dir_enfermeria": {
        "nombre": "Dirección Enfermería",
        "accion_default": "despido",
        "keys": ("DIRECTOR_ENFERMERIA", "OWNER", "CO_OWNER"),
        "aprobador": "DIRECTOR_ENFERMERIA",
    },
    "dir_seguridad": {
        "nombre": "Dirección Seguridad",
        "accion_default": "despido",
        "keys": ("DIRECTOR_SEGURIDAD", "OWNER", "CO_OWNER"),
        "aprobador": "DIRECTOR_SEGURIDAD",
    },
    "dir_logistica": {
        "nombre": "Dirección Logística",
        "accion_default": "despido",
        "keys": ("DIRECTOR_LOGISTICA", "OWNER", "CO_OWNER"),
        "aprobador": "DIRECTOR_LOGISTICA",
    },
    "dir_finanzas": {
        "nombre": "Dirección Finanzas",
        "accion_default": "despido",
        "keys": ("DIRECTOR_FINANCIERO", "OWNER", "CO_OWNER"),
        "aprobador": "DIRECTOR_FINANCIERO",
    },
    "dir_docencia": {
        "nombre": "Dirección Docencia",
        "accion_default": "despido",
        "keys": ("DIRECTOR_DOCENCIA", "OWNER", "CO_OWNER"),
        "aprobador": "DIRECTOR_DOCENCIA",
    },
}

# Solicitudes pendientes de aprobación para abrir expediente
_PENDIENTES: dict = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> dict:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_PATH):
        return {}
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _key(uid: int, tipo: str) -> str:
    return f"{uid}_{tipo}"


def abrir_exp(uid: int, tipo: str, limite: int, autor_id: int, accion: str, notas: str = "", plantilla: dict = None) -> dict:
    data = _load()
    exp = {
        "uid": uid,
        "tipo": tipo,
        "limite": max(1, min(20, int(limite))),
        "accion": accion,
        "autor_id": autor_id,
        "notas": (notas or "")[:500],
        "plantilla": plantilla or {},
        "abierto": True,
        "fecha_apertura": _now(),
        "sanciones": [],
        "accion_pendiente": False,
        "accion_ejecutada": False,
    }
    data[_key(uid, tipo)] = exp
    _save(data)
    return exp


def get_exp(uid: int, tipo: str) -> Optional[dict]:
    return _load().get(_key(uid, tipo))


def add_sancion(uid: int, tipo: str, motivo: str, autor_id: int) -> dict:
    data = _load()
    k = _key(uid, tipo)
    exp = data.get(k)
    if not exp or not exp.get("abierto"):
        raise ValueError("No hay expediente abierto de ese tipo.")
    exp["sanciones"].append({"fecha": _now(), "motivo": motivo[:500], "autor_id": autor_id})
    if len(exp["sanciones"]) >= int(exp.get("limite") or 5):
        exp["accion_pendiente"] = True
    data[k] = exp
    _save(data)
    return exp


def marcar_ejecutada(uid: int, tipo: str) -> None:
    data = _load()
    k = _key(uid, tipo)
    if k in data:
        data[k]["accion_pendiente"] = False
        data[k]["accion_ejecutada"] = True
        data[k]["abierto"] = False
        data[k]["fecha_cierre"] = _now()
        _save(data)


def _es_director(member: discord.Member) -> bool:
    try:
        import permisos
        import config
        if permisos.member_tiene_alguna_key(member, "DIRECTOR"):
            return True
        keys = permisos.keys_del_member(member)
        return any(k.startswith("DIRECTOR") for k in keys)
    except Exception:
        return any("director" in (r.name or "").lower() for r in member.roles)


def embed_plantilla(
    solicitante: discord.Member,
    afectados: Sequence[discord.Member],
    tipo_nombre: str,
    hechos: str,
    normas: str,
    evidencias: str,
    antecedentes: str,
    medida: str,
    observaciones: str,
    limite: int,
    accion: str,
    estado: str = "⏳ Pendiente de autorización",
) -> discord.Embed:
    emb = discord.Embed(
        title=f"📋 Solicitud de expediente — {tipo_nombre}",
        description="Plantilla formal de apertura de expediente.",
        color=0xF39C12 if "Pendiente" in estado else 0x2ECC71,
    )
    emb.add_field(name="1. Solicitante", value=solicitante.mention, inline=True)
    emb.add_field(
        name="2. Personal involucrado",
        value=", ".join(m.mention for m in afectados) or "—",
        inline=True,
    )
    emb.add_field(name="3. Tipo", value=tipo_nombre, inline=True)
    emb.add_field(name="4. Hechos / descripción", value=(hechos or "—")[:1020], inline=False)
    emb.add_field(name="5. Normas / políticas incumplidas", value=(normas or "—")[:1020], inline=False)
    emb.add_field(name="6. Evidencias / anexos", value=(evidencias or "—")[:1020], inline=False)
    emb.add_field(name="7. Antecedentes", value=(antecedentes or "Sin antecedentes indicados")[:1020], inline=False)
    emb.add_field(name="8. Medida / acción al límite", value=f"`{accion}` · límite **{limite}** sanciones", inline=False)
    if observaciones:
        emb.add_field(name="9. Observaciones", value=observaciones[:1020], inline=False)
    emb.add_field(name="Estado", value=estado, inline=False)
    emb.set_footer(text="Requiere autorización del director de la sección correspondiente.")
    return emb


def embed_exp(usuario: discord.Member, exp: dict) -> discord.Embed:
    info = TIPOS.get(exp.get("tipo") or "", {})
    nombre = info.get("nombre", exp.get("tipo", "?"))
    s = exp.get("sanciones") or []
    lim = int(exp.get("limite") or 5)
    accion = exp.get("accion") or "despido"
    p = exp.get("plantilla") or {}
    emb = discord.Embed(
        title=f"📁 Expediente {nombre} · {usuario.display_name}",
        description=exp.get("notas") or p.get("hechos") or "_Sin notas_",
        color=0xE74C3C if exp.get("accion_pendiente") else (0x2ECC71 if exp.get("abierto") else 0x95A5A6),
    )
    emb.add_field(name="Estado", value="🟢 Abierto" if exp.get("abierto") else "🔒 Cerrado", inline=True)
    emb.add_field(name="Sanciones", value=f"**{len(s)} / {lim}**", inline=True)
    emb.add_field(name="Acción al límite", value=accion, inline=True)
    if p.get("normas"):
        emb.add_field(name="Normas", value=str(p["normas"])[:500], inline=False)
    if p.get("evidencias"):
        emb.add_field(name="Evidencias", value=str(p["evidencias"])[:500], inline=False)
    if p.get("antecedentes"):
        emb.add_field(name="Antecedentes", value=str(p["antecedentes"])[:400], inline=False)
    if s:
        lineas = [f"`{str(x.get('fecha',''))[:10]}` {x.get('motivo','—')[:80]}" for x in s[-8:]]
        emb.add_field(name="Últimas sanciones", value="\n".join(lineas), inline=False)
    if exp.get("accion_pendiente"):
        emb.add_field(name="⚠️ LÍMITE ALCANZADO", value="Confirma la acción con el botón.", inline=False)
    emb.set_footer(text=f"Abierto por ID {exp.get('autor_id')} · {str(exp.get('fecha_apertura',''))[:16]}")
    return emb


async def _safe_reply(inter: discord.Interaction, content: str = None, *, embed=None, embeds=None, ephemeral=True, view=None):
    try:
        kwargs = dict(content=content, ephemeral=ephemeral, view=view)
        if embeds:
            kwargs["embeds"] = embeds[:10]
        elif embed:
            kwargs["embed"] = embed
        if inter.response.is_done():
            await inter.followup.send(**kwargs)
        else:
            await inter.response.send_message(**kwargs)
    except discord.NotFound:
        print("[expedientes] interaccion expirada")
    except Exception as e:
        print(f"[expedientes] safe_reply: {e}")


def _uniq_members(*members: Optional[discord.Member]) -> List[discord.Member]:
    seen = set()
    out: List[discord.Member] = []
    for m in members:
        if m is None or not isinstance(m, discord.Member):
            continue
        if m.id in seen:
            continue
        seen.add(m.id)
        out.append(m)
    return out


def _aprobadores_para(targets: Sequence[discord.Member], tipo_key: str) -> Tuple[List[str], List[int]]:
    """
    Devuelve (keys_aprobadoras, ids_bloqueados).
    Si algún afectado es director → DG + RRHH + Disciplina (él no puede aprobar).
    Si no → director de la sección del tipo.
    RRHH y Disciplina son independientes del DG.
    """
    info = TIPOS[tipo_key]
    bloqueados = [m.id for m in targets if _es_director(m)]
    if bloqueados:
        keys = list(_APROBADORES_CONTRA_DIRECTOR)
        # Si el tipo es disciplinario o RRHH, priorizar esa entidad (sigue en la lista)
        return keys, bloqueados
    # Sección normal: director de esa área + OWNER/CO_OWNER
    keys = [info["aprobador"], "OWNER", "CO_OWNER"]
    # Tipos independientes: no exigir DG
    return keys, []


class AprobacionExpedienteView(discord.ui.View):
    def __init__(self, solicitud_id: str, keys_ok: List[str], bloqueados: List[int]):
        super().__init__(timeout=86400)
        self.solicitud_id = solicitud_id
        self.keys_ok = keys_ok
        self.bloqueados = set(bloqueados)

    async def _puede(self, inter: discord.Interaction) -> bool:
        if not isinstance(inter.user, discord.Member):
            await _safe_reply(inter, "❌ Solo en servidor.")
            return False
        if inter.user.id in self.bloqueados:
            await _safe_reply(
                inter,
                "❌ Eres parte involucrada (director citado). "
                "Deben autorizar: **Director General**, **Director de RRHH** o **Director de Disciplina**.",
            )
            return False
        try:
            import permisos
            if permisos.member_tiene_alguna_key(inter.user, *self.keys_ok):
                return True
        except Exception:
            pass
        await _safe_reply(
            inter,
            f"❌ Sin permiso para autorizar.\nSe requiere una de: {', '.join(self.keys_ok)}",
        )
        return False

    @discord.ui.button(label="✅ Autorizar apertura", style=discord.ButtonStyle.success)
    async def autorizar(self, inter: discord.Interaction, btn: discord.ui.Button):
        if not await self._puede(inter):
            return
        data = _PENDIENTES.pop(self.solicitud_id, None)
        if not data:
            return await _safe_reply(inter, "Esta solicitud ya fue resuelta.")

        for c in self.children:
            c.disabled = True
        try:
            await inter.response.edit_message(view=self)
        except Exception:
            try:
                await inter.response.defer()
            except Exception:
                pass

        guild = inter.guild
        embeds = []
        menciones = []
        for uid in data["uids"]:
            member = guild.get_member(uid) if guild else None
            # Member mínimo para embed
            if not member and guild:
                try:
                    member = await guild.fetch_member(uid)
                except Exception:
                    member = None
            if not member:
                # Crear stub embed
                emb = discord.Embed(title=f"📁 Expediente abierto (ID {uid})", color=0x2ECC71)
                embeds.append(emb)
                menciones.append(f"<@{uid}>")
                abrir_exp(
                    uid, data["tipo"], data["limite"], data["autor_id"],
                    data["accion"], data.get("notas", ""), data.get("plantilla"),
                )
                continue
            exp = abrir_exp(
                member.id, data["tipo"], data["limite"], data["autor_id"],
                data["accion"], data.get("notas", ""), data.get("plantilla"),
            )
            emb = embed_exp(member, exp)
            emb.description = (
                f"**Autorizado por** {inter.user.mention}.\n"
                f"Límite **{data['limite']}** → `{data['accion']}`"
            )
            embeds.append(emb)
            menciones.append(member.mention)

        nombre = TIPOS.get(data["tipo"], {}).get("nombre", data["tipo"])
        try:
            await inter.followup.send(
                content=f"✅ Expediente **{nombre}** **AUTORIZADO** y abierto para: {', '.join(menciones)}",
                embeds=embeds[:10],
            )
        except Exception:
            await _safe_reply(
                inter,
                content=f"✅ Expediente **{nombre}** autorizado para: {', '.join(menciones)}",
                embeds=embeds[:10],
                ephemeral=False,
            )

        # Actualizar embed original
        try:
            if inter.message and inter.message.embeds:
                emb0 = inter.message.embeds[0]
                emb0.color = discord.Colour.green()
                # reemplazar campo Estado
                for i, f in enumerate(emb0.fields):
                    if f.name == "Estado":
                        emb0.set_field_at(
                            i, name="Estado",
                            value=f"✅ **AUTORIZADO** por {inter.user.mention}",
                            inline=False,
                        )
                        break
                await inter.message.edit(embed=emb0, view=self)
        except Exception:
            pass

    @discord.ui.button(label="❌ Negar", style=discord.ButtonStyle.danger)
    async def negar(self, inter: discord.Interaction, btn: discord.ui.Button):
        if not await self._puede(inter):
            return
        _PENDIENTES.pop(self.solicitud_id, None)
        for c in self.children:
            c.disabled = True
        try:
            if inter.message and inter.message.embeds:
                emb0 = inter.message.embeds[0]
                emb0.color = discord.Colour.red()
                for i, f in enumerate(emb0.fields):
                    if f.name == "Estado":
                        emb0.set_field_at(
                            i, name="Estado",
                            value=f"❌ **NEGADO** por {inter.user.mention}",
                            inline=False,
                        )
                        break
                await inter.response.edit_message(embed=emb0, view=self)
            else:
                await inter.response.edit_message(view=self)
        except Exception:
            await _safe_reply(inter, f"❌ Solicitud negada por {inter.user.mention}.")


class ConfirmarAccionView(discord.ui.View):
    def __init__(self, uid: int, tipo: str, accion: str, director_id: int):
        super().__init__(timeout=86400)
        self.uid = uid
        self.tipo = tipo
        self.accion = accion
        self.director_id = director_id

    async def interaction_check(self, inter: discord.Interaction) -> bool:
        if inter.user.id != self.director_id:
            try:
                import permisos
                if permisos.member_tiene_alguna_key(inter.user, "OWNER", "CO_OWNER"):
                    return True
            except Exception:
                pass
            await _safe_reply(inter, "❌ Solo el director a cargo puede confirmar.")
            return False
        return True

    @discord.ui.button(label="✅ Confirmar acción", style=discord.ButtonStyle.danger)
    async def confirmar(self, inter: discord.Interaction, btn: discord.ui.Button):
        guild = inter.guild
        if not guild:
            return await _safe_reply(inter, "❌ Solo en servidor.")
        member = guild.get_member(self.uid)
        try:
            if not inter.response.is_done():
                await inter.response.defer()
        except Exception:
            pass
        resultado = []
        if self.accion == "mute_24h":
            if member:
                try:
                    until = datetime.now(timezone.utc) + timedelta(hours=24)
                    await member.timeout(until, reason=f"Expediente disciplinario al límite (por {inter.user})")
                    resultado.append(f"🔇 Mute 24h a {member.mention}")
                except Exception as e:
                    resultado.append(f"⚠️ Mute falló: `{e}`")
            else:
                resultado.append("⚠️ Usuario no en el servidor.")
        else:
            if member:
                quitados = []
                for r in list(member.roles):
                    if r.is_default() or r.managed or r >= guild.me.top_role:
                        continue
                    n = (r.name or "").lower()
                    if any(x in n for x in ("director", "jefe", "supervisor", "staff", "médico", "medico", "enfermer", "rrhh", "seguridad", "logíst", "logist", "finan", "docen", "residente", "pasante", "voluntario", "encargado")):
                        try:
                            await member.remove_roles(r, reason=f"Despido por expediente ({inter.user})")
                            quitados.append(r.name)
                        except Exception:
                            pass
                resultado.append(
                    f"🚫 Despido: roles quitados → {', '.join(quitados[:15])}" if quitados
                    else "🚫 Despido registrado (revisa roles manualmente)."
                )
            else:
                resultado.append("🚫 Despido registrado (usuario ausente).")

        marcar_ejecutada(self.uid, self.tipo)
        for c in self.children:
            c.disabled = True
        try:
            await inter.message.edit(view=self)
        except Exception:
            pass
        await inter.followup.send("✅ **Acción ejecutada.**\n" + "\n".join(resultado))

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
    async def cancelar(self, inter: discord.Interaction, btn: discord.ui.Button):
        data = _load()
        k = _key(self.uid, self.tipo)
        if k in data:
            data[k]["accion_pendiente"] = False
            _save(data)
        for c in self.children:
            c.disabled = True
        try:
            if not inter.response.is_done():
                await inter.response.edit_message(view=self)
            else:
                await inter.message.edit(view=self)
        except Exception:
            pass
        await _safe_reply(inter, "Acción cancelada.")


async def _avisar_limite(usuario: discord.Member, exp: dict, director: discord.Member):
    accion = exp.get("accion") or "despido"
    tipo = exp.get("tipo") or ""
    nombre = TIPOS.get(tipo, {}).get("nombre", tipo)
    emb = discord.Embed(
        title="⚠️ Límite de sanciones alcanzado",
        description=(
            f"**Usuario:** {usuario.mention}\n"
            f"**Expediente:** {nombre}\n"
            f"**Sanciones:** {len(exp.get('sanciones') or [])} / {exp.get('limite')}\n"
            f"**Acción:** `{accion}`\n\n"
            f"Confirma para ejecutar."
        ),
        color=0xE74C3C,
    )
    view = ConfirmarAccionView(usuario.id, tipo, accion, director.id)
    try:
        await director.send(embed=emb, view=view)
    except Exception:
        pass
    return emb, view


def registrar(bot: commands.Bot) -> None:
    print("[expedientes] cargando…")
    try:
        _reg(bot)
        print("[expedientes] ✓ OK")
    except Exception:
        print("[expedientes] ✗ error (bot sigue):")
        traceback.print_exc()


def _reg(bot: commands.Bot) -> None:
    import permisos
    import roles_store

    for n in ("mi_expediente", "expediente", "abrir_expediente"):
        try:
            bot.tree.remove_command(n)
        except Exception:
            pass

    TIPO_CHOICES = [app_commands.Choice(name=v["nombre"], value=k) for k, v in TIPOS.items()]
    ACCION_CMD = [
        app_commands.Choice(name="📂 Solicitar apertura (plantilla + autorización)", value="abrir"),
        app_commands.Choice(name="➕ Agregar sanción", value="sancion"),
        app_commands.Choice(name="👁️ Ver expediente", value="ver"),
    ]
    ACCION_LIMITE = [
        app_commands.Choice(name="Despido al límite", value="despido"),
        app_commands.Choice(name="Mute 24h al límite", value="mute_24h"),
    ]

    @bot.tree.command(
        name="abrir_expediente",
        description="Expediente formal: plantilla por puntos + autorización del director de sección",
    )
    @app_commands.describe(
        accion="Qué hacer",
        tipo="Tipo / sección del expediente",
        hechos="4. Hechos / descripción de lo ocurrido",
        normas="5. Normas o políticas incumplidas",
        evidencias="6. Evidencias (links, testigos, capturas)",
        usuario="Persona 1",
        usuario2="Persona 2 (opcional)",
        usuario3="Persona 3 (opcional)",
        usuario4="Persona 4 (opcional)",
        usuario5="Persona 5 (opcional)",
        antecedentes="7. Antecedentes (opcional)",
        observaciones="9. Observaciones (opcional)",
        limite_sanciones="Al abrir: límite de sanciones (default 5)",
        accion_al_limite="Medida al llegar al límite",
        motivo="Solo para Agregar sanción",
    )
    @app_commands.choices(accion=ACCION_CMD, tipo=TIPO_CHOICES, accion_al_limite=ACCION_LIMITE)
    async def abrir_expediente(
        inter: discord.Interaction,
        accion: app_commands.Choice[str],
        tipo: app_commands.Choice[str],
        hechos: str = "",
        normas: str = "",
        evidencias: str = "",
        usuario: Optional[discord.Member] = None,
        usuario2: Optional[discord.Member] = None,
        usuario3: Optional[discord.Member] = None,
        usuario4: Optional[discord.Member] = None,
        usuario5: Optional[discord.Member] = None,
        antecedentes: str = "",
        observaciones: str = "",
        limite_sanciones: app_commands.Range[int, 1, 20] = 5,
        accion_al_limite: Optional[app_commands.Choice[str]] = None,
        motivo: str = "",
    ):
        try:
            if not isinstance(inter.user, discord.Member) or not inter.guild:
                return await _safe_reply(inter, "❌ Solo usable en el servidor.")

            t = tipo.value
            info = TIPOS.get(t)
            if not info:
                return await _safe_reply(inter, "❌ Tipo inválido.")

            act = accion.value
            targets = _uniq_members(usuario, usuario2, usuario3, usuario4, usuario5)

            # ——— VER ———
            if act == "ver":
                if not targets:
                    targets = [inter.user]
                for target in targets:
                    if target.id != inter.user.id:
                        if not permisos.member_tiene_alguna_key(
                            inter.user, *info["keys"], "DIRECTOR", "OWNER", "CO_OWNER"
                        ):
                            return await _safe_reply(
                                inter,
                                f"❌ Sin permiso. Se requiere: {', '.join(info['keys'])}",
                            )
                        break
                embeds = []
                faltan = []
                for target in targets:
                    exp = get_exp(target.id, t)
                    if not exp:
                        faltan.append(target.mention)
                    else:
                        embeds.append(embed_exp(target, exp))
                if not embeds:
                    return await _safe_reply(
                        inter,
                        f"No hay expediente **{info['nombre']}** para: {', '.join(faltan) or 'nadie'}.",
                    )
                msg = f"Sin expediente: {', '.join(faltan)}" if faltan else None
                return await _safe_reply(inter, content=msg, embeds=embeds)

            # Solicitar apertura o sanción: quien pide debe tener key de sección o superior
            keys_pedir = info["keys"] + ("DIRECTOR",)
            if not permisos.member_tiene_alguna_key(inter.user, *keys_pedir):
                return await _safe_reply(
                    inter,
                    f"❌ Sin permiso.\nSe requiere una de: {', '.join(info['keys'])}",
                )

            if not targets:
                return await _safe_reply(
                    inter,
                    "❌ Indica al menos un **usuario** (usuario … usuario5).",
                )

            # ——— ABRIR (plantilla + autorización) ———
            if act == "abrir":
                if not (hechos or "").strip():
                    return await _safe_reply(inter, "❌ Completa el punto **4. Hechos / descripción**.")
                if not (normas or "").strip():
                    return await _safe_reply(inter, "❌ Completa el punto **5. Normas incumplidas**.")

                acc = (accion_al_limite.value if accion_al_limite else None) or info["accion_default"]
                if t == "disciplinario" and accion_al_limite is None:
                    acc = "mute_24h"

                plantilla = {
                    "hechos": hechos.strip()[:1500],
                    "normas": normas.strip()[:1500],
                    "evidencias": (evidencias or "").strip()[:1500],
                    "antecedentes": (antecedentes or "").strip()[:1000],
                    "observaciones": (observaciones or "").strip()[:1000],
                }

                keys_apr, bloqueados = _aprobadores_para(targets, t)
                sid = f"exp_{inter.user.id}_{int(datetime.now(timezone.utc).timestamp())}"
                _PENDIENTES[sid] = {
                    "tipo": t,
                    "uids": [m.id for m in targets],
                    "limite": limite_sanciones,
                    "accion": acc,
                    "autor_id": inter.user.id,
                    "notas": observaciones or hechos[:200],
                    "plantilla": plantilla,
                }

                emb = embed_plantilla(
                    inter.user, targets, info["nombre"],
                    plantilla["hechos"], plantilla["normas"], plantilla["evidencias"],
                    plantilla["antecedentes"], acc, plantilla["observaciones"],
                    limite_sanciones, acc,
                    estado="⏳ Pendiente de autorización del director de sección",
                )
                if bloqueados:
                    emb.add_field(
                        name="⚖️ Caso contra director(es)",
                        value=(
                            "El director citado **no puede** aprobar ni negar.\n"
                            "Autorizan: **Director General**, **RRHH** o **Disciplina** "
                            "(RRHH y Disciplina son independientes del DG)."
                        ),
                        inline=False,
                    )
                else:
                    emb.add_field(
                        name="🔐 Autoriza",
                        value=f"Director de sección: `{info['aprobador']}` (o OWNER/CO_OWNER)",
                        inline=False,
                    )

                view = AprobacionExpedienteView(sid, keys_apr, bloqueados)

                # Mencionar roles aprobadores
                menciones = []
                for k in keys_apr:
                    if k in ("OWNER", "CO_OWNER"):
                        continue
                    rid = roles_store.obtener_id_key(k)
                    if rid:
                        rol = inter.guild.get_role(rid)
                        if rol:
                            menciones.append(rol.mention)

                await _safe_reply(
                    inter,
                    content=(
                        f"📋 Solicitud de expediente enviada.\n"
                        f"Autorizan: {' '.join(menciones) or ', '.join(keys_apr)}"
                    ),
                    embed=emb,
                    view=view,
                    ephemeral=False,
                )
                return

            # ——— SANCIÓN ———
            if act == "sancion":
                if not (motivo or "").strip():
                    return await _safe_reply(inter, "❌ Escribe el **motivo** de la sanción.")
                embeds = []
                errores = []
                pendientes = []
                for u in targets:
                    try:
                        exp = add_sancion(u.id, t, motivo.strip(), inter.user.id)
                        embeds.append(embed_exp(u, exp))
                        if exp.get("accion_pendiente") and not exp.get("accion_ejecutada"):
                            pendientes.append((u, exp))
                    except ValueError as e:
                        errores.append(f"{u.mention}: {e}")

                if not embeds and errores:
                    return await _safe_reply(
                        inter,
                        "❌ No se pudo sancionar:\n" + "\n".join(errores)
                        + "\nPrimero **Solicitar apertura** y espera autorización.",
                    )

                extra = ("\n" + "\n".join(errores)) if errores else ""
                await _safe_reply(
                    inter,
                    content=f"✅ Sanción registrada.{extra}" if extra else None,
                    embeds=embeds or None,
                    ephemeral=False,
                )
                for u, exp in pendientes:
                    emb2, view = await _avisar_limite(u, exp, inter.user)
                    try:
                        await inter.followup.send(
                            content=f"⚠️ **Límite** {u.mention} ({len(exp['sanciones'])}/{exp['limite']}). Confirma:",
                            embed=emb2,
                            view=view,
                        )
                    except Exception as e:
                        print("[expedientes] followup limite:", e)
                return

            await _safe_reply(inter, "❌ Acción no reconocida.")
        except Exception as e:
            traceback.print_exc()
            await _safe_reply(inter, f"❌ Error: `{e}`")
