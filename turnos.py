"""
turnos.py
=========
Sistema de turnos, persistente en JSON local (turnos.json):
asignación de turnos programados y control de quién está actualmente
en servicio (entrada/salida). Alimenta el grupo de comandos /turno y
el panel de estado general. No necesita edición.
"""

import json
import os
from datetime import datetime, timezone

ARCHIVO = "turnos.json"


def _cargar() -> dict:
    if not os.path.exists(ARCHIVO):
        return {"asignados": [], "en_servicio": {}}
    with open(ARCHIVO, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    data.setdefault("asignados", [])
    data.setdefault("en_servicio", {})
    return data


def _guardar(data: dict):
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat()


def asignar_turno(user_id: int, dia: str, hora_inicio: str, hora_fin: str, area: str, autor_id: int) -> int:
    data = _cargar()
    turno_id = len(data["asignados"]) + 1
    data["asignados"].append({
        "id": turno_id, "usuario_id": user_id, "dia": dia,
        "hora_inicio": hora_inicio, "hora_fin": hora_fin, "area": area,
        "autor_id": autor_id, "fecha_creacion": _ahora(),
    })
    data["asignados"] = data["asignados"][-500:]
    _guardar(data)
    return turno_id


def turnos_de(user_id: int) -> list:
    data = _cargar()
    return [t for t in data["asignados"] if t["usuario_id"] == user_id]


def esta_en_servicio(user_id: int) -> bool:
    data = _cargar()
    return str(user_id) in data["en_servicio"]


def marcar_entrada(user_id: int, area: str = "") -> bool:
    """True si quedó marcado; False si ya estaba en servicio."""
    data = _cargar()
    if str(user_id) in data["en_servicio"]:
        return False
    data["en_servicio"][str(user_id)] = {"desde": _ahora(), "area": area}
    _guardar(data)
    return True


def marcar_salida(user_id: int):
    """Devuelve el registro de entrada (dict) si estaba en servicio, si no None."""
    data = _cargar()
    registro = data["en_servicio"].pop(str(user_id), None)
    _guardar(data)
    return registro


def en_servicio_lista() -> list:
    """Lista de (user_id_int, registro) de todos los que están en servicio."""
    data = _cargar()
    return [(int(uid), r) for uid, r in data["en_servicio"].items()]


def total_en_servicio() -> int:
    return len(en_servicio_lista())
