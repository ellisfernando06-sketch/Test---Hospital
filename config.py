"""
config.py
=========
ÚNICO archivo que debes editar para adaptar el bot a tu servidor.

CÓMO FUNCIONA LA JERARQUÍA (nueva versión)
-------------------------------------------
Antes las keys "Jefe de Departamento", "Supervisor" y "Staff" eran
GENÉRICAS: todo el hospital compartía las mismas 3 keys, sin importar
si trabajabas en Seguridad o en Enfermería. Ahora cada departamento
tiene SU PROPIA key en cada rango, con su propio nombre e ícono, para
que el rol de Discord de alguien diga literalmente lo que hace
("🛡️ Jefe de Seguridad" en vez de un genérico "Jefe de Departamento").

La estructura tiene 3 niveles:

  1) DIRECCIONES: las grandes áreas del hospital (Dirección Médica,
     Dirección de Seguridad, etc.). Cada una tiene UN rol de Director
     (la key ya existente tipo DIRECTOR_MEDICO) y agrupa 1+ departamentos.

  2) DEPARTAMENTOS: unidades dentro de una dirección (ej. "Cirugía" y
     "Psiquiatría" están dentro de la Dirección Médica). Cada uno tiene
     su propio escalafón de 3 keys: STAFF -> SUPERVISOR -> JEFE.

  3) CATEGORÍAS/SEPARADORES: por cada Dirección, el bot crea además un
     rol "separador" (sin permisos, no asignable) que sirve solo para
     dividir visualmente el listado de roles del servidor en Ajustes >
     Roles, a modo de "carpeta". /configurar_roles los crea y los
     posiciona automáticamente justo encima de los roles de su grupo.

No hace falta copiar IDs de rol a mano: ejecuta /configurar_roles una
vez con el bot en tu servidor y él CREARÁ desde cero cada uno de estos
roles (no reutiliza roles existentes, aunque tengan el mismo nombre),
los coloreará y los ordenará en la jerarquía correcta. Los IDs
resultantes se guardan solos en roles_ids.json.

⚠️ Como /configurar_roles siempre crea roles nuevos, solo debe
ejecutarse UNA VEZ por servidor; volver a ejecutarlo duplicará todos
los roles.

Todo lo que sigue (KEYS_NOMBRES, JERARQUIA_KEYS, CATEGORIAS_ROLES,
DEPARTAMENTO_KEYS) se GENERA AUTOMÁTICAMENTE a partir de las secciones
1 y 2 de abajo. No necesitas tocar esa parte generada: solo edita
DIRECCIONES y DEPARTAMENTOS si quieres agregar/quitar áreas.
"""

import os

# ============================================================================
# 1) ALTA DIRECCIÓN — keys que no pertenecen a ningún departamento concreto
# ============================================================================
ALTA_DIRECCION = {
    "OWNER": ("👑 Owner", "#e74c3c"),
    "JEFE_JUNTA_DIRECTIVA": ("🏛️ Presidente del Consejo", "#8e44ad"),
    "JUNTA_DIRECTIVA": ("🏛️ Junta Directiva", "#9b59b6"),
}
CATEGORIA_ALTA_DIRECCION_SEPARADOR = ("▬▬▬▬▬ ALTA DIRECCIÓN ▬▬▬▬▬", "#c0392b")

# ============================================================================
# 2) DIRECCIONES — una por cada gran área del hospital.
#    "director_key"   -> nombre interno de la key (se mantiene el mismo
#                         nombre que ya usabas antes, para compatibilidad).
#    "director_rol"   -> (nombre visible, color) del rol de Discord.
#    "color_categoria"-> color del separador de esa Dirección.
# ============================================================================
DIRECCIONES = {
    "MEDICA": {
        "nombre": "Dirección Médica",
        "director_key": "DIRECTOR_MEDICO",
        "director_rol": ("🩺 Director Médico", "#3498db"),
        "color_categoria": "#3498db",
    },
    "ENFERMERIA": {
        "nombre": "Dirección de Enfermería",
        "director_key": "DIRECTOR_ENFERMERIA",
        "director_rol": ("💉 Director de Enfermería", "#48c9b0"),
        "color_categoria": "#48c9b0",
    },
    "SEGURIDAD": {
        "nombre": "Dirección de Seguridad",
        "director_key": "DIRECTOR_SEGURIDAD",
        "director_rol": ("🛡️ Director de Seguridad", "#34495e"),
        "color_categoria": "#34495e",
    },
    "EMERGENCIAS": {
        "nombre": "Dirección de Operaciones de Emergencia",
        "director_key": "DIRECTOR_OPERACIONES_EMERGENCIA",
        "director_rol": ("🚑 Director de Operaciones de Emergencia", "#e67e22"),
        "color_categoria": "#e67e22",
    },
    "ADMINISTRATIVA": {
        "nombre": "Dirección Administrativa",
        "director_key": "DIRECTOR_ADMINISTRATIVO",
        "director_rol": ("🗂️ Director Administrativo", "#16a085"),
        "color_categoria": "#16a085",
    },
    "RRHH": {
        "nombre": "Dirección de Recursos Humanos",
        "director_key": "DIRECTOR_RRHH",
        "director_rol": ("👥 Director de Recursos Humanos", "#f39c12"),
        "color_categoria": "#f39c12",
    },
    "FINANCIERA": {
        "nombre": "Dirección Financiera",
        "director_key": "DIRECTOR_FINANCIERO",
        "director_rol": ("💰 Director Financiero", "#f1c40f"),
        "color_categoria": "#f1c40f",
    },
    "LOGISTICA": {
        "nombre": "Dirección de Logística",
        "director_key": "DIRECTOR_LOGISTICA",
        "director_rol": ("📦 Director de Logística", "#7f8c8d"),
        "color_categoria": "#7f8c8d",
    },
}

# ============================================================================
# 3) DEPARTAMENTOS — unidades dentro de cada Dirección.
#    "direccion"  -> a qué Dirección pertenece (clave de DIRECCIONES).
#    "escalafon"  -> lista ordenada de (rango, nombre visible) de MENOR a
#                    MAYOR autoridad. El bot genera 3 keys por defecto:
#                    {DEPTO}_STAFF, {DEPTO}_SUPERVISOR, {DEPTO}_JEFE.
# ============================================================================
DEPARTAMENTOS = {
    "medico": {
        "nombre": "Cuerpo Médico",
        "direccion": "MEDICA",
        "escalafon": [
            ("STAFF", "🩺 Médico Residente"),
            ("SUPERVISOR", "🩺 Médico Adjunto"),
            ("JEFE", "🩺 Jefe de Medicina"),
        ],
    },
    "cirugia": {
        "nombre": "Cirugía",
        "direccion": "MEDICA",
        "escalafon": [
            ("STAFF", "🔪 Cirujano/a Residente"),
            ("SUPERVISOR", "🔪 Cirujano/a Adjunto/a"),
            ("JEFE", "🔪 Jefe de Cirugía"),
        ],
    },
    "psiquiatria": {
        "nombre": "Psiquiatría",
        "direccion": "MEDICA",
        "escalafon": [
            ("STAFF", "🧠 Psicólogo/a Residente"),
            ("SUPERVISOR", "🧠 Psicólogo/a Adjunto/a"),
            ("JEFE", "🧠 Jefe de Psiquiatría"),
        ],
    },
    "laboratorio": {
        "nombre": "Laboratorio",
        "direccion": "MEDICA",
        "escalafon": [
            ("STAFF", "🧪 Técnico de Laboratorio"),
            ("SUPERVISOR", "🧪 Supervisor de Laboratorio"),
            ("JEFE", "🧪 Jefe de Laboratorio"),
        ],
    },
    "enfermeria": {
        "nombre": "Enfermería",
        "direccion": "ENFERMERIA",
        "escalafon": [
            ("STAFF", "💉 Enfermero/a"),
            ("SUPERVISOR", "💉 Supervisor de Enfermería"),
            ("JEFE", "💉 Jefe de Enfermería"),
        ],
    },
    "seguridad": {
        "nombre": "Seguridad",
        "direccion": "SEGURIDAD",
        "escalafon": [
            ("STAFF", "🛡️ Agente de Seguridad"),
            ("SUPERVISOR", "🛡️ Supervisor de Seguridad"),
            ("JEFE", "🛡️ Jefe de Seguridad"),
        ],
    },
    "emergencias": {
        "nombre": "Operaciones de Emergencia",
        "direccion": "EMERGENCIAS",
        "escalafon": [
            ("STAFF", "🚑 Paramédico"),
            ("SUPERVISOR", "🚑 Supervisor de Emergencias"),
            ("JEFE", "🚑 Jefe de Emergencias"),
        ],
    },
    "traslados": {
        "nombre": "Traslados / Camillería",
        "direccion": "EMERGENCIAS",
        "escalafon": [
            ("STAFF", "🛏️ Camillero/a"),
            ("SUPERVISOR", "🛏️ Supervisor de Traslados"),
            ("JEFE", "🛏️ Jefe de Traslados"),
        ],
    },
    "administrativo": {
        "nombre": "Administración",
        "direccion": "ADMINISTRATIVA",
        "escalafon": [
            ("STAFF", "🗂️ Auxiliar Administrativo"),
            ("SUPERVISOR", "🗂️ Supervisor Administrativo"),
            ("JEFE", "🗂️ Jefe Administrativo"),
        ],
    },
    "admisiones": {
        "nombre": "Admisiones / Recepción",
        "direccion": "ADMINISTRATIVA",
        "escalafon": [
            ("STAFF", "📋 Recepcionista"),
            ("SUPERVISOR", "📋 Supervisor de Admisiones"),
            ("JEFE", "📋 Jefe de Admisiones"),
        ],
    },
    "rrhh": {
        "nombre": "Recursos Humanos",
        "direccion": "RRHH",
        "escalafon": [
            ("STAFF", "👥 Auxiliar de RRHH"),
            ("SUPERVISOR", "👥 Supervisor de RRHH"),
            ("JEFE", "👥 Jefe de RRHH"),
        ],
    },
    "finanzas": {
        "nombre": "Finanzas",
        "direccion": "FINANCIERA",
        "escalafon": [
            ("STAFF", "💰 Auxiliar Financiero"),
            ("SUPERVISOR", "💰 Supervisor Financiero"),
            ("JEFE", "💰 Jefe Financiero"),
        ],
    },
    "logistica": {
        "nombre": "Logística",
        "direccion": "LOGISTICA",
        "escalafon": [
            ("STAFF", "📦 Auxiliar de Logística"),
            ("SUPERVISOR", "📦 Supervisor de Logística"),
            ("JEFE", "📦 Jefe de Logística"),
        ],
    },
    "farmacia": {
        "nombre": "Farmacia",
        "direccion": "LOGISTICA",
        "escalafon": [
            ("STAFF", "💊 Auxiliar de Farmacia"),
            ("SUPERVISOR", "💊 Supervisor de Farmacia"),
            ("JEFE", "💊 Jefe de Farmacia"),
        ],
    },
}

# ============================================================================
# 4) NIVELES GENÉRICOS — para poder comparar autoridad SIN importar el
#    departamento (ej. "¿este usuario es al menos JEFE de algo?").
#    Orden de MENOR a MAYOR autoridad.
# ============================================================================
NIVELES_GENERICOS_ORDEN = [
    "STAFF",
    "SUPERVISOR",
    "JEFE",
    "DIRECTOR",
    "JUNTA_DIRECTIVA",
    "JEFE_JUNTA_DIRECTIVA",
    "OWNER",
]


def nivel_generico(key: str) -> str:
    """Convierte cualquier key departamental (ej. 'SEGURIDAD_JEFE') en su
    nivel genérico ('JEFE'), para comparar autoridad entre departamentos
    distintos sin tener que listar cada key a mano."""
    if key in ("OWNER", "JEFE_JUNTA_DIRECTIVA", "JUNTA_DIRECTIVA"):
        return key
    if key.startswith("DIRECTOR_"):
        return "DIRECTOR"
    for sufijo in ("_STAFF", "_SUPERVISOR", "_JEFE"):
        if key.endswith(sufijo):
            return sufijo[1:]
    return key


def tiene_nivel_minimo(keys_usuario: list[str], nivel_requerido: str) -> bool:
    """True si, entre todas las keys que tiene un usuario, alguna alcanza
    o supera el nivel genérico requerido (ej. tiene_nivel_minimo(keys, 'JEFE'))."""
    try:
        idx_requerido = NIVELES_GENERICOS_ORDEN.index(nivel_requerido)
    except ValueError:
        return False
    for key in keys_usuario:
        nivel = nivel_generico(key)
        if nivel in NIVELES_GENERICOS_ORDEN and NIVELES_GENERICOS_ORDEN.index(nivel) >= idx_requerido:
            return True
    return False


# ============================================================================
# 5) GENERACIÓN AUTOMÁTICA — no edites esta sección a mano.
#    A partir de ALTA_DIRECCION + DIRECCIONES + DEPARTAMENTOS se construyen:
#      - KEYS_NOMBRES     : todas las keys del bot -> (nombre visible, color)
#      - DEPARTAMENTO_KEYS: depto -> [key_staff, key_supervisor, key_jefe]
#      - CATEGORIAS_ROLES : direccion -> separador + lista ordenada de keys
#      - JERARQUIA_KEYS   : TODAS las keys ordenadas de mayor a menor autoridad
# ============================================================================
KEYS_NOMBRES: dict = {}
DEPARTAMENTO_KEYS: dict = {}
CATEGORIAS_ROLES: dict = {}
JERARQUIA_KEYS: list = []

# -- Alta dirección primero (máxima autoridad) --
KEYS_NOMBRES.update(ALTA_DIRECCION)
JERARQUIA_KEYS += ["OWNER", "JEFE_JUNTA_DIRECTIVA", "JUNTA_DIRECTIVA"]
CATEGORIAS_ROLES["ALTA_DIRECCION"] = {
    "nombre": "Alta Dirección",
    "separador": CATEGORIA_ALTA_DIRECCION_SEPARADOR,
    "keys": ["OWNER", "JEFE_JUNTA_DIRECTIVA", "JUNTA_DIRECTIVA"],
}

# -- Por cada Dirección: su Director + los departamentos que agrupa --
for direccion_id, direccion in DIRECCIONES.items():
    keys_de_esta_categoria = [direccion["director_key"]]
    KEYS_NOMBRES[direccion["director_key"]] = direccion["director_rol"]
    JERARQUIA_KEYS.append(direccion["director_key"])

    deptos_de_la_direccion = [
        depto_id for depto_id, d in DEPARTAMENTOS.items() if d["direccion"] == direccion_id
    ]
    for depto_id in deptos_de_la_direccion:
        depto = DEPARTAMENTOS[depto_id]
        keys_depto_ordenadas = []
        # de mayor a menor para la jerarquía general (JEFE primero)
        for rango, nombre_visible in reversed(depto["escalafon"]):
            key = f"{depto_id.upper()}_{rango}"
            color = direccion["color_categoria"]
            KEYS_NOMBRES[key] = (nombre_visible, color)
            JERARQUIA_KEYS.append(key)
            keys_de_esta_categoria.append(key)
            keys_depto_ordenadas.append(key)
        # DEPARTAMENTO_KEYS queda de MENOR a MAYOR (staff -> supervisor -> jefe),
        # que es el orden más útil para /ascenso y /descenso.
        DEPARTAMENTO_KEYS[depto_id] = list(reversed(keys_depto_ordenadas))

    CATEGORIAS_ROLES[direccion_id] = {
        "nombre": direccion["nombre"],
        "separador": (f"▬▬▬▬▬ {direccion['nombre'].upper()} ▬▬▬▬▬", direccion["color_categoria"]),
        "keys": keys_de_esta_categoria,
    }

# Compatibilidad con nombres de keys que usaba el código anterior
DIRECTOR_KEYS = [k for k in KEYS_NOMBRES if k.startswith("DIRECTOR_")]

# ============================================================================
# 6) ENRUTAMIENTO DE SOLICITUDES
#    - Cada carta de solicitud de un departamento va al Director de SU
#      Dirección (se resuelve automáticamente vía DEPARTAMENTOS -> DIRECCIONES).
#    - Las solicitudes generales van a esta key.
#    - Descargo/degradación siempre van a Recursos Humanos.
#    - Si nadie tiene la key destino asignada, el bot sube un nivel
#      automáticamente (ver solicitudes.py); si aun así no hay nadie, se
#      publica en el canal de log correspondiente.
# ============================================================================
SOLICITUD_GENERAL_KEY = "JEFE_JUNTA_DIRECTIVA"
RRHH_KEY = DIRECCIONES["RRHH"]["director_key"]


def director_key_de(depto_id: str) -> str:
    """Devuelve la key del Director responsable de un departamento dado."""
    direccion_id = DEPARTAMENTOS[depto_id]["direccion"]
    return DIRECCIONES[direccion_id]["director_key"]


# ============================================================================
# 7) ROL ESPECIAL DE SUSPENSIÓN (usado por /suspender y /reincorporar)
# ============================================================================
ROL_SUSPENDIDO_NOMBRE = "⛔ Suspendido"
ROL_SUSPENDIDO_COLOR = "#4a4a4a"

# ============================================================================
# 8) CANALES (opcional) - IDs de canales donde el bot publica registros.
#    Déjalos en None si no quieres logs en canal (los DMs igual se envían).
# ============================================================================
CANALES = {
    "log_roles": None,
    "log_finanzas": None,
    "log_documentos": None,
    "log_ascensos": None,
    "log_personal": None,       # asistencia / advertencias / solicitudes / descargos
    "log_pacientes": None,      # admisiones / altas / notas clínicas
    "log_inventario": None,     # movimientos de stock
    "log_turnos": None,         # entradas/salidas y asignaciones de turno
    "log_capacitaciones": None,
    "log_quejas": None,         # quejas formales
    "log_postulaciones": None,  # postulaciones al staff (si no se define, usa log_personal)
    "log_recetas": None,        # recetas médicas emitidas
    "log_cirugias": None,       # cirugías programadas / realizadas
    "log_laboratorio": None,    # solicitudes y resultados de laboratorio
    "log_seguridad": None,      # incidentes de seguridad
    "alerta_codigos": None,     # activación/cancelación de códigos de emergencia (recomendado)
}

# ============================================================================
# 9) ESTILO VISUAL
# ============================================================================
NOMBRE_HOSPITAL = "Hospital Central"
LOGO_URL = None

# ============================================================================
# 10) SISTEMA DE TICKETS
#     NIVEL_MINIMO_TICKETS usa nivel genérico: cualquier key de nivel JEFE
#     o superior (JEFE de cualquier depto, Director, Junta, Owner) puede
#     atender tickets.
# ============================================================================
TICKET_CATEGORIA_ID = None
NIVEL_MINIMO_TICKETS = "JEFE"

# ============================================================================
# 11) PACIENTES: niveles de gravedad usados en /paciente admitir
# ============================================================================
GRAVEDAD_PACIENTE = ["Leve", "Moderado", "Grave", "Crítico"]

# ============================================================================
# 12) INVENTARIO / LOGÍSTICA: categorías sugeridas para /inventario agregar
# ============================================================================
CATEGORIAS_INVENTARIO = [
    "Medicamentos", "Material Quirúrgico", "Equipo Médico",
    "Insumos de Enfermería", "Alimentos", "Limpieza", "Administrativo", "Otro",
]

# ============================================================================
# 13) FICHA DE PERSONAL: campos editables con /ficha editar
# ============================================================================
FICHA_CAMPOS = {
    "especialidad": "Especialidad / puesto",
    "licencia": "N.° de licencia o matrícula",
    "contacto": "Contacto (RP)",
    "notas": "Notas administrativas",
}

# ============================================================================
# 14) CÓDIGOS DE EMERGENCIA
#     "mencion_keys" ahora puede usar tanto una key exacta (ej.
#     "DIRECTOR_MEDICO") como un nivel genérico con prefijo "NIVEL:"
#     (ej. "NIVEL:JEFE" menciona a TODOS los jefes de cualquier depto).
# ============================================================================
CODIGOS_EMERGENCIA = {
    "azul": {
        "nombre": "🔵 Código Azul",
        "descripcion": "Paro cardio/respiratorio — se requiere RCP inmediata.",
        "color": "#3498db",
        "mencion_keys": ["DIRECTOR_MEDICO", "DIRECTOR_ENFERMERIA", "NIVEL:JEFE"],
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

# ============================================================================
# 15) COMANDOS ADICIONALES SUGERIDOS POR DEPARTAMENTO
#     Roadmap de comandos nuevos, ya con la key mínima requerida para
#     usarlos. No están implementados todavía como cogs; sirven de guía
#     para desarrollarlos y para que /ayuda los liste agrupados por área.
# ============================================================================
COMANDOS_ADICIONALES = {
    "medico": [
        ("/receta_emitir", "Emite una receta médica a un paciente", "MEDICO_STAFF"),
        ("/receta_ver", "Consulta las recetas activas de un paciente", "MEDICO_STAFF"),
        ("/diagnostico", "Registra un diagnóstico en la ficha clínica", "MEDICO_STAFF"),
    ],
    "cirugia": [
        ("/cirugia_programar", "Agenda una cirugía con quirófano y equipo", "CIRUGIA_SUPERVISOR"),
        ("/cirugia_listar", "Lista las cirugías programadas", "CIRUGIA_STAFF"),
        ("/cirugia_resultado", "Registra el resultado de una cirugía realizada", "CIRUGIA_STAFF"),
    ],
    "laboratorio": [
        ("/laboratorio_solicitar", "Solicita un examen de laboratorio", "MEDICO_STAFF"),
        ("/laboratorio_resultado", "Carga el resultado de un examen", "LABORATORIO_STAFF"),
        ("/laboratorio_pendientes", "Lista los exámenes pendientes de resultado", "LABORATORIO_STAFF"),
    ],
    "enfermeria": [
        ("/signos_vitales", "Registra los signos vitales de un paciente", "ENFERMERIA_STAFF"),
        ("/medicacion_administrar", "Marca una dosis de medicación como administrada", "ENFERMERIA_STAFF"),
    ],
    "emergencias": [
        ("/triage", "Clasifica a un paciente por nivel de urgencia al ingreso", "EMERGENCIAS_STAFF"),
        ("/ambulancia_despachar", "Despacha una unidad de emergencia", "EMERGENCIAS_SUPERVISOR"),
        ("/ambulancia_estado", "Consulta el estado de las unidades en ruta", "EMERGENCIAS_STAFF"),
    ],
    "traslados": [
        ("/traslado_solicitar", "Solicita el traslado de un paciente entre áreas", "STAFF"),
        ("/traslado_completar", "Marca un traslado como completado", "TRASLADOS_STAFF"),
    ],
    "seguridad": [
        ("/incidente_reportar", "Reporta un incidente de seguridad", "SEGURIDAD_STAFF"),
        ("/evacuacion", "Activa el protocolo de evacuación", "SEGURIDAD_SUPERVISOR"),
        ("/acceso_restringir", "Restringe el acceso a un área del hospital", "SEGURIDAD_SUPERVISOR"),
    ],
    "farmacia": [
        ("/farmacia_dispensar", "Dispensa un medicamento recetado", "FARMACIA_STAFF"),
        ("/farmacia_stock_critico", "Lista medicamentos por debajo del mínimo", "FARMACIA_STAFF"),
    ],
    "admisiones": [
        ("/cita_agendar", "Agenda una cita para un paciente", "ADMISIONES_STAFF"),
        ("/cita_listar", "Lista las citas del día", "ADMISIONES_STAFF"),
    ],
    "rrhh": [
        ("/evaluacion_desempeno", "Registra la evaluación de desempeño de un empleado", "RRHH_SUPERVISOR"),
        ("/vacaciones_solicitar", "Solicita vacaciones (distinto de licencia médica)", "STAFF"),
        ("/renuncia", "Presenta la renuncia formal de un usuario", "STAFF"),
    ],
    "finanzas": [
        ("/presupuesto_departamento", "Asigna o consulta el presupuesto de un depto", "FINANZAS_SUPERVISOR"),
        ("/auditoria", "Genera un reporte de auditoría financiera interna", "DIRECTOR_FINANCIERO"),
    ],
    "administrativo": [
        ("/acta_reunion", "Genera el acta oficial de una reunión de Junta", "JUNTA_DIRECTIVA"),
        ("/politica_publicar", "Publica una política o reglamento oficial", "ADMINISTRATIVO_JEFE"),
    ],
    "general": [
        ("/estadisticas", "Dashboard con métricas generales del hospital", "NIVEL:JEFE"),
        ("/buscar", "Búsqueda global de usuario, paciente o ítem", "STAFF"),
        ("/ayuda", "Menú de ayuda agrupado por dirección/departamento", "STAFF"),
    ],
}

# ============================================================================
# 16) TOKEN DEL BOT
# ============================================================================
TOKEN = os.getenv("DISCORD_TOKEN")
