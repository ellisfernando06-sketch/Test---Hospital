# -*- coding: utf-8 -*-
"""
Exámenes de postulación a Direcciones (RP — nivel accesible).
/examen_direccion canal_log → menú de direcciones → MD a quienes tienen el rol.
Log con puntuación + Aprobar / Rechazar (motivo si no llega al mínimo).
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import discord
from discord import app_commands, ui
from discord.ext import commands

try:
    import permisos
except Exception:
    permisos = None

try:
    import roles_store
except Exception:
    roles_store = None

_DATA = Path(__file__).resolve().parent / "examen_direccion_data.json"
_MINIMO = 60  # % mínimo (RP)
_PREGUNTAS_POR_EXAMEN = 6

_DIRECCIONES: List[Tuple[str, str, str, int]] = [
    ("CANCILLER", "Cancillería", "🏛️", 0x2C3E50),
    ("VICE_CANCILLER", "Vice Cancillería", "🏛️", 0x34495E),
    ("DIR_GENERAL", "Dirección General", "🖥️", 0x1A5276),
    ("DIR_MEDICO", "Dirección Médica", "🩺", 0x1ABC9C),
    ("DIR_ENFERMERIA", "Dirección de Enfermería", "💉", 0x3498DB),
    ("DIR_RRHH", "Dirección de RRHH", "👥", 0x9B59B6),
    ("DIR_DOCENCIA", "Dirección de Docencia", "📚", 0x8E44AD),
    ("DIR_LOGISTICA", "Dirección de Logística", "📦", 0xE67E22),
    ("JEFE_SEGURIDAD", "Dirección de Seguridad", "🛡️", 0x2C3E50),
]

# Preguntas de RP (claras, no académicas): (pregunta, [A,B,C,D], índice correcta)
_BANCO: Dict[str, List[Tuple[str, List[str], int]]] = {
    "CANCILLER": [
        (
            "En el roleplay del hospital, ¿qué representa principalmente el Canciller?",
            [
                "Solo un médico de urgencias",
                "La autoridad institucional que coordina y representa al hospital",
                "Un visitante con rango de color",
                "Únicamente el bot del servidor",
            ],
            1,
        ),
        (
            "Si dos direcciones discuten en OOC, lo correcto es:",
            [
                "Insultarse en el canal general",
                "Hablar con respeto, usar los canales de staff y seguir el organigrama",
                "Cerrar el servidor",
                "Ignorar siempre las normas",
            ],
            1,
        ),
        (
            "Una decisión importante del Canciller debería:",
            [
                "Hacerse solo por chat privado sin dejar rastro",
                "Quedar clara y, si hace falta, documentada para el staff",
                "Publicarse solo con memes",
                "Nunca comunicarse",
            ],
            1,
        ),
        (
            "¿Quién está por encima del Canciller en el organigrama típico del servidor?",
            [
                "Un residente",
                "Fundador / Owner (y autoridades del servidor)",
                "Cualquier visitante",
                "El bot de tickets",
            ],
            1,
        ),
        (
            "En una crisis de rol grande, el Canciller debería:",
            [
                "Desaparecer del servidor",
                "Ayudar a ordenar la situación y apoyar a las direcciones",
                "Banear a todos sin mirar",
                "Solo mirar desde el chat de memes",
            ],
            1,
        ),
        (
            "El Vice Canciller sirve para:",
            [
                "Reemplazar al Owner para siempre",
                "Apoyar al Canciller y cubrir cuando haga falta",
                "Solo poner embeds bonitos",
                "Gestionar únicamente la economía",
            ],
            1,
        ),
        (
            "Si alguien filtra información privada de una reunión de staff:",
            [
                "Se premia",
                "Se trata como falta seria según el reglamento",
                "No pasa nada",
                "Se publica otra vez en general",
            ],
            1,
        ),
        (
            "Representar al hospital ante otros implica:",
            [
                "Decir cualquier cosa en nombre del server",
                "Cuidar la imagen y seguir lo acordado con las autoridades",
                "Pelear con otros servidores",
                "No responder nunca",
            ],
            1,
        ),
    ],
    "VICE_CANCILLER": [
        (
            "El Vice Canciller actúa sobre todo cuando:",
            [
                "Quiere mandar sobre el Canciller",
                "El Canciller no está o le pide apoyo",
                "Un visitante se lo ordena",
                "Nunca puede hacer nada",
            ],
            1,
        ),
        (
            "Si el Canciller corrige una decisión tuya:",
            [
                "La ignoras",
                "La respetas y sigues el organigrama",
                "Sancionas al Canciller",
                "Cierras el ticket del Canciller",
            ],
            1,
        ),
        (
            "En un conflicto entre dos áreas, lo ideal es:",
            [
                "Ponerse de un solo lado sin escuchar",
                "Mediar con calma y buscar una solución justa",
                "Borrar los canales",
                "Banear a ambos directores",
            ],
            1,
        ),
        (
            "La información sensible de Cancillería:",
            [
                "Se comparte en el chat general",
                "Se cuida y solo se comparte con quien debe saberla",
                "Se vende a otros jugadores",
                "Se borra siempre al instante",
            ],
            1,
        ),
        (
            "Trabajar con la Dirección General significa:",
            [
                "Competir y no hablarse",
                "Coordinarse para que el hospital funcione bien",
                "Solo pelear en staff",
                "Ignorar la operación del día a día",
            ],
            1,
        ),
        (
            "Si un director cuestiona tu cargo:",
            [
                "Responder con insultos",
                "Explicar el organigrama con respeto y escalar si hace falta",
                "Renunciar en silencio",
                "Banearlo sin proceso",
            ],
            1,
        ),
        (
            "Un buen Vice Canciller en RP:",
            [
                "Solo aparece para ponerse el rol",
                "Está disponible, comunica y apoya al equipo",
                "Nunca entra a los canales de dirección",
                "Ignora las normas del server",
            ],
            1,
        ),
        (
            "En una emergencia de rol, priorizas:",
            [
                "Tu escena personal",
                "Orden, seguridad de canales y ayudar al staff",
                "Cerrar todos los tickets sin mirar",
                "Salirte del servidor",
            ],
            1,
        ),
    ],
    "DIR_GENERAL": [
        (
            "La Dirección General se enfoca en:",
            [
                "Solo curar pacientes en quirófano",
                "Coordinar que las direcciones trabajen juntas",
                "Solo poner roles de color",
                "Solo hacer anuncios de fiestas",
            ],
            1,
        ),
        (
            "Si Médica y Logística no se entienden:",
            [
                "Dejar que peleen en público",
                "Hablar con ambas y buscar un acuerdo claro",
                "Cerrar una de las dos áreas",
                "Ignorar el problema",
            ],
            1,
        ),
        (
            "Un director lleva mucho tiempo inactivo sin avisar:",
            [
                "No pasa nada nunca",
                "Se le contacta y se sigue el reglamento de inactividad",
                "Se le promociona",
                "Se le da ban sin hablar",
            ],
            1,
        ),
        (
            "Un cambio de reglas que afecta a todo el hospital debería:",
            [
                "Publicarse sin avisar a nadie",
                "Comunicarse bien a las áreas y al staff",
                "Quedarse solo en un MD",
                "Ocultarse del resto",
            ],
            1,
        ),
        (
            "En un incidente grande, Dirección General:",
            [
                "Se desconecta",
                "Ayuda a organizar y mantiene la operación en marcha",
                "Solo mira el chat de memes",
                "Banear a todos los pacientes",
            ],
            1,
        ),
        (
            "Reportar a Cancillería sirve para:",
            [
                "Quejarse sin datos",
                "Informar de lo importante con claridad",
                "Difamar a otros",
                "Nunca informar",
            ],
            1,
        ),
        (
            "Delegar a un jefe de servicio significa:",
            [
                "Abandonar el área por completo",
                "Confiar tareas pero seguir pendiente del resultado",
                "Prohibir que nadie más trabaje",
                "Pasarle el cargo de Director para siempre",
            ],
            1,
        ),
        (
            "Lo que NO es función típica de Dirección General:",
            [
                "Coordinar áreas",
                "Hacer de médico tratante en cada paciente del servidor",
                "Ayudar en crisis operativas",
                "Cuidar que se cumplan políticas del hospital",
            ],
            1,
        ),
    ],
    "DIR_MEDICO": [
        (
            "En una emergencia de rol (código), lo importante es:",
            [
                "Que cada uno improvise sin hablar",
                "Organizar quién hace qué y cuidar la escena",
                "Cerrar el canal de voz",
                "Salirse del rol",
            ],
            1,
        ),
        (
            "Un residente se equivoca en el protocolo. ¿Qué haces?",
            [
                "Humillarlo en público",
                "Corregirlo con respeto y enseñarle",
                "Ignorarlo",
                "Expulsarlo del server sin hablar",
            ],
            1,
        ),
        (
            "Trabajar con enfermería en una escena significa:",
            [
                "Ignorar al personal de enfermería",
                "Coordinar órdenes y cuidar al paciente de rol",
                "Prohibir que enfermería entre",
                "Solo hablar por OOC de forma tóxica",
            ],
            1,
        ),
        (
            "Si hay pelea OOC entre médicos en medio del rol:",
            [
                "Seguir discutiendo en la escena",
                "Separar IC/OOC y resolver fuera de la escena",
                "Banear a los dos sin más",
                "Borrar el canal del hospital",
            ],
            1,
        ),
        (
            "Un buen Director Médico en RP:",
            [
                "Solo tiene el rol y no organiza nada",
                "Apoya al equipo, da ejemplo y mantiene el orden clínico del rol",
                "Nunca responde tickets ni mensajes",
                "Ignora a residentes e internos",
            ],
            1,
        ),
        (
            "La historia clínica en rol debería tener al menos:",
            [
                "Solo un emoji",
                "Qué le pasa al paciente, qué se hizo y quién atendió",
                "Nada, nunca se anota",
                "Solo el color del rol del médico",
            ],
            1,
        ),
        (
            "Respecto a Docencia y certificaciones:",
            [
                "Competir y bloquear todo",
                "Apoyar que la gente se forme bien para el rol médico",
                "Ignorar por completo las capacitaciones",
                "Dar certificados sin ningún criterio",
            ],
            1,
        ),
        (
            "Si un médico no quiere atender sin motivo de rol:",
            [
                "Dejar la urgencia vacía siempre",
                "Hablar el tema y asegurar cobertura según las normas del área",
                "Cerrar el hospital",
                "Sancionar al paciente",
            ],
            1,
        ),
    ],
    "DIR_ENFERMERIA": [
        (
            "¿A quién se atiende primero en una escena con varios pacientes?",
            [
                "Al que llegó primero siempre",
                "Al que está más grave o necesita más cuidado",
                "Al que tiene el rol más alto de Discord",
                "Al que pide más en el chat",
            ],
            1,
        ),
        (
            "Antes de dar un medicamento en rol conviene:",
            [
                "Inventar la dosis",
                "Confirmar qué se pidió, a quién y registrarlo",
                "No preguntar nada",
                "Dárselo a otro paciente",
            ],
            1,
        ),
        (
            "Si un auxiliar se equivoca en el protocolo:",
            [
                "Reírse y no decir nada",
                "Corregir, explicar y avisar si es grave",
                "Banearlo al momento",
                "Ignorarlo siempre",
            ],
            1,
        ),
        (
            "Coordinar con el médico en una escena es:",
            [
                "Cambiar las órdenes sin avisar",
                "Seguir el plan, avisar cambios y preguntar si hay duda",
                "Nunca hablar con el médico",
                "Solo pelear en OOC",
            ],
            1,
        ),
        (
            "Si falta personal en el turno:",
            [
                "Abandonar a los pacientes",
                "Reorganizar tareas y pedir apoyo si hace falta",
                "Cerrar todo en silencio",
                "Dar rol de enfermero a cualquier visitante sin proceso",
            ],
            1,
        ),
        (
            "Los datos del paciente en RP:",
            [
                "Se publican en el chat general",
                "Se cuidan; solo se comparten con quien atiende",
                "Se inventan para troll",
                "No importan nunca",
            ],
            1,
        ),
        (
            "Liderar enfermería en una crisis de rol implica:",
            [
                "Gritar sin organizar",
                "Repartir tareas claras al equipo",
                "Salirse de la escena",
                "Dejar que cada uno haga lo que quiera",
            ],
            1,
        ),
        (
            "Formar a auxiliares es algo que:",
            [
                "No le importa a nadie",
                "Debe impulsar la Dirección de Enfermería (con Docencia si aplica)",
                "Solo hace Seguridad",
                "Solo hace el Owner",
            ],
            1,
        ),
    ],
    "DIR_RRHH": [
        (
            "Al contratar o aceptar a alguien, lo justo es:",
            [
                "Elegir solo amigos sin mirar nada",
                "Revisar perfil, normas y dejar registro del proceso",
                "Vender el puesto",
                "Aceptar a cualquiera sin leer",
            ],
            1,
        ),
        (
            "Si llega una queja formal contra un jefe:",
            [
                "Borrarla",
                "Recibirla, investigar con imparcialidad y resolver con registro",
                "Publicarla en anuncios para drama",
                "Ignorarla si el jefe es popular",
            ],
            1,
        ),
        (
            "Un nuevo miembro debería recibir:",
            [
                "Nada",
                "Normas básicas, canales y qué se espera de su cargo",
                "Admin del servidor al instante",
                "Solo un rol de color sin explicación",
            ],
            1,
        ),
        (
            "Inactividad sin avisar durante mucho tiempo:",
            [
                "Se premia",
                "Se aplica el reglamento (avisos / medidas)",
                "Se ignora siempre",
                "Se promociona al cargo superior",
            ],
            1,
        ),
        (
            "Los expedientes de personal:",
            [
                "Son públicos para todo el servidor",
                "Solo los ven quienes tienen permiso",
                "Se mandan por MD a todos",
                "Se publican en general",
            ],
            1,
        ),
        (
            "Un despido en el hospital de rol debería:",
            [
                "Ser un insulto sin motivo",
                "Tener causa clara y aviso formal",
                "Hacerse solo con un emoji",
                "Decidirse por voto de visitantes",
            ],
            1,
        ),
        (
            "Si un postulado miente en su experiencia de rol:",
            [
                "Se aprueba igual",
                "Se rechaza y se deja constancia según normas",
                "Se le da Director General",
                "Se ignora",
            ],
            1,
        ),
        (
            "RRHH y Cancillería en un caso grave deberían:",
            [
                "Ocultarse información",
                "Comunicarse con hechos y proponer soluciones",
                "Pelear en público",
                "No hablar nunca",
            ],
            1,
        ),
    ],
    "DIR_DOCENCIA": [
        (
            "Una certificación en el hospital debería basarse en:",
            [
                "Solo ser amigo del director",
                "Estudiar, evaluar y cumplir el proceso del área",
                "Pagar por fuera del rol",
                "Estar un minuto en un canal de voz",
            ],
            1,
        ),
        (
            "Si alguien copia en un examen de capacitación:",
            [
                "Se le aprueba igual",
                "Se anula o se aplica la norma de Docencia",
                "Se le sube la nota",
                "Se le da el rol de Director",
            ],
            1,
        ),
        (
            "El material de estudio debería ser:",
            [
                "Imposible de entender a propósito",
                "Claro y acorde a las normas de RP del hospital",
                "Solo memes sin contenido",
                "Secreto para siempre",
            ],
            1,
        ),
        (
            "Docencia y Dirección Médica deberían:",
            [
                "Evitarse mutuamente",
                "Coordinarse para que lo enseñado sirva en el rol clínico",
                "Pelear por los canales",
                "Ignorar las certificaciones",
            ],
            1,
        ),
        (
            "Guardar quién aprobó un curso sirve para:",
            [
                "Nada",
                "Tener orden: fecha, resultado y quién formó",
                "Borrar evidencias",
                "Trollear al staff",
            ],
            1,
        ),
        (
            "Un instructor favorece siempre a su círculo. ¿Qué haces?",
            [
                "Lo premias",
                "Revisas el caso y corriges si hubo injusticia",
                "Cierras Docencia para siempre",
                "Ignoras las quejas",
            ],
            1,
        ),
        (
            "El objetivo de capacitar es:",
            [
                "Solo llenar el servidor de roles",
                "Que la gente rolee mejor y con más calidad",
                "Sancionar por diversión",
                "Evitar que nadie entre al hospital",
            ],
            1,
        ),
        (
            "Emitir un certificado sin evaluación:",
            [
                "Está bien siempre",
                "No es correcto si el protocolo pide examen o práctica",
                "Es obligatorio cada día",
                "Solo lo hace Seguridad",
            ],
            1,
        ),
    ],
    "DIR_LOGISTICA": [
        (
            "En una emergencia, ¿qué insumos van primero?",
            [
                "Lo que pida el más ruidoso",
                "Lo más importante para atender y mantener el hospital",
                "Nada de stock nunca",
                "Solo decoración",
            ],
            1,
        ),
        (
            "Si el inventario no cuadra:",
            [
                "Se inventan números",
                "Se revisa, se corrige y se deja registro",
                "Se ignora",
                "Se culpa al bot sin mirar",
            ],
            1,
        ),
        (
            "Con Dirección Médica, Logística debería:",
            [
                "No hablar nunca",
                "Anticipar pedidos y tener canales claros de solicitud",
                "Negar todo siempre",
                "Entregar sin anotar nada",
            ],
            1,
        ),
        (
            "Un área pide material urgente fuera de lo normal:",
            [
                "Siempre se niega",
                "Se evalúa, se entrega si procede y luego se regulariza",
                "Se da a cualquiera sin control",
                "Se borra el pedido",
            ],
            1,
        ),
        (
            "El almacén restringido debería tener:",
            [
                "Acceso libre para todos",
                "Control de quién entra y qué se mueve",
                "Ningún tipo de control",
                "Solo un emoji de candado sin reglas",
            ],
            1,
        ),
        (
            "Si se pierde material:",
            [
                "Se oculta",
                "Se investiga con calma y se evita que vuelva a pasar",
                "Se culpa a alguien al azar",
                "Se cierra el hospital",
            ],
            1,
        ),
        (
            "Reportar a Dirección General sirve para:",
            [
                "Solo mandar memes",
                "Avisar niveles de stock y problemas reales",
                "Nunca informar",
                "Quejarse sin datos",
            ],
            1,
        ),
        (
            "Organizar turnos de logística busca:",
            [
                "Quemar a una sola persona 24/7",
                "Que haya cobertura y el equipo no se agote",
                "Dejar el área vacía",
                "Prohibir entrar al almacén",
            ],
            1,
        ),
    ],
    "JEFE_SEGURIDAD": [
        (
            "Si hay un intruso en zona restringida:",
            [
                "Se ignora",
                "Se identifica, se sigue el protocolo y se reporta",
                "Se banea sin mirar el rol",
                "Se huye de la escena",
            ],
            1,
        ),
        (
            "El uso de fuerza en RP de seguridad debe ser:",
            [
                "Lo máximo siempre",
                "Proporcional y justificado en la escena",
                "Aleatorio por diversión",
                "Prohibido en todo caso",
            ],
            1,
        ),
        (
            "En un incidente violento cerca de pacientes:",
            [
                "Bloquear a todos los médicos",
                "Asegurar la zona y dejar que atiendan con seguridad",
                "Evacuar sin avisar a nadie",
                "Cerrar el rol médico",
            ],
            1,
        ),
        (
            "Un informe de seguridad debería incluir:",
            [
                "Solo opiniones",
                "Qué pasó, cuándo y qué se hizo",
                "Nada escrito",
                "Insultos a los involucrados",
            ],
            1,
        ),
        (
            "Si un guardia abusa de su rol:",
            [
                "Se le cubre",
                "Se investiga y se corrige o sanciona según normas",
                "Se le asciende",
                "Se ignoran las quejas",
            ],
            1,
        ),
        (
            "El acceso a quirófano o áreas sensibles:",
            [
                "Es libre para cualquiera",
                "Se verifica quién es y por qué entra",
                "Está prohibido para todo el staff médico",
                "No se controla nunca",
            ],
            1,
        ),
        (
            "Una amenaza OOC en un canal del hospital:",
            [
                "Se trata como si fuera solo RP",
                "Se separa de IC, se documenta y se escala al staff",
                "Se responde con más amenazas",
                "Se borra sin dejar rastro y ya",
            ],
            1,
        ),
        (
            "Entrenar al equipo de seguridad sirve para:",
            [
                "Solo rellenar tiempo",
                "Que conozcan protocolos y actúen con criterio en el rol",
                "Generar caos a propósito",
                "Ignorar el reglamento",
            ],
            1,
        ),
    ],
}


def _load() -> dict:
    if not _DATA.exists():
        return {"sesiones": {}, "logs": {}}
    try:
        return json.loads(_DATA.read_text(encoding="utf-8"))
    except Exception:
        return {"sesiones": {}, "logs": {}}


def _save(data: dict) -> None:
    try:
        _DATA.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception as e:
        print(f"[examen_direccion] save: {e}")


def _es_staff(m: discord.Member) -> bool:
    if m.guild_permissions.administrator or m.guild_permissions.manage_guild:
        return True
    if m.guild and m.id == m.guild.owner_id:
        return True
    if permisos is None:
        return False
    try:
        return permisos.member_tiene_alguna_key(
            m,
            "FUNDADOR_OWNER",
            "CO_OWNER",
            "OWNER",
            "CANCILLER",
            "VICE_CANCILLER",
            "ADMIN_JEFE",
            "ADMIN",
            "DIR_GENERAL",
            "DIR_RRHH",
        )
    except Exception:
        return False


def _rol_por_key(guild: discord.Guild, key: str) -> Optional[discord.Role]:
    if roles_store is not None:
        try:
            rid = roles_store.obtener_id_key(key)
            if rid:
                r = guild.get_role(int(rid))
                if r:
                    return r
        except Exception:
            pass
    hints = {
        "CANCILLER": ("canciller",),
        "VICE_CANCILLER": ("vice canciller", "vicecanciller"),
        "DIR_GENERAL": ("director general",),
        "DIR_MEDICO": ("director médico", "director medico"),
        "DIR_ENFERMERIA": ("director de enfermería", "director de enfermeria", "dir enfermer"),
        "DIR_RRHH": ("director de rrhh", "dir rrhh", "recursos humanos"),
        "DIR_DOCENCIA": ("director de docencia", "dir docencia"),
        "DIR_LOGISTICA": ("director de logística", "director de logistica", "dir logist"),
        "JEFE_SEGURIDAD": ("jefe de seguridad", "director de seguridad"),
    }
    for r in guild.roles:
        n = (r.name or "").lower()
        for h in hints.get(key, ()):
            if h in n:
                if key == "CANCILLER" and "vice" in n:
                    continue
                return r
    return None


def _miembros_con_rol(guild: discord.Guild, key: str) -> List[discord.Member]:
    rol = _rol_por_key(guild, key)
    if not rol:
        return []
    return [m for m in guild.members if not m.bot and rol in m.roles]


def _preguntas_para(key: str) -> List[Tuple[str, List[str], int]]:
    banco = list(_BANCO.get(key) or [])
    if not banco:
        return []
    start = int(time.time()) % max(1, len(banco))
    rot = banco[start:] + banco[:start]
    return rot[:_PREGUNTAS_POR_EXAMEN]


def _embed_inicio(dir_nombre: str, emoji: str, color: int, total: int) -> discord.Embed:
    return discord.Embed(
        title=f"{emoji}  Examen de postulación · {dir_nombre}",
        description=(
            f"Evaluación de **roleplay** del Hospital General.\n\n"
            f"• **{total}** preguntas sencillas sobre el área\n"
            f"• Mínimo para que el staff pueda **aprobar:** **{_MINIMO}%**\n"
            f"• El resultado llega a tu MD y al canal de log\n\n"
            f"Pulsa **Comenzar examen** cuando quieras."
        ),
        color=color,
    ).set_footer(text="Hospital General · Postulación a Direcciones")


def _embed_pregunta(
    dir_nombre: str, emoji: str, color: int, idx: int, total: int, texto: str
) -> discord.Embed:
    return discord.Embed(
        title=f"{emoji}  {dir_nombre} · Pregunta {idx + 1}/{total}",
        description=f"**{texto}**",
        color=color,
    ).set_footer(text="Elige una opción")


def _embed_resultado(
    dir_nombre: str, emoji: str, score: int, total: int, pct: int
) -> discord.Embed:
    ok = pct >= _MINIMO
    return discord.Embed(
        title=f"{emoji}  Resultado · {dir_nombre}",
        description=(
            f"**Puntuación:** {score}/{total}  ·  **{pct}%**\n"
            f"**Mínimo:** {_MINIMO}%\n\n"
            + (
                "Alcanzaste el mínimo. El staff puede **aprobar** en el log."
                if ok
                else "No llegaste al mínimo. El staff **rechazará** con un motivo."
            )
        ),
        color=0x2ECC71 if ok else 0xE74C3C,
    ).set_footer(text="Hospital General · Resultado de postulación")


class RespuestaSelect(ui.Select):
    def __init__(self, session_id: str, opciones: List[str], correcta: int):
        self.session_id = session_id
        self.correcta = correcta
        opts = []
        for i, op in enumerate(opciones):
            opts.append(
                discord.SelectOption(
                    label=f"{chr(65 + i)}. {op[:90]}",
                    value=str(i),
                    description=(op[90:190] if len(op) > 90 else None),
                )
            )
        super().__init__(
            placeholder="Selecciona tu respuesta…",
            min_values=1,
            max_values=1,
            options=opts,
        )

    async def callback(self, interaction: discord.Interaction):
        data = _load()
        ses = data.get("sesiones", {}).get(self.session_id)
        if not ses:
            return await interaction.response.send_message(
                "❌ Sesión expirada.", ephemeral=True
            )
        if int(ses.get("user_id") or 0) != interaction.user.id:
            return await interaction.response.send_message(
                "❌ Este examen no es tuyo.", ephemeral=True
            )
        if ses.get("terminado"):
            return await interaction.response.send_message(
                "❌ Ya terminaste este examen.", ephemeral=True
            )

        eleccion = int(self.values[0])
        idx = int(ses.get("idx") or 0)
        preguntas = ses.get("preguntas") or []
        if idx >= len(preguntas):
            return await interaction.response.send_message(
                "❌ Error de índice.", ephemeral=True
            )

        if eleccion == int(preguntas[idx][2]):
            ses["score"] = int(ses.get("score") or 0) + 1
        ses["idx"] = idx + 1
        data["sesiones"][self.session_id] = ses
        _save(data)

        await interaction.response.defer()
        await _continuar_examen(interaction, self.session_id)


class PreguntaView(ui.View):
    def __init__(self, session_id: str, opciones: List[str], correcta: int):
        super().__init__(timeout=600)
        self.add_item(RespuestaSelect(session_id, opciones, correcta))


class ComenzarView(ui.View):
    def __init__(self, session_id: str):
        super().__init__(timeout=900)
        self.session_id = session_id

    @ui.button(label="Comenzar examen", style=discord.ButtonStyle.primary, emoji="📋")
    async def comenzar(self, interaction: discord.Interaction, button: ui.Button):
        data = _load()
        ses = data.get("sesiones", {}).get(self.session_id)
        if not ses:
            return await interaction.response.send_message(
                "❌ Sesión no encontrada.", ephemeral=True
            )
        if int(ses.get("user_id") or 0) != interaction.user.id:
            return await interaction.response.send_message(
                "❌ Este examen no es tuyo.", ephemeral=True
            )
        await interaction.response.defer()
        await _continuar_examen(interaction, self.session_id)


async def _continuar_examen(interaction: discord.Interaction, session_id: str):
    data = _load()
    ses = data.get("sesiones", {}).get(session_id)
    if not ses:
        return
    idx = int(ses.get("idx") or 0)
    preguntas = ses.get("preguntas") or []
    total = len(preguntas)
    dir_nombre = ses.get("dir_nombre") or "Dirección"
    emoji = ses.get("emoji") or "📋"
    color = int(ses.get("color") or 0x5D6D7E)

    if idx >= total:
        score = int(ses.get("score") or 0)
        pct = int(round(100 * score / total)) if total else 0
        ses["terminado"] = True
        ses["pct"] = pct
        data["sesiones"][session_id] = ses
        _save(data)

        emb = _embed_resultado(dir_nombre, emoji, score, total, pct)
        try:
            await interaction.edit_original_response(embed=emb, view=None)
        except Exception:
            try:
                await interaction.followup.send(embed=emb)
            except Exception:
                pass
        try:
            await interaction.user.send(embed=emb)
        except Exception:
            pass
        await _enviar_log_resultado(interaction.client, ses, score, total, pct)
        return

    q = preguntas[idx]
    texto, opciones, correcta = q[0], q[1], q[2]
    emb = _embed_pregunta(dir_nombre, emoji, color, idx, total, texto)
    view = PreguntaView(session_id, opciones, correcta)
    try:
        await interaction.edit_original_response(embed=emb, view=view)
    except Exception:
        try:
            await interaction.followup.send(embed=emb, view=view)
        except Exception:
            pass


async def _enviar_log_resultado(
    bot: commands.Bot, ses: dict, score: int, total: int, pct: int
):
    canal_id = int(ses.get("log_channel_id") or 0)
    if not canal_id:
        return
    canal = bot.get_channel(canal_id)
    if not isinstance(canal, discord.TextChannel):
        return

    uid = int(ses.get("user_id") or 0)
    dir_nombre = ses.get("dir_nombre") or "—"
    emoji = ses.get("emoji") or "📋"
    ok_min = pct >= _MINIMO

    emb = discord.Embed(
        title=f"{emoji}  Log de examen · {dir_nombre}",
        description=(
            f"**Candidato:** <@{uid}> (`{uid}`)\n"
            f"**Puntuación:** **{score}/{total}** · **{pct}%**\n"
            f"**Mínimo:** {_MINIMO}%\n"
            f"**Estado:** "
            + (
                "✅ Llegó al mínimo → puedes **Aprobar**"
                if ok_min
                else "❌ No llegó al mínimo → **Rechazar** con motivo"
            )
        ),
        color=0xF1C40F if ok_min else 0xE74C3C,
    ).set_footer(text="Hospital General · Postulaciones")

    view = LogExamenView(
        session_id=str(ses.get("id") or ""),
        user_id=uid,
        pct=pct,
        dir_nombre=dir_nombre,
    )
    try:
        await canal.send(embed=emb, view=view)
    except Exception as e:
        print(f"[examen_direccion] log: {e}")


class LogExamenView(ui.View):
    def __init__(
        self,
        session_id: str = "",
        user_id: int = 0,
        pct: int = 0,
        dir_nombre: str = "",
    ):
        super().__init__(timeout=None)
        self.session_id = session_id
        self.user_id = user_id
        self.pct = pct
        self.dir_nombre = dir_nombre

    @ui.button(
        label="Aprobar postulación",
        style=discord.ButtonStyle.success,
        emoji="✅",
        custom_id="examen_dir:aprobar",
    )
    async def aprobar(self, inter: discord.Interaction, button: ui.Button):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en servidor.", ephemeral=True
            )
        if not _es_staff(inter.user):
            return await inter.response.send_message(
                "❌ Solo staff.", ephemeral=True
            )

        data = _load()
        ses = data.get("sesiones", {}).get(self.session_id) or {}
        pct = int(ses.get("pct") or self.pct or 0)
        if pct < _MINIMO:
            return await inter.response.send_message(
                f"❌ Tiene **{pct}%** (mínimo {_MINIMO}%). Debes **Rechazar** con motivo.",
                ephemeral=True,
            )

        uid = int(ses.get("user_id") or self.user_id)
        dir_n = ses.get("dir_nombre") or self.dir_nombre
        member = inter.guild.get_member(uid)
        if member:
            try:
                await member.send(
                    embed=discord.Embed(
                        title="✅ Postulación aprobada",
                        description=(
                            f"Tu examen de **{dir_n}** fue **aprobado** "
                            f"por {inter.user.mention}.\n"
                            f"Puntuación: **{pct}%**."
                        ),
                        color=0x2ECC71,
                    ).set_footer(text="Hospital General")
                )
            except Exception:
                pass

        emb = inter.message.embeds[0].copy() if inter.message.embeds else discord.Embed()
        emb.color = 0x2ECC71
        emb.title = f"✅ Aprobado · {dir_n}"
        emb.description = (emb.description or "") + f"\n\n**Aprobado por** {inter.user.mention}"
        await inter.response.edit_message(embed=emb, view=None)

    @ui.button(
        label="Rechazar",
        style=discord.ButtonStyle.danger,
        emoji="❌",
        custom_id="examen_dir:rechazar",
    )
    async def rechazar(self, inter: discord.Interaction, button: ui.Button):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en servidor.", ephemeral=True
            )
        if not _es_staff(inter.user):
            return await inter.response.send_message(
                "❌ Solo staff.", ephemeral=True
            )

        parent = self

        class MotivoModal(ui.Modal, title="Motivo del rechazo"):
            motivo = ui.TextInput(
                label="Motivo",
                style=discord.TextStyle.paragraph,
                required=True,
                max_length=500,
                placeholder="Explica el rechazo (obligatorio)…",
            )

            async def on_submit(self, modal_inter: discord.Interaction):
                data = _load()
                ses = data.get("sesiones", {}).get(parent.session_id) or {}
                uid = int(ses.get("user_id") or parent.user_id)
                dir_n = ses.get("dir_nombre") or parent.dir_nombre
                pct = int(ses.get("pct") or parent.pct or 0)
                motivo_txt = str(self.motivo.value).strip()

                member = (
                    modal_inter.guild.get_member(uid) if modal_inter.guild else None
                )
                if member:
                    try:
                        await member.send(
                            embed=discord.Embed(
                                title="❌ Postulación rechazada",
                                description=(
                                    f"Tu examen de **{dir_n}** fue **rechazado**.\n"
                                    f"**Puntuación:** {pct}% (mín. {_MINIMO}%)\n\n"
                                    f"**Motivo:** {motivo_txt}"
                                ),
                                color=0xE74C3C,
                            ).set_footer(text="Hospital General")
                        )
                    except Exception:
                        pass

                emb = (
                    modal_inter.message.embeds[0].copy()
                    if modal_inter.message and modal_inter.message.embeds
                    else discord.Embed()
                )
                emb.color = 0xE74C3C
                emb.title = f"❌ Rechazado · {dir_n}"
                emb.description = (
                    (emb.description or "")
                    + f"\n\n**Rechazado por** {modal_inter.user.mention}\n"
                    f"**Motivo:** {motivo_txt}"
                )
                await modal_inter.response.edit_message(embed=emb, view=None)

        await inter.response.send_modal(MotivoModal())


class DireccionSelect(ui.Select):
    def __init__(self, log_channel: discord.TextChannel):
        self.log_channel = log_channel
        options = [
            discord.SelectOption(
                label=nombre,
                value=key,
                emoji=emoji,
                description=f"Examen RP · {nombre}"[:100],
            )
            for key, nombre, emoji, _ in _DIRECCIONES
        ]
        super().__init__(
            placeholder="Selecciona la dirección…",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        key = self.values[0]
        meta = next((d for d in _DIRECCIONES if d[0] == key), None)
        if not meta:
            return await interaction.response.send_message(
                "❌ Dirección inválida.", ephemeral=True
            )
        _, nombre, emoji, color = meta
        guild = interaction.guild
        assert guild

        miembros = _miembros_con_rol(guild, key)
        preguntas = _preguntas_para(key)
        if not preguntas:
            return await interaction.response.send_message(
                "❌ Sin preguntas para esta dirección.", ephemeral=True
            )
        if not miembros:
            return await interaction.response.send_message(
                f"⚠️ No hay miembros con el rol de **{nombre}**.\n"
                f"Revisa el organigrama / keys de roles.",
                ephemeral=True,
            )

        await interaction.response.defer(ephemeral=True)
        data = _load()
        data.setdefault("sesiones", {})
        enviados = fallos = 0

        for m in miembros:
            sid = f"{m.id}_{key}_{int(time.time())}"
            data["sesiones"][sid] = {
                "id": sid,
                "user_id": m.id,
                "dir_key": key,
                "dir_nombre": nombre,
                "emoji": emoji,
                "color": color,
                "log_channel_id": self.log_channel.id,
                "preguntas": [[p[0], p[1], p[2]] for p in preguntas],
                "idx": 0,
                "score": 0,
                "terminado": False,
            }
            try:
                await m.send(
                    embed=_embed_inicio(nombre, emoji, color, len(preguntas)),
                    view=ComenzarView(sid),
                )
                enviados += 1
            except Exception:
                fallos += 1

        _save(data)

        emb = discord.Embed(
            title=f"{emoji}  Examen enviado · {nombre}",
            description=(
                f"**Log:** {self.log_channel.mention}\n"
                f"**Con el rol:** {len(miembros)}\n"
                f"**MD ok:** {enviados} · **Fallos:** {fallos}\n"
                f"**Preguntas:** {len(preguntas)} · **Mínimo:** {_MINIMO}%"
            ),
            color=color,
        ).set_footer(text="Hospital General · Exámenes de Dirección")
        await interaction.followup.send(embed=emb, ephemeral=True)

        try:
            await self.log_channel.send(
                embed=discord.Embed(
                    title=f"{emoji}  Ronda iniciada · {nombre}",
                    description=(
                        f"Por {interaction.user.mention}\n"
                        f"Enviados: {enviados}/{len(miembros)}"
                    ),
                    color=color,
                )
            )
        except Exception:
            pass


class DireccionMenuView(ui.View):
    def __init__(self, log_channel: discord.TextChannel):
        super().__init__(timeout=300)
        self.add_item(DireccionSelect(log_channel))


def registrar(bot: commands.Bot) -> None:
    try:
        bot.tree.remove_command("examen_direccion")
    except Exception:
        pass
    try:
        bot.add_view(LogExamenView())
    except Exception:
        pass

    @bot.tree.command(
        name="examen_direccion",
        description="[Staff] Examen RP de postulación a Direcciones",
    )
    @app_commands.describe(canal_log="Canal de log de resultados y aprobación")
    async def examen_direccion(
        inter: discord.Interaction, canal_log: discord.TextChannel
    ):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _es_staff(inter.user):
            return await inter.response.send_message(
                "❌ Solo staff autorizado.", ephemeral=True
            )

        emb = discord.Embed(
            title="🏛️  Exámenes de Dirección · Hospital General",
            description=(
                "Elige la **dirección** en el menú.\n\n"
                "El bot busca a quienes tienen el **rol** de esa dirección "
                "y les manda el examen por **MD**.\n\n"
                f"**Log:** {canal_log.mention}\n"
                f"**Mínimo para aprobar:** **{_MINIMO}%**\n\n"
                "• Si llega al mínimo → **Aprobar**\n"
                "• Si no → **Rechazar** (motivo obligatorio)"
            ),
            color=0x1A5276,
        ).set_footer(text="Roleplay · Postulaciones a Direcciones")
        await inter.response.send_message(
            embed=emb, view=DireccionMenuView(canal_log), ephemeral=True
        )

    print("[examen_direccion] OK — preguntas RP accesibles · mín 60%")
