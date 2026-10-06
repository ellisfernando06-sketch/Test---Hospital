# -*- coding: utf-8 -*-
"""
/quitar_sancion — menú de sanciones registradas.
Quita la sanción (anula) y el rol de perfil.
Solo: autoridades competentes, Admin en jefe, Administrador, Admin en prueba.
"""
from __future__ import annotations

from typing import List, Optional

import discord
from discord import app_commands, ui
from discord.ext import commands

try:
    import sanciones as sanc
except Exception:
    sanc = None

try:
    import sancion_roles as sroles
except Exception:
    sroles = None

try:
    import permisos
except Exception:
    permisos = None

# Keys autorizadas (autoridades + admins)
_KEYS_QUITAR = (
    "FUNDADOR_OWNER",
    "CO_OWNER",
    "OWNER",
    "CANCILLER",
    "VICE_CANCILLER",
    "DIRECTOR_GENERAL",
    "ADMIN_JEFE",
    "ADMIN",
    "ADMINISTRADOR",
    "ADMIN_EN_PRUEBA",
    "ADMIN_PRUEBA",
)


def _puede_quitar(m: discord.Member) -> bool:
    if m.guild_permissions.administrator:
        return True
    if m.guild and m.id == m.guild.owner_id:
        return True
    if permisos is None:
        return False
    try:
        return permisos.member_tiene_alguna_key(m, *_KEYS_QUITAR)
    except Exception:
        return False


def _lista_activas(uid: int) -> List[dict]:
    if sanc is None:
        return []
    try:
        lista = list(sanc.sanciones_de(uid) or [])
    except Exception:
        return []
    out = [
        s
        for s in lista
        if s.get("activa", True) and not s.get("anulada")
    ]
    out.sort(key=lambda s: int(s.get("id") or 0), reverse=True)
    return out


class QuitarSelect(ui.Select):
    def __init__(self, opciones: List[dict], target: discord.Member):
        self._map = {str(s.get("id")): s for s in opciones}
        self.target = target
        opts = []
        for s in opciones[:25]:
            tipo = (s.get("tipo") or "sanción").capitalize()
            mot = (s.get("motivo") or "—")[:70]
            opts.append(
                discord.SelectOption(
                    label=f"#{s.get('id')} · {tipo}"[:100],
                    value=str(s.get("id")),
                    description=mot[:100],
                    emoji="🗑️",
                )
            )
        super().__init__(
            placeholder="Elige la sanción a quitar…",
            min_values=1,
            max_values=1,
            options=opts,
        )

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(
            interaction.user, discord.Member
        ):
            return await interaction.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _puede_quitar(interaction.user):
            return await interaction.response.send_message(
                "❌ Sin permiso. Solo autoridades, Admin en jefe, "
                "Administrador o Admin en prueba.",
                ephemeral=True,
            )
        if sanc is None:
            return await interaction.response.send_message(
                "❌ Sistema no disponible.", ephemeral=True
            )

        sid = self.values[0]
        reg = self._map.get(sid)
        if not reg:
            try:
                reg = sanc.obtener_sancion(int(sid))
            except Exception:
                reg = None
        if not reg or reg.get("anulada") or not reg.get("activa", True):
            return await interaction.response.send_message(
                "❌ Esa sanción ya no está activa.", ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        # Anular en el registro
        try:
            sanc.anular_sancion(
                int(reg.get("id") or 0),
                interaction.user.id,
                f"Quitada por {interaction.user}",
            )
        except Exception as e:
            return await interaction.followup.send(
                f"❌ No se pudo anular: {e}", ephemeral=True
            )

        # Quitar rol de perfil
        member = interaction.guild.get_member(
            int(reg.get("usuario_id") or 0)
        ) or self.target
        if member and sroles is not None:
            try:
                await sroles.quitar_rol_sancion(
                    interaction.guild, member, reg.get("tipo") or ""
                )
                await sroles.quitar_todos_roles_sancion(
                    interaction.guild, member
                )
            except Exception as e:
                print(f"[quitar_sancion] rol: {e}")

        # Aviso al usuario
        if member:
            try:
                await member.send(
                    f"✅ Tu sanción `#{reg.get('id')}` "
                    f"(**{reg.get('tipo')}**) fue **retirada** "
                    f"por el staff."
                )
            except Exception:
                pass

        await interaction.followup.send(
            f"✅ Sanción `#{reg.get('id')}` · **{reg.get('tipo')}** "
            f"retirada de {member.mention if member else 'usuario'}.\n"
            f"Registro anulado + rol de sanción quitado.",
            ephemeral=True,
        )
        try:
            await interaction.message.edit(view=None)
        except Exception:
            pass


class QuitarView(ui.View):
    def __init__(self, opciones: List[dict], target: discord.Member):
        super().__init__(timeout=180)
        self.add_item(QuitarSelect(opciones, target))


def registrar(bot: commands.Bot) -> None:
    for n in ("quitar_sancion", "retirar_sancion"):
        try:
            bot.tree.remove_command(n)
        except Exception:
            pass

    @bot.tree.command(
        name="quitar_sancion",
        description="[Staff] Quitar sanción del menú (registro + rol)",
    )
    @app_commands.describe(usuario="Miembro con sanciones registradas")
    async def quitar_sancion(
        inter: discord.Interaction, usuario: discord.Member
    ):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _puede_quitar(inter.user):
            return await inter.response.send_message(
                "❌ Sin permiso.\n"
                "Solo: **autoridades competentes**, **Admin en jefe**, "
                "**Administrador** o **Admin en prueba**.",
                ephemeral=True,
            )
        if sanc is None:
            return await inter.response.send_message(
                "❌ Sistema no disponible.", ephemeral=True
            )

        lista = _lista_activas(usuario.id)
        if not lista:
            return await inter.response.send_message(
                f"{usuario.mention} no tiene sanciones **activas** registradas.",
                ephemeral=True,
            )

        lineas = [
            f"• `#{s.get('id')}` · **{s.get('tipo')}** — "
            f"{(s.get('motivo') or '—')[:50]}"
            for s in lista[:10]
        ]
        await inter.response.send_message(
            content=(
                f"**Sanciones activas de {usuario.mention}:** {len(lista)}\n"
                + "\n".join(lineas)
                + "\n\nElige en el menú la que quieres **quitar**:"
            ),
            view=QuitarView(lista, usuario),
            ephemeral=True,
        )

    print(
        "[quitar_sancion_cmd] OK — menú + anula + quita rol (staff autorizado)"
    )
