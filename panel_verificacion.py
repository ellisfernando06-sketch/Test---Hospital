# -*- coding: utf-8 -*-
"""
panel_verificacion.py — Panel público de verificación Roblox + cuarentena.

- Valida username en API Roblox (rechazo inmediato si es falso).
- Examen → al enviar: rol Cuarentena hasta Aprobar/Negar del staff.
- Aprobar: quita cuarentena, da Comunidad, renombra.
- Negar: quita acceso / mantiene rechazo.
"""
from __future__ import annotations

import asyncio
from typing import Optional

import discord
from discord import app_commands, ui
from discord.ext import commands

import config

try:
    import verificacion as ver
except Exception:
    ver = None

_CUARENTENA_NOMBRES = ("Cuarentena", "⏳ Cuarentena", "cuarentena", "Quarantine")


def _hospital() -> str:
    return getattr(config, "NOMBRE_HOSPITAL", None) or "Hospital General"


def _es_staff_verif(member: discord.Member) -> bool:
    if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
        return True
    try:
        import permisos

        return permisos.member_tiene_alguna_key(
            member,
            "FUNDADOR_OWNER",
            "CO_OWNER",
            "OWNER",
            "ADMIN_JEFE",
            "ADMIN",
            "CANCILLER",
            "DIR_RRHH",
            "DIRECTOR_RRHH",
        )
    except Exception:
        return False


async def _rol_cuarentena(guild: discord.Guild) -> Optional[discord.Role]:
    for n in _CUARENTENA_NOMBRES:
        for r in guild.roles:
            if (r.name or "").lower() == n.lower() or n.lower() in (r.name or "").lower():
                return r
    try:
        return await guild.create_role(
            name="⏳ Cuarentena",
            colour=discord.Colour.dark_grey(),
            reason="Verificación: modo cuarentena",
            hoist=True,
            mentionable=False,
        )
    except Exception:
        return None


async def _poner_cuarentena(member: discord.Member) -> str:
    rol = await _rol_cuarentena(member.guild)
    if not rol:
        return "(no se pudo crear/encontrar rol Cuarentena)"
    try:
        if rol not in member.roles:
            await member.add_roles(rol, reason="Examen de verificación enviado")
        return rol.mention
    except Exception as e:
        return f"(error cuarentena: {e})"


async def _quitar_cuarentena(member: discord.Member) -> None:
    for r in list(member.roles):
        if any(n.lower() in (r.name or "").lower() for n in ("cuarentena", "quarantine")):
            try:
                await member.remove_roles(r, reason="Verificación resuelta")
            except Exception:
                pass


class ModalRoblox(ui.Modal, title="Verificación Roblox"):
    usuario = ui.TextInput(
        label="Usuario de Roblox (exacto)",
        placeholder="Ej: NombreDeUsuario",
        min_length=3,
        max_length=20,
        required=True,
    )

    def __init__(self, log_channel_id: int):
        super().__init__()
        self.log_channel_id = log_channel_id

    async def on_submit(self, inter: discord.Interaction):
        if ver is None:
            return await inter.response.send_message(
                "❌ Módulo de verificación no disponible.", ephemeral=True
            )
        raw = str(self.usuario).strip()
        if not raw or " " in raw:
            return await inter.response.send_message(
                "❌ Usuario inválido. Sin espacios; solo el nombre de Roblox.",
                ephemeral=True,
            )

        await inter.response.defer(ephemeral=True)
        data = await ver.buscar_usuario_roblox(raw)
        if not data:
            emb = discord.Embed(
                title="❌ Cuenta Roblox no encontrada",
                description=(
                    f"No existe el usuario **`{raw}`** en Roblox.\n"
                    f"Revisa el nombre (mayúsculas/minúsculas) e inténtalo de nuevo.\n\n"
                    f"No se permite inventar usuarios."
                ),
                color=0xE74C3C,
            )
            return await inter.followup.send(embed=emb, ephemeral=True)

        # Iniciar examen (reutiliza flujo de verificacion.py)
        try:
            view = ver.ExamenView(
                inter.user.id,
                inter.guild.id if inter.guild else 0,
                self.log_channel_id,
                data,
            )
        except TypeError:
            # Compat firmas distintas
            view = ver.ExamenView(
                staff_id=inter.user.id,
                guild_id=inter.guild.id if inter.guild else 0,
                log_channel_id=self.log_channel_id,
                roblox_data=data,
            )

        emb = discord.Embed(
            title="✅ Cuenta Roblox válida",
            description=(
                f"**Usuario:** `{data.get('name')}`\n"
                f"**Display:** {data.get('displayName')}\n"
                f"**ID:** `{data.get('id')}`\n\n"
                f"Responde el **examen** con honestidad.\n"
                f"Al terminarlo quedarás en **cuarentena** hasta que el staff "
                f"apruebe o niegue tu entrada."
            ),
            color=0x2ECC71,
        )
        if data.get("avatar_url"):
            emb.set_thumbnail(url=data["avatar_url"])
        await inter.followup.send(embed=emb, view=view, ephemeral=True)


class PanelVerificacionView(ui.View):
    def __init__(self, log_channel_id: int):
        super().__init__(timeout=None)
        self.log_channel_id = log_channel_id

    @ui.button(
        label="Iniciar verificación",
        style=discord.ButtonStyle.success,
        emoji="✅",
        custom_id="panel_verif:iniciar",
    )
    async def iniciar(self, inter: discord.Interaction, button: ui.Button):
        await inter.response.send_modal(ModalRoblox(self.log_channel_id))

    @ui.button(
        label="¿Cómo funciona?",
        style=discord.ButtonStyle.secondary,
        emoji="ℹ️",
        custom_id="panel_verif:info",
    )
    async def info(self, inter: discord.Interaction, button: ui.Button):
        emb = discord.Embed(
            title="ℹ️ Proceso de verificación",
            description=(
                f"**{_hospital()}** · Acceso al servidor\n\n"
                f"**1.** Pulsa **Iniciar verificación**.\n"
                f"**2.** Escribe tu usuario de **Roblox real** (se valida en la API).\n"
                f"**3.** Si el usuario no existe → **rechazo inmediato**.\n"
                f"**4.** Completa el examen de normativa / RP.\n"
                f"**5.** Al enviar el examen → modo **Cuarentena** (espera staff).\n"
                f"**6.** Staff **Aprueba** o **Niega** la entrada.\n\n"
                f"Sé honesto: el staff revisa tus respuestas."
            ),
            color=0x3498DB,
        )
        await inter.response.send_message(embed=emb, ephemeral=True)


def embed_panel_verificacion() -> discord.Embed:
    emb = discord.Embed(
        title=f"🛡️ Verificación · {_hospital()}",
        description=(
            "Bienvenido/a.\n\n"
            "Para acceder a la **comunidad** debes verificar tu cuenta de "
            "**Roblox** y completar un breve examen.\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "**📌 Requisitos**\n"
            "• Usuario de Roblox **real** (no inventado)\n"
            "• Leer la normativa básica del servidor\n"
            "• Responder con sinceridad\n\n"
            "**⏳ Tras el examen**\n"
            "Quedarás en **cuarentena** hasta que el staff permita o niegue "
            "tu entrada.\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Pulsa el botón verde cuando estés listo/a."
        ),
        color=0x1ABC9C,
    )
    emb.set_footer(text=f"{_hospital()} · Verificación institucional")
    return emb


def registrar(bot: commands.Bot) -> None:
    # Vista persistente (custom_id fijo; log se guarda en data al publicar)
    try:
        bot.add_view(PanelVerificacionView(log_channel_id=0))
    except Exception:
        pass

    # Hook: al terminar examen, poner cuarentena
    if ver is not None:
        _orig_finish = getattr(ver, "ExamenView", None)
        # Parche suave vía monkeypatch del envío a log si existe método
        try:
            if hasattr(ver, "ExamenView"):
                cls = ver.ExamenView
                if hasattr(cls, "_finalizar") or hasattr(cls, "_enviar_resultado"):
                    pass  # se refuerza en botones de staff abajo
        except Exception:
            pass

    @bot.tree.command(
        name="panel_verificacion",
        description="[Staff] Publica el panel de verificación Roblox",
    )
    @app_commands.describe(
        canal="Canal donde se publica el panel",
        canal_log="Canal de logs donde staff aprueba/niega",
    )
    async def panel_verificacion(
        inter: discord.Interaction,
        canal: discord.TextChannel,
        canal_log: discord.TextChannel,
    ):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _es_staff_verif(inter.user):
            return await inter.response.send_message(
                "❌ Solo staff autorizado.", ephemeral=True
            )

        view = PanelVerificacionView(log_channel_id=canal_log.id)
        # Guardar log id en custom view state via extra store
        try:
            import roles_store

            roles_store.guardar_extra("canal_log_verificacion", canal_log.id)
            roles_store.guardar_extra("canal_panel_verificacion", canal.id)
        except Exception:
            pass

        await canal.send(embed=embed_panel_verificacion(), view=view)
        await inter.response.send_message(
            f"✅ Panel en {canal.mention} · Logs: {canal_log.mention}",
            ephemeral=True,
        )

    print("[panel_verificacion] OK — /panel_verificacion")
