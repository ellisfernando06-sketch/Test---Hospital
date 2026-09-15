"""
roles_store.py
===============
Guarda en un JSON local (roles_ids.json) los IDs de rol de Discord
que corresponden a cada key y a cada peldaño de cada departamento,
para que no tengas que copiar IDs a mano en config.py. Se llena solo
al ejecutar /configurar_roles. No necesita edición.
"""

import json
import os

ARCHIVO = "roles_ids.json"


def _cargar() -> dict:
    if not os.path.exists(ARCHIVO):
        return {"keys": {}, "departamentos": {}, "extra": {}}
    with open(ARCHIVO, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    data.setdefault("keys", {})
    data.setdefault("departamentos", {})
    data.setdefault("extra", {})
    return data


def _guardar(data: dict):
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# --- Keys generales -------------------------------------------------------
def guardar_id_key(key: str, role_id: int):
    data = _cargar()
    data["keys"][key] = role_id
    _guardar(data)


def obtener_id_key(key: str):
    return _cargar()["keys"].get(key)


def todas_las_keys_configuradas() -> dict:
    return _cargar()["keys"]


# --- Escalafones de departamento -------------------------------------------
def guardar_escalafon_id(slug: str, indice: int, role_id: int):
    data = _cargar()
    lista = data["departamentos"].get(slug, [])
    while len(lista) <= indice:
        lista.append(None)
    lista[indice] = role_id
    data["departamentos"][slug] = lista
    _guardar(data)


def escalafon_ids(slug: str, cantidad: int) -> list:
    data = _cargar()
    lista = list(data["departamentos"].get(slug, []))
    while len(lista) < cantidad:
        lista.append(None)
    return lista[:cantidad]


# --- Roles extra (ej. rol de suspensión) ------------------------------------
def guardar_extra(nombre: str, role_id: int):
    data = _cargar()
    data["extra"][nombre] = role_id
    _guardar(data)


def obtener_extra(nombre: str):
    return _cargar()["extra"].get(nombre)
