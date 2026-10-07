# -*- coding: utf-8 -*-
"""
Banco de 20 preguntas por dirección.
Nivel: difícil / enredado para RP de control directivo.
Opciones casi iguales; solo una centra el criterio correcto.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

Q = List[Tuple[str, List[str], int]]


def _item(texto: str, correcta: str, casi: List[str]) -> Tuple[str, List[str], int]:
    """Mezcla fija: correcta nunca siempre en la misma letra."""
    # rotación simple según longitud del enunciado
    pos = len(texto) % 4
    ops = list(casi[:3])
    while len(ops) < 3:
        ops.append("Delegar sin seguimiento ni registro")
    ops.insert(pos, correcta)
    ops = ops[:4]
    return (texto, ops, pos)


def _pack(rows: List[Tuple[str, str, List[str]]]) -> Q:
    return [_item(t, c, m) for t, c, m in rows]


BANCO: Dict[str, Q] = {
    "CANCILLER": _pack([
        (
            "Hay choque entre dos Direcciones con impacto operativo. ¿Cuál es la acción de control correcta del Canciller?",
            "Mediar con criterio institucional, fijar responsable y dejar constancia del acuerdo",
            [
                "Mediar en privado y no dejar rastro para evitar conflictos",
                "Mediar solo si ambas partes lo piden por escrito el mismo día",
                "Mediar publicando el drama en anuncios para presión social",
            ],
        ),
        (
            "Una directiva de Vice Cancillería contradice el reglamento. El control adecuado es:",
            "Revisarla, corregirla o anularla según jerarquía y dejar registro formal",
            [
                "Revisarla en silencio y dejar que cada área elija qué aplicar",
                "Revisarla solo si hay quejas públicas reiteradas",
                "Revisarla y aplicar la del Vice por ser más reciente",
            ],
        ),
        (
            "¿Qué define mejor el control institucional del Canciller frente a un Director?",
            "Supervisar alineación al organigrama y exigir rendición de cuentas sin sustituir su operación diaria",
            [
                "Supervisar cada tarea menor del Director en tiempo real",
                "Supervisar solo cuando el Director lo autorice",
                "Supervisar sustituyendo al Director en todas las escenas de RP",
            ],
        ),
        (
            "En crisis de imagen del servidor, la prioridad de control es:",
            "Respuesta oficial coordinada, contención del daño y continuidad operativa",
            [
                "Respuesta oficial improvisada y borrar evidencias incómodas",
                "Respuesta oficial solo del área más afectada, sin coordinación",
                "Respuesta oficial retrasada hasta que baje el drama",
            ],
        ),
        (
            "Un miembro de staff filtra una reunión restringida. El control correcto es:",
            "Abrir proceso, aplicar medida proporcional y reforzar confidencialidad",
            [
                "Abrir proceso solo si el Owner lo ordena por escrito",
                "Abrir proceso público en general para escarmiento",
                "Abrir proceso informal sin registro para no ‘complicar’",
            ],
        ),
        (
            "¿Cuándo es legítimo intervenir en un área operativa?",
            "Ante riesgo institucional, incumplimiento grave o vacío de mando",
            [
                "Ante cualquier desacuerdo menor de estilo de RP",
                "Ante pedidos de un solo residente sin validación",
                "Ante aburrimiento del Canciller en el turno",
            ],
        ),
        (
            "Cambio estructural del organigrama. Control mínimo aceptable:",
            "Validación de autoridades competentes y comunicación formal",
            [
                "Validación solo en un chat privado sin difusión",
                "Validación por reacción de emojis en general",
                "Validación unilateral del Director más antiguo",
            ],
        ),
        (
            "Relación Canciller–Owner en términos de control:",
            "Ejecución estratégica dentro de límites del organigrama y del Owner",
            [
                "Ejecución estratégica sustituyendo al Owner en todo",
                "Ejecución estratégica sin rendición de cuentas",
                "Ejecución estratégica solo ceremonial",
            ],
        ),
        (
            "Sanción a un Director. ¿Qué criterio de control aplica?",
            "Debido proceso, proporcionalidad y registro",
            [
                "Debido proceso público y humillación como ejemplo",
                "Debido proceso omitido si el Director es ‘problemático’",
                "Debido proceso reemplazado por votación de visitantes",
            ],
        ),
        (
            "Dos áreas piden prioridad contradictoria. El Canciller debe:",
            "Definir prioridad institucional temporal y comunicar el criterio",
            [
                "Definir prioridad según quién escriba primero",
                "Definir prioridad según afinidad personal",
                "Definir prioridad dejando que peleen hasta cansarse",
            ],
        ),
        (
            "Ausencia prolongada del Canciller. Control preventivo correcto:",
            "Delegación formal al Vice y aviso de cobertura a direcciones clave",
            [
                "Delegación informal ‘si pasa algo avisen’",
                "Delegación automática a cualquier Admin online",
                "Delegación inexistente para ‘no perder poder’",
            ],
        ),
        (
            "Un Director ignora una directiva institucional. Primer control:",
            "Requerimiento formal, plazo y escalado si persiste",
            [
                "Requerimiento en tono de burla en staff",
                "Requerimiento omitido y ban inmediato",
                "Requerimiento solo si hay tres quejas anónimas",
            ],
        ),
        (
            "¿Qué distingue control de microgestión en Cancillería?",
            "Fijar criterios y resultados, no ejecutar cada detalle operativo",
            [
                "Fijar criterios y además escribir cada mensaje del área",
                "Fijar criterios solo cuando hay crisis mediática",
                "Fijar criterios sin revisar nunca el cumplimiento",
            ],
        ),
        (
            "Información sensible de alta dirección. Control de acceso:",
            "Necesidad de conocer y roles autorizados",
            [
                "Necesidad de conocer ampliada a todo el staff",
                "Necesidad de conocer solo amigos de confianza",
                "Necesidad de conocer publicada en anuncios ‘por transparencia’",
            ],
        ),
        (
            "Conflicto OOC entre directores en canal visible. Control:",
            "Cortar la escalada, pasar a canal adecuado y documentar",
            [
                "Cortar la escalada borrando sin dejar contexto al staff",
                "Cortar la escalada dejando que ‘se resuelvan solos’ en público",
                "Cortar la escalada sancionando al que menos escribe",
            ],
        ),
        (
            "Métrica útil de control institucional:",
            "Cumplimiento de acuerdos, tiempos de respuesta y escalados resueltos",
            [
                "Cumplimiento medido solo por cantidad de mensajes",
                "Cumplimiento medido solo por likes en anuncios",
                "Cumplimiento medido solo por miedo a sanciones",
            ],
        ),
        (
            "El Vice emite una orden urgente sin coordinar. Tú:",
            "Validas impacto, alineas con criterio institucional y ajustas si hace falta",
            [
                "Validas siempre en automático por ser Vice",
                "Validas rechazando toda orden del Vice por defecto",
                "Validas ignorando el tema hasta mañana",
            ],
        ),
        (
            "Representación externa del hospital. Control correcto:",
            "Mensaje único alineado, con respaldo y límites claros",
            [
                "Mensaje libre de cualquier staff ‘con buena intención’",
                "Mensaje improvisado sin consultar autoridades",
                "Mensaje agresivo para ‘imponer respeto’",
            ],
        ),
        (
            "Cola de decisiones pendientes. Mejor práctica de control:",
            "Priorizar por riesgo/impacto y asignar dueño a cada punto",
            [
                "Priorizar por orden alfabético de áreas",
                "Priorizar lo más fácil para cerrar rápido",
                "Priorizar lo que genera más ruido en el chat",
            ],
        ),
        (
            "Tras resolver un conflicto grave, el cierre de control incluye:",
            "Acuerdo explícito, responsables y seguimiento breve",
            [
                "Acuerdo implícito ‘ya quedó’ sin seguimiento",
                "Acuerdo público humillante para una parte",
                "Acuerdo borrado para ‘no reabrir heridas’ sin registro interno",
            ],
        ),
    ]),
    "VICE_CANCILLER": _pack([
        (
            "Actúas con plenitud de control cuando:",
            "Hay ausencia del Canciller o delegación formal expresa",
            [
                "Hay ganas de ‘ordenar’ aunque el Canciller esté activo",
                "Hay pedido informal de un solo Director",
                "Hay presión de un grupo en staff-general",
            ],
        ),
        (
            "Decisión interina tuya. Control documental mínimo:",
            "Registro con motivo, alcance, fecha y vigencia",
            [
                "Registro mental suficiente si ‘todos lo saben’",
                "Registro solo en MD al amigo de confianza",
                "Registro público detallando datos sensibles innecesarios",
            ],
        ),
        (
            "El Canciller anula tu decisión. Control correcto:",
            "Acatar, documentar el cambio y alinear comunicación",
            [
                "Acatar en apariencia y mantener la tuya en privado",
                "Acatar después de discutir el tema en público",
                "Acatar solo si estás de acuerdo personalmente",
            ],
        ),
        (
            "Disputa RRHH–Docencia en tu turno. Control:",
            "Mediar, fijar criterio temporal y reportar al Canciller si aplica",
            [
                "Mediar favoreciendo siempre a RRHH por ‘ser staff’",
                "Mediar cerrando ambas áreas hasta nuevo aviso",
                "Mediar evitando cualquier registro ‘para no comprometerse’",
            ],
        ),
        (
            "Límite de tu control respecto al Canciller:",
            "Complementar y cubrir sin desplazar la línea institucional permanente",
            [
                "Complementar intentando igualar rango de facto",
                "Complementar solo en tareas decorativas",
                "Complementar sustituyendo al Owner si hace falta",
            ],
        ),
        (
            "Director cuestiona tu legitimidad. Control:",
            "Reafirmar mandato con organigrama y escalar si hay boicot",
            [
                "Reafirmar con sanción inmediata sin diálogo",
                "Reafirmar ignorando por completo el cuestionamiento",
                "Reafirmar renunciando para ‘evitar problemas’",
            ],
        ),
        (
            "Información de Cancillería en tu poder. Control de difusión:",
            "Solo necesidad de conocer y canales autorizados",
            [
                "Solo necesidad de conocer ampliada a todo Admin",
                "Solo necesidad de conocer según simpatía",
                "Solo necesidad de conocer publicada ‘en resumen’ en general",
            ],
        ),
        (
            "Emergencia de rol masiva. Tu prioridad de control:",
            "Cadena de mando, estabilidad de canales y continuidad",
            [
                "Cadena de mando sacrificada por tu escena personal",
                "Cadena de mando reemplazada por bans masivos sin criterio",
                "Cadena de mando ignorada ‘hasta que calme’",
            ],
        ),
        (
            "Coordinación con Dirección General. Control sano:",
            "Separar estrategia institucional de operación diaria y sincronizar",
            [
                "Separar equipos y competir por autoridad",
                "Separar sin compartir información crítica",
                "Separar dejando que General ignore Cancillería",
            ],
        ),
        (
            "Orden tuya choca con un protocolo de área. Control:",
            "Verificar protocolo, ajustar la orden o escalar con justificación",
            [
                "Verificar imponiendo la orden por jerarquía sin mirar el protocolo",
                "Verificar anulando el protocolo en silencio",
                "Verificar evitando decidir hasta que alguien se queje",
            ],
        ),
        (
            "Ausencia tuya previsible. Control preventivo:",
            "Aviso de cobertura y traspaso de pendientes críticos",
            [
                "Aviso opcional solo a amigos cercanos",
                "Aviso inexistente porque ‘no debería pasar nada’",
                "Aviso público de datos internos innecesarios",
            ],
        ),
        (
            "Queja formal contra tu gestión. Control:",
            "Recibir, no retaliar y seguir proceso imparcial",
            [
                "Recibir y cerrar el caso tú mismo sin revisión",
                "Recibir y sancionar al quejoso por ‘faltar al respeto’",
                "Recibir y borrar la queja ‘para proteger la imagen’",
            ],
        ),
        (
            "¿Qué es control y no apariencia de control?",
            "Decisiones con criterio, dueño y seguimiento",
            [
                "Decisiones anunciadas sin seguimiento",
                "Decisiones solo reactivas cuando hay drama",
                "Decisiones delegadas a nadie en concreto",
            ],
        ),
        (
            "Staff pide ‘atajo’ fuera de norma. Control:",
            "Rechazar el atajo o canalizar excepción documentada",
            [
                "Rechazar y humillar en público",
                "Aceptar el atajo si ahorra tiempo siempre",
                "Aceptar el atajo solo para rangos altos sin registro",
            ],
        ),
        (
            "Doble mensaje contradictorio tuyo y del Canciller. Control:",
            "Alinear al mensaje institucional vigente y aclarar al equipo",
            [
                "Alinear manteniendo ambos mensajes ‘según convenga’",
                "Alinear imponiendo el tuyo por ser más reciente",
                "Alinear sin aclarar para no ‘confundir más’",
            ],
        ),
        (
            "Indicador de que estás controlando bien el turno:",
            "Pendientes claros, escalados a tiempo y áreas informadas",
            [
                "Pendientes acumulados ‘para revisar luego’",
                "Pendientes resueltos solo a gritos",
                "Pendientes inexistentes porque no preguntas nada",
            ],
        ),
        (
            "Un Admin presiona para saltarse a un Director. Control:",
            "Respetar cadena de mando salvo riesgo grave justificado",
            [
                "Respetar al Admin siempre por rango de Discord",
                "Respetar saltando mandos para ir más rápido siempre",
                "Respetar ignorando tanto al Admin como al Director",
            ],
        ),
        (
            "Cierre de tu guardia de control. Debe incluir:",
            "Estado de incidentes abiertos y handoff al Canciller/continidad",
            [
                "Estado omitido si no hubo ‘nada grave’ a tu juicio",
                "Estado publicado con datos sensibles de miembros",
                "Estado solo verbal sin posibilidad de seguimiento",
            ],
        ),
        (
            "Firma o visto bueno interino. Control de validez:",
            "Solo dentro de la delegación y el alcance registrado",
            [
                "Solo si queda bonito en el embed",
                "Solo como costumbre aunque no haya delegación",
                "Solo para asuntos personales de amigos",
            ],
        ),
        (
            "Objetivo central de tu rol de control:",
            "Estabilidad institucional cuando el Canciller no puede ejercer",
            [
                "Estabilidad de tu imagen personal ante el server",
                "Estabilidad lograda cerrando canales por sistema",
                "Estabilidad impuesta sin comunicar criterios",
            ],
        ),
    ]),
    "DIR_GENERAL": _pack([
        (
            "Fallo de coordinación Médica–Logística. Control correcto:",
            "Mesa breve, responsables, plazo y criterio de prioridad",
            [
                "Mesa pública de reproches en general",
                "Mesa omitida dejando que ‘se arreglen solos’",
                "Mesa que cierra Logística como castigo",
            ],
        ),
        (
            "Director inactivo sin justificación. Control:",
            "Aviso formal, plazos y escalado a Cancillería/RRHH según norma",
            [
                "Aviso informal y olvidar el tema",
                "Aviso reemplazado por ban inmediato",
                "Aviso innecesario porque ‘ya volverá’",
            ],
        ),
        (
            "Protocolo transversal nuevo. Control de implantación:",
            "Consulta a afectados, validación y difusión oficial",
            [
                "Consulta solo a amigos del área",
                "Consulta omitida y publicación sorpresa",
                "Consulta eterna sin decidir nunca",
            ],
        ),
        (
            "¿Qué es control operativo y no sustitución clínica?",
            "Asegurar cobertura y flujos; no ser el médico de cada paciente",
            [
                "Asegurar cobertura atendiendo tú cada escena",
                "Asegurar cobertura prohibiendo el RP médico",
                "Asegurar cobertura solo con anuncios motivacionales",
            ],
        ),
        (
            "Prioridades semanales. Buena práctica de control:",
            "Pocas prioridades medibles comunicadas a direcciones",
            [
                "Muchas prioridades vagas ‘para cubrir todo’",
                "Prioridades secretas solo en tu libreta",
                "Prioridades cambiadas cada hora sin aviso",
            ],
        ),
        (
            "Reporte a Cancillería de calidad implica:",
            "Hechos, riesgos y acciones con responsables",
            [
                "Hechos mezclados con rumores de pasillo",
                "Hechos omitidos y solo opiniones",
                "Hechos exagerados para forzar decisiones",
            ],
        ),
        (
            "Delegación a jefe de servicio. Control residual:",
            "Autonomía con indicadores y puntos de control",
            [
                "Autonomía total sin revisión",
                "Autonomía cero y microgestión de cada mensaje",
                "Autonomía solo cuando hay crisis pública",
            ],
        ),
        (
            "Conflicto OOC entre directores. Control:",
            "Separar IC/OOC, mediar en canal adecuado y registrar acuerdos",
            [
                "Separar dejando el conflicto en la escena de RP",
                "Separar sancionando al más nuevo por defecto",
                "Separar borrando historial útil al staff",
            ],
        ),
        (
            "Falta de personal en varias áreas. Control:",
            "Reasignar cobertura crítica e informar impacto",
            [
                "Reasignar cerrando el hospital sin aviso",
                "Reasignar culpando a un visitante",
                "Reasignar ignorando el problema hasta mañana",
            ],
        ),
        (
            "Indicador útil de control general:",
            "Tiempo de resolución de bloqueos entre áreas",
            [
                "Tiempo online del Director General",
                "Tiempo de respuesta en memes",
                "Tiempo desde el último ban",
            ],
        ),
        (
            "Un área pide excepción al protocolo. Control:",
            "Evaluar riesgo, documentar excepción y límite temporal",
            [
                "Evaluar y conceder siempre para ‘quedar bien’",
                "Evaluar y negar siempre sin análisis",
                "Evaluar en privado sin dejar rastro",
            ],
        ),
        (
            "Doble mando confuso en una operación. Control:",
oms            "Declarar un líder de coordinación y canal único de órdenes",
            [
                "Declarar que ‘todos mandan un poco’",
                "Declarar silencio total sin líder",
                "Declarar líder al que grite más fuerte",
            ],
        ),
        (
            "Seguridad reporta riesgo en un área clínica. Control:",
            "Coordinar contención y continuidad asistencial de RP",
            [
                "Coordinar bloqueando toda atención médica",
                "Coordinar ignorando a Seguridad por ‘exagerados’",
                "Coordinar cerrando canales clínicos sin plan",
            ],
        ),
        (
            "Cambio de turno de dirección. Handoff mínimo:",
            "Pendientes críticos, riesgos abiertos y contactos clave",
            [
                "Pendientes ‘si pasa algo avisan’",
                "Pendientes solo de tu escena personal",
                "Pendientes borrados para empezar limpio",
            ],
        ),
        (
            "Presión para decidir sin datos. Control:",
            "Decisión provisional acotada o espera breve con responsable de dato",
            [
                "Decisión definitiva improvisada para ‘cerrar ya’",
                "Decisión evitada indefinidamente",
                "Decisión basada solo en el rumor más fuerte",
            ],
        ),
        (
            "¿Cuándo escalar a Cancillería de inmediato?",
            "Riesgo institucional, quiebre de mando o conflicto entre direcciones sin salida",
            [
                "Riesgo de que te critiquen en memes",
                "Riesgo operativo menor resoluble en el área",
                "Riesgo de perder una discusión trivial",
            ],
        ),
        (
            "Control de calidad de un proceso no es:",
            "Castigar públicamente el primer error sin contexto",
            [
                "Revisar cuellos de botella y tiempos",
                "Ajustar el flujo con las áreas",
                "Medir cumplimiento de acuerdos",
            ],
        ),
        (
            "Un Director pide recursos de otra área. Control:",
            "Validar necesidad, impacto y acuerdo entre responsables",
            [
                "Validar ordenando el traslado sin consultar",
                "Validar negando por sistema sin oír motivos",
                "Validar en un MD y no informar a nadie más",
            ],
        ),
        (
            "Objetivo central de tu control como Dir. General:",
            "Que las direcciones operen alineadas y sin bloqueos crónicos",
            [
                "Que todas las escenas pasen por ti",
                "Que Cancillería no se entere de problemas",
                "Que el organigrama se ignore ‘si funciona’",
            ],
        ),
        (
            "Tras un fallo de coordinación, el cierre de control incluye:",
            "Causa, corrección y dueño del seguimiento",
            [
                "Causa oculta para no señalar a nadie nunca",
                "Causa amplificada para culpar en público",
                "Causa sin corrección ‘porque ya pasó’",
            ],
        ),
    ]),
    "DIR_MEDICO": _pack([
        (
            "Código en rol desordenado. Tu control como Director Médico:",
            "Asignar roles de escena, líder clínico y punto de información",
            [
                "Asignar que cada uno improvise ‘con creatividad’",
                "Asignar silencio total sin líder",
                "Asignar la escena al que escribe más rápido",
            ],
        ),
        (
            "Residente comete error de protocolo. Control formativo:",
            "Corregir en el momento, enseñar y registrar si es grave/reiterado",
            [
                "Corregir humillando en el canal para que ‘aprenda’",
                "Corregir ignorando ‘para no cortar el RP’",
                "Corregir expulsando del server sin expediente",
            ],
        ),
        (
            "Conflicto OOC entre médicos en escena. Control:",
            "Pausar o sacar el OOC, preservar IC y mediar fuera",
            [
                "Pausar dejando que el OOC continúe en la escena",
                "Pausar baneando a ambos sin escuchar",
                "Pausar borrando el canal clínico",
            ],
        ),
        (
            "Médico se niega a cobertura sin motivo de rol. Control:",
            "Exigir justificación IC/OOC válida y asegurar cobertura alternativa",
            [
                "Exigir nada y dejar urgencias descubiertas",
                "Exigir ban inmediato por ‘falta de compromiso’",
                "Exigir que un visitante cubra sin proceso",
            ],
        ),
        (
            "Documentación mínima de un ingreso de RP. Control de calidad:",
            "Motivo, hallazgos relevantes, plan y responsable",
            [
                "Motivo solo con un emoji",
                "Motivo omitido si ‘hubo prisa’",
                "Motivo inventado para troll de escena",
            ],
        ),
        (
            "Coordinación con Enfermería en escena crítica. Control:",
            "Órdenes claras, confirmación y actualización de estado",
            [
                "Órdenes contradictorias para ‘probar al equipo’",
                "Órdenes solo por OOC tóxico",
                "Órdenes omitidas asumiendo que ‘ya saben’",
            ],
        ),
        (
            "Relación de control con Docencia:",
            "Alinear competencias clínicas de RP y validar estándares",
            [
                "Alinear bloqueando certificaciones por competencia de egos",
                "Alinear ignorando la formación del personal",
                "Alinear dejando que Docencia dicte cada tratamiento en escena",
            ],
        ),
        (
            "Priorización de pacientes en urgencias de RP. Criterio de control:",
            "Gravedad y riesgo de la escena, no el rango Discord",
            [
                "Gravedad igualada al que tiene mejor rol de color",
                "Gravedad sustituida por orden de llegada siempre",
                "Gravedad decidida por quien pide más en el chat",
            ],
        ),
        (
            "Error grave reiterado de un especialista. Control:",
            "Expediente, límites de práctica de RP y escalado según norma",
            [
                "Expediente omitido por ser ‘bueno en otras cosas’",
                "Expediente público para escarnio",
                "Expediente reemplazado por quitarle el rol en silencio sin proceso",
            ],
        ),
        (
            "¿Qué NO es control directivo médico?",
            "Sustituir siempre al médico tratante en cada paciente del server",
            [
                "Definir protocolos de escena",
                "Supervisar calidad del equipo",
                "Coordinar cobertura de turnos críticos",
            ],
        ),
        (
            "Transferencia a otra área. Control de información:",
            "Estado actual, lo hecho y pendientes explícitos",
            [
                "Estado omitido ‘ya lo ven ellos’",
                "Estado inventado para acelerar",
                "Estado solo en un chiste de pasillo",
            ],
        ),
        (
            "Interno pregunta algo básico en plena escena. Control:",
            "Respuesta breve útil o reasignación para no romper seguridad de escena",
            [
                "Respuesta ridiculizándolo en público",
                "Respuesta ignorándolo por completo",
                "Respuesta quitándole el rol al instante",
            ],
        ),
        (
            "Doble liderazgo clínico confuso. Control:",
            "Nombrar un líder de escena y un canal de órdenes",
            [
                "Nombrar que ambos den órdenes a la vez",
                "Nombrar líder al más agresivo en OOC",
                "Nombrar ninguno para ‘libertad creativa’",
            ],
        ),
        (
            "Material/protocolo clínico de RP dudoso. Control:",
            "Contrastar con norma del área y unificar criterio",
            [
                "Contrastar dejando que cada médico invente el suyo",
                "Contrastar imponiendo tu gusto sin mirar la norma",
                "Contrastar ocultando el protocolo al equipo",
            ],
        ),
        (
            "Indicador de control del servicio médico:",
            "Escenas críticas con roles claros y handoffs completos",
            [
                "Escenas medidas solo por duración del voice",
                "Escenas medidas solo por cantidad de muertes PK",
                "Escenas sin ningún registro ‘porque es RP’",
            ],
        ),
        (
            "Queja sobre un médico de tu equipo. Control:",
            "Escuchar, contrastar hechos y aplicar proceso del área/RRHH",
            [
                "Escuchar y defender a ciegas por lealtad",
                "Escuchar y sancionar sin oír a la otra parte",
                "Escuchar y publicar la queja en anuncios",
            ],
        ),
        (
            "Cobertura nocturna débil. Control preventivo:",
            "Plan de turnos, responsables y escalado si falla",
            [
                "Plan inexistente ‘si alguien aparece bien’",
                "Plan que obliga a una sola persona 24/7 sin relevo",
                "Plan secreto solo para tu círculo",
            ],
        ),
        (
            "Confidencialidad del paciente de RP. Control:",
            "Compartir solo con necesidad asistencial de la escena",
            [
                "Compartir en general ‘para que todos roleen’",
                "Compartir como chisme de staff",
                "Compartir nunca ni con el equipo tratante",
            ],
        ),
        (
            "Cierre de una escena médica compleja. Control:",
            "Estado final, plan y responsable de seguimiento",
            [
                "Estado final omitido al desconectarte",
                "Estado final convertido en troll al paciente",
                "Estado final borrado del canal útil",
            ],
        ),
        (
            "Tu meta de control como Director Médico:",
            "Calidad y orden del RP clínico del equipo, no protagonismo eterno",
            [
                "Calidad medida solo por tu tiempo en escena",
                "Calidad lograda prohibiendo residentes",
                "Calidad ignorando protocolos ‘si hay feeling’",
            ],
        ),
    ]),
    "DIR_ENFERMERIA": _pack([
        (
            "Varios pacientes a la vez. Criterio de control de prioridad:",
            "Gravedad y dependencia, no el rango Discord",
            [
                "Gravedad igualada al orden de llegada siempre",
                "Gravedad según quién escribe más mensajes",
                "Gravedad según color del rol del paciente",
            ],
        ),
        (
            "Administración de medicación en RP. Control mínimo:",
            "Verificar orden, paciente, vía y dejar registro breve",
            [
                "Verificar solo el color del ‘frasco’ en RP",
                "Verificar omitiendo registro ‘por prisa’",
                "Verificar inventando dosis para acelerar la escena",
            ],
        ),
        (
            "Auxiliar incumple un aislamiento de escena. Control:",
            "Corregir de inmediato, educar y reportar si es grave",
            [
                "Corregir riéndose sin más",
                "Corregir baneando al instante sin contexto",
                "Corregir ignorando para no cortar el RP",
            ],
        ),
        (
            "Orden médica confusa en escena. Control:",
            "Pedir aclaración antes de ejecutar mal",
            [
                "Pedir nada y hacer lo contrario a propósito",
                "Pedir humillando al médico en voz alta de RP",
                "Pedir omitiendo y arriesgando al paciente de rol",
            ],
        ),
        (
            "Turno corto de personal. Control:",
            "Redistribuir tareas críticas y escalar falta de cobertura",
            [
                "Redistribuir abandonando pacientes menos ‘interesantes’",
                "Redistribuir cerrando el área en silencio",
                "Redistribuir dando rol de enfermero a cualquiera sin proceso",
            ],
        ),
        (
            "Liderazgo de enfermería en crisis. Control:",
            "Asignar tareas, tiempos y un punto de control del equipo",
            [
                "Asignar gritos sin roles claros",
                "Asignar salida de la escena del líder",
                "Asignar que cada uno haga lo que quiera",
            ],
        ),
        (
            "Confidencialidad del paciente. Control:",
            "Solo necesidad asistencial del equipo que atiende",
            [
                "Solo necesidad publicada en general",
                "Solo necesidad para chisme de descanso",
                "Solo necesidad nunca ni con el médico tratante",
            ],
        ),
        (
            "Conflicto entre enfermeros en turno. Control:",
            "Separar, escuchar, mediar y documentar si afecta servicio",
            [
                "Separar dejando la pelea en el pasillo de rol",
                "Separar baneando al más nuevo",
                "Separar cerrando el turno completo por sistema",
            ],
        ),
        (
            "Formación de auxiliares. Responsabilidad de control:",
            "Impulsarla desde Enfermería con apoyo de Docencia si aplica",
            [
                "Impulsarla dejándola solo a Seguridad",
                "Impulsarla solo cuando el Owner lo pida",
                "Impulsarla nunca porque ‘se aprende solo’",
            ],
        ),
        (
            "Entrega de turno. Control mínimo:",
            "Pendientes, pacientes críticos y riesgos abiertos",
            [
                "Pendientes omitidos ‘ya se ven’",
                "Pendientes falsos para quedar bien",
                "Pendientes solo de tu drama OOC",
            ],
        ),
        (
            "Falta material de enfermería. Control:",
            "Reportar por canal de Logística/área y registrar el faltante",
            [
                "Reportar solo en memes",
                "Reportar culpando a un compañero sin datos",
                "Reportar nada e improvisar siempre",
            ],
        ),
        (
            "Indicador de control del servicio de enfermería:",
            "Cobertura de turnos y escenas con roles de cuidado claros",
            [
                "Cobertura medida solo por tiempo en voice",
                "Cobertura medida solo por cantidad de mensajes",
                "Cobertura ignorada si el Director está online",
            ],
        ),
        (
            "Médico da órdenes contradictorias. Control de enfermería:",
            "Detener, clarificar con el líder de escena y unificar",
            [
                "Detener eligiendo la orden más peligrosa por velocidad",
                "Detener insultando al médico en OOC en medio de la escena",
                "Detener ejecutando ambas a la vez",
            ],
        ),
        (
            "¿Qué NO es control de Dirección de Enfermería?",
            "Sustituir el diagnóstico y liderazgo médico en toda escena por sistema",
            [
                "Organizar turnos y estándares de cuidado",
                "Supervisar auxiliares y calidad de registro",
                "Coordinar con el equipo médico tratante",
            ],
        ),
        (
            "Paciente de rol agitado en recepción. Control:",
            "Abordaje calmado según protocolo y aviso a quien corresponda",
            [
                "Abordaje con insultos para ‘imponer respeto’",
                "Abordaje ignorando un riesgo claro de escena",
                "Abordaje baneando al jugador al primer grito sin contexto",
            ],
        ),
        (
            "Doble reporte de estado del mismo paciente. Control:",
            "Unificar fuente de verdad con el equipo tratante",
            [
                "Unificar dejando ambas versiones sin aclarar",
                "Unificar borrando registros útiles",
                "Unificar inventando una tercera versión ‘más épica’",
            ],
        ),
        (
            "Incumplimiento reiterado de un protocolo de cuidado. Control:",
            "Reentrenamiento, límites y escalado si no corrige",
            [
                "Reentrenamiento omitido por ser ‘buena gente’",
                "Reentrenamiento público humillante como única medida",
                "Reentrenamiento reemplazado por quitar el rol en silencio",
            ],
        ),
        (
            "Coordinación con Dir. Médica. Control sano:",
            "Flujos claros de órdenes y feedback de escena",
            [
                "Flujos de competencia tóxica por protagonismo",
                "Flujos de silencio total ‘para no molestar’",
                "Flujos de ignorar órdenes médicas por costumbre",
            ],
        ),
        (
            "Cierre de turno con incidente abierto. Control:",
            "Dejar dueño del seguimiento y estado del incidente",
            [
                "Dejar el incidente ‘para mañana’ sin dueño",
                "Dejar el incidente oculto al siguiente equipo",
                "Dejar el incidente como chisme sin datos",
            ],
        ),
        (
            "Meta de control de Enfermería:",
            "Cuidado ordenado, seguro para la escena y enseñable al equipo",
            [
                "Cuidado centrado solo en tu protagonismo",
                "Cuidado sin registros porque ‘es rol’",
                "Cuidado improvisado sin estándares",
            ],
        ),
    ]),
    "DIR_RRHH": _pack([
        (
            "Proceso de selección justo. Control mínimo:",
            "Perfil, evaluación, decisión motivada y registro",
            [
                "Perfil omitido eligiendo solo amigos",
                "Perfil evaluado en secreto sin registro",
                "Perfil reemplazado por sorteo público",
            ],
        ),
        (
            "Queja formal contra un jefe de servicio. Control:",
            "Recepción, imparcialidad, investigación y resolución documentada",
            [
                "Recepción y borrado ‘para proteger al jefe’",
                "Recepción y publicación en anuncios para drama",
                "Recepción e investigación hecha solo por el acusado",
            ],
        ),
        (
            "Onboarding de nuevo personal. Control:",
            "Normativa, organigrama, canales y expectativas del cargo",
            [
                "Normativa omitida ‘ya se aprende’",
                "Normativa reemplazada por admin inmediato",
                "Normativa solo del color del rol",
            ],
        ),
        (
            "Inactividad injustificada reiterada. Control:",
            "Aviso, plazos y medida según reglamento",
            [
                "Aviso inexistente y premio de rol",
                "Aviso reemplazado por ban sorpresa",
                "Aviso eterno sin nunca aplicar medida",
            ],
        ),
        (
            "Expedientes laborales. Control de acceso:",
            "Solo roles autorizados y necesidad de conocer",
            [
                "Solo roles de todo el staff por comodidad",
                "Solo publicación en general ‘por transparencia’",
                "Solo MD masivo a amigos",
            ],
        ),
        (
            "Despido de un miembro. Control:",
            "Causa, proceso y comunicación formal",
            [
                "Causa inventada en el momento por rabia",
                "Causa omitida con solo un emoji",
                "Causa decidida por voto de visitantes",
            ],
        ),
        (
            "Postulado falsea experiencia. Control:",
            "Rechazo, registro y aplicación de norma antisuplantación",
            [
                "Rechazo omitido aprobándolo igual",
                "Rechazo público humillante innecesario",
                "Rechazo y promoción a Director General",
            ],
        ),
        (
            "Conflicto de interés en contratación. Control:",
            "Declararlo y abstenerse de decidir",
            [
                "Declararlo y decidir igual ‘porque conoces mejor’",
                "Ocultarlo para agilizar",
                "Usarlo para forzar la contratación de tu círculo",
            ],
        ),
        (
            "Relación con Cancillería en caso grave. Control:",
            "Informar con hechos y proponer medidas proporcionales",
            [
                "Informar con rumores para forzar acción",
                "Informar ocultando datos críticos",
                "Informar difamando en público",
            ],
        ),
        (
            "¿Qué NO es control de RRHH?",
            "Imponer sanciones clínicas de tratamiento médico en escena",
            [
                "Gestionar altas, bajas y procesos formales",
                "Mediar conflictos laborales de personal",
                "Custodiar expedientes y plazos",
            ],
        ),
        (
            "Favoritismo detectado en un proceso. Control:",
            "Reabrir criterio, corregir y documentar la corrección",
            [
                "Reabrir solo si hay escándalo público",
                "Reabrir para vengar al favorecido",
                "Reabrir borrando todo rastro del proceso",
            ],
        ),
        (
            "Métrica útil de control de RRHH:",
            "Tiempos de cobertura de vacantes y calidad del onboarding",
            [
                "Tiempos medidos solo por cantidad de roles dados",
                "Tiempos medidos solo por likes",
                "Tiempos ignorados si ‘hay gente online’",
            ],
        ),
        (
            "Cambio de área solicitado por un miembro. Control:",
            "Evaluar disponibilidad, impacto y norma del destino",
            [
                "Evaluar negando siempre sin oír",
                "Evaluar aceptando sin consultar al área destino",
                "Evaluar baneando por pedir el cambio",
            ],
        ),
        (
            "Doble expediente contradictorio. Control:",
            "Conciliar hechos con evidencias y dejar una versión oficial",
            [
                "Conciliar dejando ambas versiones activas",
                "Conciliar borrando el expediente completo",
                "Conciliar eligiendo la versión del amigo",
            ],
        ),
        (
            "Presión de un Director para contratar a alguien. Control:",
            "Mantener el proceso y registrar la intervención indebida si existe",
            [
                "Mantener el proceso saltándotelo por jerarquía",
                "Mantener el proceso filtrando el candidato en público",
                "Mantener el proceso renunciando a evaluar",
            ],
        ),
        (
            "Escalado disciplinario. Control de proporcionalidad:",
            "Graduar según gravedad, reiteración y norma publicada",
            [
                "Graduar según estado de ánimo del día",
                "Graduar siempre al máximo ‘para escarmiento’",
                "Graduar nunca aplicando solo advertencias eternas",
            ],
        ),
        (
            "Cierre de un caso de personal. Control:",
            "Decisión, motivo, fecha y vía de notificación al interesado",
            [
                "Decisión sin motivo ‘porque ya se sabe’",
                "Decisión filtrada como chisme",
                "Decisión sin notificar al interesado",
            ],
        ),
        (
            "Onboarding incompleto detectado a los 7 días. Control:",
            "Completar brechas y asignar responsable de cierre",
            [
                "Completar culpando solo al nuevo",
                "Completar ignorando porque ‘ya está dentro’",
                "Completar repitiendo todo el proceso desde cero sin necesidad",
            ],
        ),
        (
            "Solicitud de acceso a un expediente. Control:",
            "Verificar autorización y registrar el acceso",
            [
                "Verificar entregando copia a cualquiera del staff",
                "Verificar negando incluso a roles autorizados sin causa",
                "Verificar publicando extractos en general",
            ],
        ),
        (
            "Meta de control de RRHH:",
            "Procesos justos, trazables y alineados al reglamento del hospital",
            [
                "Procesos rápidos aunque sean opacos",
                "Procesos basados en amistades",
                "Procesos improvisados sin registro",
            ],
        ),
    ]),
    "DIR_DOCENCIA": _pack([
        (
            "Certificación válida. Control mínimo:",
            "Material, evaluación y registro de resultado/firmas según protocolo",
            [
                "Material omitido aprobando por amistad",
                "Material evaluado solo por estar en voz un minuto",
                "Material reemplazado por pago OOC",
            ],
        ),
        (
            "Copia en examen de capacitación. Control:",
            "Anular o aplicar política académica y dejar constancia",
            [
                "Anular aprobando igual ‘para no drama’",
                "Anular subiendo nota por pena",
                "Anular dando rol de Director como castigo irónico",
            ],
        ),
        (
            "Instructor sesga notas a su círculo. Control:",
            "Auditar evaluaciones, corregir y limitar al instructor si procede",
            [
                "Auditar premiando su ‘lealtad de equipo’",
                "Auditar cerrando Docencia completa por un caso",
                "Auditar ignorando quejas sin revisar evidencias",
            ],
        ),
        (
            "Temario desactualizado respecto al RP del hospital. Control:",
            "Revisar con el área técnica y publicar versión vigente",
            [
                "Revisar dejando versiones contradictorias activas",
                "Revisar ocultando el temario ‘para que sea difícil’",
                "Revisar copiando de otro server sin adaptarlo",
            ],
        ),
        (
            "Coordinación con Dirección Médica. Control de contenido:",
            "Validar que lo enseñado sea usable y coherente en escena clínica",
            [
                "Validar bloqueando a Médica por ego",
                "Validar dejando que Médica ignore por completo la formación",
                "Validar permitiendo que Docencia ordene tratamientos en cada paciente",
            ],
        ),
        (
            "Registro de capacitaciones. Control de trazabilidad:",
            "Fecha, instructor, alumno y resultado verificable",
            [
                "Fecha omitida ‘porque se recuerda’",
                "Fecha solo oral en voz",
                "Fecha borrada al día siguiente siempre",
            ],
        ),
        (
            "Aprobar por pena a un alumno. Control correcto:",
            "Mantener el criterio del examen y ofrecer reintento según norma",
            [
                "Mantener el criterio bajando la nota de corte en secreto",
                "Mantener el criterio publicando burla al alumno",
                "Mantener el criterio regalar el certificado",
            ],
        ),
        (
            "¿Qué NO es control de Docencia?",
            "Despedir personal de otras áreas sin proceso de RRHH",
            [
                "Diseñar evaluaciones y estándares de aprobación",
                "Supervisar instructores y calidad del material",
                "Registrar certificaciones emitidas",
            ],
        ),
        (
            "Doble certificado contradictorio del mismo alumno. Control:",
            "Verificar evidencias y dejar una emisión oficial corregida",
            [
                "Verificar dejando ambos como válidos",
                "Verificar borrando todo el historial del alumno",
                "Verificar eligiendo el más favorable al amigo",
            ],
        ),
        (
            "Carga de formadores excesiva. Control:",
            "Planificar turnos de formación y evitar sobrecarga",
            [
                "Planificar obligando 24/7 ‘por vocación’",
                "Planificar prohibiendo formar por completo",
                "Planificar improvisando el mismo día sin aviso",
            ],
        ),
        (
            "Alumno no entiende el material. Control pedagógico:",
            "Aclarar, ajustar explicación y mantener el estándar de evaluación",
            [
                "Aclarar insultando por ‘no leer’",
                "Aclarar bajando el estándar solo para ese caso sin criterio",
                "Aclarar negando cualquier apoyo adicional legítimo",
            ],
        ),
        (
            "Solicitud de certificado sin evaluación. Control:",
            "Rechazar si el protocolo exige examen/práctica",
            [
                "Rechazar solo si el alumno es nuevo",
                "Aceptar si lo pide un Director amigo",
                "Aceptar si ‘ya tiene el rol de color’",
            ],
        ),
        (
            "Indicador útil de control docente:",
            "Tasa de aprobación coherente y quejas de sesgo revisadas",
            [
                "Tasa medida solo por cantidad de certificados regalados",
                "Tasa medida solo por embeds bonitos",
                "Tasa ignorada si hay muchos alumnos",
            ],
        ),
        (
            "Feedback al evaluado. Control de calidad:",
            "Puntos concretos a mejorar sin humillación",
            [
                "Puntos reemplazados por burla pública",
                "Puntos omitidos totalmente siempre",
                "Puntos solo con emojis de risa",
            ],
        ),
        (
            "Instructor improvisa reglas de evaluación distintas. Control:",
            "Unificar rúbrica y exigir adherencia",
            [
                "Unificar dejando ‘libertad creativa’ total",
                "Unificar sancionando alumnos por la inconsistencia del instructor",
                "Unificar ocultando la rúbrica oficial",
            ],
        ),
        (
            "Revalidación de competencias. Control de propósito:",
            "Mantener estándar mínimo actualizado del RP del área",
            [
                "Mantener estándar como castigo arbitrario",
                "Mantener estándar para quitar roles al azar",
                "Mantener estándar inexistente porque ‘molestan’",
            ],
        ),
        (
            "Publicación de resultados. Control:",
            "Informar al alumno y al log del área según protocolo",
            [
                "Informar doxxeando datos innecesarios",
                "Informar ocultando el resultado al interesado",
                "Informar con insultos en el log",
            ],
        ),
        (
            "Presión de un Director para aprobar a alguien. Control:",
            "Conservar independencia evaluadora y registrar la presión indebida",
            [
                "Conservar independencia cediendo por jerarquía",
                "Conservar independencia filtrando al alumno en público",
                "Conservar independencia cancelando el examen de todos",
            ],
        ),
        (
            "Cierre de una convocatoria de certificación. Control:",
            "Lista de resultados, pendientes de firma y archivo del acta",
            [
                "Lista mental sin archivo",
                "Lista publicada con datos sensibles de más",
                "Lista borrada para ‘empezar limpio’ sin trazabilidad",
            ],
        ),
        (
            "Meta de control de Docencia:",
            "Formación justa, trazable y útil para el RP del hospital",
            [
                "Formación ornamental sin evaluación real",
                "Formación basada en favoritismos",
                "Formación improvisada sin material",
            ],
        ),
    ]),
    "DIR_LOGISTICA": _pack([
        (
            "Emergencia con stock limitado. Criterio de control:",
            "Priorizar criticidad clínica/operativa y registrar salidas",
            [
                "Priorizar al que más insiste en el chat",
                "Priorizar lo decorativo porque ‘se ve mejor’",
                "Priorizar negar todo para conservar números bonitos",
            ],
        ),
        (
            "Inventario descuadrado. Control correctivo:",
            "Auditoría, ajuste documentado y control preventivo",
            [
                "Auditoría inventando cifras para cuadrar",
                "Auditoría omitida ‘no pasa nada’",
                "Auditoría culpando al bot sin revisar movimientos",
            ],
        ),
        (
            "Pedido urgente fuera de protocolo. Control:",
            "Evaluar, entregar si procede y regularizar con registro",
            [
                "Evaluar negando siempre por sistema",
                "Evaluar entregando a cualquiera sin control",
                "Evaluar borrando el pedido para no dejar rastro",
            ],
        ),
        (
            "Almacén restringido. Control de acceso:",
            "Quién entra, por qué y qué se mueve",
            [
                "Quién entra libremente ‘si es staff’",
                "Quién entra sin ningún registro de movimiento",
                "Quién entra prohibido incluso con necesidad justificada siempre",
            ],
        ),
        (
            "Pérdida de material. Control:",
            "Investigar causa, responsabilidad y medida preventiva",
            [
                "Investigar ocultando el faltante",
                "Investigar culpando al azar",
                "Investigar cerrando el hospital por un faltante menor",
            ],
        ),
        (
            "Coordinación con Médica. Control de demanda:",
            "Previsión, canal de solicitud y confirmación de entrega",
            [
                "Previsión sin hablar nunca con Médica",
                "Previsión negando insumos críticos sin alternativa",
                "Previsión entregando sin anotar nada",
            ],
        ),
        (
            "Reporte a Dirección General. Contenido de control:",
            "Niveles de stock, riesgos y acciones con dueño",
            [
                "Niveles solo de memes del área",
                "Niveles omitidos y solo quejas",
                "Niveles falsos para ‘no preocupar’",
            ],
        ),
        (
            "Turnos logísticos. Objetivo de control:",
            "Cobertura estable sin quemar al equipo",
            [
                "Cobertura con una sola persona 24/7 forzada",
                "Cobertura cero ‘porque no hay movimiento’",
                "Cobertura improvisada cada día sin aviso",
            ],
        ),
        (
            "Área pide de más sin justificación. Control:",
            "Cuestionar necesidad, ajustar cantidad y registrar",
            [
                "Cuestionar entregando todo sin control",
                "Cuestionar insultando al solicitante",
                "Cuestionar ignorando el pedido para siempre",
            ],
        ),
        (
            "¿Qué NO es control de Logística?",
            "Sancionar clínicamente a un médico por un tratamiento de escena",
            [
                "Controlar inventario y accesos de almacén",
                "Priorizar insumos críticos",
                "Reportar riesgos de desabastecimiento",
            ],
        ),
        (
            "Doble salida registrada del mismo ítem. Control:",
            "Conciliar movimientos y corregir el registro oficial",
            [
                "Conciliar dejando ambas salidas sin revisión",
                "Conciliar borrando el inventario completo",
                "Conciliar culpando sin revisar timestamps",
            ],
        ),
        (
            "Proveedor interno incumple plazos. Control:",
            "Aviso, alternativa temporal y escalado si reitera",
            [
                "Aviso premiando al proveedor",
                "Aviso inexistente e improvisación eterna",
                "Aviso cerrando el área usuaria como castigo",
            ],
        ),
        (
            "Indicador útil de control logístico:",
            "Quiebres de stock crítico y tiempo de reposición",
            [
                "Quiebres medidos solo por mensajes en el canal",
                "Quiebres ignorados si el Director está online",
                "Quiebres celebrados como ‘caos divertido’",
            ],
        ),
        (
            "Demora de entrega a un área. Control comunicacional:",
            "Avisar impacto y nueva ETA al responsable del área",
            [
                "Avisar nada esperando que no se noten",
                "Avisar mintiendo una hora imposible",
                "Avisar en público humillando al solicitante",
            ],
        ),
        (
            "Plan de stock mínimo. Propósito de control:",
            "Evitar cero en insumos esenciales de operación/RP",
            [
                "Evitar que nadie pida nunca nada",
                "Evitar trabajo de inventario porque ‘es aburrido’",
                "Evitar transparencia del almacén",
            ],
        ),
        (
            "Disputa entre áreas por el mismo lote. Control:",
            "Aplicar prioridad institucional documentada y comunicar",
            [
                "Aplicar prioridad al amigo del Director de Logística",
                "Aplicar prioridad al que grita más",
                "Aplicar prioridad tirando el lote ‘para que no peleen’",
            ],
        ),
        (
            "Acceso indebido al almacén detectado. Control:",
            "Cortar acceso, reportar e investigar movimiento",
            [
                "Cortar acceso sin investigar qué salió",
                "Cortar acceso publicando doxxing del implicado",
                "Cortar acceso ignorando porque ‘no faltó mucho’",
            ],
        ),
        (
            "Cierre diario de inventario. Control mínimo:",
            "Entradas, salidas, faltantes y responsable del conteo",
            [
                "Entradas omitidas ‘ya está en la cabeza’",
                "Entradas inventadas para cuadrar bonito",
                "Entradas borradas al cerrar el PC",
            ],
        ),
        (
            "Presión para saltarse registro ‘solo esta vez’. Control:",
            "Mantener registro o excepción documentada con límite",
            [
                "Mantener registro cediendo siempre por prisa",
                "Mantener registro humillando al solicitante en general",
                "Mantener registro eliminando el historial anterior",
            ],
        ),
        (
            "Meta de control de Logística:",
            "Disponibilidad trazable de recursos críticos con cuentas claras",
            [
                "Disponibilidad caótica sin números",
                "Disponibilidad solo para el círculo del Director",
                "Disponibilidad simulada en reportes falsos",
            ],
        ),
    ]),
    "JEFE_SEGURIDAD": _pack([
        (
            "Intruso en área restringida. Control de primera respuesta:",
            "Identificar, contener según protocolo y reportar",
            [
                "Identificar ignorando el hecho ‘si no toca nada’",
                "Identificar baneando sin evidencia de escena",
                "Identificar huyendo de la zona asignada",
            ],
        ),
        (
            "Uso de fuerza en RP. Criterio de control:",
            "Proporcional, escalonado y justificado en la escena",
            [
                "Proporcional al máximo desde el primer segundo siempre",
                "Proporcional al azar ‘para que sea épico’",
                "Proporcional prohibido incluso ante riesgo claro de escena",
            ],
        ),
        (
            "Incidente violento cerca de atención clínica. Control:",
            "Asegurar la escena y permitir asistencia segura",
            [
                "Asegurar bloqueando a todo el personal médico",
                "Asegurar evacuando sin informar a nadie",
                "Asegurar cerrando el RP clínico por sistema",
            ],
        ),
        (
            "Informe de incidente. Contenido de control:",
            "Hechos, horarios, involucrados y acciones tomadas",
            [
                "Hechos mezclados con opiniones personales sin marcar",
                "Hechos omitidos ‘porque ya se sabe’",
                "Hechos convertidos en insultos a los involucrados",
            ],
        ),
        (
            "Guardia abusa de autoridad. Control:",
            "Investigar, sancionar/reentrenar según norma",
            [
                "Investigar cubriendo al guardia por lealtad",
                "Investigar ascendiendo ‘para motivar’",
                "Investigar ignorando quejas reiteradas",
            ],
        ),
        (
            "Acceso a quirófano. Control:",
            "Verificar rol y necesidad de la escena",
            [
                "Verificar dejando pasar a cualquiera ‘si parece staff’",
                "Verificar prohibiendo a todo personal clínico siempre",
                "Verificar sin ningún criterio estable",
            ],
        ),
        (
            "Amenaza OOC en canal del hospital. Control:",
            "Separar IC/OOC, documentar y escalar a staff admin",
            [
                "Separar tratándola solo como RP",
                "Separar respondiendo con más amenazas",
                "Separar borrando sin dejar registro interno",
            ],
        ),
        (
            "Entrenamiento del equipo. Enfoque de control:",
            "Protocolos, comunicación y proporcionalidad",
            [
                "Protocolos reemplazados por caos improvisado",
                "Protocolos solo de chat sin práctica de criterios",
                "Protocolos que enseñan a ignorar el reglamento",
            ],
        ),
        (
            "Rondas y puestos. Propósito de control:",
            "Disuasión, detección temprana y cobertura de puntos clave",
            [
                "Disuasión solo decorativa sin reportes",
                "Disuasión inexistente dejando puestos vacíos crónicos",
                "Disuasión centrada solo en RP de café",
            ],
        ),
        (
            "¿Qué NO es control de Seguridad?",
            "Diagnosticar y tratar clínicamente al paciente en lugar del médico",
            [
                "Controlar accesos sensibles",
                "Contener incidentes de seguridad de RP",
                "Reportar riesgos a dirección/cancillería",
            ],
        ),
        (
            "Doble versión de un incidente. Control:",
            "Contrastar evidencias y fijar relato oficial interno",
            [
                "Contrastar publicando ambas para drama",
                "Contrastar eligiendo la del amigo",
                "Contrastar borrando evidencias incómodas",
            ],
        ),
        (
            "Civil de RP altera recepción. Control:",
            "Contención proporcional y reporte si escala",
            [
                "Contención con fuerza máxima sin escalón",
                "Contención ignorando un peligro claro de escena",
                "Contención baneando al primer grito sin contexto",
            ],
        ),
        (
            "Indicador útil de control de seguridad:",
            "Incidentes con informe completo y puestos críticos cubiertos",
            [
                "Incidentes medidos solo por cantidad de PK",
                "Incidentes ignorados si ‘no hubo ban’",
                "Incidentes celebrados sin aprendizaje",
            ],
        ),
        (
            "Coordinación con Cancillería en crisis. Control:",
            "Hechos, plan de contención y estado de canales/accesos",
            [
                "Hechos ocultos para ‘no preocupar’",
                "Hechos exagerados sin plan",
                "Hechos convertidos en culpa hacia Cancillería",
            ],
        ),
        (
            "Presión para inventar un delito y PK. Control:",
            "Exigir justificación de RP seria y proporcional",
            [
                "Exigir nada y permitir PK por aburrimiento",
                "Exigir PK obligatorio en anuncios",
                "Exigir ocultar el motivo al resto del staff",
            ],
        ),
        (
            "Fallo de cobertura en un puesto clave. Control:",
            "Reasignar, registrar el hueco y corregir el plan de turnos",
            [
                "Reasignar culpando en público sin plan",
                "Reasignar ignorando el hueco",
                "Reasignar cerrando el hospital entero siempre",
            ],
        ),
        (
            "Evidencias de un incidente. Control de custodia:",
            "Conservar ordenado para staff autorizado",
            [
                "Conservar publicando todo en general",
                "Conservar borrando al terminar la escena siempre",
                "Conservar falsificando detalles ‘para que cierre mejor’",
            ],
        ),
        (
            "Admin pide saltarse identificación ‘rápido’. Control:",
            "Mantener protocolo o excepción documentada por riesgo real",
            [
                "Mantener protocolo cediendo siempre por rango Discord",
                "Mantener protocolo humillando al Admin en general",
                "Mantener protocolo eliminando la identificación para todos",
            ],
        ),
        (
            "Cierre de incidente. Control mínimo:",
            "Informe breve, estado de la zona y retorno a cobertura normal",
            [
                "Informe omitido y abandono del puesto",
                "Informe con doxxing de involucrados",
                "Informe que premia el abuso de fuerza",
            ],
        ),
        (
            "Meta de control de Seguridad:",
            "Escenas seguras, accesos controlados y uso proporcional de autoridad",
            [
                "Escenas caóticas para contenido",
                "Escenas dominadas por abuso de poder",
                "Escenas sin reportes ni aprendizaje",
            ],
        ),
    ]),
}
