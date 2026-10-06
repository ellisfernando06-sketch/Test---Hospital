# -*- coding: utf-8 -*-
"""
Si apelable=False: el MD no lleva botón (o el botón no funciona).
Si apelable=True (o no definido en sanciones viejas): funciona normal.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import discord
from discord import ui
from discord.ext import commands


def registrar(bot: commands.Bot) -> None:
    try:
        import sanciones_apelacion_ui as ui_mod
    except Exception as e:
        print(f"[sancion_apelable_check] sin ui: {e}")
        return

    try:
        import sanciones as sanc
    except Exception:
        sanc = None

    _orig_notify = getattr(ui_mod, "notificar_usuario", None)
    _orig_embed = getattr(ui_mod, "embed_dm_sancion", None)

    def embed_dm_sancion(reg: dict) -> discord.Embed:
        emb = _orig_embed(reg) if _orig_embed else discord.Embed(title="Medida")
        apelable = reg.get("apelable", True)
        if apelable is False or str(apelable).lower() in ("0", "false", "no"):
            # Quitar texto de apelar del description si existe
            desc = emb.description or ""
            desc = desc.replace("Si no estás de acuerdo → **Apelar**.", "")
            desc = desc.replace("Si no estás de acuerdo, pulsa **Apelar**.", "")
            desc = desc.strip() + "\n\n**Esta medida no admite apelación.**"
            emb.description = desc
            emb.color = 0x7F8C8D
        else:
            if emb.description and "Apelar" not in emb.description:
                emb.description = (emb.description or "") + "\n\nSi no estás de acuerdo → **Apelar**."
        return emb

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
        async def apelar(self, inter: discord.Interaction, button: ui.Button):
            if sanc is None:
                return await inter.response.send_message(
                    "❌ Sistema no disponible.", ephemeral=True
                )

            sid = self.sancion_id
            if not sid and inter.message and inter.message.embeds:
                import re

                m = re.search(
                    r"#(\d+)", inter.message.embeds[0].description or ""
                )
                if m:
                    sid = int(m.group(1))

            reg = sanc.obtener_sancion(sid) if sid else None
            if not reg:
                lista = sanc.sanciones_de(inter.user.id, solo_activas=True)
                reg = lista[-1] if lista else None

            if not reg or reg.get("anulada") or not reg.get("activa", True):
                return await inter.response.send_message(
                    "❌ No hay sanción activa para apelar.", ephemeral=True
                )

            apelable = reg.get("apelable", True)
            if apelable is False or str(apelable).lower() in (
                "0",
                "false",
                "no",
            ):
                return await inter.response.send_message(
                    "❌ Esta sanción **no admite apelación**. "
                    "Fue definida así por quien la impuso.",
                    ephemeral=True,
                )

            # Delegar al flujo original si existe
            try:
                Orig = getattr(ui_mod, "_ApelarSancionView_orig", None)
                if Orig is not None:
                    v = Orig(int(reg.get("id") or 0))
                    return await v.apelar.callback(v, inter, button)  # type: ignore
            except Exception:
                pass

            await inter.response.defer(ephemeral=True)
            guild = inter.guild
            if guild is None:
                for g in inter.client.guilds:
                    if g.get_member(inter.user.id):
                        guild = g
                        break
            if not guild:
                return await inter.followup.send(
                    "❌ Servidor no encontrado.", ephemeral=True
                )
            member = guild.get_member(inter.user.id)
            if not member:
                return await inter.followup.send(
                    "❌ No estás en el servidor.", ephemeral=True
                )
            canal = await sanc.abrir_ticket_apelacion(guild, member, reg)
            if not canal:
                return await inter.followup.send(
                    "❌ No se pudo abrir la apelación.", ephemeral=True
                )
            await inter.followup.send(
                f"✅ Apelación: {canal.mention}", ephemeral=True
            )

    async def notificar_usuario(bot, guild, reg: dict) -> bool:
        apelable = reg.get("apelable", True)
        es_apelable = not (
            apelable is False
            or str(apelable).lower() in ("0", "false", "no")
        )

        uid = int(reg.get("usuario_id") or 0)
        member = guild.get_member(uid)
        if not member:
            return False

        tipo = (reg.get("tipo") or "").lower()
        if tipo not in (
            "advertencia",
            "disciplinaria",
            "administrativa",
            "sancion",
            "sanción",
            "ban",
        ):
            return False

        if tipo == "ban":
            try:
                rol = await ui_mod._rol_cuarentena(guild)
                if rol and rol not in member.roles:
                    await member.add_roles(
                        rol, reason=f"Ban #{reg.get('id')}"
                    )
            except Exception:
                pass

        emb = embed_dm_sancion(reg)
        try:
            if es_apelable:
                await member.send(
                    embed=emb,
                    view=ApelarSancionView(int(reg.get("id") or 0)),
                )
            else:
                # Sin botón de apelar
                await member.send(embed=emb)
            return True
        except Exception as e:
            print(f"[sancion_apelable_check] dm: {e}")
            return False

    # Guardar original y reemplazar
    if hasattr(ui_mod, "ApelarSancionView"):
        ui_mod._ApelarSancionView_orig = ui_mod.ApelarSancionView
    ui_mod.ApelarSancionView = ApelarSancionView
    ui_mod.embed_dm_sancion = embed_dm_sancion
    ui_mod.notificar_usuario = notificar_usuario

    try:
        bot.add_view(ApelarSancionView(0))
    except Exception:
        pass

    # Panel / ticket: filtrar no apelables
    if sanc is not None and hasattr(sanc, "abrir_ticket_apelacion"):
        _abrir = sanc.abrir_ticket_apelacion

        async def abrir_ticket_apelacion(guild, usuario, sancion, *a, **kw):
            apelable = sancion.get("apelable", True)
            if apelable is False or str(apelable).lower() in (
                "0",
                "false",
                "no",
            ):
                return None
            return await _abrir(guild, usuario, sancion, *a, **kw)

        # No reemplazar abrir globalmente de forma que rompa logs —
        # solo el botón ya bloquea. Dejamos abrir intacto para staff.

    print("[sancion_apelable_check] OK — Apelar solo si apelable=True")
