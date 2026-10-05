# -*- coding: utf-8 -*-
"""panel_verificacion.py — Panel Roblox; rechazo inmediato si user falso. Sin cuarentena."""
from __future__ import annotations

import discord
from discord import app_commands, ui
from discord.ext import commands

import config

try:
    import verificacion as ver
except Exception:
    ver = None


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


class ModalRoblox(ui.Modal, title="Verificación Roblox"):
    usuario = ui.TextInput(
        label="Usuario de Roblox (exacto)",
        placeholder="NombreDeUsuario",
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
                "❌ Verificación no disponible.", ephemeral=True
            )
        raw = str(self.usuario).strip()
        if not raw or " " in raw:
            return await inter.response.send_message(
                "❌ Usuario inválido (sin espacios).", ephemeral=True
            )

        await inter.response.defer(ephemeral=True)
        data = await ver.buscar_usuario_roblox(raw)
        if not data:
            emb = discord.Embed(
                title="❌ Cuenta Roblox no encontrada",
                description=(
                    f"**`{raw}`** no existe en Roblox.\n"
                    f"Revisa el nombre e inténtalo de nuevo.\n\n"
                    f"No se aceptan usuarios inventados."
                ),
                color=0xE74C3C,
            )
            return await inter.followup.send(embed=emb, ephemeral=True)

        view = ver.ExamenView(
            user_id=inter.user.id,
            guild_id=inter.guild.id if inter.guild else 0,
            staff_id=inter.user.id,
            log_channel_id=self.log_channel_id,
            roblox_data=data,
        )
        emb = discord.Embed(
            title="✅ Cuenta Roblox válida",
            description=(
                f"**Usuario:** `{data.get('name')}`\n"
                f"**Display:** {data.get('displayName')}\n"
                f"**ID:** `{data.get('id')}`\n\n"
                f"Completa el examen. El staff revisará tus respuestas "
                f"y **aprobará o negará** tu verificación."
            ),
            color=0x2ECC71,
        )
        if data.get("avatar_url"):
            emb.set_thumbnail(url=data["avatar_url"])
        await inter.followup.send(embed=emb, ephemeral=True)
        await inter.followup.send(embed=view._embed_pregunta(), view=view, ephemeral=True)


class PanelVerificacionView(ui.View):
    def __init__(self, log_channel_id: int = 0):
        super().__init__(timeout=None)
        self.log_channel_id = log_channel_id

    def _log_id(self) -> int:
        if self.log_channel_id:
            return int(self.log_channel_id)
        try:
            import roles_store

            cid = roles_store.obtener_extra("canal_log_verificacion")
            return int(cid) if cid else 0
        except Exception:
            return 0

    @ui.button(
        label="Iniciar verificación",
        style=discord.ButtonStyle.success,
        emoji="✅",
        custom_id="panel_verif:iniciar",
    )
    async def iniciar(self, inter: discord.Interaction, button: ui.Button):
        lid = self._log_id()
        if not lid:
            return await inter.response.send_message(
                "❌ Falta canal de logs. Staff: vuelve a publicar el panel.",
                ephemeral=True,
            )
        await inter.response.send_modal(ModalRoblox(lid))

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
                f"**{_hospital()}**\n\n"
                f"**1.** Usuario Roblox real (API oficial)\n"
                f"**2.** Si no existe → rechazo inmediato\n"
                f"**3.** Examen de normativa / RP\n"
                f"**4.** Staff **Aprueba** o **Niega** en el canal de logs"
            ),
            color=0x3498DB,
        )
        await inter.response.send_message(embed=emb, ephemeral=True)


def embed_panel_verificacion() -> discord.Embed:
    return discord.Embed(
        title=f"🛡️ Verificación · {_hospital()}",
        description=(
            "Para unirte a la **comunidad** verifica tu **Roblox** "
            "y completa el examen.\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "**Requisitos**\n"
            "• Usuario Roblox **real**\n"
            "• Normativa básica leída\n"
            "• Respuestas honestas\n\n"
            "El staff revisará tu solicitud y te avisará.\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0x1ABC9C,
    ).set_footer(text=f"{_hospital()} · Verificación institucional")


def registrar(bot: commands.Bot) -> None:
    try:
        bot.add_view(PanelVerificacionView(0))
    except Exception:
        pass

    @bot.tree.command(
        name="panel_verificacion",
        description="[Staff] Publica el panel de verificación Roblox",
    )
    @app_commands.describe(
        canal="Canal del panel",
        canal_log="Canal donde staff Aprueba/Niega",
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
                "❌ Solo staff.", ephemeral=True
            )
        try:
            import roles_store

            roles_store.guardar_extra("canal_log_verificacion", canal_log.id)
        except Exception:
            pass
        view = PanelVerificacionView(canal_log.id)
        await canal.send(embed=embed_panel_verificacion(), view=view)
        await inter.response.send_message(
            f"✅ Panel en {canal.mention} · Log {canal_log.mention}",
            ephemeral=True,
        )

    print("[panel_verificacion] OK — sin cuarentena")
