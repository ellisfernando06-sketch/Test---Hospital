# -*- coding: utf-8 -*-
"""
UI paneles autoridades — solo menús, proceso interno, solo resultado.
Sin consejo / junta / comité de consejo.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import discord
from discord import ui

import paneles_autoridades_config as cfg
import paneles_permisos_auth as auth
import paneles_store as store

# owner_id del panel abierto → anti-uso ajeno
_PANEL_OWNER: Dict[str, int] = {}


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")


def _bar(pct: int) -> str:
    pct = max(0, min(100, int(pct)))
    filled = pct // 12
    return "▰" * filled + "▱" * (8 - filled) + f" {pct}%"


def _banner(gid: int) -> str:
    em = store.emergencia(gid)
    if not em:
        return ""
    return (
        f"\n🔴 **EMERGENCIA ACTIVA** · {em.get('tipo', '—')}\n"
        f"{str(em.get('descripcion', ''))[:150]}\n"
    )


async def _solo_resultado(
    inter: discord.Interaction,
    *,
    titulo: str,
    desc: str,
    color: int = cfg.COLOR_OK,
) -> None:
    emb = discord.Embed(title=titulo, description=desc, color=color)
    emb.set_footer(text=f"Hospital General · {_ts()}")
    try:
        if inter.response.is_done():
            await inter.followup.send(embed=emb, ephemeral=True)
        else:
            await inter.response.send_message(embed=emb, ephemeral=True)
    except Exception:
        try:
            await inter.followup.send(embed=emb, ephemeral=True)
        except Exception:
            pass


def embed_principal(member: discord.Member, panel: str) -> discord.Embed:
    gid = member.guild.id
    em = store.emergencia(gid)
    pend = store.pendientes(gid)
    dels = store.delegaciones_activas(gid)
    aud = [
        a
        for a in (store.load().get("auditoria") or [])
        if int(a.get("guild_id") or 0) == gid
    ][:5]
    lineas = "\n".join(
        f"• `{a.get('accion')}` — {a.get('actor_name')}" for a in aud
    ) or "_Sin acciones recientes_"

    if panel == "fundador":
        color, titulo, sub = cfg.COLOR_FUNDADOR, "👑  Mando General", "*Fundador del Hospital General*"
        extra = (
            f"**Pendientes:** {len(pend)} · **Delegaciones:** {len(dels)}\n"
            f"**Emergencia:** {'🔴 ' + str(em.get('tipo')) if em else '🟢 Normal'}\n"
            f"**Zonas:** Gobernanza · Interinstitucional · Calidad\n"
        )
    elif panel == "gobernanza":
        color, titulo, sub = cfg.COLOR_GOBERNANZA, "⚖️  Orden y Legitimidad", "*Co-Fundador · Gobernanza*"
        extra = (
            f"**Políticas:** {len(store.list_items('politicas', gid))} · "
            f"**Ética abiertos:** {len([x for x in store.list_items('casos_etica', gid) if x.get('estado')=='abierto'])}\n"
            f"**Objetivos:** {len(store.list_items('objetivos', gid))}\n"
        )
    elif panel == "interinstitucional":
        color, titulo, sub = cfg.COLOR_INTER, "🤝  Puentes y Alianzas", "*Co-Fundador · Interinstitucional*"
        extra = (
            f"**Convenios:** {len(store.list_items('convenios', gid))} · "
            f"**Aliados:** {len(store.list_items('aliados', gid))}\n"
            f"**Campañas:** {len(store.list_items('campanas', gid))}\n"
        )
    else:
        color, titulo, sub = cfg.COLOR_CALIDAD, "🏅  Excelencia y Seguridad", "*Co-Fundador · Calidad*"
        extra = (
            f"**Eventos adversos:** {len(store.list_items('eventos_adversos', gid))} · "
            f"**Planes:** {len(store.list_items('planes_mejora', gid))}\n"
            f"**Acreditaciones:** {len(store.list_items('acreditaciones', gid))}\n"
        )

    emb = discord.Embed(
        title=titulo,
        description=(
            f"{sub}\n**Titular:** {member.mention}\n"
            f"{_banner(gid)}\n{extra}\n"
            f"**Últimas acciones**\n{lineas}\n\n"
            f"Elige una **categoría** en el menú. "
            f"El bot procesa en interno y solo muestra el **resultado**."
        ),
        color=color,
    )
    try:
        emb.set_thumbnail(url=member.display_avatar.url)
    except Exception:
        pass
    emb.set_footer(text=f"{titulo.split('  ')[-1] if '  ' in titulo else titulo} · {_ts()}")
    return emb


# ── Catálogos de menús (sin consejo) ──────────────────────────

CATS: Dict[str, List[Tuple[str, str, str]]] = {
    # value, label, description
    "fundador": [
        ("decisiones", "Decisiones", "Aprobar, vetar o devolver propuestas"),
        ("delegaciones", "Delegaciones", "Poderes temporales a Co-Fundadores"),
        ("autoridades", "Autoridades", "Nombrar, destituir o reasignar"),
        ("comunicacion", "Comunicación oficial", "Anuncios y documentos oficiales"),
        ("emergencia", "Emergencia", "Declarar o cerrar alerta institucional"),
        ("supervision", "Supervisión", "Zonas, auditoría y prioridades"),
        ("informes", "Informes", "Informe ejecutivo por periodo"),
    ],
    "gobernanza": [
        ("politicas", "Políticas y reglamentos", "Crear, publicar o derogar"),
        ("actas", "Actas y registros", "Redactar y consultar actas"),
        ("etica", "Ética", "Casos éticos y resolución"),
        ("disciplina", "Disciplina", "Advertir, silenciar, expulsar (inferiores)"),
        ("talento", "Talento humano", "Contratar, evaluar, desvincular"),
        ("auditoria", "Auditoría interna", "Lanzar y cerrar auditorías"),
        ("estrategia", "Planeación estratégica", "Objetivos y avance"),
        ("transparencia", "Transparencia y legal", "Informes y riesgos legales"),
    ],
    "interinstitucional": [
        ("convenios", "Convenios", "Crear, renovar o terminar"),
        ("aliados", "Aliados", "Directorio de entidades"),
        ("reuniones", "Reuniones institucionales", "Agendar con aliados"),
        ("donaciones", "Donaciones y campañas", "Campañas y aportes"),
        ("financiamiento", "Financiamiento", "Solicitudes de fondos"),
        ("comunicacion", "Comunicación y prensa", "Comunicados y medios"),
        ("comunidad", "Comunidad y RSE", "Jornadas comunitarias"),
        ("referencias", "Referencias", "Derivaciones a otros hospitales"),
        ("informes", "Informes", "Resumen de alianzas"),
    ],
    "calidad": [
        ("seguridad", "Seguridad del paciente", "Eventos adversos y alertas"),
        ("auditorias", "Auditorías", "Procesos e historias clínicas"),
        ("mejora", "Mejora continua", "Planes y acciones correctivas"),
        ("acreditaciones", "Acreditaciones", "Procesos y simulacros"),
        ("indicadores", "Indicadores", "Semáforo por servicio"),
        ("satisfaccion", "Satisfacción", "Encuestas a usuarios"),
        ("comites", "Comités asistenciales", "Calidad, infecciones, ética asistencial"),
        ("protocolos", "Protocolos", "Aprobar o suspender"),
        ("informes", "Informes", "Informe de calidad"),
    ],
}

ACCIONES: Dict[str, Dict[str, List[Tuple[str, str, str]]]] = {
    "fundador": {
        "decisiones": [
            ("ver_pend", "Ver pendientes", "Lista de propuestas en cola"),
            ("aprobar", "Aprobar decisión", "Ejecuta y avisa al origen"),
            ("vetar", "Vetar decisión", "Cancela con motivo obligatorio"),
            ("devolver", "Devolver con observaciones", "Regresa para corrección"),
        ],
        "delegaciones": [
            ("ver_del", "Ver delegaciones activas", "Con vencimientos"),
            ("delegar", "Delegar poder temporal", "Caduca solo"),
            ("revocar_del", "Revocar delegación", "Retira el poder al instante"),
        ],
        "autoridades": [
            ("listar_aut", "Listar autoridades", "Quién ocupa cada cargo"),
            ("nombrar", "Nombrar Co-Fundador", "Un titular por zona"),
            ("destituir", "Destituir Co-Fundador", "Con motivo y confirmación"),
            ("reasignar", "Reasignar zona", "Cambia de zona a un Co-Fundador"),
        ],
        "comunicacion": [
            ("anuncio", "Anuncio oficial", "Publica con sello del Fundador"),
            ("sellar", "Sellar documento", "Marca documento como oficial"),
            ("prioridad", "Fijar prioridad estratégica", "Visible en panel de zona"),
        ],
        "emergencia": [
            ("estado_em", "Estado de emergencia", "Consulta alerta actual"),
            ("abrir_em", "Declarar emergencia", "Banner en los 4 paneles"),
            ("cerrar_em", "Cerrar emergencia", "Archiva el informe"),
        ],
        "supervision": [
            ("ver_gob", "Ver zona Gobernanza", "Solo lectura"),
            ("ver_int", "Ver zona Interinstitucional", "Solo lectura"),
            ("ver_cal", "Ver zona Calidad", "Solo lectura"),
            ("auditoria", "Auditoría total", "Bitácora filtrable"),
        ],
        "informes": [
            ("inf_ejec", "Informe ejecutivo", "Resumen de las tres zonas"),
        ],
    },
    "gobernanza": {
        "politicas": [
            ("pol_crear", "Crear política", "Queda como borrador"),
            ("pol_ver", "Ver políticas", "Por estado"),
            ("pol_pub", "Publicar política", "Puede requerir aprobación"),
            ("pol_der", "Derogar política", "Con motivo"),
        ],
        "actas": [
            ("acta_red", "Redactar acta", "Registro institucional"),
            ("acta_ver", "Consultar actas", "Listado reciente"),
        ],
        "etica": [
            ("et_abrir", "Abrir caso", "Con gravedad"),
            ("et_ver", "Ver casos", "Por estado"),
            ("et_res", "Resolver caso", "Dictamen y medida"),
        ],
        "disciplina": [
            ("disc_adv", "Advertir", "Sobre inferiores de jerarquía"),
            ("disc_sil", "Silenciar", "Timeout con límite"),
            ("disc_exp", "Expulsar", "Solo inferiores; confirmación"),
            ("disc_his", "Ver historial", "Sanciones previas"),
        ],
        "talento": [
            ("tal_con", "Contratar", "Asigna rol de personal"),
            ("tal_des", "Desvincular", "Quita roles de personal"),
            ("tal_eva", "Evaluar desempeño", "Calificación 1–5"),
            ("tal_asc", "Ascender o trasladar", "Cambio de cargo"),
        ],
        "auditoria": [
            ("aud_lan", "Lanzar auditoría", "Área y plazo"),
            ("aud_hal", "Registrar hallazgo", "Severidad"),
            ("aud_cer", "Cerrar auditoría", "Con conclusión"),
        ],
        "estrategia": [
            ("est_obj", "Nuevo objetivo", "Meta e indicador"),
            ("est_ava", "Actualizar avance", "Porcentaje"),
            ("est_ver", "Ver objetivos", "Listado"),
        ],
        "transparencia": [
            ("tra_inf", "Informe transparencia", "Requiere aprobación"),
            ("tra_rie", "Riesgo legal", "Nivel y mitigación"),
            ("tra_con", "Revisar contrato", "Dictamen"),
        ],
    },
    "interinstitucional": {
        "convenios": [
            ("con_crear", "Crear convenio", "Aviso a Gobernanza"),
            ("con_ver", "Ver convenios", "Con vencimientos"),
            ("con_ren", "Renovar convenio", "Nueva vigencia"),
            ("con_ter", "Terminar convenio", "Con motivo"),
            ("con_may", "Proponer convenio mayor", "Aprobación Fundador"),
        ],
        "aliados": [
            ("ali_reg", "Registrar aliado", "Al directorio"),
            ("ali_dir", "Ver directorio", "Por categoría"),
        ],
        "reuniones": [
            ("reu_age", "Agendar reunión", "Con aliado"),
        ],
        "donaciones": [
            ("don_cam", "Lanzar campaña", "Meta y destino"),
            ("don_reg", "Registrar donación", "Suma a la meta"),
            ("don_agr", "Agradecimiento", "Al donante"),
        ],
        "financiamiento": [
            ("fin_sol", "Solicitud de fondos", "Puede requerir aprobación"),
        ],
        "comunicacion": [
            ("com_of", "Comunicado oficial", "Crisis requiere aprobación"),
            ("com_pre", "Gestión de prensa", "Registro de medio"),
        ],
        "comunidad": [
            ("comu_jor", "Jornada comunitaria", "Aviso a Calidad"),
        ],
        "referencias": [
            ("ref_hos", "Referencia a hospital", "Prioridad y nota"),
        ],
        "informes": [
            ("inf_ali", "Informe de alianzas", "Resumen del periodo"),
        ],
    },
    "calidad": {
        "seguridad": [
            ("seg_evt", "Evento adverso", "Aviso si grave"),
            ("seg_inv", "Abrir investigación", "Causa raíz"),
            ("seg_ale", "Alerta de seguridad", "Canal de alertas"),
        ],
        "auditorias": [
            ("cau_pro", "Auditar procesos", "Departamento"),
            ("cau_hc", "Auditar historias clínicas", "Muestra"),
            ("cau_ver", "Ver auditorías", "Por estado"),
        ],
        "mejora": [
            ("mej_plan", "Plan de mejora", "Acción y plazo"),
            ("mej_cer", "Cerrar acción", "Con evidencia"),
            ("mej_ver", "Ver planes abiertos", "Vencimientos"),
        ],
        "acreditaciones": [
            ("acr_ini", "Iniciar acreditación", "Aviso al Fundador"),
            ("acr_est", "Estado por entidad", "Barras de avance"),
            ("acr_sim", "Programar simulacro", "Fecha y evaluadores"),
        ],
        "indicadores": [
            ("ind_ver", "Ver indicadores", "Semáforo"),
        ],
        "satisfaccion": [
            ("sat_enc", "Lanzar encuesta", "1 a 5 estrellas"),
        ],
        "comites": [
            ("com_con", "Convocar comité asistencial", "Calidad / infecciones / ética"),
        ],
        "protocolos": [
            ("pro_apr", "Aprobar protocolo", "Queda vigente"),
            ("pro_sus", "Suspender protocolo", "Aprobación Fundador"),
        ],
        "informes": [
            ("inf_cal", "Informe de calidad", "Resumen del periodo"),
        ],
    },
}

# Acciones que van a cola del Fundador
_APROB = {
    "disc_exp",  # expulsión puede ir directa si inferior; aún registramos
    "tra_inf",
    "con_may",
    "fin_sol",
    "pro_sus",
    "pol_pub",
}

# Solo lectura / sin modal
_SOLO_LECTURA = {
    "ver_pend", "ver_del", "listar_aut", "estado_em", "auditoria", "inf_ejec",
    "ver_gob", "ver_int", "ver_cal",
    "pol_ver", "acta_ver", "et_ver", "est_ver", "disc_his",
    "con_ver", "ali_dir", "inf_ali",
    "cau_ver", "mej_ver", "acr_est", "ind_ver", "inf_cal",
}


async def ejecutar_accion(
    inter: discord.Interaction,
    panel: str,
    accion: str,
    label: str,
    valores: Optional[dict] = None,
) -> None:
    valores = valores or {}
    if not inter.guild or not isinstance(inter.user, discord.Member):
        return await _solo_resultado(
            inter, titulo="❌ Error", desc="Solo en el servidor.", color=cfg.COLOR_ERR
        )

    # Seguridad: rol + dueño del panel
    if not auth.puede_usar_panel(inter.user, panel):
        store.auditar(
            inter.guild.id, inter.user.id, str(inter.user), panel, accion, resultado="denegado"
        )
        return await _solo_resultado(
            inter,
            titulo="❌ Acceso denegado",
            desc="No posees la autoridad requerida o tu rol cambió.",
            color=cfg.COLOR_ERR,
        )

    try:
        if not inter.response.is_done():
            await inter.response.defer(ephemeral=True)
    except Exception:
        pass

    gid = inter.guild.id
    uid = inter.user.id
    color = {
        "fundador": cfg.COLOR_FUNDADOR,
        "gobernanza": cfg.COLOR_GOBERNANZA,
        "interinstitucional": cfg.COLOR_INTER,
        "calidad": cfg.COLOR_CALIDAD,
    }.get(panel, cfg.COLOR_OK)

    # —— Lecturas ——
    if accion == "ver_pend":
        pend = store.pendientes(gid)
        txt = (
            "\n".join(
                f"`{p['id']}` **{p.get('titulo')}** · zona `{p.get('zona')}`"
                for p in pend[:20]
            )
            or "No hay decisiones pendientes."
        )
        store.auditar(gid, uid, str(inter.user), "Fundador", accion)
        return await _solo_resultado(inter, titulo="📋 Pendientes", desc=txt, color=color)

    if accion == "ver_del":
        dels = store.delegaciones_activas(gid)
        txt = (
            "\n".join(
                f"`{d['id']}` <@{d['user_id']}> · **{d.get('poder')}** · <t:{d.get('vence_ts')}:R>"
                for d in dels[:20]
            )
            or "Sin delegaciones activas."
        )
        store.auditar(gid, uid, str(inter.user), "Fundador", accion)
        return await _solo_resultado(inter, titulo="🔑 Delegaciones", desc=txt, color=color)

    if accion == "listar_aut":
        lines = []
        for key, nombre in [
            (cfg.KEY_FUNDADOR, "Fundador del Hospital"),
            (cfg.KEY_GOBERNANZA, "Co-Fundador · Gobernanza"),
            (cfg.KEY_INTER, "Co-Fundador · Interinstitucional"),
            (cfg.KEY_CALIDAD, "Co-Fundador · Calidad"),
        ]:
            menciones = []
            try:
                import permisos

                for m in inter.guild.members:
                    if permisos.member_tiene_alguna_key(m, key):
                        menciones.append(m.mention)
            except Exception:
                pass
            lines.append(f"**{nombre}:** {', '.join(menciones) or '_Vacante_'}")
        store.auditar(gid, uid, str(inter.user), "Fundador", accion)
        return await _solo_resultado(inter, titulo="👑 Autoridades", desc="\n".join(lines), color=color)

    if accion == "estado_em":
        em = store.emergencia(gid)
        txt = (
            f"🔴 **{em.get('tipo')}**\n{em.get('descripcion')}"
            if em
            else "🟢 Sin emergencia activa."
        )
        store.auditar(gid, uid, str(inter.user), "Fundador", accion)
        return await _solo_resultado(
            inter, titulo="Emergencia", desc=txt, color=cfg.COLOR_EMERGENCIA if em else cfg.COLOR_OK
        )

    if accion == "auditoria":
        aud = [
            a
            for a in (store.load().get("auditoria") or [])
            if int(a.get("guild_id") or 0) == gid
        ][:25]
        txt = (
            "\n".join(
                f"`{a.get('id')}` **{a.get('accion')}** · {a.get('actor_name')} · {a.get('resultado')}"
                for a in aud
            )
            or "_Vacío_"
        )
        store.auditar(gid, uid, str(inter.user), panel, accion)
        return await _solo_resultado(inter, titulo="🔎 Auditoría", desc=txt[:3900], color=color)

    if accion in ("inf_ejec", "inf_ali", "inf_cal", "ind_ver"):
        desc = embed_principal(inter.user, panel if panel != "fundador" else "gobernanza").description or "—"
        store.auditar(gid, uid, str(inter.user), panel, accion)
        return await _solo_resultado(inter, titulo="📊 Informe", desc=desc[:3900], color=color)

    if accion in ("ver_gob", "ver_int", "ver_cal"):
        z = {"ver_gob": "gobernanza", "ver_int": "interinstitucional", "ver_cal": "calidad"}[accion]
        emb = embed_principal(inter.user, z)
        store.auditar(gid, uid, str(inter.user), "Fundador", accion, z)
        return await _solo_resultado(
            inter, titulo=emb.title or z, desc=emb.description or "—", color=emb.color.value if emb.color else color
        )

    # Listados por bucket
    buckets_ver = {
        "pol_ver": "politicas",
        "acta_ver": "actas",
        "et_ver": "casos_etica",
        "est_ver": "objetivos",
        "con_ver": "convenios",
        "ali_dir": "aliados",
        "cau_ver": "auditorias_cal",
        "mej_ver": "planes_mejora",
        "acr_est": "acreditaciones",
    }
    if accion in buckets_ver:
        items = store.list_items(buckets_ver[accion], gid)
        txt = (
            "\n".join(
                f"`{i.get('id')}` {i.get('titulo') or i.get('nombre') or i.get('detalle') or '—'}"
                for i in items
            )
            or "_Sin registros_"
        )
        store.auditar(gid, uid, str(inter.user), panel, accion)
        return await _solo_resultado(inter, titulo="📋 Listado", desc=txt[:3900], color=color)

    # Decisiones fundador
    if accion in ("aprobar", "vetar", "devolver"):
        pid = (valores.get("id") or "").strip()
        com = (valores.get("comentario") or valores.get("motivo") or "").strip()
        if not pid:
            return await _solo_resultado(
                inter, titulo="❌ Datos incompletos", desc="Falta el ID.", color=cfg.COLOR_ERR
            )
        if accion == "vetar" and not com:
            return await _solo_resultado(
                inter, titulo="❌ Motivo obligatorio", desc="Indica el motivo del veto.", color=cfg.COLOR_ERR
            )
        estado = {"aprobar": "aprobado", "vetar": "vetado", "devolver": "devuelto"}[accion]
        it = store.resolver_pendiente(pid, estado, com)
        if not it:
            return await _solo_resultado(
                inter, titulo="❌ No encontrado", desc=f"`{pid}` no existe.", color=cfg.COLOR_ERR
            )
        store.auditar(gid, uid, str(inter.user), "Fundador", f"decision:{estado}", pid)
        try:
            u = inter.client.get_user(int(it.get("origen_id") or 0))
            if u:
                await u.send(
                    embed=discord.Embed(
                        title=f"Decisión {estado}",
                        description=f"**{it.get('titulo')}**\n{com or '—'}",
                        color=cfg.COLOR_OK if estado == "aprobado" else cfg.COLOR_ERR,
                    )
                )
        except Exception:
            pass
        return await _solo_resultado(
            inter,
            titulo=f"✅ Decisión {estado}",
            desc=f"**ID:** `{pid}`\n**Título:** {it.get('titulo')}\n**Nota:** {com or '—'}",
            color=cfg.COLOR_OK if estado == "aprobado" else cfg.COLOR_ERR,
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
            return await _solo_resultado(
                inter, titulo="❌ Datos inválidos", desc="Usuario u horas incorrectos.", color=cfg.COLOR_ERR
            )
        data = store.load()
        item = {
            "id": store.nid("DEL"),
            "guild_id": gid,
            "user_id": tid,
            "poder": valores.get("poder") or "general",
            "vence_ts": int(time.time()) + max(1, horas) * 3600,
            "revocada": False,
            "por": uid,
        }
        data.setdefault("delegaciones", []).insert(0, item)
        store.save(data)
        store.auditar(gid, uid, str(inter.user), "Fundador", "delegar", str(tid))
        return await _solo_resultado(
            inter,
            titulo="✅ Poder delegado",
            desc=f"**A:** <@{tid}>\n**Poder:** {item['poder']}\n**Horas:** {horas}\n**ID:** `{item['id']}`",
            color=color,
        )

    if accion == "abrir_em":
        data = store.load()
        data.setdefault("emergencia", {})[str(gid)] = {
            "activa": True,
            "tipo": valores.get("tipo") or "institucional",
            "descripcion": valores.get("descripcion") or "",
            "alcance": valores.get("alcance") or "hospital",
            "por": uid,
            "ts": int(time.time()),
        }
        store.save(data)
        store.auditar(gid, uid, str(inter.user), "Fundador", "emergencia_on")
        return await _solo_resultado(
            inter,
            titulo="🔴 Emergencia declarada",
            desc=f"**Tipo:** {valores.get('tipo')}\n{valores.get('descripcion')}",
            color=cfg.COLOR_EMERGENCIA,
        )

    if accion == "cerrar_em":
        data = store.load()
        em = data.setdefault("emergencia", {}).get(str(gid))
        if em:
            em["activa"] = False
            em["cierre"] = valores.get("resumen") or ""
            em["cierre_ts"] = int(time.time())
        store.save(data)
        store.auditar(gid, uid, str(inter.user), "Fundador", "emergencia_off")
        return await _solo_resultado(
            inter, titulo="🟢 Emergencia cerrada", desc=valores.get("resumen") or "Archivada.", color=cfg.COLOR_OK
        )

    # Disciplina: solo inferiores
    if accion in ("disc_adv", "disc_sil", "disc_exp"):
        raw = str(valores.get("usuario") or valores.get("user_id") or "").strip()
        try:
            tid = int(raw.replace("<@", "").replace(">", "").replace("!", ""))
        except Exception:
            return await _solo_resultado(
                inter, titulo="❌ Usuario inválido", desc="Indica un ID o mención válida.", color=cfg.COLOR_ERR
            )
        objetivo = inter.guild.get_member(tid)
        if not objetivo:
            return await _solo_resultado(
                inter, titulo="❌ No encontrado", desc="El miembro no está en el servidor.", color=cfg.COLOR_ERR
            )
        ok, msg = auth.puede_actuar_sobre(inter.user, objetivo)
        if not ok:
            store.auditar(gid, uid, str(inter.user), panel, accion, str(tid), "denegado")
            return await _solo_resultado(inter, titulo="❌ No permitido", desc=msg, color=cfg.COLOR_ERR)

        motivo = valores.get("motivo") or "Sin motivo"
        # Intentar enlazar sanción existente
        try:
            # registro mínimo
            store.add_item(
                "sanciones_panel",
                gid,
                uid,
                tipo=accion,
                objetivo_id=tid,
                motivo=motivo,
                estado="registrado",
            )
        except Exception:
            pass
        store.auditar(gid, uid, str(inter.user), panel, accion, str(tid), "ok")
        tipo_txt = {"disc_adv": "Advertencia", "disc_sil": "Silencio", "disc_exp": "Expulsión"}[accion]
        return await _solo_resultado(
            inter,
            titulo=f"✅ {tipo_txt} registrada",
            desc=f"**Miembro:** {objetivo.mention}\n**Motivo:** {motivo}\n_Usa también `/sancion` para aplicar la medida formal del bot._",
            color=color,
        )

    # Aprobación cola
    if accion in _APROB and accion not in ("disc_exp",):
        item = store.encolar(
            gid, uid, panel, f"{panel}/{accion}", str(valores)[:500], {"vals": valores}
        )
        store.auditar(gid, uid, str(inter.user), panel, accion, item["id"], "en_cola")
        return await _solo_resultado(
            inter,
            titulo="⏳ Enviado al Fundador",
            desc=f"**{label}** requiere aprobación.\n**ID:** `{item['id']}`",
            color=cfg.COLOR_WARN,
        )

    # Alta genérica
    bucket_map = {
        "pol_crear": "politicas",
        "acta_red": "actas",
        "et_abrir": "casos_etica",
        "est_obj": "objetivos",
        "con_crear": "convenios",
        "ali_reg": "aliados",
        "don_cam": "campanas",
        "seg_evt": "eventos_adversos",
        "mej_plan": "planes_mejora",
        "acr_ini": "acreditaciones",
        "aud_lan": "auditorias_cal",
        "cau_pro": "auditorias_cal",
        "cau_hc": "auditorias_cal",
    }
    ref = "—"
    if accion in bucket_map:
        entry = store.add_item(bucket_map[accion], gid, uid, **valores)
        ref = entry["id"]
        # Enlaces cruzados simples
        if accion == "con_crear":
            store.add_item(
                "enlaces",
                gid,
                uid,
                origen="interinstitucional",
                destino="gobernanza",
                tipo="revision_legal",
                ref=ref,
                estado="pendiente",
            )
        if accion == "seg_evt" and "grave" in str(valores.get("gravedad", "")).lower():
            store.encolar(gid, uid, "calidad", f"Evento grave {ref}", str(valores)[:300])

    store.auditar(gid, uid, str(inter.user), panel, accion, ref, "ok", valores)
    detalle = "\n".join(f"**{k}:** {str(v)[:180]}" for k, v in valores.items() if v) or "Completado."
    return await _solo_resultado(
        inter,
        titulo=f"✅ {label}",
        desc=(f"**Ref:** `{ref}`\n" if ref != "—" else "") + detalle,
        color=color,
    )


# ── Modales ───────────────────────────────────────────────────

_MODAL_FIELDS: Dict[str, List[Tuple[str, str, bool]]] = {
    "aprobar": [("id", "ID decisión", True), ("comentario", "Comentario", False)],
    "vetar": [("id", "ID decisión", True), ("motivo", "Motivo", True)],
    "devolver": [("id", "ID decisión", True), ("comentario", "Observaciones", True)],
    "delegar": [
        ("user_id", "ID del Co-Fundador", True),
        ("poder", "Poder (ej. gobernanza)", True),
        ("horas", "Horas (1–168)", True),
    ],
    "revocar_del": [("id", "ID delegación", True), ("motivo", "Motivo", True)],
    "abrir_em": [("tipo", "Tipo", True), ("descripcion", "Descripción", True)],
    "cerrar_em": [("resumen", "Resumen de cierre", True)],
    "pol_crear": [("titulo", "Título", True), ("contenido", "Contenido", True)],
    "seg_evt": [
        ("servicio", "Servicio", True),
        ("gravedad", "Gravedad", True),
        ("descripcion", "Descripción", True),
    ],
    "con_crear": [("entidad", "Entidad", True), ("tipo", "Tipo", True), ("objeto", "Objeto", True)],
    "disc_adv": [("usuario", "ID usuario", True), ("motivo", "Motivo", True)],
    "disc_sil": [("usuario", "ID usuario", True), ("duracion", "Minutos", True), ("motivo", "Motivo", True)],
    "disc_exp": [("usuario", "ID usuario", True), ("motivo", "Motivo", True)],
    "nombrar": [("user_id", "ID usuario", True), ("zona", "Zona", True)],
    "destituir": [("user_id", "ID usuario", True), ("motivo", "Motivo", True)],
    "anuncio": [("titulo", "Título", True), ("mensaje", "Mensaje", True)],
}


class AccionModal(ui.Modal):
    def __init__(self, panel: str, accion: str, label: str, owner_id: int):
        super().__init__(title=label[:45])
        self.panel = panel
        self.accion = accion
        self.label = label
        self.owner_id = owner_id
        fields = _MODAL_FIELDS.get(accion, [("detalle", "Detalle", True)])
        self._ins: List[ui.TextInput] = []
        for cid, lab, req in fields[:5]:
            long_f = cid in ("contenido", "descripcion", "mensaje", "motivo", "detalle", "resumen")
            t = ui.TextInput(
                label=lab[:45],
                custom_id=cid,
                required=req,
                style=discord.TextStyle.paragraph if long_f else discord.TextStyle.short,
                max_length=1000 if long_f else 120,
            )
            self._ins.append(t)
            self.add_item(t)

    async def on_submit(self, inter: discord.Interaction):
        if inter.user.id != self.owner_id:
            return await inter.response.send_message(
                embed=discord.Embed(
                    title="❌ Panel ajeno",
                    description="Este panel pertenece a otra persona.",
                    color=cfg.COLOR_ERR,
                ),
                ephemeral=True,
            )
        vals = {t.custom_id: str(t.value).strip() for t in self._ins}
        for t in self._ins:
            if t.required and not vals.get(t.custom_id):
                return await inter.response.send_message(
                    embed=discord.Embed(
                        title="❌ Campo obligatorio",
                        description=f"Completa **{t.label}**.",
                        color=cfg.COLOR_ERR,
                    ),
                    ephemeral=True,
                )
        await ejecutar_accion(inter, self.panel, self.accion, self.label, vals)


# ── Selects ───────────────────────────────────────────────────


class CatSelect(ui.Select):
    def __init__(self, panel: str, owner_id: int):
        self.panel = panel
        self.owner_id = owner_id
        opts = [
            discord.SelectOption(label=lab[:100], value=val, description=desc[:100])
            for val, lab, desc in CATS.get(panel, [])[:25]
        ]
        super().__init__(
            placeholder="Selecciona una categoría",
            options=opts,
            custom_id=f"auth_{panel}_cat_{owner_id}"[:100],
            row=0,
        )

    async def callback(self, inter: discord.Interaction):
        if inter.user.id != self.owner_id:
            return await inter.response.send_message(
                "❌ Este panel no es tuyo.", ephemeral=True
            )
        if not isinstance(inter.user, discord.Member) or not auth.puede_usar_panel(
            inter.user, self.panel
        ):
            return await inter.response.send_message(
                embed=discord.Embed(
                    title="❌ Acceso denegado",
                    description="No posees la autoridad requerida",
                    color=cfg.COLOR_ERR,
                ),
                ephemeral=True,
            )
        cat = self.values[0]
        view = ui.View(timeout=180)
        view.add_item(AccionSelect(self.panel, cat, self.owner_id))
        view.add_item(NavBtn("inicio", self.panel, self.owner_id))
        view.add_item(NavBtn("cerrar", self.panel, self.owner_id))
        lab = next((l for v, l, _ in CATS[self.panel] if v == cat), cat)
        await inter.response.send_message(
            embed=discord.Embed(
                title=f"📂 {lab}",
                description="Selecciona una **acción**:",
                color=embed_principal(inter.user, self.panel).color,
            ),
            view=view,
            ephemeral=True,
        )


class AccionSelect(ui.Select):
    def __init__(self, panel: str, cat: str, owner_id: int):
        self.panel = panel
        self.cat = cat
        self.owner_id = owner_id
        acts = ACCIONES.get(panel, {}).get(cat, [])
        opts = [
            discord.SelectOption(label=lab[:100], value=val, description=desc[:100])
            for val, lab, desc in acts[:25]
        ]
        super().__init__(placeholder="Selecciona una acción", options=opts, row=0)

    async def callback(self, inter: discord.Interaction):
        if inter.user.id != self.owner_id:
            return await inter.response.send_message("❌ Panel ajeno.", ephemeral=True)
        if not isinstance(inter.user, discord.Member) or not auth.puede_usar_panel(
            inter.user, self.panel
        ):
            return await inter.response.send_message(
                embed=discord.Embed(
                    title="❌ Acceso denegado",
                    description="No posees la autoridad requerida",
                    color=cfg.COLOR_ERR,
                ),
                ephemeral=True,
            )
        accion = self.values[0]
        label = next(
            (l for v, l, _ in ACCIONES.get(self.panel, {}).get(self.cat, []) if v == accion),
            accion,
        )
        if accion in _SOLO_LECTURA:
            return await ejecutar_accion(inter, self.panel, accion, label)
        await inter.response.send_modal(
            AccionModal(self.panel, accion, label, self.owner_id)
        )


class NavBtn(ui.Button):
    def __init__(self, kind: str, panel: str, owner_id: int):
        labels = {"inicio": ("🏠 Inicio", discord.ButtonStyle.secondary), "cerrar": ("✖️ Cerrar", discord.ButtonStyle.danger)}
        lab, style = labels[kind]
        super().__init__(label=lab, style=style, row=1)
        self.kind = kind
        self.panel = panel
        self.owner_id = owner_id

    async def callback(self, inter: discord.Interaction):
        if inter.user.id != self.owner_id:
            return await inter.response.send_message("❌ Panel ajeno.", ephemeral=True)
        if self.kind == "cerrar":
            return await inter.response.send_message(
                embed=discord.Embed(title="Panel cerrado", color=cfg.COLOR_OK),
                ephemeral=True,
            )
        if not isinstance(inter.user, discord.Member):
            return
        view = PanelView(self.panel, inter.user.id)
        await inter.response.send_message(
            embed=embed_principal(inter.user, self.panel), view=view, ephemeral=True
        )


class PanelView(ui.View):
    def __init__(self, panel: str, owner_id: int):
        super().__init__(timeout=600)
        self.panel = panel
        self.owner_id = owner_id
        self.add_item(CatSelect(panel, owner_id))
        self.add_item(NavBtn("cerrar", panel, owner_id))
