"""
inventario.py
=============
Sistema de inventario / logística, persistente en JSON local
(inventario.json + movimientos_inventario.json): stock por ítem,
mínimos de alerta y bitácora de movimientos (entradas/salidas).
Alimenta el grupo de comandos /inventario y el panel de estado
general. No necesita edición.
"""

import json
import os
from datetime import datetime, timezone

ARCHIVO = "inventario.json"
ARCHIVO_LOG = "movimientos_inventario.json"


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


def _clave(nombre_item: str) -> str:
    return nombre_item.strip().lower()


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat()


def obtener_item(nombre_item: str) -> dict:
    data = _cargar(ARCHIVO)
    return data.get(_clave(nombre_item))


def todos_los_items() -> list:
    data = _cargar(ARCHIVO)
    return sorted(data.values(), key=lambda i: i["nombre"].lower())


def items_bajo_minimo() -> list:
    return [i for i in todos_los_items() if i["cantidad"] <= i.get("minimo", 0)]


def agregar_stock(nombre_item: str, cantidad: int, categoria: str, autor_id: int, motivo: str = ""):
    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor a 0.")
    data = _cargar(ARCHIVO)
    clave = _clave(nombre_item)
    item = data.setdefault(clave, {"nombre": nombre_item, "cantidad": 0, "minimo": 0, "categoria": categoria or "Otro"})
    item["nombre"] = nombre_item
    if categoria:
        item["categoria"] = categoria
    item["cantidad"] = item.get("cantidad", 0) + cantidad
    _guardar(ARCHIVO, data)
    _registrar_movimiento("entrada", nombre_item, cantidad, autor_id, motivo)
    return item["cantidad"]


def retirar_stock(nombre_item: str, cantidad: int, autor_id: int, motivo: str = ""):
    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor a 0.")
    data = _cargar(ARCHIVO)
    clave = _clave(nombre_item)
    item = data.get(clave)
    if not item or item.get("cantidad", 0) < cantidad:
        raise LookupError("No hay suficiente stock de ese ítem.")
    item["cantidad"] -= cantidad
    _guardar(ARCHIVO, data)
    _registrar_movimiento("salida", item["nombre"], -cantidad, autor_id, motivo)
    return item["cantidad"]


def set_minimo(nombre_item: str, minimo: int):
    data = _cargar(ARCHIVO)
    clave = _clave(nombre_item)
    item = data.get(clave)
    if not item:
        raise LookupError("Ese ítem no existe en el inventario todavía.")
    item["minimo"] = max(0, minimo)
    _guardar(ARCHIVO, data)


def _registrar_movimiento(tipo: str, nombre_item: str, delta: int, autor_id: int, motivo: str = ""):
    log = _cargar(ARCHIVO_LOG)
    lista = log.get("movimientos", [])
    lista.append({
        "tipo": tipo, "item": nombre_item, "delta": delta,
        "autor_id": autor_id, "motivo": motivo, "fecha": _ahora(),
    })
    log["movimientos"] = lista[-500:]
    _guardar(ARCHIVO_LOG, log)


def ultimos_movimientos(limite: int = 10) -> list:
    log = _cargar(ARCHIVO_LOG)
    return log.get("movimientos", [])[-limite:][::-1]
