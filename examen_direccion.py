# -*- coding: utf-8 -*-
"""
Exámenes de postulación a Direcciones (incl. Cancillería / Vice Cancillería).

/examen_direccion canal_log:
  · Menú de direcciones
  · Enviar examen a quienes tienen el rol de esa dirección
  · Preguntas difíciles por área
  · Resultados al DM del evaluado
  · Log con puntuación + Aprobar / Rechazar (con motivo si < mínimo)
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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
_MINIMO = 70  # % mínimo para poder aprobar
_PREGUNTAS_POR_EXAMEN = 8

# key de rol → (id menú, nombre, emoji, color)
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

# Preguntas difíciles por dirección: (pregunta, opciones[4], índice correcta 0-3)
_BANCO: Dict[str, List[Tuple[str, List[str], int]]] = {
    "CANCILLER": [
        (
            "En un conflicto entre dos Direcciones con impacto en la operación del hospital, ¿cuál es la primera obligación del Canciller?",
            [
                "Imponer una decisión inmediata sin consultar",
                "Mediar con criterio institucional, documentar y preservar la cadena de mando",
                "Delegar todo al Director General sin intervención",
                "Cerrar ambas direcciones hasta nuevo aviso",
            ],
            1,
        ),
        (
            "La Vice Cancillería emite una directiva que contradice el reglamento general. ¿Qué debe hacer el Canciller?",
            [
                "Ignorarla si no es urgente",
                "Validar, corregir o anular según jerarquía y dejar constancia formal",
                "Permitir que cada área elija qué aplicar",
                "Expulsar al Vice Canciller sin proceso",
            ],
            1,
        ),
        (
            "¿Qué principio rige la representación institucional ante autoridades externas?",
            [
                "Solo el Director Médico puede representar al hospital",
                "Unidad de criterio, protocolo y respaldo documental de Cancillería",
                "Cualquier staff puede hablar en nombre del hospital",
                "No se permite ninguna representación externa",
            ],
            1,
        ),
        (
            "Una sanción a un Director debe:",
            [
                "Aplicarse en público sin expediente",
                "Seguir debido proceso, registro y proporcionalidad",
                "Decidirse solo por votación informal",
                "Ser siempre un ban inmediato",
            ],
            1,
        ),
        (
            "Ante una crisis de imagen del servidor de rol, la prioridad del Canciller es:",
            [
                "Borrar evidencias",
                "Coordinar respuesta oficial, contener daños y proteger la operación",
                "Culpar a un área al azar",
                "Cerrar el servidor sin aviso",
            ],
            1,
        ),
        (
            "La relación Canciller–Fundador/Owner implica:",
            [
                "Que el Canciller sustituye al Owner en todo",
                "Ejecución estratégica bajo límites del organigrama y del Owner",
                "Independencia total sin rendición de cuentas",
                "Solo funciones ceremoniales",
            ],
            1,
        ),
        (
            "Un miembro del staff filtra información confidencial de una reunión de Cancillería. Acción correcta:",
            [
                "Advertencia verbal sin registro",
                "Investigación, medida proporcional y refuerzo de confidencialidad",
                "Ignorarlo si no hay quejas",
                "Promover al miembro por honestidad",
            ],
            1,
        ),
        (
            "¿Cuándo es legítimo que Cancillería intervenga en un área operativa?",
            [
                "Nunca",
                "Cuando hay riesgo institucional, incumplimiento grave o vacío de mando",
                "Siempre, en cada decisión menor",
                "Solo si lo pide un residente",
            ],
            1,
        ),
        (
            "La aprobación de un cambio estructural del organigrama requiere:",
            [
                "Solo un mensaje en general",
                "Validación de autoridades competentes y comunicación formal",
                "Voto de todos los visitantes",
                "Decisión unilateral de un jefe de servicio",
            ],
            1,
        ),
        (
            "El lema institucional debe usarse en actos oficiales para:",
            [
                "Decoración sin significado",
                "Reforzar identidad, disciplina y servicio del hospital",
                "Reemplazar el reglamento",
                "Evitar sanciones",
            ],
            1,
        ),
    ],
    "VICE_CANCILLER": [
        (
            "El Vice Canciller actúa con plenitud cuando:",
            [
                "El Canciller está ausente o lo delega formalmente",
                "Lo decide por iniciativa personal siempre",
                "Un director se lo pide en privado",
                "Nunca puede actuar",
            ],
            0,
        ),
        (
            "En ausencia del Canciller, una disputa entre RRHH y Docencia se resuelve:",
            [
                "Ignorándola",
                "Con mediación, registro y respeto al organigrama",
                "Favoreciendo siempre a RRHH",
                "Cerrando ambas áreas",
            ],
            1,
        ),
        (
            "¿Qué documento debe conservar el Vice Canciller tras una decisión interina?",
            [
                "Ninguno",
                "Acta o registro con motivo, fecha y alcance",
                "Solo un emoji de reacción",
                "Un mensaje privado sin copia",
            ],
            1,
        ),
        (
            "Si el Canciller anula una decisión del Vice Canciller:",
            [
                "Se ignora la anulación",
                "Se acata y se documenta el cambio",
                "Se apela en público al Owner inmediatamente sin canal",
                "Se sanciona al Canciller",
            ],
            1,
        ),
        (
            "La confidencialidad de expedientes de alta dirección implica:",
            [
                "Compartirlos en staff-general",
                "Acceso restringido y necesidad de conocer",
                "Publicarlos en anuncios",
                "Eliminarlos cada día",
            ],
            1,
        ),
        (
            "Un Director cuestiona la legitimidad del Vice Canciller. Respuesta correcta:",
            [
                "Sancionar sin diálogo",
                "Reafirmar el mandato, citar organigrama y escalar si es necesario",
                "Renunciar de inmediato",
                "Ignorar y no responder",
            ],
            1,
        ),
        (
            "Coordinación con Dirección General debe ser:",
            [
                "Competencia hostil",
                "Complementaria: estrategia institucional vs. operación diaria",
                "Inexistente",
                "Solo por intermediarios anónimos",
            ],
            1,
        ),
        (
            "En una emergencia de rol masiva, el Vice Canciller prioriza:",
            [
                "Su propia escena de RP",
                "Cadena de mando, seguridad de canales y continuidad operativa",
                "Cerrar todos los tickets",
                "Banear a todos los residentes",
            ],
            1,
        ),
        (
            "La firma en documentos oficiales del Vice Canciller:",
            [
                "No tiene valor",
                "Vale según delegación y registro de firmas institucionales",
                "Sustituye siempre al Owner",
                "Solo sirve en certificados médicos",
            ],
            1,
        ),
        (
            "¿Qué diferencia clave existe entre Vice Canciller y Admin en jefe?",
            [
                "Ninguna",
                "El Vice es autoridad institucional; el Admin en jefe es staff de servidor",
                "El Admin en jefe manda sobre el Canciller",
                "El Vice solo gestiona tickets",
            ],
            1,
        ),
    ],
    "DIR_GENERAL": [
        (
            "La Dirección General coordina principalmente:",
            [
                "Solo el área de limpieza",
                "Alineación operativa entre direcciones y políticas hospitalarias",
                "Únicamente sanciones de Discord",
                "Solo la economía del servidor",
            ],
            1,
        ),
        (
            "Un fallo de comunicación entre Médica y Logística se gestiona:",
            [
                "Dejando que escalen en público",
                "Con mesa de coordinación, responsables y plazos",
                "Cerrando Logística",
                "Ignorando el problema",
            ],
            1,
        ),
        (
            "Indicadores de rendimiento de direcciones deben ser:",
            [
                "Secretos e inexistentes",
                "Medibles, revisados y orientados a mejora",
                "Solo opiniones personales",
                "Publicados por visitantes",
            ],
            1,
        ),
        (
            "Ante un Director inactivo sin justificación:",
            [
                "Nada",
                "Aviso formal, plazos y escalado a Cancillería/RRHH",
                "Ban inmediato sin proceso",
                "Promoción automática",
            ],
            1,
        ),
        (
            "La planificación semanal de operaciones incluye:",
            [
                "Solo memes",
                "Prioridades clínicas, recursos y cobertura de turnos críticos",
                "Únicamente eventos sociales",
                "Cerrar el hospital los fines de semana",
            ],
            1,
        ),
        (
            "Un cambio de protocolo transversal requiere:",
            [
                "Publicarlo sin consulta",
                "Consulta a áreas afectadas, validación y difusión oficial",
                "Solo mensaje a un amigo",
                "Ocultarlo del staff",
            ],
            1,
        ),
        (
            "Relación con Seguridad en incidentes graves:",
            [
                "Dirigir el RP médico ignorando seguridad",
                "Coordinar contención, acceso y continuidad asistencial",
                "Dejar solo a Seguridad sin información",
                "Evacuar sin protocolo",
            ],
            1,
        ),
        (
            "Reportes a Cancillería deben ser:",
            [
                "Informales y sin datos",
                "Periódicos, claros y con riesgos/acciones",
                "Solo quejas anónimas",
                "Inexistentes",
            ],
            1,
        ),
        (
            "¿Qué no es función de Dirección General?",
            [
                "Coordinar direcciones",
                "Sustituir el rol clínico del médico tratante en cada paciente",
                "Supervisar políticas operativas",
                "Escalar crisis institucionales",
            ],
            1,
        ),
        (
            "Delegación a jefes de servicio implica:",
            [
                "Abandonar toda supervisión",
                "Autonomía operativa con rendición de cuentas",
                "Prohibir toda iniciativa",
                "Transferir la titularidad del cargo",
            ],
            1,
        ),
    ],
    "DIR_MEDICO": [
        (
            "En un código azul en rol, el Director Médico debe garantizar:",
            [
                "Que nadie intervenga",
                "Liderazgo clínico, asignación de roles y registro del evento",
                "Solo observar sin intervenir",
                "Cerrar el canal de voz",
            ],
            1,
        ),
        (
            "La jerarquía en escena de trauma prioritiza:",
            [
                "Al visitante más antiguo",
                "Al médico de mayor competencia asignado y al líder de escena",
                "Al que escriba más rápido",
                "Siempre al paramédico sobre el médico",
            ],
            1,
        ),
        (
            "Un residente comete un error grave de protocolo. Acción correcta:",
            [
                "Humillarlo en público",
                "Corregir, documentar, formar y escalar si es reiterado",
                "Ignorarlo",
                "Expulsarlo del servidor sin expediente",
            ],
            1,
        ),
        (
            "La coordinación con Enfermería en quirófano de rol implica:",
            [
                "Ignorar al personal de enfermería",
                "Comunicación clara de órdenes, tiempos y seguridad del paciente",
                "Dejar que cada uno improvise sin plan",
                "Prohibir la presencia de enfermería",
            ],
            1,
        ),
        (
            "Consentimiento informado en RP médico:",
            [
                "No existe en rol",
                "Debe respetarse salvo emergencias vitales justificadas",
                "Solo aplica a staff",
                "Es opcional siempre",
            ],
            1,
        ),
        (
            "Un médico especialista se niega a recibir traslados sin motivo clínico. Usted:",
            [
                "Lo apoya sin preguntar",
                "Evalúa carga, criterios y obliga cobertura según protocolo",
                "Cierra urgencias",
                "Sanciona al paciente",
            ],
            1,
        ),
        (
            "Documentación clínica mínima en un ingreso incluye:",
            [
                "Solo el nombre",
                "Motivo, hallazgos, plan y responsable",
                "Un emoji",
                "Nada si hay prisa",
            ],
            1,
        ),
        (
            "Conflicto OOC entre médicos en canal de rol:",
            [
                "Continuar la discusión en escena",
                "Separar IC/OOC, pausar si hace falta y mediar fuera de escena",
                "Banear a ambos sin hablar",
                "Eliminar el canal",
            ],
            1,
        ),
        (
            "La supervisión de internos/residentes busca:",
            [
                "Sustituirlos siempre",
                "Autonomía progresiva con seguridad del paciente ficticio",
                "Prohibirles actuar",
                "Dejarlos solos en códigos",
            ],
            1,
        ),
        (
            "Relación con Docencia para certificaciones clínicas:",
            [
                "Competencia y bloqueo",
                "Estándares clínicos alineados y validación de competencias",
                "Ignorar certificaciones",
                "Que Docencia dicte tratamientos en cada paciente",
            ],
            1,
        ),
    ],
    "DIR_ENFERMERIA": [
        (
            "La prioritización de cuidados se basa en:",
            [
                "Orden de llegada solo",
                "Gravedad, dependencia y recursos disponibles",
                "Simpatía personal",
                "Rango Discord del paciente",
            ],
            1,
        ),
        (
            "Administración de medicación en rol exige:",
            [
                "Improvisar dosis",
                "Verificación de orden, paciente, vía y registro",
                "Solo el color del medicamento",
                "No registrar nada",
            ],
            1,
        ),
        (
            "Un auxiliar incumple aislamiento. Acción:",
            [
                "Reírse",
                "Corregir de inmediato, educar y reportar si es grave",
                "Ignorar",
                "Cerrar el hospital",
            ],
            1,
        ),
        (
            "Coordinación con el médico tratante implica:",
            [
                "Cambiar órdenes sin avisar",
                "Ejecutar plan, reportar cambios y clarificar dudas",
                "Nunca hablar con el médico",
                "Solo escribir en OOC",
            ],
            1,
        ),
        (
            "Turnos cortos de personal se resuelven:",
            [
                "Abandonando pacientes",
                "Redistribución, priorización y escalado a Dirección",
                "Cerrando urgencias en silencio",
                "Promoviendo a visitantes a enfermeros",
            ],
            1,
        ),
        (
            "Registro de enfermería debe ser:",
            [
                "Opcional",
                "Claro, oportuno y verificable",
                "Solo mental",
                "Copia exacta del chat de memes",
            ],
            1,
        ),
        (
            "Liderazgo de equipo de enfermería en crisis:",
            [
                "Gritar sin roles",
                "Asignar tareas, tiempos y punto de control",
                "Salir de la escena",
                "Dejar que cada uno haga lo que quiera",
            ],
            1,
        ),
        (
            "Formación de auxiliares es responsabilidad de:",
            [
                "Nadie",
                "Dirección de Enfermería con apoyo de Docencia",
                "Solo Seguridad",
                "Solo el Owner",
            ],
            1,
        ),
        (
            "Confidencialidad del paciente en RP:",
            [
                "Se publica en general",
                "Se protege; solo se comparte con necesidad asistencial",
                "Se vende a otros jugadores",
                "No existe",
            ],
            1,
        ),
        (
            "Conflicto entre enfermeros en turno:",
            [
                "Pelear en el pasillo de rol",
                "Separar, escuchar, mediar y documentar",
                "Banear al más nuevo",
                "Cerrar el turno",
            ],
            1,
        ),
    ],
    "DIR_RRHH": [
        (
            "Un proceso de selección justo incluye:",
            [
                "Elegir amigos sin criterios",
                "Perfil, evaluación, transparencia y registro",
                "Solo sorteo",
                "Vender el puesto",
            ],
            1,
        ),
        (
            "Una queja formal contra un jefe de servicio se gestiona:",
            [
                "Borrándola",
                "Recepción, imparcialidad, investigación y resolución documentada",
                "Publicándola en anuncios",
                "Ignorándola si el jefe es popular",
            ],
            1,
        ),
        (
            "Onboarding de nuevo personal debe incluir:",
            [
                "Nada",
                "Normativa, organigrama, canales y expectativas del cargo",
                "Solo el rol de color",
                "Acceso admin inmediato",
            ],
            1,
        ),
        (
            "Inactividad injustificada reiterada:",
            [
                "Premio",
                "Aviso, plazos y medidas según reglamento",
                "Promoción",
                "Ignorar siempre",
            ],
            1,
        ),
        (
            "Confidencialidad de expedientes laborales:",
            [
                "Abiertos a todos",
                "Acceso restringido a roles autorizados",
                "En el canal general",
                "En DMs masivos",
            ],
            1,
        ),
        (
            "Despido de un miembro requiere:",
            [
                "Mensaje agresivo sin causa",
                "Causa, proceso y comunicación formal",
                "Solo un emoji",
                "Voto de visitantes",
            ],
            1,
        ),
        (
            "Conflicto de interés en una contratación:",
            [
                "Ocultarlo",
                "Declararlo y abstenerse de decidir",
                "Forzar la contratación",
                "Mentir en el registro",
            ],
            1,
        ),
        (
            "Métricas de RRHH útiles son:",
            [
                "Ninguna",
                "Tiempo de cobertura, rotación y calidad de procesos",
                "Solo likes",
                "Cantidad de memes",
            ],
            1,
        ),
        (
            "Relación con Cancillería en casos graves:",
            [
                "Ocultar información",
                "Informar con hechos y proponer medidas",
                "Difamar en público",
                "Renunciar en silencio",
            ],
            1,
        ),
        (
            "Un postulado falsea experiencia. Acción:",
            [
                "Aprobarlo igual",
                "Rechazar, registrar y aplicar norma antisuplantación",
                "Ignorar",
                "Darle admin",
            ],
            1,
        ),
    ],
    "DIR_DOCENCIA": [
        (
            "Una certificación clínica debe basarse en:",
            [
                "Amistad",
                "Competencias evaluables y material oficial",
                "Solo presencia en voz",
                "Pago OOC",
            ],
            1,
        ),
        (
            "El Director de Docencia puede emitir certificados cuando:",
            [
                "Quiere",
                "Hay proceso, evaluación y firmas según protocolo",
                "Lo pide un visitante",
                "Sin examen nunca",
            ],
            1,
        ),
        (
            "Un instructor sesga notas a favor de su círculo. Usted:",
            [
                "Lo premia",
                "Investiga, corrige evaluaciones y sanciona si procede",
                "Ignora",
                "Cierra Docencia",
            ],
            1,
        ),
        (
            "Material de estudio debe ser:",
            [
                "Secreto imposible",
                "Claro, alineado a normativa RP y actualizado",
                "Copiado de servidores ajenos sin revisión",
                "Solo imágenes sin texto",
            ],
            1,
        ),
        (
            "Revalidación de certificaciones sirve para:",
            [
                "Molestar",
                "Mantener estándares y actualizar competencias",
                "Eliminar roles al azar",
                "Nada",
            ],
            1,
        ),
        (
            "Coordinación con Dirección Médica en contenidos:",
            [
                "Evitarla",
                "Validar rigor clínico del temario",
                "Que Médica ignore Docencia",
                "Solo pelear en staff",
            ],
            1,
        ),
        (
            "Un postulante copia en el examen. Acción:",
            [
                "Aprobarlo",
                "Anular, registrar y aplicar política académica",
                "Subirle nota",
                "Darle el rol de director",
            ],
            1,
        ),
        (
            "Registro de capacitaciones debe permitir:",
            [
                "Olvidar quién aprobó",
                "Trazabilidad de fecha, instructor y resultado",
                "Borrar evidencias",
                "Solo oral",
            ],
            1,
        ),
        (
            "Carga horaria de formadores se gestiona:",
            [
                "Quemándolos sin límite",
                "Planificando turnos y evitando sobrecarga",
                "Obligando 24/7",
                "Prohibiendo formar",
            ],
            1,
        ),
        (
            "La excelencia docente se mide por:",
            [
                "Cantidad de roles de color",
                "Calidad de aprendizaje y cumplimiento de estándares",
                "Solo embeds bonitos",
                "Número de sanciones",
            ],
            1,
        ),
    ],
    "DIR_LOGISTICA": [
        (
            "Prioridad de suministro en emergencia:",
            [
                "Lo más barato siempre",
                "Criticidad clínica y continuidad operativa",
                "Lo que pida el más ruidoso",
                "Nada de stock",
            ],
            1,
        ),
        (
            "Inventario descuadrado se corrige:",
            [
                "Inventando cifras",
                "Auditoría, ajuste documentado y controles",
                "Ignorando",
                "Culpando a un bot",
            ],
            1,
        ),
        (
            "Coordinación con Médica para insumos críticos:",
            [
                "No hablar",
                "Previsión de demanda y canales de solicitud claros",
                "Entregar sin registro",
                "Negar todo",
            ],
            1,
        ),
        (
            "Un proveedor interno incumple plazos reiterados:",
            [
                "Premiarlo",
                "Aviso, alternativas y escalado",
                "Ignorar",
                "Cerrar el hospital",
            ],
            1,
        ),
        (
            "Almacenes restringidos requieren:",
            [
                "Acceso libre",
                "Control de acceso y registro de movimientos",
                "Solo un emoji de llave",
                "Ningún control",
            ],
            1,
        ),
        (
            "Plan de contingencia logística incluye:",
            [
                "Nada",
                "Stock mínimo, rutas alternativas y responsables",
                "Solo rezar",
                "Borrar el inventario",
            ],
            1,
        ),
        (
            "Pérdida de material se investiga para:",
            [
                "Culpar al azar",
                "Causa, responsabilidad y prevención",
                "Ocultar el faltante",
                "Aumentar el caos",
            ],
            1,
        ),
        (
            "Reportes a Dirección General deben mostrar:",
            [
                "Solo quejas",
                "Niveles de stock, riesgos y acciones",
                "Memes",
                "Nada",
            ],
            1,
        ),
        (
            "Rotación de turnos logísticos busca:",
            [
                "Fatiga crónica",
                "Cobertura estable y bienestar del equipo",
                "Un solo miembro 24/7",
                "Cero personal",
            ],
            1,
        ),
        (
            "Solicitudes urgentes fuera de protocolo:",
            [
                "Siempre negadas",
                "Evaluadas, registradas y regularizadas después",
                "Sin registro nunca",
                "Entregadas a cualquiera",
            ],
            1,
        ),
    ],
    "JEFE_SEGURIDAD": [
        (
            "Primera respuesta ante un intruso en área restringida:",
            [
                "Ignorarlo",
                "Identificar, contener según protocolo y reportar",
                "Banear sin evidencia",
                "Huir",
            ],
            1,
        ),
        (
            "Uso de fuerza en RP de seguridad debe ser:",
            [
                "Máximo siempre",
                "Proporcional, escalonado y justificado",
                "Aleatorio",
                "Prohibido siempre",
            ],
            1,
        ),
        (
            "Coordinación con personal clínico en incidente violento:",
            [
                "Bloquear a todos los médicos",
                "Asegurar escena y permitir asistencia segura",
                "Evacuar sin avisar a nadie",
                "Cerrar el RP médico",
            ],
            1,
        ),
        (
            "Informe de incidente de seguridad incluye:",
            [
                "Solo opiniones",
                "Hechos, horarios, involucrados y acciones",
                "Nada escrito",
                "Difamación",
            ],
            1,
        ),
        (
            "Un guardia abusa de autoridad. Usted:",
            [
                "Lo cubre",
                "Investiga, sanciona y reentrena",
                "Lo asciende",
                "Ignora quejas",
            ],
            1,
        ),
        (
            "Control de accesos a quirófano implica:",
            [
                "Dejar pasar a cualquiera",
                "Verificación de rol y necesidad",
                "Prohibir a todo el staff médico",
                "No hay control",
            ],
            1,
        ),
        (
            "Amenaza OOC en canales del hospital:",
            [
                "Tratarla como RP",
                "Separar IC/OOC, documentar y escalar a staff admin",
                "Responder con más amenazas",
                "Borrar sin registro",
            ],
            1,
        ),
        (
            "Rondas y puestos fijos sirven para:",
            [
                "Decoración",
                "Disuasión, detección temprana y cobertura",
                "Nada",
                "Solo RP de café",
            ],
            1,
        ),
        (
            "Relación con Cancillería en crisis de seguridad:",
            [
                "Ocultar el incidente",
                "Informar con hechos y plan de contención",
                "Culpar a Cancillería",
                "Cerrar sin avisar",
            ],
            1,
        ),
        (
            "Entrenamiento del equipo de seguridad prioriza:",
            [
                "Solo chat",
                "Protocolos, comunicación y proporcionalidad",
                "Caos improvisado",
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
    # fallback por nombre aproximado
    for _, nombre, emoji, _ in _DIRECCIONES:
        if _direccion_key_por_nombre(nombre) == key:
            pass
    nombres_hint = {
        "CANCILLER": "canciller",
        "VICE_CANCILLER": "vice",
        "DIR_GENERAL": "director general",
        "DIR_MEDICO": "director médico",
        "DIR_ENFERMERIA": "enfermer",
        "DIR_RRHH": "rrhh",
        "DIR_DOCENCIA": "docencia",
        "DIR_LOGISTICA": "logíst",
        "JEFE_SEGURIDAD": "seguridad",
    }
    hint = nombres_hint.get(key, key.lower())
    for r in guild.roles:
        n = (r.name or "").lower()
        if hint in n and "director" in n or (key == "CANCILLER" and "canciller" in n and "vice" not in n):
            return r
        if key == "VICE_CANCILLER" and "vice" in n and "canciller" in n:
            return r
        if key == "JEFE_SEGURIDAD" and "seguridad" in n and ("jefe" in n or "director" in n):
            return r
    return None


def _direccion_key_por_nombre(nombre: str) -> Optional[str]:
    for k, n, _, _ in _DIRECCIONES:
        if n == nombre:
            return k
    return None


def _miembros_con_rol(guild: discord.Guild, key: str) -> List[discord.Member]:
    rol = _rol_por_key(guild, key)
    if not rol:
        return []
    return [m for m in guild.members if (not m.bot) and rol in m.roles]


def _preguntas_para(key: str) -> List[Tuple[str, List[str], int]]:
    banco = list(_BANCO.get(key) or [])
    if not banco:
        return []
    # tomar hasta N, rotando por tiempo
    start = int(time.time()) % max(1, len(banco))
    rot = banco[start:] + banco[:start]
    return rot[:_PREGUNTAS_POR_EXAMEN]


def _embed_inicio(dir_nombre: str, emoji: str, color: int, total: int) -> discord.Embed:
    emb = discord.Embed(
        title=f"{emoji}  Examen de postulación · {dir_nombre}",
        description=(
            f"Evaluación institucional del **Hospital General**.\n\n"
            f"• **{total}** preguntas de nivel directivo\n"
            f"• Mínimo para poder ser **aprobado por staff:** **{_MINIMO}%**\n"
            f"• Responde con honestidad; el resultado se registra\n\n"
            f"Pulsa **Comenzar examen** cuando estés listo."
        ),
        color=color,
    )
    emb.set_footer(text="Hospital General · Direcciones · Evaluación formal")
    return emb


def _embed_pregunta(
    dir_nombre: str,
    emoji: str,
    color: int,
    idx: int,
    total: int,
    texto: str,
) -> discord.Embed:
    emb = discord.Embed(
        title=f"{emoji}  {dir_nombre} · Pregunta {idx + 1}/{total}",
        description=f"**{texto}**",
        color=color,
    )
    emb.set_footer(text="Elige una opción · No se puede volver atrás")
    return emb


def _embed_resultado(
    dir_nombre: str,
    emoji: str,
    score: int,
    total: int,
    pct: int,
) -> discord.Embed:
    ok = pct >= _MINIMO
    color = 0x2ECC71 if ok else 0xE74C3C
    emb = discord.Embed(
        title=f"{emoji}  Resultado · {dir_nombre}",
        description=(
            f"**Puntuación:** {score}/{total}  ·  **{pct}%**\n"
            f"**Mínimo requerido:** {_MINIMO}%\n\n"
            + (
                "Alcanzaste el mínimo. El staff puede **aprobar** tu postulación en el log."
                if ok
                else "No alcanzaste el mínimo. El staff **rechazará** la postulación con motivo."
            )
        ),
        color=color,
    )
    emb.set_footer(text="Hospital General · Resultado enviado también al log oficial")
    return emb


class RespuestaSelect(ui.Select):
    def __init__(self, session_id: str, opciones: List[str], correcta: int):
        self.session_id = session_id
        self.correcta = correcta
        opts = [
            discord.SelectOption(
                label=f"{chr(65 + i)}. {opciones[i][:90]}",
                value=str(i),
                description=opciones[i][90:190] if len(opciones[i]) > 90 else None,
            )
            for i in range(len(opciones))
        ]
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
                "❌ Sesión expirada o inválida.", ephemeral=True
            )
        if int(ses.get("user_id") or 0) != interaction.user.id:
            return await interaction.response.send_message(
                "❌ Este examen no es tuyo.", ephemeral=True
            )
        if ses.get("terminado"):
            return await interaction.response.send_message(
                "❌ Examen ya finalizado.", ephemeral=True
            )

        eleccion = int(self.values[0])
        idx = int(ses.get("idx") or 0)
        preguntas = ses.get("preguntas") or []
        if idx >= len(preguntas):
            return await interaction.response.send_message(
                "❌ Índice inválido.", ephemeral=True
            )

        # preguntas guardadas como [texto, opciones, correcta]
        ok = eleccion == int(preguntas[idx][2])
        if ok:
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

    @ui.button(
        label="Comenzar examen",
        style=discord.ButtonStyle.primary,
        emoji="📋",
        custom_id="examen_dir:start_static",  # replaced per instance below
    )
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

        # DM resultado (por si el examen no estaba en DM)
        try:
            user = interaction.user
            await user.send(embed=emb)
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
    color = 0xF1C40F if ok_min else 0xE74C3C

    emb = discord.Embed(
        title=f"{emoji}  Log de examen · {dir_nombre}",
        description=(
            f"**Candidato:** <@{uid}> (`{uid}`)\n"
            f"**Puntuación:** **{score}/{total}** · **{pct}%**\n"
            f"**Mínimo:** {_MINIMO}%\n"
            f"**Estado mínimo:** "
            + (
                "✅ Alcanzado — staff puede **Aprobar**"
                if ok_min
                else "❌ No alcanzado — staff debe **Rechazar** con motivo"
            )
        ),
        color=color,
    )
    emb.set_footer(text=f"Sesión {ses.get('id', '')[:12]} · Hospital General")

    view = LogExamenView(
        session_id=str(ses.get("id") or ""),
        user_id=uid,
        pct=pct,
        dir_nombre=dir_nombre,
    )
    try:
        msg = await canal.send(embed=emb, view=view)
        data = _load()
        data.setdefault("logs", {})[str(ses.get("id"))] = {
            "message_id": msg.id,
            "channel_id": canal.id,
            "user_id": uid,
            "pct": pct,
            "dir": dir_nombre,
        }
        _save(data)
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

    def _es_staff(self, m: discord.Member) -> bool:
        return _es_staff(m)

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
        if not self._es_staff(inter.user):
            return await inter.response.send_message(
                "❌ Solo staff autorizado.", ephemeral=True
            )

        data = _load()
        ses = data.get("sesiones", {}).get(self.session_id) or {}
        pct = int(ses.get("pct") or self.pct or 0)
        if pct < _MINIMO:
            return await inter.response.send_message(
                f"❌ Puntuación **{pct}%** < mínimo **{_MINIMO}%**. "
                f"Debes **Rechazar** con motivo; no se puede aprobar.",
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
                            f"Puntuación: **{pct}%** (mín. {_MINIMO}%)."
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
        if not self._es_staff(inter.user):
            return await inter.response.send_message(
                "❌ Solo staff autorizado.", ephemeral=True
            )

        class MotivoModal(ui.Modal, title="Motivo del rechazo"):
            motivo = ui.TextInput(
                label="Motivo",
                style=discord.TextStyle.paragraph,
                required=True,
                max_length=500,
                placeholder="Explica por qué se rechaza la postulación…",
            )

            def __init__(self, parent: "LogExamenView"):
                super().__init__()
                self.parent = parent

            async def on_submit(self, modal_inter: discord.Interaction):
                data = _load()
                ses = data.get("sesiones", {}).get(self.parent.session_id) or {}
                uid = int(ses.get("user_id") or self.parent.user_id)
                dir_n = ses.get("dir_nombre") or self.parent.dir_nombre
                pct = int(ses.get("pct") or self.parent.pct or 0)
                motivo_txt = str(self.motivo.value).strip()

                member = modal_inter.guild.get_member(uid) if modal_inter.guild else None
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
                            ).set_footer(text="Hospital General · Prepara la normativa del área")
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

        await inter.response.send_modal(MotivoModal(self))


class DireccionSelect(ui.Select):
    def __init__(self, log_channel: discord.TextChannel):
        self.log_channel = log_channel
        options = [
            discord.SelectOption(
                label=nombre,
                value=key,
                emoji=emoji,
                description=f"Examen · {nombre}"[:100],
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
                "❌ No hay banco de preguntas para esta dirección.",
                ephemeral=True,
            )

        if not miembros:
            return await interaction.response.send_message(
                f"⚠️ No encontré miembros con el rol de **{nombre}**.\n"
                f"Verifica que el rol esté vinculado en el organigrama.",
                ephemeral=True,
            )

        await interaction.response.defer(ephemeral=True)
        enviados = 0
        fallos = 0
        data = _load()
        data.setdefault("sesiones", {})

        for m in miembros:
            sid = f"{m.id}_{key}_{int(time.time())}"
            ses = {
                "id": sid,
                "user_id": m.id,
                "dir_key": key,
                "dir_nombre": nombre,
                "emoji": emoji,
                "color": color,
                "log_channel_id": self.log_channel.id,
                "preguntas": [
                    [p[0], p[1], p[2]] for p in preguntas
                ],
                "idx": 0,
                "score": 0,
                "terminado": False,
            }
            data["sesiones"][sid] = ses
            try:
                view = ComenzarView(sid)
                # custom_id único no persistente: timeout 900 ok
                await m.send(
                    embed=_embed_inicio(nombre, emoji, color, len(preguntas)),
                    view=view,
                )
                enviados += 1
            except Exception:
                fallos += 1

        _save(data)

        emb = discord.Embed(
            title=f"{emoji}  Examen enviado · {nombre}",
            description=(
                f"**Canal de log:** {self.log_channel.mention}\n"
                f"**Destinatarios (con rol):** {len(miembros)}\n"
                f"**DM enviados:** {enviados}\n"
                f"**Fallos (MD cerrado):** {fallos}\n"
                f"**Preguntas:** {len(preguntas)} · **Mínimo:** {_MINIMO}%\n\n"
                f"Cuando terminen, el log mostrará la puntuación y "
                f"botones **Aprobar** / **Rechazar**."
            ),
            color=color,
        )
        emb.set_footer(text="Hospital General · Postulaciones a Direcciones")
        await interaction.followup.send(embed=emb, ephemeral=True)

        try:
            await self.log_channel.send(
                embed=discord.Embed(
                    title=f"{emoji}  Ronda de examen iniciada · {nombre}",
                    description=(
                        f"Iniciada por {interaction.user.mention}\n"
                        f"Destinatarios: {enviados}/{len(miembros)}"
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
        description="[Staff] Examen de postulación a Direcciones (log + aprobación)",
    )
    @app_commands.describe(
        canal_log="Canal donde se publicará el resultado y la aprobación",
    )
    async def examen_direccion(
        inter: discord.Interaction,
        canal_log: discord.TextChannel,
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
                "Selecciona la **dirección** en el menú.\n\n"
                f"El bot detectará a quienes tengan el **rol** de esa dirección "
                f"y les enviará el examen por **MD**.\n\n"
                f"**Log de resultados:** {canal_log.mention}\n"
                f"**Mínimo para aprobar:** **{_MINIMO}%**\n\n"
                "• Si alcanza el mínimo → staff puede **Aprobar**\n"
                "• Si no → staff **Rechaza** con **motivo** (obligatorio)"
            ),
            color=0x1A5276,
        )
        emb.set_footer(text="Postulaciones institucionales · Evaluación formal")
        await inter.response.send_message(
            embed=emb,
            view=DireccionMenuView(canal_log),
            ephemeral=True,
        )

    print("[examen_direccion] OK — /examen_direccion con log y aprobación")
