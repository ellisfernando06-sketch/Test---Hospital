# -*- coding: utf-8 -*-
"""
postulaciones.py — Postulaciones al staff con sistema de aprobación/negación.
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
from solicitudes import enviar_solicitud_con_aprobacion

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


class PostulacionModal(ui.Modal, title="📋 Postulación al staff del Hospital"):
    motivo = ui.TextInput(
        label="¿Por qué quieres unirte a este departamento?",
        style=discord.TextStyle.paragraph,
        max_length=500,
        placeholder="Explica tu motivación, compromiso y disponibilidad...",
    )
    experiencia = ui.TextInput(
        label="Experiencia RP / real relevante",
        style=discord.TextStyle.paragraph,
        max_length=500,
        required=False,
        placeholder="Describe experiencia previa en roleplay o en el área (opcional)",
    )

    def __init__(self, departamento_slug: str, departamento_nombre: str):
        super().__init__()
        self.departamento_slug = departamento_slug
        self.departamento_nombre = departamento_nombre

    async def on_submit(self, interaction: discord.Interaction):
        if tiene_pendiente(interaction.user.id):
            await interaction.response.send_message(
                "⚠️ Ya tienes una postulación **pendiente**. Espera la resolución antes de enviar otra.",
                ephemeral=True,
            )
            return

        pid = crear(
            interaction.user.id,
            self.departamento_slug,
            str(self.motivo),
            str(self.experiencia) or "",
        )

        descripcion = (
            f"**INSTRUCCIONES PARA EL EVALUADOR**\n"
            f"Revise la motivación y experiencia del postulante. "
            f"Puede consultar el historial del usuario y, si lo considera necesario, "
            f"solicitar una entrevista o prueba adicional antes de decidir.\n\n"
            f"────────────────────────\n"
            f"**Motivo de la postulación:**\n"
            f"> {self.motivo}\n\n"
            f"**Experiencia declarada:**\n"
            f"> {self.experiencia or 'No especificada'}\n\n"
            f"────────────────────────\n"
            f"**Estado:** ⏳ Pendiente de autorización\n"
            f"**Acción requerida:** Aprobar o Negar esta postulación."
        )

        embed = crear_embed(
            "info",
            f"📋 Postulación #{pid} — {self.departamento_nombre}",
            descripcion,
            autor=interaction.user,
        )
        embed.add_field(name="👤 Postulante", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=True)
        embed.add_field(name="🏥 Departamento", value=self.departamento_nombre, inline=True)
        embed.add_field(
            name="📌 Instrucciones",
            value=(
                "• **Aprobar**: el postulante podrá ser contactado para incorporación.\n"
                "• **Negar**: se notificará al postulante con el resultado.\n"
                "• Puede pedir más información respondiendo en el canal de log."
            ),
            inline=False,
        )

        if self.departamento_slug and self.departamento_slug in config.DEPARTAMENTOS:
            dest_key = config.DEPARTAMENTOS[self.departamento_slug]["director_key"]
        else:
            dest_key = config.KEY_SOLICITUD_GENERAL

        async def on_approve(inter: discord.Interaction, info: dict):
            resolver(pid, "aprobada")
            try:
                user = inter.guild.get_member(interaction.user.id) if inter.guild else None
                if user:
                    await user.send(
                        embed=crear_embed(
                            "exito",
                            f"✅ Postulación #{pid} APROBADA",
                            f"Tu postulación a **{self.departamento_nombre}** ha sido **aprobada** por {inter.user.mention}.\n\n"
                            f"El director o staff te contactará próximamente para los siguientes pasos de incorporación. ¡Felicidades!",
                        )
                    )
            except Exception:
                pass

        async def on_deny(inter: discord.Interaction, info: dict):
            resolver(pid, "negada")
            try:
                user = inter.guild.get_member(interaction.user.id) if inter.guild else None
                if user:
                    await user.send(
                        embed=crear_embed(
                            "error",
                            f"❌ Postulación #{pid} NEGADA",
                            f"Tu postulación a **{self.departamento_nombre}** ha sido **negada** por {inter.user.mention}.\n\n"
                            f"Puedes volver a postularte más adelante o consultar con el staff si deseas feedback.",
                        )
                    )
            except Exception:
                pass

        await enviar_solicitud_con_aprobacion(
            interaction,
            key_aprobador=dest_key,
            embed=embed,
            tipo=f"postulacion_{self.departamento_slug}",
            datos={
                "pid": str(pid),
                "postulante": str(interaction.user.id),
                "departamento": self.departamento_nombre,
                "motivo": str(self.motivo),
            },
            canal_key="log_postulaciones",
            on_approve=on_approve,
            on_deny=on_deny,
        )

        await interaction.response.send_message(
            f"✅ Tu postulación **#{pid}** a **{self.departamento_nombre}** fue enviada al director correspondiente.\n"
            f"Recibirás un mensaje cuando sea **aprobada** o **negada**.",
            ephemeral=True,
        )
