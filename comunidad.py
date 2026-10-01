# -*- coding: utf-8 -*-
"""comunidad.py — Reglas por DM/panel; al aceptar se otorga rol **Miembro**."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List, Optional

import discord
from discord import ui, app_commands
from discord.ext import commands

import config
import permisos

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "comunidad_aceptados.json")
_REGLAMENTO_PATH = os.path.join(_DATA_DIR, "reglamento.json")

NOMBRES_ROL_MIEMBRO = (
    "👤 miembro",
    "miembro",
    "✅ miembro",
    "✔️ miembro",
)

REGLAS_DEFAULT = """
# Reglamento del hospital

Bienvenido/a a **{hospital}**.
Al aceptar estas reglas el sistema te asigna el rol de **Miembro**.

## 1. Respeto
- Trata bien a pacientes, personal y staff.
- No acoso, discriminación ni toxicidad.

## 2. Roleplay
- Mantén el personaje y el contexto del hospital.
- En canales de RP no metas OOC sin marcar.
- Metagaming y powergaming están prohibidos.

## 3. Canales
- Cada canal tiene un uso (tickets, RP, off-topic).
- No spam ni flood.

## 4. Staff y tickets
- Se respetan las decisiones de staff y dirección.
- Apelaciones solo por canales o paneles oficiales.

## 5. Economía e ítems
- Dinero e ítems de la tienda son de RP.
- No se cambian por beneficios reales fuera del servidor.

## 6. Sanciones
- El incumplimiento puede derivar en advertencias, mute o expulsión.

Al pulsar **Acepto las reglas** confirmas que las leíste.
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> dict:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_PATH):
        return {"aceptados": {}}
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("aceptados", {})
        return data
    except Exception:
        return {"aceptados": {}}


def _save(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _hospital() -> str:
    return getattr(config, "NOMBRE_HOSPITAL", None) or "Hospital General"


def cargar_reglamento() -> str:
    if os.path.isfile(_REGLAMENTO_PATH):
        try:
            with open(_REGLAMENTO_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and data.get("texto"):
                return str(data["texto"])
            if isinstance(data, str):
                return data
        except Exception:
            pass
    return REGLAS_DEFAULT.format(hospital=_hospital())


def detectar_rol_comunidad(guild: discord.Guild) -> Optional[discord.Role]:
    """Resuelve el rol **Miembro** (al aceptar reglas)."""
    try:
        import roles_acceso

        r = roles_acceso.rol_miembro(guild)
        if r:
            return r
    except Exception:
        pass
    for rol in guild.roles:
        n = (rol.name or "").lower().strip()
        if n in NOMBRES_ROL_MIEMBRO or n == "miembro" or (
            "miembro" in n and "comunidad" not in n
        ):
            if rol.is_default() or rol.managed:
                continue
            return rol
    return None


def embed_reglas(member: Optional[discord.Member] = None) -> discord.Embed:
    hospital = _hospital()
    texto = cargar_reglamento()
    if len(texto) > 3900:
        texto = texto[:3900] + "\n…"
    emb = discord.Embed(
        title=f"📋 Reglamento · {hospital}",
        description=texto,
        color=0x3498DB,
        timestamp=discord.utils.utcnow(),
    )
    emb.set_footer(text=f"{hospital} · Acepta abajo para recibir el rol Miembro")
    return emb


class AceptarReglasView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(
        label="Acepto las reglas",
        style=discord.ButtonStyle.success,
        custom_id="comunidad:acepto",
    )
    async def acepto(self, interaction: discord.Interaction, button: ui.Button):
        guild = interaction.guild
        member = interaction.user if isinstance(interaction.user, discord.Member) else None

        if not guild or not member:
            # DM: buscar en guilds del bot
            bot = interaction.client
            for g in bot.guilds:
                m = g.get_member(interaction.user.id)
                if m:
                    guild = g
                    member = m
                    break
            if not guild or not member:
                return await interaction.response.send_message(
                    embed=discord.Embed(
                        description="Entra al servidor del hospital y vuelve a aceptar.",
                        color=0xE74C3C,
                    ),
                    ephemeral=True,
                )

        rol = detectar_rol_comunidad(guild)
        if not rol:
            try:
                import roles_acceso

                created = await roles_acceso.asegurar_roles_acceso(guild)
                rol = created.get("miembro") or detectar_rol_comunidad(guild)
            except Exception:
                pass
        if not rol:
            return await interaction.response.send_message(
                "❌ No existe el rol **Miembro**. Un admin debe crearlo o usar `/configurar_roles`.",
                ephemeral=True,
            )

        try:
            if rol not in member.roles:
                await member.add_roles(rol, reason="Aceptó las reglas — rol Miembro")
        except discord.Forbidden:
            return await interaction.response.send_message(
                f"Aceptaste las reglas, pero el bot no pudo darte {rol.mention}.\n"
                "Sube el rol del bot por encima de **Miembro**.",
                ephemeral=True,
            )
        except Exception as e:
            return await interaction.response.send_message(
                f"❌ Error al asignar rol: {e}", ephemeral=True
            )

        data = _load()
        data["aceptados"][str(member.id)] = {
            "guild_id": guild.id,
            "at": _now(),
            "role_id": rol.id,
        }
        _save(data)

        await interaction.response.send_message(
            embed=discord.Embed(
                title="✅ Reglas aceptadas",
                description=(
                    f"Se te otorgó **{rol.mention}**.\n\n"
                    f"**Siguiente paso:** completa la **verificación** para obtener **Comunidad**."
                ),
                color=0x2ECC71,
            ),
            ephemeral=True,
        )


class PanelReglasView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(
        label="Recibir reglas en MD",
        style=discord.ButtonStyle.primary,
        custom_id="comunidad:panel_md",
    )
    async def enviar_md(self, inter: discord.Interaction, button: ui.Button):
        try:
            await inter.user.send(embed=embed_reglas(), view=AceptarReglasView())
            await inter.response.send_message(
                "📬 Revisa tus **MD** y pulsa **Acepto las reglas** para obtener el rol **Miembro**.",
                ephemeral=True,
            )
        except discord.Forbidden:
            await inter.response.send_message(
                "❌ No pude enviarte MD. Activa mensajes directos del servidor.",
                ephemeral=True,
            )


def registrar(bot: commands.Bot) -> None:
    for name in ("panel_reglas", "reglas"):
        try:
            bot.tree.remove_command(name)
        except Exception:
            pass

    @bot.tree.command(name="panel_reglas", description="[Staff] Publica el panel de reglamento")
    async def panel_reglas(inter: discord.Interaction):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message("❌ Solo en el servidor.", ephemeral=True)
        if not inter.user.guild_permissions.manage_guild:
            return await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
        emb = discord.Embed(
            title="📋 Reglamento del servidor",
            description=(
                f"Para usar los canales del servidor debes **leer y aceptar** el reglamento.\n\n"
                f"1️⃣ Pulsa **Recibir reglas en MD** o lee el embed\n"
                f"2️⃣ Pulsa **Acepto las reglas** → rol **Miembro**\n"
                f"3️⃣ Completa la **verificación** → rol **Comunidad**"
            ),
            color=0x3498DB,
        )
        await inter.channel.send(embed=emb, view=PanelReglasView())
        await inter.response.send_message("✅ Panel publicado.", ephemeral=True)

    @bot.tree.command(name="reglas", description="Recibe el reglamento por MD")
    async def reglas_cmd(inter: discord.Interaction):
        try:
            await inter.user.send(embed=embed_reglas(), view=AceptarReglasView())
            await inter.response.send_message(
                "📬 Reglamento enviado por MD.", ephemeral=True
            )
        except discord.Forbidden:
            await inter.response.send_message(
                "❌ Activa los MD del servidor.", ephemeral=True
            )

    bot.add_view(AceptarReglasView())
    bot.add_view(PanelReglasView())
    print("[comunidad] OK — aceptar reglas → Miembro")
