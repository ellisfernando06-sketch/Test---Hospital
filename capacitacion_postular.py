# -*- coding: utf-8 -*
"""
capacitacion_postular.py — Botón Postularse en /capacitacion programar (y reanuncios).
"""
from __future__ import annotations

import traceback
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands


class PostularCapView(discord.ui.View):
    """Vista persistente: custom_id incluye el id de la capacitación."""

    def __init__(self, cap_id: int = 0):
        super().__init__(timeout=None)
        self.cap_id = int(cap_id or 0)
        # Botones con custom_id fijo para persistencia
        if self.cap_id:
            for child in self.children:
                if isinstance(child, discord.ui.Button) and child.custom_id:
                    if child.custom_id.startswith("cap_postular"):
                        child.custom_id = f"cap_postular:{self.cap_id}"
                    elif child.custom_id.startswith("cap_despostular"):
                        child.custom_id = f"cap_despostular:{self.cap_id}"
                    elif child.custom_id.startswith("cap_ver_postulados"):
                        child.custom_id = f"cap_ver_postulados:{self.cap_id}"

    @discord.ui.button(
        label="📝 Postularse",
        style=discord.ButtonStyle.success,
        custom_id="cap_postular:0",
    )
    async def postular_btn(self, inter: discord.Interaction, button: discord.ui.Button):
        cap_id = self._id_desde(button.custom_id) or self.cap_id
        if not cap_id:
            return await inter.response.send_message("❌ Capacitación no identificada.", ephemeral=True)
        import capacitaciones as cap
        ok, msg = cap.postular(cap_id, inter.user.id)
        c = cap.obtener(cap_id)
        titulo = (c or {}).get("titulo", f"#{cap_id}")
        if ok:
            await inter.response.send_message(
                f"✅ Te postulaste a **{titulo}**.\n{msg}",
                ephemeral=True,
            )
        else:
            await inter.response.send_message(f"⚠️ {msg}", ephemeral=True)

    @discord.ui.button(
        label="Retirar postulación",
        style=discord.ButtonStyle.secondary,
        custom_id="cap_despostular:0",
    )
    async def despostular_btn(self, inter: discord.Interaction, button: discord.ui.Button):
        cap_id = self._id_desde(button.custom_id) or self.cap_id
        if not cap_id:
            return await inter.response.send_message("❌ Capacitación no identificada.", ephemeral=True)
        import capacitaciones as cap
        ok, msg = cap.despostular(cap_id, inter.user.id)
        await inter.response.send_message(
            f"{'✅' if ok else '⚠️'} {msg}",
            ephemeral=True,
        )

    @discord.ui.button(
        label="👥 Ver postulados",
        style=discord.ButtonStyle.primary,
        custom_id="cap_ver_postulados:0",
    )
    async def ver_btn(self, inter: discord.Interaction, button: discord.ui.Button):
        cap_id = self._id_desde(button.custom_id) or self.cap_id
        if not cap_id:
            return await inter.response.send_message("❌ Capacitación no identificada.", ephemeral=True)
        import capacitaciones as cap
        ids = cap.postulados_de(cap_id)
        c = cap.obtener(cap_id)
        titulo = (c or {}).get("titulo", f"#{cap_id}")
        if not ids:
            return await inter.response.send_message(
                f"Nadie se ha postulado aún a **{titulo}**.",
                ephemeral=True,
            )
        menciones = []
        guild = inter.guild
        for uid in ids[:40]:
            m = guild.get_member(uid) if guild else None
            menciones.append(m.mention if m else f"<@{uid}>")
        extra = f"\n… y {len(ids) - 40} más" if len(ids) > 40 else ""
        await inter.response.send_message(
            f"👥 **Postulados a {titulo}** ({len(ids)}):\n" + ", ".join(menciones) + extra,
            ephemeral=True,
        )

    @staticmethod
    def _id_desde(custom_id: Optional[str]) -> int:
        if not custom_id or ":" not in custom_id:
            return 0
        try:
            return int(custom_id.split(":")[-1])
        except Exception:
            return 0


def _view_for(cap_id: int) -> PostularCapView:
    return PostularCapView(cap_id)


def registrar(bot: commands.Bot) -> None:
    print("[capacitacion_postular] cargando…")
    try:
        # Vista genérica para botones persistentes tras reinicio
        if not getattr(bot, "_cap_postular_view_ok", False):
            bot.add_view(PostularCapView(0))
            bot._cap_postular_view_ok = True

        _parchar_programar(bot)
        print("[capacitacion_postular] ✓ OK")
    except Exception:
        print("[capacitacion_postular] ✗ error (bot sigue):")
        traceback.print_exc()


def _parchar_programar(bot: commands.Bot) -> None:
    import capacitaciones
    import config
    import permisos
    import roles_store

    grupo = bot.tree.get_command("capacitacion")
    if grupo is None:
        # Crear grupo si el núcleo no lo cargó
        grupo = app_commands.Group(name="capacitacion", description="Sistema de capacitaciones del personal")
        bot.tree.add_command(grupo)
    else:
        try:
            grupo.remove_command("programar")
        except Exception:
            pass

    # Choices de departamento (igual que el núcleo)
    try:
        depto_choices = [
            app_commands.Choice(name=d["nombre"], value=s)
            for s, d in config.DEPARTAMENTOS.items()
        ]
    except Exception:
        depto_choices = []

    @grupo.command(name="programar", description="Programa una capacitación, la anuncia y permite postularse")
    @app_commands.describe(
        titulo="Título",
        fecha_hora="Fecha y hora",
        departamento="Departamento destinatario (opcional)",
        descripcion="Descripción",
    )
    @app_commands.choices(departamento=depto_choices)
    async def capacitacion_programar(
        interaction: discord.Interaction,
        titulo: str,
        fecha_hora: str,
        descripcion: str,
        departamento: app_commands.Choice[str] = None,
    ):
        if not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("❌ Solo en servidor.", ephemeral=True)
        if not permisos.member_tiene_alguna_key(
            interaction.user, "SUPERVISOR", "JEFE_DEPARTAMENTO", "DIRECTOR", "OWNER", "CO_OWNER"
        ):
            raise permisos.SinPermiso(["SUPERVISOR", "JEFE_DEPARTAMENTO", "DIRECTOR", "OWNER"])

        slug = departamento.value if departamento else ""
        cap_id = capacitaciones.programar(titulo, fecha_hora, slug, descripcion, interaction.user.id)

        try:
            from estilos import crear_embed
            embed = crear_embed("info", f"🎓 Capacitación #{cap_id}: {titulo}", descripcion, autor=interaction.user)
        except Exception:
            embed = discord.Embed(
                title=f"🎓 Capacitación #{cap_id}: {titulo}",
                description=descripcion or "—",
                color=0x3498DB,
            )
            embed.set_author(name=str(interaction.user))

        embed.add_field(name="Fecha y hora", value=fecha_hora, inline=True)
        embed.add_field(name="ID", value=str(cap_id), inline=True)

        mencion = ""
        if slug and slug in getattr(config, "DEPARTAMENTOS", {}):
            ids = roles_store.escalafon_ids(slug, len(config.DEPARTAMENTOS[slug]["escalafon_nombres"]))
            roles_m = [interaction.guild.get_role(i) for i in ids if i]
            roles_m = [r for r in roles_m if r]
            mencion = " ".join(r.mention for r in roles_m)
            embed.add_field(name="Departamento", value=config.DEPARTAMENTOS[slug]["nombre"], inline=True)
        else:
            embed.add_field(name="Departamento", value="General / Todo el personal", inline=True)

        embed.add_field(
            name="Postulación",
            value="Pulsa **📝 Postularse** para inscribirte.",
            inline=False,
        )
        embed.set_footer(text="Usa el botón para postularte · Ver postulados disponible para staff")

        view = _view_for(cap_id)
        await interaction.response.send_message(content=mencion or None, embed=embed, view=view)

        try:
            from estilos import enviar_log  # type: ignore
        except Exception:
            enviar_log = None
        # log opcional vía núcleo
        try:
            import bot_hospital  # noqa
        except Exception:
            pass
        # intentar enviar_log del núcleo si existe en globals del bot module
        try:
            # hospital_core remote defines enviar_log
            mod = __import__("hospital_core")
        except Exception:
            pass

    # Reanunciar capacitación existente con botón
    try:
        grupo.remove_command("anunciar")
    except Exception:
        pass

    @grupo.command(name="anunciar", description="Reenvía el anuncio de una capacitación con botón Postularse")
    @app_commands.describe(id_capacitacion="ID de la capacitación programada")
    async def capacitacion_anunciar(interaction: discord.Interaction, id_capacitacion: int):
        if not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("❌ Solo en servidor.", ephemeral=True)
        if not permisos.member_tiene_alguna_key(
            interaction.user, "SUPERVISOR", "JEFE_DEPARTAMENTO", "DIRECTOR", "OWNER", "CO_OWNER"
        ):
            raise permisos.SinPermiso(["SUPERVISOR", "JEFE_DEPARTAMENTO", "DIRECTOR", "OWNER"])

        c = capacitaciones.obtener(id_capacitacion)
        if not c:
            return await interaction.response.send_message(
                f"❌ No existe la capacitación #{id_capacitacion}.",
                ephemeral=True,
            )

        embed = discord.Embed(
            title=f"🎓 Capacitación #{c['id']}: {c.get('titulo', '—')}",
            description=c.get("descripcion") or "—",
            color=0x3498DB,
        )
        embed.add_field(name="Fecha y hora", value=c.get("fecha_hora") or "—", inline=True)
        embed.add_field(name="Postulados", value=str(len(c.get("postulados") or [])), inline=True)
        slug = c.get("departamento_slug") or ""
        if slug and slug in getattr(config, "DEPARTAMENTOS", {}):
            embed.add_field(name="Departamento", value=config.DEPARTAMENTOS[slug]["nombre"], inline=True)
        else:
            embed.add_field(name="Departamento", value="General", inline=True)
        embed.add_field(
            name="Postulación",
            value="Pulsa **📝 Postularse** para inscribirte.",
            inline=False,
        )

        view = _view_for(int(c["id"]))
        await interaction.response.send_message(embed=embed, view=view)
