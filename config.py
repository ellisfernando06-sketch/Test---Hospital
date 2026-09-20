# -*- coding: utf-8 -*-
"""
config.py — EL ÚNICO ARCHIVO QUE DEBES EDITAR.

Sistema por KEYS:
  - Cada DIRECTOR_* solo gestiona su departamento.
  - Despidos, sanciones internas e investigaciones → DIRECTOR_RRHH (con aprobación).
  - Staff del Servidor: Director General, Director Disciplinario, Director Administrativo, Admin en prueba.
"""
import os

TOKEN = os.getenv("TOKEN") or os.getenv("DISCORD_TOKEN") or os.getenv("BOT_TOKEN")

NOMBRE_HOSPITAL = "Hospital General"
MONEDA = "$"
LOGO_URL = None

KEYS_NOMBRES = {
    "OWNER":                ("👑 Owner", "#E74C3C"),
    "CO_OWNER":             ("🤝 Co-Owner", "#C0392B"),
    "DIRECTOR_GENERAL":     ("🖥️ Director General", "#2C3E50"),
    "DIRECTOR_DISCIPLINA":  ("⚖️ Director de Disciplina", "#8E44AD"),
    "DIRECTOR_ADMINISTRATIVO": ("📋 Director Administrativo", "#16A085"),
    "DIRECTOR_MEDICO":      ("🩺 Director Médico", "#1ABC9C"),
    "DIRECTOR_ENFERMERIA":  ("💉 Director de Enfermería", "#3498DB"),
    "DIRECTOR_RRHH":        ("👥 Director de Recursos Humanos", "#9B59B6"),
    "DIRECTOR_FINANCIERO":  ("💰 Director Financiero", "#F1C40F"),
    "DIRECTOR_LOGISTICA":   ("📦 Director de Logística", "#E67E22"),
    "DIRECTOR_SEGURIDAD":   ("🛡️ Director de Seguridad", "#34495E"),
    "ENCARGADO_AREA":       ("🎖️ Encargado de Área", "#2980B9"),
    "JEFE_DEPARTAMENTO":    ("⭐ Jefe de Departamento", "#2ECC71"),
    "SUPERVISOR":           ("📌 Supervisor", "#27AE60"),
    "STAFF":                ("🏥 Personal del Hospital", "#95A5A6"),
    "RESIDENTE":            ("📚 Residente", "#1ABC9C"),
    "PASANTE":              ("📝 Pasante", "#BDC3C7"),
    "VOLUNTARIO":           ("💚 Voluntario", "#27AE60"),
    "STAFF_SERVIDOR":       ("🖥️ Staff del Servidor", "#7F8C8D"),
}

JERARQUIA_KEYS = [
    "VOLUNTARIO",
    "PASANTE",
    "STAFF",
    "RESIDENTE",
    "SUPERVISOR",
    "ENCARGADO_AREA",
    "JEFE_DEPARTAMENTO",
    "DIRECTOR",
    "DIRECTOR_ADMINISTRATIVO",
    "DIRECTOR_DISCIPLINA",
    "DIRECTOR_GENERAL",
    "CO_OWNER",
    "OWNER",
]

DIRECTOR_KEYS = [k for k in KEYS_NOMBRES if k.startswith("DIRECTOR_")]
RRHH_KEY = "DIRECTOR_RRHH"

KEY_DESPIDOS = "DIRECTOR_RRHH"
KEY_SANCIONES = "DIRECTOR_RRHH"
KEY_INVESTIGACIONES = "DIRECTOR_RRHH"
KEY_SOLICITUD_GENERAL = "DIRECTOR_RRHH"
KEY_SUSPENSIONES = "DIRECTOR_RRHH"
KEY_DEGRADOS = "DIRECTOR_RRHH"

KEYS_CON_STAFF_SERVIDOR = {
    "DIRECTOR_GENERAL",
    "DIRECTOR_DISCIPLINA",
    "DIRECTOR_ADMINISTRATIVO",
}

KEYS_CITATORIO = ["DIRECTOR_GENERAL", "DIRECTOR_DISCIPLINA", "DIRECTOR_ADMINISTRATIVO", "OWNER", "CO_OWNER"]
KEYS_REPORTE_PROCEDIMIENTO = ["DIRECTOR_GENERAL", "DIRECTOR_DISCIPLINA", "DIRECTOR_ADMINISTRATIVO", "OWNER", "CO_OWNER"]
KEYS_SANCION_OOC = ["DIRECTOR_GENERAL", "DIRECTOR_DISCIPLINA", "DIRECTOR_ADMINISTRATIVO", "OWNER", "CO_OWNER"]

ESCALADA_SOLICITUDES = ["DIRECTOR_DISCIPLINA", "DIRECTOR_GENERAL", "CO_OWNER", "OWNER"]

ROL_SUSPENDIDO_NOMBRE = "⛔ Suspendido"
ROL_SUSPENDIDO_COLOR = "#7F8C8D"

DEPARTAMENTOS = {
    "medico": {
        "nombre": "Cuerpo Médico",
        "emoji": "🩺",
        "director_key": "DIRECTOR_MEDICO",
        "escalafon_nombres": [
            "🩺 Pasante de Medicina",
            "🩺 Interno",
            "🩺 Médico General",
            "🩺 Médico Especialista",
            "🩺 Encargado de Servicio",
            "🩺 Jefe de Servicio",
            "🩺 Subdirector Médico",
        ],
    },
    "especialidades": {
        "nombre": "Especialidades Médicas",
        "emoji": "🫀",
        "director_key": "DIRECTOR_MEDICO",
        "escalafon_nombres": [
            "🫀 Cardiología",
            "🫀 Encargado de Cardiología",
            "🫀 Jefe de Cardiología",
            "🧠 Neurología",
            "🧠 Encargado de Neurología",
            "🧠 Jefe de Neurología",
            "🦴 Traumatología",
            "🦴 Encargado de Traumatología",
            "🦴 Jefe de Traumatología",
            "👶 Pediatría",
            "👶 Encargado de Pediatría",
            "👶 Jefe de Pediatría",
            "🤰 Ginecología y Obstetricia",
            "🤰 Encargado de Ginecología",
            "🤰 Jefe de Ginecología",
            "👁️ Oftalmología",
            "👁️ Encargado de Oftalmología",
            "👁️ Jefe de Oftalmología",
            "👂 Otorrinolaringología",
            "👂 Encargado de ORL",
            "👂 Jefe de ORL",
            "🧪 Laboratorio Clínico",
            "🧪 Encargado de Laboratorio",
            "🧪 Jefe de Laboratorio",
            "📷 Radiología / Imagen",
            "📷 Encargado de Radiología",
            "📷 Jefe de Radiología",
            "🩹 Cirugía General",
            "🩹 Encargado de Cirugía",
            "🩹 Jefe de Cirugía",
            "🚑 Urgencias / Emergencias",
            "🚑 Encargado de Urgencias",
            "🚑 Jefe de Urgencias",
            "💊 Anestesiología",
            "💊 Encargado de Anestesia",
            "💊 Jefe de Anestesia",
            "🧬 Oncología",
            "🧬 Encargado de Oncología",
            "🧬 Jefe de Oncología",
            "🫁 Neumología",
            "🫁 Encargado de Neumología",
            "🫁 Jefe de Neumología",
            "🦠 Infectología",
            "🦠 Encargado de Infectología",
            "🦠 Jefe de Infectología",
            "🫀 Subdirector de Especialidades",
        ],
    },
    "enfermeria": {
        "nombre": "Enfermería",
        "emoji": "💉",
        "director_key": "DIRECTOR_ENFERMERIA",
        "escalafon_nombres": [
            "💉 Auxiliar de Enfermería",
            "💉 Enfermero/a",
            "💉 Enfermero/a Especialista",
            "💉 Enfermero/a de Urgencias",
            "💉 Encargado de Enfermería",
            "💉 Jefe de Enfermería",
            "💉 Subdirector de Enfermería",
        ],
    },
    "rrhh": {
        "nombre": "Recursos Humanos",
        "emoji": "👥",
        "director_key": "DIRECTOR_RRHH",
        "escalafon_nombres": [
            "👥 Asistente de RRHH",
            "👥 Analista de RRHH",
            "👥 Coordinador de RRHH",
            "👥 Encargado de Personal",
            "👥 Jefe de RRHH",
            "👥 Subdirector de RRHH",
        ],
    },
    "finanzas": {
        "nombre": "Finanzas",
        "emoji": "💰",
        "director_key": "DIRECTOR_FINANCIERO",
        "escalafon_nombres": [
            "💰 Auxiliar Contable",
            "💰 Contador",
            "💰 Coordinador Financiero",
            "💰 Encargado de Tesorería",
            "💰 Jefe de Finanzas",
            "💰 Subdirector Financiero",
        ],
    },
    "logistica": {
        "nombre": "Logística e Insumos",
        "emoji": "📦",
        "director_key": "DIRECTOR_LOGISTICA",
        "escalafon_nombres": [
            "📦 Auxiliar de Almacén",
            "📦 Técnico de Insumos",
            "📦 Encargado de Insumos",
            "📦 Encargado de Farmacia",
            "📦 Jefe de Logística",
            "📦 Subdirector de Logística",
        ],
    },
    "seguridad": {
        "nombre": "Seguridad",
        "emoji": "🛡️",
        "director_key": "DIRECTOR_SEGURIDAD",
        "escalafon_nombres": [
            "🛡️ Guardia",
            "🛡️ Guardia Senior",
            "🛡️ Supervisor de Seguridad",
            "🛡️ Encargado de Seguridad",
            "🛡️ Jefe de Seguridad",
            "🛡️ Subdirector de Seguridad",
        ],
    },
    "administracion": {
        "nombre": "Administración",
        "emoji": "📋",
        "director_key": "DIRECTOR_ADMINISTRATIVO",
        "escalafon_nombres": [
            "📋 Recepcionista",
            "📋 Asistente Administrativo",
            "📋 Coordinador Administrativo",
            "📋 Encargado de Admisiones",
            "📋 Jefe Administrativo",
            "📋 Subdirector Administrativo",
        ],
    },
    "staff_servidor": {
        "nombre": "Staff del Servidor",
        "emoji": "🖥️",
        "director_key": "DIRECTOR_GENERAL",
        "escalafon_nombres": [
            "🖥️ Admin en prueba",
        ],
    },
}

CANALES = {
    "log_general":         None,
    "log_roles":           None,
    "log_ascensos":        None,
    "log_personal":        None,
    "log_documentos":      None,
    "log_finanzas":        None,
    "log_solicitudes":     None,
    "log_inventario":      None,
    "log_pacientes":       None,
    "log_turnos":          None,
    "log_capacitaciones":  None,
    "log_quejas":          None,
    "log_postulaciones":   None,
    "log_sanciones":       None,
    "log_investigaciones": None,
    "log_sanciones_ooc":   None,
    "log_procedimientos":  None,
    "alerta_codigos":      None,
    "bot_status":          1481762625279758449,
    "aprobaciones":        None,
    "citatorio_general":   None,
    "citatorio_disciplina": None,
    "citatorio_admin":     None,
    "aprobaciones_rrhh":   None,
}

SEPARADORES_ROLES = [
    ("sep_cupula",          "『 👑 ADMINISTRACIÓN 』", "#2C3E50"),
    ("sep_servidor",        "『 🖥️ STAFF DEL SERVIDOR 』", "#7F8C8D"),
    ("sep_directores",      "『 🏛️ DIRECCIÓN HOSPITAL 』", "#2C3E50"),
    ("sep_medico",          "『 🩺 CUERPO MÉDICO 』", "#1ABC9C"),
    ("sep_especialidades",  "『 🫀 ESPECIALIDADES 』", "#E74C3C"),
    ("sep_enfermeria",      "『 💉 ENFERMERÍA 』", "#3498DB"),
    ("sep_rrhh",            "『 👥 RECURSOS HUMANOS 』", "#9B59B6"),
    ("sep_finanzas",        "『 💰 FINANZAS 』", "#F1C40F"),
    ("sep_logistica",       "『 📦 LOGÍSTICA 』", "#E67E22"),
    ("sep_seguridad",       "『 🛡️ SEGURIDAD 』", "#34495E"),
    ("sep_admin",           "『 📋 ADMINISTRACIÓN HOSPITAL 』", "#16A085"),
    ("sep_mandos",          "『 ⭐ MANDOS INTERMEDIOS 』", "#27AE60"),
    ("sep_staff",           "『 🏥 PERSONAL / STAFF 』", "#95A5A6"),
]

GRAVEDAD_PACIENTE = ["Estable", "Observación", "Grave", "Crítico"]

CATEGORIAS_INVENTARIO = [
    "Medicamentos",
    "Material quirúrgico",
    "Insumos de enfermería",
    "Equipo médico",
    "Protección personal",
    "Oficina y papelería",
    "General",
]

CODIGOS_EMERGENCIA = {
    "azul": {
        "nombre": "Código Azul",
        "descripcion": "Paro cardiorrespiratorio — reanimación inmediata.",
        "color": "#2980B9",
        "mencion_keys": ["DIRECTOR_MEDICO", "DIRECTOR_ENFERMERIA", "STAFF"],
    },
    "rojo": {
        "nombre": "Código Rojo",
        "descripcion": "Incendio dentro de las instalaciones.",
        "color": "#C0392B",
        "mencion_keys": ["DIRECTOR_SEGURIDAD", "SUPERVISOR", "STAFF"],
    },
    "plata": {
        "nombre": "Código Plata",
        "descripcion": "Persona armada o situación con rehenes.",
        "color": "#95A5A6",
        "mencion_keys": ["DIRECTOR_SEGURIDAD", "DIRECTOR_RRHH"],
    },
    "negro": {
        "nombre": "Código Negro",
        "descripcion": "Amenaza de bomba.",
        "color": "#2C3E50",
        "mencion_keys": ["DIRECTOR_SEGURIDAD", "DIRECTOR_RRHH"],
    },
    "naranja": {
        "nombre": "Código Naranja",
        "descripcion": "Derrame de material peligroso o contaminación.",
        "color": "#E67E22",
        "mencion_keys": ["DIRECTOR_LOGISTICA", "DIRECTOR_MEDICO"],
    },
    "amarillo": {
        "nombre": "Código Amarillo",
        "descripcion": "Desastre externo / llegada masiva de heridos.",
        "color": "#F1C40F",
        "mencion_keys": ["DIRECTOR_MEDICO", "DIRECTOR_ENFERMERIA", "STAFF"],
    },
    "ambar": {
        "nombre": "Código Ámbar",
        "descripcion": "Desaparición o secuestro de un menor.",
        "color": "#D35400",
        "mencion_keys": ["DIRECTOR_SEGURIDAD", "SUPERVISOR"],
    },
    "verde": {
        "nombre": "Código Verde",
        "descripcion": "Evacuación general del edificio.",
        "color": "#27AE60",
        "mencion_keys": ["DIRECTOR_SEGURIDAD", "DIRECTOR_RRHH", "STAFF"],
    },
}

FICHA_CAMPOS = {
    "especialidad": "Especialidad",
    "licencia": "N° de licencia",
    "contacto": "Contacto RP",
    "ingreso": "Fecha de ingreso",
    "notas": "Notas administrativas",
}

TICKET_STAFF_KEYS = ["SUPERVISOR", "DIRECTOR", "DIRECTOR_DISCIPLINA", "DIRECTOR_GENERAL", "DIRECTOR_ADMINISTRATIVO", "CO_OWNER", "OWNER"]
TICKET_CATEGORIA_ID = 1381426327630118932

TIPOS_SOLICITUD_RRHH = {
    "despido": {
        "titulo": "🚫 Solicitud de despido",
        "campos": ["usuario", "motivo", "evidencia"],
        "key_aprobador": "DIRECTOR_RRHH",
    },
    "sancion_interna": {
        "titulo": "⚠️ Solicitud de sanción interna",
        "campos": ["usuario", "tipo_sancion", "motivo", "evidencia"],
        "key_aprobador": "DIRECTOR_RRHH",
    },
    "degrado": {
        "titulo": "⬇️ Solicitud de degradado",
        "campos": ["usuario", "cargo_actual", "cargo_propuesto", "motivo"],
        "key_aprobador": "DIRECTOR_RRHH",
    },
    "investigacion": {
        "titulo": "🔎 Solicitud de investigación interna",
        "campos": ["usuario", "motivo", "evidencia"],
        "key_aprobador": "DIRECTOR_RRHH",
    },
    "suspension": {
        "titulo": "⛔ Solicitud de suspensión",
        "campos": ["usuario", "duracion", "motivo"],
        "key_aprobador": "DIRECTOR_RRHH",
    },
}


def nombre_key(key: str) -> str:
    return KEYS_NOMBRES.get(key, (key, ""))[0]


def keys_de_direccion():
    return [k for k in KEYS_NOMBRES if k.startswith("DIRECTOR_")]
