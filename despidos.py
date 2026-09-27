# -*- coding: utf-8 -*-
"""despidos.py — /despedir con imagen de evidencia y destinatario seleccionable."""
from __future__ import annotations

from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

import config
import permisos
import registros
import roles_store
from estilos import crear_embed
from permisos import require_key

# Destinatarios (mismo listado que el núcleo; RRHH incluido)
_DEST_CHOICES = [
    app_commands.Choice(name="👥 Director de RRHH", value="DIRECTOR_RRHH"),
    app_commands.Choice(name="🖥️ Director General", value="DIRECTOR_GENERAL"),
    app_commands.Choice(name="⚖️ Director de Disciplina", value="DIRECTOR_DISCIPLINA"),
    app_commands.Choice(name="📋 Director Administrativo", value="DIRECTOR_ADMINISTRATIVO"),
    app_commands.Choice(name="🩺 Director Médico", value="DIRECTOR_MEDICO"),
    app_commands.Choice(name="💉 Director de Enfermería", value="DIRECTOR_ENFERMERIA"),
    app_commands.Choice(name="💰 Director Financiero", value="DIRECTOR_FINANCIERO"),
    app_commands.Choice(name="📦 Director de Logística", value="DIRECTOR_LOGISTICA"),
    app_commands.Choice(name="🛡️ Director de Seguridad", value="DIRECTOR_SEGURIDAD"),
    app_commands.Choice(name="📚 Director de Docencia", value="DIRECTOR_DOCENCIA"),
    app_commands.Choice(name="👑 Owner", value="OWNER"),
    app_commands.Choice(name="🤝 Co-Owner", value="CO_OWNER"),
]

_NOMBRES = {
    "DIRECTOR_RRHH": "Director de RRHH",
    "DIRECTOR_GENERAL": "Director General",
    "DIRECTOR_DISCIPLINA": "Director de Disciplina",
    "DIRECTOR_ADMINISTRATIVO": "Director Administrativo",
    "DIRECTOR_MEDICO": "Director Médico",
    "DIRECTOR_ENFERMERIA": "Director de Enfermería",
    "DIRECTOR_FINANCIERO": "Director Financiero",
    "DIRECTOR_LOGISTICA": "Director de Logística",
    "DIRECTOR_SEGURIDAD": "Director de Seguridad",
    "DIRECTOR_DOCENCIA": "Director de Docencia",
    "OWNER": "Owner",
    "CO_OWNER": "Co-Owner",
}

_CANAL_POR_KEY = {
    "DIRECTOR_RRHH": "aprobaciones_rrhh",
    "DIRECTOR_GENERAL": "citatorio_general",
    "DIRECTOR_DISCIPLINA": "citatorio_disciplina",
    "DIRECTOR_ADMINISTRATIVO": "citatorio_admin",
}


def _nombre_dest(key: str) -> str:
    try:
        from solicitudes import nombre_destinatario
        return nombre_destinatario(key)
    except Exception:
        return _NOMBRES.get(key, key)


def _canal_key(key: str) -> Optional[str]:
    try:
        from solicitudes import canal_para_key
        return canal_para_key(key)
    except Exception:
        return _CANAL_POR_KEY.get(key) or "aprobaciones_rrhh"


async def _enviar_log(bot, canal_key: str, embed: discord.Embed):
    cid = config.CANALES.get(canal_key)
    if not cid:
        return
    canal = bot.get_channel(cid)
    if canal:
        try:
            await canal.send(embed=embed)
        except discord.Forbidden:
            pass


def _roles_hospital_de(member: discord.Member, guild: discord.Guild):
    roles_a_quitar = []
    for key in config.KEYS_NOMBRES:
        rid = roles_store.obtener_id_key(key)
        rol = guild.get_role(rid) if rid else None
        if rol and rol in member.roles:
            roles_a_quitar.append(rol)
    for slug, data in config.DEPARTAMENTOS.items():
        try:
            ids = roles_store.escalafon_ids(slug, len(data["escalafon_nombres"]))
        except Exception:
            ids = []
        for rid in ids:
            rol = guild.get_role(rid) if rid else None
            if rol and rol in member.roles:
                roles_a_quitar.append(rol)
    return roles_a_quitar


def registrar(bot: commands.Bot) -> None:
    try:
        bot.tree.remove_command("despedir")
    except Exception:
        pass

    @bot.tree.command(
        name="despedir",
        description="Solicita el despido (evidencia con imagen opcional; elige destinatario, p.ej. RRHH)",
    )
    @app_commands.describe(
        usuario="Usuario a despedir",
        motivo="Motivo del despido",
        destinatario="A quién se envía la solicitud (RRHH, Dirección General, etc.)",
        evidencia="Texto de evidencia o detalle adicional (opcional)",
        evidencia_imagen="Imagen/prueba adjunta (opcional)",
        evidencia_imagen2="Segunda imagen de prueba (opcional)",
    )
    @app_commands.choices(destinatario=_DEST_CHOICES)
    @require_key(
        "DIRECTOR", "DIRECTOR_DISCIPLINA", "DIRECTOR_GENERAL",
        "DIRECTOR_ADMINISTRATIVO", "DIRECTOR_RRHH", "OWNER", "CO_OWNER",
        "JEFE_DEPARTAMENTO", "SUPERVISOR",
    )
    async def despedir(
        interaction: discord.Interaction,
        usuario: discord.Member,
        motivo: str,
        destinatario: app_commands.Choice[str],
        evidencia: str = "",
        evidencia_imagen: Optional[discord.Attachment] = None,
        evidencia_imagen2: Optional[discord.Attachment] = None,
    ):
        emisor = interaction.user
        if not isinstance(emisor, discord.Member):
            await interaction.response.send_message("❌ Solo en servidor.", ephemeral=True)
            return

        if not permisos.puede_actuar_sobre(emisor, usuario):
            await interaction.response.send_message(
                "❌ No puedes solicitar el despido de alguien de tu mismo nivel o superior.",
                ephemeral=True,
            )
            return

        # Validar adjuntos: solo imágenes (o permitir también vídeo/pdf de prueba)
        img_urls = []
        for att in (evidencia_imagen, evidencia_imagen2):
            if not att:
                continue
            ct = (att.content_type or "").lower()
            name = (att.filename or "").lower()
            if ct.startswith("image/") or name.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                img_urls.append(att.url)
            else:
                # Aun así se adjunta la URL como prueba
                img_urls.append(att.url)

        key_dest = destinatario.value
        nombre_dest = _nombre_dest(key_dest)

        # OWNER o DIRECTOR_RRHH pueden ejecutar directo
        if permisos.member_tiene_key(emisor, "OWNER") or permisos.member_tiene_key(emisor, "DIRECTOR_RRHH"):
            guild = interaction.guild
            if not guild:
                await interaction.response.send_message("❌ Solo en servidor.", ephemeral=True)
                return
            roles_a_quitar = _roles_hospital_de(usuario, guild)
            if roles_a_quitar:
                try:
                    await usuario.remove_roles(
                        *roles_a_quitar,
                        reason=f"Despedido por {emisor}: {motivo}",
                    )
                except discord.Forbidden:
                    await interaction.response.send_message(
                        "❌ No tengo permisos suficientes para quitar roles.",
                        ephemeral=True,
                    )
                    return
            registros.registrar_evento_cargo(usuario.id, "despido", motivo, emisor.id)
            emb = crear_embed(
                "error",
                "🚫 Despido",
                f"**{emisor}** despidió a **{usuario}**\n**Motivo:** {motivo}\n"
                f"**Evidencia:** {evidencia or '—'}",
                autor=emisor,
            )
            if img_urls:
                emb.set_image(url=img_urls[0])
                if len(img_urls) > 1:
                    emb.add_field(
                        name="Más pruebas",
                        value="\n".join(f"[Archivo {i}]({u})" for i, u in enumerate(img_urls[1:], 2)),
                        inline=False,
                    )
            await interaction.response.send_message(
                f"✅ {usuario.mention} fue despedido (ejecutado por {emisor.mention}).",
                embed=emb,
            )
            await _enviar_log(bot, "log_personal", emb)
            return

        # Solicitud con aprobación
        desc = (
            f"**Usuario:** {usuario.mention}\n"
            f"**Motivo:** {motivo}\n"
            f"**Evidencia (texto):** {evidencia or '—'}\n"
            f"**Destinatario:** {nombre_dest}"
        )
        if img_urls:
            links = "\n".join(f"[Prueba {i}]({u})" for i, u in enumerate(img_urls, 1))
            desc += f"\n**Evidencia (archivos):**\n{links}"

        embed = crear_embed(
            "aviso",
            "🚫 Solicitud de despido",
            desc,
            autor=emisor,
        )
        embed.add_field(name="Estado", value="⏳ Pendiente de aprobación", inline=False)
        if img_urls:
            embed.set_image(url=img_urls[0])

        async def _on_approve(inter, info):
            guild = inter.guild
            uid = int(info["datos"].get("usuario_id", 0))
            miembro = guild.get_member(uid) if guild else None
            if not miembro and guild:
                try:
                    miembro = await guild.fetch_member(uid)
                except Exception:
                    miembro = None
            if not miembro:
                await inter.followup.send("⚠️ Usuario no encontrado al aprobar.", ephemeral=True)
                return
            roles_a_quitar = _roles_hospital_de(miembro, guild)
            if roles_a_quitar:
                try:
                    await miembro.remove_roles(
                        *roles_a_quitar,
                        reason=f"Despido aprobado por {inter.user}",
                    )
                except discord.Forbidden:
                    await inter.followup.send("❌ Sin permisos para quitar roles.", ephemeral=True)
                    return
            registros.registrar_evento_cargo(
                miembro.id,
                "despido",
                info["datos"].get("motivo", ""),
                inter.user.id,
            )
            await inter.followup.send(
                f"✅ Despido de {miembro.mention} ejecutado.",
                ephemeral=True,
            )
            await _enviar_log(
                inter.client,
                "log_personal",
                crear_embed(
                    "error",
                    "🚫 Despido aprobado",
                    f"**{inter.user}** aprobó el despido de **{miembro}**\n"
                    f"Motivo: {info['datos'].get('motivo', '—')}",
                ),
            )

        await interaction.response.defer(ephemeral=True)
        try:
            from solicitudes import enviar_solicitud_con_aprobacion

            await enviar_solicitud_con_aprobacion(
                interaction,
                key_aprobador=key_dest,
                embed=embed,
                tipo="despido",
                datos={
                    "usuario_id": usuario.id,
                    "motivo": motivo,
                    "evidencia": evidencia,
                    "evidencia_urls": ",".join(img_urls),
                },
                canal_key=_canal_key(key_dest),
                on_approve=_on_approve,
            )
            # Si hay más de una imagen, enviar las extras como mensaje extra en el canal
            # (el embed principal ya muestra la primera)
            await interaction.followup.send(
                f"✅ Solicitud de despido de {usuario.mention} enviada a **{nombre_dest}**."
                + (" Con imagen(es) de prueba." if img_urls else ""),
                ephemeral=True,
            )
        except Exception as e:
            print(f"[despedir] error: {e}")
            await interaction.followup.send(f"❌ Error: `{e}`", ephemeral=True)

    print("[despidos] OK — /despedir con imagen y destinatario")
