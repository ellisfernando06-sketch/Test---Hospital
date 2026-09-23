# -*- coding: utf-8 -*
"""postulaciones.py — Postulaciones con aprobación y rol inicial."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List, Optional

import discord
from discord import ui

import config
from estilos import crear_embed

try:
    from solicitudes import enviar_solicitud_con_aprobacion
except Exception:
    enviar_solicitud_con_aprobacion = None

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "postulaciones.json")


def _load() -> dict:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_PATH):
        return {"seq": 0, "items": []}
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("seq", 0)
        data.setdefault("items", [])
        return data
    except Exception:
        return {"seq": 0, "items": []}


def _save(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def tiene_pendiente(uid: int) -> bool:
    data = _load()
    return any(i.get("autor_id") == uid and i.get("estado") == "pendiente" for i in data.get("items", []))


def pendientes() -> List[dict]:
    return [i for i in _load().get("items", []) if i.get("estado") == "pendiente"]


def postulaciones_de(uid: int) -> List[dict]:
    return [i for i in _load().get("items", []) if i.get("autor_id") == uid]


def crear(autor_id: int, departamento_slug: str, motivo: str, experiencia: str) -> int:
    data = _load()
    data["seq"] = int(data.get("seq") or 0) + 1
    pid = data["seq"]
    data.setdefault("items", []).append({
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
    for i in data.get("items", []):
        if int(i.get("id") or 0) == int(pid):
            i["estado"] = estado
            _save(data)
            return True
    return False


def _rol_inicial(guild: discord.Guild, slug: str):
    dep = (getattr(config, "DEPARTAMENTOS", None) or {}).get(slug) or {}
    nombres = dep.get("escalafon_nombres") or []
    if not nombres or not guild:
        return None, dep
    target = nombres[0]
    for r in guild.roles:
        if r.name == target:
            return r, dep
    import re
    def _norm(s):
        return re.sub(r"[^a-z0-9áéíóúñ ]", "", (s or "").lower()).strip()
    tn = _norm(target)
    for r in guild.roles:
        if tn and tn in _norm(r.name):
            return r, dep
    return None, dep


def _ping_director(guild: discord.Guild, slug: str) -> str:
    dep = (getattr(config, "DEPARTAMENTOS", None) or {}).get(slug) or {}
    dkey = dep.get("director_key")
    if not dkey or not guild:
        return ""
    try:
        import roles_store
        rid = roles_store.obtener_id_key(dkey)
        if rid:
            r = guild.get_role(int(rid))
            if r:
                return r.mention
    except Exception:
        pass
    return ""


class PostulacionModal(ui.Modal, title="📋 Postulación al staff del Hospital"):
    motivo = ui.TextInput(
        label="¿Por qué quieres unirte a este departamento?",
        style=discord.TextStyle.paragraph,
        max_length=800,
    )
    experiencia = ui.TextInput(
        label="Experiencia",
        style=discord.TextStyle.paragraph,
        max_length=800,
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
            str(self.experiencia) if self.experiencia.value else "—",
        )

        embed = discord.Embed(
            title=f"📋 Postulación #{pid} — {self.departamento_nombre}",
            description=(
                f"Revise la motivación y experiencia del postulante.\n\n"
                f"**Motivo de la postulación:**\n{self.motivo}\n\n"
                f"**Experiencia:**\n{self.experiencia.value or '—'}\n\n"
                f"**Acción requerida:** Aprobar o Negar esta postulación."
            ),
            color=0x3498DB,
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="👤 Postulante", value=interaction.user.mention, inline=True)
        embed.add_field(name="🏥 Departamento", value=self.departamento_nombre, inline=True)
        embed.add_field(
            name="📌 Notas",
            value=(
                "• **Aprobar**: asigna el **rol inicial** del departamento y notifica al director.\n"
                "• **Negar**: se notificará al postulante.\n"
            ),
            inline=False,
        )

        if self.departamento_slug and self.departamento_slug in config.DEPARTAMENTOS:
            dest_key = config.DEPARTAMENTOS[self.departamento_slug]["director_key"]
        else:
            dest_key = getattr(config, "KEY_SOLICITUD_GENERAL", "DIRECTOR_RRHH")

        async def on_approve(inter: discord.Interaction, info: dict):
            resolver(pid, "aprobada")
            guild = inter.guild
            user = guild.get_member(interaction.user.id) if guild else None
            rol_dado, dep = _rol_inicial(guild, self.departamento_slug) if guild else (None, {})
            director_ping = _ping_director(guild, self.departamento_slug) if guild else ""
            try:
                if user and rol_dado:
                    await user.add_roles(rol_dado, reason=f"Postulación #{pid} aprobada")
            except Exception as e:
                print("[postulaciones] add_roles:", e)
            try:
                if user:
                    extra = (
                        f"\nRol asignado: **{rol_dado.name}**."
                        if rol_dado
                        else "\n_(Rol inicial no encontrado; asígnalo manualmente.)_"
                    )
                    await user.send(
                        embed=crear_embed(
                            "exito",
                            f"✅ Postulación #{pid} APROBADA",
                            f"Tu postulación a **{self.departamento_nombre}** fue **aprobada** por {inter.user.mention}.{extra}",
                        )
                    )
            except Exception:
                pass
            try:
                if inter.channel:
                    parts = []
                    if director_ping:
                        parts.append(director_ping)
                    parts.append(f"✅ Postulación **#{pid}** · **{self.departamento_nombre}**")
                    if user:
                        parts.append(user.mention)
                    if rol_dado:
                        parts.append(f"rol {rol_dado.mention}")
                    await inter.channel.send(" · ".join(parts))
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
                            f"Tu postulación a **{self.departamento_nombre}** ha sido **negada** por {inter.user.mention}.",
                        )
                    )
            except Exception:
                pass

        if enviar_solicitud_con_aprobacion is None:
            await interaction.response.send_message(
                "Sistema de aprobación no disponible.", ephemeral=True
            )
            return

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
