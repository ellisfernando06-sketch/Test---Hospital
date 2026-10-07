# -*- coding: utf-8 -*-
import json
from typing import Any, Dict, List, Tuple

# Parte A del banco (CANCILLER, VICE, DIR_GENERAL, DIR_MEDICO, DIR_ENFERMERIA)
# Opciones casi iguales; una centra el control correcto.

def _t(q: str, good: str, bad: List[str], rot: int = 1) -> Tuple[str, List[str], int]:
    ops = list(bad[:3])
    while len(ops) < 3:
        ops.append("Actuar sin registro ni responsable")
    pos = rot % 4
    ops.insert(pos, good)
    return (q, ops[:4], pos)


def _p(rows: List[Tuple[str, str, List[str], int]]) -> List[Tuple[str, List[str], int]]:
    return [_t(q, g, b, r) for q, g, b, r in rows]


BANCO_PART: Dict[str, List[Tuple[str, List[str], int]]] = {
    "CANCILLER": _p([
        ("Choque entre Direcciones con impacto operativo. Control del Canciller:", "Mediar, fijar responsable y dejar constancia del acuerdo", ["Mediar en privado sin dejar rastro", "Mediar solo si ambas partes lo piden el mismo día", "Mediar publicando el drama en anuncios"], 1),
        ("Directiva del Vice contradice el reglamento. Control:", "Revisar, corregir o anular según jerarquía y registrar", ["Dejar que cada área elija qué aplicar", "Aplicar la del Vice por ser más reciente", "Esperar tres quejas públicas"], 2),
        ("Control institucional frente a un Director:", "Supervisar alineación y exigir cuentas sin sustituir su operación diaria", ["Microgestionar cada tarea en tiempo real", "Supervisar solo si el Director autoriza", "Sustituirlo en todas las escenas de RP"], 0),
        ("Crisis de imagen del servidor. Prioridad de control:", "Respuesta oficial coordinada, contención y continuidad operativa", ["Borrar evidencias incómodas", "Que responda solo el área afectada", "Esperar a que baje el drama"], 1),
        ("Staff filtra reunión restringida. Control:", "Proceso, medida proporcional y reforzar confidencialidad", ["Proceso solo si el Owner ordena por escrito", "Escarmiento público en general", "Aviso informal sin registro"], 3),
        ("¿Cuándo intervenir en un área operativa?", "Riesgo institucional, incumplimiento grave o vacío de mando", ["Desacuerdo menor de estilo de RP", "Pedido de un solo residente", "Aburrimiento del Canciller"], 1),
        ("Cambio estructural del organigrama. Control mínimo:", "Validación de autoridades y comunicación formal", ["Solo chat privado sin difusión", "Reacciones de emoji en general", "Decisión unilateral del Director más antiguo"], 2),
        ("Relación Canciller–Owner en control:", "Ejecución estratégica dentro de límites del organigrama y del Owner", ["Sustituir al Owner en todo", "Sin rendición de cuentas", "Solo función ceremonial"], 0),
        ("Sanción a un Director. Criterio de control:", "Debido proceso, proporcionalidad y registro", ["Humillación pública como ejemplo", "Omitir proceso si es problemático", "Votación de visitantes"], 1),
        ("Dos áreas piden prioridad contradictoria:", "Definir prioridad institucional temporal y comunicar el criterio", ["Prioridad a quien escribe primero", "Prioridad por afinidad personal", "Dejar que peleen hasta cansarse"], 2),
        ("Ausencia prolongada del Canciller:", "Delegación formal al Vice y aviso de cobertura", ["Si pasa algo avisen", "Cualquier Admin online", "No delegar para no perder poder"], 1),
        ("Director ignora directiva institucional. Primer control:", "Requerimiento formal, plazo y escalado si persiste", ["Burla en staff", "Ban inmediato sin requerimiento", "Esperar tres quejas anónimas"], 0),
        ("Control vs microgestión en Cancillería:", "Fijar criterios y resultados, no cada detalle operativo", ["Escribir cada mensaje del área", "Solo intervenir en crisis mediática", "Nunca revisar cumplimiento"], 3),
        ("Info sensible de alta dirección. Acceso:", "Necesidad de conocer y roles autorizados", ["Todo el staff por comodidad", "Solo amigos de confianza", "Publicar resumen en anuncios"], 1),
        ("Conflicto OOC entre directores en canal visible:", "Cortar escalada, canal adecuado y documentar", ["Borrar sin contexto al staff", "Dejar que se resuelvan en público", "Sancionar al que menos escribe"], 2),
        ("Métrica útil de control institucional:", "Cumplimiento de acuerdos, tiempos de respuesta y escalados resueltos", ["Cantidad de mensajes", "Likes en anuncios", "Miedo a sanciones"], 0),
        ("El Vice emite orden urgente sin coordinar:", "Validar impacto, alinear criterio y ajustar si hace falta", ["Aceptar siempre por ser Vice", "Rechazar toda orden del Vice", "Ignorar hasta mañana"], 1),
        ("Representación externa del hospital:", "Mensaje único alineado, con respaldo y límites claros", ["Cualquier staff con buena intención", "Improvisar sin consultar", "Mensaje agresivo para imponer respeto"], 2),
        ("Cola de decisiones pendientes:", "Priorizar por riesgo/impacto y asignar dueño", ["Orden alfabético de áreas", "Lo más fácil de cerrar", "Lo que más ruido genera en chat"], 1),
        ("Cierre tras conflicto grave:", "Acuerdo explícito, responsables y seguimiento breve", ["Ya quedó sin seguimiento", "Humillación pública de una parte", "Borrar registro interno para no reabrir"], 0),
    ]),
    "VICE_CANCILLER": _p([
        ("Actúas con plenitud de control cuando:", "Hay ausencia del Canciller o delegación formal expresa", ["Ganas de ordenar aunque el Canciller esté activo", "Pedido informal de un Director", "Presión de un grupo en staff"], 1),
        ("Decisión interina. Control documental mínimo:", "Registro con motivo, alcance, fecha y vigencia", ["Registro mental si todos lo saben", "Solo MD a un amigo", "Publicar datos sensibles innecesarios"], 2),
        ("El Canciller anula tu decisión:", "Acatar, documentar el cambio y alinear comunicación", ["Acatar en apariencia y mantener la tuya", "Discutir el tema en público primero", "Acatar solo si estás de acuerdo"], 0),
        ("Disputa RRHH–Docencia en tu turno:", "Mediar, fijar criterio temporal y reportar si aplica", ["Favorecer siempre a RRHH", "Cerrar ambas áreas", "Evitar cualquier registro"], 1),
        ("Límite de control respecto al Canciller:", "Complementar y cubrir sin desplazar la línea institucional permanente", ["Igualar rango de facto", "Solo tareas decorativas", "Sustituir al Owner si hace falta"], 3),
        ("Director cuestiona tu legitimidad:", "Reafirmar mandato con organigrama y escalar si hay boicot", ["Sanción inmediata sin diálogo", "Ignorar por completo", "Renunciar para evitar problemas"], 1),
        ("Info de Cancillería en tu poder:", "Solo necesidad de conocer y canales autorizados", ["Ampliar a todo Admin", "Según simpatía", "Resumen en general"], 2),
        ("Emergencia de rol masiva. Prioridad:", "Cadena de mando, estabilidad de canales y continuidad", ["Tu escena personal primero", "Bans masivos sin criterio", "Esperar a que calme"], 0),
        ("Coordinación con Dirección General:", "Separar estrategia institucional de operación diaria y sincronizar", ["Competir por autoridad", "No compartir información crítica", "Que General ignore Cancillería"], 1),
        ("Tu orden choca con protocolo de área:", "Verificar protocolo, ajustar la orden o escalar con justificación", ["Imponer por jerarquía sin mirar protocolo", "Anular el protocolo en silencio", "Evitar decidir hasta que se quejen"], 2),
        ("Ausencia tuya previsible:", "Aviso de cobertura y traspaso de pendientes críticos", ["Solo a amigos cercanos", "No avisar porque no debería pasar nada", "Aviso con datos internos innecesarios"], 1),
        ("Queja formal contra tu gestión:", "Recibir, no retaliar y seguir proceso imparcial", ["Cerrar el caso tú mismo", "Sancionar al quejoso", "Borrar la queja para proteger imagen"], 0),
        ("Control real vs apariencia:", "Decisiones con criterio, dueño y seguimiento", ["Anunciadas sin seguimiento", "Solo reactivas con drama", "Delegadas a nadie concreto"], 3),
        ("Staff pide atajo fuera de norma:", "Rechazar o canalizar excepción documentada", ["Rechazar y humillar en público", "Aceptar si ahorra tiempo", "Aceptar solo para rangos altos sin registro"], 1),
        ("Mensaje tuyo y del Canciller se contradicen:", "Alinear al mensaje institucional vigente y aclarar al equipo", ["Usar ambos según convenga", "Imponer el tuyo por ser reciente", "No aclarar para no confundir más"], 2),
        ("Indicador de buen control del turno:", "Pendientes claros, escalados a tiempo y áreas informadas", ["Pendientes para revisar luego", "Resueltos solo a gritos", "No preguntar nada"], 0),
        ("Admin presiona para saltarse a un Director:", "Respetar cadena de mando salvo riesgo grave justificado", ["Obedecer al Admin por rango Discord", "Saltar mandos para ir más rápido", "Ignorar a ambos"], 1),
        ("Cierre de tu guardia de control:", "Estado de incidentes abiertos y handoff de continuidad", ["Omitir si no hubo nada grave a tu juicio", "Publicar datos sensibles de miembros", "Solo verbal sin seguimiento"], 2),
        ("Firma o visto bueno interino. Validez:", "Solo dentro de la delegación y el alcance registrado", ["Si queda bonito en el embed", "Por costumbre aunque no haya delegación", "Asuntos personales de amigos"], 1),
        ("Objetivo central de tu rol de control:", "Estabilidad institucional cuando el Canciller no puede ejercer", ["Tu imagen personal", "Cerrar canales por sistema", "Imponer sin comunicar criterios"], 0),
    ]),
    "DIR_GENERAL": _p([
        ("Fallo de coordinación Médica–Logística:", "Mesa breve, responsables, plazo y criterio de prioridad", ["Reproches en general", "Que se arreglen solos", "Cerrar Logística como castigo"], 1),
        ("Director inactivo sin justificación:", "Aviso formal, plazos y escalado según norma", ["Aviso informal y olvidar", "Ban inmediato", "Ya volverá"], 2),
        ("Protocolo transversal nuevo:", "Consulta a afectados, validación y difusión oficial", ["Solo amigos del área", "Publicación sorpresa", "Consulta eterna sin decidir"], 0),
        ("Control operativo vs sustitución clínica:", "Asegurar cobertura y flujos; no ser el médico de cada paciente", ["Atender tú cada escena", "Prohibir el RP médico", "Solo anuncios motivacionales"], 1),
        ("Prioridades semanales de control:", "Pocas prioridades medibles comunicadas a direcciones", ["Muchas prioridades vagas", "Secretas en tu libreta", "Cambiadas cada hora sin aviso"], 3),
        ("Reporte de calidad a Cancillería:", "Hechos, riesgos y acciones con responsables", ["Rumores de pasillo", "Solo opiniones", "Exagerar para forzar decisiones"], 1),
        ("Delegación a jefe de servicio:", "Autonomía con indicadores y puntos de control", ["Autonomía total sin revisión", "Microgestión de cada mensaje", "Solo en crisis pública"], 2),
        ("Conflicto OOC entre directores:", "Separar IC/OOC, mediar en canal adecuado y registrar acuerdos", ["Dejar el conflicto en la escena", "Sancionar al más nuevo", "Borrar historial útil"], 0),
        ("Falta de personal en varias áreas:", "Reasignar cobertura crítica e informar impacto", ["Cerrar hospital sin aviso", "Culpar a un visitante", "Ignorar hasta mañana"], 1),
        ("Indicador útil de control general:", "Tiempo de resolución de bloqueos entre áreas", ["Tiempo online del Dir. General", "Respuesta en memes", "Desde el último ban"], 2),
        ("Área pide excepción al protocolo:", "Evaluar riesgo, documentar excepción y límite temporal", ["Conceder siempre para quedar bien", "Negar siempre sin análisis", "Privado sin rastro"], 1),
        ("Doble mando confuso en una operación:", "Declarar un líder de coordinación y canal único de órdenes", ["Todos mandan un poco", "Silencio total sin líder", "Líder al que grite más"], 0),
        ("Seguridad reporta riesgo en área clínica:", "Coordinar contención y continuidad asistencial de RP", ["Bloquear toda atención médica", "Ignorar a Seguridad", "Cerrar canales clínicos sin plan"], 3),
        ("Cambio de turno de dirección. Handoff:", "Pendientes críticos, riesgos abiertos y contactos clave", ["Si pasa algo avisan", "Solo tu escena personal", "Borrar pendientes para empezar limpio"], 1),
        ("Presión para decidir sin datos:", "Decisión provisional acotada o espera breve con responsable del dato", ["Definitiva improvisada para cerrar ya", "Evitar indefinidamente", "Solo el rumor más fuerte"], 2),
        ("¿Cuándo escalar a Cancillería de inmediato?", "Riesgo institucional, quiebre de mando o conflicto entre direcciones sin salida", ["Que te critiquen en memes", "Problema menor resoluble en el área", "Perder una discusión trivial"], 0),
        ("Control de calidad de un proceso no es:", "Castigar públicamente el primer error sin contexto", ["Revisar cuellos de botella", "Ajustar el flujo con las áreas", "Medir cumplimiento de acuerdos"], 1),
        ("Director pide recursos de otra área:", "Validar necesidad, impacto y acuerdo entre responsables", ["Ordenar traslado sin consultar", "Negar por sistema sin oír", "Solo MD sin informar a nadie más"], 2),
        ("Meta de control como Dir. General:", "Que las direcciones operen alineadas y sin bloqueos crónicos", ["Que todas las escenas pasen por ti", "Que Cancillería no se entere", "Ignorar el organigrama si funciona"], 1),
        ("Tras fallo de coordinación, el cierre incluye:", "Causa, corrección y dueño del seguimiento", ["Ocultar causa para no señalar", "Culpar en público", "Sin corrección porque ya pasó"], 0),
    ]),
}
