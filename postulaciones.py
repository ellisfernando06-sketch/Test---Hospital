# -*- coding: utf-8 -*-
"""
postulaciones.py — Postulaciones al staff.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List, Optional

import discord
from discord import ui

import config
from estilos import crear_embed
from solicitudes import enviar_solicitud

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "postulaciones.json")


def _load() -> dict:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_PATH):
        return {"lista": [], "next_id": 1}
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("lista", [])
        data.setdefault("next_id", 1)
        return data
    except Exception:
        return {"lista": [], "next_id": 1}


def _save(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def tiene_pendiente(uid: int) -> bool:
    data = _load()
    return any(p.get("autor_id") == uid and p.get("estado") == "pendiente" for p in data["lista"])


def pendientes() -> List[dict]:
    data = _load()
    return [p for p in data["lista"] if p.get("estado") == "pendiente"]


def postulaciones_de(uid: int) -> List[dict]:
    data = _load()
    return [p for p in data["lista"] if p.get("autor_id") == uid]


def crear(autor_id: int, departamento_slug: str, motivo: str, experiencia: str) -> int:
    data = _load()
    pid = data["next_id"]
    data["next_id"] = pid + 1
    data["lista"].append({
        "id": pid,
        "autor_id": autor_id,
        "departamento_slug": departamento_slug,
        "motivo": motivo,
        "experiencia": experiencia,
        "estado": "pendiente",
        "fecha": datetime.now(timezone.utc).isoformat(),
    })
    _save(data)
    return pid


def resolver(pid: int, estado: str) -> bool:
    data = _load()
    for p in data["lista"]:
        if p.get("id") == pid:
            p["estado"] = estado
            p["resuelto"] = datetime.now(timezone.utc).isoformat()
            _save(data)
            return True
    return False


class PostulacionModal(ui.Modal, title="Postulación al staff"):
    motivo = ui.TextInput(label="¿Por qué quieres unirte?", style=discord.TextStyle.paragraph, max_length=500)
    experiencia = ui.TextInput(label="Experiencia RP / real", style=discord.TextStyle.paragraph, max_length=500, required=False)

    def __init__(self, departamento_slug: str, departamento_nombre: str):
        super().__init__()
        self.departamento_slug = departamento_slug
        self.departamento_nombre = departamento_nombre

    async def on_submit(self, interaction: discord.Interaction):
        pid = crear(
            interaction.user.id,
            self.departamento_slug,
            str(self.motivo),
            str(self.experiencia) or "",
        )
        embed = crear_embed(
            "info",
            f"📋 Postulación #{pid} — {self.departamento_nombre}",
            f"**Motivo:** {self.motivo}\n\n**Experiencia:** {self.experiencia or '—'}",
            autor=interaction.user,
        )
        embed.add_field(name="Postulante", value=interaction.user.mention)
        # Destino: director del depto o RRHH / Junta
        if self.departamento_slug and self.departamento_slug in config.DEPARTAMENTOS:
            dest_key = config.DEPARTAMENTOS[self.departamento_slug]["director_key"]
        else:
            dest_key = config.KEY_SOLICITUD_GENERAL
        await enviar_solicitud(interaction, dest_key, embed, "log_postulaciones")
        await interaction.response.send_message(
            f"✅ Tu postulación #{pid} a **{self.departamento_nombre}** fue enviada.",
            ephemeral=True,
        )
