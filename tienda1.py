# -*- coding: utf-8 -*
"""tienda.py parte 1 — catálogo e inventario."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import discord
from discord import ui, app_commands
from discord.ext import commands

import config
import economia
import permisos

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_INV_PATH = os.path.join(_DATA_DIR, "inventario_jugadores.json")
_CLAIM_PATH = os.path.join(_DATA_DIR, "bienvenida_claims.json")
MONEDA = getattr(config, "MONEDA", "$") or "$"

CATALOGO: Dict[str, dict] = {
    "estetoscopio": {"nombre": "Estetoscopio clínico", "cat": "instrumentos_medicos", "emoji": "🩺", "precio": 185.0, "desc": "Doble campana, acero inoxidable.", "stock": 40},
    "tensiometro": {"nombre": "Tensiómetro aneroide", "cat": "instrumentos_medicos", "emoji": "💉", "precio": 95.0, "desc": "Esfigmomanómetro adulto/pediátrico.", "stock": 50},
    "oximetro": {"nombre": "Oxímetro de pulso", "cat": "instrumentos_medicos", "emoji": "📟", "precio": 65.0, "desc": "SpO2 y frecuencia cardíaca.", "stock": 80},
    "otoscopio": {"nombre": "Otoscopio LED", "cat": "instrumentos_medicos", "emoji": "🔦", "precio": 120.0, "desc": "Examen de oído + 10 espéculos.", "stock": 30},
    "glucometro": {"nombre": "Glucómetro + 25 tiras", "cat": "instrumentos_medicos", "emoji": "🩸", "precio": 48.0, "desc": "Glucosa capilar + lancetas.", "stock": 60},
    "termometro_ir": {"nombre": "Termómetro infrarrojo", "cat": "instrumentos_medicos", "emoji": "🌡️", "precio": 42.0, "desc": "Sin contacto, 1 s.", "stock": 70},
    "botiquin_basico": {"nombre": "Botiquín básico", "cat": "farmacia", "emoji": "🧰", "precio": 35.0, "desc": "Gasas, vendas, alcohol, apósitos, guantes.", "stock": 100},
    "kit_sutura": {"nombre": "Kit de sutura desechable", "cat": "farmacia", "emoji": "🪡", "precio": 28.0, "desc": "Porta-agujas, pinza, hilo, gasas.", "stock": 45},
    "mascarillas_n95": {"nombre": "Caja mascarillas N95 (20)", "cat": "farmacia", "emoji": "😷", "precio": 55.0, "desc": "Protección respiratoria.", "stock": 90},
    "guantes_nitrilo": {"nombre": "Caja guantes nitrilo (100)", "cat": "farmacia", "emoji": "🧤", "precio": 18.0, "desc": "Talla M, sin polvo.", "stock": 120},
    "uniforme_medico": {"nombre": "Uniforme médico completo", "cat": "uniformes", "emoji": "🥼", "precio": 75.0, "desc": "Filipina + pantalón + cofia.", "stock": 50},
    "bata_blanca": {"nombre": "Bata blanca profesional", "cat": "uniformes", "emoji": "👔", "precio": 55.0, "desc": "Algodón, bolsillos laterales.", "stock": 40},
    "noche_residencia": {"nombre": "Noche en residencia del personal", "cat": "hospedaje", "emoji": "🛏️", "precio": 40.0, "desc": "Habitación individual, baño compartido.", "stock": -1},
    "semana_residencia": {"nombre": "Semana en residencia del personal", "cat": "hospedaje", "emoji": "🏠", "precio": 220.0, "desc": "7 noches + cocina común.", "stock": -1},
    "suite_guardia": {"nombre": "Suite de guardia (24 h)", "cat": "hospedaje", "emoji": "🏨", "precio": 85.0, "desc": "Cama, escritorio, ducha privada.", "stock": -1},
    "depto_studio": {"nombre": "Depto studio (alquiler mensual)", "cat": "casas", "emoji": "🏢", "precio": 650.0, "desc": "Cerca del hospital, 1 ambiente.", "stock": 8},
    "casa_2hab": {"nombre": "Casa 2 habitaciones (mensual)", "cat": "casas", "emoji": "🏡", "precio": 980.0, "desc": "Zona residencial, patio, 2 baños.", "stock": 4},
    "habitacion_compartida": {"nombre": "Habitación compartida (mensual)", "cat": "casas", "emoji": "🚪", "precio": 280.0, "desc": "Para personal en formación.", "stock": 15},
    "gasolina_20l": {"nombre": "Gasolina 20 litros", "cat": "combustible", "emoji": "⛽", "precio": 32.0, "desc": "Combustible regular estación hospital.", "stock": -1},
    "gasolina_40l": {"nombre": "Gasolina 40 litros", "cat": "combustible", "emoji": "⛽", "precio": 60.0, "desc": "Descuento institucional.", "stock": -1},
    "tarjeta_transporte": {"nombre": "Tarjeta transporte urbano (mes)", "cat": "combustible", "emoji": "🚌", "precio": 45.0, "desc": "Rutas ciudad–hospital.", "stock": -1},
    "carga_electrica": {"nombre": "Carga vehículo eléctrico (full)", "cat": "combustible", "emoji": "🔌", "precio": 22.0, "desc": "Punto de carga del hospital.", "stock": -1},
    "menu_cafeteria": {"nombre": "Menú cafetería del día", "cat": "alimentacion", "emoji": "🍽️", "precio": 8.5, "desc": "Plato fuerte + bebida.", "stock": -1},
    "pack_cafe": {"nombre": "Pack café de guardia (x5)", "cat": "alimentacion", "emoji": "☕", "precio": 12.0, "desc": "Cinco cafés máquina personal.", "stock": -1},
}

CATEGORIAS_META = {
    "instrumentos_medicos": {"nombre": "Instrumentos médicos", "emoji": "🩺", "orden": 1},
    "farmacia": {"nombre": "Farmacia y curación", "emoji": "💊", "orden": 2},
    "uniformes": {"nombre": "Uniformes y EPI", "emoji": "🥼", "orden": 3},
    "hospedaje": {"nombre": "Hospedaje", "emoji": "🛏️", "orden": 4},
    "casas": {"nombre": "Casas y residencias", "emoji": "🏡", "orden": 5},
    "combustible": {"nombre": "Combustible y transporte", "emoji": "⛽", "orden": 6},
    "alimentacion": {"nombre": "Alimentación", "emoji": "🍽️", "orden": 7},
}

ITEM_BIENVENIDA = "botiquin_basico"


def _load_inv() -> dict:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_INV_PATH):
        return {}
    try:
        with open(_INV_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_inv(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_INV_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def inv_jugador(uid: int) -> Dict[str, int]:
    data = _load_inv()
    return {k: int(v) for k, v in (data.get(str(uid)) or {}).items()}


def agregar_item(uid: int, item_id: str, cant: int = 1) -> int:
    data = _load_inv()
    key = str(uid)
    bag = data.setdefault(key, {})
    bag[item_id] = int(bag.get(item_id, 0)) + cant
    _save_inv(data)
    return bag[item_id]


def items_por_categoria(cat: str):
    return [(i, d) for i, d in CATALOGO.items() if d.get("cat") == cat]


def comprar(uid: int, item_id: str, cantidad: int = 1):
    if item_id not in CATALOGO:
        return False, "Ítem no existe."
    if cantidad < 1 or cantidad > 20:
        return False, "Cantidad inválida (1–20)."
    info = CATALOGO[item_id]
    total = float(info["precio"]) * cantidad
    stock = info.get("stock", -1)
    if stock == 0:
        return False, "Sin stock."
    if stock > 0 and cantidad > stock:
        return False, f"Solo quedan {stock}."
    try:
        economia.modificar_balance(uid, -total)
    except ValueError:
        bal = economia.obtener_balance(uid)
        return False, f"Fondos insuficientes. Necesitas {MONEDA}{total:.2f} (tienes {MONEDA}{bal:.2f})."
    economia.registrar_movimiento("compra_tienda", uid, 0, total, f"Compra {info['nombre']} x{cantidad}")
    if stock > 0:
        info["stock"] = stock - cantidad
    agregar_item(uid, item_id, cantidad)
    return True, f"Compraste **{info.get('emoji','')} {info['nombre']}** ×{cantidad} por **{MONEDA}{total:.2f}**."


def _load_claims() -> dict:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_CLAIM_PATH):
        return {}
    try:
        with open(_CLAIM_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_claims(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_CLAIM_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def ya_reclamo_bienvenida(uid: int) -> bool:
    return str(uid) in _load_claims()


def marcar_bienvenida(uid: int) -> None:
    data = _load_claims()
    data[str(uid)] = datetime.now(timezone.utc).isoformat()
    _save_claims(data)


def reclamar_bienvenida(uid: int):
    if ya_reclamo_bienvenida(uid):
        return False, "Ya reclamaste el kit de bienvenida."
    item = CATALOGO.get(ITEM_BIENVENIDA)
    if not item:
        return False, "Kit no configurado."
    agregar_item(uid, ITEM_BIENVENIDA, 1)
    marcar_bienvenida(uid)
    return True, f"Recibiste **{item.get('emoji','')} {item['nombre']}** gratis.\n{item.get('desc','')}"
