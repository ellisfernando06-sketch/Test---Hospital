# -*- coding: utf-8 -*-
"""
quejas.py — Quejas formales.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List

import discord
from discord import ui

import config
from estilos import crear_embed
from solicitudes import enviar_solicitud

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "quejas.json")


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


def pendientes() -> List[dict]:
    data = _load()
    return [q for q in data["lista"] if q.get("estado") == "pendiente"]


def resolver(qid: int) -> bool:
    data = _load()
    for q in data["lista"]:
        if q.get("id") == qid and q.get("estado") == "pendiente":
            q["estado"] = "resuelta"
            q["resuelto"] = datetime.now(timezone.utc).isoformat()
            _save(data)
            return True
    return False


def crear(autor_id: int, departamento: str, contra: str, descripcion: str) -> int:
    data = _load()
    qid = data["next_id"]
    data["next_id"] = qid + 1
    data["lista"].append({
        "id": qid,
        "autor_id": autor_id,
        "departamento": departamento,
        "contra": contra,
        "descripcion": descripcion,
        "estado": "pendiente",
        "fecha": datetime.now(timezone.utc).isoformat(),
    })
    _save(data)
    return qid


class QuejaModal(ui.Modal, title="Queja formal"):
    contra = ui.TextInput(label="Contra quién / qué", max_length=100)
    descripcion = ui.TextInput(label="Descripción de la queja", style=discord.TextStyle.paragraph, max_length=1000)

    def __init__(self, area_slug: str, area_nombre: str):
        super().__init__()
        self.area_slug = area_slug
        self.area_nombre = area_nombre

    async def on_submit(self, interaction: discord.Interaction):
        qid = crear(
            interaction.user.id,
            self.area_nombre,
            str(self.contra),
            str(self.descripcion),
        )
        embed = crear_embed(
            "aviso",
            f"📢 Queja formal #{qid}",
            str(self.descripcion),
            autor=interaction.user,
        )
        embed.add_field(name="Área", value=self.area_nombre)
        embed.add_field(name="Contra", value=str(self.contra))
        embed.add_field(name="Autor", value=interaction.user.mention)
        await enviar_solicitud(interaction, config.RRHH_KEY, embed, "log_quejas")
        await interaction.response.send_message(
            f"✅ Tu queja #{qid} fue enviada a Recursos Humanos.",
            ephemeral=True,
        )
