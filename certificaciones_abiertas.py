# -*- coding: utf-8 -*
"""
certificaciones_abiertas.py — Gestión de certificaciones abiertas del sistema.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List, Optional

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "certificaciones_abiertas.json")

_DEFAULTS = [
    {"nombre": "RCP Básico", "descripcion": "Reanimación cardiopulmonar básica", "departamento": "medico", "director_zona_key": "DIRECTOR_MEDICO"},
    {"nombre": "Primeros auxilios", "descripcion": "Atención inicial de emergencias", "departamento": "medico", "director_zona_key": "DIRECTOR_MEDICO"},
    {"nombre": "Bioseguridad", "descripcion": "Normas de bioseguridad hospitalaria", "departamento": "enfermeria", "director_zona_key": "DIRECTOR_ENFERMERIA"},
    {"nombre": "Laboratorista", "descripcion": "Manejo básico de laboratorio", "departamento": "medico", "director_zona_key": "DIRECTOR_MEDICO"},
    {"nombre": "Atención al paciente", "descripcion": "Protocolo de atención y trato al paciente", "departamento": "rrhh", "director_zona_key": "DIRECTOR_RRHH"},
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
    """Si no hay certificaciones, crea un set básico para que /certificar funcione."""
    data = _load()
    if data.get("certificaciones"):
        return
    nid = data.get("next_id", 1)
    for d in _DEFAULTS:
        data["certificaciones"].append({
            "id": nid,
            "nombre": d["nombre"],
            "descripcion": d.get("descripcion", ""),
            "departamento": d.get("departamento", ""),
            "director_zona_key": d.get("director_zona_key", "DIRECTOR_DOCENCIA"),
            "requiere_dos_firmas": True,
            "activa": True,
            "fecha_creacion": datetime.now(timezone.utc).isoformat(),
        })
        nid += 1
    data["next_id"] = nid
    _save(data)
    print(f"[certificaciones_abiertas] defaults creados: {len(_DEFAULTS)}")


def crear_certificacion(
    nombre: str,
    descripcion: str = "",
    departamento: str = "",
    director_zona_key: str = "DIRECTOR_ADMINISTRATIVO",
    requiere_dos_firmas: bool = True,
    activa: bool = True,
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
