# -*- coding: utf-8 -*-
"""
panel_tickets_ui.py — Panel de tickets institucional, elegante y profesional.
/panel_tickets publica el panel.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import discord
from discord import app_commands, ui
from discord.ext import commands

import config

try:
    import roles_store
except Exception:
    roles_store = None

try:
    import paneles as _paneles
except Exception:
    _paneles = None

# Tipos de ticket (menú)
_TIPOS = [
    ("soporte", "Soporte general", "Ayuda con el servidor, roles o acceso"),
    ("reportar", "Reportar usuario / incidente", "Reportes de conducta o RP"),
    ("queja", "Queja o reclamación", "Inconformidades formales"),
    ("postulacion", "Postulación / personal", "Consultas de ingreso al staff"),
    ("otro", "Otro asunto", "Cualquier otro tema privado"),
]


def _hospital() -> str:
    return getattr(config, "NOMBRE_HOSPITAL", None) or "Hospital General"


def embed_panel_tickets() -> discord.Embed:
    hospital = _hospital()
    desc = (
        f"Bienvenido/a al **centro de atención** de **{hospital}**.\n\n"
        f"Si necesitas ayuda del personal, abre un **ticket privado**.\n"
        f"Solo tú y el staff autorizado podrán verlo.\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"**Cómo funciona**\n"
        f"**1.** Elige el tipo de consulta en el menú\n"
        f"**2.** Se crea un canal privado solo para ti\n"
        f"**3.** Describe tu caso con claridad\n"
        f"**4.** El staff te responderá a la brevedad\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"*Mantén el respeto. Los tickets son un canal formal de comunicación.*"
    )
    emb = discord.Embed(
        title=f"🎫  Centro de Tickets · {hospital}",
        description=desc,
        color=0x1A5276,
        timestamp=datetime.now(timezone.utc),
    )
    emb.add_field(
        name="📋 Tipos disponibles",
        value=(
            "• Soporte general\n"
            "• Reportar usuario / incidente\n"
            "• Queja o reclamación\n"
            "• Postulación / personal\n"
            "• Otro asunto"
        ),
        inline=True,
    )
    emb.add_field(
        name="⏱️ Atención",
        value=(
            "Respuesta del staff\n"
            "en el menor tiempo posible.\n\n"
            "Horario según disponibilidad\n"
            "del personal en línea."
        ),
        inline=True,
    )
    emb.set_footer(
        text=f"{hospital}  ·  Atención institucional  ·  Salud · Disciplina · Servicio"
    )
    return emb


def embed_ticket_abierto(
    member: discord.Member, tipo_label: str, tipo_desc: str
) -> discord.Embed:
    hospital = _hospital()
    emb = discord.Embed(
        title="✨ Ticket abierto",
        description=(
            f"Hola, {member.mention}.\n\n"
            f"Tu solicitud fue registrada correctamente.\n"
            f"Un miembro del **staff** te atenderá en este canal.\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"**Tipo:** {tipo_label}\n"
            f"**Detalle:** {tipo_desc}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"**Por favor:**\n"
            f"• Explica tu caso con orden y claridad\n"
            f"• Adjunta capturas si ayudan\n"
            f"• Espera la respuesta del personal\n\n"
            f"*Gracias por confiar en {hospital}.*"
        ),
        color=0x148F77,
        timestamp=datetime.now(timezone.utc),
    )
    emb.set_author(
        name=member.display_name,
        icon_url=getattr(member.display_avatar, "url", None),
    )
    emb.set_footer(text=f"{hospital}  ·  Ticket privado")
    return emb


def _categoria_tickets(guild: discord.Guild) -> Optional[discord.CategoryChannel]:
    cid = getattr(config, "TICKET_CATEGORIA_ID", None)
    if cid:
        ch = guild.get_channel(int(cid))
        if isinstance(ch, discord.CategoryChannel):
            return ch
    for c in guild.categories:
        n = (c.name or "").lower()
        if "ticket" in n:
            return c
    return None


def _overwrites_ticket(
    guild: discord.Guild, user: discord.Member
) -> dict:
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, attach_files=True, read_message_history=True
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            manage_channels=True,
            manage_messages=True,
        ),
    }
    keys = list(getattr(config, "TICKET_STAFF_KEYS", None) or [])
    if not keys:
        keys = ["OWNER", "CO_OWNER", "ADMIN", "ADMIN_JEFE", "DIR_RRHH", "DIRECTOR_RRHH"]

    if roles_store is not None:
        for key in keys:
            if key == "DIRECTOR":
                for dk in getattr(config, "DIRECTOR_KEYS", []) or []:
                    rid = roles_store.obtener_id_key(dk)
                    if rid:
                        rol = guild.get_role(rid)
                        if rol:
                            overwrites[rol] = discord.PermissionOverwrite(
                                view_channel=True, send_messages=True
                            )
            else:
                rid = roles_store.obtener_id_key(key)
                if rid:
                    rol = guild.get_role(rid)
                    if rol:
                        overwrites[rol] = discord.PermissionOverwrite(
                            view_channel=True, send_messages=True
                        )

    # Staff por nombre
    if _paneles is not None:
        try:
            staff_role = _paneles._rol_staff_servidor(guild)
            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True
                )
        except Exception:
            pass
    else:
        for n in ("Staff del Servidor", "Staff", "STAFF"):
            r = discord.utils.get(guild.roles, name=n)
            if r:
                overwrites[r] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True
                )
                break

    # Admins
    for r in guild.roles:
        if r.permissions.administrator and r != guild.default_role:
            overwrites[r] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True
            )

    return overwrites


class TicketTipoSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=label,
                value=value,
                description=desc[:100],
                emoji={"soporte": "💬", "reportar": "⚠️", "queja": "📩", "postulacion": "📋", "otro": "📁"}.get(
                    value, "🎫"
                ),
            )
            for value, label, desc in _TIPOS
        ]
        super().__init__(
            placeholder="Selecciona el tipo de ticket…",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="panel_tickets:tipo",
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )

        tipo = self.values[0]
        meta = next((t for t in _TIPOS if t[0] == tipo), _TIPOS[-1])
        _, label, desc = meta

        # Evitar spam: un ticket abierto del mismo usuario
        pref = f"ticket-{interaction.user.name}".lower()[:40]
        for ch in guild.text_channels:
            n = (ch.name or "").lower()
            if n.startswith("ticket-") and interaction.user.name.lower()[:20] in n:
                return await interaction.response.send_message(
                    f"Ya tienes un ticket abierto: {ch.mention}\n"
                    f"Úsalo o pide al staff que lo cierre.",
                    ephemeral=True,
                )

        await interaction.response.defer(ephemeral=True)

        cat = _categoria_tickets(guild)
        overwrites = _overwrites_ticket(guild, interaction.user)
        safe_name = (
            f"ticket-{tipo}-{interaction.user.name}"
            .lower()
            .replace(" ", "-")[:90]
        )

        try:
            canal = await guild.create_text_channel(
                safe_name,
                category=cat,
                overwrites=overwrites,
                topic=f"Ticket de {interaction.user} · {label}",
                reason=f"Ticket {tipo} · {interaction.user}",
            )
        except discord.Forbidden:
            return await interaction.followup.send(
                "❌ No tengo permisos para crear canales.", ephemeral=True
            )
        except Exception as e:
            return await interaction.followup.send(
                f"❌ Error al crear el ticket: {e}", ephemeral=True
            )

        emb = embed_ticket_abierto(interaction.user, label, desc)

        # Vista de cierre (paneles o tickets_cierre)
        view_cierre = None
        if _paneles is not None:
            try:
                view_cierre = _paneles.CerrarTicketView()
            except Exception:
                pass

        mentions = [interaction.user.mention]
        try:
            if _paneles is not None:
                sr = _paneles._rol_staff_servidor(guild)
                if sr:
                    mentions.append(sr.mention)
        except Exception:
            pass

        kwargs = {"content": " ".join(mentions), "embed": emb}
        if view_cierre is not None:
            kwargs["view"] = view_cierre

        await canal.send(**kwargs)
        await interaction.followup.send(
            f"✅ Ticket creado: {canal.mention}\n**Tipo:** {label}",
            ephemeral=True,
        )


class PanelTicketsView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketTipoSelect())


def registrar(bot: commands.Bot) -> None:
    try:
        bot.add_view(PanelTicketsView())
    except Exception as e:
        print(f"[panel_tickets_ui] add_view: {e}")

    try:
        bot.tree.remove_command("panel_tickets")
    except Exception:
        pass

    @bot.tree.command(
        name="panel_tickets",
        description="[Staff] Publica el panel profesional de tickets",
    )
    @app_commands.describe(canal="Canal donde se publica el panel (opcional)")
    async def panel_tickets(
        inter: discord.Interaction,
        canal: Optional[discord.TextChannel] = None,
    ):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not (
            inter.user.guild_permissions.administrator
            or inter.user.guild_permissions.manage_guild
            or inter.user.guild_permissions.manage_channels
        ):
            return await inter.response.send_message(
                "❌ Solo staff autorizado.", ephemeral=True
            )

        destino = canal or (
            inter.channel if isinstance(inter.channel, discord.TextChannel) else None
        )
        if destino is None:
            return await inter.response.send_message(
                "❌ Indica un canal de texto.", ephemeral=True
            )

        await destino.send(embed=embed_panel_tickets(), view=PanelTicketsView())
        await inter.response.send_message(
            f"✅ Panel de tickets publicado en {destino.mention}",
            ephemeral=True,
        )

    print("[panel_tickets_ui] OK — /panel_tickets elegante")
