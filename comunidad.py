# -*- coding: utf-8 -*-
"""comunidad.py — Reglas por DM, confirmación y rol de comunidad (estilo sistema)."""
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

NOMBRES_ROL_COMUNIDAD = (
    "comunidad", "miembro de la comunidad", "miembro", "ciudadano",
    "verificado", "civil", "civilian", "habitante", "residente civil",
    "✅ verificado", "✔️ miembro",
)

REGLAS_DEFAULT = """
# Reglamento del hospital

Bienvenido/a a **{hospital}**.
Al aceptar estas reglas el sistema te asigna el rol de **comunidad**.

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
- Incumplir puede traer warn, mute, kick o ban según la gravedad.

---
Al pulsar **Acepto las reglas** confirmas que las leíste.
El sistema intentará darte el rol de comunidad.
""".strip()

_MAX_DESC = 3900


def _hospital() -> str:
    return getattr(config, "NOMBRE_HOSPITAL", None) or "Hospital General"


def _split_text(text: str, max_len: int = _MAX_DESC) -> List[str]:
    text = (text or "").strip()
    if not text:
        return [""]
    if len(text) <= max_len:
        return [text]
    chunks: List[str] = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        cut = text.rfind("\n", 0, max_len)
        if cut < max_len // 3:
            cut = max_len
        chunks.append(text[:cut].rstrip())
        text = text[cut:].lstrip("\n")
    return chunks


def _load() -> dict:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_PATH):
        return {}
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load_reglamento_text() -> str:
    hospital = _hospital()
    if os.path.isfile(_REGLAMENTO_PATH):
        try:
            with open(_REGLAMENTO_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            texto = (data.get("texto") or data.get("contenido") or "").strip()
            if texto:
                return texto.replace("{hospital}", hospital)
        except Exception:
            pass
    return REGLAS_DEFAULT.format(hospital=hospital)


def detectar_rol_comunidad(guild: discord.Guild) -> Optional[discord.Role]:
    for rol in guild.roles:
        n = (rol.name or "").lower().strip()
        if n in NOMBRES_ROL_COMUNIDAD or any(x in n for x in ("comunidad", "miembro", "verificado")):
            if rol.is_default() or rol.managed:
                continue
            return rol
    return None


def embed_reglas_chunk(texto: str, pagina: int, total: int) -> discord.Embed:
    hospital = _hospital()
    titulo = "📜  Reglamento del sistema"
    if total > 1:
        titulo += f"  ·  {pagina}/{total}"
    emb = discord.Embed(
        title=titulo,
        description=(
            f"```\n"
            f" HOSPITAL  ·  {hospital.upper()}\n"
            f" MÓDULO    ·  REGLAS DE COMUNIDAD\n"
            f"```\n\n"
            f"{texto}"
        ),
        color=0x2E86DE,
        timestamp=discord.utils.utcnow(),
    )
    emb.set_footer(text=f"🖥️  {hospital}  ·  Sistema de gestión  │  Acepta abajo para continuar")
    return emb


class AceptarReglasView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Acepto las reglas", style=discord.ButtonStyle.success, custom_id="comunidad:acepto")
    async def acepto(self, interaction: discord.Interaction, button: ui.Button):
        if not isinstance(interaction.user, discord.Member):
            # DM: buscar miembro en guilds del bot
            member = None
            for g in interaction.client.guilds:
                m = g.get_member(interaction.user.id)
                if m:
                    member = m
                    break
            if not member:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="❌  No se encontró el servidor",
                        description="Entra al servidor del hospital y vuelve a aceptar.",
                        color=0xFF4757,
                    ),
                    ephemeral=True,
                )
                return
        else:
            member = interaction.user

        guild = member.guild
        rol = detectar_rol_comunidad(guild)
        data = _load()
        data[str(member.id)] = {
            "at": datetime.now(timezone.utc).isoformat(),
            "guild_id": guild.id,
        }
        _save(data)

        if rol and rol not in member.roles:
            try:
                await member.add_roles(rol, reason="Aceptó reglamento de comunidad")
            except discord.Forbidden:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="⚠️  Rol no asignado",
                        description=(
                            f"Aceptaste las reglas, pero el bot no pudo darte {rol.mention}.\n"
                            f"Pide a un admin que suba el rol del bot o te asigne el rol a mano."
                        ),
                        color=0xFFA502,
                    ),
                    ephemeral=True,
                )
                return
            except Exception as e:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="❌  Error",
                        description=f"No se pudo asignar el rol: `{e}`",
                        color=0xFF4757,
                    ),
                    ephemeral=True,
                )
                return

        emb = discord.Embed(
            title="✅  Acceso de comunidad activado",
            description=(
                f"```\n"
                f" HOSPITAL  ·  {_hospital().upper()}\n"
                f" MÓDULO    ·  COMUNIDAD\n"
                f"```\n\n"
                f"**Estado:** reglas aceptadas\n\n"
                f"Ya formas parte de la comunidad del hospital.\n"
                + (f"Rol asignado: {rol.mention}\n" if rol else "")
                + f"\nPuedes explorar los canales públicos.\n"
                f"Si quieres unirte al personal, mira **postulaciones**."
            ),
            color=0x00D2A0,
            timestamp=discord.utils.utcnow(),
        )
        emb.set_footer(text=f"🖥️  {_hospital()}  ·  Sistema de gestión")
        await interaction.response.send_message(embed=emb, ephemeral=True)


async def enviar_reglas_dm(user: discord.abc.User) -> tuple:
    texto = _load_reglamento_text()
    chunks = _split_text(texto)
    view = AceptarReglasView()
    try:
        for i, chunk in enumerate(chunks, start=1):
            emb = embed_reglas_chunk(chunk, i, len(chunks))
            if i == len(chunks):
                await user.send(embed=emb, view=view)
            else:
                await user.send(embed=emb)
        return True, None
    except discord.Forbidden:
        return False, "No pude enviarte MD. Abre mensajes directos del servidor e inténtalo otra vez."
    except Exception as e:
        return False, str(e)


class PanelReglasView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Recibir reglas en MD", style=discord.ButtonStyle.primary, custom_id="comunidad:panel_md")
    async def enviar_md(self, inter: discord.Interaction, button: ui.Button):
        await inter.response.defer(ephemeral=True)
        ok, err = await enviar_reglas_dm(inter.user)
        if ok:
            await inter.followup.send(
                embed=discord.Embed(
                    title="📬  Reglamento enviado",
                    description=(
                        "**Estado:** enviado a tus mensajes directos\n\n"
                        "Abre el MD del bot y pulsa **Acepto las reglas** para activar el acceso de comunidad."
                    ),
                    color=0x2E86DE,
                ),
                ephemeral=True,
            )
        else:
            await inter.followup.send(
                embed=discord.Embed(
                    title="❌  No se pudo enviar",
                    description=f"**Estado:** error\n\n{err}",
                    color=0xFF4757,
                ),
                ephemeral=True,
            )


def embed_reglas_panel() -> discord.Embed:
    hospital = _hospital()
    return discord.Embed(
        title="🖥️  Panel de acceso — Reglamento",
        description=(
            f"```\n"
            f" HOSPITAL  ·  {hospital.upper()}\n"
            f" MÓDULO    ·  REGLAS DE COMUNIDAD\n"
            f"```\n\n"
            f"**Estado del acceso**\n"
            f"Para usar los canales de comunidad debes **leer y aceptar** el reglamento.\n\n"
            f"**Pasos**\n"
            f"1️⃣ Pulsa **Recibir reglas en MD**\n"
            f"2️⃣ Abre el mensaje directo del bot\n"
            f"3️⃣ Pulsa **Acepto las reglas**\n\n"
            f"También puedes usar el comando **`/reglas`**.\n\n"
            f"*El sistema asignará el rol de comunidad automáticamente si está configurado.*"
        ),
        color=0x2E86DE,
        timestamp=discord.utils.utcnow(),
    ).set_footer(text=f"🖥️  {hospital}  ·  Sistema de gestión  │  Panel de reglas")


def registrar(bot: commands.Bot) -> None:
    @bot.tree.command(name="reglas", description="Recibe el reglamento por mensaje directo")
    async def reglas_cmd(inter: discord.Interaction):
        if not isinstance(inter.user, discord.Member):
            await inter.response.send_message(
                embed=discord.Embed(
                    title="❌  Solo en el servidor",
                    description="Usa este comando dentro del servidor del hospital.",
                    color=0xFF4757,
                ),
                ephemeral=True,
            )
            return
        await inter.response.defer(ephemeral=True)
        ok, err = await enviar_reglas_dm(inter.user)
        if ok:
            await inter.followup.send(
                embed=discord.Embed(
                    title="📬  Reglamento enviado",
                    description="Revisa tus **MD** y acepta las reglas para activar el acceso.",
                    color=0x2E86DE,
                ),
                ephemeral=True,
            )
        else:
            await inter.followup.send(
                embed=discord.Embed(
                    title="❌  Error",
                    description=str(err),
                    color=0xFF4757,
                ),
                ephemeral=True,
            )

    @bot.tree.command(name="panel_reglas", description="Publica el panel de reglas del sistema")
    @app_commands.describe(canal="Canal donde publicar el panel")
    async def panel_reglas(inter: discord.Interaction, canal: Optional[discord.TextChannel] = None):
        if not isinstance(inter.user, discord.Member) or not permisos.member_tiene_alguna_key(
            inter.user, "OWNER", "CO_OWNER", "DIRECTOR", "DIRECTOR_ADMINISTRATIVO"
        ):
            await inter.response.send_message(
                embed=discord.Embed(
                    title="❌  Sin permiso",
                    description="Solo dirección o administración pueden publicar este panel.",
                    color=0xFF4757,
                ),
                ephemeral=True,
            )
            return
        dest = canal or inter.channel
        if not isinstance(dest, discord.TextChannel):
            await inter.response.send_message(
                embed=discord.Embed(
                    title="❌  Canal inválido",
                    description="Elige un canal de texto.",
                    color=0xFF4757,
                ),
                ephemeral=True,
            )
            return
        emb = embed_reglas_panel()
        rol = detectar_rol_comunidad(inter.guild) if inter.guild else None
        if rol:
            emb.add_field(name="Rol de comunidad", value=rol.mention, inline=False)
        else:
            emb.add_field(
                name="⚠️ Rol",
                value="Crea un rol llamado **Comunidad** o **Miembro** para el acceso automático.",
                inline=False,
            )
        await dest.send(embed=emb, view=PanelReglasView())
        await inter.response.send_message(
            embed=discord.Embed(
                title="✅  Panel publicado",
                description=f"Panel de reglas en {dest.mention}",
                color=0x00D2A0,
            ),
            ephemeral=True,
        )

    bot.add_view(PanelReglasView())
    bot.add_view(AceptarReglasView())
    print("[comunidad] OK — reglas estilo sistema")
