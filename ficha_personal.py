"""
ficha_personal.py
==================
Ficha de personal editable, persistente en JSON local
(ficha_personal.json): datos administrativos de cada miembro del
personal que no cambian con cada turno (especialidad, licencia,
contacto RP, notas). Es un complemento de registros.py: aquí vive la
FICHA (estado actual, editable), en registros.py vive el HISTORIAL
(eventos con fecha). Alimenta el grupo de comandos /ficha. No
necesita edición.
"""

import json
import os

ARCHIVO = "ficha_personal.json"


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


def set_campo(user_id: int, campo: str, valor: str):
    data = _cargar()
    ficha = data.setdefault(str(user_id), {})
    ficha[campo] = valor
    _guardar(data)


def obtener(user_id: int) -> dict:
    return _cargar().get(str(user_id), {})
