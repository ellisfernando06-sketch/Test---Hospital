# -*- coding: utf-8 -*
"""logs_store.py — Canales de log + auto-detección por nombre (RRHH)."""
from __future__ import annotations

import json
import os
from typing import Dict, Optional, Tuple

import discord
import config

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "canales_logs.json")

TIPOS_LOG = (
    "log_solicitudes", "log_postulaciones", "log_quejas", "log_sanciones",
    "log_investigaciones", "aprobaciones_rrhh", "aprobaciones", "log_personal",
    "log_general", "staff_disciplina", "log_tickets",
)

NOMBRES_CANAL: Dict[str, Tuple[str, ...]] = {
    "log_solicitudes": (
        "solicitudes-rrhh", "rrhh-solicitudes", "log-solicitudes", "solicitudes",
        "recursos-humanos", "rrhh", "logs-rrhh", "aprobaciones-rrhh",
        "staff-rrhh", "canal-rrhh",
    ),
    "aprobaciones_rrhh": (
        "aprobaciones-rrhh", "rrhh-aprobaciones", "aprobaciones", "rrhh", "recursos-humanos",
    ),
    "log_postulaciones": ("postulaciones", "log-postulaciones", "rrhh-postulaciones", "rrhh"),
    "log_quejas": ("quejas", "log-quejas", "rrhh-quejas", "rrhh"),
    "log_sanciones": ("sanciones", "log-sanciones", "disciplina", "rrhh"),
    "log_investigaciones": ("investigaciones", "log-investigaciones", "disciplina", "rrhh"),
    "log_tickets": ("log-tickets", "tickets-log", "transcripciones", "logs-tickets"),
    "log_general": ("log-general", "logs", "bot-logs", "registros"),
}


def _ensure() -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)


def _load() -> dict:
    _ensure()
    if not os.path.isfile(_PATH):
        return {}
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save(data: dict) -> None:
    _ensure()
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def set_canal(tipo: str, channel_id: int) -> None:
    data = _load()
    data[str(tipo)] = int(channel_id)
    _save(data)
    if isinstance(getattr(config, "CANALES", None), dict):
        config.CANALES[str(tipo)] = int(channel_id)


def get_canal_id(tipo: str) -> Optional[int]:
    data = _load()
    cid = data.get(str(tipo))
    if cid:
        return int(cid)
    canales = getattr(config, "CANALES", None) or {}
    if isinstance(canales, dict):
        v = canales.get(tipo)
        return int(v) if v else None
    return None


def detectar_canal(guild: discord.Guild, tipo: str) -> Optional[discord.TextChannel]:
    """ID guardado → escaneo por nombre. Evita canales 'owner'."""
    cid = get_canal_id(tipo)
    if cid:
        ch = guild.get_channel(int(cid))
        if isinstance(ch, discord.TextChannel):
            return ch

    nombres = NOMBRES_CANAL.get(tipo) or ()
    text_channels = [c for c in guild.text_channels if isinstance(c, discord.TextChannel)]
    for nombre in nombres:
        n = nombre.lower().replace(" ", "-")
        for ch in text_channels:
            cn = (ch.name or "").lower()
            if "owner" in cn and "rrhh" not in cn and "solicitud" not in cn:
                continue
            if n in cn or cn in n:
                return ch

    if tipo in ("log_solicitudes", "aprobaciones_rrhh"):
        for ch in text_channels:
            cn = (ch.name or "").lower()
            if "owner" in cn:
                continue
            if "rrhh" in cn or "recursos" in cn:
                return ch
    return None


def resolver_canal_log(bot, guild: Optional[discord.Guild], tipo: str = "log_solicitudes"):
    if guild is None:
        return None
    ch = detectar_canal(guild, tipo)
    if ch:
        try:
            set_canal(tipo, ch.id)
        except Exception:
            pass
    return ch


def todos() -> Dict[str, int]:
    data = _load()
    out = {k: int(v) for k, v in data.items() if v}
    canales = getattr(config, "CANALES", None) or {}
    if isinstance(canales, dict):
        for k, v in canales.items():
            if v and k not in out:
                out[k] = int(v)
    return out
