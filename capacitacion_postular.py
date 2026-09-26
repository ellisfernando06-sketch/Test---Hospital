# -*- coding: utf-8 -*
"""
capacitacion_postular.py — Programar/anunciar con botón Postularse
y enlace a certificación del catálogo por rama.
"""
from __future__ import annotations

import re
import traceback
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands


def _cap_id_desde_mensaje(message: Optional[discord.Message]) -> int:
    if not message or not message.embeds:
        return 0
    emb = message.embeds[0]
    for f in emb.fields:
        if (f.name or "").strip().lower() == "id":
            try:
                return int(str(f.value).strip())
            except Exception:
                pass
    m = re.search(r"#(\d+)", emb.title or "")
    if m:
        return int(m.group(1))
    if emb.footer and emb.footer.text:
        m = re.search(r"id[=:\s]+(\d+)", emb.footer.text, re.I)
        if m:
            return int(m.group(1))
    return 0


class PostularCapView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 Postularse", style=discord.ButtonStyle.success, custom_id="cap_postular_btn")
    async def postular_btn(self, inter: discord.Interaction, button: discord.ui.Button):
        cap_id = _cap_id_desde_mensaje(inter.message)
        if not cap_id:
            return await inter.response.send_message(
                "❌ No pude identificar la capacitación. Usa `/capacitacion anunciar`.",
                ephemeral=True,
            )
        import capacitaciones as cap
        ok, msg = cap.postular(cap_id, inter.user.id)
        c = cap.obtener(cap_id)
        titulo = (c or {}).get("titulo", f"#{cap_id}")
        if ok:
            await inter.response.send_message(
                f"✅ Te postulaste a **{titulo}** (#{cap_id}).\n{msg}",
                ephemeral=True,
            )
        else:
            await inter.response.send_message(f"⚠️ {msg}", ephemeral=True)

    @discord.ui.button(label="Retirar postulación", style=discord.ButtonStyle.secondary, custom_id="cap_despostular_btn")
    async def despostular_btn(self, inter: discord.Interaction, button: discord.ui.Button):
        cap_id = _cap_id_desde_mensaje(inter.message)
        if not cap_id:
            return await inter.response.send_message("❌ Capacitación no identificada.", ephemeral=True)
        import capacitaciones as cap
        ok, msg = cap.despostular(cap_id, inter.user.id)
        await inter.response.send_message(f"{'✅' if ok else '⚠️'} {msg}", ephemeral=True)

    @discord.ui.button(label="👥 Ver postulados", style=discord.ButtonStyle.primary, custom_id="cap_ver_postulados_btn")
    async def ver_btn(self, inter: discord.Interaction, button: discord.ui.Button):
        cap_id = _cap_id_desde_mensaje(inter.message)
        if not cap_id:
            return await inter.response.send_message("❌ Capacitación no identificada.", ephemeral=True)
        import capacitaciones as cap
        ids = cap.postulados_de(cap_id)
        c = cap.obtener(cap_id)
        titulo = (c or {}).get("titulo", f"#{cap_id}")
        if not ids:
            return await inter.response.send_message(
                f"Nadie se ha postulado aún a **{titulo}**.", ephemeral=True
            )
        guild = inter.guild
        menciones = []
        for uid in ids[:40]:
            m = guild.get_member(uid) if guild else None
            menciones.append(m.mention if m else f"<@{uid}>")
        extra = f"\n… y {len(ids) - 40} más" if len(ids) > 40 else ""
        await inter.response.send_message(
            f"👥 **Postulados a {titulo}** ({len(ids)}):\n" + ", ".join(menciones) + extra,
            ephemeral=True,
        )


def registrar(bot: commands.Bot) -> None:
    print("[capacitacion_postular] cargando…")
    try:
        if not getattr(bot, "_cap_postular_view_ok", False):
            bot.add_view(PostularCapView())
            bot._cap_postular_view_ok = True
        _parchar_programar(bot)
        print("[capacitacion_postular] ✓ OK")
    except Exception:
        print("[capacitacion_postular] ✗ error:")
        traceback.print_exc()


def _parchar_programar(bot: commands.Bot) -> None:
    import capacitaciones
    import certificaciones_abiertas
    import config
    import permisos
    import roles_store

    certificaciones_abiertas.asegurar_defaults()

    grupo = bot.tree.get_command("capacitacion")
    if grupo is None:
        grupo = app_commands.Group(name="capacitacion", description="Sistema de capacitaciones del personal")
        bot.tree.add_command(grupo)
    else:
        for n in ("programar", "anunciar", "listar_certs"):
            try:
                grupo.remove_command(n)
            except Exception:
                pass

    try:
        depto_choices = [
            app_commands.Choice(name=d["nombre"], value=s)
            for s, d in config.DEPARTAMENTOS.items()
        ]
        depto_choices.insert(0, app_commands.Choice(name="General / Todas las ramas", value="general"))
    except Exception:
        depto_choices = [app_commands.Choice(name="General", value="general")]

    # Hasta 25 certificaciones en el choice de Discord
    certs = certificaciones_abiertas.listar_certificaciones_activas()[:25]
    cert_choices = [
        app_commands.Choice(
            name=f"{c['nombre'][:80]}" + (f" ({c.get('departamento','')})" if c.get("departamento") else ""),
            value=str(c["id"]),
        )
        for c in certs
    ]
    if not cert_choices:
        cert_choices = [app_commands.Choice(name="(Sin catálogo)", value="0")]

    @grupo.command(name="programar", description="Programa capacitación enlazada a una certificación y permite postularse")
    @app_commands.describe(
        titulo="Título de la capacitación",
        fecha_hora="Fecha y hora",
        certificacion="Certificación del catálogo a la que apunta",
        departamento="Rama / departamento destinatario",
        descripcion="Descripción",
    )
    @app_commands.choices(departamento=depto_choices, certificacion=cert_choices)
    async def capacitacion_programar(
        interaction: discord.Interaction,
        titulo: str,
        fecha_hora: str,
        certificacion: app_commands.Choice[str],
        descripcion: str = "",
        departamento: app_commands.Choice[str] = None,
    ):
        if not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("❌ Solo en servidor.", ephemeral=True)
        if not permisos.member_tiene_alguna_key(
            interaction.user, "SUPERVISOR", "JEFE_DEPARTAMENTO", "DIRECTOR", "OWNER", "CO_OWNER",
            "DIRECTOR_DOCENCIA", "ENCARGADO_AREA",
        ):
            raise permisos.SinPermiso(["SUPERVISOR", "JEFE_DEPARTAMENTO", "DIRECTOR", "OWNER"])

        slug = departamento.value if departamento else "general"
        cert_id = int(certificacion.value) if certificacion and certificacion.value != "0" else 0
        cert = certificaciones_abiertas.obtener_certificacion(cert_id) if cert_id else None

        # Si el título está vacío de sentido, usar nombre de cert
        if cert and (not titulo or titulo.strip().lower() in ("auto", "-", "x")):
            titulo = cert["nombre"]

        cap_id = capacitaciones.programar(
            titulo, fecha_hora, slug, descripcion or (cert.get("descripcion") if cert else ""),
            interaction.user.id, certificacion_id=cert_id,
        )

        embed = discord.Embed(
            title=f"🎓 Capacitación #{cap_id}: {titulo}",
            description=descripcion or (cert.get("descripcion") if cert else "—"),
            color=0x3498DB,
        )
        embed.add_field(name="Fecha y hora", value=fecha_hora, inline=True)
        embed.add_field(name="ID", value=str(cap_id), inline=True)
        if slug and slug in getattr(config, "DEPARTAMENTOS", {}):
            embed.add_field(name="Departamento", value=config.DEPARTAMENTOS[slug]["nombre"], inline=True)
        else:
            embed.add_field(name="Departamento", value="General / Todas las ramas", inline=True)

        if cert:
            embed.add_field(
                name="📜 Certificación vinculada",
                value=f"**{cert['nombre']}** (#{cert['id']})\n_{cert.get('descripcion') or ''}_",
                inline=False,
            )
            embed.add_field(
                name="Director de zona",
                value=cert.get("director_zona_key") or "DIRECTOR_DOCENCIA",
                inline=True,
            )

        embed.add_field(
            name="Postulación",
            value="Pulsa **📝 Postularse** para inscribirte. Al completar, se podrá **certificar** con `/certificar`.",
            inline=False,
        )
        embed.set_footer(text=f"id={cap_id} · cert={cert_id} · Botones activos")

        mencion = ""
        if slug and slug in getattr(config, "DEPARTAMENTOS", {}):
            ids = roles_store.escalafon_ids(slug, len(config.DEPARTAMENTOS[slug]["escalafon_nombres"]))
            roles_m = [interaction.guild.get_role(i) for i in ids if i]
            roles_m = [r for r in roles_m if r]
            mencion = " ".join(r.mention for r in roles_m)

        await interaction.response.send_message(
            content=mencion or None,
            embed=embed,
            view=PostularCapView(),
        )

    @grupo.command(name="anunciar", description="Reenvía anuncio de capacitación con botón Postularse")
    @app_commands.describe(id_capacitacion="ID de la capacitación programada")
    async def capacitacion_anunciar(interaction: discord.Interaction, id_capacitacion: int):
        if not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("❌ Solo en servidor.", ephemeral=True)
        if not permisos.member_tiene_alguna_key(
            interaction.user, "SUPERVISOR", "JEFE_DEPARTAMENTO", "DIRECTOR", "OWNER", "CO_OWNER", "DIRECTOR_DOCENCIA",
        ):
            raise permisos.SinPermiso(["SUPERVISOR", "JEFE_DEPARTAMENTO", "DIRECTOR", "OWNER"])

        c = capacitaciones.obtener(id_capacitacion)
        if not c:
            return await interaction.response.send_message(
                f"❌ No existe la capacitación #{id_capacitacion}.", ephemeral=True
            )

        cert = None
        if c.get("certificacion_id"):
            cert = certificaciones_abiertas.obtener_certificacion(int(c["certificacion_id"]))

        embed = discord.Embed(
            title=f"🎓 Capacitación #{c['id']}: {c.get('titulo', '—')}",
            description=c.get("descripcion") or "—",
            color=0x3498DB,
        )
        embed.add_field(name="Fecha y hora", value=c.get("fecha_hora") or "—", inline=True)
        embed.add_field(name="ID", value=str(c["id"]), inline=True)
        embed.add_field(name="Postulados", value=str(len(c.get("postulados") or [])), inline=True)
        if cert:
            embed.add_field(
                name="📜 Certificación vinculada",
                value=f"**{cert['nombre']}** (#{cert['id']})",
                inline=False,
            )
        embed.add_field(
            name="Postulación",
            value="Pulsa **📝 Postularse** para inscribirte.",
            inline=False,
        )
        embed.set_footer(text=f"id={c['id']} · cert={c.get('certificacion_id') or 0} · Botones activos")
        await interaction.response.send_message(embed=embed, view=PostularCapView())

    @grupo.command(name="listar_certs", description="Lista certificaciones del catálogo por rama")
    @app_commands.describe(departamento="Filtrar por departamento (opcional)")
    @app_commands.choices(departamento=depto_choices)
    async def listar_certs(interaction: discord.Interaction, departamento: app_commands.Choice[str] = None):
        slug = departamento.value if departamento else ""
        items = certificaciones_abiertas.listar_por_departamento(slug) if slug else certificaciones_abiertas.listar_certificaciones_activas()
        if not items:
            return await interaction.response.send_message("No hay certificaciones activas.", ephemeral=True)
        # Agrupar por depto
        from collections import defaultdict
        grupos = defaultdict(list)
        for c in items:
            grupos[c.get("departamento") or "general"].append(c)
        emb = discord.Embed(
            title="📜 Catálogo de certificaciones",
            description="Estas certificaciones aparecen al **programar** capacitaciones y en `/certificar`.",
            color=0x8E44AD,
        )
        for dep, lista in sorted(grupos.items()):
            lineas = [f"`#{x['id']}` **{x['nombre']}**" for x in lista[:12]]
            if len(lista) > 12:
                lineas.append(f"… +{len(lista)-12}")
            emb.add_field(name=dep.upper(), value="\n".join(lineas), inline=False)
        await interaction.response.send_message(embed=emb, ephemeral=True)
