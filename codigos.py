"""
codigos.py
==========
Estado de los códigos de emergencia hospitalarios definidos en
config.CODIGOS_EMERGENCIA (Código Azul, Rojo, Plata, etc.),
persistente en JSON local (codigos_activos.json). Un mismo código
puede estar activo en varias ubicaciones a la vez. Alimenta el grupo
de comandos /codigo y el panel de estado general. No necesita
edición.
"""

import json
import os
from datetime import datetime, timezone

ARCHIVO = "codigos_activos.json"


def _cargar() -> list:
    if not os.path.exists(ARCHIVO):
        return []
    with open(ARCHIVO, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _guardar(data: list):
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat()


def activar(codigo_key: str, ubicacion: str, detalles: str, autor_id: int) -> dict:
    data = _cargar()
    entrada = {
        "codigo": codigo_key, "ubicacion": ubicacion, "detalles": detalles,
        "autor_id": autor_id, "fecha": _ahora(),
    }
    data.append(entrada)
    _guardar(data)
    return entrada


def cancelar_todos(codigo_key: str) -> int:
    """Cancela todas las activaciones vigentes de ese código. Devuelve cuántas se cerraron."""
    data = _cargar()
    restantes = [e for e in data if e["codigo"] != codigo_key]
    cerradas = len(data) - len(restantes)
    _guardar(restantes)
    return cerradas


def activos() -> list:
    return _cargar()


def hay_activos() -> bool:
    return bool(_cargar())
