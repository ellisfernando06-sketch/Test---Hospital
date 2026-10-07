# -*- coding: utf-8 -*-
"""Mensaje de felicitación profesional + explicación de criterios por dirección."""
from __future__ import annotations

from typing import Dict, List

import discord

# Criterios que evalúan las preguntas (explicación para el aprobado)
_CRITERIOS: Dict[str, List[str]] = {
    "CANCILLER": [
        "Mediación institucional con registro y responsable claro",
        "Respeto al organigrama y límites frente al Owner",
        "Intervención solo ante riesgo grave o vacío de mando",
        "Confidencialidad y respuesta coordinada en crisis",
        "Priorizar por impacto, no por ruido o afinidad",
    ],
    "VICE_CANCILLER": [
        "Actuar con delegación formal o en ausencia del Canciller",
        "Documentar decisiones interinas (motivo, alcance, vigencia)",
        "Acatar correcciones del Canciller y alinear comunicación",
        "Cubrir sin desplazar la línea institucional permanente",
        "Handoff claro al cerrar el turno de control",
    ],
    "DIR_GENERAL": [
        "Coordinar áreas sin sustituir la operación clínica de cada una",
        "Protocolos transversales: consulta, validación y difusión",
        "Delegación con indicadores y puntos de control",
        "Reportes a Cancillería con hechos, riesgos y responsables",
        "Resolver bloqueos entre direcciones con plazos y dueños",
    ],
    "DIR_MEDICO": [
        "Liderazgo de escena: roles claros y punto de información",
        "Formación del equipo: corregir, enseñar y registrar lo grave",
        "Separar IC/OOC y proteger la calidad del RP clínico",
        "Priorizar por gravedad de escena, no por rango Discord",
        "Documentación mínima: motivo, plan y responsable",
    ],
    "DIR_ENFERMERIA": [
        "Prioridad por gravedad y dependencia del paciente de RP",
        "Verificación de órdenes, vía y registro de cuidados",
        "Liderazgo de turno: tareas, tiempos y punto de control",
        "Coordinación clara con el equipo médico tratante",
        "Entrega de turno con pendientes y riesgos abiertos",
    ],
    "DIR_RRHH": [
        "Selección con perfil, evaluación y registro motivado",
        "Quejas con imparcialidad e investigación documentada",
        "Onboarding: normas, organigrama y expectativas del cargo",
        "Expedientes solo con autorización y necesidad de conocer",
        "Procesos justos, trazables y alineados al reglamento",
    ],
    "DIR_DOCENCIA": [
        "Certificación con material, evaluación y registro/firmas",
        "Independencia evaluadora frente a presiones de jerarquía",
        "Temario usable y coherente con el RP del área",
        "Trazabilidad: fecha, instructor, alumno y resultado",
        "Feedback respetuoso con puntos concretos a mejorar",
    ],
    "DIR_LOGISTICA": [
        "Priorizar insumos críticos y registrar movimientos",
        "Auditoría y ajuste documentado del inventario",
        "Excepciones urgentes regularizadas con registro",
        "Control de acceso al almacén y trazabilidad de salidas",
        "Reportes con stock, riesgos y responsables",
    ],
    "JEFE_SEGURIDAD": [
        "Identificar, contener según protocolo y reportar",
        "Uso de fuerza proporcional, escalonado y justificado",
        "Proteger la escena para que la atención clínica pueda continuar",
        "Informes con hechos, horarios e involucrados",
        "Separar IC/OOC y escalar amenazas OOC al staff",
    ],
}

_NOMBRE_PUESTO: Dict[str, str] = {
    "CANCILLER": "Canciller",
    "VICE_CANCILLER": "Vice Canciller",
    "DIR_GENERAL": "Director(a) General",
    "DIR_MEDICO": "Director(a) Médico(a)",
    "DIR_ENFERMERIA": "Director(a) de Enfermería",
    "DIR_RRHH": "Director(a) de Recursos Humanos",
    "DIR_DOCENCIA": "Director(a) de Docencia",
    "DIR_LOGISTICA": "Director(a) de Logística",
    "JEFE_SEGURIDAD": "Jefe(a) / Director(a) de Seguridad",
}


def embed_felicitacion(
    *,
    dir_key: str = "",
    dir_nombre: str = "",
    aprobado_por: str = "Staff",
    emoji: str = "🏛️",
) -> discord.Embed:
    puesto = _NOMBRE_PUESTO.get(dir_key) or dir_nombre or "Dirección"
    criterios = _CRITERIOS.get(dir_key) or [
        "Criterio institucional y respeto al organigrama",
        "Registro y responsables en las decisiones",
        "Proporcionalidad y comunicación clara",
        "Priorizar el interés del hospital sobre el ruido del chat",
    ]

    lineas = "\n".join(f"• {c}" for c in criterios)
    emb = discord.Embed(
        title=f"{emoji}  Felicitaciones · {puesto}",
        description=(
            f"El **Hospital General** reconoce formalmente tu postulación.\n\n"
            f"Has sido **aprobado(a)** para el puesto de **{puesto}**.\n"
            f"Evaluación revisada por: **{aprobado_por}**\n\n"
            f"---\n\n"
            f"**Qué evaluaban las preguntas de este examen**\n"
            f"No se buscaba una respuesta de memoria, sino **criterio de control**:\n\n"
            f"{lineas}\n\n"
            f"---\n\n"
            f"A partir de ahora se espera de ti:\n"
            f"• Representar el cargo con seriedad y respeto\n"
            f"• Coordinarte con el organigrama y las demás direcciones\n"
            f"• Dejar constancia de lo importante y formar a tu equipo\n\n"
            f"*Bienvenido(a) a la responsabilidad de **{puesto}**.*"
        ),
        color=0x1A5276,
    )
    emb.set_footer(text="Hospital General · Direcciones · Evaluación institucional")
    return emb
