# -*- coding: utf-8 -*-
"""
/sancion — un comando, menú de tipos, opción apelable (sí/no) del admin.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Optional

import discord
from discord import app_commands, ui
from discord.ext import commands

import config

try:
    import registros
except Exception:
    registros = None

try:
    import sanciones as sanc
except Exception:
    sanc = None

try:
    import permisos
except Exception:
    permisos = None


def _hospital() -> str:
    return getattr(config, "NOMBRE_HOSPITAL", None) or "Hospital General"


def _es_staff(m: discord.Member) -> bool:
    if m.guild_permissions.administrator or m.guild_permissions.moderate_members:
        return True
    if m.guild_permissions.manage_guild:
        return True
    if permisos is None:
        return False
    try:
        return permisos.member_tiene_alguna_key(
            m,
            "FUNDADOR_OWNER",
            "CO_OWNER",
            "OWNER",
            "ADMIN",
            "ADMIN_JEFE",
            "CANCILLER",
            "DIRECTOR_GENERAL",
            "DIRECTOR_DISCIPLINA",
            "DIRECTOR_ADMINISTRATIVO",
            "DIR_RRHH",
            "DIRECTOR_RRHH",
            "SUPERVISOR",
            "DIRECTOR",
        )
    except Exception:
        return False


def _puede_sobre(actor: discord.Member, target: discord.Member) -> bool:
    if actor.id == target.guild.owner_id:
        return True
    if target.id == target.guild.owner_id:
        return False
    if permisos is not None:
        try:
            return permisos.puede_actuar_sobre(actor, target)
        except Exception:
            pass
    return actor.top_role > target.top_role


_TIPOS = [
    ("advertencia", "Advertencia", "Aviso formal — sin kick/ban"),
    ("disciplinaria", "Disciplinaria", "Sanción disciplinaria registrada"),
    ("administrativa", "Administrativa", "Sanción administrativa registrada"),
    ("timeout", "Timeout", "Silenciar temporal (indica minutos)"),
    ("kick", "Kick", "Expulsar del servidor"),
    ("ban", "Ban", "Ban / cuarentena disciplinaria"),
]


def _marcar_apelable(reg: dict, apelable: bool) -> dict:
    """Guarda el flag en el registro de sanciones."""
    if sanc is None or not reg:
        return reg
    try:
        data = sanc._load()
        for s in data.get("sanciones") or []:
            if int(s.get("id") or 0) == int(reg.get("id") or 0):
                s["apelable"] = bool(apelable)
                reg["apelable"] = bool(apelable)
                break
        sanc._save(data)
    except Exception as e:
        print(f"[sancion_unico] apelable: {e}")
        reg["apelable"] = bool(apelable)
    return reg


async def _aplicar(
    inter: discord.Interaction,
    usuario: discord.Member,
    tipo: str,
    motivo: str,
    minutos: int = 0,
    apelable: bool = True,
) -> str:
    guild = inter.guild
    assert guild and isinstance(inter.user, discord.Member)

    extra = ""
    if tipo == "timeout":
        mins = max(1, min(int(minutos or 10), 40320))
        try:
            await usuario.timeout(
                timedelta(minutes=mins),
                reason=f"{motivo} — por {inter.user}",
            )
            extra = f" · {mins} min"
        except discord.Forbidden:
            return "❌ Sin permiso de timeout o el usuario es superior."
        except Exception as e:
            return f"❌ Timeout: {e}"

    elif tipo == "kick":
        try:
            await usuario.kick(reason=f"{motivo} — por {inter.user}")
        except discord.Forbidden:
            return "❌ Sin permiso de kick o el usuario es superior."
        except Exception as e:
            return f"❌ Kick: {e}"

    elif tipo == "ban":
        try:
            from sanciones_apelacion_ui import _rol_cuarentena

            rol = await _rol_cuarentena(guild)
            if rol and rol not in usuario.roles:
                await usuario.add_roles(
                    rol, reason=f"Ban disciplinario — {motivo}"
                )
            extra = " · cuarentena"
        except Exception:
            try:
                await usuario.ban(
                    reason=f"{motivo} — por {inter.user}",
                    delete_message_days=0,
                )
                extra = " · ban Discord"
            except discord.Forbidden:
                return "❌ Sin permiso de ban/cuarentena."
            except Exception as e:
                return f"❌ Ban: {e}"

    tipo_reg = {
        "advertencia": "advertencia",
        "disciplinaria": "disciplinaria",
        "administrativa": "administrativa",
        "timeout": "disciplinaria",
        "kick": "disciplinaria",
        "ban": "ban",
    }.get(tipo, "disciplinaria")

    detalle = motivo
    if tipo == "timeout":
        detalle = f"{minutos or 10} min: {motivo}"
    elif tipo in ("kick", "ban"):
        detalle = f"[{tipo}] {motivo}"

    if registros is not None:
        try:
            if sanc is not None:
                sanc._skip_notify = True  # type: ignore
            if tipo == "advertencia":
                registros.registrar_advertencia(
                    usuario.id, motivo, inter.user.id
                )
            else:
                registros.registrar_evento_cargo(
                    usuario.id, tipo, detalle, inter.user.id
                )
            if sanc is not None:
                sanc._skip_notify = False  # type: ignore
        except Exception as e:
            print(f"[sancion_unico] registros: {e}")
            try:
                if sanc is not None:
                    sanc._skip_notify = False  # type: ignore
            except Exception:
                pass

    reg = None
    if sanc is not None:
        try:
            sanc._skip_notify = True  # type: ignore
            try:
                reg = sanc.registrar_sancion(
                    usuario.id,
                    tipo_reg,
                    detalle,
                    inter.user.id,
                    duracion=f"{minutos} min" if tipo == "timeout" else "",
                )
            except TypeError:
                reg = sanc.registrar_sancion(
                    usuario.id, tipo_reg, detalle, inter.user.id
                )
            finally:
                sanc._skip_notify = False  # type: ignore
            reg = _marcar_apelable(reg, apelable)
        except Exception as e:
            print(f"[sancion_unico] sanciones: {e}")

    if reg is not None:
        try:
            from sanciones_apelacion_ui import notificar_usuario

            await notificar_usuario(inter.client, guild, reg)
        except Exception as e:
            print(f"[sancion_unico] dm: {e}")

    if reg is not None and sanc is not None:
        try:
            emb = sanc.embed_sancion(reg, guild)
            await sanc.enviar_log_sancion(inter.client, emb)
        except Exception:
            pass

    label = next((l for v, l, _ in _TIPOS if v == tipo), tipo)
    sid = f" · `#{reg.get('id')}`" if reg else ""
    ap = " · apelable" if apelable else " · sin apelación"
    return f"✅ **{label}** a {usuario.mention}{sid}{extra}{ap}"


class SancionTipoSelect(ui.Select):
    def __init__(
        self,
        usuario: discord.Member,
        motivo: str,
        minutos: int,
        apelable: bool,
    ):
        self.usuario = usuario
        self.motivo = motivo
        self.minutos = minutos
        self.apelable = apelable
        options = [
            discord.SelectOption(
                label=label,
                value=value,
                description=desc[:100],
                emoji={
                    "advertencia": "⚠️",
                    "disciplinaria": "🔨",
                    "administrativa": "📋",
                    "timeout": "🔇",
                    "kick": "👢",
                    "ban": "🚫",
                }.get(value, "⚖️"),
            )
            for value, label, desc in _TIPOS
        ]
        super().__init__(
            placeholder="Elige el tipo de sanción…",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _es_staff(interaction.user):
            return await interaction.response.send_message(
                "❌ Solo staff.", ephemeral=True
            )
        if not _puede_sobre(interaction.user, self.usuario):
            return await interaction.response.send_message(
                "❌ No puedes actuar sobre ese usuario.", ephemeral=True
            )

        tipo = self.values[0]
        if tipo == "timeout" and self.minutos < 1:
            return await interaction.response.send_message(
                "❌ Para **Timeout** indica `minutos` en el comando.",
                ephemeral=True,
            )

        await interaction.response.defer(ephemeral=True)
        msg = await _aplicar(
            interaction,
            self.usuario,
            tipo,
            self.motivo,
            minutos=self.minutos,
            apelable=self.apelable,
        )
        try:
            await interaction.message.edit(
                content=msg, view=None, embed=None
            )
        except Exception:
            pass
        await interaction.followup.send(msg, ephemeral=True)


class SancionTipoView(ui.View):
    def __init__(
        self,
        usuario: discord.Member,
        motivo: str,
        minutos: int,
        apelable: bool,
    ):
        super().__init__(timeout=120)
        self.add_item(
            SancionTipoSelect(usuario, motivo, minutos, apelable)
        )


def registrar(bot: commands.Bot) -> None:
    for n in ("sancionar", "sancion"):
        try:
            bot.tree.remove_command(n)
        except Exception:
            pass

    @bot.tree.command(
        name="sancion",
        description="[Staff] Sanción con menú de tipo y si admite apelación",
    )
    @app_commands.describe(
        usuario="Miembro",
        motivo="Motivo (MD al usuario)",
        permite_apelacion="Si el sancionado puede apelar (tú decides)",
        minutos="Solo para Timeout (1–40320)",
    )
    @app_commands.choices(
        permite_apelacion=[
            app_commands.Choice(name="Sí — puede apelar", value="si"),
            app_commands.Choice(name="No — sin apelación", value="no"),
        ]
    )
    async def sancion(
        inter: discord.Interaction,
        usuario: discord.Member,
        motivo: str,
        permite_apelacion: app_commands.Choice[str],
        minutos: Optional[app_commands.Range[int, 1, 40320]] = None,
    ):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _es_staff(inter.user):
            return await inter.response.send_message(
                "❌ Solo staff autorizado.", ephemeral=True
            )
        if usuario.bot:
            return await inter.response.send_message(
                "❌ No se sanciona bots.", ephemeral=True
            )
        if not _puede_sobre(inter.user, usuario):
            return await inter.response.send_message(
                "❌ No puedes actuar sobre ese usuario.", ephemeral=True
            )

        apelable = (permite_apelacion.value or "si").lower() == "si"
        mins = int(minutos or 0)
        texto = (
            f"**Usuario:** {usuario.mention}\n"
            f"**Motivo:** {motivo[:200]}\n"
            f"**Apelación:** {'permitida' if apelable else 'no permitida'}\n"
            + (f"**Minutos (timeout):** {mins}\n" if mins else "")
            + "\nElige el tipo:"
        )
        await inter.response.send_message(
            content=texto,
            view=SancionTipoView(usuario, motivo, mins, apelable),
            ephemeral=True,
        )

    print("[sancion_comando_unico] OK — /sancion + apelable sí/no")
