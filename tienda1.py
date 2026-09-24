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
    # ── Instrumentos médicos ──
    "estetoscopio": {"nombre": "Estetoscopio clínico", "cat": "instrumentos_medicos", "emoji": "🩺", "precio": 185.0, "desc": "Doble campana, acero inoxidable.", "stock": 40},
    "tensiometro": {"nombre": "Tensiómetro aneroide", "cat": "instrumentos_medicos", "emoji": "💉", "precio": 95.0, "desc": "Esfigmomanómetro adulto/pediátrico.", "stock": 50},
    "oximetro": {"nombre": "Oxímetro de pulso", "cat": "instrumentos_medicos", "emoji": "📟", "precio": 65.0, "desc": "SpO2 y frecuencia cardíaca.", "stock": 80},
    "otoscopio": {"nombre": "Otoscopio LED", "cat": "instrumentos_medicos", "emoji": "🔦", "precio": 120.0, "desc": "Examen de oído + 10 espéculos.", "stock": 30},
    "glucometro": {"nombre": "Glucómetro + 25 tiras", "cat": "instrumentos_medicos", "emoji": "🩸", "precio": 48.0, "desc": "Glucosa capilar + lancetas.", "stock": 60},
    "termometro_ir": {"nombre": "Termómetro infrarrojo", "cat": "instrumentos_medicos", "emoji": "🌡️", "precio": 42.0, "desc": "Sin contacto, 1 s.", "stock": 70},
    "desfibrilador": {"nombre": "DEA / Desfibrilador portátil", "cat": "instrumentos_medicos", "emoji": "⚡", "precio": 450.0, "desc": "Desfibrilador externo automático.", "stock": 12},
    "monitor_vital": {"nombre": "Monitor multiparamétrico", "cat": "instrumentos_medicos", "emoji": "📊", "precio": 680.0, "desc": "ECG, SpO2, presión, temperatura.", "stock": 8},
    "linterna_clinica": {"nombre": "Linterna clínica LED", "cat": "instrumentos_medicos", "emoji": "💡", "precio": 25.0, "desc": "Examen pupilar y cavidad oral.", "stock": 90},
    "martillo_reflejos": {"nombre": "Martillo de reflejos", "cat": "instrumentos_medicos", "emoji": "🔨", "precio": 22.0, "desc": "Neurológico, punta de goma.", "stock": 55},

    # ── Farmacia y curación ──
    "botiquin_basico": {"nombre": "Botiquín básico", "cat": "farmacia", "emoji": "🧰", "precio": 35.0, "desc": "Gasas, vendas, alcohol, apósitos, guantes.", "stock": 100},
    "kit_sutura": {"nombre": "Kit de sutura desechable", "cat": "farmacia", "emoji": "🪡", "precio": 28.0, "desc": "Porta-agujas, pinza, hilo, gasas.", "stock": 45},
    "mascarillas_n95": {"nombre": "Caja mascarillas N95 (20)", "cat": "farmacia", "emoji": "😷", "precio": 55.0, "desc": "Protección respiratoria.", "stock": 90},
    "guantes_nitrilo": {"nombre": "Caja guantes nitrilo (100)", "cat": "farmacia", "emoji": "🧤", "precio": 18.0, "desc": "Talla M, sin polvo.", "stock": 120},
    "botiquin_trauma": {"nombre": "Botiquín de trauma avanzado", "cat": "farmacia", "emoji": "🩹", "precio": 95.0, "desc": "Torniquetes, apósitos hemostáticos, férulas.", "stock": 35},
    "kit_rcp": {"nombre": "Kit RCP / BLS", "cat": "farmacia", "emoji": "❤️", "precio": 60.0, "desc": "Mascarilla de reanimación + bolsa.", "stock": 40},
    "suero_fisiologico": {"nombre": "Suero fisiológico 500 ml (pack 6)", "cat": "farmacia", "emoji": "💧", "precio": 24.0, "desc": "Solución NaCl 0.9%.", "stock": 80},
    "analgesicos": {"nombre": "Pack analgésicos básicos", "cat": "farmacia", "emoji": "💊", "precio": 15.0, "desc": "Paracetamol, ibuprofeno (RP).", "stock": 150},
    "antiseptico": {"nombre": "Antiséptico quirúrgico 500 ml", "cat": "farmacia", "emoji": "🧴", "precio": 18.0, "desc": "Clorhexidina / alcohol isopropílico.", "stock": 70},

    # ── Uniformes y EPI ──
    "uniforme_medico": {"nombre": "Uniforme médico completo", "cat": "uniformes", "emoji": "🥼", "precio": 75.0, "desc": "Filipina + pantalón + cofia.", "stock": 50},
    "bata_blanca": {"nombre": "Bata blanca profesional", "cat": "uniformes", "emoji": "👔", "precio": 55.0, "desc": "Algodón, bolsillos laterales.", "stock": 40},
    "uniforme_enfermeria": {"nombre": "Uniforme de enfermería", "cat": "uniformes", "emoji": "💉", "precio": 70.0, "desc": "Filipina color + pantalón.", "stock": 45},
    "zapatos_clinicos": {"nombre": "Zapatos clínicos antideslizantes", "cat": "uniformes", "emoji": "👟", "precio": 65.0, "desc": "Cómodos para turnos largos.", "stock": 35},
    "gafas_proteccion": {"nombre": "Gafas de protección", "cat": "uniformes", "emoji": "🥽", "precio": 20.0, "desc": "Antisalpicaduras, transparentes.", "stock": 80},
    "bata_quirurgica": {"nombre": "Bata quirúrgica estéril", "cat": "uniformes", "emoji": "🥼", "precio": 38.0, "desc": "Uso en quirófano (desechable).", "stock": 60},
    "gorro_quirurgico": {"nombre": "Pack gorros quirúrgicos (10)", "cat": "uniformes", "emoji": "🧢", "precio": 12.0, "desc": "Desechables, varios colores.", "stock": 100},

    # ── Hospedaje ──
    "noche_residencia": {"nombre": "Noche en residencia del personal", "cat": "hospedaje", "emoji": "🛏️", "precio": 40.0, "desc": "Habitación individual, baño compartido.", "stock": -1},
    "semana_residencia": {"nombre": "Semana en residencia del personal", "cat": "hospedaje", "emoji": "🏠", "precio": 220.0, "desc": "7 noches + cocina común.", "stock": -1},
    "suite_guardia": {"nombre": "Suite de guardia (24 h)", "cat": "hospedaje", "emoji": "🏨", "precio": 85.0, "desc": "Cama, escritorio, ducha privada.", "stock": -1},
    "noche_vip": {"nombre": "Noche suite VIP personal", "cat": "hospedaje", "emoji": "✨", "precio": 120.0, "desc": "Habitación premium + desayuno.", "stock": -1},

    # ── Casas y residencias ──
    "depto_studio": {"nombre": "Depto studio (alquiler mensual)", "cat": "casas", "emoji": "🏢", "precio": 650.0, "desc": "Cerca del hospital, 1 ambiente.", "stock": 8},
    "casa_2hab": {"nombre": "Casa 2 habitaciones (mensual)", "cat": "casas", "emoji": "🏡", "precio": 980.0, "desc": "Zona residencial, patio, 2 baños.", "stock": 4},
    "habitacion_compartida": {"nombre": "Habitación compartida (mensual)", "cat": "casas", "emoji": "🚪", "precio": 280.0, "desc": "Para personal en formación.", "stock": 15},
    "depto_1hab": {"nombre": "Depto 1 habitación (mensual)", "cat": "casas", "emoji": "🏬", "precio": 780.0, "desc": "Amoblado, cerca del hospital.", "stock": 6},
    "casa_familiar": {"nombre": "Casa familiar 3 hab (mensual)", "cat": "casas", "emoji": "🏘️", "precio": 1350.0, "desc": "Ideal familias del staff.", "stock": 2},

    # ── Combustible y transporte ──
    "gasolina_20l": {"nombre": "Gasolina 20 litros", "cat": "combustible", "emoji": "⛽", "precio": 32.0, "desc": "Combustible regular estación hospital.", "stock": -1},
    "gasolina_40l": {"nombre": "Gasolina 40 litros", "cat": "combustible", "emoji": "⛽", "precio": 60.0, "desc": "Descuento institucional.", "stock": -1},
    "tarjeta_transporte": {"nombre": "Tarjeta transporte urbano (mes)", "cat": "combustible", "emoji": "🚌", "precio": 45.0, "desc": "Rutas ciudad–hospital.", "stock": -1},
    "carga_electrica": {"nombre": "Carga vehículo eléctrico (full)", "cat": "combustible", "emoji": "🔌", "precio": 22.0, "desc": "Punto de carga del hospital.", "stock": -1},
    "taxi_hospital": {"nombre": "Voucher taxi hospital (ida)", "cat": "combustible", "emoji": "🚕", "precio": 18.0, "desc": "Traslado urgente o turno noche.", "stock": -1},
    "parking_mes": {"nombre": "Parking hospital (mensual)", "cat": "combustible", "emoji": "🅿️", "precio": 55.0, "desc": "Estacionamiento personal.", "stock": -1},

    # ── Alimentación ──
    "menu_cafeteria": {"nombre": "Menú cafetería del día", "cat": "alimentacion", "emoji": "🍽️", "precio": 8.5, "desc": "Plato fuerte + bebida.", "stock": -1},
    "pack_cafe": {"nombre": "Pack café de guardia (x5)", "cat": "alimentacion", "emoji": "☕", "precio": 12.0, "desc": "Cinco cafés máquina personal.", "stock": -1},
    "almuerzo_ejecutivo": {"nombre": "Almuerzo ejecutivo staff", "cat": "alimentacion", "emoji": "🥗", "precio": 14.0, "desc": "Menú premium + postre.", "stock": -1},
    "pack_snacks": {"nombre": "Pack snacks de turno", "cat": "alimentacion", "emoji": "🍫", "precio": 9.0, "desc": "Barras energéticas + agua.", "stock": -1},
    "cena_guardia": {"nombre": "Cena de guardia nocturna", "cat": "alimentacion", "emoji": "🌙", "precio": 11.0, "desc": "Comida caliente para turnos largos.", "stock": -1},
    "bebida_energetica": {"nombre": "Pack bebidas energéticas (x6)", "cat": "alimentacion", "emoji": "⚡", "precio": 16.0, "desc": "Para turnos intensos.", "stock": -1},

    # ── Tecnología y oficina ──
    "tablet_clinica": {"nombre": "Tablet clínica básica", "cat": "tecnologia", "emoji": "📱", "precio": 220.0, "desc": "Para HC y órdenes médicas.", "stock": 15},
    "laptop_staff": {"nombre": "Laptop staff hospital", "cat": "tecnologia", "emoji": "💻", "precio": 480.0, "desc": "Portátil institucional.", "stock": 8},
    "auriculares": {"nombre": "Auriculares con micrófono", "cat": "tecnologia", "emoji": "🎧", "precio": 35.0, "desc": "Reuniones y llamadas.", "stock": 40},
    "powerbank": {"nombre": "Power bank 20.000 mAh", "cat": "tecnologia", "emoji": "🔋", "precio": 28.0, "desc": "Carga rápida USB-C.", "stock": 50},
    "kit_oficina": {"nombre": "Kit oficina básica", "cat": "tecnologia", "emoji": "📎", "precio": 15.0, "desc": "Bolígrafos, libretas, clips.", "stock": 80},

    # ── Bienestar y extras RP ──
    "gimnasio_mes": {"nombre": "Membresía gimnasio hospital (mes)", "cat": "bienestar", "emoji": "🏋️", "precio": 40.0, "desc": "Sala de ejercicio del personal.", "stock": -1},
    "masaje_relajante": {"nombre": "Sesión masaje relajante", "cat": "bienestar", "emoji": "💆", "precio": 35.0, "desc": "30 min post-turno.", "stock": -1},
    "curso_rcp": {"nombre": "Curso RCP certificado (RP)", "cat": "bienestar", "emoji": "📜", "precio": 50.0, "desc": "Capacitación básica BLS.", "stock": -1},
    "kit_descanso": {"nombre": "Kit descanso de guardia", "cat": "bienestar", "emoji": "😴", "precio": 22.0, "desc": "Antifaz, tapones, manta ligera.", "stock": 40},
}

CATEGORIAS_META = {
    "instrumentos_medicos": {"nombre": "Instrumentos médicos", "emoji": "🩺", "orden": 1},
    "farmacia": {"nombre": "Farmacia y curación", "emoji": "💊", "orden": 2},
    "uniformes": {"nombre": "Uniformes y EPI", "emoji": "🥼", "orden": 3},
    "hospedaje": {"nombre": "Hospedaje", "emoji": "🛏️", "orden": 4},
    "casas": {"nombre": "Casas y residencias", "emoji": "🏡", "orden": 5},
    "combustible": {"nombre": "Combustible y transporte", "emoji": "⛽", "orden": 6},
    "alimentacion": {"nombre": "Alimentación", "emoji": "🍽️", "orden": 7},
    "tecnologia": {"nombre": "Tecnología y oficina", "emoji": "💻", "orden": 8},
    "bienestar": {"nombre": "Bienestar y extras", "emoji": "✨", "orden": 9},
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
