# -*- coding: utf-8 -*-
"""
roles_config.py — ÚNICA FUENTE DE VERDAD del organigrama oficial.
Incluye cadena médica completa + enfermería + paramédicos.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

# ═══════════════════════════════════════════════════════════════
# ORGANIGRAMA OFICIAL (mayor → menor)
# ═══════════════════════════════════════════════════════════════

KEYS_NOMBRES: Dict[str, Tuple[str, str]] = {
    # ── AUTORIDADES COMPETENTES ──────────────────────────────
    "FUNDADOR_OWNER":       ("👑 Fundador y Owner",              "#E74C3C"),
    "CO_OWNER":             ("🤝 Co-Owner",                      "#C0392B"),

    # ── STAFF DEL SERVER ─────────────────────────────────────
    "ADMIN_JEFE":           ("🛡️ Admin en Jefe",                 "#9B59B6"),
    "ADMIN":                ("🛡️ Admin",                         "#8E44AD"),
    "ADMIN_PRUEBA":         ("🛡️ Admin en Prueba",               "#7D3C98"),

    # ── GERENCIA ─────────────────────────────────────────────
    "PREFECTO_OPERACIONES": ("🏛️ Prefecto de Operaciones Hospitalarias", "#2C3E50"),
    "DIR_GENERAL":          ("🖥️ Director General",              "#34495E"),
    "DIR_MEDICO":           ("🩺 Director Médico",               "#1ABC9C"),
    "DIR_ENFERMERIA":       ("💉 Director de Enfermería",        "#3498DB"),
    "DIR_RRHH":             ("👥 Director de RRHH",              "#9B59B6"),
    "DIR_DOCENCIA":         ("📚 Director de Docencia e Investigación", "#8E44AD"),
    "DIR_LOGISTICA":        ("📦 Director de Logística",         "#E67E22"),

    # ── JEFATURA DE DEPARTAMENTO ─────────────────────────────
    "JEFE_DEPARTAMENTO":    ("⭐ Jefe de Departamento",          "#2ECC71"),

    # ── ÁREA MÉDICA (escalonado mayor → menor) ───────────────
    "JEFE_SERVICIO":        ("🩺 Jefe de Servicio",              "#16A085"),
    "MEDICO_ESPECIALISTA":  ("🩺 Médico Especialista",           "#1ABC9C"),
    "MEDICO_GENERAL":       ("🩺 Médico General",                "#48C9B0"),
    "JEFE_GUIA_RESIDENTES": ("🎓 Jefe y Guía/Docente de Residentes", "#5DADE2"),
    "RESIDENTE":            ("📚 Residente",                     "#3498DB"),
    "INTERNO":              ("📝 Interno / Practicante",         "#85C1E9"),

    # ── ÁREA ENFERMERÍA (escalonado) ─────────────────────────
    "SUBDIR_ENFERMERIA":    ("💉 Subdirector de Enfermería",     "#2980B9"),
    "JEFE_ENFERMERIA":      ("💉 Jefe de Enfermería",            "#3498DB"),
    "ENCARGADO_ENFERMERIA": ("💉 Encargado de Enfermería",       "#5DADE2"),
    "ENFERMERO_ESPECIALISTA": ("💉 Enfermero/a Especialista",    "#5DADE2"),
    "ENFERMERO":            ("💉 Enfermero/a",                   "#85C1E9"),
    "AUXILIAR_ENFERMERIA":  ("💉 Auxiliar de Enfermería",        "#AED6F1"),

    # ── APOYO CLÍNICO ────────────────────────────────────────
    "PARAMEDICO":           ("🚑 Paramédico",                    "#E74C3C"),
    "TECNICO_SALUD":        ("🔬 Técnico en Salud",              "#E67E22"),

    # ── ÁREA ADMINISTRATIVA ──────────────────────────────────
    "ADMINISTRATIVO_SENIOR": ("📋 Administrativo Senior",        "#F39C12"),
    "ADMINISTRATIVO_JUNIOR": ("📋 Administrativo Junior / Auxiliar", "#F5B041"),

    # ── SISTEMA ──────────────────────────────────────────────
    "INACTIVIDAD_JUSTIFICADA": ("⏸️ Inactividad Justificada",    "#95A5A6"),
}

# Orden jerárquico de mayor a menor
JERARQUIA_KEYS: List[str] = [
    "FUNDADOR_OWNER",
    "CO_OWNER",
    "ADMIN_JEFE",
    "ADMIN",
    "ADMIN_PRUEBA",
    "PREFECTO_OPERACIONES",
    "DIR_GENERAL",
    "DIR_MEDICO",
    "DIR_ENFERMERIA",
    "DIR_RRHH",
    "DIR_DOCENCIA",
    "DIR_LOGISTICA",
    "JEFE_DEPARTAMENTO",
    # Médicos
    "JEFE_SERVICIO",
    "MEDICO_ESPECIALISTA",
    "MEDICO_GENERAL",
    "JEFE_GUIA_RESIDENTES",
    "RESIDENTE",
    "INTERNO",
    # Enfermería
    "SUBDIR_ENFERMERIA",
    "JEFE_ENFERMERIA",
    "ENCARGADO_ENFERMERIA",
    "ENFERMERO_ESPECIALISTA",
    "ENFERMERO",
    "AUXILIAR_ENFERMERIA",
    # Apoyo clínico
    "PARAMEDICO",
    "TECNICO_SALUD",
    # Admin
    "ADMINISTRATIVO_SENIOR",
    "ADMINISTRATIVO_JUNIOR",
]

SECCIONES = {
    "autoridades": {
        "nombre": "Autoridades Competentes",
        "emoji": "👑",
        "keys": ["FUNDADOR_OWNER", "CO_OWNER"],
        "color": "#E74C3C",
    },
    "staff_server": {
        "nombre": "Staff del Server",
        "emoji": "🛡️",
        "keys": ["ADMIN_JEFE", "ADMIN", "ADMIN_PRUEBA"],
        "color": "#9B59B6",
    },
    "gerencia": {
        "nombre": "Gerencia",
        "emoji": "🏛️",
        "keys": [
            "PREFECTO_OPERACIONES", "DIR_GENERAL", "DIR_MEDICO",
            "DIR_ENFERMERIA", "DIR_RRHH", "DIR_DOCENCIA", "DIR_LOGISTICA",
        ],
        "color": "#2C3E50",
    },
    "jefatura": {
        "nombre": "Jefatura de Departamento",
        "emoji": "⭐",
        "keys": ["JEFE_DEPARTAMENTO"],
        "color": "#2ECC71",
    },
    "area_medica": {
        "nombre": "Área Médica",
        "emoji": "🩺",
        "keys": [
            "JEFE_SERVICIO", "MEDICO_ESPECIALISTA", "MEDICO_GENERAL",
            "JEFE_GUIA_RESIDENTES", "RESIDENTE", "INTERNO",
        ],
        "color": "#1ABC9C",
    },
    "area_enfermeria": {
        "nombre": "Área de Enfermería",
        "emoji": "💉",
        "keys": [
            "SUBDIR_ENFERMERIA", "JEFE_ENFERMERIA", "ENCARGADO_ENFERMERIA",
            "ENFERMERO_ESPECIALISTA", "ENFERMERO", "AUXILIAR_ENFERMERIA",
        ],
        "color": "#3498DB",
    },
    "apoyo_clinico": {
        "nombre": "Apoyo Clínico",
        "emoji": "🚑",
        "keys": ["PARAMEDICO", "TECNICO_SALUD"],
        "color": "#E74C3C",
    },
    "area_admin": {
        "nombre": "Área Administrativa",
        "emoji": "📋",
        "keys": ["ADMINISTRATIVO_SENIOR", "ADMINISTRATIVO_JUNIOR"],
        "color": "#F39C12",
    },
}

SEPARADORES_ROLES = [
    ("sep_autoridades", "『 👑 AUTORIDADES COMPETENTES 』", "#E74C3C"),
    ("sep_staff_server", "『 🛡️ STAFF DEL SERVER 』", "#9B59B6"),
    ("sep_gerencia", "『 🏛️ GERENCIA 』", "#2C3E50"),
    ("sep_jefatura", "『 ⭐ JEFATURA DE DEPARTAMENTO 』", "#2ECC71"),
    ("sep_area_medica", "『 🩺 ÁREA MÉDICA 』", "#1ABC9C"),
    ("sep_area_enfermeria", "『 💉 ÁREA DE ENFERMERÍA 』", "#3498DB"),
    ("sep_apoyo_clinico", "『 🚑 APOYO CLÍNICO 』", "#E74C3C"),
    ("sep_area_admin", "『 📋 ÁREA ADMINISTRATIVA 』", "#F39C12"),
    ("sep_sistema", "『 ⚙️ SISTEMA 』", "#95A5A6"),
]

ROLES_OTORGADOS_CONSERVAR = {
    "cert_rcp": ("🎓 Cert. RCP Básico", "#9B59B6"),
    "cert_primeros_auxilios": ("🎓 Cert. Primeros auxilios", "#9B59B6"),
    "cert_bioseguridad": ("🎓 Cert. Bioseguridad", "#9B59B6"),
    "cert_atencion_paciente": ("🎓 Cert. Atención al paciente", "#9B59B6"),
    "cert_etica": ("🎓 Cert. Ética hospitalaria", "#9B59B6"),
    "cert_formador": ("🎓 Cert. Formador de formadores", "#9B59B6"),
    "cert_evaluacion": ("🎓 Cert. Evaluación de competencias", "#9B59B6"),
    "cert_investigacion": ("🎓 Cert. Investigación básica", "#9B59B6"),
    "cert_cuidados_enf": ("🎓 Cert. Cuidados de enfermería", "#9B59B6"),
    "jefe_seguridad": ("🛡️ Jefe de Seguridad", "#34495E"),
    "supervisor_seguridad": ("🛡️ Supervisor de Seguridad", "#34495E"),
    "guardia": ("🛡️ Guardia", "#34495E"),
    "uniforme_medico": ("👔 Uniforme médico", "#34495E"),
    "uniforme_enfermeria": ("👔 Uniforme enfermería", "#34495E"),
    "accesorio_rp": ("💍 Accesorio RP", "#E91E63"),
}

KEYS_APROBAR_INACTIVIDAD = [
    "FUNDADOR_OWNER",
    "CO_OWNER",
    "PREFECTO_OPERACIONES",
    "DIR_GENERAL",
    "DIR_RRHH",
]

INACTIVIDAD = {
    "aviso_dias": 7,
    "inactivo_dias": 14,
    "sancion_dias": 30,
    "max_dias_solicitud": 10,
    "cooldown_dias": 14,
}

CANALES_SETUP = [
    "bienvenida",
    "verificacion_roblox",
    "normativa_rp",
    "normativa_discord",
    "normativa_general",
    "solicitudes_inactividad",
    "log_staff",
]


def nombre_key(key: str) -> str:
    return KEYS_NOMBRES.get(key, (key, ""))[0]


def color_key(key: str) -> str:
    return KEYS_NOMBRES.get(key, ("", "#95A5A6"))[1]


def nivel_de_key(key: str) -> int:
    try:
        return JERARQUIA_KEYS.index(key)
    except ValueError:
        return 999
