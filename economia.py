"""
economia.py
===========
Sistema financiero simple, persistente en un archivo JSON local
(economia.json). Suficiente para un servidor de roleplay; si el
servidor crece mucho, esto se puede migrar a una base de datos real
sin cambiar los comandos del bot (solo estas funciones). No necesita
edición.
"""

import json
import os
from datetime import datetime, timezone

ARCHIVO = "economia.json"
ARCHIVO_LOG = "movimientos_financieros.json"


def _cargar(archivo: str) -> dict:
    if not os.path.exists(archivo):
        return {}
    with open(archivo, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _guardar(archivo: str, data: dict):
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def obtener_balance(user_id: int) -> float:
    data = _cargar(ARCHIVO)
    return float(data.get(str(user_id), 0))


def set_balance(user_id: int, monto: float):
    data = _cargar(ARCHIVO)
    data[str(user_id)] = round(float(monto), 2)
    _guardar(ARCHIVO, data)


def modificar_balance(user_id: int, delta: float) -> float:
    """Suma (o resta, si delta es negativo) al balance. Devuelve el nuevo balance."""
    nuevo = obtener_balance(user_id) + delta
    if nuevo < 0:
        raise ValueError("El balance no puede quedar negativo.")
    set_balance(user_id, nuevo)
    return nuevo


def registrar_movimiento(tipo: str, autor_id: int, objetivo_id: int, monto: float, motivo: str = ""):
    log = _cargar(ARCHIVO_LOG)
    lista = log.get("movimientos", [])
    lista.append(
        {
            "tipo": tipo,
            "autor_id": autor_id,
            "objetivo_id": objetivo_id,
            "monto": monto,
            "motivo": motivo,
            "fecha": datetime.now(timezone.utc).isoformat(),
        }
    )
    log["movimientos"] = lista[-500:]  # conserva solo los últimos 500 registros
    _guardar(ARCHIVO_LOG, log)


def ultimos_movimientos(user_id: int = None, limite: int = 10) -> list:
    log = _cargar(ARCHIVO_LOG)
    movimientos = log.get("movimientos", [])
    if user_id is not None:
        movimientos = [
            m for m in movimientos
            if m["autor_id"] == user_id or m["objetivo_id"] == user_id
        ]
    return movimientos[-limite:][::-1]


def resumen_general(limite_movimientos: int = 10) -> dict:
    """Resumen financiero global del hospital, usado por /balance_general."""
    data = _cargar(ARCHIVO)
    log = _cargar(ARCHIVO_LOG)
    movimientos = log.get("movimientos", [])
    return {
        "total_en_circulacion": round(sum(float(v) for v in data.values()), 2),
        "cuentas_activas": len(data),
        "ultimos_movimientos": movimientos[-limite_movimientos:][::-1],
    }
