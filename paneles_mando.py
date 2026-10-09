# -*- coding: utf-8 -*-
"""
Paneles de autoridades — Hospital General

Fundador · Mando General
Co-Fundador Gobernanza · Orden y Legitimidad
Co-Fundador Interinstitucional · Puentes y Alianzas
Co-Fundador Calidad · Excelencia y Seguridad

UX: solo menús desplegables → el bot procesa interno → un solo embed de resultado.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import discord
from discord import app_commands, ui
from discord.ext import commands

import mando_store as store

try:
    from roles_cofundadores import member_es_cofundador, member_es_fundador
except Exception:

    def member_es_fundador(m: discord.Member) -> bool:
        return bool(m.guild and m.id == m.guild.owner_id)

    def member_es_cofundador(m: discord.Member, zona: str | None = None) -> bool:
        return False


C_F = 0x9B59B6
C_G = 0x3498DB
C_I = 0x1ABC9C
C_C = 0xE67E22
C_OK = 0x2ECC71
C_ERR = 0xE74C3C
C_WARN = 0xF1C40F


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")


def _banner(gid: int) -> str:
    em = store.emergencia_activa(gid)
    if not em:
        return ""
    return f"\n🚨 **EMERGENCIA:** {em.get('tipo', '—')} — {str(em.get('descripcion', ''))[:120]}\n"


async def _resultado(
    inter: discord.Interaction,
    *,
    titulo: str,
    descripcion: str,
    color: int = C_OK,
    defer_done: bool = False,
) -> None:
    emb = discord.Embed(title=titulo, description=descripcion, color=color)
    emb.set_footer(text=f"Hospital General · {_ts()}")
    try:
        if defer_done or inter.response.is_done():
            await inter.followup.send(embed=emb, ephemeral=True)
        else:
            await inter.response.send_message(embed=emb, ephemeral=True)
    except Exception:
        try:
            await inter.followup.send(embed=emb, ephemeral=True)
        except Exception:
            pass


def _audit(inter: discord.Interaction, rol: str, accion: str, afectado: str = "—", resultado: str = "ok", extra=None):
    if not inter.guild:
        return
    store.auditar(
        guild_id=inter.guild.id,
        actor_id=inter.user.id,
        actor_name=str(inter.user),
        rol=rol,
        accion=accion,
        afectado=afectado,
        resultado=resultado,
        extra=extra or {},
    )


# ═══════════════════════════════════════════════════════════════
# Catálogo completo de acciones por panel (value = zona:cat:accion)
# ═══════════════════════════════════════════════════════════════

# Fundador: categorías → acciones
FUNDADOR_MENU: Dict[str, List[Tuple[str, str]]] = {
    "📋 Decisiones": [
        ("ver_pendientes", "Ver pendientes"),
        ("aprobar", "Aprobar decisión"),
        ("vetar", "Vetar decisión"),
        ("devolver", "Devolver decisión"),
    ],
    "🔑 Delegaciones": [
        ("ver_delegaciones", "Ver delegaciones activas"),
        ("delegar", "Delegar poder"),
        ("revocar_delegacion", "Revocar delegación"),
    ],
    "👑 Autoridades": [
        ("listar_autoridades", "Listar autoridades"),
        ("nombrar_cofundador", "Nombrar Co-Fundador"),
        ("destituir_cofundador", "Destituir Co-Fundador"),
        ("reasignar_zona", "Reasignar zona"),
    ],
    "🏛️ Consejo": [
        ("convocar_consejo", "Convocar consejo"),
        ("anuncio_oficial", "Anuncio oficial"),
        ("sellar_documento", "Sellar documento"),
    ],
    "🚨 Emergencia": [
        ("estado_emergencia", "Estado de emergencia"),
        ("declarar_emergencia", "Declarar emergencia"),
        ("cerrar_emergencia", "Cerrar emergencia"),
    ],
    "👁️ Supervisión": [
        ("ver_zona_gob", "Ver zona Gobernanza"),
        ("ver_zona_int", "Ver zona Interinstitucional"),
        ("ver_zona_cal", "Ver zona Calidad"),
        ("auditoria_total", "Auditoría total"),
        ("fijar_prioridad", "Fijar prioridad estratégica"),
    ],
    "📊 Informes": [
        ("informe_ejecutivo", "Informe ejecutivo"),
    ],
}

ZONA_MENUS: Dict[str, Dict[str, List[Tuple[str, str]]]] = {
    "gobernanza": {
        "📘 Políticas": [
            ("pol_crear", "Crear política"),
            ("pol_publicar", "Publicar política"),
            ("pol_derogar", "Derogar política"),
            ("pol_ver", "Ver políticas"),
        ],
        "📝 Actas": [
            ("acta_redactar", "Redactar acta"),
            ("acta_ver", "Consultar actas"),
        ],
        "⚖️ Ética": [
            ("etica_abrir", "Abrir caso"),
            ("etica_resolver", "Resolver caso"),
            ("etica_ver", "Ver casos"),
        ],
        "⚠️ Disciplina": [
            ("disc_advertir", "Advertir"),
            ("disc_silenciar", "Silenciar"),
            ("disc_expulsar", "Expulsar (aprobación)"),
            ("disc_historial", "Historial"),
        ],
        "🧑‍⚕️ Talento humano": [
            ("tal_contratar", "Contratar"),
            ("tal_desvincular", "Desvincular"),
            ("tal_evaluar", "Evaluar desempeño"),
            ("tal_ascender", "Ascender o trasladar"),
        ],
        "🔍 Auditoría interna": [
            ("aud_lanzar", "Lanzar auditoría"),
            ("aud_hallazgo", "Registrar hallazgo"),
            ("aud_cerrar", "Cerrar auditoría"),
        ],
        "🎯 Estrategia": [
            ("est_objetivo", "Nuevo objetivo"),
            ("est_avance", "Actualizar avance"),
            ("est_ver", "Ver objetivos"),
        ],
        "🧾 Transparencia": [
            ("tra_informe", "Informe transparencia (aprobación)"),
            ("tra_riesgo", "Registrar riesgo legal"),
            ("tra_contrato", "Revisar contrato"),
        ],
    },
    "interinstitucional": {
        "🤝 Convenios": [
            ("con_crear", "Crear convenio"),
            ("con_renovar", "Renovar convenio"),
            ("con_terminar", "Terminar convenio"),
            ("con_mayor", "Proponer convenio mayor (aprobación)"),
            ("con_ver", "Ver convenios"),
        ],
        "🏢 Aliados": [
            ("ali_registrar", "Registrar aliado"),
            ("ali_directorio", "Directorio"),
        ],
        "📅 Reuniones": [
            ("reu_agendar", "Agendar reunión"),
        ],
        "🎗️ Donaciones": [
            ("don_campana", "Lanzar campaña"),
            ("don_registrar", "Registrar donación"),
            ("don_agradecer", "Agradecimiento"),
        ],
        "🏦 Financiamiento": [
            ("fin_solicitud", "Solicitud (aprobación si monto alto)"),
        ],
        "📰 Comunicación": [
            ("com_oficial", "Comunicado oficial"),
            ("com_prensa", "Gestión de prensa"),
        ],
        "🌎 Comunidad": [
            ("comu_jornada", "Jornada comunitaria"),
        ],
        "🚑 Referencias": [
            ("ref_hospital", "Referencia a otro hospital"),
        ],
        "📊 Informes": [
            ("inf_alianzas", "Informe de alianzas"),
        ],
    },
    "calidad": {
        "🩺 Seguridad del paciente": [
            ("seg_evento", "Registrar evento adverso"),
            ("seg_investigacion", "Abrir investigación"),
            ("seg_alerta", "Alerta de seguridad"),
        ],
        "🧪 Auditorías": [
            ("cau_procesos", "Auditar procesos"),
            ("cau_hc", "Auditar historias clínicas"),
            ("cau_ver", "Ver auditorías"),
        ],
        "🛠️ Mejora continua": [
            ("mej_plan", "Plan de mejora"),
            ("mej_cerrar", "Cerrar acción correctiva"),
            ("mej_ver", "Ver planes abiertos"),
        ],
        "🏅 Acreditaciones": [
            ("acr_iniciar", "Iniciar acreditación"),
            ("acr_estado", "Estado por entidad"),
            ("acr_simulacro", "Programar simulacro"),
        ],
        "📈 Indicadores": [
            ("ind_ver", "Ver indicadores"),
        ],
        "😀 Satisfacción": [
            ("sat_encuesta", "Lanzar encuesta"),
        ],
        "👥 Comités": [
            ("com_convocar", "Convocar comité"),
        ],
        "📘 Protocolos": [
            ("pro_aprobar", "Aprobar protocolo"),
            ("pro_suspender", "Suspender protocolo (aprobación)"),
        ],
        "📊 Informes": [
            ("inf_calidad", "Informe de calidad"),
        ],
    },
}

ZONA_META = {
    "gobernanza": ("Orden y Legitimidad", "⚖️", C_G, "Co-Fundador · Gobernanza"),
    "interinstitucional": ("Puentes y Alianzas", "🤝", C_I, "Co-Fundador · Interinstitucional"),
    "calidad": ("Excelencia y Seguridad", "🏅", C_C, "Co-Fundador · Calidad"),
}

# Acciones que van a cola del Fundador
_APROBACION = {
    "disc_expulsar",
    "tra_informe",
    "con_mayor",
    "fin_solicitud",
    "pro_suspender",
}


# ═══════════════════════════════════════════════════════════════
# Procesamiento interno unificado
# ═══════════════════════════════════════════════════════════════


async def _procesar(
    inter: discord.Interaction,
    *,
    panel: str,
    accion: str,
    label: str,
    valores: Optional[dict] = None,
) -> None:
    """Ejecuta la acción en silencio y devuelve un solo resultado."""
    valores = valores or {}
    if not inter.guild or not isinstance(inter.user, discord.Member):
        return await _resultado(
            inter, titulo="❌ Error", descripcion="Solo en el servidor.", color=C_ERR
        )

    try:
        if not inter.response.is_done():
            await inter.response.defer(ephemeral=True)
    except Exception:
        pass

    gid = inter.guild.id
    uid = inter.user.id
    data = store.load()

    # —— Fundador: consultas ——
    if panel == "fundador":
        if accion == "ver_pendientes":
            pend = store.listar_pendientes(gid)
            if not pend:
                txt = "No hay decisiones pendientes."
            else:
                txt = "\n".join(
                    f"`{p['id']}` · **{p.get('titulo')}** · zona `{p.get('origen_zona')}`"
                    for p in pend[:20]
                )
            _audit(inter, "Fundador", accion)
            return await _resultado(
                inter, titulo="📋 Decisiones pendientes", descripcion=txt, color=C_F, defer_done=True
            )

        if accion in ("aprobar", "vetar", "devolver"):
            pid = (valores.get("id") or "").strip()
            com = (valores.get("comentario") or "").strip()
            if not pid:
                return await _resultado(
                    inter, titulo="❌ Datos incompletos", descripcion="Falta el ID de la decisión.", color=C_ERR, defer_done=True
                )
            if accion == "vetar" and not com:
                return await _resultado(
                    inter, titulo="❌ Datos incompletos", descripcion="El motivo es obligatorio al vetar.", color=C_ERR, defer_done=True
                )
            estado = {"aprobar": "aprobado", "vetar": "vetado", "devolver": "devuelto"}[accion]
            it = store.actualizar_pendiente(pid, estado, com)
            if not it:
                return await _resultado(
                    inter, titulo="❌ No encontrado", descripcion=f"No existe la decisión `{pid}`.", color=C_ERR, defer_done=True
                )
            _audit(inter, "Fundador", f"decision:{estado}", pid)
            try:
                u = inter.client.get_user(int(it.get("origen_id") or 0))
                if u:
                    await u.send(
                        embed=discord.Embed(
                            title=f"Decisión {estado}",
                            description=f"**{it.get('titulo')}**\n{com or '—'}",
                            color=C_OK if estado == "aprobado" else C_ERR,
                        )
                    )
            except Exception:
                pass
            return await _resultado(
                inter,
                titulo=f"✅ Decisión {estado}",
                descripcion=f"**ID:** `{pid}`\n**Título:** {it.get('titulo')}\n**Comentario:** {com or '—'}",
                color=C_OK if estado == "aprobado" else C_ERR,
                defer_done=True,
            )

        if accion == "ver_delegaciones":
            dels = store.listar_delegaciones(gid)
            txt = (
                "\n".join(
                    f"`{d['id']}` <@{d['user_id']}> · **{d.get('poder')}** · vence <t:{d.get('vence_ts')}:R>"
                    for d in dels[:20]
                )
                or "Sin delegaciones activas."
            )
            _audit(inter, "Fundador", accion)
            return await _resultado(
                inter, titulo="🔑 Delegaciones activas", descripcion=txt, color=C_F, defer_done=True
            )

        if accion == "delegar":
            try:
                tid = int(
                    str(valores.get("user_id", ""))
                    .replace("<@", "")
                    .replace(">", "")
                    .replace("!", "")
                    .strip()
                )
                horas = int(valores.get("horas") or "24")
            except Exception:
                return await _resultado(
                    inter, titulo="❌ Datos inválidos", descripcion="Usuario u horas incorrectos.", color=C_ERR, defer_done=True
                )
            poder = valores.get("poder") or "general"
            item = {
                "id": store.nuevo_id("DEL"),
                "guild_id": gid,
                "user_id": tid,
                "poder": poder,
                "condiciones": valores.get("condiciones") or "",
                "vence_ts": int(time.time()) + max(1, horas) * 3600,
                "revocada": False,
                "por": uid,
            }
            data.setdefault("delegaciones", []).insert(0, item)
            store.save(data)
            _audit(inter, "Fundador", "delegar", str(tid))
            return await _resultado(
                inter,
                titulo="✅ Poder delegado",
                descripcion=f"**A:** <@{tid}>\n**Poder:** {poder}\n**Duración:** {horas}h\n**ID:** `{item['id']}`",
                defer_done=True,
            )

        if accion == "revocar_delegacion":
            did = (valores.get("id") or "").strip()
            found = None
            for d in data.get("delegaciones") or []:
                if d.get("id") == did:
                    d["revocada"] = True
                    d["motivo_revoca"] = valores.get("motivo") or ""
                    found = d
                    break
            if not found:
                return await _resultado(
                    inter, titulo="❌ No encontrado", descripcion=f"Delegación `{did}` inexistente.", color=C_ERR, defer_done=True
                )
            store.save(data)
            _audit(inter, "Fundador", "revocar_delegacion", did)
            return await _resultado(
                inter, titulo="✅ Delegación revocada", descripcion=f"**ID:** `{did}`", defer_done=True
            )

        if accion == "listar_autoridades":
            lines = []
            mapping = [
                ("FUNDADOR_OWNER", "Fundador del Hospital"),
                ("COFUNDADOR_GOBERNANZA", "Co-Fundador · Gobernanza"),
                ("COFUNDADOR_INTERINSTITUCIONAL", "Co-Fundador · Interinstitucional"),
                ("COFUNDADOR_CALIDAD", "Co-Fundador · Calidad"),
            ]
            try:
                import permisos
            except Exception:
                permisos = None
            for key, nombre in mapping:
                miembros = []
                if permisos:
                    try:
                        for m in inter.guild.members:
                            if permisos.member_tiene_alguna_key(m, key):
                                miembros.append(m.mention)
                    except Exception:
                        pass
                lines.append(f"**{nombre}:** {', '.join(miembros) or '_Nadie_'}")
            _audit(inter, "Fundador", accion)
            return await _resultado(
                inter, titulo="👑 Autoridades", descripcion="\n".join(lines), color=C_F, defer_done=True
            )

        if accion == "estado_emergencia":
            em = store.emergencia_activa(gid)
            if not em:
                txt = "🟢 Sin emergencia activa."
            else:
                txt = f"🚨 **{em.get('tipo')}**\n{em.get('descripcion')}\nAlcance: {em.get('alcance')}"
            _audit(inter, "Fundador", accion)
            return await _resultado(
                inter, titulo="Estado de emergencia", descripcion=txt, color=C_ERR if em else C_OK, defer_done=True
            )

        if accion == "declarar_emergencia":
            data["emergencia"] = {
                "guild_id": gid,
                "activa": True,
                "tipo": valores.get("tipo") or "General",
                "descripcion": valores.get("descripcion") or "",
                "alcance": valores.get("alcance") or "hospital",
                "por": uid,
                "ts": int(time.time()),
            }
            store.save(data)
            _audit(inter, "Fundador", "emergencia_on", valores.get("tipo", ""))
            return await _resultado(
                inter,
                titulo="🚨 Emergencia declarada",
                descripcion=f"**Tipo:** {valores.get('tipo')}\n{valores.get('descripcion')}",
                color=C_ERR,
                defer_done=True,
            )

        if accion == "cerrar_emergencia":
            if data.get("emergencia"):
                data["emergencia"]["activa"] = False
                data["emergencia"]["cierre"] = valores.get("resumen") or ""
                data["emergencia"]["cierre_ts"] = int(time.time())
            store.save(data)
            _audit(inter, "Fundador", "emergencia_off")
            return await _resultado(
                inter, titulo="🟢 Emergencia cerrada", descripcion=valores.get("resumen") or "Archivada.", defer_done=True
            )

        if accion == "auditoria_total":
            aud = [a for a in (data.get("auditoria") or []) if int(a.get("guild_id") or 0) == gid][:25]
            txt = (
                "\n".join(
                    f"`{a.get('id')}` **{a.get('accion')}** · {a.get('actor_name')} · {a.get('resultado')}"
                    for a in aud
                )
                or "_Sin registros_"
            )
            _audit(inter, "Fundador", accion)
            return await _resultado(
                inter, titulo="🔎 Auditoría total", descripcion=txt[:3900], color=C_F, defer_done=True
            )

        if accion == "informe_ejecutivo":
            pend = len(store.listar_pendientes(gid))
            dels = len(store.listar_delegaciones(gid))
            em = store.emergencia_activa(gid)
            txt = (
                f"**Pendientes de aprobación:** {pend}\n"
                f"**Delegaciones activas:** {dels}\n"
                f"**Emergencia:** {'Sí — ' + str(em.get('tipo')) if em else 'No'}\n\n"
                f"**Políticas:** {len(data.get('politicas') or [])}\n"
                f"**Convenios:** {len(data.get('convenios') or [])}\n"
                f"**Eventos adversos:** {len(data.get('eventos_adversos') or [])}\n"
                f"**Planes de mejora:** {len(data.get('planes_mejora') or [])}"
            )
            _audit(inter, "Fundador", accion)
            return await _resultado(
                inter, titulo="📊 Informe ejecutivo", descripcion=txt, color=C_F, defer_done=True
            )

        if accion.startswith("ver_zona_"):
            z = {"ver_zona_gob": "gobernanza", "ver_zona_int": "interinstitucional", "ver_zona_cal": "calidad"}[accion]
            titulo, emoji, color, _ = ZONA_META[z]
            _audit(inter, "Fundador", accion, z)
            return await _resultado(
                inter,
                titulo=f"{emoji} Vista · {titulo}",
                descripcion=embed_zona_resumen(gid, z),
                color=color,
                defer_done=True,
            )

    # —— Zonas: listados ——
    listados = {
        "pol_ver": ("politicas", "Políticas"),
        "acta_ver": ("actas", "Actas"),
        "etica_ver": ("casos_etica", "Casos de ética"),
        "est_ver": ("objetivos", "Objetivos"),
        "con_ver": ("convenios", "Convenios"),
        "ali_directorio": ("aliados", "Aliados"),
        "cau_ver": ("auditorias_calidad", "Auditorías"),
        "mej_ver": ("planes_mejora", "Planes de mejora"),
        "acr_estado": ("acreditaciones", "Acreditaciones"),
    }
    if accion in listados:
        bkey, titulo = listados[accion]
        items = [x for x in (data.get(bkey) or []) if int(x.get("guild_id") or 0) == gid][:20]
        txt = (
            "\n".join(
                f"`{i.get('id')}` {i.get('titulo') or i.get('nombre') or i.get('detalle') or i.get('entidad') or '—'}"
                for i in items
            )
            or "_Sin registros_"
        )
        _audit(inter, panel, accion)
        color = ZONA_META.get(panel, ("", "", C_OK, ""))[2] if panel in ZONA_META else C_OK
        return await _resultado(
            inter, titulo=f"📋 {titulo}", descripcion=txt[:3900], color=color, defer_done=True
        )

    if accion in ("informe_ejecutivo", "inf_alianzas", "inf_calidad", "ind_ver"):
        resumen = embed_zona_resumen(gid, panel if panel in ZONA_META else "gobernanza")
        _audit(inter, panel, accion)
        color = ZONA_META.get(panel, ("", "", C_OK, ""))[2] if panel in ZONA_META else C_F
        return await _resultado(
            inter, titulo="📊 Informe", descripcion=resumen, color=color, defer_done=True
        )

    # —— Crear / registrar genérico ——
    buckets = {
        "pol_crear": "politicas",
        "acta_redactar": "actas",
        "etica_abrir": "casos_etica",
        "est_objetivo": "objetivos",
        "con_crear": "convenios",
        "ali_registrar": "aliados",
        "don_campana": "campanas",
        "seg_evento": "eventos_adversos",
        "mej_plan": "planes_mejora",
        "acr_iniciar": "acreditaciones",
        "aud_lanzar": "auditorias_calidad",
        "cau_procesos": "auditorias_calidad",
        "cau_hc": "auditorias_calidad",
    }

    if accion in _APROBACION:
        item = store.encolar_aprobacion(
            guild_id=gid,
            origen_id=uid,
            origen_zona=panel if panel != "fundador" else "fundador",
            titulo=f"{panel}/{accion}",
            detalle=str(valores)[:500],
            payload={"vals": valores, "accion": accion},
        )
        _audit(inter, panel, accion, item["id"], "en_cola")
        return await _resultado(
            inter,
            titulo="⏳ Enviado al Fundador",
            descripcion=f"La acción **{label}** requiere aprobación.\n**ID:** `{item['id']}`",
            color=C_WARN,
            defer_done=True,
        )

    bkey = buckets.get(accion)
    ref = "—"
    if bkey:
        entry = {
            "id": store.nuevo_id(bkey[:3].upper()),
            "guild_id": gid,
            "ts": int(time.time()),
            "por": uid,
            "estado": "activo",
            **{k: v for k, v in valores.items() if k},
        }
        data.setdefault(bkey, []).insert(0, entry)
        store.save(data)
        ref = entry["id"]

    _audit(inter, panel, accion, ref, "ok", valores)
    color = ZONA_META.get(panel, ("", "", C_OK, ""))[2] if panel in ZONA_META else C_F
    detalle = "\n".join(f"**{k}:** {str(v)[:200]}" for k, v in valores.items() if v) or "Acción completada."
    return await _resultado(
        inter,
        titulo=f"✅ {label}",
        descripcion=(f"**Ref:** `{ref}`\n" if ref != "—" else "") + detalle,
        color=color,
        defer_done=True,
    )


def embed_zona_resumen(gid: int, zona: str) -> str:
    data = store.load()
    if zona == "gobernanza":
        return (
            f"Políticas: **{len(data.get('politicas') or [])}**\n"
            f"Casos ética: **{len(data.get('casos_etica') or [])}**\n"
            f"Objetivos: **{len(data.get('objetivos') or [])}**\n"
            f"Pendientes aprobación: **{len(store.listar_pendientes(gid, 'gobernanza'))}**"
            f"{_banner(gid)}"
        )
    if zona == "interinstitucional":
        return (
            f"Convenios: **{len(data.get('convenios') or [])}**\n"
            f"Aliados: **{len(data.get('aliados') or [])}**\n"
            f"Campañas: **{len(data.get('campanas') or [])}**"
            f"{_banner(gid)}"
        )
    return (
        f"Eventos adversos: **{len(data.get('eventos_adversos') or [])}**\n"
        f"Planes mejora: **{len(data.get('planes_mejora') or [])}**\n"
        f"Acreditaciones: **{len(data.get('acreditaciones') or [])}**"
        f"{_banner(gid)}"
    )


# ═══════════════════════════════════════════════════════════════
# Modales mínimos (solo cuando hace falta texto)
# ═══════════════════════════════════════════════════════════════

_NECESITA_MODAL = {
    "aprobar": [("id", "ID decisión", True), ("comentario", "Comentario", False)],
    "vetar": [("id", "ID decisión", True), ("comentario", "Motivo (obligatorio)", True)],
    "devolver": [("id", "ID decisión", True), ("comentario", "Observaciones", False)],
    "delegar": [
        ("user_id", "ID usuario", True),
        ("poder", "Poder", True),
        ("horas", "Horas", True),
        ("condiciones", "Condiciones", False),
    ],
    "revocar_delegacion": [("id", "ID delegación", True), ("motivo", "Motivo", True)],
    "declarar_emergencia": [
        ("tipo", "Tipo", True),
        ("descripcion", "Descripción", True),
        ("alcance", "Alcance", False),
    ],
    "cerrar_emergencia": [("resumen", "Resumen de cierre", True)],
    "pol_crear": [
        ("titulo", "Título", True),
        ("categoria", "Categoría", True),
        ("contenido", "Contenido", True),
    ],
    "seg_evento": [
        ("servicio", "Servicio", True),
        ("gravedad", "Gravedad", True),
        ("descripcion", "Descripción", True),
    ],
    "con_crear": [
        ("entidad", "Entidad", True),
        ("tipo", "Tipo", True),
        ("objeto", "Objeto", True),
    ],
    "disc_advertir": [("usuario", "ID usuario", True), ("motivo", "Motivo", True)],
    "disc_silenciar": [("usuario", "ID usuario", True), ("duracion", "Minutos", True), ("motivo", "Motivo", True)],
    "disc_expulsar": [("usuario", "ID usuario", True), ("motivo", "Motivo", True)],
    "tal_contratar": [("usuario", "ID usuario", True), ("cargo", "Cargo", True), ("area", "Área", True)],
    "tal_desvincular": [("usuario", "ID usuario", True), ("motivo", "Motivo", True)],
    "fijar_prioridad": [("zona", "Zona", True), ("prioridad", "Prioridad", True), ("plazo", "Plazo", False)],
    "nombrar_cofundador": [("usuario", "ID usuario", True), ("zona", "Zona (gobernanza/interinstitucional/calidad)", True)],
    "destituir_cofundador": [("usuario", "ID usuario", True), ("motivo", "Motivo", True)],
    "reasignar_zona": [("usuario", "ID usuario", True), ("zona", "Zona nueva", True)],
    "anuncio_oficial": [("titulo", "Título", True), ("mensaje", "Mensaje", True)],
    "convocar_consejo": [("fecha", "Fecha", True), ("agenda", "Agenda", True)],
    "sellar_documento": [("tipo", "Tipo", True), ("doc_id", "ID documento", True)],
}

# Default modal for actions not listed
def _fields_for(accion: str) -> List[tuple]:
    if accion in _NECESITA_MODAL:
        return _NECESITA_MODAL[accion]
    return [("detalle", "Detalle", True)]


class AccionModal(ui.Modal):
    def __init__(self, panel: str, accion: str, label: str):
        super().__init__(title=label[:45])
        self.panel = panel
        self.accion = accion
        self.label = label
        self._inputs: List[ui.TextInput] = []
        for i, (cid, lab, req) in enumerate(_fields_for(accion)[:5]):
            tin = ui.TextInput(
                label=lab[:45],
                custom_id=cid,
                required=req,
                style=discord.TextStyle.paragraph if cid in ("contenido", "descripcion", "mensaje", "motivo", "detalle", "resumen", "comentario") else discord.TextStyle.short,
                max_length=1000 if cid in ("contenido", "descripcion", "mensaje") else 200,
            )
            self._inputs.append(tin)
            self.add_item(tin)

    async def on_submit(self, inter: discord.Interaction):
        vals = {t.custom_id: str(t.value).strip() for t in self._inputs}
        for t in self._inputs:
            if t.required and not vals.get(t.custom_id):
                return await inter.response.send_message(
                    embed=discord.Embed(
                        title="❌ Campo obligatorio",
                        description=f"Completa **{t.label}**.",
                        color=C_ERR,
                    ),
                    ephemeral=True,
                )
        await _procesar(inter, panel=self.panel, accion=self.accion, label=self.label, valores=vals)


# ═══════════════════════════════════════════════════════════════
# UI: solo menús
# ═══════════════════════════════════════════════════════════════


class FundadorCatSelect(ui.Select):
    def __init__(self):
        opts = [
            discord.SelectOption(label=cat.split(" ", 1)[-1] if " " in cat else cat, value=cat, emoji=cat.split(" ")[0] if cat[0] > "\u2000" else None)
            for cat in FUNDADOR_MENU
        ]
        # clean emojis in labels
        opts = []
        for cat in FUNDADOR_MENU:
            parts = cat.split(" ", 1)
            emoji = parts[0] if len(parts) > 1 else None
            lab = parts[1] if len(parts) > 1 else cat
            opts.append(discord.SelectOption(label=lab[:100], value=cat, emoji=emoji))
        super().__init__(placeholder="Categoría · Mando General…", options=opts, custom_id="mando:f:cat", row=0)

    async def callback(self, inter: discord.Interaction):
        if not isinstance(inter.user, discord.Member) or not member_es_fundador(inter.user):
            return await inter.response.send_message(
                embed=discord.Embed(title="❌ Sin permiso", description="Solo el **Fundador del Hospital**.", color=C_ERR),
                ephemeral=True,
            )
        cat = self.values[0]
        view = ui.View(timeout=120)
        view.add_item(FundadorAccionSelect(cat))
        await inter.response.send_message(
            embed=discord.Embed(
                title="👑 Mando General",
                description=f"Categoría: **{cat}**\nElige la acción:",
                color=C_F,
            ),
            view=view,
            ephemeral=True,
        )


class FundadorAccionSelect(ui.Select):
    def __init__(self, categoria: str):
        self.categoria = categoria
        acciones = FUNDADOR_MENU.get(categoria, [])
        opts = [
            discord.SelectOption(label=lab[:100], value=val)
            for val, lab in acciones[:25]
        ]
        super().__init__(placeholder="Acción…", options=opts, row=0)

    async def callback(self, inter: discord.Interaction):
        if not isinstance(inter.user, discord.Member) or not member_es_fundador(inter.user):
            return await inter.response.send_message(
                embed=discord.Embed(title="❌ Sin permiso", description="Solo el Fundador.", color=C_ERR),
                ephemeral=True,
            )
        accion = self.values[0]
        label = next((l for v, l in FUNDADOR_MENU.get(self.categoria, []) if v == accion), accion)
        # consultas directas sin modal
        if accion in (
            "ver_pendientes",
            "ver_delegaciones",
            "listar_autoridades",
            "estado_emergencia",
            "auditoria_total",
            "informe_ejecutivo",
            "ver_zona_gob",
            "ver_zona_int",
            "ver_zona_cal",
        ):
            return await _procesar(inter, panel="fundador", accion=accion, label=label)
        await inter.response.send_modal(AccionModal("fundador", accion, label))


class ZonaCatSelect(ui.Select):
    def __init__(self, zona: str):
        self.zona = zona
        menus = ZONA_MENUS[zona]
        opts = []
        for cat in menus:
            parts = cat.split(" ", 1)
            emoji = parts[0] if len(parts) > 1 else None
            lab = parts[1] if len(parts) > 1 else cat
            opts.append(discord.SelectOption(label=lab[:100], value=cat, emoji=emoji))
        super().__init__(
            placeholder="Categoría…",
            options=opts[:25],
            custom_id=f"mando:z:{zona}:cat",
            row=0,
        )

    async def callback(self, inter: discord.Interaction):
        if not isinstance(inter.user, discord.Member) or not (
            member_es_fundador(inter.user) or member_es_cofundador(inter.user, self.zona)
        ):
            return await inter.response.send_message(
                embed=discord.Embed(
                    title="❌ Sin permiso",
                    description="Solo el Co-Fundador de esta zona o el Fundador.",
                    color=C_ERR,
                ),
                ephemeral=True,
            )
        cat = self.values[0]
        view = ui.View(timeout=120)
        view.add_item(ZonaAccionSelect(self.zona, cat))
        titulo, emoji, color, _ = ZONA_META[self.zona]
        await inter.response.send_message(
            embed=discord.Embed(
                title=f"{emoji} {titulo}",
                description=f"Categoría: **{cat}**\nElige la acción:",
                color=color,
            ),
            view=view,
            ephemeral=True,
        )


class ZonaAccionSelect(ui.Select):
    def __init__(self, zona: str, categoria: str):
        self.zona = zona
        self.categoria = categoria
        acciones = ZONA_MENUS[zona].get(categoria, [])
        opts = [discord.SelectOption(label=lab[:100], value=val) for val, lab in acciones[:25]]
        super().__init__(placeholder="Acción…", options=opts, row=0)

    async def callback(self, inter: discord.Interaction):
        if not isinstance(inter.user, discord.Member) or not (
            member_es_fundador(inter.user) or member_es_cofundador(inter.user, self.zona)
        ):
            return await inter.response.send_message(
                embed=discord.Embed(title="❌ Sin permiso", description="Sin permiso.", color=C_ERR),
                ephemeral=True,
            )
        accion = self.values[0]
        label = next((l for v, l in ZONA_MENUS[self.zona].get(self.categoria, []) if v == accion), accion)
        if accion.endswith("_ver") or accion in (
            "ali_directorio",
            "inf_alianzas",
            "inf_calidad",
            "ind_ver",
            "acr_estado",
            "est_ver",
            "disc_historial",
        ):
            return await _procesar(inter, panel=self.zona, accion=accion, label=label)
        await inter.response.send_modal(AccionModal(self.zona, accion, label))


class FundadorPanelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(FundadorCatSelect())


class ZonaPanelView(ui.View):
    def __init__(self, zona: str):
        super().__init__(timeout=None)
        self.zona = zona
        self.add_item(ZonaCatSelect(zona))


def embed_fundador(guild: discord.Guild) -> discord.Embed:
    pend = store.listar_pendientes(guild.id)
    dels = store.listar_delegaciones(guild.id)
    em = store.emergencia_activa(guild.id)
    data = store.load()
    aud = [a for a in (data.get("auditoria") or []) if int(a.get("guild_id") or 0) == guild.id][:5]
    lineas = "\n".join(
        f"• `{a.get('accion')}` — {a.get('actor_name')}" for a in aud
    ) or "_Sin acciones_"
    return discord.Embed(
        title="👑  Mando General · Fundador del Hospital",
        description=(
            f"**Pendientes:** {len(pend)} · **Delegaciones:** {len(dels)}\n"
            f"**Emergencia:** {'🚨 ' + str(em.get('tipo')) if em else '🟢 Normal'}\n"
            f"{_banner(guild.id)}\n"
            f"**Últimas acciones**\n{lineas}\n\n"
            f"Usa el **menú** para actuar. Todo se procesa interno; solo verás el resultado."
        ),
        color=C_F,
    ).set_footer(text=f"Hospital General · {_ts()}")


def embed_zona(guild: discord.Guild, zona: str) -> discord.Embed:
    titulo, emoji, color, rol = ZONA_META[zona]
    return discord.Embed(
        title=f"{emoji}  {titulo}",
        description=(
            f"**Rol:** {rol}\n"
            f"{embed_zona_resumen(guild.id, zona)}\n\n"
            f"Menú de categorías → acción → **solo el resultado**."
        ),
        color=color,
    ).set_footer(text=f"Hospital General · {_ts()}")


def registrar(bot: commands.Bot) -> None:
    try:
        bot.add_view(FundadorPanelView())
        for z in ZONA_MENUS:
            bot.add_view(ZonaPanelView(z))
    except Exception:
        pass

    try:
        bot.tree.remove_command("enviar_panel_mando")
    except Exception:
        pass

    @bot.tree.command(
        name="enviar_panel_mando",
        description="[Fundador] Publica paneles de autoridades (menús, solo resultado)",
    )
    @app_commands.describe(canal="Canal", cual="Panel a enviar")
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
            return await inter.response.send_message(
                embed=discord.Embed(title="❌", description="Solo en servidor.", color=C_ERR),
                ephemeral=True,
            )
        if not member_es_fundador(inter.user):
            return await inter.response.send_message(
                embed=discord.Embed(
                    title="❌ Sin permiso",
                    description="Solo el **Fundador del Hospital**.",
                    color=C_ERR,
                ),
                ephemeral=True,
            )
        await inter.response.defer(ephemeral=True)
        val = cual.value
        enviados = []
        try:
            if val in ("fundador", "todos"):
                await canal.send(embed=embed_fundador(inter.guild), view=FundadorPanelView())
                enviados.append("Fundador")
            for z in ("gobernanza", "interinstitucional", "calidad"):
                if val in (z, "todos"):
                    await canal.send(embed=embed_zona(inter.guild, z), view=ZonaPanelView(z))
                    enviados.append(z)
        except Exception as e:
            return await inter.followup.send(
                embed=discord.Embed(title="❌ Error", description=str(e), color=C_ERR),
                ephemeral=True,
            )
        _audit(inter, "Fundador", "enviar_panel_mando", canal.mention, "ok", {"cual": val})
        await inter.followup.send(
            embed=discord.Embed(
                title="✅ Paneles publicados",
                description=f"{canal.mention}\n{', '.join(enviados)}",
                color=C_OK,
            ),
            ephemeral=True,
        )

    print("[paneles_mando] OK — menús + proceso interno + solo resultado")
