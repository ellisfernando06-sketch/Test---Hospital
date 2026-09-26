# -*- coding: utf-8 -*
"""
inventario_rp.py — Posesiones del personaje para RP, por categoría.
Certificados, ítems de tienda, uniformes, accesorios, identificación, licencias…
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "inventario_rp.json")

# Categorías visibles en /mi_equipo (orden de visualización)
CATEGORIAS: Dict[str, dict] = {
    "certificados": {
        "nombre": "📜 Certificados y diplomas",
        "uso_rp": "Acreditan formación completada. Muéstralos en auditorías o promociones.",
    },
    "licencias": {
        "nombre": "📋 Licencias",
        "uso_rp": "Licencia médica u otras habilitaciones oficiales del hospital.",
    },
    "identificacion": {
        "nombre": "🪪 Identificación",
        "uso_rp": "Credenciales e identificaciones para acceso y control.",
    },
    "uniformes": {
        "nombre": "👔 Uniformes y ropa",
        "uso_rp": "Ropa de trabajo / vestimenta del personaje en servicio.",
    },
    "accesorios": {
        "nombre": "💍 Accesorios",
        "uso_rp": "Complementos de apariencia o utilidad menor.",
    },
    "instrumentos_medicos": {
        "nombre": "🩺 Instrumentos médicos",
        "uso_rp": "Equipo clínico que puedes usar en procedimientos RP.",
    },
    "farmacia": {
        "nombre": "💊 Farmacia y curación",
        "uso_rp": "Insumos de curación y farmacia para atención RP.",
    },
    "tecnologia": {
        "nombre": "💻 Tecnología",
        "uso_rp": "Dispositivos y equipo electrónico del personaje.",
    },
    "documentos": {
        "nombre": "📄 Documentos",
        "uso_rp": "Papeles administrativos u otros documentos RP.",
    },
    "otros": {
        "nombre": "📦 Otros",
        "uso_rp": "Posesiones diversas no clasificadas arriba.",
    },
}

# Mapeo catálogo tienda → categoría RP
_MAP_TIENDA = {
    "instrumentos_medicos": "instrumentos_medicos",
    "farmacia": "farmacia",
    "uniformes": "uniformes",
    "tecnologia": "tecnologia",
    "alimentacion": "otros",
    "bienestar": "otros",
    "hospedaje": "otros",
    "casas": "otros",
    "combustible": "otros",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> dict:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_PATH):
        return {}
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _bag(data: dict, uid: int) -> dict:
    k = str(uid)
    if k not in data:
        data[k] = {"items": []}
    data[k].setdefault("items", [])
    return data[k]


def otorgar(
    uid: int,
    *,
    categoria: str,
    nombre: str,
    cantidad: int = 1,
    origen: str = "sistema",
    descripcion: str = "",
    meta: Optional[dict] = None,
    emoji: str = "",
    item_id: str = "",
) -> dict:
    """Añade o acumula un ítem en el inventario RP del usuario."""
    cat = categoria if categoria in CATEGORIAS else "otros"
    data = _load()
    bag = _bag(data, uid)
    nombre = (nombre or "Ítem").strip()[:120]
    cantidad = max(1, int(cantidad))

    # Acumular si mismo item_id o mismo nombre+categoría (no certificados únicos)
    if cat != "certificados" and item_id:
        for it in bag["items"]:
            if it.get("item_id") == item_id and it.get("categoria") == cat:
                it["cantidad"] = int(it.get("cantidad", 1)) + cantidad
                it["ultima"] = _now()
                _save(data)
                return it

    entry = {
        "id": f"{uid}_{int(datetime.now(timezone.utc).timestamp()*1000)}",
        "categoria": cat,
        "nombre": nombre,
        "emoji": emoji or CATEGORIAS[cat]["nombre"].split()[0],
        "cantidad": cantidad,
        "origen": origen,
        "descripcion": (descripcion or "")[:300],
        "meta": meta or {},
        "item_id": item_id or "",
        "fecha": _now(),
        "ultima": _now(),
    }
    bag["items"].append(entry)
    _save(data)
    return entry


def otorgar_certificado(
    uid: int,
    *,
    nombre: str,
    numero: str = "",
    cedula: str = "",
    departamento: str = "",
    emisor: str = "",
) -> dict:
    return otorgar(
        uid,
        categoria="certificados",
        nombre=nombre,
        cantidad=1,
        origen="certificar",
        emoji="🎓",
        descripcion=f"Folio {numero}" + (f" · CI {cedula}" if cedula else ""),
        meta={
            "numero": numero,
            "cedula": cedula,
            "departamento": departamento,
            "emisor": emisor,
        },
        item_id=f"cert_{numero}" if numero else "",
    )


def otorgar_desde_tienda(uid: int, item_id: str, info: dict, cantidad: int = 1) -> dict:
    cat_tienda = info.get("cat") or "otros"
    cat = _MAP_TIENDA.get(cat_tienda, "otros")
    # Heurística por nombre
    n = (info.get("nombre") or item_id).lower()
    if any(x in n for x in ("uniforme", "bata", "casaca", "pantal", "zapat", "gorro")):
        cat = "uniformes"
    elif any(x in n for x in ("credencial", "carnet", "identific", "placa")):
        cat = "identificacion"
    elif any(x in n for x in ("licencia", "habilit")):
        cat = "licencias"
    elif any(x in n for x in ("anillo", "reloj", "collar", "lentes", "gafa")):
        cat = "accesorios"

    return otorgar(
        uid,
        categoria=cat,
        nombre=info.get("nombre") or item_id,
        cantidad=cantidad,
        origen="tienda",
        emoji=info.get("emoji") or "📦",
        descripcion=info.get("desc") or "",
        item_id=item_id,
        meta={"precio": info.get("precio"), "cat_tienda": cat_tienda},
    )


def listar(uid: int, categoria: Optional[str] = None) -> List[dict]:
    data = _load()
    bag = _bag(data, uid)
    items = bag.get("items") or []
    if categoria:
        return [i for i in items if i.get("categoria") == categoria]
    return list(items)


def por_categoria(uid: int) -> Dict[str, List[dict]]:
    out: Dict[str, List[dict]] = {k: [] for k in CATEGORIAS}
    for it in listar(uid):
        cat = it.get("categoria") if it.get("categoria") in CATEGORIAS else "otros"
        out[cat].append(it)
    return out


def resumen_texto(uid: int) -> str:
    grupos = por_categoria(uid)
    partes = []
    for cat, info in CATEGORIAS.items():
        items = grupos.get(cat) or []
        if not items:
            continue
        lineas = [f"**{info['nombre']}**"]
        lineas.append(f"_{info['uso_rp']}_")
        for it in items[:15]:
            em = it.get("emoji") or "•"
            cant = int(it.get("cantidad") or 1)
            extra = f" ×{cant}" if cant > 1 else ""
            desc = f" — {it['descripcion']}" if it.get("descripcion") else ""
            lineas.append(f"{em} **{it.get('nombre')}**{extra}{desc}")
        if len(items) > 15:
            lineas.append(f"… y {len(items) - 15} más")
        partes.append("\n".join(lineas))
    return "\n\n".join(partes) if partes else "No tienes posesiones registradas aún."
