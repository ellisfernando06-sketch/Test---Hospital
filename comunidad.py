# -*- coding: utf-8 -*
"""comunidad.py — Reglas por DM, confirmación y rol de comunidad."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Optional

import discord
from discord import ui, app_commands
from discord.ext import commands

import config
import permisos

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PATH = os.path.join(_DATA_DIR, "comunidad_aceptados.json")

NOMBRES_ROL_COMUNIDAD = (
    "comunidad", "miembro de la comunidad", "miembro", "ciudadano",
    "verificado", "civil", "civilian", "habitante", "residente civil",
    "✅ verificado", "✔️ miembro",
)

REGLAS_DEFAULT = """
# 📜 Reglamento del Hospital

Bienvenido/a a **{hospital}**. Al aceptar estas reglas obtienes acceso de **comunidad**.

## 1. Respeto
- Trata a pacientes, personal y staff con respeto.
- Prohibido acoso, discriminación o toxicidad.

## 2. Roleplay
- Mantén el personaje y el contexto hospitalario.
- No metas OOC en canales de RP sin marcar.
- Metagaming y powergaming están prohibidos.

## 3. Canales
- Usa cada canal para su propósito (tickets, RP, off-topic).
- No spam ni flood.

## 4. Staff y tickets
- Las decisiones de staff/dirección se respetan.
- Apelaciones solo por los canales o paneles oficiales.

## 5. Economía e ítems
- El dinero e ítems de la tienda son de RP.
- No se transfieren beneficios reales fuera del servidor.

## 6. Sanciones
- Incumplir puede implicar warn, mute, kick o ban según gravedad.

---
Al pulsar **Acepto las reglas** confirmas haberlas leído y se te asignará el rol de comunidad (si está disponible).
""".strip()


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


def ya_acepto(uid: int) -> bool:
    return str(uid) in _load()


def marcar_aceptado(uid: int) -> None:
    data = _load()
    data[str(uid)] = datetime.now(timezone.utc).isoformat()
    _save(data)


def detectar_rol_comunidad(guild: discord.Guild) -> Optional[discord.Role]:
    rid = getattr(config, "ROL_COMUNIDAD_ID", None)
    if rid:
        r = guild.get_role(int(rid))
        if r:
            return r
    roles = list(guild.roles)
    lower_map = {(r.name or "").strip().lower(): r for r in roles}
    for nombre in NOMBRES_ROL_COMUNIDAD:
        if nombre in lower_map:
            return lower_map[nombre]
    for r in roles:
        n = (r.name or "").lower()
        for nombre in NOMBRES_ROL_COMUNIDAD:
            if nombre in n and r != guild.default_role:
                return r
    return None


def texto_reglas() -> str:
    custom = getattr(config, "REGLAS_TEXTO", None)
    hospital = getattr(config, "NOMBRE_HOSPITAL", "Hospital") or "Hospital"
    base = custom if custom else REGLAS_DEFAULT
    try:
        return base.format(hospital=hospital)
    except Exception:
        return base.replace("{hospital}", hospital)


class AceptarReglasView(ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=600)
        self.guild_id = guild_id

    @ui.button(label="Acepto las reglas", style=discord.ButtonStyle.success, emoji="✅")
    async def aceptar(self, inter: discord.Interaction, btn: ui.Button):
        if ya_acepto(inter.user.id):
            await inter.response.send_message("Ya habías aceptado las reglas.", ephemeral=True)
            return
        guild = inter.client.get_guild(self.guild_id)
        if not guild:
            await inter.response.send_message("No pude encontrar el servidor.", ephemeral=True)
            return
        member = guild.get_member(inter.user.id)
        if not member:
            try:
                member = await guild.fetch_member(inter.user.id)
            except Exception:
                member = None
        if not member:
            await inter.response.send_message("Debes estar en el servidor para recibir el rol.", ephemeral=True)
            return
        rol = detectar_rol_comunidad(guild)
        asignado = False
        if rol:
            try:
                await member.add_roles(rol, reason="Aceptó reglamento de comunidad")
                asignado = True
            except discord.Forbidden:
                marcar_aceptado(inter.user.id)
                await inter.response.send_message(
                    f"Aceptaste las reglas, pero no puedo asignar {rol.mention} (jerarquía del bot).",
                    ephemeral=True,
                )
                return
            except Exception as e:
                await inter.response.send_message(f"Error al asignar rol: {e}", ephemeral=True)
                return
        marcar_aceptado(inter.user.id)
        if asignado:
            msg = f"✅ Reglas aceptadas. Rol **{rol.name}** asignado. ¡Bienvenido/a!"
        else:
            msg = (
                "✅ Reglas aceptadas.\n"
                "⚠️ No encontré rol de comunidad (Comunidad, Miembro, Ciudadano, Verificado…).\n"
                "Crea el rol o define ROL_COMUNIDAD_ID en config."
            )
        await inter.response.send_message(msg, ephemeral=True)
        for c in self.children:
            c.disabled = True
        try:
            await inter.message.edit(view=self)
        except Exception:
            pass

    @ui.button(label="Rechazar", style=discord.ButtonStyle.secondary, emoji="❌")
    async def rechazar(self, inter: discord.Interaction, btn: ui.Button):
        await inter.response.send_message(
            "No aceptaste las reglas. Sin rol de comunidad el acceso será limitado.",
            ephemeral=True,
        )


async def enviar_reglas_dm(member: discord.Member):
    texto = texto_reglas()
    emb = discord.Embed(title="📜 Reglamento de la comunidad", description=texto[:4000], color=0x5865F2)
    emb.set_footer(text=getattr(config, "NOMBRE_HOSPITAL", "Hospital"))
    view = AceptarReglasView(member.guild.id)
    try:
        await member.send(embed=emb, view=view)
        return True, None
    except discord.Forbidden:
        return False, "Tienes los MD cerrados. Ábrelos e inténtalo de nuevo."
    except Exception as e:
        return False, str(e)


class PanelReglasView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Recibir reglas por MD", style=discord.ButtonStyle.primary, emoji="📜", custom_id="reglas_dm")
    async def reglas_dm(self, inter: discord.Interaction, btn: ui.Button):
        if not isinstance(inter.user, discord.Member):
            await inter.response.send_message("Solo en el servidor.", ephemeral=True)
            return
        if ya_acepto(inter.user.id):
            await inter.response.send_message("Ya aceptaste las reglas. Usa `/reglas` para reenviar el texto.", ephemeral=True)
            return
        await inter.response.defer(ephemeral=True)
        ok, err = await enviar_reglas_dm(inter.user)
        if ok:
            await inter.followup.send(
                "📬 Reglas en tus **MD**. Pulsa **Acepto las reglas** allí para el rol de comunidad.",
                ephemeral=True,
            )
        else:
            await inter.followup.send(f"❌ No pude enviarte MD: {err}", ephemeral=True)


def embed_reglas_panel() -> discord.Embed:
    return discord.Embed(
        title="📜 Reglamento de la comunidad",
        description=(
            "Pulsa el botón para recibir las **reglas en tu MD**.\n"
            "Al **aceptarlas** se te asignará el rol de **comunidad**.\n\nTambién: `/reglas`."
        ),
        color=0x5865F2,
    )


def registrar(bot: commands.Bot) -> None:
    @bot.tree.command(name="reglas", description="Recibe el reglamento por mensaje directo")
    async def reglas_cmd(inter: discord.Interaction):
        if not isinstance(inter.user, discord.Member):
            await inter.response.send_message("Solo en el servidor.", ephemeral=True)
            return
        await inter.response.defer(ephemeral=True)
        ok, err = await enviar_reglas_dm(inter.user)
        if ok:
            await inter.followup.send("📬 Reglas enviadas a tus MD. Acéptalas allí.", ephemeral=True)
        else:
            await inter.followup.send(f"❌ {err}", ephemeral=True)

    @bot.tree.command(name="panel_reglas", description="Publica el panel de reglas")
    @app_commands.describe(canal="Canal del panel")
    async def panel_reglas(inter: discord.Interaction, canal: Optional[discord.TextChannel] = None):
        if not isinstance(inter.user, discord.Member) or not permisos.member_tiene_alguna_key(
            inter.user, "OWNER", "CO_OWNER", "DIRECTOR", "DIRECTOR_ADMINISTRATIVO"
        ):
            await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
            return
        dest = canal or inter.channel
        if not isinstance(dest, discord.TextChannel):
            await inter.response.send_message("❌ Canal inválido.", ephemeral=True)
            return
        emb = embed_reglas_panel()
        rol = detectar_rol_comunidad(inter.guild) if inter.guild else None
        if rol:
            emb.add_field(name="Rol detectado", value=rol.mention, inline=False)
        else:
            emb.add_field(name="⚠️ Rol", value="Crea un rol **Comunidad** o **Miembro**.", inline=False)
        await dest.send(embed=emb, view=PanelReglasView())
        await inter.response.send_message(f"✅ Panel reglas en {dest.mention}", ephemeral=True)

    bot.add_view(PanelReglasView())
    print("[comunidad] OK")
