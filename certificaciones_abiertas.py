# -*- coding: utf-8 -*
"""
certificaciones_abiertas.py — Certificaciones por rama / dirección del hospital.
Enlazables con capacitaciones programadas.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List, Optional

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "certificaciones_abiertas.json")

# Catálogo base: todas las ramas y direcciones
# departamento = slug de config.DEPARTAMENTOS o "general"
_DEFAULTS = [
    # ── General / transversal ──
    {"nombre": "RCP Básico", "descripcion": "Reanimación cardiopulmonar básica", "departamento": "general", "director_zona_key": "DIRECTOR_DOCENCIA", "rol_clave": "cert_rcp"},
    {"nombre": "Primeros auxilios", "descripcion": "Atención inicial de emergencias", "departamento": "general", "director_zona_key": "DIRECTOR_DOCENCIA", "rol_clave": "cert_primeros_auxilios"},
    {"nombre": "Bioseguridad", "descripcion": "Normas de bioseguridad hospitalaria", "departamento": "general", "director_zona_key": "DIRECTOR_DOCENCIA", "rol_clave": "cert_bioseguridad"},
    {"nombre": "Atención al paciente", "descripcion": "Protocolo de trato y atención al paciente", "departamento": "general", "director_zona_key": "DIRECTOR_RRHH", "rol_clave": "cert_atencion_paciente"},
    {"nombre": "Ética hospitalaria", "descripcion": "Código ético y confidencialidad", "departamento": "general", "director_zona_key": "DIRECTOR_GENERAL", "rol_clave": "cert_etica"},
    {"nombre": "Evacuación y códigos", "descripcion": "Códigos de emergencia y evacuación", "departamento": "general", "director_zona_key": "DIRECTOR_SEGURIDAD", "rol_clave": "cert_evacuacion"},
    # ── Cuerpo médico ──
    {"nombre": "Laboratorista", "descripcion": "Manejo básico de laboratorio clínico", "departamento": "medico", "director_zona_key": "DIRECTOR_MEDICO", "rol_clave": "cert_laboratorista"},
    {"nombre": "Soporte vital avanzado", "descripcion": "SVA / ACLS orientado a RP médico", "departamento": "medico", "director_zona_key": "DIRECTOR_MEDICO", "rol_clave": "cert_sva"},
    {"nombre": "Urgencias médicas", "descripcion": "Protocolo de urgencias y triage", "departamento": "medico", "director_zona_key": "DIRECTOR_MEDICO", "rol_clave": "cert_urgencias"},
    {"nombre": "Procedimientos clínicos", "descripcion": "Procedimientos básicos de consulta", "departamento": "medico", "director_zona_key": "DIRECTOR_MEDICO", "rol_clave": "cert_proc_clinicos"},
    {"nombre": "Cirugía menor (RP)", "descripcion": "Protocolo de quirófano y cirugía menor RP", "departamento": "medico", "director_zona_key": "DIRECTOR_MEDICO", "rol_clave": "cert_cirugia"},
    # ── Enfermería ──
    {"nombre": "Cuidados de enfermería", "descripcion": "Cuidados básicos y registro de enfermería", "departamento": "enfermeria", "director_zona_key": "DIRECTOR_ENFERMERIA", "rol_clave": "cert_cuidados_enf"},
    {"nombre": "Administración de medicamentos", "descripcion": "Vías, dosis y seguridad en medicación", "departamento": "enfermeria", "director_zona_key": "DIRECTOR_ENFERMERIA", "rol_clave": "cert_medicacion"},
    {"nombre": "Curaciones y heridas", "descripcion": "Técnicas de curación y vendaje", "departamento": "enfermeria", "director_zona_key": "DIRECTOR_ENFERMERIA", "rol_clave": "cert_curaciones"},
    {"nombre": "Monitorización de signos", "descripcion": "Toma y registro de signos vitales", "departamento": "enfermeria", "director_zona_key": "DIRECTOR_ENFERMERIA", "rol_clave": "cert_signos"},
    # ── RRHH ──
    {"nombre": "Inducción de personal", "descripcion": "Ingreso, normativa interna y organigrama", "departamento": "rrhh", "director_zona_key": "DIRECTOR_RRHH", "rol_clave": "cert_induccion"},
    {"nombre": "Gestión de expedientes", "descripcion": "Manejo de expedientes y sanciones", "departamento": "rrhh", "director_zona_key": "DIRECTOR_RRHH", "rol_clave": "cert_expedientes"},
    {"nombre": "Entrevistas y selección", "descripcion": "Proceso de postulación y entrevistas", "departamento": "rrhh", "director_zona_key": "DIRECTOR_RRHH", "rol_clave": "cert_entrevistas"},
    # ── Finanzas ──
    {"nombre": "Caja y cobranza", "descripcion": "Manejo de caja y pagos RP", "departamento": "finanzas", "director_zona_key": "DIRECTOR_FINANCIERO", "rol_clave": "cert_caja"},
    {"nombre": "Contabilidad básica", "descripcion": "Registros contables del hospital", "departamento": "finanzas", "director_zona_key": "DIRECTOR_FINANCIERO", "rol_clave": "cert_contabilidad"},
    {"nombre": "Presupuestos departamentales", "descripcion": "Solicitud y control de presupuesto", "departamento": "finanzas", "director_zona_key": "DIRECTOR_FINANCIERO", "rol_clave": "cert_presupuesto"},
    # ── Logística ──
    {"nombre": "Control de inventario", "descripcion": "Entrada, salida y stock de insumos", "departamento": "logistica", "director_zona_key": "DIRECTOR_LOGISTICA", "rol_clave": "cert_inventario"},
    {"nombre": "Almacén hospitalario", "descripcion": "Organización y seguridad de almacén", "departamento": "logistica", "director_zona_key": "DIRECTOR_LOGISTICA", "rol_clave": "cert_almacen"},
    {"nombre": "Cadena de frío", "descripcion": "Conservación de insumos sensibles", "departamento": "logistica", "director_zona_key": "DIRECTOR_LOGISTICA", "rol_clave": "cert_cadena_frio"},
    # ── Seguridad ──
    {"nombre": "Vigilancia hospitalaria", "descripcion": "Rondas, accesos y reportes", "departamento": "seguridad", "director_zona_key": "DIRECTOR_SEGURIDAD", "rol_clave": "cert_vigilancia"},
    {"nombre": "Control de accesos", "descripcion": "Credenciales y zonas restringidas", "departamento": "seguridad", "director_zona_key": "DIRECTOR_SEGURIDAD", "rol_clave": "cert_accesos"},
    {"nombre": "Protocolo de amenazas", "descripcion": "Códigos plata/negro y contención", "departamento": "seguridad", "director_zona_key": "DIRECTOR_SEGURIDAD", "rol_clave": "cert_amenazas"},
    # ── Administración ──
    {"nombre": "Recepción y orientación", "descripcion": "Atención en mostrador y derivación", "departamento": "administracion", "director_zona_key": "DIRECTOR_ADMINISTRATIVO", "rol_clave": "cert_recepcion"},
    {"nombre": "Documentación administrativa", "descripcion": "Formularios, archivos y correspondencia", "departamento": "administracion", "director_zona_key": "DIRECTOR_ADMINISTRATIVO", "rol_clave": "cert_doc_admin"},
    {"nombre": "Agenda y citas", "descripcion": "Gestión de citas y agenda hospitalaria", "departamento": "administracion", "director_zona_key": "DIRECTOR_ADMINISTRATIVO", "rol_clave": "cert_citas"},
    # ── Docencia ──
    {"nombre": "Formador de formadores", "descripcion": "Diseño y dictado de capacitaciones", "departamento": "docencia", "director_zona_key": "DIRECTOR_DOCENCIA", "rol_clave": "cert_formador"},
    {"nombre": "Evaluación de competencias", "descripcion": "Criterios de certificación y evaluación", "departamento": "docencia", "director_zona_key": "DIRECTOR_DOCENCIA", "rol_clave": "cert_evaluacion"},
    {"nombre": "Investigación básica", "descripcion": "Metodología de investigación hospitalaria", "departamento": "docencia", "director_zona_key": "DIRECTOR_DOCENCIA", "rol_clave": "cert_investigacion"},
    # ── Disciplina / Dirección general (transversal alta) ──
    {"nombre": "Normativa disciplinaria", "descripcion": "Régimen disciplinario y citatorios", "departamento": "general", "director_zona_key": "DIRECTOR_DISCIPLINA", "rol_clave": "cert_disciplina"},
    {"nombre": "Liderazgo hospitalario", "descripcion": "Liderazgo para mandos y jefaturas", "departamento": "general", "director_zona_key": "DIRECTOR_GENERAL", "rol_clave": "cert_liderazgo"},
]


def _load() -> dict:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_PATH):
        return {"certificaciones": [], "next_id": 1}
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("certificaciones", [])
        data.setdefault("next_id", 1)
        return data
    except Exception:
        return {"certificaciones": [], "next_id": 1}


def _save(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    try:
        with open(_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[certificaciones_abiertas] Error al guardar: {e}")


def asegurar_defaults() -> None:
    """Crea o completa el catálogo con todas las certificaciones por rama."""
    data = _load()
    existentes = {(c.get("nombre") or "").strip().lower() for c in data.get("certificaciones", [])}
    nid = int(data.get("next_id") or 1)
    añadidos = 0
    for d in _DEFAULTS:
        key = d["nombre"].strip().lower()
        if key in existentes:
            continue
        data["certificaciones"].append({
            "id": nid,
            "nombre": d["nombre"],
            "descripcion": d.get("descripcion", ""),
            "departamento": d.get("departamento", "general"),
            "director_zona_key": d.get("director_zona_key", "DIRECTOR_DOCENCIA"),
            "rol_clave": d.get("rol_clave", "certificado_general"),
            "requiere_dos_firmas": True,
            "activa": True,
            "fecha_creacion": datetime.now(timezone.utc).isoformat(),
        })
        existentes.add(key)
        nid += 1
        añadidos += 1
    data["next_id"] = nid
    if añadidos:
        _save(data)
        print(f"[certificaciones_abiertas] +{añadidos} certificaciones")


def crear_certificacion(
    nombre: str,
    descripcion: str = "",
    departamento: str = "general",
    director_zona_key: str = "DIRECTOR_DOCENCIA",
    requiere_dos_firmas: bool = True,
    activa: bool = True,
    rol_clave: str = "certificado_general",
) -> int:
    data = _load()
    cert_id = data.get("next_id", 1)
    data["next_id"] = cert_id + 1
    data.setdefault("certificaciones", []).append({
        "id": cert_id,
        "nombre": nombre,
        "descripcion": descripcion,
        "departamento": departamento,
        "director_zona_key": director_zona_key,
        "rol_clave": rol_clave,
        "requiere_dos_firmas": requiere_dos_firmas,
        "activa": activa,
        "fecha_creacion": datetime.now(timezone.utc).isoformat(),
    })
    _save(data)
    return cert_id


def listar_certificaciones_activas() -> List[dict]:
    asegurar_defaults()
    data = _load()
    return [c for c in data.get("certificaciones", []) if c.get("activa", True)]


def listar_por_departamento(departamento: str) -> List[dict]:
    dep = (departamento or "").strip().lower()
    out = []
    for c in listar_certificaciones_activas():
        d = (c.get("departamento") or "general").lower()
        if not dep or dep in ("general", "todos", "all") or d == dep or d == "general":
            out.append(c)
    return out


def listar_todas_certificaciones() -> List[dict]:
    asegurar_defaults()
    data = _load()
    return data.get("certificaciones", [])


def obtener_certificacion(cert_id: int) -> Optional[dict]:
    data = _load()
    for cert in data.get("certificaciones", []):
        if int(cert.get("id", -1)) == int(cert_id):
            return cert
    return None


def obtener_por_nombre(nombre: str) -> Optional[dict]:
    n = (nombre or "").strip().lower()
    for c in listar_certificaciones_activas():
        if (c.get("nombre") or "").strip().lower() == n:
            return c
    return None


def activar_certificacion(cert_id: int) -> bool:
    data = _load()
    for cert in data.get("certificaciones", []):
        if int(cert.get("id", -1)) == int(cert_id):
            cert["activa"] = True
            _save(data)
            return True
    return False


def desactivar_certificacion(cert_id: int) -> bool:
    data = _load()
    for cert in data.get("certificaciones", []):
        if int(cert.get("id", -1)) == int(cert_id):
            cert["activa"] = False
            _save(data)
            return True
    return False


def actualizar_certificacion(cert_id: int, **kwargs) -> Optional[dict]:
    data = _load()
    for cert in data.get("certificaciones", []):
        if int(cert.get("id", -1)) == int(cert_id):
            cert.update(kwargs)
            _save(data)
            return cert
    return None


def eliminar_certificacion(cert_id: int) -> bool:
    data = _load()
    original_len = len(data.get("certificaciones", []))
    data["certificaciones"] = [
        c for c in data.get("certificaciones", [])
        if int(c.get("id", -1)) != int(cert_id)
    ]
    if len(data["certificaciones"]) < original_len:
        _save(data)
        return True
    return False
