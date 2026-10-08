# -*- coding: utf-8 -*-
"""
Paneles de autoridad del Hospital General.
- Fundador: Mando General (morado)
- Co-Fundador Gobernanza: Orden y Legitimidad (azul)
- Co-Fundador Interinstitucional: Puentes y Alianzas (verde)
- Co-Fundador Calidad: Excelencia y Seguridad (coral)

/enviar_panel_mando — solo Fundador
No modifica comandos existentes; módulo aditivo.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Callable, List, Optional, Sequence

import discord
from discord import app_commands, ui
from discord.ext import commands

import mando_store as store

try:
    from roles_cofundadores import (
        member_es_cofundador,
        member_es_fundador,
    )
except Exception:

    def member_es_fundador(m: discord.Member) -> bool:
        return bool(m.guild and m.id == m.guild.owner_id)

    def member_es_cofundador(m: discord.Member, zona: str | None = None) -> bool:
        return False


# ── Colores oficiales ──────────────────────────────────────────
C_FUNDADOR = 0x9B59B6
C_GOB = 0x3498DB
C_INT = 0x1ABC9C
C_CAL = 0xE67E22
C_OK = 0x2ECC71
C_ERR = 0xE74C3C
C_WARN = 0xF1C40F


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")


def _banner_emergencia(guild_id: int) -> str:
    em = store.emergencia_activa(guild_id)
    if not em:
        return ""
    return (
        f"\n\n🚨 **EMERGENCIA ACTIVA** · {em.get('tipo', '—')}\n"
        f"{em.get('descripcion', '')[:200]}\n"
    )


async def _aviso_usuario(bot: commands.Bot, user_id: int, embed: discord.Embed) -> None:
    try:
        u = bot.get_user(user_id) or await bot.fetch_user(user_id)
        await u.send(embed=embed)
    except Exception:
        pass


def _check_fundador(inter: discord.Interaction) -> bool:
    return isinstance(inter.user, discord.Member) and member_es_fundador(inter.user)


def _check_zona(inter: discord.Interaction, zona: str) -> bool:
    if not isinstance(inter.user, discord.Member):
        return False
    if member_es_fundador(inter.user):
        return True
    return member_es_cofundador(inter.user, zona)


# ═══════════════════════════════════════════════════════════════
# Formularios genéricos
# ═══════════════════════════════════════════════════════════════


class ModalTexto(ui.Modal):
    def __init__(
        self,
        *,
        title: str,
        fields: List[tuple],  # (custom_id, label, required, style, max, placeholder)
        on_submit_cb: Callable,
    ):
        super().__init__(title=title[:45])
        self._cb = on_submit_cb
        self._inputs: List[ui.TextInput] = []
        for cid, label, req, style, mx, ph in fields[:5]:
            tin = ui.TextInput(
                label=label[:45],
                custom_id=cid,
                required=req,
                style=style,
                max_length=mx,
                placeholder=(ph or "")[:100],
            )
            self._inputs.append(tin)
            self.add_item(tin)

    async def on_submit(self, inter: discord.Interaction):
        try:
            await inter.response.defer(ephemeral=True)
        except Exception:
            pass
        valores = {t.custom_id: str(t.value).strip() for t in self._inputs}
        for t in self._inputs:
            if t.required and not valores.get(t.custom_id):
                return await inter.followup.send(
                    f"❌ Falta el campo **{t.label}**.", ephemeral=True
                )
        await self._cb(inter, valores)


# ═══════════════════════════════════════════════════════════════
# PANEL FUNDADOR — Mando General
# ═══════════════════════════════════════════════════════════════


def embed_fundador(guild: discord.Guild) -> discord.Embed:
    pend = store.listar_pendientes(guild.id)
    dels = store.listar_delegaciones(guild.id)
    em = store.emergencia_activa(guild.id)
    data = store.load()
    aud = [a for a in (data.get("auditoria") or []) if int(a.get("guild_id") or 0) == guild.id][
        :5
    ]
    lineas_aud = "\n".join(
        f"• `{a.get('accion')}` — {a.get('actor_name')} → {a.get('afectado')} ({a.get('resultado')})"
        for a in aud
    ) or "_Sin acciones recientes_"
    emb = discord.Embed(
        title="👑  Mando General · Fundador del Hospital",
        description=(
            f"**Decisiones pendientes:** {len(pend)}\n"
            f"**Delegaciones activas:** {len(dels)}\n"
            f"**Emergencia:** {'🚨 ACTIVA — ' + str(em.get('tipo')) if em else '🟢 Normal'}\n"
            f"**Semáforo zonas:** Gobernanza · Interinstitucional · Calidad\n"
            f"{_banner_emergencia(guild.id)}\n"
            f"**Últimas 5 acciones**\n{lineas_aud}"
        ),
        color=C_FUNDADOR,
    )
    emb.set_footer(text=f"Hospital General · {_ts()}")
    return emb


class FundadorCatSelect(ui.Select):
    def __init__(self):
        opts = [
            discord.SelectOption(label="Decisiones", value="decisiones", emoji="📋"),
            discord.SelectOption(label="Delegaciones", value="delegaciones", emoji="🔑"),
            discord.SelectOption(label="Autoridades", value="autoridades", emoji="👑"),
            discord.SelectOption(label="Consejo", value="consejo", emoji="🏛️"),
            discord.SelectOption(label="Emergencia", value="emergencia", emoji="🚨"),
            discord.SelectOption(label="Supervisión", value="supervision", emoji="👁️"),
            discord.SelectOption(label="Informes", value="informes", emoji="📊"),
        ]
        super().__init__(placeholder="Categoría del Mando General…", options=opts, row=0)

    async def callback(self, inter: discord.Interaction):
        if not _check_fundador(inter):
            return await inter.response.send_message(
                "❌ Solo el **Fundador del Hospital**.", ephemeral=True
            )
        cat = self.values[0]
        view = FundadorAccionesView(cat)
        await inter.response.send_message(
            embed=discord.Embed(
                title=f"Mando General · {cat.title()}",
                description="Elige una acción:",
                color=C_FUNDADOR,
            ),
            view=view,
            ephemeral=True,
        )


class FundadorAccionesView(ui.View):
    def __init__(self, categoria: str):
        super().__init__(timeout=180)
        self.categoria = categoria
        botones = {
            "decisiones": [
                ("✅ Aprobar", "apr", discord.ButtonStyle.success),
                ("⛔ Vetar", "vet", discord.ButtonStyle.danger),
                ("↩️ Devolver", "dev", discord.ButtonStyle.secondary),
                ("📋 Ver pendientes", "ver", discord.ButtonStyle.primary),
            ],
            "delegaciones": [
                ("🔑 Delegar poder", "del", discord.ButtonStyle.success),
                ("🚫 Revocar", "rev", discord.ButtonStyle.danger),
                ("📜 Ver activas", "vdel", discord.ButtonStyle.primary),
            ],
            "autoridades": [
                ("👑 Nombrar Co-Fundador", "nom", discord.ButtonStyle.success),
                ("⚠️ Destituir", "des", discord.ButtonStyle.danger),
                ("🔁 Reasignar zona", "rea", discord.ButtonStyle.primary),
            ],
            "consejo": [
                ("🏛️ Convocar consejo", "con", discord.ButtonStyle.primary),
                ("📢 Anuncio oficial", "anu", discord.ButtonStyle.success),
                ("🖋️ Sellar documento", "sel", discord.ButtonStyle.secondary),
            ],
            "emergencia": [
                ("🚨 Declarar emergencia", "eme", discord.ButtonStyle.danger),
                ("🟢 Cerrar emergencia", "cem", discord.ButtonStyle.success),
            ],
            "supervision": [
                ("👁️ Ver zona", "vzo", discord.ButtonStyle.primary),
                ("🔎 Auditoría total", "aud", discord.ButtonStyle.primary),
                ("↩️ Revertir acción", "revac", discord.ButtonStyle.danger),
                ("🎯 Fijar prioridades", "pri", discord.ButtonStyle.success),
            ],
            "informes": [
                ("📊 Informe ejecutivo", "inf", discord.ButtonStyle.primary),
            ],
        }
        for label, key, style in botones.get(categoria, []):
            self.add_item(_FundadorBtn(label, key, style, categoria))


class _FundadorBtn(ui.Button):
    def __init__(self, label: str, key: str, style: discord.ButtonStyle, cat: str):
        super().__init__(label=label, style=style)
        self.key = key
        self.cat = cat

    async def callback(self, inter: discord.Interaction):
        if not _check_fundador(inter):
            return await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
        assert inter.guild and isinstance(inter.user, discord.Member)
        gid = inter.guild.id
        uid = inter.user.id

        async def ok(msg: str):
            store.auditar(
                guild_id=gid,
                actor_id=uid,
                actor_name=str(inter.user),
                rol="Fundador",
                accion=f"{self.cat}:{self.key}",
                afectado=msg[:120],
                resultado="ok",
            )
            await inter.followup.send(
                embed=discord.Embed(description=f"✅ {msg}", color=C_OK),
                ephemeral=True,
            )

        # ── Decisiones ──
        if self.key == "ver":
            await inter.response.defer(ephemeral=True)
            pend = store.listar_pendientes(gid)
            if not pend:
                return await inter.followup.send("No hay decisiones pendientes.", ephemeral=True)
            txt = "\n".join(
                f"**{p['id']}** · {p.get('titulo')} (zona: {p.get('origen_zona')})"
                for p in pend[:15]
            )
            return await inter.followup.send(
                embed=discord.Embed(
                    title="📋 Decisiones pendientes",
                    description=txt,
                    color=C_FUNDADOR,
                ),
                ephemeral=True,
            )

        if self.key in ("apr", "vet", "dev"):

            async def _res(inter2: discord.Interaction, vals: dict):
                pid = vals.get("id", "")
                com = vals.get("comentario", "")
                estado = {"apr": "aprobado", "vet": "vetado", "dev": "devuelto"}[self.key]
                if self.key == "vet" and not com:
                    return await inter2.followup.send(
                        "❌ El motivo es obligatorio al vetar.", ephemeral=True
                    )
                it = store.actualizar_pendiente(pid, estado, com)
                if not it:
                    return await inter2.followup.send("❌ ID no encontrado.", ephemeral=True)
                store.auditar(
                    guild_id=gid,
                    actor_id=uid,
                    actor_name=str(inter.user),
                    rol="Fundador",
                    accion=f"decision:{estado}",
                    afectado=pid,
                    resultado="ok",
                )
                await _aviso_usuario(
                    inter2.client,  # type: ignore
                    int(it.get("origen_id") or 0),
                    discord.Embed(
                        title=f"Decisión {estado}",
                        description=f"**{it.get('titulo')}**\n{com or '—'}",
                        color=C_OK if estado == "aprobado" else C_ERR,
                    ),
                )
                await inter2.followup.send(
                    f"✅ Decisión **{pid}** → **{estado}**.", ephemeral=True
                )

            fields = [
                ("id", "ID de la decisión", True, discord.TextStyle.short, 20, "APR-XXXXXXXX"),
                (
                    "comentario",
                    "Comentario / motivo",
                    self.key == "vet",
                    discord.TextStyle.paragraph,
                    500,
                    "Opcional salvo veto",
                ),
            ]
            return await inter.response.send_modal(
                ModalTexto(
                    title={"apr": "Aprobar", "vet": "Vetar", "dev": "Devolver"}[self.key],
                    fields=fields,
                    on_submit_cb=_res,
                )
            )

        # ── Delegaciones ──
        if self.key == "vdel":
            await inter.response.defer(ephemeral=True)
            dels = store.listar_delegaciones(gid)
            if not dels:
                return await inter.followup.send("Sin delegaciones activas.", ephemeral=True)
            txt = "\n".join(
                f"• <@{d['user_id']}> · **{d.get('poder')}** · vence <t:{d.get('vence_ts')}:R>"
                for d in dels[:15]
            )
            return await inter.followup.send(
                embed=discord.Embed(title="📜 Delegaciones activas", description=txt, color=C_FUNDADOR),
                ephemeral=True,
            )

        if self.key == "del":

            async def _del(inter2: discord.Interaction, vals: dict):
                try:
                    tid = int(vals["user_id"].strip().replace("<@", "").replace(">", "").replace("!", ""))
                    horas = int(vals.get("horas") or "24")
                except Exception:
                    return await inter2.followup.send("❌ Usuario o horas inválidos.", ephemeral=True)
                poder = vals.get("poder") or "general"
                data = store.load()
                item = {
                    "id": store.nuevo_id("DEL"),
                    "guild_id": gid,
                    "user_id": tid,
                    "poder": poder,
                    "condiciones": vals.get("condiciones") or "",
                    "vence_ts": int(time.time()) + max(1, horas) * 3600,
                    "revocada": False,
                    "por": uid,
                }
                data.setdefault("delegaciones", []).insert(0, item)
                store.save(data)
                store.auditar(
                    guild_id=gid, actor_id=uid, actor_name=str(inter.user),
                    rol="Fundador", accion="delegar", afectado=str(tid), resultado="ok",
                )
                await _aviso_usuario(
                    inter2.client,  # type: ignore
                    tid,
                    discord.Embed(
                        title="🔑 Poder delegado",
                        description=f"**{poder}** por {horas}h.\n{vals.get('condiciones') or ''}",
                        color=C_FUNDADOR,
                    ),
                )
                await inter2.followup.send(f"✅ Delegado a <@{tid}> ({poder}, {horas}h).", ephemeral=True)

            return await inter.response.send_modal(
                ModalTexto(
                    title="Delegar poder",
                    fields=[
                        ("user_id", "ID o mención del Co-Fundador", True, discord.TextStyle.short, 30, "123…"),
                        ("poder", "Poder (ej. sanciones, convenios)", True, discord.TextStyle.short, 40, "general"),
                        ("horas", "Duración en horas", True, discord.TextStyle.short, 6, "24"),
                        ("condiciones", "Condiciones", False, discord.TextStyle.paragraph, 300, "Opcional"),
                    ],
                    on_submit_cb=_del,
                )
            )

        if self.key == "rev":

            async def _rev(inter2: discord.Interaction, vals: dict):
                did = vals.get("id", "")
                data = store.load()
                found = None
                for d in data.get("delegaciones") or []:
                    if d.get("id") == did:
                        d["revocada"] = True
                        d["motivo_revoca"] = vals.get("motivo") or ""
                        found = d
                        break
                if not found:
                    return await inter2.followup.send("❌ Delegación no encontrada.", ephemeral=True)
                store.save(data)
                store.auditar(
                    guild_id=gid, actor_id=uid, actor_name=str(inter.user),
                    rol="Fundador", accion="revocar_delegacion", afectado=did, resultado="ok",
                )
                await inter2.followup.send(f"✅ Delegación **{did}** revocada.", ephemeral=True)

            return await inter.response.send_modal(
                ModalTexto(
                    title="Revocar delegación",
                    fields=[
                        ("id", "ID de delegación", True, discord.TextStyle.short, 20, "DEL-…"),
                        ("motivo", "Motivo", True, discord.TextStyle.paragraph, 300, "…"),
                    ],
                    on_submit_cb=_rev,
                )
            )

        # ── Emergencia ──
        if self.key == "eme":

            async def _eme(inter2: discord.Interaction, vals: dict):
                data = store.load()
                data["emergencia"] = {
                    "guild_id": gid,
                    "activa": True,
                    "tipo": vals.get("tipo") or "General",
                    "descripcion": vals.get("descripcion") or "",
                    "alcance": vals.get("alcance") or "hospital",
                    "por": uid,
                    "ts": int(time.time()),
                }
                store.save(data)
                store.auditar(
                    guild_id=gid, actor_id=uid, actor_name=str(inter.user),
                    rol="Fundador", accion="emergencia_on", afectado=vals.get("tipo", ""), resultado="ok",
                )
                await inter2.followup.send(
                    embed=discord.Embed(
                        title="🚨 Emergencia declarada",
                        description=vals.get("descripcion") or "—",
                        color=C_ERR,
                    ),
                    ephemeral=True,
                )

            return await inter.response.send_modal(
                ModalTexto(
                    title="Declarar emergencia",
                    fields=[
                        ("tipo", "Tipo", True, discord.TextStyle.short, 40, "Operativa / Imagen / …"),
                        ("descripcion", "Descripción", True, discord.TextStyle.paragraph, 500, "…"),
                        ("alcance", "Alcance", False, discord.TextStyle.short, 40, "hospital"),
                    ],
                    on_submit_cb=_eme,
                )
            )

        if self.key == "cem":

            async def _cem(inter2: discord.Interaction, vals: dict):
                data = store.load()
                if data.get("emergencia"):
                    data["emergencia"]["activa"] = False
                    data["emergencia"]["cierre"] = vals.get("resumen") or ""
                    data["emergencia"]["cierre_ts"] = int(time.time())
                store.save(data)
                store.auditar(
                    guild_id=gid, actor_id=uid, actor_name=str(inter.user),
                    rol="Fundador", accion="emergencia_off", afectado="—", resultado="ok",
                )
                await inter2.followup.send("✅ Emergencia cerrada y archivada.", ephemeral=True)

            return await inter.response.send_modal(
                ModalTexto(
                    title="Cerrar emergencia",
                    fields=[("resumen", "Resumen de cierre", True, discord.TextStyle.paragraph, 500, "…")],
                    on_submit_cb=_cem,
                )
            )

        # ── Auditoría / informe ──
        if self.key == "aud":
            await inter.response.defer(ephemeral=True)
            data = store.load()
            aud = [a for a in (data.get("auditoria") or []) if int(a.get("guild_id") or 0) == gid][:20]
            txt = "\n".join(
                f"`{a.get('id')}` {a.get('accion')} · {a.get('actor_name')} · {a.get('resultado')}"
                for a in aud
            ) or "_Vacío_"
            return await inter.followup.send(
                embed=discord.Embed(title="🔎 Auditoría", description=txt[:3900], color=C_FUNDADOR),
                ephemeral=True,
            )

        if self.key == "inf":
            await inter.response.defer(ephemeral=True)
            pend = len(store.listar_pendientes(gid))
            dels = len(store.listar_delegaciones(gid))
            em = store.emergencia_activa(gid)
            return await inter.followup.send(
                embed=discord.Embed(
                    title="📊 Informe ejecutivo",
                    description=(
                        f"Pendientes de aprobación: **{pend}**\n"
                        f"Delegaciones activas: **{dels}**\n"
                        f"Emergencia: **{'Sí' if em else 'No'}**\n"
                        f"Zonas: Gobernanza · Interinstitucional · Calidad"
                    ),
                    color=C_FUNDADOR,
                ),
                ephemeral=True,
            )

        # ── Resto: modal genérico de registro ──
        async def _gen(inter2: discord.Interaction, vals: dict):
            store.auditar(
                guild_id=gid, actor_id=uid, actor_name=str(inter.user),
                rol="Fundador", accion=f"{self.cat}:{self.key}",
                afectado=str(vals)[:120], resultado="ok", extra=vals,
            )
            await inter2.followup.send(
                embed=discord.Embed(
                    title="✅ Acción registrada",
                    description="\n".join(f"**{k}:** {v}" for k, v in vals.items()),
                    color=C_OK,
                ),
                ephemeral=True,
            )

        return await inter.response.send_modal(
            ModalTexto(
                title=self.label[:45],
                fields=[
                    ("detalle", "Detalle / notas", True, discord.TextStyle.paragraph, 800, "Describe la acción…"),
                    ("extra", "Dato adicional", False, discord.TextStyle.short, 100, "Opcional"),
                ],
                on_submit_cb=_gen,
            )
        )


class FundadorPanelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(FundadorCatSelect())

    @ui.button(
        label="Actualizar resumen",
        style=discord.ButtonStyle.secondary,
        emoji="🔄",
        custom_id="mando:fundador:refresh",
        row=1,
    )
    async def refresh(self, inter: discord.Interaction, button: ui.Button):
        if not inter.guild or not _check_fundador(inter):
            return await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
        await inter.response.edit_message(embed=embed_fundador(inter.guild), view=self)


# ═══════════════════════════════════════════════════════════════
# PANEL CO-FUNDADOR (plantilla por zona)
# ═══════════════════════════════════════════════════════════════

_ZONAS = {
    "gobernanza": {
        "titulo": "Orden y Legitimidad · Gobernanza",
        "emoji": "⚖️",
        "color": C_GOB,
        "cats": [
            ("Políticas", "politicas", "📘"),
            ("Actas", "actas", "📝"),
            ("Ética", "etica", "⚖️"),
            ("Disciplina", "disciplina", "⚠️"),
            ("Talento humano", "talento", "🧑‍⚕️"),
            ("Auditoría interna", "auditoria", "🔍"),
            ("Estrategia", "estrategia", "🎯"),
            ("Transparencia", "transparencia", "🧾"),
        ],
        "acciones": {
            "politicas": [("📘 Crear política", "crear"), ("📢 Publicar política", "pub"), ("🗑️ Derogar", "der"), ("📚 Ver políticas", "ver")],
            "actas": [("📝 Redactar acta", "red"), ("🗂️ Consultar actas", "ver")],
            "etica": [("⚖️ Abrir caso", "abrir"), ("🔨 Resolver caso", "res"), ("📂 Ver casos", "ver")],
            "disciplina": [("⚠️ Advertir", "adv"), ("🔇 Silenciar", "sil"), ("🚪 Expulsar", "exp"), ("📖 Historial", "his")],
            "talento": [("🧑‍⚕️ Contratar", "con"), ("👋 Desvincular", "des"), ("⭐ Evaluar", "eva"), ("🔼 Ascender/trasladar", "asc")],
            "auditoria": [("🔍 Lanzar auditoría", "lan"), ("📌 Hallazgo", "hal"), ("✔️ Cerrar auditoría", "cer")],
            "estrategia": [("🎯 Nuevo objetivo", "obj"), ("📈 Actualizar avance", "ava")],
            "transparencia": [("🧾 Informe transparencia", "inf"), ("🛡️ Riesgo legal", "rie"), ("📄 Revisar contrato", "con")],
        },
    },
    "interinstitucional": {
        "titulo": "Puentes y Alianzas · Interinstitucional",
        "emoji": "🤝",
        "color": C_INT,
        "cats": [
            ("Convenios", "convenios", "🤝"),
            ("Aliados", "aliados", "🏢"),
            ("Reuniones", "reuniones", "📅"),
            ("Donaciones", "donaciones", "🎗️"),
            ("Financiamiento", "financiamiento", "🏦"),
            ("Comunicación", "comunicacion", "📰"),
            ("Comunidad", "comunidad", "🌎"),
            ("Referencias", "referencias", "🚑"),
            ("Informes", "informes", "📊"),
        ],
        "acciones": {
            "convenios": [("🤝 Crear convenio", "crear"), ("🔄 Renovar", "ren"), ("❌ Terminar", "ter"), ("⬆️ Proponer mayor", "may"), ("📚 Ver convenios", "ver")],
            "aliados": [("🏢 Registrar aliado", "reg"), ("🗒️ Directorio", "dir")],
            "reuniones": [("📅 Agendar reunión", "age")],
            "donaciones": [("🎗️ Lanzar campaña", "cam"), ("💰 Registrar donación", "don"), ("💌 Agradecimiento", "agr")],
            "financiamiento": [("🏦 Solicitud", "sol")],
            "comunicacion": [("📰 Comunicado oficial", "com"), ("🎙️ Gestión de prensa", "pre")],
            "comunidad": [("🌎 Jornada comunitaria", "jor")],
            "referencias": [("🚑 Referencia hospital", "ref")],
            "informes": [("📊 Informe de alianzas", "inf")],
        },
    },
    "calidad": {
        "titulo": "Excelencia y Seguridad · Calidad",
        "emoji": "🏅",
        "color": C_CAL,
        "cats": [
            ("Seguridad paciente", "seguridad", "🩺"),
            ("Auditorías", "auditorias", "🧪"),
            ("Mejora continua", "mejora", "🛠️"),
            ("Acreditaciones", "acreditaciones", "🏅"),
            ("Indicadores", "indicadores", "📈"),
            ("Satisfacción", "satisfaccion", "😀"),
            ("Comités", "comites", "👥"),
            ("Protocolos", "protocolos", "📘"),
            ("Informes", "informes", "📊"),
        ],
        "acciones": {
            "seguridad": [("🩺 Evento adverso", "evt"), ("🔬 Investigación", "inv"), ("🚧 Alerta seguridad", "ale")],
            "auditorias": [("🧪 Auditar procesos", "pro"), ("📑 Auditar HC", "hc"), ("📋 Ver auditorías", "ver")],
            "mejora": [("🛠️ Plan de mejora", "plan"), ("✅ Cerrar acción", "cer"), ("📂 Ver planes", "ver")],
            "acreditaciones": [("🏅 Iniciar acreditación", "ini"), ("🧭 Estado entidad", "est"), ("🎭 Simulacro", "sim")],
            "indicadores": [("📈 Ver indicadores", "ver")],
            "satisfaccion": [("😀 Lanzar encuesta", "enc")],
            "comites": [("👥 Convocar comité", "com")],
            "protocolos": [("📘 Aprobar protocolo", "apr"), ("🛑 Suspender protocolo", "sus")],
            "informes": [("📊 Informe de calidad", "inf")],
        },
    },
}


def embed_zona(guild: discord.Guild, zona: str) -> discord.Embed:
    meta = _ZONAS[zona]
    data = store.load()
    extra = ""
    if zona == "gobernanza":
        extra = (
            f"Políticas: {len(data.get('politicas') or [])} · "
            f"Casos ética abiertos: {sum(1 for c in (data.get('casos_etica') or []) if c.get('estado')=='abierto')} · "
            f"Objetivos: {len(data.get('objetivos') or [])}"
        )
    elif zona == "interinstitucional":
        extra = (
            f"Convenios: {len(data.get('convenios') or [])} · "
            f"Aliados: {len(data.get('aliados') or [])} · "
            f"Campañas: {len(data.get('campanas') or [])}"
        )
    else:
        extra = (
            f"Eventos adversos: {len(data.get('eventos_adversos') or [])} · "
            f"Planes mejora: {len(data.get('planes_mejora') or [])} · "
            f"Acreditaciones: {len(data.get('acreditaciones') or [])}"
        )
    return discord.Embed(
        title=f"{meta['emoji']}  {meta['titulo']}",
        description=(
            f"{extra}\n{_banner_emergencia(guild.id)}\n"
            f"Elige una **categoría** para ver las acciones."
        ),
        color=meta["color"],
    ).set_footer(text=f"Hospital General · {_ts()}")


class ZonaCatSelect(ui.Select):
    def __init__(self, zona: str):
        self.zona = zona
        meta = _ZONAS[zona]
        opts = [
            discord.SelectOption(label=lab, value=val, emoji=emo)
            for lab, val, emo in meta["cats"]
        ]
        super().__init__(placeholder="Categoría…", options=opts[:25], row=0)

    async def callback(self, inter: discord.Interaction):
        if not _check_zona(inter, self.zona):
            return await inter.response.send_message(
                "❌ Solo el Co-Fundador de esta zona (o el Fundador).", ephemeral=True
            )
        cat = self.values[0]
        meta = _ZONAS[self.zona]
        view = ui.View(timeout=180)
        for label, key in meta["acciones"].get(cat, []):
            style = discord.ButtonStyle.primary
            if any(x in label for x in ("Derogar", "Expulsar", "Desvincular", "Suspender", "Terminar")):
                style = discord.ButtonStyle.danger
            elif any(x in label for x in ("Crear", "Publicar", "Aprobar", "Contratar", "Lanzar", "Registrar")):
                style = discord.ButtonStyle.success
            view.add_item(_ZonaBtn(self.zona, cat, key, label, style))
        await inter.response.send_message(
            embed=discord.Embed(
                title=f"{meta['emoji']} {cat.title()}",
                description="Elige una acción:",
                color=meta["color"],
            ),
            view=view,
            ephemeral=True,
        )


class _ZonaBtn(ui.Button):
    def __init__(self, zona: str, cat: str, key: str, label: str, style: discord.ButtonStyle):
        super().__init__(label=label[:80], style=style)
        self.zona = zona
        self.cat = cat
        self.key = key

    async def callback(self, inter: discord.Interaction):
        if not _check_zona(inter, self.zona):
            return await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
        assert inter.guild and isinstance(inter.user, discord.Member)
        gid = inter.guild.id
        uid = inter.user.id
        meta = _ZONAS[self.zona]

        # Acciones que requieren aprobación del Fundador
        requiere_aprobacion = (
            (self.zona == "gobernanza" and self.cat == "disciplina" and self.key == "exp")
            or (self.zona == "gobernanza" and self.cat == "transparencia" and self.key == "inf")
            or (self.zona == "interinstitucional" and self.cat == "convenios" and self.key == "may")
            or (self.zona == "interinstitucional" and self.cat == "financiamiento" and self.key == "sol")
            or (self.zona == "interinstitucional" and self.cat == "comunicacion" and self.key == "com")
            or (self.zona == "calidad" and self.cat == "protocolos" and self.key == "sus")
        )

        async def _submit(inter2: discord.Interaction, vals: dict):
            titulo = f"{self.zona}/{self.cat}/{self.key}"
            if requiere_aprobacion:
                item = store.encolar_aprobacion(
                    guild_id=gid,
                    origen_id=uid,
                    origen_zona=self.zona,
                    titulo=titulo,
                    detalle=str(vals)[:500],
                    payload={"vals": vals, "accion": titulo},
                )
                store.auditar(
                    guild_id=gid, actor_id=uid, actor_name=str(inter.user),
                    rol=f"Co-Fundador {self.zona}", accion=titulo,
                    afectado=item["id"], resultado="en_cola",
                )
                return await inter2.followup.send(
                    embed=discord.Embed(
                        title="⏳ Enviado a aprobación del Fundador",
                        description=f"ID: **{item['id']}**\n{titulo}",
                        color=C_WARN,
                    ),
                    ephemeral=True,
                )

            # Persistencia simple por categoría
            data = store.load()
            bucket_map = {
                ("gobernanza", "politicas"): "politicas",
                ("gobernanza", "actas"): "actas",
                ("gobernanza", "etica"): "casos_etica",
                ("gobernanza", "estrategia"): "objetivos",
                ("interinstitucional", "convenios"): "convenios",
                ("interinstitucional", "aliados"): "aliados",
                ("interinstitucional", "donaciones"): "campanas",
                ("calidad", "seguridad"): "eventos_adversos",
                ("calidad", "mejora"): "planes_mejora",
                ("calidad", "acreditaciones"): "acreditaciones",
            }
            bkey = bucket_map.get((self.zona, self.cat))
            if bkey and self.key in ("crear", "abrir", "reg", "cam", "evt", "plan", "ini", "obj", "red"):
                entry = {
                    "id": store.nuevo_id(bkey[:3].upper()),
                    "guild_id": gid,
                    "ts": int(time.time()),
                    "por": uid,
                    "estado": "abierto",
                    **vals,
                }
                data.setdefault(bkey, []).insert(0, entry)
                store.save(data)
                ref = entry["id"]
            else:
                ref = "—"

            store.auditar(
                guild_id=gid, actor_id=uid, actor_name=str(inter.user),
                rol=f"Co-Fundador {self.zona}", accion=titulo,
                afectado=ref, resultado="ok", extra=vals,
            )

            # Avisos cruzados (simplificado)
            if self.zona == "calidad" and self.cat == "seguridad" and self.key == "evt":
                # aviso fundador si menciona grave
                if "grave" in (vals.get("gravedad") or "").lower():
                    pass  # cola opcional

            await inter2.followup.send(
                embed=discord.Embed(
                    title="✅ Acción registrada",
                    description=(
                        f"**Zona:** {self.zona}\n**Acción:** {self.label}\n"
                        + (f"**ID:** `{ref}`\n" if ref != "—" else "")
                        + "\n".join(f"**{k}:** {v[:200]}" for k, v in vals.items())
                    ),
                    color=meta["color"],
                ),
                ephemeral=True,
            )

        # Campos según acción
        fields = [
            ("detalle", "Detalle principal", True, discord.TextStyle.paragraph, 800, "Describe…"),
        ]
        if self.key in ("adv", "sil", "exp", "des", "con", "asc", "his"):
            fields.insert(
                0,
                ("usuario", "ID o mención de usuario", True, discord.TextStyle.short, 40, "123…"),
            )
        if self.key in ("sil",):
            fields.append(("duracion", "Duración (minutos)", True, discord.TextStyle.short, 6, "60"))
        if self.key in ("evt",):
            fields = [
                ("servicio", "Servicio", True, discord.TextStyle.short, 60, "Urgencias…"),
                ("gravedad", "Gravedad", True, discord.TextStyle.short, 20, "leve/moderada/grave"),
                ("descripcion", "Descripción", True, discord.TextStyle.paragraph, 800, "…"),
            ]
        if self.key in ("crear",) and self.cat == "politicas":
            fields = [
                ("titulo", "Título", True, discord.TextStyle.short, 100, "…"),
                ("categoria", "Categoría", True, discord.TextStyle.short, 40, "…"),
                ("contenido", "Contenido", True, discord.TextStyle.paragraph, 1000, "…"),
                ("vigencia", "Vigencia", False, discord.TextStyle.short, 40, "indefinida"),
            ]
        if self.key in ("ver", "dir", "inf", "his"):
            await inter.response.defer(ephemeral=True)
            data = store.load()
            bucket_map = {
                "politicas": "politicas",
                "actas": "actas",
                "etica": "casos_etica",
                "convenios": "convenios",
                "aliados": "aliados",
                "donaciones": "campanas",
                "seguridad": "eventos_adversos",
                "mejora": "planes_mejora",
                "acreditaciones": "acreditaciones",
                "estrategia": "objetivos",
            }
            b = bucket_map.get(self.cat)
            items = [x for x in (data.get(b) or []) if int(x.get("guild_id") or 0) == gid][:15] if b else []
            txt = "\n".join(
                f"`{i.get('id')}` {i.get('titulo') or i.get('detalle') or i.get('nombre') or '—'}"
                for i in items
            ) or "_Sin registros_"
            store.auditar(
                guild_id=gid, actor_id=uid, actor_name=str(inter.user),
                rol=f"Co-Fundador {self.zona}", accion=f"{self.cat}:ver",
                afectado="—", resultado="ok",
            )
            return await inter.followup.send(
                embed=discord.Embed(title=f"📋 {self.cat.title()}", description=txt[:3900], color=meta["color"]),
                ephemeral=True,
            )

        await inter.response.send_modal(
            ModalTexto(
                title=self.label[:45],
                fields=fields,
                on_submit_cb=_submit,
            )
        )


class ZonaPanelView(ui.View):
    def __init__(self, zona: str):
        super().__init__(timeout=None)
        self.zona = zona
        self.add_item(ZonaCatSelect(zona))

    @ui.button(label="Actualizar", style=discord.ButtonStyle.secondary, emoji="🔄", row=1)
    async def refresh(self, inter: discord.Interaction, button: ui.Button):
        if not inter.guild or not _check_zona(inter, self.zona):
            return await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
        # custom_id dinámico no persistente en este botón — ok en mismo mensaje
        await inter.response.edit_message(embed=embed_zona(inter.guild, self.zona), view=self)


# ═══════════════════════════════════════════════════════════════
# Comando de envío
# ═══════════════════════════════════════════════════════════════


def registrar(bot: commands.Bot) -> None:
    try:
        bot.add_view(FundadorPanelView())
    except Exception:
        pass

    @bot.tree.command(
        name="enviar_panel_mando",
        description="[Fundador] Envía los paneles de Mando / Co-Fundadores a un canal",
    )
    @app_commands.describe(
        canal="Canal donde publicar los paneles",
        cual="Qué panel enviar",
    )
    @app_commands.choices(
        cual=[
            app_commands.Choice(name="Fundador · Mando General", value="fundador"),
            app_commands.Choice(name="Co-Fundador · Gobernanza", value="gobernanza"),
            app_commands.Choice(name="Co-Fundador · Interinstitucional", value="interinstitucional"),
            app_commands.Choice(name="Co-Fundador · Calidad", value="calidad"),
            app_commands.Choice(name="Los 4 paneles", value="todos"),
        ]
    )
    async def enviar_panel_mando(
        inter: discord.Interaction,
        canal: discord.TextChannel,
        cual: app_commands.Choice[str],
    ):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message("❌ Solo en servidor.", ephemeral=True)
        if not member_es_fundador(inter.user):
            return await inter.response.send_message(
                "❌ Solo el **Fundador del Hospital**.", ephemeral=True
            )
        await inter.response.defer(ephemeral=True)
        enviados = []
        val = cual.value

        async def send_one(kind: str):
            if kind == "fundador":
                await canal.send(embed=embed_fundador(inter.guild), view=FundadorPanelView())
            else:
                await canal.send(
                    embed=embed_zona(inter.guild, kind),
                    view=ZonaPanelView(kind),
                )
            enviados.append(kind)

        try:
            if val == "todos":
                for k in ("fundador", "gobernanza", "interinstitucional", "calidad"):
                    await send_one(k)
            else:
                await send_one(val)
        except Exception as e:
            return await inter.followup.send(f"❌ Error al enviar: {e}", ephemeral=True)

        store.auditar(
            guild_id=inter.guild.id,
            actor_id=inter.user.id,
            actor_name=str(inter.user),
            rol="Fundador",
            accion="enviar_panel_mando",
            afectado=canal.mention,
            resultado="ok",
            extra={"cual": val},
        )
        await inter.followup.send(
            f"✅ Panel(es) enviado(s) a {canal.mention}: {', '.join(enviados)}",
            ephemeral=True,
        )

    print("[paneles_mando] OK — Mando General + 3 zonas")
