# -*- coding: utf-8 -*-
"""
certificaciones_abiertas.py — Gestión de certificaciones abiertas del sistema.
Permite crear, listar y gestionar certificaciones disponibles para certificar.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List, Optional

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "certificaciones_abiertas.json")


def _load() -> dict:
    """Carga el archivo de certificaciones abiertas."""
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
    """Guarda el archivo de certificaciones abiertas."""
    os.makedirs(_DATA_DIR, exist_ok=True)
    try:
        with open(_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[certificaciones_abiertas] Error al guardar: {e}")


def crear_certificacion(
    nombre: str,
    descripcion: str = "",
    departamento: str = "",
    director_zona_key: str = "DIRECTOR_ADMINISTRATIVO",
    requiere_dos_firmas: bool = True,
    activa: bool = True,
) -> int:
    """
    Crea una nueva certificación abierta.
    
    Args:
        nombre: Nombre de la certificación (ej: "Laboratorista", "RCP Básico")
        descripcion: Descripción detallada
        departamento: Departamento/Zona asociada
        director_zona_key: Clave del rol del director de la zona
        requiere_dos_firmas: Si requiere firma de 2 directores
        activa: Si está activa para certificar
    
    Returns:
        ID de la certificación creada
    """
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
    """Lista todas las certificaciones activas."""
    data = _load()
    return [c for c in data.get("certificaciones", []) if c.get("activa", True)]


def listar_todas_certificaciones() -> List[dict]:
    """Lista todas las certificaciones (activas e inactivas)."""
    data = _load()
    return data.get("certificaciones", [])


def obtener_certificacion(cert_id: int) -> Optional[dict]:
    """Obtiene una certificación por ID."""
    data = _load()
    for cert in data.get("certificaciones", []):
        if cert.get("id") == cert_id:
            return cert
    return None


def activar_certificacion(cert_id: int) -> bool:
    """Activa una certificación."""
    data = _load()
    for cert in data.get("certificaciones", []):
        if cert.get("id") == cert_id:
            cert["activa"] = True
            _save(data)
            return True
    return False


def desactivar_certificacion(cert_id: int) -> bool:
    """Desactiva una certificación."""
    data = _load()
    for cert in data.get("certificaciones", []):
        if cert.get("id") == cert_id:
            cert["activa"] = False
            _save(data)
            return True
    return False


def actualizar_certificacion(cert_id: int, **kwargs) -> Optional[dict]:
    """Actualiza los datos de una certificación."""
    data = _load()
    for cert in data.get("certificaciones", []):
        if cert.get("id") == cert_id:
            cert.update(kwargs)
            _save(data)
            return cert
    return None


def eliminar_certificacion(cert_id: int) -> bool:
    """Elimina una certificación."""
    data = _load()
    original_len = len(data.get("certificaciones", []))
    data["certificaciones"] = [
        c for c in data.get("certificaciones", [])
        if c.get("id") != cert_id
    ]
    if len(data["certificaciones"]) < original_len:
        _save(data)
        return True
    return False
