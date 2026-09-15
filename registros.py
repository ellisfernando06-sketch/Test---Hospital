"""
registros.py
============
Historiales de personal, persistidos en un JSON local
(registros.json): asistencia, advertencias, licencias/permisos y
eventos de cargo (ascensos, descensos, transferencias,
contrataciones, despidos, suspensiones). Alimenta /expediente,
/mi_expediente y /historial_advertencias. No necesita edición.
"""

import json
import os
from datetime import datetime, timezone

ARCHIVO = "registros.json"


def _cargar() -> dict:
    if not os.path.exists(ARCHIVO):
        return {}
    with open(ARCHIVO, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _guardar(data: dict):
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _lista(user_id: int, campo: str) -> list:
    data = _cargar()
    return data.get(str(user_id), {}).get(campo, [])


def _agregar(user_id: int, campo: str, entrada: dict, limite: int = 200):
    data = _cargar()
    perfil = data.setdefault(str(user_id), {})
    lista = perfil.setdefault(campo, [])
    lista.append(entrada)
    perfil[campo] = lista[-limite:]
    _guardar(data)


# --- Asistencia -------------------------------------------------------------
def registrar_asistencia(user_id: int, estado: str, autor_id: int):
    _agregar(user_id, "asistencia", {"estado": estado, "autor_id": autor_id, "fecha": _ahora()})


def asistencia_de(user_id: int) -> list:
    return _lista(user_id, "asistencia")


# --- Advertencias -------------------------------------------------------------
def registrar_advertencia(user_id: int, motivo: str, autor_id: int):
    _agregar(user_id, "advertencias", {"motivo": motivo, "autor_id": autor_id, "fecha": _ahora()})


def advertencias_de(user_id: int) -> list:
    return _lista(user_id, "advertencias")


# --- Licencias / permisos ------------------------------------------------------
def registrar_licencia(user_id: int, motivo: str, desde: str, hasta: str, autor_id: int):
    _agregar(user_id, "licencias", {
        "motivo": motivo, "desde": desde, "hasta": hasta, "autor_id": autor_id, "fecha": _ahora()
    })


def licencias_de(user_id: int) -> list:
    return _lista(user_id, "licencias")


# --- Historial de cargos --------------------------------------------------------
def registrar_evento_cargo(user_id: int, tipo: str, detalle: str, autor_id: int):
    _agregar(user_id, "cargos", {"tipo": tipo, "detalle": detalle, "autor_id": autor_id, "fecha": _ahora()})


def historial_cargos_de(user_id: int) -> list:
    return _lista(user_id, "cargos")


def expediente_completo(user_id: int) -> dict:
    data = _cargar()
    return data.get(str(user_id), {})
