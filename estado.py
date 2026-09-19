# -*- coding: utf-8 -*-
"""
estado.py — Panel de estado general del hospital.
"""
from __future__ import annotations

import discord
from discord import ui

import pacientes
import turnos
from estilos import crear_embed


def construir_embed(guild: discord.Guild) -> discord.Embed:
    admitidos = pacientes.admitidos()
    en_servicio = turnos.en_servicio_lista()

    embed = crear_embed("info", "🏥 Estado del Hospital", "")
    embed.add_field(name="Pacientes admitidos", value=str(len(admitidos)), inline=True)
    embed.add_field(name="Personal en servicio", value=str(len(en_servicio)), inline=True)
    embed.add_field(name="Miembros del servidor", value=str(guild.member_count or len(guild.members)), inline=True)

    if admitidos:
        lineas = []
        for uid, f in admitidos[:8]:
            m = guild.get_member(uid)
            nombre = m.display_name if m else str(uid)
            lineas.append(f"• {nombre} — {f.get('gravedad', '?')}")
        embed.add_field(name="Últimos pacientes", value="\n".join(lineas) or "—", inline=False)

    if en_servicio:
        lineas = []
        for uid, reg in en_servicio[:8]:
            m = guild.get_member(uid)
            nombre = m.display_name if m else str(uid)
            area = f" ({reg['area']})" if reg.get("area") else ""
            lineas.append(f"• {nombre}{area}")
        embed.add_field(name="En servicio ahora", value="\n".join(lineas) or "—", inline=False)

    return embed


class PanelEstadoView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Refrescar", style=discord.ButtonStyle.primary, emoji="🔄", custom_id="estado_refrescar")
    async def refrescar(self, interaction: discord.Interaction, button: ui.Button):
        embed = construir_embed(interaction.guild)
        await interaction.response.edit_message(embed=embed, view=self)
