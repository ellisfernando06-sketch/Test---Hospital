# -*- coding: utf-8 -*-
"""Config de autoridades — rellenar IDs en setup o a mano."""
from __future__ import annotations

# Keys (roles_config / roles_store)
KEY_FUNDADOR = "FUNDADOR_OWNER"
KEY_GOBERNANZA = "COFUNDADOR_GOBERNANZA"
KEY_INTER = "COFUNDADOR_INTERINSTITUCIONAL"
KEY_CALIDAD = "COFUNDADOR_CALIDAD"

KEYS_AUTORIDAD = (KEY_FUNDADOR, KEY_GOBERNANZA, KEY_INTER, KEY_CALIDAD)

# Colores paneles
COLOR_FUNDADOR = 0x9B59B6
COLOR_GOBERNANZA = 0x3498DB
COLOR_INTER = 0x1ABC9C
COLOR_CALIDAD = 0xE67E22
COLOR_OK = 0x2ECC71
COLOR_ERR = 0xE74C3C
COLOR_WARN = 0xF1C40F
COLOR_EMERGENCIA = 0xC0392B

# Límites que requieren aprobación del Fundador
MAX_TIMEOUT_MIN_SIN_APROBACION = 60 * 24  # 24h
MONTO_FINANCIAMIENTO_APROBACION = 10000

# Canales (nombres que setup puede crear; IDs se guardan en store)
CANALES_SETUP = [
    ("panel-fundador", "👑 panel-fundador"),
    ("panel-gobernanza", "⚖️ panel-gobernanza"),
    ("panel-interinstitucional", "🌐 panel-interinstitucional"),
    ("panel-calidad", "🏅 panel-calidad"),
    ("aprobaciones-autoridades", "✅ aprobaciones-autoridades"),
    ("auditoria-autoridades", "🔎 auditoria-autoridades"),
]

CATEGORIA_PANELES = "→【👑】AUTORIDADES"

# Listas de menús
ZONAS = ["gobernanza", "interinstitucional", "calidad"]
GRAVEDADES = ["leve", "moderada", "grave", "centinela"]
PRIORIDADES = ["alta", "media", "baja"]
DURACIONES_DELEGACION = [
    ("1h", 1),
    ("6h", 6),
    ("24h", 24),
    ("3d", 72),
    ("7d", 168),
]
PERIODOS = ["semana", "mes", "trimestre", "año"]
TIPOS_EMERGENCIA = ["sanitaria", "operativa", "seguridad", "institucional"]
TIPOS_CONVENIO = ["docente", "asistencial", "financiero", "tecnológico", "cooperación"]
CATEGORIAS_ALIADO = ["ministerio", "aseguradora", "universidad", "hospital", "ONG", "donante"]

# Roles de personal que talento puede asignar (keys)
ROLES_PERSONAL_KEYS = [
    "DIR_MEDICO", "DIR_ENFERMERIA", "DIR_RRHH", "DIR_DOCENCIA", "DIR_LOGISTICA",
    "DIR_GENERAL", "JEFE_DEPARTAMENTO", "JEFE_SERVICIO", "MEDICO_ESPECIALISTA",
    "MEDICO_GENERAL", "RESIDENTE", "INTERNO", "ENFERMERO_GENERAL", "GUARDIA",
]
