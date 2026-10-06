# -*- coding: utf-8 -*-
"""
Un solo comando /sancion con menú desplegable de tipos:
  Advertencia · Disciplinaria · Administrativa · Timeout · Kick · Ban
Flujo ordenado, un registro, un MD con Apelar.
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


# Orden del menú (value, label, description)
_TIPOS = [
    ("advertencia", "Advertencia", "Aviso formal — sin kick/ban"),
    ("disciplinaria", "Disciplinaria", "Sanción disciplinaria registrada"),
    ("administrativa", "Administrativa", "Sanción administrativa registrada"),
    ("timeout", "Timeout", "Silenciar temporal (indica minutos)"),
    ("kick", "Kick", "Expulsar del servidor"),
    ("ban", "Ban", "Ban / cuarentena disciplinaria"),
]


async def _aplicar(
    inter: discord.Interaction,
    usuario: discord.Member,
    tipo: str,
    motivo: str,
    minutos: int = 0,
) -> str:
    """Ejecuta la medida. Devuelve texto de resultado."""
    guild = inter.guild
    assert guild and isinstance(inter.user, discord.Member)

    # 1) Acción Discord según tipo
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
        # Cuarentena si sigue en el server; si no se puede ban real opcional
        try:
            # Preferir cuarentena disciplinaria (apelable)
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

    # 2) Registro canónico (una sola vez)
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

    # registros (expediente) — el hook puede registrar otra vez; usamos skip + un solo sanciones
    if registros is not None:
        try:
            if tipo == "advertencia":
                # Solo expediente; sanciones se hace abajo sin doble notify del hook
                try:
                    import sanciones as smod

                    smod._skip_notify = True  # type: ignore
                except Exception:
                    pass
                registros.registrar_advertencia(
                    usuario.id, motivo, inter.user.id
                )
                try:
                    import sanciones as smod

                    smod._skip_notify = False  # type: ignore
                except Exception:
                    pass
            else:
                try:
                    import sanciones as smod

                    smod._skip_notify = True  # type: ignore
                except Exception:
                    pass
                registros.registrar_evento_cargo(
                    usuario.id, tipo, detalle, inter.user.id
                )
                try:
                    import sanciones as smod

                    smod._skip_notify = False  # type: ignore
                except Exception:
                    pass
        except Exception as e:
            print(f"[sancion_unico] registros: {e}")

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
        except Exception as e:
            print(f"[sancion_unico] sanciones: {e}")

    # 3) Un MD
    if reg is not None:
        try:
            from sanciones_apelacion_ui import notificar_usuario

            await notificar_usuario(inter.client, guild, reg)
        except Exception as e:
            print(f"[sancion_unico] dm: {e}")

    # 4) Log sanciones si existe
    if reg is not None and sanc is not None:
        try:
            emb = sanc.embed_sancion(reg, guild)
            await sanc.enviar_log_sancion(inter.client, emb)
        except Exception:
            pass

    label = next((l for v, l, _ in _TIPOS if v == tipo), tipo)
    sid = f" · `#{reg.get('id')}`" if reg else ""
    return f"✅ **{label}** a {usuario.mention}{sid}{extra}"


class SancionTipoSelect(ui.Select):
    def __init__(self, usuario: discord.Member, motivo: str, minutos: int):
        self.usuario = usuario
        self.motivo = motivo
        self.minutos = minutos
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
                "❌ Para **Timeout** indica minutos en el comando (parámetro `minutos`).",
                ephemeral=True,
            )

        await interaction.response.defer(ephemeral=True)
        msg = await _aplicar(
            interaction,
            self.usuario,
            tipo,
            self.motivo,
            minutos=self.minutos,
        )
        try:
            await interaction.message.edit(
                content=msg, view=None, embed=None
            )
        except Exception:
            pass
        await interaction.followup.send(msg, ephemeral=True)


class SancionTipoView(ui.View):
    def __init__(self, usuario: discord.Member, motivo: str, minutos: int):
        super().__init__(timeout=120)
        self.add_item(SancionTipoSelect(usuario, motivo, minutos))


def registrar(bot: commands.Bot) -> None:
    # Quitar alias confusos si existen
    for n in ("sancionar", "sancion"):
        try:
            bot.tree.remove_command(n)
        except Exception:
            pass

    @bot.tree.command(
        name="sancion",
        description="[Staff] Sanción: elige tipo en el menú (advertencia, ban, kick…)",
    )
    @app_commands.describe(
        usuario="Miembro",
        motivo="Motivo (se envía por MD)",
        minutos="Solo para Timeout (1–40320)",
    )
    async def sancion(
        inter: discord.Interaction,
        usuario: discord.Member,
        motivo: str,
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

        mins = int(minutos or 0)
        texto = (
            f"**Usuario:** {usuario.mention}\n"
            f"**Motivo:** {motivo[:200]}\n"
            + (f"**Minutos (timeout):** {mins}\n" if mins else "")
            + "\nElige el tipo en el menú:"
        )
        await inter.response.send_message(
            content=texto,
            view=SancionTipoView(usuario, motivo, mins),
            ephemeral=True,
        )

    print("[sancion_comando_unico] OK — /sancion + menú de tipos")
