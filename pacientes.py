"""
pacientes.py
============
Sistema de pacientes, persistente en un JSON local (pacientes.json):
admisión, alta, notas clínicas, cambios de área/cama e historial de
admisiones anteriores por paciente. Alimenta el grupo de comandos
/paciente y el panel de estado general. No necesita edición.
"""

import json
import os
from datetime import datetime, timezone

ARCHIVO = "pacientes.json"


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


def esta_admitido(user_id: int) -> bool:
    data = _cargar()
    ficha = data.get(str(user_id))
    return bool(ficha and ficha.get("admitido"))


def admitir(user_id: int, gravedad: str, motivo: str, autor_id: int, cama: str = "", area: str = ""):
    data = _cargar()
    ficha = data.setdefault(str(user_id), {})
    ficha["admitido"] = True
    ficha["gravedad"] = gravedad
    ficha["motivo"] = motivo
    ficha["cama"] = cama
    ficha["area"] = area
    ficha["fecha_admision"] = _ahora()
    ficha["autor_admision_id"] = autor_id
    ficha.setdefault("notas", [])
    _guardar(data)


def dar_alta(user_id: int, resumen: str, autor_id: int):
    data = _cargar()
    ficha = data.setdefault(str(user_id), {})
    historial = ficha.setdefault("historial", [])
    historial.append({
        "fecha_admision": ficha.get("fecha_admision"),
        "fecha_alta": _ahora(),
        "motivo": ficha.get("motivo", ""),
        "gravedad": ficha.get("gravedad", ""),
        "resumen_alta": resumen,
        "autor_alta_id": autor_id,
    })
    ficha["historial"] = historial[-50:]
    ficha["admitido"] = False
    ficha["cama"] = ""
    ficha["area"] = ""
    _guardar(data)


def agregar_nota(user_id: int, texto: str, autor_id: int):
    data = _cargar()
    ficha = data.setdefault(str(user_id), {})
    notas = ficha.setdefault("notas", [])
    notas.append({"texto": texto, "autor_id": autor_id, "fecha": _ahora()})
    ficha["notas"] = notas[-50:]
    _guardar(data)


def cambiar_gravedad(user_id: int, gravedad: str):
    data = _cargar()
    ficha = data.setdefault(str(user_id), {})
    ficha["gravedad"] = gravedad
    _guardar(data)


def transferir_area(user_id: int, area: str, cama: str = None):
    data = _cargar()
    ficha = data.setdefault(str(user_id), {})
    ficha["area"] = area
    if cama is not None:
        ficha["cama"] = cama
    _guardar(data)


def ficha_de(user_id: int) -> dict:
    return _cargar().get(str(user_id), {})


def admitidos() -> list:
    """Lista de (user_id_int, ficha) de todos los pacientes admitidos ahora."""
    data = _cargar()
    return [(int(uid), f) for uid, f in data.items() if f.get("admitido")]


def total_admitidos() -> int:
    return len(admitidos())
