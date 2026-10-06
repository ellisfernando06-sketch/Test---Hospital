# -*- coding: utf-8 -*-
"""
/apelar_sancion y /apelar — menú desplegable de sanciones REGISTRADAS
(las creadas con /sancion u otros comandos enganchados).
Solo las activas y apelables.
"""
from __future__ import annotations

from typing import List

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


def _lista_registradas(uid: int, solo_apelables: bool = True) -> List[dict]:
    """Todas las sanciones registradas del usuario, ordenadas."""
    if sanc is None:
        return []
    try:
        lista = list(sanc.sanciones_de(uid) or [])
    except Exception:
        return []
    out = []
    for s in lista:
        if not s.get("activa", True) or s.get("anulada"):
            continue
        if solo_apelables and not _es_apelable(s):
            continue
        out.append(s)
    out.sort(key=lambda s: int(s.get("id") or 0), reverse=True)
    return out


class ApelarSelect(ui.Select):
    def __init__(self, opciones: List[dict]):
        self._map = {str(s.get("id")): s for s in opciones}
        opts = []
        for s in opciones[:25]:
            tipo = (s.get("tipo") or "sanción").capitalize()
            mot = (s.get("motivo") or "—")[:80]
            fecha = (s.get("fecha") or "")[:16]
            label = f"#{s.get('id')} · {tipo}"
            if fecha:
                label = f"#{s.get('id')} · {tipo} · {fecha}"
            opts.append(
                discord.SelectOption(
                    label=label[:100],
                    value=str(s.get("id")),
                    description=mot[:100],
                    emoji="⚖️",
                )
            )
        super().__init__(
            placeholder="Elige la sanción registrada a apelar…",
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
        reg = self._map.get(sid)
        if not reg:
            try:
                reg = sanc.obtener_sancion(int(sid))
            except Exception:
                reg = None
        if not reg or not _es_apelable(reg):
            return await interaction.response.send_message(
                "❌ Esa sanción no admite apelación o ya no está activa.",
                ephemeral=True,
            )
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
            f"**Sanción registrada** `#{reg.get('id')}` · {reg.get('tipo')}\n"
            f"{(reg.get('motivo') or '')[:120]}",
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


async def _mostrar_menu(inter: discord.Interaction) -> None:
    lista = _lista_registradas(inter.user.id, solo_apelables=True)
    if not lista:
        todas = _lista_registradas(inter.user.id, solo_apelables=False)
        if todas:
            return await inter.response.send_message(
                "Tienes sanciones registradas, pero **ninguna admite apelación**.",
                ephemeral=True,
            )
        return await inter.response.send_message(
            "✅ No tienes sanciones registradas activas para apelar.",
            ephemeral=True,
        )

    lineas = []
    for s in lista[:10]:
        lineas.append(
            f"• `#{s.get('id')}` · **{s.get('tipo')}** — "
            f"{(s.get('motivo') or '—')[:60]}"
        )
    extra = f"\n… y {len(lista) - 10} más" if len(lista) > 10 else ""

    await inter.response.send_message(
        content=(
            f"**Sanciones registradas apelables:** {len(lista)}\n"
            + "\n".join(lineas)
            + extra
            + "\n\nElige en el menú desplegable:"
        ),
        view=ApelarView(lista),
        ephemeral=True,
    )


def registrar(bot: commands.Bot) -> None:
    for n in ("apelar_sancion", "apelar"):
        try:
            bot.tree.remove_command(n)
        except Exception:
            pass

    @bot.tree.command(
        name="apelar_sancion",
        description="Apelar: menú de sanciones registradas (de /sancion)",
    )
    async def apelar_sancion(inter: discord.Interaction):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if sanc is None:
            return await inter.response.send_message(
                "❌ Sistema no disponible.", ephemeral=True
            )
        await _mostrar_menu(inter)

    @bot.tree.command(
        name="apelar",
        description="Alias: menú de sanciones registradas para apelar",
    )
    async def apelar(inter: discord.Interaction):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if sanc is None:
            return await inter.response.send_message(
                "❌ Sistema no disponible.", ephemeral=True
            )
        await _mostrar_menu(inter)

    # Botón Apelar del MD: si hay varias, menú; si una, ticket directo
    try:
        import sanciones_apelacion_ui as ui_mod

        class ApelarSancionView(ui.View):
            def __init__(self, sancion_id: int = 0):
                super().__init__(timeout=None)
                self.sancion_id = int(sancion_id or 0)

            @ui.button(
                label="Apelar",
                style=discord.ButtonStyle.primary,
                emoji="⚖️",
                custom_id="sancion:apelar",
            )
            async def apelar_btn(
                self, inter: discord.Interaction, button: ui.Button
            ):
                if not inter.guild:
                    # DM: buscar guild
                    guild = None
                    for g in inter.client.guilds:
                        if g.get_member(inter.user.id):
                            guild = g
                            break
                else:
                    guild = inter.guild

                if not guild or not isinstance(inter.user, discord.Member):
                    # En DM inter.user puede ser User
                    member = None
                    if guild:
                        member = guild.get_member(inter.user.id)
                    if not member:
                        return await inter.response.send_message(
                            "❌ Usa `/apelar_sancion` en el servidor.",
                            ephemeral=True,
                        )
                else:
                    member = inter.user

                if sanc is None:
                    return await inter.response.send_message(
                        "❌ Sistema no disponible.", ephemeral=True
                    )

                lista = _lista_registradas(member.id, solo_apelables=True)
                if not lista:
                    return await inter.response.send_message(
                        "❌ No hay sanciones registradas apelables.",
                        ephemeral=True,
                    )

                # Preferir la del botón si está en la lista
                if self.sancion_id:
                    for s in lista:
                        if int(s.get("id") or 0) == self.sancion_id:
                            if not _es_apelable(s):
                                return await inter.response.send_message(
                                    "❌ Esta sanción no admite apelación.",
                                    ephemeral=True,
                                )
                            await inter.response.defer(ephemeral=True)
                            canal = await sanc.abrir_ticket_apelacion(
                                guild, member, s
                            )
                            if not canal:
                                return await inter.followup.send(
                                    "❌ No se pudo abrir el ticket.",
                                    ephemeral=True,
                                )
                            return await inter.followup.send(
                                f"✅ {canal.mention}", ephemeral=True
                            )

                if len(lista) == 1:
                    await inter.response.defer(ephemeral=True)
                    canal = await sanc.abrir_ticket_apelacion(
                        guild, member, lista[0]
                    )
                    if not canal:
                        return await inter.followup.send(
                            "❌ No se pudo abrir el ticket.",
                            ephemeral=True,
                        )
                    return await inter.followup.send(
                        f"✅ {canal.mention}", ephemeral=True
                    )

                # Varias → menú desplegable
                await inter.response.send_message(
                    content=(
                        f"Tienes **{len(lista)}** sanciones registradas.\n"
                        "Elige cuál apelar:"
                    ),
                    view=ApelarView(lista),
                    ephemeral=True,
                )

        ui_mod.ApelarSancionView = ApelarSancionView
        try:
            bot.add_view(ApelarSancionView(0))
        except Exception:
            pass
    except Exception as e:
        print(f"[apelar_sancion_cmd] view: {e}")

    # Panel: menú de registradas
    try:
        import sanciones_apelacion_ui as ui_mod

        class PanelApelacionesView(ui.View):
            def __init__(self):
                super().__init__(timeout=None)

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
                lista = _lista_registradas(inter.user.id, solo_apelables=True)
                if not lista:
                    return await inter.response.send_message(
                        "No tienes sanciones **registradas** apelables.",
                        ephemeral=True,
                    )
                await inter.response.send_message(
                    content=(
                        f"**{len(lista)}** sanción(es) registrada(s).\n"
                        "Elige en el menú:"
                    ),
                    view=ApelarView(lista),
                    ephemeral=True,
                )

            @ui.button(
                label="Mis sanciones registradas",
                style=discord.ButtonStyle.secondary,
                emoji="📜",
                custom_id="panel_apelaciones:estado",
            )
            async def estado(
                self, inter: discord.Interaction, button: ui.Button
            ):
                if sanc is None:
                    return await inter.response.send_message(
                        "❌ No disponible.", ephemeral=True
                    )
                lista = _lista_registradas(
                    inter.user.id, solo_apelables=False
                )
                if not lista:
                    return await inter.response.send_message(
                        "✅ Sin sanciones registradas activas.",
                        ephemeral=True,
                    )
                lineas = []
                for s in lista[:15]:
                    ap = "apelable" if _es_apelable(s) else "sin apelación"
                    lineas.append(
                        f"`#{s.get('id')}` · **{s.get('tipo')}** · {ap}\n"
                        f"  {(s.get('motivo') or '—')[:80]}"
                    )
                await inter.response.send_message(
                    "\n".join(lineas), ephemeral=True
                )

        ui_mod.PanelApelacionesView = PanelApelacionesView
        try:
            bot.add_view(PanelApelacionesView())
        except Exception:
            pass
    except Exception as e:
        print(f"[apelar_sancion_cmd] panel: {e}")

    print(
        "[apelar_sancion_cmd] OK — menú desplegable de sanciones registradas"
    )
