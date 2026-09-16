"""
config.py
=========
ÚNICO archivo que debes editar para adaptar el bot a tu servidor.

Aquí defines los NOMBRES de las keys (roles), la estructura de
departamentos, y hacia dónde se enrutan las solicitudes. No hace
falta copiar IDs de rol a mano: ejecuta /configurar_roles una vez
con el bot en tu servidor y el bot creará automáticamente cada rol
que falte (o usará el que ya exista con ese nombre exacto). Los IDs
resultantes se guardan solos en roles_ids.json.
"""

# ---------------------------------------------------------------------------
# 1) KEYS: nombre interno -> (nombre visible del rol, color hex)
#    El bot crea un rol de Discord por cada una de estas keys.
# ---------------------------------------------------------------------------
KEYS_NOMBRES = {
    "OWNER": ("👑 Owner", "#e74c3c"),
    "JEFE_JUNTA_DIRECTIVA": ("🏛️ Presidente del Consejo", "#8e44ad"),
    "JUNTA_DIRECTIVA": ("🏛️ Junta Directiva", "#9b59b6"),

    "DIRECTOR_MEDICO": ("🩺 Director Médico", "#3498db"),
    "DIRECTOR_SEGURIDAD": ("🛡️ Director de Seguridad", "#2c3e50"),
    "DIRECTOR_OPERACIONES_EMERGENCIA": ("🚑 Director de Operaciones de Emergencia", "#e67e22"),
    "DIRECTOR_ADMINISTRATIVO": ("🗂️ Director Administrativo", "#16a085"),
    "DIRECTOR_FINANCIERO": ("💰 Director Financiero", "#f1c40f"),
    "DIRECTOR_RRHH": ("👥 Director de Recursos Humanos", "#1abc9c"),
    "DIRECTOR_ENFERMERIA": ("💉 Director de Enfermería", "#3498db"),
    "DIRECTOR_LOGISTICA": ("📦 Director de Logística", "#7f8c8d"),

    "JEFE_DEPARTAMENTO": ("🧭 Jefe de Departamento", "#2980b9"),
    "SUPERVISOR": ("📋 Supervisor", "#27ae60"),
    "STAFF": ("🏥 Personal", "#95a5a6"),
}

# Todas las keys que empiezan con DIRECTOR_ forman la key genérica "DIRECTOR"
DIRECTOR_KEYS = [k for k in KEYS_NOMBRES if k.startswith("DIRECTOR_")]

# ---------------------------------------------------------------------------
# 2) JERARQUÍA GENERAL (de menor a mayor autoridad)
# ---------------------------------------------------------------------------
JERARQUIA_KEYS = [
    "STAFF",
    "SUPERVISOR",
    "JEFE_DEPARTAMENTO",
    "DIRECCIÓN",
    "JUNTA_DIRECTIVA",
    "JEFE_JUNTA_DIRECTIVA",
    "OWNER",
]

# ---------------------------------------------------------------------------
# 3) DEPARTAMENTOS: escalafón por NOMBRES (el bot crea estos roles también)
#    "director_key" es la entidad superior que recibe las solicitudes
#    y administra ascensos/descensos/reportes de ese departamento.
# ---------------------------------------------------------------------------
DEPARTAMENTOS = {
    "seguridad": {
        "nombre": "Seguridad",
        "director_key": "DIRECTOR_SEGURIDAD",
        "escalafon_nombres": ["Agente de Seguridad", "Supervisor de Seguridad", "Jefe de Seguridad"],
    },
    "emergencias": {
        "nombre": "Operaciones de Emergencia",
        "director_key": "DIRECTOR_OPERACIONES_EMERGENCIA",
        "escalafon_nombres": ["Paramédico", "Supervisor de Emergencias", "Jefe de Emergencias"],
    },
    "medico": {
        "nombre": "Cuerpo Médico",
        "director_key": "DIRECTOR_MEDICO",
        "escalafon_nombres": ["Médico Residente", "Médico Adjunto", "Jefe de Medicina"],
    },
    "enfermeria": {
        "nombre": "Enfermería",
        "director_key": "DIRECTOR_ENFERMERIA",
        "escalafon_nombres": ["Enfermero/a", "Supervisor de Enfermería", "Jefe de Enfermería"],
    },
    "administrativo": {
        "nombre": "Administración",
        "director_key": "DIRECTOR_ADMINISTRATIVO",
        "escalafon_nombres": ["Auxiliar Administrativo", "Supervisor Administrativo", "Jefe Administrativo"],
    },
    "rrhh": {
        "nombre": "Recursos Humanos",
        "director_key": "DIRECTOR_RRHH",
        "escalafon_nombres": ["Auxiliar de RRHH", "Supervisor de RRHH", "Jefe de RRHH"],
    },
    "logistica": {
        "nombre": "Logística",
        "director_key": "DIRECTOR_LOGISTICA",
        "escalafon_nombres": ["Auxiliar de Logística", "Supervisor de Logística", "Jefe de Logística"],
    },
        "farmacia": {
        "nombre": "Farmacia",
        "director_key": "DIRECTOR_LOGISTICA",
        "escalafon_nombres": ["Auxiliar de Farmacia", "Supervisor de Farmacia", "Jefe de Farmacia"],
    },
    "psiquiatria": {
        "nombre": "Psiquiatría",
        "director_key": "DIRECTOR_MEDICO",
        "escalafon_nombres": ["Psicólogo/a Residente", "Psicólogo/a Adjunto/a", "Jefe de Psiquiatría"],
    },
    "laboratorio": {
        "nombre": "Laboratorio",
        "director_key": "DIRECTOR_MEDICO",
        "escalafon_nombres": ["Técnico de Laboratorio", "Supervisor de Laboratorio", "Jefe de Laboratorio"],
    },
    "admisiones": {
        "nombre": "Admisiones / Recepción",
        "director_key": "DIRECTOR_ADMINISTRATIVO",
        "escalafon_nombres": ["Recepcionista", "Supervisor de Admisiones", "Jefe de Admisiones"],
    },
    "traslados": {
        "nombre": "Traslados / Camillería",
        "director_key": "DIRECTOR_LOGISTICA",
        "escalafon_nombres": ["Camillero/a", "Supervisor de Traslados", "Jefe de Traslados"],
    },
    "cirugia": {
        "nombre": "Cirugía",
        "director_key": "DIRECTOR_MEDICO",
        "escalafon_nombres": ["Cirujano/a Residente", "Cirujano/a Adjunto/a", "Jefe de Cirugía"],
    },
}

# ---------------------------------------------------------------------------
# 4) ENRUTAMIENTO DE SOLICITUDES
#    - Toda carta de solicitud de un departamento va al director de ESE
#      departamento (director_key de arriba).
#    - Las solicitudes "generales" (no ligadas a un departamento) van a
#      esta key.
#    - Las solicitudes de descargo/degradación SIEMPRE van a esta key
#      (Recursos Humanos), sin importar el departamento del afectado.
#    - Si nadie tiene la key destino asignada todavía, el bot sube un
#      nivel automáticamente (ver solicitudes.py) para que nada se
#      pierda, y si aun así no hay nadie, se publica en el canal de
#      log correspondiente.
# ---------------------------------------------------------------------------
SOLICITUD_GENERAL_KEY = "JEFE_JUNTA_DIRECTIVA"
RRHH_KEY = "DIRECTOR_RRHH"

# ---------------------------------------------------------------------------
# 5) ROL ESPECIAL DE SUSPENSIÓN (usado por /suspender y /reincorporar)
# ---------------------------------------------------------------------------
ROL_SUSPENDIDO_NOMBRE = "⛔ Suspendido"
ROL_SUSPENDIDO_COLOR = "#4a4a4a"

# ---------------------------------------------------------------------------
# 6) CANALES (opcional) - IDs de canales donde el bot publica registros
#    Déjalos en None si no quieres logs en canal (los DMs igual se envían).
# ---------------------------------------------------------------------------
CANALES = {
    "log_roles": None,
    "log_finanzas": None,
    "log_documentos": None,
    "log_ascensos": None,
    "log_personal": None,     # asistencia / advertencias / solicitudes / descargos
    "log_pacientes": None,    # admisiones / altas / notas clínicas
    "log_inventario": None,   # movimientos de stock
    "log_turnos": None,       # entradas/salidas y asignaciones de turno
    "log_capacitaciones": None,
    "log_quejas": None,       # quejas formales
    "log_postulaciones": None,  # postulaciones al staff (si no se define, usa log_personal)
    "alerta_codigos": None,   # activación/cancelación de códigos de emergencia (recomendado configurarlo)
}

# ---------------------------------------------------------------------------
# 7) ESTILO VISUAL
# ---------------------------------------------------------------------------
NOMBRE_HOSPITAL = "Hospital Central"
LOGO_URL = None

# ---------------------------------------------------------------------------
# 8) SISTEMA DE TICKETS
# ---------------------------------------------------------------------------
TICKET_CATEGORIA_ID = None
TICKET_STAFF_KEYS = ["JEFE_JUNTA_DIRECTIVA", "DIRECTOR", "JEFE_DEPARTAMENTO"]

# ---------------------------------------------------------------------------
# 9) PACIENTES: niveles de gravedad usados en /paciente admitir
# ---------------------------------------------------------------------------
GRAVEDAD_PACIENTE = ["Leve", "Moderado", "Grave", "Crítico"]

# ---------------------------------------------------------------------------
# 10) INVENTARIO / LOGÍSTICA: categorías sugeridas (solo para autocompletar
#     la elección en /inventario agregar; puedes escribir cualquier otra).
# ---------------------------------------------------------------------------
CATEGORIAS_INVENTARIO = [
    "Medicamentos", "Material Quirúrgico", "Equipo Médico",
    "Insumos de Enfermería", "Alimentos", "Limpieza", "Administrativo", "Otro",
]

# ---------------------------------------------------------------------------
# 11) FICHA DE PERSONAL: campos editables con /ficha editar
# ---------------------------------------------------------------------------
FICHA_CAMPOS = {
    "especialidad": "Especialidad / puesto",
    "licencia": "N.° de licencia o matrícula",
    "contacto": "Contacto (RP)",
    "notas": "Notas administrativas",
}

# ---------------------------------------------------------------------------
# 12) CÓDIGOS DE EMERGENCIA: nombre visible, descripción, color y qué keys
#     son mencionadas al activarse. Actívalos con /codigo activar.
#     Cualquier miembro con una key de personal (STAFF o superior) puede
#     activar un código; cancelarlo requiere SUPERVISOR o superior.
# ---------------------------------------------------------------------------
CODIGOS_EMERGENCIA = {
    "azul": {
        "nombre": "🔵 Código Azul",
        "descripcion": "Paro cardio/respiratorio — se requiere RCP inmediata.",
        "color": "#3498db",
        "mencion_keys": ["DIRECTOR_MEDICO", "DIRECTOR_ENFERMERIA"],
    },
    "rojo": {
        "nombre": "🔴 Código Rojo",
        "descripcion": "Incendio activo dentro de las instalaciones.",
        "color": "#e74c3c",
        "mencion_keys": ["DIRECTOR_SEGURIDAD", "DIRECTOR_OPERACIONES_EMERGENCIA"],
    },
    "plata": {
        "nombre": "⚪ Código Plata",
        "descripcion": "Persona armada o amenaza activa dentro del hospital.",
        "color": "#95a5a6",
        "mencion_keys": ["DIRECTOR_SEGURIDAD"],
    },
    "negro": {
        "nombre": "⚫ Código Negro",
        "descripcion": "Amenaza de bomba u objeto sospechoso.",
        "color": "#2c3e50",
        "mencion_keys": ["DIRECTOR_SEGURIDAD"],
    },
    "naranja": {
        "nombre": "🟠 Código Naranja",
        "descripcion": "Derrame o exposición a materiales peligrosos.",
        "color": "#e67e22",
        "mencion_keys": ["DIRECTOR_SEGURIDAD", "DIRECTOR_LOGISTICA"],
    },
    "amarillo": {
        "nombre": "🟡 Código Amarillo",
        "descripcion": "Desastre externo / afluencia masiva de víctimas.",
        "color": "#f1c40f",
        "mencion_keys": ["DIRECTOR_MEDICO", "DIRECTOR_OPERACIONES_EMERGENCIA"],
    },
    "ambar": {
        "nombre": "🟨 Código Ámbar",
        "descripcion": "Secuestro o desaparición de un menor en las instalaciones.",
        "color": "#f39c12",
        "mencion_keys": ["DIRECTOR_SEGURIDAD"],
    },
    "verde": {
        "nombre": "🟢 Código Verde",
        "descripcion": "Evacuación general de las instalaciones.",
        "color": "#27ae60",
        "mencion_keys": ["DIRECTOR_SEGURIDAD", "JEFE_JUNTA_DIRECTIVA"],
    },
}

# ---------------------------------------------------------------------------
# 13) TOKEN DEL BOT
# ---------------------------------------------------------------------------
import os

TOKEN = os.getenv("DISCORD_TOKEN")
