"""
quejas.py
=========
Quejas formales (modal rellenable), persistente en JSON local
(quejas.json) para poder listar pendientes y resolverlas.

Cualquiera puede presentar una queja con /queja. Igual que las
cartas de solicitud, siempre se envía por DM al encargado de
Recursos Humanos (config.RRHH_KEY) reutilizando el enrutamiento de
solicitudes.py (sube de nivel si no hay nadie asignado todavía, y
si el DM falla queda publicada en config.CANALES["log_quejas"]).
No necesita edición.
"""

import json
import os
from datetime import datetime, timezone

import discord
from discord import ui

import config
from estilos import crear_embed
from solicitudes import enviar_solicitud

ARCHIVO = "quejas.json"


def _cargar() -> list:
    if not os.path.exists(ARCHIVO):
        return []
    with open(ARCHIVO, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _guardar(data: list):
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _registrar(autor_id: int, contra: str, departamento_nombre: str, descripcion: str) -> int:
    data = _cargar()
    queja_id = (data[-1]["id"] + 1) if data else 1
    data.append({
        "id": queja_id, "autor_id": autor_id, "contra": contra,
        "departamento": departamento_nombre, "descripcion": descripcion,
        "estado": "pendiente", "fecha": datetime.now(timezone.utc).isoformat(),
    })
    _guardar(data[-300:])
    return queja_id


def pendientes() -> list:
    return [q for q in _cargar() if q["estado"] == "pendiente"]


def resolver(queja_id: int) -> bool:
    data = _cargar()
    for q in data:
        if q["id"] == queja_id:
            q["estado"] = "resuelta"
            _guardar(data)
            return True
    return False


def total_pendientes() -> int:
    return len(pendientes())


class QuejaModal(ui.Modal, title="Queja Formal"):
    contra = ui.TextInput(
        label="¿Contra quién o qué área es la queja?",
        max_length=150,
        placeholder="Ej: un miembro del personal, un departamento, un procedimiento...",
    )
    descripcion = ui.TextInput(
        label="Describe la queja con detalle",
        style=discord.TextStyle.paragraph,
        max_length=1500,
    )

    def __init__(self, departamento_slug: str, departamento_nombre: str):
        super().__init__()
        self.departamento_slug = departamento_slug
        self.departamento_nombre = departamento_nombre

    async def on_submit(self, interaction: discord.Interaction):
        queja_id = _registrar(
            interaction.user.id, str(self.contra.value), self.departamento_nombre, str(self.descripcion.value)
        )

        embed = crear_embed(
            "aviso", f"📢 Queja Formal #{queja_id}", str(self.descripcion.value), autor=interaction.user
        )
        embed.add_field(name="Contra", value=str(self.contra.value))
        embed.add_field(name="Área relacionada", value=self.departamento_nombre)
        embed.add_field(name="Presentada por", value=interaction.user.mention, inline=False)

        await enviar_solicitud(interaction, config.RRHH_KEY, embed, "log_quejas")
