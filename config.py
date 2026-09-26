# -*- coding: utf-8 -*
"""
config.py — EL ÚNICO ARCHIVO QUE DEBES EDITAR (IDs de canales y nombres).
"""
import os

TOKEN = os.getenv("TOKEN") or os.getenv("DISCORD_TOKEN") or os.getenv("BOT_TOKEN")

NOMBRE_HOSPITAL = "Hospital General"
MONEDA = "$"
LOGO_URL = None

KEYS_NOMBRES = {
    "OWNER":                ("🛠️ Gerente Developer", "#E74C3C"),
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
    "DIRECTOR_DOCENCIA":    ("📚 Director de Investigación y Docencia", "#8E44AD"),
    "ENCARGADO_AREA":       ("🎖️ Encargado de Área", "#2980B9"),
    "JEFE_DEPARTAMENTO":    ("⭐ Jefe de Departamento", "#2ECC71"),
    "SUPERVISOR":           ("📌 Supervisor", "#27AE60"),
    "STAFF":                ("🏥 Personal del Hospital", "#95A5A6"),
    "RESIDENTE":            ("📚 Residente", "#1ABC9C"),
    "PASANTE":              ("📝 Pasante", "#BDC3C7"),
    "VOLUNTARIO":           ("💚 Voluntario", "#27AE60"),
    "STAFF_SERVIDOR":       ("🖥️ Staff del Servidor", "#7F8C8D"),
}

GERENTE_DEVELOPER_KEY = "OWNER"

JERARQUIA_KEYS = [
    "VOLUNTARIO", "PASANTE", "STAFF", "RESIDENTE", "SUPERVISOR",
    "ENCARGADO_AREA", "JEFE_DEPARTAMENTO", "DIRECTOR",
    "DIRECTOR_ADMINISTRATIVO", "DIRECTOR_DISCIPLINA", "DIRECTOR_GENERAL",
    "CO_OWNER", "OWNER",
]

DIRECTOR_KEYS = [k for k in KEYS_NOMBRES if k.startswith("DIRECTOR_")]
RRHH_KEY = "DIRECTOR_RRHH"
DOCENCIA_KEY = "DIRECTOR_DOCENCIA"

KEY_DESPIDOS = "DIRECTOR_RRHH"
KEY_SANCIONES = "DIRECTOR_RRHH"
KEY_INVESTIGACIONES = "DIRECTOR_RRHH"
KEY_SOLICITUD_GENERAL = "DIRECTOR_RRHH"
KEY_SUSPENSIONES = "DIRECTOR_RRHH"
KEY_DEGRADOS = "DIRECTOR_RRHH"

KEYS_CON_STAFF_SERVIDOR = {
    "DIRECTOR_GENERAL", "DIRECTOR_DISCIPLINA", "DIRECTOR_ADMINISTRATIVO",
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
            "🩺 Pasante de Medicina", "🩺 Interno", "🩺 Médico General",
            "🩺 Médico Especialista", "🩺 Encargado de Servicio",
            "🩺 Jefe de Servicio", "🩺 Subdirector Médico",
        ],
    },
    "enfermeria": {
        "nombre": "Enfermería",
        "emoji": "💉",
        "director_key": "DIRECTOR_ENFERMERIA",
        "escalafon_nombres": [
            "💉 Auxiliar de Enfermería", "💉 Enfermero/a",
            "💉 Enfermero/a Especialista", "💉 Encargado de Enfermería",
            "💉 Jefe de Enfermería", "💉 Subdirector de Enfermería",
        ],
    },
    "rrhh": {
        "nombre": "Recursos Humanos",
        "emoji": "👥",
        "director_key": "DIRECTOR_RRHH",
        "escalafon_nombres": [
            "👥 Asistente de RRHH", "👥 Analista de RRHH",
            "👥 Coordinador de RRHH", "👥 Jefe de RRHH",
        ],
    },
    "finanzas": {
        "nombre": "Finanzas",
        "emoji": "💰",
        "director_key": "DIRECTOR_FINANCIERO",
        "escalafon_nombres": ["💰 Auxiliar Contable", "💰 Contador", "💰 Jefe de Finanzas"],
    },
    "logistica": {
        "nombre": "Logística e Insumos",
        "emoji": "📦",
        "director_key": "DIRECTOR_LOGISTICA",
        "escalafon_nombres": ["📦 Auxiliar de Almacén", "📦 Técnico de Insumos", "📦 Jefe de Logística"],
    },
    "seguridad": {
        "nombre": "Seguridad",
        "emoji": "🛡️",
        "director_key": "DIRECTOR_SEGURIDAD",
        "escalafon_nombres": ["🛡️ Guardia", "🛡️ Supervisor de Seguridad", "🛡️ Jefe de Seguridad"],
    },
    "administracion": {
        "nombre": "Administración",
        "emoji": "📋",
        "director_key": "DIRECTOR_ADMINISTRATIVO",
        "escalafon_nombres": ["📋 Recepcionista", "📋 Asistente Administrativo", "📋 Jefe Administrativo"],
    },
    "docencia": {
        "nombre": "Investigación y Docencia",
        "emoji": "📚",
        "director_key": "DIRECTOR_DOCENCIA",
        "escalafon_nombres": [
            "📚 Instructor Junior",
            "📚 Instructor",
            "📚 Instructor Senior",
            "📚 Coordinador de Capacitación",
            "📚 Jefe de Investigación y Docencia",
            "📚 Subdirector de Investigación y Docencia",
        ],
    },
}

CANALES = {
    "log_general": None, "log_roles": None, "log_ascensos": None, "log_personal": None,
    "log_documentos": None, "log_pacientes": None, "log_turnos": None, "log_inventario": None,
    "log_procedimientos": None, "alerta_codigos": None, "log_finanzas": None,
    "log_solicitudes": None, "log_capacitaciones": None, "log_certificados": None,
    "log_quejas": None, "log_postulaciones": None, "log_sanciones": None,
    "log_investigaciones": None, "log_sanciones_ooc": None,
    "bot_status": 1481762625279758449,
    "aprobaciones": None, "aprobaciones_rrhh": None,
    "citatorio_general": None, "citatorio_disciplina": None, "citatorio_admin": None,
    "panel_guardia": None, "log_quirofano": None,
}

SEPARADORES_ROLES = [
    ("sep_cupula", "『 🛠️ GERENCIA / DESARROLLO 』", "#E74C3C"),
    ("sep_servidor", "『 🖥️ STAFF DEL SERVIDOR 』", "#7F8C8D"),
    ("sep_directores", "『 🏛️ DIRECCIÓN HOSPITAL 』", "#2C3E50"),
    ("sep_medico", "『 🩺 CUERPO MÉDICO 』", "#1ABC9C"),
    ("sep_enfermeria", "『 💉 ENFERMERÍA 』", "#3498DB"),
    ("sep_rrhh", "『 👥 RECURSOS HUMANOS 』", "#9B59B6"),
    ("sep_finanzas", "『 💰 FINANZAS 』", "#F1C40F"),
    ("sep_logistica", "『 📦 LOGÍSTICA 』", "#E67E22"),
    ("sep_seguridad", "『 🛡️ SEGURIDAD 』", "#34495E"),
    ("sep_admin", "『 📋 ADMINISTRACIÓN HOSPITAL 』", "#16A085"),
    ("sep_docencia", "『 📚 INVESTIGACIÓN Y DOCENCIA 』", "#8E44AD"),
    ("sep_staff", "『 🏥 PERSONAL / STAFF 』", "#95A5A6"),
    ("sep_graduados", "『 🎓 GRADUADOS / CERTIFICACIONES 』", "#8E44AD"),
    ("sep_identificacion", "『 🪪 IDENTIFICACIÓN Y LICENCIAS 』", "#1ABC9C"),
    ("sep_equipo_rp", "『 🩺 EQUIPO Y MATERIAL RP 』", "#E67E22"),
    ("sep_uniformes", "『 👔 UNIFORMES Y APARIENCIA 』", "#34495E"),
]

ROLES_OTORGADOS = {
    "graduado": ("🎓 Graduado", "#8E44AD", "sep_graduados"),
    "certificado_general": ("🎓 Certificado hospitalario", "#8E44AD", "sep_graduados"),
    "cert_rcp": ("🎓 Cert. RCP Básico", "#9B59B6", "sep_graduados"),
    "cert_primeros_auxilios": ("🎓 Cert. Primeros auxilios", "#9B59B6", "sep_graduados"),
    "cert_bioseguridad": ("🎓 Cert. Bioseguridad", "#9B59B6", "sep_graduados"),
    "cert_atencion_paciente": ("🎓 Cert. Atención al paciente", "#9B59B6", "sep_graduados"),
    "cert_etica": ("🎓 Cert. Ética hospitalaria", "#9B59B6", "sep_graduados"),
    "cert_evacuacion": ("🎓 Cert. Evacuación y códigos", "#9B59B6", "sep_graduados"),
    "cert_laboratorista": ("🎓 Cert. Laboratorista", "#9B59B6", "sep_graduados"),
    "cert_sva": ("🎓 Cert. Soporte vital avanzado", "#9B59B6", "sep_graduados"),
    "cert_urgencias": ("🎓 Cert. Urgencias médicas", "#9B59B6", "sep_graduados"),
    "cert_proc_clinicos": ("🎓 Cert. Procedimientos clínicos", "#9B59B6", "sep_graduados"),
    "cert_cirugia": ("🎓 Cert. Cirugía menor RP", "#9B59B6", "sep_graduados"),
    "cert_cuidados_enf": ("🎓 Cert. Cuidados de enfermería", "#9B59B6", "sep_graduados"),
    "cert_medicacion": ("🎓 Cert. Administración de medicamentos", "#9B59B6", "sep_graduados"),
    "cert_curaciones": ("🎓 Cert. Curaciones y heridas", "#9B59B6", "sep_graduados"),
    "cert_signos": ("🎓 Cert. Monitorización de signos", "#9B59B6", "sep_graduados"),
    "cert_induccion": ("🎓 Cert. Inducción de personal", "#9B59B6", "sep_graduados"),
    "cert_expedientes": ("🎓 Cert. Gestión de expedientes", "#9B59B6", "sep_graduados"),
    "cert_entrevistas": ("🎓 Cert. Entrevistas y selección", "#9B59B6", "sep_graduados"),
    "cert_caja": ("🎓 Cert. Caja y cobranza", "#9B59B6", "sep_graduados"),
    "cert_contabilidad": ("🎓 Cert. Contabilidad básica", "#9B59B6", "sep_graduados"),
    "cert_presupuesto": ("🎓 Cert. Presupuestos", "#9B59B6", "sep_graduados"),
    "cert_inventario": ("🎓 Cert. Control de inventario", "#9B59B6", "sep_graduados"),
    "cert_almacen": ("🎓 Cert. Almacén hospitalario", "#9B59B6", "sep_graduados"),
    "cert_cadena_frio": ("🎓 Cert. Cadena de frío", "#9B59B6", "sep_graduados"),
    "cert_vigilancia": ("🎓 Cert. Vigilancia hospitalaria", "#9B59B6", "sep_graduados"),
    "cert_accesos": ("🎓 Cert. Control de accesos", "#9B59B6", "sep_graduados"),
    "cert_amenazas": ("🎓 Cert. Protocolo de amenazas", "#9B59B6", "sep_graduados"),
    "cert_recepcion": ("🎓 Cert. Recepción y orientación", "#9B59B6", "sep_graduados"),
    "cert_doc_admin": ("🎓 Cert. Documentación administrativa", "#9B59B6", "sep_graduados"),
    "cert_citas": ("🎓 Cert. Agenda y citas", "#9B59B6", "sep_graduados"),
    "cert_formador": ("🎓 Cert. Formador de formadores", "#9B59B6", "sep_graduados"),
    "cert_evaluacion": ("🎓 Cert. Evaluación de competencias", "#9B59B6", "sep_graduados"),
    "cert_investigacion": ("🎓 Cert. Investigación básica", "#9B59B6", "sep_graduados"),
    "cert_disciplina": ("🎓 Cert. Normativa disciplinaria", "#9B59B6", "sep_graduados"),
    "cert_liderazgo": ("🎓 Cert. Liderazgo hospitalario", "#9B59B6", "sep_graduados"),
    "crear_identificacion": ("🪪 Crear identificación", "#E67E22", "sep_identificacion"),
    "credencial": ("🪪 Credencial hospitalaria", "#1ABC9C", "sep_identificacion"),
    "licencia_medica": ("📋 Licencia médica", "#2980B9", "sep_identificacion"),
    "licencia_enfermeria": ("📋 Licencia de enfermería", "#3498DB", "sep_identificacion"),
    "pase_areas": ("🪪 Pase de áreas restringidas", "#16A085", "sep_identificacion"),
    "eq_clinico": ("🩺 Equipo clínico", "#E74C3C", "sep_equipo_rp"),
    "eq_farmacia": ("💊 Material de farmacia", "#27AE60", "sep_equipo_rp"),
    "eq_tecnologia": ("💻 Equipo tecnológico", "#3498DB", "sep_equipo_rp"),
    "uniforme_medico": ("👔 Uniforme médico", "#34495E", "sep_uniformes"),
    "uniforme_enfermeria": ("👔 Uniforme enfermería", "#34495E", "sep_uniformes"),
    "accesorio_rp": ("💍 Accesorio RP", "#E91E63", "sep_uniformes"),
}

MAP_CERT_A_ROL = {
    "rcp": "cert_rcp",
    "primeros auxilios": "cert_primeros_auxilios",
    "bioseguridad": "cert_bioseguridad",
    "atención al paciente": "cert_atencion_paciente",
    "atencion al paciente": "cert_atencion_paciente",
    "ética": "cert_etica",
    "etica": "cert_etica",
    "evacuación": "cert_evacuacion",
    "evacuacion": "cert_evacuacion",
    "laboratorista": "cert_laboratorista",
    "soporte vital": "cert_sva",
    "sva": "cert_sva",
    "urgencias": "cert_urgencias",
    "procedimientos clínicos": "cert_proc_clinicos",
    "cirugía": "cert_cirugia",
    "cirugia": "cert_cirugia",
    "cuidados de enfermería": "cert_cuidados_enf",
    "medicamentos": "cert_medicacion",
    "curaciones": "cert_curaciones",
    "signos": "cert_signos",
    "inducción": "cert_induccion",
    "induccion": "cert_induccion",
    "expedientes": "cert_expedientes",
    "entrevistas": "cert_entrevistas",
    "caja": "cert_caja",
    "contabilidad": "cert_contabilidad",
    "presupuesto": "cert_presupuesto",
    "inventario": "cert_inventario",
    "almacén": "cert_almacen",
    "almacen": "cert_almacen",
    "cadena de frío": "cert_cadena_frio",
    "vigilancia": "cert_vigilancia",
    "accesos": "cert_accesos",
    "amenazas": "cert_amenazas",
    "recepción": "cert_recepcion",
    "recepcion": "cert_recepcion",
    "documentación administrativa": "cert_doc_admin",
    "agenda": "cert_citas",
    "formador": "cert_formador",
    "evaluación": "cert_evaluacion",
    "evaluacion": "cert_evaluacion",
    "investigación": "cert_investigacion",
    "investigacion": "cert_investigacion",
    "disciplinaria": "cert_disciplina",
    "liderazgo": "cert_liderazgo",
}

MAP_TIENDA_CAT_A_ROL = {
    "instrumentos_medicos": "eq_clinico",
    "farmacia": "eq_farmacia",
    "tecnologia": "eq_tecnologia",
    "uniformes": "uniforme_medico",
}

GRAVEDAD_PACIENTE = ["Estable", "Observación", "Grave", "Crítico"]
CATEGORIAS_INVENTARIO = [
    "Medicamentos", "Material quirúrgico", "Insumos de enfermería",
    "Equipo médico", "Protección personal", "Oficina y papelería", "General",
]
CODIGOS_EMERGENCIA = {
    "azul": {"nombre": "Código Azul", "descripcion": "Paro cardiorrespiratorio — reanimación inmediata.", "color": "#2980B9", "mencion_keys": ["DIRECTOR_MEDICO", "DIRECTOR_ENFERMERIA", "STAFF"]},
    "rojo": {"nombre": "Código Rojo", "descripcion": "Incendio dentro de las instalaciones.", "color": "#C0392B", "mencion_keys": ["DIRECTOR_SEGURIDAD", "SUPERVISOR", "STAFF"]},
    "plata": {"nombre": "Código Plata", "descripcion": "Persona armada o situación con rehenes.", "color": "#95A5A6", "mencion_keys": ["DIRECTOR_SEGURIDAD", "DIRECTOR_RRHH"]},
    "negro": {"nombre": "Código Negro", "descripcion": "Amenaza de bomba.", "color": "#2C3E50", "mencion_keys": ["DIRECTOR_SEGURIDAD", "DIRECTOR_RRHH"]},
    "naranja": {"nombre": "Código Naranja", "descripcion": "Derrame de material peligroso o contaminación.", "color": "#E67E22", "mencion_keys": ["DIRECTOR_LOGISTICA", "DIRECTOR_MEDICO"]},
    "amarillo": {"nombre": "Código Amarillo", "descripcion": "Desastre externo / llegada masiva de heridos.", "color": "#F1C40F", "mencion_keys": ["DIRECTOR_MEDICO", "DIRECTOR_ENFERMERIA", "STAFF"]},
    "ambar": {"nombre": "Código Ámbar", "descripcion": "Desaparición o secuestro de un menor.", "color": "#D35400", "mencion_keys": ["DIRECTOR_SEGURIDAD", "SUPERVISOR"]},
    "verde": {"nombre": "Código Verde", "descripcion": "Evacuación general del edificio.", "color": "#27AE60", "mencion_keys": ["DIRECTOR_SEGURIDAD", "DIRECTOR_RRHH", "STAFF"]},
}
FICHA_CAMPOS = {"especialidad": "Especialidad", "licencia": "N° de licencia", "contacto": "Contacto RP", "ingreso": "Fecha de ingreso", "notas": "Notas administrativas"}
TICKET_STAFF_KEYS = ["SUPERVISOR", "DIRECTOR", "DIRECTOR_DISCIPLINA", "DIRECTOR_GENERAL", "DIRECTOR_ADMINISTRATIVO", "CO_OWNER", "OWNER"]
TICKET_CATEGORIA_ID = 1381426327630118932
TIPOS_SOLICITUD_RRHH = {
    "despido": {"titulo": "🚫 Solicitud de despido", "campos": ["usuario", "motivo", "evidencia"], "key_aprobador": "DIRECTOR_RRHH"},
    "sancion_interna": {"titulo": "⚠️ Solicitud de sanción interna", "campos": ["usuario", "tipo_sancion", "motivo", "evidencia"], "key_aprobador": "DIRECTOR_RRHH"},
    "degrado": {"titulo": "⬇️ Solicitud de degradado", "campos": ["usuario", "cargo_actual", "cargo_propuesto", "motivo"], "key_aprobador": "DIRECTOR_RRHH"},
    "investigacion": {"titulo": "🔎 Solicitud de investigación interna", "campos": ["usuario", "motivo", "evidencia"], "key_aprobador": "DIRECTOR_RRHH"},
    "suspension": {"titulo": "⛔ Solicitud de suspensión", "campos": ["usuario", "duracion", "motivo"], "key_aprobador": "DIRECTOR_RRHH"},
}

def nombre_key(key: str) -> str:
    return KEYS_NOMBRES.get(key, (key, ""))[0]

def keys_de_direccion():
    return [k for k in KEYS_NOMBRES if k.startswith("DIRECTOR_")]
