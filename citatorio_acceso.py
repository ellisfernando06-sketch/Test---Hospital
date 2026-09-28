# -*- coding: utf-8 -*-
"""
citatorio_acceso.py
===================
Tras aprobar un citatorio, el citado NO entra solo al canal.
1) Solicita acceso al encargado del citatorio.
2) El encargado aprueba.
3) El bot mueve al miembro al canal de voz adecuado.
"""
from __future__ import annotations

import traceback
from typing import Dict, Optional

import discord
from discord import ui
from discord.ext import commands

_SOLICITUDES: Dict[str, dict] = {}


def registrar(bot: commands.Bot) -> None:
    try:
        import reuniones_voice as RV
    except Exception:
        print("[citatorio_acceso] reuniones_voice no disponible")
        return

    class SolicitarAccesoView(ui.View):
        def __init__(self, cita_id: str, citado_id: int, encargado_id: int):
            super().__init__(timeout=7200)
            self.cita_id = cita_id
            self.citado_id = citado_id
            self.encargado_id = encargado_id

        @ui.button(
            label="📨 Solicitar acceso al canal",
            style=discord.ButtonStyle.primary,
            custom_id="cita_solicitar_acceso",
        )
        async def solicitar(self, inter: discord.Interaction, _btn: ui.Button):
            data = RV._CITAS.get(self.cita_id) or _SOLICITUDES.get(self.cita_id)
            if not data:
                return await inter.response.send_message(
                    "Esta cita ya no está pendiente.", ephemeral=True
                )
            if inter.user.id != self.citado_id:
                return await inter.response.send_message(
                    "❌ Solo la persona citada puede solicitar el acceso.", ephemeral=True
                )

            await inter.response.defer(ephemeral=True)
            guild = inter.guild or inter.client.get_guild(data.get("guild_id") or 0)
            if not guild:
                return await inter.followup.send("❌ Servidor no encontrado.", ephemeral=True)

            vc_id = data.get("vc_id")
            try:
                vc = guild.get_channel(int(vc_id)) if vc_id else None
            except Exception:
                vc = None
            vc_name = data.get("vc_name") or (vc.name if isinstance(vc, discord.VoiceChannel) else "canal")

            enc_id = int(data.get("autor_id") or data.get("aprobador_id") or self.encargado_id or 0)
            encargado = guild.get_member(enc_id) if enc_id else None

            sid = f"acc_{self.cita_id}_{inter.user.id}"
            _SOLICITUDES[sid] = {
                **data,
                "cita_id": self.cita_id,
                "solicitante_id": inter.user.id,
                "encargado_id": enc_id,
            }

            emb = discord.Embed(
                title="🚪 Solicitud de acceso al citatorio",
                description=(
                    f"**Solicitante:** {inter.user.mention}\n"
                    f"**Motivo del citatorio:** {data.get('motivo') or '—'}\n"
                    f"**Canal de destino:** **{vc_name}**\n\n"
                    f"Si apruebas, el bot **moverá** al miembro al canal indicado "
                    f"(debe estar conectado a un canal de voz)."
                ),
                color=0x3498DB,
            )
            view_apr = AprobarAccesoView(sid, inter.user.id, enc_id)

            enviado = False
            if encargado:
                try:
                    await encargado.send(embed=emb, view=view_apr)
                    enviado = True
                except Exception:
                    pass

            # Copia en el canal donde se aprobó el citatorio
            ch = None
            try:
                ch_id = data.get("channel_id")
                if ch_id:
                    ch = guild.get_channel(int(ch_id))
            except Exception:
                ch = None
            if ch:
                try:
                    mention = encargado.mention if encargado else f"<@{enc_id}>"
                    await ch.send(content=mention, embed=emb, view=view_apr)
                    enviado = True
                except Exception:
                    pass

            if enviado:
                await inter.followup.send(
                    f"✅ Solicitud de acceso enviada al **encargado del citatorio**."
                    + (f" ({encargado.mention})" if encargado else ""),
                    ephemeral=True,
                )
            else:
                await inter.followup.send(
                    "❌ No pude contactar al encargado (MD cerrado y sin canal).",
                    ephemeral=True,
                )

    class AprobarAccesoView(ui.View):
        def __init__(self, sid: str, citado_id: int, encargado_id: int):
            super().__init__(timeout=7200)
            self.sid = sid
            self.citado_id = citado_id
            self.encargado_id = encargado_id

        async def interaction_check(self, inter: discord.Interaction) -> bool:
            data = _SOLICITUDES.get(self.sid) or {}
            allowed = {self.encargado_id, int(data.get("autor_id") or 0), int(data.get("aprobador_id") or 0)}
            allowed.discard(0)
            if inter.user.id not in allowed:
                # permitir OWNER en servidor
                if isinstance(inter.user, discord.Member):
                    try:
                        import permisos

                        if permisos.member_tiene_alguna_key(inter.user, "OWNER", "CO_OWNER"):
                            return True
                    except Exception:
                        pass
                await inter.response.send_message(
                    "❌ Solo el **encargado del citatorio** puede aprobar el acceso.",
                    ephemeral=True,
                )
                return False
            return True

        @ui.button(label="✅ Aprobar y mover al canal", style=discord.ButtonStyle.success, custom_id="cita_acc_ok")
        async def aprobar(self, inter: discord.Interaction, _btn: ui.Button):
            data = _SOLICITUDES.get(self.sid)
            if not data:
                return await inter.response.send_message("Solicitud ya resuelta.", ephemeral=True)

            await inter.response.defer(ephemeral=True)
            guild = inter.guild or inter.client.get_guild(data.get("guild_id") or 0)
            if not guild:
                return await inter.followup.send("❌ Servidor no encontrado.", ephemeral=True)

            uid = int(data.get("solicitante_id") or data.get("citado_id") or self.citado_id)
            mem = guild.get_member(uid)
            if not mem:
                return await inter.followup.send("❌ Miembro no encontrado.", ephemeral=True)

            vc = None
            try:
                vc = guild.get_channel(int(data.get("vc_id") or 0))
            except Exception:
                vc = None
            if not isinstance(vc, discord.VoiceChannel):
                return await inter.followup.send(
                    "❌ No encuentro el canal de voz de destino.", ephemeral=True
                )

            ok, msg = await RV._mover(mem, vc)
            if ok:
                _SOLICITUDES.pop(self.sid, None)
                cita_id = data.get("cita_id")
                if cita_id:
                    RV._CITAS.pop(cita_id, None)
                for c in self.children:
                    c.disabled = True
                try:
                    await inter.message.edit(view=self)
                except Exception:
                    pass
                await inter.followup.send(
                    f"✅ Acceso aprobado. {mem.mention}: {msg}",
                    ephemeral=True,
                )
                try:
                    await mem.send(
                        f"✅ Tu acceso al citatorio fue **aprobado**. {msg}"
                    )
                except Exception:
                    pass
            else:
                await inter.followup.send(
                    f"⚠️ Aprobado, pero no se pudo mover: {msg}\n"
                    f"Pide a {mem.mention} que entre a **cualquier** canal de voz e inténtalo de nuevo.",
                    ephemeral=True,
                )

        @ui.button(label="❌ Negar acceso", style=discord.ButtonStyle.danger, custom_id="cita_acc_no")
        async def negar(self, inter: discord.Interaction, _btn: ui.Button):
            data = _SOLICITUDES.pop(self.sid, None) or {}
            await inter.response.send_message("❌ Acceso denegado.", ephemeral=True)
            uid = int(data.get("solicitante_id") or self.citado_id)
            guild = inter.guild or inter.client.get_guild(data.get("guild_id") or 0)
            mem = guild.get_member(uid) if guild else None
            if mem:
                try:
                    await mem.send("❌ Tu solicitud de acceso al citatorio fue **denegada** por el encargado.")
                except Exception:
                    pass
            for c in self.children:
                c.disabled = True
            try:
                await inter.message.edit(view=self)
            except Exception:
                pass

    async def _on_citatorio_ok(inter: discord.Interaction, info: dict):
        """Tras aprobar el citatorio: el citado debe pedir acceso; el encargado autoriza el movimiento."""
        datos = info.get("datos") or {}
        uid = RV._parse_uid(datos.get("citado") or "")
        if not uid or not inter.guild:
            try:
                await inter.followup.send("⚠️ Aprobado, pero no identifiqué al citado.", ephemeral=True)
            except Exception:
                pass
            return

        vc_id = datos.get("vc_id")
        vc_name = datos.get("vc_name") or "canal de voz"
        try:
            vc_id_int = int(vc_id) if vc_id else 0
        except Exception:
            vc_id_int = 0

        vc = inter.guild.get_channel(vc_id_int) if vc_id_int else None
        if isinstance(vc, discord.VoiceChannel):
            vc_name = vc.name

        autor_id = info.get("autor_id") or inter.user.id
        cid = f"cita_{uid}_{info.get('fecha', '')}_{vc_id_int}"
        RV._CITAS[cid] = {
            "guild_id": inter.guild.id,
            "channel_id": inter.channel_id if inter.channel else 0,
            "motivo": datos.get("motivo", ""),
            "citado_id": uid,
            "vc_id": str(vc_id_int) if vc_id_int else datos.get("vc_id"),
            "vc_name": vc_name,
            "autor_id": autor_id,
            "aprobador_id": inter.user.id,
        }

        emb = discord.Embed(
            title="📢 Citatorio APROBADO — solicita acceso",
            description=(
                f"**Motivo:** {datos.get('motivo', '—')}\n"
                f"**Fecha:** {datos.get('fecha', '—')}\n"
                f"**Canal de voz:** **{vc_name}**"
                + (f" ({vc.mention})" if isinstance(vc, discord.VoiceChannel) else "")
                + "\n\n"
                f"El bot **no** te mueve automáticamente.\n"
                f"1. Pulsa **📨 Solicitar acceso al canal**\n"
                f"2. El **encargado del citatorio** debe aprobar\n"
                f"3. Entra a un canal de voz; el bot te moverá al de destino"
            ),
            color=0x2ECC71,
        )
        emb.set_footer(text="Acceso controlado por el encargado del citatorio")
        view = SolicitarAccesoView(cid, uid, int(autor_id or 0))
        mem = inter.guild.get_member(uid)

        if mem:
            try:
                await mem.send(embed=emb, view=view)
            except Exception:
                pass

        try:
            await inter.followup.send(
                content=(
                    f"{mem.mention if mem else f'<@{uid}>'} — citatorio **aprobado**.\n"
                    f"Debe **solicitar acceso**; el encargado lo autoriza y el bot lo mueve."
                ),
                embed=emb,
                view=view,
            )
        except Exception as e:
            print("[citatorio_acceso] followup:", e)

    # Sustituir callback de aprobación
    RV._on_citatorio_ok = _on_citatorio_ok
    bot.add_view(SolicitarAccesoView("persist", 0, 0))
    bot.add_view(AprobarAccesoView("persist", 0, 0))
    print("[citatorio_acceso] OK — acceso solo con aprobación del encargado")
