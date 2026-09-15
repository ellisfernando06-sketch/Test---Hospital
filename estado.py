"""
estado.py
=========
Panel de estado general del hospital: un único embed que resume en
vivo los datos de todos los demás sistemas (pacientes, códigos de
emergencia activos, personal en turno, inventario bajo mínimo y
quejas pendientes). Se publica con /panel_estado (vista con botón de
refrescar, persistente) o se consulta puntualmente con
/estado_hospital. No necesita edición.
"""

import discord
from discord import ui

import capacitaciones  # noqa: F401  (reservado por si se agregan próximas capacitaciones al panel)
import codigos
import config
import inventario
import pacientes
import quejas
import turnos
from estilos import crear_embed


def construir_embed(guild: discord.Guild) -> discord.Embed:
    admitidos = pacientes.admitidos()
    conteo_gravedad = {}
    for _, ficha in admitidos:
        g = ficha.get("gravedad", "Sin clasificar")
        conteo_gravedad[g] = conteo_gravedad.get(g, 0) + 1

    tipo = "exito"
    codigos_activos = codigos.activos()
    if codigos_activos:
        tipo = "error"
    elif pacientes.total_admitidos() == 0 and inventario.items_bajo_minimo():
        tipo = "aviso"

    embed = crear_embed(tipo, "🏥 Estado General del Hospital", f"**{config.NOMBRE_HOSPITAL}**")

    # --- Pacientes ---------------------------------------------------------
    if admitidos:
        resumen_gravedad = ", ".join(f"{g}: {n}" for g, n in conteo_gravedad.items())
        valor_pacientes = f"**{len(admitidos)}** admitido(s) — {resumen_gravedad}"
    else:
        valor_pacientes = "Sin pacientes admitidos."
    embed.add_field(name="🛏️ Pacientes", value=valor_pacientes, inline=False)

    # --- Códigos de emergencia ----------------------------------------------
    if codigos_activos:
        lineas = []
        for c in codigos_activos[:10]:
            info = config.CODIGOS_EMERGENCIA.get(c["codigo"], {})
            nombre = info.get("nombre", c["codigo"])
            lineas.append(f"{nombre} — {c['ubicacion']}")
        embed.add_field(name="🚨 Códigos activos", value="\n".join(lineas), inline=False)
    else:
        embed.add_field(name="🚨 Códigos activos", value="Ninguno activo. ✅", inline=False)

    # --- Personal en turno ---------------------------------------------------
    en_servicio = turnos.en_servicio_lista()
    if en_servicio:
        nombres = []
        for uid, registro in en_servicio[:15]:
            member = guild.get_member(uid) if guild else None
            etiqueta = member.display_name if member else str(uid)
            area = f" ({registro['area']})" if registro.get("area") else ""
            nombres.append(f"{etiqueta}{area}")
        extra = f"\n…y {len(en_servicio) - 15} más." if len(en_servicio) > 15 else ""
        embed.add_field(name=f"👥 Personal en turno ({len(en_servicio)})", value="\n".join(nombres) + extra, inline=False)
    else:
        embed.add_field(name="👥 Personal en turno", value="Nadie marcado en servicio ahora mismo.", inline=False)

    # --- Inventario ---------------------------------------------------------
    bajos = inventario.items_bajo_minimo()
    if bajos:
        lineas = [f"⚠️ {i['nombre']}: {i['cantidad']} (mínimo {i['minimo']})" for i in bajos[:10]]
        embed.add_field(name=f"📦 Inventario bajo mínimo ({len(bajos)})", value="\n".join(lineas), inline=False)
    else:
        embed.add_field(name="📦 Inventario", value="Todo por encima del mínimo. ✅", inline=False)

    # --- Quejas ---------------------------------------------------------------
    pendientes = quejas.total_pendientes()
    embed.add_field(
        name="📢 Quejas pendientes",
        value=f"**{pendientes}** sin resolver." if pendientes else "Sin quejas pendientes. ✅",
        inline=False,
    )

    return embed


class PanelEstadoView(ui.View):
    """Vista persistente con un botón para refrescar el panel de estado."""

    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="🔄 Actualizar", style=discord.ButtonStyle.secondary, custom_id="hospital:actualizar_estado")
    async def actualizar(self, interaction: discord.Interaction, button: ui.Button):
        embed = construir_embed(interaction.guild)
        await interaction.response.edit_message(embed=embed)
