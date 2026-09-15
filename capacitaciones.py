"""
capacitaciones.py
==================
Sistema de capacitaciones, persistente en JSON local
(capacitaciones.json): programación de capacitaciones y registro de
quién las completó/certificó. Alimenta el grupo de comandos
/capacitacion. No necesita edición.
"""

import json
import os
from datetime import datetime, timezone

ARCHIVO = "capacitaciones.json"


def _cargar() -> dict:
    if not os.path.exists(ARCHIVO):
        return {"programadas": [], "completadas": {}}
    with open(ARCHIVO, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    data.setdefault("programadas", [])
    data.setdefault("completadas", {})
    return data


def _guardar(data: dict):
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat()


def programar(titulo: str, fecha_hora: str, departamento_slug: str, descripcion: str, autor_id: int) -> int:
    data = _cargar()
    cap_id = len(data["programadas"]) + 1
    data["programadas"].append({
        "id": cap_id, "titulo": titulo, "fecha_hora": fecha_hora,
        "departamento_slug": departamento_slug or "", "descripcion": descripcion,
        "autor_id": autor_id, "fecha_creacion": _ahora(),
    })
    data["programadas"] = data["programadas"][-200:]
    _guardar(data)
    return cap_id


def listar_programadas() -> list:
    return _cargar()["programadas"]


def certificar(user_id: int, titulo: str, autor_id: int):
    data = _cargar()
    lista = data["completadas"].setdefault(str(user_id), [])
    lista.append({"titulo": titulo, "fecha": _ahora(), "autor_id": autor_id})
    data["completadas"][str(user_id)] = lista[-100:]
    _guardar(data)


def completadas_de(user_id: int) -> list:
    return _cargar()["completadas"].get(str(user_id), [])
