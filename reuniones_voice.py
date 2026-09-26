# -*- coding: utf-8 -*
"""reuniones_voice.py — citatorios/reuniones con VC elegible + Asamblea (carga segura)."""
from __future__ import annotations

import re
import traceback
from typing import Dict, List, Optional, Set

import discord
from discord import app_commands
from discord.ext import commands

_CITAS: Dict[str, dict] = {}
_REU_DIR: Dict[int, dict] = {}
_REU_DEPT: Dict[int, dict] = {}


def _parse_uid(texto: str) -> Optional[int]:
    if not texto:
        return None
    m = re.search(r"(\d{15,20})", str(texto))
    return int(m.group(1)) if m else None


async def _asegurar_permisos_vc(guild: discord.Guild, vc: discord.VoiceChannel, member: discord.Member) -> None:
    try:
        overwrites = vc.overwrites_for(member)
        overwrites.connect = True
        overwrites.speak = True
        overwrites.view_channel = True
        await vc.set_permissions(member, overwrite=overwrites, reason="Citatorio/reunión confirmada")
    except Exception as e:
        print(f"[reuniones_voice] permisos VC: {e}")


async def _mover(member: discord.Member, vc: discord.VoiceChannel):
    try:
        await _asegurar_permisos_vc(member.guild, vc, member)
        if not member.voice or not member.voice.channel:
            return False, (
                f"No estás en ningún canal de voz. "
                f"Entra a **cualquier** canal de voz y vuelve a pulsar **Confirmar**, "
                f"o entra directo a **{vc.name**."
            )
        if member.voice.channel.id == vc.id:
            return True, f"Ya estabas en **{vc.name}**."
        await member.move_to(vc, reason="Confirmación citatorio/reunión")
        return True, f"Movido a **{vc.name}**."
    except discord.Forbidden:
        return False, "No tengo permiso de **Mover miembros**. Revisa el rol del bot."
    except Exception as e:
        print(f"[reuniones_voice] mover: {e}")
        return False, f"Error al mover: `{e}`"


async def _mover_lista(guild, uids: Set[int], vc: discord.VoiceChannel) -> List[str]:
    out = []
    if not guild or not vc:
        return out
    for uid in uids:
        m = guild.get_member(uid)
        if not m:
            continue
        ok, _ = await _mover(m, vc)
        if ok:
            out.append(m.mention)
    return out


class ConfirmarCitaView(discord.ui.View):
    def __init__(self, cita_id: str, citado_id: int):
        super().__init__(timeout=7200)
        self.cita_id = cita_id
        self.citado_id = citado_id

    async def interaction_check(self, inter: discord.Interaction) -> bool:
        data = _CITAS.get(self.cita_id) or {}
        allowed = {self.citado_id}
        for k in ("autor_id", "aprobador_id"):
            if data.get(k):
                try:
                    allowed.add(int(data[k]))
                except Exception:
                    pass
        if inter.user.id not in allowed and inter.user.id != self.citado_id:
            await inter.response.send_message(
                "❌ Solo el citado (o el encargado) puede confirmar.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="✅ Confirmar y unirme al canal", style=discord.ButtonStyle.success)
    async def ok(self, inter: discord.Interaction, btn: discord.ui.Button):
        data = _CITAS.get(self.cita_id)
        if not data:
            for c in self.children:
                c.disabled = True
            await inter.response.edit_message(view=self)
            return await inter.followup.send("Esta cita ya no está pendiente.", ephemeral=True)

        guild = inter.guild or inter.client.get_guild(data.get("guild_id") or 0)
        if not guild:
            return await inter.response.send_message("❌ Servidor no encontrado.", ephemeral=True)

        vc_id = data.get("vc_id")
        try:
            vc = guild.get_channel(int(vc_id)) if vc_id else None
        except Exception:
            vc = None

        if not isinstance(vc, discord.VoiceChannel):
            return await inter.response.send_message(
                "❌ No encuentro el canal de voz de destino. Pide que reemitan el citatorio eligiendo el canal.",
                ephemeral=True,
            )

        mem = guild.get_member(inter.user.id)
        if not mem:
            return await inter.response.send_message("❌ No te encuentro en el servidor.", ephemeral=True)

        await inter.response.defer(ephemeral=True)
        ok, msg = await _mover(mem, vc)

        if ok:
            _CITAS.pop(self.cita_id, None)
            for c in self.children:
                c.disabled = True
            try:
                await inter.message.edit(view=self)
            except Exception:
                pass
            extras = []
            for k in ("aprobador_id", "autor_id"):
                try:
                    oid = int(data.get(k) or 0)
                except Exception:
                    oid = 0
                if oid and oid != inter.user.id:
                    other = guild.get_member(oid)
                    if other:
                        ok2, _ = await _mover(other, vc)
                        if ok2:
                            extras.append(other.mention)
            extra_txt = f" También: {', '.join(extras)}." if extras else ""
            await inter.followup.send(f"✅ {msg}{extra_txt}", ephemeral=True)
            try:
                ch = inter.client.get_channel(data.get("channel_id") or 0)
                if ch:
                    await ch.send(
                        f"✅ {inter.user.mention} **confirmó** y fue unido a **{vc.name}**."
                        + (f" (+ {', '.join(extras)})" if extras else "")
                    )
            except Exception:
                pass
        else:
            await inter.followup.send(
                f"⚠️ {msg}\n\n"
                f"1. Entra a un canal de voz (o a {vc.mention})\n"
                f"2. Vuelve a pulsar **✅ Confirmar y unirme al canal**",
                ephemeral=True,
            )

    @discord.ui.button(label="❌ No puedo asistir", style=discord.ButtonStyle.danger)
    async def no(self, inter: discord.Interaction, btn: discord.ui.Button):
        if inter.user.id != self.citado_id:
            return await inter.response.send_message("❌ Solo el citado puede rechazar.", ephemeral=True)
        _CITAS.pop(self.cita_id, None)
        for c in self.children:
            c.disabled = True
        await inter.response.edit_message(view=self)
        await inter.followup.send("Indicaste que no puedes asistir.", ephemeral=True)


async def _on_citatorio_ok(inter: discord.Interaction, info: dict):
    datos = info.get("datos") or {}
    uid = _parse_uid(datos.get("citado") or "")
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
        mem = inter.guild.get_member(uid)
        if mem:
            await _asegurar_permisos_vc(inter.guild, vc, mem)

    cid = f"cita_{uid}_{info.get('fecha', '')}_{vc_id_int}"
    _CITAS[cid] = {
        "guild_id": inter.guild.id,
        "channel_id": inter.channel_id if inter.channel else 0,
        "motivo": datos.get("motivo", ""),
        "citado_id": uid,
        "vc_id": str(vc_id_int) if vc_id_int else datos.get("vc_id"),
        "vc_name": vc_name,
        "autor_id": info.get("autor_id"),
        "aprobador_id": inter.user.id,
    }

    emb = discord.Embed(
        title="📢 Citatorio APROBADO — confirma y únete",
        description=(
            f"**Motivo:** {datos.get('motivo', '—')}\n"
            f"**Fecha:** {datos.get('fecha', '—')}\n"
            f"**Canal de voz:** **{vc_name}**"
            + (f" ({vc.mention})" if isinstance(vc, discord.VoiceChannel) else "")
            + "\n\n"
            f"1. Entra a un canal de voz (o al de destino)\n"
            f"2. Pulsa **✅ Confirmar y unirme al canal**\n"
            f"→ El bot te moverá automáticamente."
        ),
        color=0x2ECC71,
    )
    emb.set_footer(text="Discord solo permite moverte si ya estás conectado a voz.")
    view = ConfirmarCitaView(cid, uid)
    mem = inter.guild.get_member(uid)

    if mem:
        try:
            await mem.send(embed=emb, view=view)
        except Exception:
            pass

    try:
        await inter.followup.send(
            content=f"{mem.mention if mem else f'<@{uid}>'} — citatorio **aprobado**. Confirma para unirte al canal:",
            embed=emb,
            view=view,
        )
    except Exception as e:
        print(f"[reuniones_voice] followup citatorio: {e}")


class ConfirmarDirView(discord.ui.View):
    def __init__(self, mid: int, esperados: Set[int], vc_id: int):
        super().__init__(timeout=7200)
        self.mid = mid
        self.esperados = esperados
        self.vc_id = vc_id
        self.ok: Set[int] = set()

    @discord.ui.button(label="✅ Confirmo y úneme", style=discord.ButtonStyle.success)
    async def confirmar(self, inter: discord.Interaction, btn: discord.ui.Button):
        try:
            import permisos
            puede = permisos.member_tiene_alguna_key(inter.user, "DIRECTOR", "OWNER", "CO_OWNER")
        except Exception:
            puede = inter.user.id in self.esperados
        if not isinstance(inter.user, discord.Member) or not (puede or inter.user.id in self.esperados):
            return await inter.response.send_message("❌ Solo Directores.", ephemeral=True)

        self.ok.add(inter.user.id)
        guild = inter.guild
        vc = guild.get_channel(self.vc_id) if guild else None

        movi_ya = ""
        if isinstance(vc, discord.VoiceChannel) and isinstance(inter.user, discord.Member):
            ok, msg = await _mover(inter.user, vc)
            movi_ya = f"\n→ {msg}"

        texto = (
            f"**Confirmados ({len(self.ok)}/{len(self.esperados)}):** "
            + ", ".join(f"<@{u}>" for u in self.ok)
        )
        emb = inter.message.embeds[0] if inter.message.embeds else discord.Embed()
        for i, f in enumerate(emb.fields):
            if f.name == "Asistencia":
                emb.set_field_at(i, name="Asistencia", value=texto, inline=False)
                break
        else:
            emb.add_field(name="Asistencia", value=texto, inline=False)

        await inter.response.edit_message(embed=emb)
        if movi_ya:
            try:
                await inter.followup.send(f"✅ Confirmado.{movi_ya}", ephemeral=True)
            except Exception:
                pass

        if self.esperados and self.ok >= self.esperados:
            for c in self.children:
                c.disabled = True
            await inter.message.edit(view=self)
            movidos = []
            if isinstance(vc, discord.VoiceChannel):
                movidos = await _mover_lista(guild, self.ok, vc)
            nom = vc.name if isinstance(vc, discord.VoiceChannel) else "canal"
            await inter.followup.send(
                f"🏛️ **Todos confirmaron.** "
                + (f"En **{nom}**: {', '.join(movidos)}" if movidos else f"Entren a **{nom}** (deben estar en voz para ser movidos).")
            )
            _REU_DIR.pop(self.mid, None)


class VotoReunionView(discord.ui.View):
    def __init__(self, mid: int, minimo: int, vc_id: int, modo: str, autorizados: Set[int]):
        super().__init__(timeout=7200)
        self.mid = mid
        self.minimo = max(1, minimo)
        self.vc_id = vc_id
        self.modo = modo
        self.autorizados = autorizados
        self.votos: Set[int] = set()

    def _puede(self, m: discord.Member) -> bool:
        if self.modo == "asamblea":
            return True
        if m.id in self.autorizados:
            return True
        try:
            import permisos
            if self.modo == "general":
                return permisos.member_tiene_alguna_key(m, "DIRECTOR", "OWNER", "CO_OWNER", "JEFE_DEPARTAMENTO")
            return permisos.member_tiene_alguna_key(m, "JEFE_DEPARTAMENTO", "DIRECTOR", "OWNER", "CO_OWNER", "SUPERVISOR")
        except Exception:
            return False

    @discord.ui.button(label="✅ Confirmo y úneme", style=discord.ButtonStyle.success)
    async def votar(self, inter: discord.Interaction, btn: discord.ui.Button):
        if not isinstance(inter.user, discord.Member) or not self._puede(inter.user):
            return await inter.response.send_message("❌ Sin permiso para votar.", ephemeral=True)

        self.votos.add(inter.user.id)
        guild = inter.guild
        vc = guild.get_channel(self.vc_id) if guild else None

        movi_ya = ""
        if isinstance(vc, discord.VoiceChannel):
            ok, msg = await _mover(inter.user, vc)
            movi_ya = f"\n→ {msg}"

        texto = (
            f"**Confirmados: {len(self.votos)}/{self.minimo}**\n"
            + ", ".join(f"<@{u}>" for u in list(self.votos)[:20])
        )
        emb = inter.message.embeds[0] if inter.message.embeds else discord.Embed()
        for i, f in enumerate(emb.fields):
            if f.name == "Confirmaciones":
                emb.set_field_at(i, name="Confirmaciones", value=texto, inline=False)
                break
        else:
            emb.add_field(name="Confirmaciones", value=texto, inline=False)

        await inter.response.edit_message(embed=emb)
        if movi_ya:
            try:
                await inter.followup.send(f"✅ Confirmado.{movi_ya}", ephemeral=True)
            except Exception:
                pass

        if len(self.votos) >= self.minimo:
            for c in self.children:
                c.disabled = True
            await inter.message.edit(view=self)
            movidos = []
            if isinstance(vc, discord.VoiceChannel):
                movidos = await _mover_lista(guild, self.votos, vc)
            nom = vc.name if isinstance(vc, discord.VoiceChannel) else "canal"
            tipo = {"asamblea": "Asamblea", "general": "Reunión General", "dept": "Reunión Departamental"}.get(self.modo, "Reunión")
            await inter.followup.send(
                f"📅 **Mínimo alcanzado ({len(self.votos)}/{self.minimo}) — {tipo}.** "
                + (f"En **{nom}**: {', '.join(movidos)}" if movidos else f"Entren a **{nom}** (deben estar en voz).")
            )
            _REU_DEPT.pop(self.mid, None)


def registrar(bot: commands.Bot) -> None:
    print("[reuniones_voice] cargando…")
    try:
        _registrar_interno(bot)
        print("[reuniones_voice] ✓ OK")
    except Exception:
        print("[reuniones_voice] ✗ error (bot sigue online):")
        traceback.print_exc()


def _registrar_interno(bot: commands.Bot) -> None:
    import config
    import permisos
    import roles_store

    async def _emitir(inter, direccion, key_apr, canal_key, usuario, motivo, fecha_hora, canal_voz, lugar="", obs=""):
        try:
            from estilos import crear_embed
            emb = crear_embed("aviso", f"📢 Citatorio — {direccion}", motivo, autor=inter.user)
        except Exception:
            emb = discord.Embed(title=f"📢 Citatorio — {direccion}", description=motivo, color=0xF39C12)
        emb.add_field(name="Citado", value=usuario.mention, inline=True)
        emb.add_field(name="Fecha/hora", value=fecha_hora, inline=True)
        emb.add_field(name="Canal de voz", value=canal_voz.mention, inline=True)
        if lugar:
            emb.add_field(name="Lugar", value=lugar, inline=True)
        if obs:
            emb.add_field(name="Observaciones", value=obs[:500], inline=False)
        emb.add_field(name="Estado", value="⏳ Pendiente de autorización", inline=False)
        import solicitudes as sol
        await sol.enviar_solicitud_con_aprobacion(
            inter, key_aprobador=key_apr, embed=emb,
            tipo=f"citatorio_{direccion.lower().replace(' ', '_')}",
            datos={
                "citado": str(usuario.id), "motivo": motivo, "fecha": fecha_hora,
                "lugar": lugar or "", "vc_id": str(canal_voz.id), "vc_name": canal_voz.name,
            },
            canal_key=canal_key, on_approve=_on_citatorio_ok,
        )
        await inter.response.send_message(
            f"✅ Citatorio enviado a **{direccion}**.\n"
            f"Al **aprobar** + **confirmar**, se unirá a **{canal_voz.name}**.\n"
            f"⚠️ El citado debe estar conectado a voz para poder ser movido.",
            ephemeral=True,
        )

    specs = [
        ("citatorio_general", "Director General", "DIRECTOR_GENERAL", "citatorio_general",
         ("DIRECTOR_GENERAL", "OWNER", "CO_OWNER")),
        ("citatorio_disciplina", "Director de Disciplina", "DIRECTOR_DISCIPLINA", "citatorio_disciplina",
         ("DIRECTOR_DISCIPLINA", "OWNER", "CO_OWNER")),
        ("citatorio_admin", "Director Administrativo", "DIRECTOR_ADMINISTRATIVO", "citatorio_admin",
         ("DIRECTOR_ADMINISTRATIVO", "OWNER", "CO_OWNER")),
    ]

    for nombre, direccion, key, ckey, keys_ok in specs:
        try:
            bot.tree.remove_command(nombre)
        except Exception:
            pass

        def make(n=nombre, d=direccion, k=key, ck=ckey, ko=keys_ok):
            @bot.tree.command(name=n, description=f"Citatorio {d} (elige canal de voz)")
            @app_commands.describe(
                usuario="Persona citada", motivo="Motivo", fecha_hora="Fecha y hora",
                canal_voz="Canal de voz de destino", lugar="Lugar (opcional)", observaciones="Obs. (opcional)",
            )
            async def cmd(
                inter: discord.Interaction, usuario: discord.Member, motivo: str, fecha_hora: str,
                canal_voz: discord.VoiceChannel, lugar: str = "", observaciones: str = "",
            ):
                if not permisos.member_tiene_alguna_key(inter.user, *ko):
                    raise permisos.SinPermiso(list(ko))
                await _emitir(inter, d, k, ck, usuario, motivo, fecha_hora, canal_voz, lugar, observaciones)
            return cmd
        make()

    try:
        bot.tree.remove_command("convocar_directores")
    except Exception:
        pass

    @bot.tree.command(name="convocar_directores", description="Reunión de Directores (elige canal de voz)")
    @app_commands.describe(titulo="Motivo", fecha_hora="Fecha y hora", canal_voz="Canal de voz destino", detalles="Detalles")
    async def convocar_directores(
        inter: discord.Interaction, titulo: str, fecha_hora: str,
        canal_voz: discord.VoiceChannel, detalles: str = "",
    ):
        if not isinstance(inter.user, discord.Member):
            return
        if not permisos.member_tiene_alguna_key(inter.user, "OWNER", "CO_OWNER", "DIRECTOR"):
            raise permisos.SinPermiso(["OWNER", "CO_OWNER", "DIRECTOR"])
        esperados: Set[int] = set()
        menciones = []
        for dk in list(getattr(config, "DIRECTOR_KEYS", [])) + ["OWNER", "CO_OWNER"]:
            rid = roles_store.obtener_id_key(dk)
            if rid:
                rol = inter.guild.get_role(rid)
                if rol:
                    if dk.startswith("DIRECTOR"):
                        menciones.append(rol.mention)
                    for m in rol.members:
                        esperados.add(m.id)
        emb = discord.Embed(title=f"🏛️ Directores: {titulo}", description=detalles or "—", color=0x2C3E50)
        emb.add_field(name="Fecha y hora", value=fecha_hora, inline=True)
        emb.add_field(name="Canal de voz", value=canal_voz.mention, inline=True)
        emb.add_field(name="Asistencia", value=f"**Confirmados (0/{len(esperados)}):** —", inline=False)
        emb.set_footer(text=f"Al confirmar → se intenta unir a {canal_voz.name} (deben estar en voz)")
        await inter.response.send_message(content=" ".join(menciones) or None, embed=emb)
        msg = await inter.original_response()
        await msg.edit(view=ConfirmarDirView(msg.id, esperados, canal_voz.id))
        _REU_DIR[msg.id] = {"esperados": list(esperados)}

    try:
        bot.tree.remove_command("convocar_reunion_departamento")
    except Exception:
        pass

    choices = [app_commands.Choice(name=d["nombre"], value=s) for s, d in config.DEPARTAMENTOS.items()]
    choices.append(app_commands.Choice(name="🏛️ Reunión General (Directores)", value="__general__"))
    choices.append(app_commands.Choice(name="📣 Asamblea del Servidor (todos)", value="__asamblea__"))

    @bot.tree.command(name="convocar_reunion_departamento", description="Reunión / Asamblea (elige canal de voz)")
    @app_commands.describe(
        departamento="Depto, General o Asamblea", titulo="Motivo", fecha_hora="Fecha y hora",
        canal_voz="Canal de voz destino", minimo_confirmaciones="Mínimo (default 2)", detalles="Detalles",
    )
    @app_commands.choices(departamento=choices)
    async def convocar_reunion(
        inter: discord.Interaction,
        departamento: app_commands.Choice[str],
        titulo: str, fecha_hora: str, canal_voz: discord.VoiceChannel,
        minimo_confirmaciones: app_commands.Range[int, 1, 200] = 2, detalles: str = "",
    ):
        if not isinstance(inter.user, discord.Member) or not inter.guild:
            return
        slug = departamento.value
        es_gen = slug == "__general__"
        es_asa = slug == "__asamblea__"
        autorizados: Set[int] = set()
        menciones = []
        modo = "dept"
        color = 0x3498DB
        nombre = f"Reunión de {departamento.name}"

        if es_asa:
            if not permisos.member_tiene_alguna_key(inter.user, "OWNER", "CO_OWNER", "DIRECTOR", "JEFE_DEPARTAMENTO", "SUPERVISOR"):
                raise permisos.SinPermiso(["OWNER", "CO_OWNER", "DIRECTOR", "JEFE_DEPARTAMENTO", "SUPERVISOR"])
            menciones = ["@everyone"]
            nombre = "Asamblea del Servidor"
            color = 0xE67E22
            modo = "asamblea"
        elif es_gen:
            if not permisos.member_tiene_alguna_key(inter.user, "OWNER", "CO_OWNER", "DIRECTOR"):
                raise permisos.SinPermiso(["OWNER", "CO_OWNER", "DIRECTOR"])
            for dk in list(getattr(config, "DIRECTOR_KEYS", [])) + ["OWNER", "CO_OWNER", "JEFE_DEPARTAMENTO"]:
                rid = roles_store.obtener_id_key(dk)
                if rid:
                    rol = inter.guild.get_role(rid)
                    if rol:
                        if dk.startswith("DIRECTOR") or dk in ("OWNER", "CO_OWNER"):
                            menciones.append(rol.mention)
                        for m in rol.members:
                            autorizados.add(m.id)
            nombre = "Reunión General"
            color = 0x2C3E50
            modo = "general"
        else:
            depto = config.DEPARTAMENTOS.get(slug)
            if not depto:
                return await inter.response.send_message("❌ Depto inválido.", ephemeral=True)
            dir_key = depto["director_key"]
            ok = (
                permisos.member_tiene_alguna_key(inter.user, dir_key, "OWNER", "CO_OWNER")
                or (permisos.member_tiene_alguna_key(inter.user, "JEFE_DEPARTAMENTO", "SUPERVISOR")
                    and permisos.departamento_del_member(inter.user) == slug)
            )
            if not ok:
                raise permisos.SinPermiso([dir_key, "JEFE_DEPARTAMENTO", "SUPERVISOR"])
            ids = roles_store.escalafon_ids(slug, len(depto["escalafon_nombres"]))
            for i in ids:
                r = inter.guild.get_role(i) if i else None
                if r:
                    menciones.append(r.mention)
            for k in (dir_key, "JEFE_DEPARTAMENTO"):
                rid = roles_store.obtener_id_key(k)
                if rid:
                    rol = inter.guild.get_role(rid)
                    if rol:
                        for m in rol.members:
                            autorizados.add(m.id)

        emb = discord.Embed(title=f"📅 {nombre}: {titulo}", description=detalles or "—", color=color)
        emb.add_field(name="Fecha y hora", value=fecha_hora, inline=True)
        emb.add_field(name="Canal de voz", value=canal_voz.mention, inline=True)
        emb.add_field(name="Mínimo", value=str(minimo_confirmaciones), inline=True)
        emb.add_field(name="Confirmaciones", value=f"**0/{minimo_confirmaciones}**", inline=False)
        emb.set_footer(text=f"Al confirmar → intenta unir a {canal_voz.name} (deben estar en voz)")
        allowed = discord.AllowedMentions(everyone=es_asa, roles=True, users=True)
        await inter.response.send_message(
            content=" ".join(menciones) if menciones else None, embed=emb, allowed_mentions=allowed,
        )
        msg = await inter.original_response()
        await msg.edit(view=VotoReunionView(msg.id, minimo_confirmaciones, canal_voz.id, modo, autorizados))
        _REU_DEPT[msg.id] = {"minimo": minimo_confirmaciones, "modo": modo}
