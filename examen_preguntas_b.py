# -*- coding: utf-8 -*-
"""Banco B: preguntas detalladas, claras, nivel RP de dirección."""
from __future__ import annotations
from typing import Dict, List, Tuple


def _t(q: str, good: str, bad: List[str], rot: int = 1) -> Tuple[str, List[str], int]:
    ops = list(bad[:3])
    while len(ops) < 3:
        ops.append("Actuar sin dejar registro ni responsable")
    pos = rot % 4
    ops.insert(pos, good)
    return (q, ops[:4], pos)


def _p(rows: List[Tuple[str, str, List[str], int]]) -> List[Tuple[str, List[str], int]]:
    return [_t(q, g, b, r) for q, g, b, r in rows]


BANCO_PART: Dict[str, List[Tuple[str, List[str], int]]] = {
    "DIR_MEDICO": _p([
        (
            "Hay un código / emergencia de rol y la escena está desordenada (nadie sabe quién lidera). "
            "Como Director Médico, ¿cómo tomas el control?",
            "Asignas roles de escena, nombras un líder clínico y un punto claro de información",
            [
                "Dejas que cada uno improvise ‘con creatividad’",
                "Pides silencio total sin nombrar líder",
                "Dejas el mando a quien escribe más rápido en el chat",
            ],
            1,
        ),
        (
            "Un residente comete un error de protocolo en escena. ¿Cuál es el control formativo correcto?",
            "Lo corriges en el momento, le enseñas y registras el caso si es grave o se repite",
            [
                "Lo humillas en el canal para que ‘aprenda’",
                "Lo ignoras para no cortar el RP",
                "Lo expulsas del servidor sin expediente",
            ],
            2,
        ),
        (
            "Dos médicos discuten en OOC en medio de una escena con paciente. ¿Qué haces?",
            "Sacas el OOC de la escena, proteges el IC y medias fuera del rol clínico",
            [
                "Dejas que el OOC siga delante del paciente de rol",
                "Baneas a ambos sin escuchar",
                "Borras el canal clínico entero",
            ],
            0,
        ),
        (
            "Un médico de tu equipo se niega a cubrir sin un motivo de rol válido. ¿Control correcto?",
            "Pides justificación válida (IC/OOC) y aseguras cobertura alternativa según normas",
            [
                "Dejas urgencias descubiertas",
                "Baneas al instante por ‘falta de compromiso’",
                "Pones a un visitante a cubrir sin proceso",
            ],
            1,
        ),
        (
            "¿Qué debería tener como mínimo el registro de un ingreso de RP?",
            "Motivo de consulta, hallazgos relevantes, plan y quién es el responsable",
            [
                "Solo un emoji",
                "Nada si ‘hubo prisa’",
                "Datos inventados para trollear",
            ],
            3,
        ),
        (
            "En una escena crítica debes coordinarte con Enfermería. ¿Cómo se ve un buen control?",
            "Órdenes claras, confirmación de lo recibido y actualización del estado del paciente",
            [
                "Órdenes contradictorias a propósito ‘para probar al equipo’",
                "Solo discutir en OOC de forma tóxica",
                "No decir nada asumiendo que ‘ya saben’",
            ],
            1,
        ),
        (
            "¿Cómo debe ser tu relación de control con Docencia?",
            "Alinear qué competencias de RP se enseñan y validar estándares mínimos",
            [
                "Bloquear certificaciones por competencia de egos",
                "Ignorar por completo la formación del personal",
                "Dejar que Docencia ordene el tratamiento de cada paciente",
            ],
            2,
        ),
        (
            "En urgencias de RP llegan varios pacientes a la vez. ¿Cómo priorizas?",
            "Por gravedad y riesgo de la escena, no por el rango de Discord del jugador",
            [
                "Por quien tiene el rol de color más ‘alto’",
                "Siempre por orden de llegada, sin mirar gravedad",
                "Por quien pide más veces en el chat",
            ],
            0,
        ),
        (
            "Un especialista comete errores graves una y otra vez. ¿Qué control aplica?",
            "Expediente, límites a su práctica de RP y escalado según la norma del hospital",
            [
                "Lo dejas pasar porque ‘en otras cosas es bueno’",
                "Lo exposas en público para escarnio",
                "Le quitas el rol en silencio sin proceso",
            ],
            1,
        ),
        (
            "¿Qué NO es función de control del Director Médico?",
            "Ser siempre el médico tratante de cada paciente del servidor",
            [
                "Definir protocolos de escena",
                "Supervisar la calidad del equipo",
                "Coordinar cobertura de turnos críticos",
            ],
            2,
        ),
        (
            "Traspasas un paciente a otra área. ¿Qué información de control debes dar?",
            "Estado actual, qué se hizo ya y qué queda pendiente",
            [
                "Nada: ‘ya lo ven ellos’",
                "Inventar datos para que acepten más rápido",
                "Solo un chiste de pasillo",
            ],
            1,
        ),
        (
            "Un interno pregunta algo muy básico en plena emergencia. ¿Qué haces?",
            "Respuesta breve útil o lo reasignas para no romper la seguridad de la escena",
            [
                "Lo ridiculizas en público",
                "Lo ignoras por completo",
                "Le quitas el rol al instante",
            ],
            0,
        ),
        (
            "Hay dos líderes clínicos dando órdenes distintas. ¿Cómo unificas el control?",
            "Nombras un líder de escena y un canal único de órdenes",
            [
                "Dejas que ambos manden a la vez",
                "Eliges al más agresivo en OOC",
                "No nombras a nadie ‘por libertad creativa’",
            ],
            3,
        ),
        (
            "Circula un protocolo clínico de RP dudoso. ¿Qué haces?",
            "Lo contrastas con la norma del área y unificas el criterio del equipo",
            [
                "Dejas que cada médico invente el suyo",
                "Impones tu gusto sin mirar la norma",
                "Ocultas el protocolo al equipo",
            ],
            1,
        ),
        (
            "Te llega una queja sobre un médico de tu equipo. ¿Control correcto?",
            "Escuchas, contrastas hechos y aplicas el proceso del área o de RRHH",
            [
                "Lo defiendes a ciegas por lealtad",
                "Sancionas sin oír a la otra parte",
                "Publicas la queja en anuncios",
            ],
            2,
        ),
        (
            "La cobertura nocturna está débil. ¿Qué control preventivo pones?",
            "Plan de turnos, responsables claros y cómo escalar si alguien falta",
            [
                "‘Si alguien aparece, bien’",
                "Obligar a una sola persona 24/7 sin relevo",
                "Un plan secreto solo para tu círculo",
            ],
            0,
        ),
        (
            "Datos del paciente de RP. ¿Cómo se controla la confidencialidad?",
            "Se comparten solo con quien tiene necesidad asistencial en la escena",
            [
                "Se publican en general ‘para que todos roleen’",
                "Se usan como chisme de staff",
                "No se comparten ni con el equipo que atiende",
            ],
            1,
        ),
        (
            "Cierras una escena médica compleja. ¿Qué debe quedar claro?",
            "Estado final del paciente, plan siguiente y quién hace el seguimiento",
            [
                "Te desconectas sin decir el estado",
                "Cierras trolando al paciente",
                "Borras el canal donde estaba la info útil",
            ],
            2,
        ),
        (
            "¿Cuál es tu meta de control como Director Médico?",
            "Calidad y orden del RP clínico del equipo, no protagonizar todas las escenas",
            [
                "Medir éxito solo por cuánto tiempo estás tú en escena",
                "Prohibir residentes para ‘evitar errores’",
                "Ignorar protocolos si ‘hay feeling’",
            ],
            0,
        ),
        (
            "Un médico inventa diagnósticos imposibles solo para troll. ¿Qué haces?",
            "Cortas la incoherencia, reorientas la escena y aplicas norma si se repite",
            [
                "Lo premias por ser ‘divertido’",
                "Lo ignoras siempre",
                "Lo promocionas a jefe de servicio",
            ],
            1,
        ),
    ]),
    "DIR_ENFERMERIA": _p([
        (
            "Hay varios pacientes de rol a la vez. ¿Cómo decides a quién atender primero?",
            "Por gravedad y cuánto cuidado necesita, no por el rango de Discord",
            [
                "Siempre por orden de llegada, sin mirar gravedad",
                "Por quien escribe más mensajes",
                "Por el color del rol del paciente",
            ],
            1,
        ),
        (
            "Vas a administrar un medicamento en RP. ¿Qué control mínimo haces?",
            "Confirmas la orden, el paciente, la vía y dejas un registro breve",
            [
                "Solo miras el ‘color del frasco’ en la escena",
                "Omites el registro porque hay prisa",
                "Inventas la dosis para acelerar",
            ],
            2,
        ),
        (
            "Un auxiliar incumple un aislamiento de escena. ¿Qué haces?",
            "Lo corriges de inmediato, le explicas y reportas si el fallo es grave",
            [
                "Te ríes y no dices nada",
                "Lo baneas al instante sin contexto",
                "Lo ignoras para no cortar el RP",
            ],
            0,
        ),
        (
            "La orden del médico en escena no se entiende. ¿Control correcto?",
            "Pides aclaración antes de ejecutar algo mal",
            [
                "Haces lo contrario a propósito",
                "Humillas al médico en medio del RP",
                "Actúas igual arriesgando al paciente de rol",
            ],
            1,
        ),
        (
            "Falta personal en el turno. ¿Cómo controlas la situación?",
            "Redistribuyes tareas críticas y escalas la falta de cobertura",
            [
                "Abandonas a los pacientes ‘menos interesantes’",
                "Cierras el área en silencio",
                "Das rol de enfermero a cualquier visitante sin proceso",
            ],
            3,
        ),
        (
            "En una crisis de rol debes liderar al equipo de enfermería. ¿Qué haces?",
            "Asignas tareas, tiempos y un punto de control del equipo",
            [
                "Solo gritas sin roles claros",
                "Te sales de la escena",
                "Dejas que cada uno haga lo que quiera",
            ],
            1,
        ),
        (
            "Datos del paciente en RP. ¿Quién puede verlos?",
            "Solo el equipo que atiende por necesidad asistencial",
            [
                "Cualquiera en el canal general",
                "Sirven para chisme en el descanso",
                "Ni siquiera el médico tratante",
            ],
            2,
        ),
        (
            "Dos enfermeros pelean en pleno turno. ¿Control correcto?",
            "Los separas, escuchas, medias y documentas si afecta el servicio",
            [
                "Dejas la pelea en el ‘pasillo’ de rol",
                "Baneas al más nuevo",
                "Cierras el turno completo por sistema",
            ],
            0,
        ),
        (
            "¿Quién debe impulsar la formación de auxiliares?",
            "Dirección de Enfermería, con apoyo de Docencia si aplica",
            [
                "Solo Seguridad",
                "Solo cuando el Owner lo pide",
                "Nadie: ‘se aprende solo’",
            ],
            1,
        ),
        (
            "Entregas el turno al siguiente equipo. ¿Qué información mínima das?",
            "Pendientes, pacientes críticos y riesgos que siguen abiertos",
            [
                "Nada: ‘ya se ven’",
                "Datos falsos para quedar bien",
                "Solo tu drama OOC del día",
            ],
            2,
        ),
        (
            "Falta material de enfermería. ¿Qué haces?",
            "Lo reportas por el canal de Logística/área y registras el faltante",
            [
                "Solo lo comentas con memes",
                "Culpas a un compañero sin datos",
                "No reportas e improvisas siempre",
            ],
            1,
        ),
        (
            "El médico da dos órdenes que se contradicen. ¿Control de enfermería?",
            "Paras, aclaras con el líder de escena y unificas antes de actuar",
            [
                "Eliges la más peligrosa para ir más rápido",
                "Insultas al médico en OOC en medio de la escena",
                "Intentas hacer las dos a la vez",
            ],
            0,
        ),
        (
            "¿Qué NO es control de la Dirección de Enfermería?",
            "Sustituir el diagnóstico y el liderazgo médico en todas las escenas por sistema",
            [
                "Organizar turnos y estándares de cuidado",
                "Supervisar auxiliares y calidad de registros",
                "Coordinarse con el equipo médico tratante",
            ],
            3,
        ),
        (
            "Un paciente de rol está muy agitado en recepción. ¿Qué haces?",
            "Lo abordas con calma según protocolo y avisas a quien corresponda",
            [
                "Lo insultas para ‘imponer respeto’",
                "Ignoras un riesgo claro de escena",
                "Baneas al jugador al primer grito sin contexto",
            ],
            1,
        ),
        (
            "Hay dos versiones distintas del estado del mismo paciente. ¿Qué haces?",
            "Unificas la información con el equipo tratante (una fuente clara)",
            [
                "Dejas las dos versiones sin aclarar",
                "Borras los registros útiles",
                "Inventas una tercera versión ‘más épica’",
            ],
            2,
        ),
        (
            "Alguien incumple un protocolo de cuidado una y otra vez. ¿Control?",
            "Reentrenamiento, límites claros y escalado si no corrige",
            [
                "Lo dejas pasar por ser ‘buena gente’",
                "Solo humillación pública",
                "Le quitas el rol en silencio sin proceso",
            ],
            0,
        ),
        (
            "¿Cómo se ve una buena coordinación con Dirección Médica?",
            "Flujos claros de órdenes y feedback de lo que pasa en escena",
            [
                "Competencia tóxica por protagonismo",
                "Silencio total ‘para no molestar’",
                "Ignorar órdenes médicas por costumbre",
            ],
            1,
        ),
        (
            "Cierras el turno y queda un incidente abierto. ¿Qué dejas?",
            "Quién sigue el caso y en qué estado está el incidente",
            [
                "‘Mañana se ve’ sin dueño",
                "Lo ocultas al siguiente equipo",
                "Solo un chisme sin datos",
            ],
            2,
        ),
        (
            "¿Cuál es la meta de control de Enfermería?",
            "Cuidado ordenado, seguro para la escena y que se pueda enseñar al equipo",
            [
                "Que tú protagonices todas las escenas",
                "No registrar nada porque ‘es rol’",
                "Improvisar sin estándares",
            ],
            0,
        ),
        (
            "Un auxiliar inventa vías o dosis absurdas por troll. ¿Qué haces?",
            "Cortas la incoherencia, corriges y aplicas norma si se repite",
            [
                "Lo dejas porque ‘da risa’",
                "Lo ignoras siempre",
                "Lo asciendes por creatividad",
            ],
            1,
        ),
    ]),
    "DIR_RRHH": _p([
        (
            "Estás seleccionando a alguien para un cargo. ¿Qué control mínimo debe tener el proceso?",
            "Perfil del puesto, evaluación, decisión con motivo y registro",
            [
                "Elegir solo amigos sin criterios",
                "Decidir en secreto sin dejar registro",
                "Hacer un sorteo público",
            ],
            1,
        ),
        (
            "Llega una queja formal contra un jefe de servicio. ¿Cómo la controlas?",
            "La recibes, investigas con imparcialidad y resuelves dejando constancia",
            [
                "La borras ‘para proteger al jefe’",
                "La publicas en anuncios para generar drama",
                "Dejas que investigue solo el acusado",
            ],
            2,
        ),
        (
            "Entra alguien nuevo al hospital. ¿Qué debe incluir el onboarding?",
            "Normas básicas, organigrama, canales y qué se espera de su cargo",
            [
                "Nada: ‘ya se aprende’",
                "Admin del servidor al instante",
                "Solo el color del rol",
            ],
            0,
        ),
        (
            "Hay inactividad injustificada reiterada. ¿Qué control aplica?",
            "Aviso, plazos y medida según el reglamento",
            [
                "Premiar con un rol mejor",
                "Ban sorpresa sin avisos",
                "Avisos eternos sin nunca aplicar medida",
            ],
            1,
        ),
        (
            "¿Quién puede ver expedientes laborales?",
            "Solo roles autorizados y cuando hay necesidad de conocer",
            [
                "Todo el staff por comodidad",
                "Se publican en el canal general",
                "Se mandan por MD a amigos",
            ],
            3,
        ),
        (
            "Debes despedir a un miembro. ¿Qué es un control correcto?",
            "Causa clara, proceso y comunicación formal",
            [
                "Inventar la causa por rabia del momento",
                "Solo un emoji",
                "Que voten los visitantes",
            ],
            1,
        ),
        (
            "Un postulado miente sobre su experiencia de rol. ¿Qué haces?",
            "Rechazas, dejas registro y aplicas la norma contra suplantación",
            [
                "Lo apruebas igual",
                "Lo humillas en público más de lo necesario",
                "Lo pones de Director General",
            ],
            2,
        ),
        (
            "Tienes conflicto de interés en una contratación (es alguien cercano). ¿Control?",
            "Lo declaras y te abstienes de decidir",
            [
                "Decides igual porque ‘lo conoces mejor’",
                "Lo ocultas para agilizar",
                "Lo usas para meter a tu círculo",
            ],
            0,
        ),
        (
            "Hay un caso grave y debes hablar con Cancillería. ¿Cómo informas?",
            "Con hechos y propuestas de medidas proporcionales",
            [
                "Con rumores para forzar una reacción",
                "Ocultando datos críticos",
                "Difamando en un canal público",
            ],
            1,
        ),
        (
            "¿Qué NO es control de RRHH?",
            "Imponer sanciones clínicas sobre cómo tratar a un paciente en escena",
            [
                "Gestionar altas, bajas y procesos formales",
                "Mediar conflictos laborales del personal",
                "Custodiar expedientes y plazos",
            ],
            2,
        ),
        (
            "Detectas favoritismo en un proceso de selección. ¿Qué haces?",
            "Reabres el criterio, corriges y documentas la corrección",
            [
                "Solo actúas si ya hay escándalo público",
                "Usas el caso para vengarte",
                "Borras todo rastro del proceso",
            ],
            1,
        ),
        (
            "¿Qué métrica te ayuda a ver si RRHH controla bien?",
            "Tiempo en cubrir vacantes y calidad del onboarding",
            [
                "Cuántos roles de color repartiste",
                "Cuántos likes tiene tu anuncio",
                "Si ‘hay gente online’ aunque el proceso esté mal",
            ],
            0,
        ),
        (
            "Un miembro pide cambio de área. ¿Cómo lo controlas?",
            "Evalúas disponibilidad, impacto y normas del área de destino",
            [
                "Niegas siempre sin escuchar",
                "Aceptas sin consultar al área destino",
                "Lo baneas por pedir el cambio",
            ],
            3,
        ),
        (
            "Hay dos expedientes que se contradicen. ¿Qué haces?",
            "Conciliás hechos con evidencias y dejas una versión oficial",
            [
                "Dejas las dos versiones activas",
                "Borras el expediente completo",
                "Eliges la versión de tu amigo",
            ],
            1,
        ),
        (
            "Un Director te presiona para contratar a alguien. ¿Control?",
            "Mantienes el proceso y registras la presión indebida si existe",
            [
                "Te saltas el proceso por jerarquía",
                "Filtras al candidato en un canal público",
                "Renuncias a evaluar",
            ],
            2,
        ),
        (
            "Escalas una medida disciplinaria. ¿Cómo cuidas la proporcionalidad?",
            "Según gravedad, si se repite y lo que dice el reglamento publicado",
            [
                "Según tu humor del día",
                "Siempre al máximo ‘para escarmiento’",
                "Nunca: solo advertencias eternas",
            ],
            0,
        ),
        (
            "Cierras un caso de personal. ¿Qué debe quedar?",
            "Decisión, motivo, fecha y que el interesado fue notificado",
            [
                "Decisión sin motivo ‘porque ya se sabe’",
                "La decisión como chisme",
                "Sin avisar al interesado",
            ],
            1,
        ),
        (
            "A los 7 días ves que el onboarding quedó incompleto. ¿Qué haces?",
            "Completas lo que falta y asignas quién cierra el proceso",
            [
                "Culpas solo al nuevo",
                "Lo ignoras porque ‘ya está dentro’",
                "Repites todo desde cero sin necesidad",
            ],
            2,
        ),
        (
            "Alguien pide acceso a un expediente. ¿Control?",
            "Verificas si está autorizado y registras el acceso",
            [
                "Das copia a cualquiera del staff",
                "Niegas incluso a roles autorizados sin causa",
                "Publicas extractos en general",
            ],
            1,
        ),
        (
            "¿Cuál es la meta de control de RRHH?",
            "Procesos justos, trazables y alineados al reglamento del hospital",
            [
                "Procesos rápidos aunque sean opacos",
                "Procesos basados en amistades",
                "Procesos improvisados sin registro",
            ],
            0,
        ),
    ]),
    "DIR_DOCENCIA": _p([
        (
            "Para que una certificación sea válida, ¿qué control mínimo debe existir?",
            "Material de estudio, evaluación y registro del resultado/firmas según el protocolo",
            [
                "Aprobar por amistad",
                "Solo estar un minuto en un canal de voz",
                "Pago por fuera del rol",
            ],
            1,
        ),
        (
            "Alguien copia en el examen de una capacitación. ¿Qué haces?",
            "Anulas o aplicas la política académica y dejas constancia",
            [
                "Lo apruebas igual ‘para no generar drama’",
                "Le subes la nota por pena",
                "Le das el rol de Director",
            ],
            2,
        ),
        (
            "Un instructor favorece siempre a su círculo en las notas. ¿Control?",
            "Auditas evaluaciones, corriges y limitas al instructor si hace falta",
            [
                "Lo premias por ‘lealtad de equipo’",
                "Cierras toda Docencia por un solo caso",
                "Ignoras las quejas sin mirar evidencias",
            ],
            0,
        ),
        (
            "El temario está desactualizado respecto al RP del hospital. ¿Qué haces?",
            "Lo revisas con el área técnica y publicas la versión vigente",
            [
                "Dejas varias versiones contradictorias activas",
                "Lo ocultas ‘para que sea más difícil’",
                "Copias de otro server sin adaptarlo",
            ],
            1,
        ),
        (
            "¿Cómo te coordinas bien con Dirección Médica?",
            "Validas que lo enseñado se pueda usar y sea coherente en las escenas clínicas",
            [
                "Bloqueas a Médica por ego",
                "Dejas que Médica ignore la formación",
                "Dejas que Docencia ordene el tratamiento de cada paciente",
            ],
            3,
        ),
        (
            "¿Qué debe quedar registrado de una capacitación?",
            "Fecha, instructor, alumno y resultado verificable",
            [
                "Nada: ‘se recuerda’",
                "Solo un comentario oral en voz",
                "Se borra al día siguiente siempre",
            ],
            1,
        ),
        (
            "Te da pena un alumno y quieres aprobarlo aunque no llegue. ¿Qué es correcto?",
            "Mantienes el criterio del examen y ofreces reintento según la norma",
            [
                "Bajas la nota de corte en secreto solo para él",
                "Te burlas en público",
                "Le regalas el certificado",
            ],
            2,
        ),
        (
            "¿Qué NO es control de Docencia?",
            "Despedir personal de otras áreas sin el proceso de RRHH",
            [
                "Diseñar evaluaciones y el estándar de aprobación",
                "Supervisar instructores y el material",
                "Registrar las certificaciones emitidas",
            ],
            0,
        ),
        (
            "Aparecen dos certificados contradictorios del mismo alumno. ¿Qué haces?",
            "Verificas evidencias y dejas una emisión oficial corregida",
            [
                "Dejas los dos como válidos",
                "Borras todo el historial del alumno",
                "Eliges el más favorable a tu amigo",
            ],
            1,
        ),
        (
            "Los formadores están sobrecargados. ¿Cómo controlas la carga?",
            "Planificas turnos de formación y evitas quemarlos",
            [
                "Los obligas 24/7 ‘por vocación’",
                "Prohíbes formar por completo",
                "Improvisas el mismo día sin aviso",
            ],
            2,
        ),
        (
            "Un alumno no entiende el material. ¿Qué haces?",
            "Aclaras, ajustas la explicación y mantienes el estándar de evaluación",
            [
                "Lo insultas por ‘no leer’",
                "Bajas el estándar solo para ese caso sin criterio",
                "Le niegas cualquier apoyo legítimo",
            ],
            1,
        ),
        (
            "Piden un certificado sin haber hecho la evaluación que pide el protocolo. ¿Qué haces?",
            "Lo rechazas si el protocolo exige examen o práctica",
            [
                "Lo rechazas solo si el alumno es nuevo",
                "Lo aceptas si lo pide un Director amigo",
                "Lo aceptas si ya tiene el rol de color",
            ],
            0,
        ),
        (
            "Un Director te presiona para aprobar a alguien. ¿Control?",
            "Mantienes la independencia al evaluar y registras la presión indebida",
            [
                "Cedes por jerarquía",
                "Filtras al alumno en un canal público",
                "Cancelas el examen de todos",
            ],
            3,
        ),
        (
            "Das feedback al evaluado. ¿Cómo debe ser?",
            "Puntos concretos a mejorar, sin humillación",
            [
                "Burla pública",
                "Nada de feedback nunca",
                "Solo emojis de risa",
            ],
            1,
        ),
        (
            "Cada instructor inventa sus propias reglas de evaluación. ¿Qué haces?",
            "Unificas la rúbrica y exiges que todos la sigan",
            [
                "Dejas ‘libertad creativa’ total",
                "Sancionas a los alumnos por esa inconsistencia",
                "Ocultas la rúbrica oficial",
            ],
            2,
        ),
        (
            "¿Para qué sirve revalidar competencias?",
            "Mantener un estándar mínimo actualizado del RP del área",
            [
                "Castigar de forma arbitraria",
                "Quitar roles al azar",
                "No sirve: solo molesta",
            ],
            0,
        ),
        (
            "Publicas resultados de un examen. ¿Control correcto?",
            "Informas al alumno y al log del área según el protocolo",
            [
                "Doxxeas datos de más",
                "Ocultas el resultado al interesado",
                "Pones insultos en el log",
            ],
            1,
        ),
        (
            "Cierras una convocatoria de certificación. ¿Qué debe quedar archivado?",
            "Lista de resultados, firmas pendientes y el acta o registro final",
            [
                "Solo lo que recuerdes de memoria",
                "Una lista con datos sensibles innecesarios",
                "Nada: borras todo ‘para empezar limpio’",
            ],
            2,
        ),
        (
            "¿Cuál es la meta de control de Docencia?",
            "Formación justa, trazable y útil para el RP del hospital",
            [
                "Solo decorar con certificados sin evaluación real",
                "Favoritismos de círculo",
                "Improvisar sin material",
            ],
            0,
        ),
        (
            "Médica pide un curso nuevo urgente. ¿Qué haces?",
            "Evalúas la necesidad y armas el contenido con criterio del área",
            [
                "Niegas siempre",
                "Inventas contenido sin calidad",
                "Ignoras el pedido",
            ],
            1,
        ),
    ]),
    "DIR_LOGISTICA": _p([
        (
            "Hay emergencia y el stock es limitado. ¿Cómo decides qué entregar primero?",
            "Priorizas lo crítico para la atención y la operación, y registras las salidas",
            [
                "Priorizas a quien más insiste en el chat",
                "Priorizas lo decorativo porque ‘se ve mejor’",
                "Niegas todo para que los números se vean bonitos",
            ],
            1,
        ),
        (
            "El inventario no cuadra. ¿Qué control correctivo aplicas?",
            "Auditas, ajustas con documento y pones control para que no se repita",
            [
                "Inventas cifras para que cuadre",
                "Lo dejas: ‘no pasa nada’",
                "Culpas al bot sin revisar movimientos",
            ],
            2,
        ),
        (
            "Piden material urgente fuera del protocolo habitual. ¿Qué haces?",
            "Evalúas, entregas si procede y luego regularizas con registro",
            [
                "Niegas siempre por sistema",
                "Entregas a cualquiera sin control",
                "Borras el pedido para no dejar rastro",
            ],
            0,
        ),
        (
            "El almacén es restringido. ¿Qué debes controlar?",
            "Quién entra, por qué entra y qué material se mueve",
            [
                "Entrada libre si ‘parece staff’",
                "Entrada sin registrar movimientos",
                "Prohibir incluso con necesidad justificada siempre",
            ],
            1,
        ),
        (
            "Se pierde material. ¿Cómo lo controlas?",
            "Investigas causa y responsabilidad y tomas una medida preventiva",
            [
                "Ocultas el faltante",
                "Culpas a alguien al azar",
                "Cierras el hospital por un faltante menor",
            ],
            3,
        ),
        (
            "¿Cómo te coordinas bien con Dirección Médica?",
            "Previsión de demanda, canal claro de pedidos y confirmación de entrega",
            [
                "No hablar nunca con Médica",
                "Negar insumos críticos sin alternativa",
                "Entregar sin anotar nada",
            ],
            1,
        ),
        (
            "Reportas a Dirección General. ¿Qué debe llevar el reporte?",
            "Niveles de stock, riesgos y acciones con un responsable",
            [
                "Solo memes del área",
                "Solo quejas sin datos",
                "Números falsos ‘para no preocupar’",
            ],
            2,
        ),
        (
            "Organizas turnos de logística. ¿Qué buscas?",
            "Cobertura estable sin quemar al equipo",
            [
                "Una sola persona forzada 24/7",
                "Dejar el área vacía",
                "Improvisar cada día sin aviso",
            ],
            0,
        ),
        (
            "Un área pide de más sin justificar. ¿Qué haces?",
            "Cuestionas la necesidad, ajustas la cantidad y registras",
            [
                "Entregas todo sin control",
                "Insultas al que pidió",
                "Ignoras el pedido para siempre",
            ],
            1,
        ),
        (
            "¿Qué NO es control de Logística?",
            "Sancionar clínicamente a un médico por cómo trató a un paciente en escena",
            [
                "Controlar inventario y accesos del almacén",
                "Priorizar insumos críticos",
                "Reportar riesgo de desabastecimiento",
            ],
            2,
        ),
        (
            "El mismo ítem aparece salido dos veces en el registro. ¿Qué haces?",
            "Conciliás los movimientos y corriges el registro oficial",
            [
                "Dejas las dos salidas sin revisar",
                "Borras todo el inventario",
                "Culpas sin mirar horarios ni pruebas",
            ],
            1,
        ),
        (
            "Un proveedor interno incumple plazos una y otra vez. ¿Control?",
            "Aviso, alternativa temporal y escalado si se repite",
            [
                "Premiar al proveedor",
                "No avisary seguir improvisando",
                "Cerrar el área que usa el material como castigo",
            ],
            0,
        ),
        (
            "Se demora una entrega. ¿Qué comunicación de control das?",
            "Avisas el impacto y la nueva hora estimada al responsable del área",
            [
                "No avisas esperando que no se note",
                "Mientes una hora imposible",
                "Humillas al solicitante en público",
            ],
            3,
        ),
        (
            "¿Para qué sirve un plan de stock mínimo?",
            "Evitar quedarse en cero en lo esencial para operar el RP del hospital",
            [
                "Para que nadie pida nunca nada",
                "Para no hacer inventario porque ‘aburre’",
                "Para ocultar el estado del almacén",
            ],
            1,
        ),
        (
            "Dos áreas pelean por el mismo lote. ¿Cómo decides?",
            "Aplicas una prioridad institucional documentada y la comunicas",
            [
                "Se lo das al amigo del Director de Logística",
                "Se lo das al que grita más",
                "Tiras el lote ‘para que no peleen’",
            ],
            2,
        ),
        (
            "Detectas acceso indebido al almacén. ¿Qué haces?",
            "Cortas el acceso, reportas e investigas qué se movió",
            [
                "Cortas el acceso sin investigar salidas",
                "Publicas datos personales del implicado",
                "Lo ignoras porque ‘no faltó mucho’",
            ],
            0,
        ),
        (
            "Cierras el inventario del día. ¿Qué debe quedar?",
            "Entradas, salidas, faltantes y quién hizo el conteo",
            [
                "Solo lo que recuerdas de memoria",
                "Cifras inventadas para que se vea bonito",
                "Borras todo al apagar el PC",
            ],
            1,
        ),
        (
            "Te piden saltarte el registro ‘solo esta vez’. ¿Control?",
            "Mantienes el registro o documentas una excepción con límite",
            [
                "Cedes siempre por la prisa",
                "Humillas al solicitante en general",
                "Borras el historial anterior",
            ],
            2,
        ),
        (
            "¿Cuál es la meta de control de Logística?",
            "Que los recursos críticos estén disponibles y se puedan rastrear con cuentas claras",
            [
                "Caos sin números",
                "Stock solo para el círculo del Director",
                "Reportes falsos",
            ],
            0,
        ),
        (
            "¿Qué indicador te dice si Logística controla bien?",
            "Quiebres de stock crítico y tiempo real de reposición",
            [
                "Cuántos mensajes hay en el canal",
                "Si el Director está online",
                "Si el caos ‘se ve divertido’",
            ],
            1,
        ),
    ]),
    "JEFE_SEGURIDAD": _p([
        (
            "Hay un intruso en una zona restringida del hospital de RP. ¿Primera respuesta de control?",
            "Lo identificas, lo contienes según el protocolo y reportas",
            [
                "Lo ignoras si ‘no toca nada’",
                "Lo baneas sin evidencia de escena",
                "Huyes de la zona que te toca cubrir",
            ],
            1,
        ),
        (
            "En una escena de seguridad debes usar fuerza de RP. ¿Qué criterio aplica?",
            "Proporcional, de menos a más, y justificada por lo que pasa en la escena",
            [
                "Máxima fuerza desde el primer segundo siempre",
                "Al azar ‘para que quede épico’",
                "Prohibida incluso si hay riesgo claro en la escena",
            ],
            2,
        ),
        (
            "Hay un incidente violento cerca de donde se atiende a pacientes. ¿Qué priorizas?",
            "Asegurar la zona y permitir que la atención continúe con seguridad",
            [
                "Bloquear a todo el personal médico",
                "Evacuar sin avisar a nadie",
                "Cerrar el RP clínico por completo",
            ],
            0,
        ),
        (
            "Redactas un informe de incidente. ¿Qué debe incluir?",
            "Qué pasó, cuándo, quiénes estuvieron y qué acciones se tomaron",
            [
                "Solo opiniones personales sin hechos",
                "Nada escrito porque ‘ya se sabe’",
                "Insultos hacia los involucrados",
            ],
            1,
        ),
        (
            "Un guardia de tu equipo abusa de su autoridad. ¿Qué haces?",
            "Investigas y aplicas sanción o reentrenamiento según la norma",
            [
                "Lo cubres por lealtad",
                "Lo asciendes ‘para motivarlo’",
                "Ignoras las quejas reiteradas",
            ],
            3,
        ),
        (
            "Control de acceso a quirófano u otra área sensible. ¿Qué verificas?",
            "Quién es (rol) y por qué necesita entrar a esa escena",
            [
                "Dejas pasar a cualquiera que ‘parezca staff’",
                "Prohíbes a todo el personal clínico siempre",
                "No tienes un criterio estable",
            ],
            1,
        ),
        (
            "Alguien amenaza en OOC dentro de un canal del hospital. ¿Control correcto?",
            "Separas IC de OOC, documentas y escalas al staff de administración",
            [
                "Lo tratas solo como si fuera RP",
                "Respondes con más amenazas",
                "Borras todo sin dejar registro interno",
            ],
            2,
        ),
        (
            "Entrenamiento del equipo de seguridad. ¿En qué debe centrarse?",
            "Protocolos, comunicación en escena y uso proporcional de la autoridad",
            [
                "Caos improvisado ‘para practicar’",
                "Solo teoría en chat sin criterios claros",
                "Enseñar a ignorar el reglamento",
            ],
            0,
        ),
        (
            "¿Para qué sirven las rondas y los puestos fijos?",
            "Disuadir, detectar problemas temprano y cubrir puntos clave",
            [
                "Solo decorar el mapa",
                "Dejar puestos vacíos de forma crónica",
                "Solo hacer RP de descanso",
            ],
            1,
        ),
        (
            "¿Qué NO es control de Seguridad?",
            "Diagnosticar y tratar al paciente en lugar del médico",
            [
                "Controlar accesos sensibles",
                "Contener incidentes de seguridad en el RP",
                "Reportar riesgos a dirección o Cancillería",
            ],
            2,
        ),
        (
            "Hay dos versiones distintas de un incidente. ¿Qué haces?",
            "Contrastas evidencias y fijas un relato oficial interno para el staff",
            [
                "Publicas ambas versiones para generar drama",
                "Eliges la versión de tu amigo",
                "Borras las evidencias que incomodan",
            ],
            1,
        ),
        (
            "Un civil de RP arma altercado en recepción. ¿Control?",
            "Contención proporcional y reporte si el tema escala",
            [
                "Fuerza máxima sin ningún escalón",
                "Ignorar un peligro claro de escena",
                "Banear al jugador al primer grito sin contexto",
            ],
            0,
        ),
        (
            "En crisis debes informar a Cancillería. ¿Qué llevas?",
            "Hechos, plan de contención y estado de canales o accesos",
            [
                "Ocultas el tema ‘para no preocupar’",
                "Exageras sin tener plan",
                "Culpas a Cancillería del incidente",
            ],
            3,
        ),
        (
            "Te presionan para inventar un delito y hacer PK. ¿Qué haces?",
            "Exiges justificación seria de RP y proporcionalidad",
            [
                "Permites el PK por aburrimiento",
                "Lo haces obligatorio en anuncios",
                "Ocultas el motivo al resto del staff",
            ],
            1,
        ),
        (
            "Falla la cobertura de un puesto clave. ¿Control?",
            "Reasignas, registras el hueco y corriges el plan de turnos",
            [
                "Culpas en público sin plan",
                "Ignoras el hueco",
                "Cierras el hospital entero siempre",
            ],
            2,
        ),
        (
            "Custodia de evidencias de un incidente. ¿Qué es correcto?",
            "Conservarlas ordenadas para el staff autorizado",
            [
                "Publicarlas todas en el canal general",
                "Borrarlas al terminar la escena siempre",
                "Falsificar detalles ‘para que cierre mejor’",
            ],
            0,
        ),
        (
            "Un Admin pide saltarse la identificación ‘rápido’. ¿Qué haces?",
            "Mantienes el protocolo o documentas una excepción solo si hay riesgo real",
            [
                "Cedes siempre por el rango de Discord",
                "Lo humillas en el chat general",
                "Eliminas la identificación para todos",
            ],
            1,
        ),
        (
            "Cierras un incidente. ¿Qué debe quedar?",
            "Informe breve, estado de la zona y vuelta a la cobertura normal",
            [
                "Abandonar el puesto sin más",
                "Doxxing de los involucrados",
                "Premiar el abuso de fuerza",
            ],
            2,
        ),
        (
            "¿Cuál es la meta de control de Seguridad?",
            "Escenas seguras, accesos controlados y autoridad usada con proporcionalidad",
            [
                "Caos a propósito ‘para contenido’",
                "Abuso de poder como norma",
                "Cero reportes y cero aprendizaje",
            ],
            0,
        ),
        (
            "¿Qué indicador te dice si Seguridad controla bien?",
            "Incidentes con informe completo y puestos críticos cubiertos",
            [
                "Solo la cantidad de PK",
                "Si no hubo ban, ‘no pasó nada’",
                "Celebrar incidentes sin aprender de ellos",
            ],
            1,
        ),
    ]),
}
