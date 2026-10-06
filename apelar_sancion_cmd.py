# -*- coding: utf-8 -*-
"""
/apelar_sancion — menú de sanciones activas creadas con /sancion.
Solo muestra las que tienen apelable=True (o sin flag = sí, por compatibilidad).
Abre el mismo ticket de apelación que el botón Apelar del MD.
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


def _es_apelable(reg: dict) -> bool:
    if not reg:
        return False
    if not reg.get("activa", True) or reg.get("anulada"):
        return False
    ap = reg.get("apelable", True)
    if ap is False or str(ap).lower() in ("0", "false", "no"):
        return False
    return True


def _sanciones_apelables(uid: int) -> List[dict]:
    if sanc is None:
        return []
    try:
        lista = sanc.sanciones_de(uid, solo_activas=True)
    except TypeError:
        lista = [
            s
            for s in (sanc.sanciones_de(uid) or [])
            if s.get("activa", True) and not s.get("anulada")
        ]
    out = [s for s in lista if _es_apelable(s)]
    out.sort(key=lambda s: int(s.get("id") or 0), reverse=True)
    return out


class ApelarSelect(ui.Select):
    def __init__(self, opciones: List[dict]):
        self._map = {str(s.get("id")): s for s in opciones}
        opts = []
        for s in opciones[:25]:
            tipo = (s.get("tipo") or "sanción").capitalize()
            mot = (s.get("motivo") or "—")[:50]
            opts.append(
                discord.SelectOption(
                    label=f"#{s.get('id')} · {tipo}"[:100],
                    value=str(s.get("id")),
                    description=mot,
                    emoji="⚖️",
                )
            )
        super().__init__(
            placeholder="Elige la sanción a apelar…",
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
        if sanc is None:
            return await interaction.response.send_message(
                "❌ Sistema no disponible.", ephemeral=True
            )

        sid = self.values[0]
        reg = self._map.get(sid) or sanc.obtener_sancion(int(sid))
        if not reg or not _es_apelable(reg):
            return await interaction.response.send_message(
                "❌ Esa sanción no admite apelación o ya no está activa.",
                ephemeral=True,
            )

        # Solo el sancionado puede apelar la suya
        if int(reg.get("usuario_id") or 0) != interaction.user.id:
            return await interaction.response.send_message(
                "❌ Solo puedes apelar tus propias sanciones.",
                ephemeral=True,
            )

        await interaction.response.defer(ephemeral=True)
        canal = await sanc.abrir_ticket_apelacion(
            interaction.guild, interaction.user, reg
        )
        if not canal:
            return await interaction.followup.send(
                "❌ No se pudo abrir el ticket de apelación.",
                ephemeral=True,
            )
        await interaction.followup.send(
            f"✅ Apelación abierta: {canal.mention}\n"
            f"Sanción `#{reg.get('id')}` · {reg.get('tipo')}",
            ephemeral=True,
        )
        try:
            await interaction.message.edit(view=None)
        except Exception:
            pass


class ApelarView(ui.View):
    def __init__(self, opciones: List[dict]):
        super().__init__(timeout=180)
        self.add_item(ApelarSelect(opciones))


def registrar(bot: commands.Bot) -> None:
    for n in ("apelar_sancion", "apelar"):
        try:
            bot.tree.remove_command(n)
        except Exception:
            pass

    @bot.tree.command(
        name="apelar_sancion",
        description="Apelar una sanción activa (las de /sancion)",
    )
    async def apelar_sancion(inter: discord.Interaction):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if sanc is None:
            return await inter.response.send_message(
                "❌ Sistema de sanciones no disponible.", ephemeral=True
            )

        lista = _sanciones_apelables(inter.user.id)
        if not lista:
            # Puede haber activas pero no apelables
            try:
                todas = sanc.sanciones_de(inter.user.id, solo_activas=True)
            except TypeError:
                todas = [
                    s
                    for s in (sanc.sanciones_de(inter.user.id) or [])
                    if s.get("activa", True) and not s.get("anulada")
                ]
            if todas and not any(_es_apelable(s) for s in todas):
                return await inter.response.send_message(
                    "Tienes sanciones activas, pero **ninguna admite apelación**.",
                    ephemeral=True,
                )
            return await inter.response.send_message(
                "✅ No tienes sanciones activas para apelar.",
                ephemeral=True,
            )

        await inter.response.send_message(
            content=(
                f"Tienes **{len(lista)}** sanción(es) apelable(s).\n"
                "Elige cuál apelar:"
            ),
            view=ApelarView(lista),
            ephemeral=True,
        )

    # También alias corto
    @bot.tree.command(
        name="apelar",
        description="Alias de /apelar_sancion",
    )
    async def apelar(inter: discord.Interaction):
        return await apelar_sancion.callback(inter)  # type: ignore

    # Panel: solo sanciones apelables
    try:
        import sanciones_apelacion_ui as ui_mod

        if hasattr(ui_mod, "PanelApelacionesView"):
            Orig = ui_mod.PanelApelacionesView

            class PanelApelacionesView(Orig):
                @ui.button(
                    label="Abrir apelación",
                    style=discord.ButtonStyle.primary,
                    emoji="⚖️",
                    custom_id="panel_apelaciones:abrir",
                )
                async def abrir(
                    self, inter: discord.Interaction, button: ui.Button
                ):
                    if not inter.guild or not isinstance(
                        inter.user, discord.Member
                    ):
                        return await inter.response.send_message(
                            "❌ Solo en el servidor.", ephemeral=True
                        )
                    if sanc is None:
                        return await inter.response.send_message(
                            "❌ Sistema no disponible.", ephemeral=True
                        )
                    lista = _sanciones_apelables(inter.user.id)
                    if not lista:
                        return await inter.response.send_message(
                            "No tienes sanciones **apelables** activas.",
                            ephemeral=True,
                        )
                    if len(lista) == 1:
                        await inter.response.defer(ephemeral=True)
                        canal = await sanc.abrir_ticket_apelacion(
                            inter.guild, inter.user, lista[0]
                        )
                        if not canal:
                            return await inter.followup.send(
                                "❌ No se pudo crear el ticket.",
                                ephemeral=True,
                            )
                        return await inter.followup.send(
                            f"✅ {canal.mention}", ephemeral=True
                        )
                    await inter.response.send_message(
                        content="Elige la sanción a apelar:",
                        view=ApelarView(lista),
                        ephemeral=True,
                    )

            ui_mod.PanelApelacionesView = PanelApelacionesView
            try:
                bot.add_view(PanelApelacionesView())
            except Exception:
                pass
    except Exception as e:
        print(f"[apelar_sancion_cmd] panel: {e}")

    print("[apelar_sancion_cmd] OK — /apelar_sancion + /apelar enlazados")
