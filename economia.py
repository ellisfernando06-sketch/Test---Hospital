# -*- coding: utf-8 -*-
"""
economia.py — Balances y movimientos financieros.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "economia.json")


def _load() -> dict:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_PATH):
        return {"balances": {}, "movimientos": []}
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("balances", {})
        data.setdefault("movimientos", [])
        return data
    except Exception:
        return {"balances": {}, "movimientos": []}


def _save(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def obtener_balance(uid: int) -> float:
    data = _load()
    return float(data["balances"].get(str(uid), 0.0))


def modificar_balance(uid: int, delta: float) -> float:
    data = _load()
    key = str(uid)
    actual = float(data["balances"].get(key, 0.0))
    nuevo = actual + delta
    # BUG CORREGIDO: antes esta función nunca validaba fondos suficientes y
    # dejaba que el balance quedara en negativo sin avisar. bot_hospital.py
    # (en /retirar y /transferir) espera que se lance ValueError cuando no
    # alcanza el saldo, y lo captura con "except ValueError" — pero como
    # nunca se lanzaba, cualquiera podía retirar o transferir más dinero
    # del que realmente tenía. Ahora se valida antes de guardar.
    if nuevo < 0:
        raise ValueError("Fondos insuficientes.")
    data["balances"][key] = nuevo
    _save(data)
    return nuevo


def registrar_movimiento(tipo: str, de_id: int, a_id: int, monto: float, motivo: str = "") -> None:
    data = _load()
    data["movimientos"].append({
        "fecha": datetime.now(timezone.utc).isoformat(),
        "tipo": tipo,
        "de_id": de_id,
        "a_id": a_id,
        "monto": monto,
        "motivo": motivo,
    })
    _save(data)


def ultimos_movimientos(uid: int, limite: int = 15) -> List[dict]:
    """
    Últimos movimientos financieros de un usuario (como emisor o receptor).
    BUG CORREGIDO: bot_hospital.py llama a economia.ultimos_movimientos()
    en /historial_financiero, pero esta función no existía (antes se
    llamaba historial()), lo que causaba un AttributeError y hacía
    truenar el comando. Se renombró y se conserva historial() como alias
    por compatibilidad.
    """
    data = _load()
    movs = [
        m for m in data["movimientos"]
        if m.get("de_id") == uid or m.get("a_id") == uid
    ]
    return movs[-limite:]


def historial(uid: int, limite: int = 15) -> List[dict]:
    """Alias retrocompatible de ultimos_movimientos()."""
    return ultimos_movimientos(uid, limite)


def resumen_general(limite_movimientos: int = 10) -> dict:
    """
    Resumen financiero general del hospital.
    BUG CORREGIDO: bot_hospital.py llama a economia.resumen_general() en
    /balance_general, pero la función no existía en absoluto, lo que
    causaba un AttributeError y hacía truenar el comando.
    """
    data = _load()
    total_en_circulacion = sum(float(v) for v in data["balances"].values())
    cuentas_activas = sum(1 for v in data["balances"].values() if float(v) != 0)
    return {
        "total_en_circulacion": total_en_circulacion,
        "cuentas_activas": cuentas_activas,
        "ultimos_movimientos": data["movimientos"][-limite_movimientos:],
    }
