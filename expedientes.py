# -*- coding: utf-8 -*
"""
expedientes.py — /abrir_expediente (varios usuarios a la vez).
"""
from __future__ import annotations

import json
import os
import traceback
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import discord
from discord import app_commands
from discord.ext import commands

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "expedientes_tipo.json")

TIPOS = {
    "administrativo": {"nombre": "Administrativo", "accion_default": "despido", "keys": ("DIRECTOR_ADMINISTRATIVO", "OWNER", "CO_OWNER")},
    "disciplinario": {"nombre": "Disciplinario", "accion_default": "mute_24h", "keys": ("DIRECTOR_DISCIPLINA", "OWNER", "CO_OWNER")},
    "investigacion_rrhh": {"nombre": "Investigación RRHH", "accion_default": "despido", "keys": ("DIRECTOR_RRHH", "OWNER", "CO_OWNER")},
    "dir_medico": {"nombre": "Dirección Médica", "accion_default": "despido", "keys": ("DIRECTOR_MEDICO", "OWNER", "CO_OWNER")},
    "dir_enfermeria": {"nombre": "Dirección Enfermería", "accion_default": "despido", "keys": ("DIRECTOR_ENFERMERIA", "OWNER", "CO_OWNER")},
    "dir_seguridad": {"nombre": "Dirección Seguridad", "accion_default": "despido", "keys": ("DIRECTOR_SEGURIDAD", "OWNER", "CO_OWNER")},
    "dir_logistica": {"nombre": "Dirección Logística", "accion_default": "despido", "keys": ("DIRECTOR_LOGISTICA", "OWNER", "CO_OWNER")},
    "dir_finanzas": {"nombre": "Dirección Finanzas", "accion_default": "despido", "keys": ("DIRECTOR_FINANCIERO", "OWNER", "CO_OWNER")},
    "dir_docencia": {"nombre": "Dirección Docencia", "accion_default": "despido", "keys": ("DIRECTOR_DOCENCIA", "OWNER", "CO_OWNER")},
}


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


def abrir_exp(uid: int, tipo: str, limite: int, autor_id: int, accion: str, notas: str = "") -> dict:
    data = _load()
    exp = {
        "uid": uid,
        "tipo": tipo,
        "limite": max(1, min(20, int(limite))),
        "accion": accion,
        "autor_id": autor_id,
        "notas": (notas or "")[:500],
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


def embed_exp(usuario: discord.Member, exp: dict) -> discord.Embed:
    info = TIPOS.get(exp.get("tipo") or "", {})
    nombre = info.get("nombre", exp.get("tipo", "?"))
    s = exp.get("sanciones") or []
    lim = int(exp.get("limite") or 5)
    accion = exp.get("accion") or "despido"
    emb = discord.Embed(
        title=f"📁 Expediente {nombre} · {usuario.display_name}",
        description=exp.get("notas") or "_Sin notas_",
        color=0xE74C3C if exp.get("accion_pendiente") else (0x2ECC71 if exp.get("abierto") else 0x95A5A6),
    )
    emb.add_field(name="Estado", value="🟢 Abierto" if exp.get("abierto") else "🔒 Cerrado", inline=True)
    emb.add_field(name="Sanciones", value=f"**{len(s)} / {lim}**", inline=True)
    emb.add_field(name="Acción al límite", value=accion, inline=True)
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
        print("[expedientes] ✓ OK (1 comando: abrir_expediente)")
    except Exception:
        print("[expedientes] ✗ error (bot sigue):")
        traceback.print_exc()


def _reg(bot: commands.Bot) -> None:
    import permisos

    for n in ("mi_expediente", "expediente", "abrir_expediente", "agregar_sancion_expediente", "ver_expediente_tipo"):
        try:
            bot.tree.remove_command(n)
        except Exception:
            pass

    TIPO_CHOICES = [app_commands.Choice(name=v["nombre"], value=k) for k, v in TIPOS.items()]
    ACCION_CMD = [
        app_commands.Choice(name="📂 Abrir expediente", value="abrir"),
        app_commands.Choice(name="➕ Agregar sanción", value="sancion"),
        app_commands.Choice(name="👁️ Ver expediente", value="ver"),
    ]
    ACCION_LIMITE = [
        app_commands.Choice(name="Despido al límite", value="despido"),
        app_commands.Choice(name="Mute 24h al límite", value="mute_24h"),
    ]

    @bot.tree.command(
        name="abrir_expediente",
        description="Expediente: abrir / sanción / ver (varios usuarios a la vez)",
    )
    @app_commands.describe(
        accion="Qué hacer",
        tipo="Tipo de expediente",
        usuario="Persona 1",
        usuario2="Persona 2 (opcional)",
        usuario3="Persona 3 (opcional)",
        usuario4="Persona 4 (opcional)",
        usuario5="Persona 5 (opcional)",
        limite_sanciones="Al abrir: límite (default 5)",
        accion_al_limite="Al abrir: despido o mute 24h",
        motivo="Al agregar sanción: motivo (igual para todos)",
        notas="Al abrir: notas opcionales",
    )
    @app_commands.choices(accion=ACCION_CMD, tipo=TIPO_CHOICES, accion_al_limite=ACCION_LIMITE)
    async def abrir_expediente(
        inter: discord.Interaction,
        accion: app_commands.Choice[str],
        tipo: app_commands.Choice[str],
        usuario: Optional[discord.Member] = None,
        usuario2: Optional[discord.Member] = None,
        usuario3: Optional[discord.Member] = None,
        usuario4: Optional[discord.Member] = None,
        usuario5: Optional[discord.Member] = None,
        limite_sanciones: app_commands.Range[int, 1, 20] = 5,
        accion_al_limite: Optional[app_commands.Choice[str]] = None,
        motivo: str = "",
        notas: str = "",
    ):
        try:
            if not isinstance(inter.user, discord.Member):
                return await _safe_reply(inter, "❌ Solo usable en el servidor.")

            t = tipo.value
            info = TIPOS.get(t)
            if not info:
                return await _safe_reply(inter, "❌ Tipo de expediente inválido.")

            act = accion.value
            targets = _uniq_members(usuario, usuario2, usuario3, usuario4, usuario5)

            # --- VER ---
            if act == "ver":
                if not targets:
                    targets = [inter.user]
                # Ver varios: permiso si alguno no es uno mismo
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
                msg = None
                if faltan:
                    msg = f"Sin expediente: {', '.join(faltan)}"
                return await _safe_reply(inter, content=msg, embeds=embeds)

            keys_ok = info["keys"] + ("DIRECTOR",)
            if not permisos.member_tiene_alguna_key(inter.user, *keys_ok):
                return await _safe_reply(
                    inter,
                    f"❌ Sin permiso para este tipo.\nSe requiere una de: {', '.join(info['keys'])}",
                )

            if not targets:
                return await _safe_reply(
                    inter,
                    "❌ Indica al menos un **usuario** (puedes usar usuario, usuario2, usuario3… hasta 5).",
                )

            # --- ABRIR (varios) ---
            if act == "abrir":
                acc = (accion_al_limite.value if accion_al_limite else None) or info["accion_default"]
                if t == "disciplinario" and accion_al_limite is None:
                    acc = "mute_24h"
                embeds = []
                menciones = []
                for u in targets:
                    exp = abrir_exp(u.id, t, limite_sanciones, inter.user.id, acc, notas)
                    emb = embed_exp(u, exp)
                    emb.description = (
                        f"Abierto por {inter.user.mention}.\n"
                        f"Límite **{limite_sanciones}** → `{acc}` (con confirmación)."
                    )
                    embeds.append(emb)
                    menciones.append(u.mention)
                return await _safe_reply(
                    inter,
                    content=f"✅ Expediente **{info['nombre']}** abierto a: {', '.join(menciones)}",
                    embeds=embeds,
                    ephemeral=False,
                )

            # --- SANCIÓN (varios, mismo motivo) ---
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
                        + "\nAbre primero con **Abrir expediente**.",
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
            await _safe_reply(inter, f"❌ Error al procesar: `{e}`")
