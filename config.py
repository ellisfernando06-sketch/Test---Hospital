# -*- coding: utf-8 -*-
"""
config.py — EL ÚNICO ARCHIVO QUE DEBES EDITAR.
"""
# ---------------------------------------------------------------------------
# 1) TOKEN Y DATOS GENERALES
#    El TOKEN se toma ÚNICAMENTE de variables de entorno (Railway / hosting).
#    En Railway: Variables → TOKEN = <tu token del bot>
#    También acepta DISCORD_TOKEN por compatibilidad.
#    NUNCA pongas el token en este archivo.
# ---------------------------------------------------------------------------
import os
TOKEN = os.getenv("TOKEN") or os.getenv("DISCORD_TOKEN") or os.getenv("BOT_TOKEN")
# Se valida al arrancar (bot.run). Vacío aquí solo para poder importar módulos.

NOMBRE_HOSPITAL = "Hospital General"
MONEDA = "$"
LOGO_URL = None  # Opcional: URL de un logo para los embeds

# ---------------------------------------------------------------------------
# 2) KEYS (roles de cargo)
#    Formato: key: ("Nombre exacto del rol en Discord (con emoji)", "#COLOR_HEX")
#    El bot busca por nombre exacto (con emoji). Si no existe, lo CREA con ese nombre y color.
#    Si ya existe, reutiliza el ID (no duplica).
# ---------------------------------------------------------------------------
KEYS_NOMBRES = {
    "OWNER":                ("👑 Owner", "#E74C3C"),
    "CO_OWNER":             ("🤝 Co-Owner", "#C0392B"),
    "ENCARGADO_DISCIPLINA": ("⚖️ Encargado de Disciplina", "#8E44AD"),
    "DIRECTOR_MEDICO":      ("🩺 Director Médico", "#1ABC9C"),
    "DIRECTOR_ENFERMERIA":  ("💉 Director de Enfermería", "#3498DB"),
    "DIRECTOR_RRHH":        ("👥 Director de Recursos Humanos", "#9B59B6"),
    "DIRECTOR_FINANCIERO":  ("💰 Director Financiero", "#F1C40F"),
    "DIRECTOR_LOGISTICA":   ("📦 Director de Logística", "#E67E22"),
    "DIRECTOR_SEGURIDAD":   ("🛡️ Director de Seguridad", "#34495E"),
    "JEFE_DEPARTAMENTO":    ("⭐ Jefe de Departamento", "#2ECC71"),
    "SUPERVISOR":           ("📌 Supervisor", "#27AE60"),
    "STAFF":                ("🏥 Personal del Hospital", "#95A5A6"),
}

# Jerarquía de MENOR a MAYOR
JERARQUIA_KEYS = [
    "STAFF",
    "SUPERVISOR",
    "JEFE_DEPARTAMENTO",
    "DIRECTOR",          # alias lógico para cualquier DIRECTOR_*
    "ENCARGADO_DISCIPLINA",
    "CO_OWNER",
    "OWNER",
]

# Todas las keys que empiezan por DIRECTOR_ cuentan también como "DIRECTOR"
DIRECTOR_KEYS = [k for k in KEYS_NOMBRES if k.startswith("DIRECTOR_")]

# Key de Recursos Humanos (usada por quejas y solicitudes)
RRHH_KEY = "DIRECTOR_RRHH"

# Rol de suspensión
ROL_SUSPENDIDO_NOMBRE = "⛔ Suspendido"
ROL_SUSPENDIDO_COLOR = "#7F8C8D"

# ---------------------------------------------------------------------------
# 3) DEPARTAMENTOS
#    escalafon_nombres: de menor a mayor rango dentro del departamento
# ---------------------------------------------------------------------------
DEPARTAMENTOS = {
    "medico": {
        "nombre": "Cuerpo Médico",
        "emoji": "🩺",
        "director_key": "DIRECTOR_MEDICO",
        "escalafon_nombres": [
            "🩺 Interno",
            "🩺 Médico General",
            "🩺 Médico Especialista",
            "🩺 Jefe de Servicio",
            "🩺 Subdirector Médico",
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
            "💰 Subdirector Financiero",
        ],
    },
    "logistica": {
        "nombre": "Logística",
        "emoji": "📦",
        "director_key": "DIRECTOR_LOGISTICA",
        "escalafon_nombres": [
            "📦 Auxiliar de Almacén",
            "📦 Encargado de Insumos",
            "📦 Coordinador de Logística",
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
            "🛡️ Subdirector de Seguridad",
        ],
    },
}

# A dónde va una solicitud del área "general"
KEY_SOLICITUD_GENERAL = "DIRECTOR_RRHH"

# Si nadie tiene la key destino, la solicitud sube por esta cadena
ESCALADA_SOLICITUDES = ["ENCARGADO_DISCIPLINA", "CO_OWNER", "OWNER"]

# ---------------------------------------------------------------------------
# 4) ORDEN DE ROLES POR CATEGORÍAS
# ---------------------------------------------------------------------------
# Orden: OWNER / CO_OWNER / Disciplina → Directores → escalafones → Jefe/Supervisor/STAFF → Suspendido

# ---------------------------------------------------------------------------
# 5) CANALES DE LOG
# ---------------------------------------------------------------------------
CANALES = {
    "log_general":        None,
    "log_roles":          None,
    "log_ascensos":       None,
    "log_personal":       None,
    "log_documentos":     None,
    "log_finanzas":       None,
    "log_solicitudes":    None,
    "log_inventario":     None,
    "log_pacientes":      None,
    "log_turnos":         None,
    "log_capacitaciones": None,
    "log_quejas":         None,
    "log_postulaciones":  None,
    "alerta_codigos":     None,
    "bot_status":         1481762625279758449,
    "aprobaciones":       None,
}

# ---------------------------------------------------------------------------
# 6) PACIENTES E INVENTARIO
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# 7) CÓDIGOS DE EMERGENCIA
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# 8) FICHA DE PERSONAL
# ---------------------------------------------------------------------------
FICHA_CAMPOS = {
    "especialidad": "Especialidad",
    "licencia": "N° de licencia",
    "contacto": "Contacto RP",
    "ingreso": "Fecha de ingreso",
    "notas": "Notas administrativas",
}

# ---------------------------------------------------------------------------
# 9) TICKETS
# ---------------------------------------------------------------------------
TICKET_STAFF_KEYS = ["SUPERVISOR", "DIRECTOR", "ENCARGADO_DISCIPLINA", "CO_OWNER", "OWNER"]
TICKET_CATEGORIA_ID = 1381426327630118932

# ---------------------------------------------------------------------------
# Utilidades (no tocar)
# ---------------------------------------------------------------------------
def nombre_key(key: str) -> str:
    return KEYS_NOMBRES.get(key, (key, ""))[0]


def keys_de_direccion():
    return [k for k in KEYS_NOMBRES if k.startswith("DIRECTOR_")]
