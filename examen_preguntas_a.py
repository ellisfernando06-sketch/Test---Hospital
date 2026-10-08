# -*- coding: utf-8 -*-
"""Banco A: preguntas detalladas, claras, nivel RP de dirección."""
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
    "CANCILLER": _p([
        (
            "Dos Direcciones (por ejemplo Médica y Logística) discuten en OOC y eso está afectando turnos y escenas. "
            "Como Canciller, ¿cuál es la forma correcta de tomar el control?",
            "Mediar con calma, fijar un responsable de cada lado, acordar qué se hace y dejar constancia para el staff",
            [
                "Mediar solo en privado y no dejar rastro para que no haya ‘papel’",
                "Publicar la discusión en anuncios para que la comunidad presione",
                "Dejar que sigan discutiendo hasta que uno se rinda",
            ],
            1,
        ),
        (
            "El Vice Canciller publica una regla que choca con el reglamento del hospital. ¿Qué haces?",
            "La revisas, la corriges o la anulas según el organigrama y dejas registro de por qué",
            [
                "Dejas que cada área decida si la aplica o no",
                "La dejas pasar porque el Vice es de confianza",
                "Aplicas siempre la más reciente aunque contradiga el reglamento",
            ],
            2,
        ),
        (
            "Un Director cumple su área, pero ignora una decisión institucional tuya. ¿Cuál es el primer paso de control?",
            "Requerimiento claro, plazo para cumplir y escalado si no hay cambio",
            [
                "Ban inmediato sin avisar",
                "Burlarte del tema en el chat de staff",
                "Esperar a que lleguen tres quejas anónimas",
            ],
            0,
        ),
        (
            "Hay una crisis de imagen del servidor (drama público, quejas externas). ¿Qué priorizas?",
            "Mensaje oficial coordinado, contener el daño y mantener la operación del hospital",
            [
                "Borrar pruebas incómodas y guardar silencio",
                "Que solo hable el área más señalada, sin coordinar",
                "Esperar días a que ‘se enfríe’ solo",
            ],
            1,
        ),
        (
            "Alguien del staff filtra lo hablado en una reunión restringida de Cancillería. ¿Qué es correcto?",
            "Abrir proceso, aplicar una medida proporcional y reforzar la confidencialidad",
            [
                "Hacer un escarmiento público en el canal general",
                "Solo un aviso informal sin dejar registro",
                "Ignorarlo si el Owner no lo ordena por escrito",
            ],
            3,
        ),
        (
            "¿En qué momento es legítimo que Cancillería intervenga fuerte en un área operativa?",
            "Cuando hay riesgo para el hospital, incumplimiento grave o no hay mando claro en esa área",
            [
                "Cuando no te gusta el estilo de RP de un Director",
                "Cuando un residente te lo pide en privado",
                "Cuando estás aburrido en el turno",
            ],
            1,
        ),
        (
            "Quieres cambiar parte del organigrama (cargos o jerarquía). ¿Qué control mínimo hace falta?",
            "Validación de las autoridades competentes y comunicación formal al staff",
            [
                "Solo un mensaje privado entre dos personas",
                "Reacciones de emoji en el chat general",
                "Que lo decida el Director con más antigüedad",
            ],
            2,
        ),
        (
            "Respecto al Fundador/Owner, ¿cómo se entiende tu control como Canciller?",
            "Ejecutas la línea institucional dentro de los límites del organigrama y del Owner",
            [
                "Sustituyes al Owner en todas las decisiones",
                "Actúas sin rendir cuentas a nadie",
                "Solo haces actos ceremoniales sin peso real",
            ],
            0,
        ),
        (
            "Debes sancionar a un Director. ¿Qué criterio de control aplica?",
            "Proceso justo, medida proporcional al hecho y registro de lo decidido",
            [
                "Humillación pública para ‘dar ejemplo’",
                "Saltar el proceso porque ‘ya se sabe cómo es’",
                "Que voten los visitantes del servidor",
            ],
            1,
        ),
        (
            "Médica y Seguridad piden prioridad el mismo día y no cabe todo. ¿Qué haces?",
            "Defines una prioridad temporal con criterio del hospital y se la comunicas a ambas",
            [
                "Priorizas a quien escribió primero en el chat",
                "Priorizas a quien te cae mejor",
                "Dejas que peleen hasta que se cansen",
            ],
            2,
        ),
        (
            "Vas a ausentarte varios días. ¿Cuál es el control preventivo correcto?",
            "Delegas formalmente al Vice y avisas cobertura a las direcciones clave",
            [
                "Dices ‘si pasa algo avisen’ sin nombrar responsable",
                "Cualquier Admin online puede decidir por ti sin aviso",
                "No delegas para no ‘perder poder’",
            ],
            1,
        ),
        (
            "¿Qué diferencia control serio de microgestión en Cancillería?",
            "Marcas criterios y resultados; no escribes cada mensaje de cada área",
            [
                "Revisas y reescribes cada mensaje del staff",
                "Solo intervienes cuando hay drama en redes",
                "Nunca revisas si se cumplió lo acordado",
            ],
            3,
        ),
        (
            "Información sensible de alta dirección. ¿Quién debe verla?",
            "Solo quien tiene necesidad real de conocerla y el rol autorizado",
            [
                "Todo el staff por comodidad",
                "Solo tus amigos de confianza",
                "Un resumen en anuncios ‘por transparencia’",
            ],
            1,
        ),
        (
            "Dos Directores pelean en OOC en un canal visible. ¿Control correcto?",
            "Cortas la escalada, los pasas a un canal adecuado y documentas el acuerdo",
            [
                "Borras todo sin dejar contexto al resto del staff",
                "Dejas que se resuelvan a gritos en público",
                "Sancionas al que escribió menos mensajes",
            ],
            2,
        ),
        (
            "¿Qué métrica te dice si estás controlando bien la institución?",
            "Si se cumplen acuerdos, se responde a tiempo y los escalados se cierran",
            [
                "Cuántos mensajes mandas al día",
                "Cuántos likes tienen tus anuncios",
                "Cuánto miedo hay a las sanciones",
            ],
            0,
        ),
        (
            "El Vice da una orden urgente sin coordinar contigo. ¿Qué haces?",
            "Revisas el impacto, la alineas al criterio institucional y la ajustas si hace falta",
            [
                "La aceptas siempre solo por ser el Vice",
                "La rechazas todas por sistema",
                "La ignoras hasta el día siguiente",
            ],
            1,
        ),
        (
            "Alguien debe hablar en nombre del hospital hacia fuera. ¿Control correcto?",
            "Un mensaje único, alineado, con respaldo y límites claros",
            [
                "Cualquier staff con ‘buena intención’ puede hablar",
                "Se improvisa sin consultar a nadie",
                "Se responde agresivo para ‘imponer respeto’",
            ],
            2,
        ),
        (
            "Tienes muchas decisiones pendientes. ¿Cómo las ordenas?",
            "Priorizas por riesgo e impacto y asignas un dueño a cada punto",
            [
                "Por orden alfabético de áreas",
                "Primero lo más fácil para ‘cerrar rápido’",
                "Primero lo que más ruido genera en el chat",
            ],
            1,
        ),
        (
            "Tras resolver un conflicto grave entre áreas, ¿cómo cierras el tema?",
            "Dejas acuerdo explícito, responsables y un seguimiento breve",
            [
                "Dices ‘ya quedó’ sin seguimiento",
                "Humillas a una parte en público",
                "Borras el registro interno ‘para no reabrir heridas’",
            ],
            0,
        ),
        (
            "En una escena masiva de rol el hospital se desordena. ¿Tu prioridad como Canciller?",
            "Orden de mando, estabilidad de canales y que la operación pueda seguir",
            [
                "Tu propia escena de personaje primero",
                "Banear a media comunidad sin criterio",
                "Desconectarte hasta que pase",
            ],
            1,
        ),
    ]),
    "VICE_CANCILLER": _p([
        (
            "¿Cuándo puedes ejercer control casi como Canciller?",
            "Cuando el Canciller está ausente o te delegó formalmente ese alcance",
            [
                "Cuando tienes ganas de ordenar aunque el Canciller esté activo",
                "Cuando un solo Director te lo pide en privado",
                "Cuando un grupo presiona en el chat de staff",
            ],
            1,
        ),
        (
            "Tomas una decisión interina importante. ¿Qué debe quedar registrado?",
            "Motivo, alcance (qué cubre), fecha y hasta cuándo vale",
            [
                "Nada: si ‘todos lo saben’ basta",
                "Solo un MD a un amigo de confianza",
                "Un post público con datos sensibles de más",
            ],
            2,
        ),
        (
            "El Canciller anula una decisión tuya. ¿Qué es correcto?",
            "La acatas, documentas el cambio y alineas lo que se comunica al equipo",
            [
                "La acatas en público pero mantienes la tuya en privado",
                "Discutís el tema primero en un canal visible",
                "Solo la acatas si personalmente estás de acuerdo",
            ],
            0,
        ),
        (
            "En tu turno, RRHH y Docencia chocan por un proceso. ¿Cómo controlas?",
            "Medias, fijas un criterio temporal y reportas al Canciller si hace falta",
            [
                "Favoreces siempre a RRHH por ser ‘más staff’",
                "Cierras ambas áreas hasta nuevo aviso",
                "Evitas dejar registro para no ‘comprometerte’",
            ],
            1,
        ),
        (
            "¿Cuál es el límite sano de tu rol frente al Canciller?",
            "Complementas y cubres sin pretender reemplazar la línea institucional permanente",
            [
                "Intentas igualar su rango de hecho",
                "Solo haces tareas decorativas",
                "Puedes sustituir al Owner si ‘hace falta’",
            ],
            3,
        ),
        (
            "Un Director dice que tu cargo ‘no cuenta’. ¿Qué haces?",
            "Reafirmas el mandato con el organigrama y escalas si hay boicot",
            [
                "Sancionas al instante sin diálogo",
                "Ignoras por completo el comentario",
                "Renuncias para evitar problemas",
            ],
            1,
        ),
        (
            "Tienes información sensible de Cancillería. ¿Cómo la manejas?",
            "Solo la compartes por necesidad de conocer y en canales autorizados",
            [
                "Se la pasas a todo Admin por comodidad",
                "Solo a quien te cae bien",
                "Publicas un ‘resumen’ en general",
            ],
            2,
        ),
        (
            "Emergencia grande de rol en el servidor. ¿Qué priorizas?",
            "Cadena de mando, que los canales no colapsen y que se pueda seguir operando",
            [
                "Tu escena personal de personaje",
                "Bans masivos sin mirar el caso",
                "Esperar a que ‘se calme solo’",
            ],
            0,
        ),
        (
            "¿Cómo te coordinas bien con Dirección General?",
            "Separas lo institucional de lo operativo diario y sincronizan lo importante",
            [
                "Compiten por quién manda más",
                "No se comparten datos críticos",
                "General puede ignorar a Cancillería siempre",
            ],
            1,
        ),
        (
            "Das una orden y un área dice que choca con su protocolo. ¿Qué haces?",
            "Revisas el protocolo, ajustas la orden o escalas con una justificación clara",
            [
                "Impones la orden solo por jerarquía sin mirar el protocolo",
                "Anulas el protocolo del área en silencio",
                "No decides hasta que alguien se queje otra vez",
            ],
            2,
        ),
        (
            "Vas a faltar un tiempo previsible. ¿Control preventivo?",
            "Avisas cobertura y traspasas los pendientes críticos",
            [
                "Solo se lo dices a dos amigos",
                "No avisas porque ‘no debería pasar nada’",
                "Avisas en público con datos internos de más",
            ],
            1,
        ),
        (
            "Llega una queja formal sobre tu gestión. ¿Qué es correcto?",
            "La recibes, no retalias y dejas que siga el proceso imparcial",
            [
                "Cierras el caso tú mismo sin revisión",
                "Sancionas al que se quejó",
                "Borras la queja ‘para proteger la imagen’",
            ],
            0,
        ),
        (
            "¿Qué es control real y no solo apariencia?",
            "Decisiones con criterio, un responsable claro y seguimiento",
            [
                "Anuncios sin que nadie revise el cumplimiento",
                "Actuar solo cuando ya hay drama",
                "Delegar ‘en el aire’ sin nombrar a nadie",
            ],
            3,
        ),
        (
            "Un miembro del staff pide un atajo fuera de la norma ‘solo esta vez’. ¿Qué haces?",
            "Lo rechazas o, si cabe excepción, la documentas con límite",
            [
                "Lo rechazas y lo humillas en público",
                "Lo aceptas siempre si ahorra tiempo",
                "Lo aceptas solo para rangos altos sin dejar rastro",
            ],
            1,
        ),
        (
            "Tu mensaje y el del Canciller se contradicen. ¿Qué haces?",
            "Te alineas al mensaje institucional vigente y lo aclaras al equipo",
            [
                "Usas uno u otro según te convenga",
                "Impones el tuyo por ser el más reciente",
                "No aclaras nada ‘para no confundir más’",
            ],
            2,
        ),
        (
            "Al terminar tu guardia de control, ¿qué debes dejar?",
            "Estado de incidentes abiertos y traspaso a quien sigue",
            [
                "Nada si a tu juicio ‘no hubo nada grave’",
                "Un post con datos sensibles de miembros",
                "Solo un comentario oral imposible de seguir",
            ],
            0,
        ),
        (
            "Un Admin de Discord quiere saltarse a un Director. ¿Control correcto?",
            "Respetas la cadena de mando salvo riesgo grave bien justificado",
            [
                "Obedeces al Admin siempre por su permiso de Discord",
                "Saltas mandos para ir siempre más rápido",
                "Ignoras tanto al Admin como al Director",
            ],
            1,
        ),
        (
            "Das un visto bueno interino en un documento. ¿Cuándo vale?",
            "Solo dentro de lo que te delegaron y del alcance registrado",
            [
                "Siempre que el embed se vea bonito",
                "Por costumbre aunque no haya delegación",
                "Para favores personales de amigos",
            ],
            2,
        ),
        (
            "¿Cuál es el objetivo central de tu rol?",
            "Mantener estabilidad institucional cuando el Canciller no puede ejercer",
            [
                "Cuidar solo tu imagen personal",
                "Cerrar canales ‘por sistema’ sin criterio",
                "Imponer decisiones sin explicar el porqué",
            ],
            0,
        ),
        (
            "Hay un pendiente delicado y no estás seguro. ¿Qué haces?",
            "Consultas al Canciller o a la autoridad que corresponda antes de forzar",
            [
                "Improvisas aunque dañe al hospital",
                "Ignoras el tema por completo",
                "Baneas a alguien al azar para ‘cerrar el caso’",
            ],
            1,
        ),
    ]),
    "DIR_GENERAL": _p([
        (
            "Médica y Logística no se entienden y eso retrasa insumos en escena. ¿Control correcto?",
            "Reunión breve, responsables, plazo y un criterio de prioridad claro",
            [
                "Reproches públicos en el chat general",
                "Dejar que ‘se arreglen solos’ sin intervenir",
                "Cerrar Logística como castigo",
            ],
            1,
        ),
        (
            "Un Director lleva tiempo inactivo sin justificar. ¿Qué haces?",
            "Aviso formal, plazos y escalado a Cancillería/RRHH según la norma",
            [
                "Un aviso informal y olvidar el tema",
                "Ban inmediato sin proceso",
                "Nada: ‘ya volverá’",
            ],
            2,
        ),
        (
            "Vas a implantar un protocolo que afecta a varias áreas. ¿Cómo lo controlas?",
            "Consultas a quienes afecta, validas y lo difundes de forma oficial",
            [
                "Solo lo comentas con amigos del área",
                "Lo publicas de sorpresa sin consulta",
                "Consultas eternamente y nunca decides",
            ],
            0,
        ),
        (
            "¿Qué es control operativo y qué no lo es en Dirección General?",
            "Asegurar cobertura y flujos entre áreas; no ser el médico de cada paciente",
            [
                "Atender tú personalmente cada escena clínica",
                "Prohibir el RP médico para ‘ordenar’",
                "Solo publicar mensajes motivacionales",
            ],
            1,
        ),
        (
            "Armas las prioridades de la semana. ¿Buena práctica?",
            "Pocas prioridades medibles y comunicadas a las direcciones",
            [
                "Muchas prioridades vagas ‘para cubrir todo’",
                "Prioridades secretas solo en tu libreta",
                "Cambiarlas cada hora sin avisar",
            ],
            3,
        ),
        (
            "Preparas un reporte para Cancillería. ¿Qué debe llevar?",
            "Hechos, riesgos y acciones con responsables nombrados",
            [
                "Rumores de pasillo mezclados como si fueran hechos",
                "Solo opiniones personales",
                "Exageraciones para forzar una decisión",
            ],
            1,
        ),
        (
            "Delegas en un jefe de servicio. ¿Qué control te queda?",
            "Le das autonomía pero con indicadores y puntos de revisión",
            [
                "Autonomía total sin nunca revisar",
                "Microgestión de cada mensaje suyo",
                "Solo revisas cuando hay crisis pública",
            ],
            2,
        ),
        (
            "Dos Directores pelean en OOC. ¿Qué haces?",
            "Separas IC/OOC, medias en el canal adecuado y registras el acuerdo",
            [
                "Dejas que el conflicto siga dentro de la escena de RP",
                "Sancionas al más nuevo por defecto",
                "Borras el historial que el staff podría necesitar",
            ],
            0,
        ),
        (
            "Falta personal en varias áreas el mismo día. ¿Control?",
            "Reasignas cobertura de lo crítico e informas el impacto",
            [
                "Cierras el hospital sin avisar",
                "Culpas a un visitante",
                "Ignoras el problema hasta mañana",
            ],
            1,
        ),
        (
            "¿Qué indicador te dice si Dirección General está controlando bien?",
            "Cuánto tardan en resolverse los bloqueos entre áreas",
            [
                "Cuánto tiempo estás online",
                "Qué tan rápido respondes memes",
                "Cuánto hace del último ban",
            ],
            2,
        ),
        (
            "Un área pide una excepción al protocolo. ¿Cómo la controlas?",
            "Evalúas el riesgo, documentas la excepción y le pones límite de tiempo",
            [
                "La concedes siempre para quedar bien",
                "La niegas siempre sin analizar",
                "La resuelves en privado sin dejar rastro",
            ],
            1,
        ),
        (
            "En una operación hay dos personas dando órdenes distintas. ¿Qué haces?",
            "Declaras un líder de coordinación y un solo canal de órdenes",
            [
                "Dices que ‘todos mandan un poco’",
                "Impides hablar a todos sin nombrar líder",
                "Dejas de líder al que grita más fuerte",
            ],
            0,
        ),
        (
            "Seguridad avisa un riesgo en una zona clínica. ¿Control correcto?",
            "Coordinas contención y que la atención de RP pueda seguir con seguridad",
            [
                "Bloqueas toda atención médica",
                "Ignoras a Seguridad por ‘exagerados’",
                "Cierras canales clínicos sin plan",
            ],
            3,
        ),
        (
            "Cambias de turno con otro responsable de dirección. ¿Qué traspasas?",
            "Pendientes críticos, riesgos abiertos y contactos clave",
            [
                "Solo ‘si pasa algo avisen’",
                "Solo lo de tu escena personal",
                "Borras pendientes para ‘empezar limpio’",
            ],
            1,
        ),
        (
            "Te presionan para decidir sin datos. ¿Qué haces?",
            "Das una decisión provisional acotada o esperas poco con alguien encargado del dato",
            [
                "Decides en definitivo improvisando para ‘cerrar ya’",
                "Evitas decidir indefinidamente",
                "Te basas solo en el rumor más fuerte",
            ],
            2,
        ),
        (
            "¿Cuándo escalar de inmediato a Cancillería?",
            "Riesgo institucional, quiebre de mando o conflicto entre direcciones sin salida",
            [
                "Porque te criticaron en un meme",
                "Un problema menor que el área puede resolver",
                "Por perder una discusión trivial",
            ],
            0,
        ),
        (
            "Un Director pide recursos de otra área. ¿Control?",
            "Validas necesidad, impacto y acuerdo entre los responsables",
            [
                "Ordenas el traslado sin consultar",
                "Niegas por sistema sin oír motivos",
                "Lo hablas solo en un MD y no informas a nadie más",
            ],
            1,
        ),
        (
            "¿Cuál es tu meta de control como Director General?",
            "Que las direcciones trabajen alineadas y sin bloqueos crónicos",
            [
                "Que todas las escenas pasen por ti",
                "Que Cancillería no se entere de los problemas",
                "Ignorar el organigrama ‘si total funciona’",
            ],
            2,
        ),
        (
            "Hubo un fallo de coordinación. Al cerrar el tema, ¿qué dejas?",
            "Causa, corrección aplicada y quién hace el seguimiento",
            [
                "Ocultas la causa para no señalar a nadie",
                "Culpas en público sin corrección clara",
                "Nada de corrección porque ‘ya pasó’",
            ],
            0,
        ),
        (
            "Un protocolo se incumple una y otra vez en varias áreas. ¿Qué haces?",
            "Revisas el cuello de botella, ajustas el flujo y mides si se cumple",
            [
                "Castigas en público el primer error sin contexto",
                "Borras el protocolo y ya",
                "Echas la culpa siempre al área más nueva",
            ],
            1,
        ),
    ]),
}
