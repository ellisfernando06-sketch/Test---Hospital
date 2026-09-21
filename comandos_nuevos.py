# -*- coding: utf-8 -*-
"""
comandos_nuevos.py — Comandos adicionales: sanciones, verificación Roblox,
moderación, contabilidad ampliada y utilidades por dirección.

Se registra llamando a registrar(bot) desde Bot_Hospital.py.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Optional, List

import discord
from discord import app_commands
from discord.ext import commands

import config
import economia
import permisos
import registros
import roles_store
import sanciones
import verificacion
from estilos import crear_embed
from permisos import require_key


def registrar(bot: commands.Bot) -> None:
    """Registra todos los comandos nuevos en el árbol del bot."""

    # ------------------------------------------------------------------
    # SANCIONES
    # ------------------------------------------------------------------

    @bot.tree.command(name="sancionar", description="Aplica una sanción con historial y log")
    @app_commands.describe(
        usuario="Usuario a sancionar",
        tipo="Tipo de sanción",
        motivo="Motivo",
        evidencia_texto="Evidencia en texto (opcional)",
        evidencia_archivo="Imagen/video/clip de evidencia (opcional)",
        duracion="Duración si aplica (ej: 3 días)",
    )
    @app_commands.choices(tipo=[
        app_commands.Choice(name="Advertencia", value="Advertencia"),
        app_commands.Choice(name="Sanción interna", value="Sanción interna"),
        app_commands.Choice(name="Sanción disciplinaria", value="Sanción disciplinaria"),
        app_commands.Choice(name="Sanción administrativa", value="Sanción administrativa"),
        app_commands.Choice(name="Suspensión", value="Suspensión"),
        app_commands.Choice(name="Otra", value="Otra"),
    ])
    @require_key("DIRECTOR", "DIRECTOR_DISCIPLINA", "DIRECTOR_ADMINISTRATIVO", "DIRECTOR_RRHH", "DIRECTOR_GENERAL", "SUPERVISOR", "OWNER", "CO_OWNER")
    async def sancionar(
        interaction: discord.Interaction,
        usuario: discord.Member,
        tipo: app_commands.Choice[str],
        motivo: str,
        evidencia_texto: str = "",
        evidencia_archivo: Optional[discord.Attachment] = None,
        duracion: str = "",
    ):
        if not permisos.puede_actuar_sobre(interaction.user, usuario):
            await interaction.response.send_message(
                "❌ No puedes sancionar a alguien de tu mismo nivel o superior.", ephemeral=True)
            return

        urls: List[str] = []
        if evidencia_archivo:
            urls.append(evidencia_archivo.url)

        reg = sanciones.registrar_sancion(
            usuario_id=usuario.id,
            tipo=tipo.value,
            motivo=motivo,
            autor_id=interaction.user.id,
            evidencia=evidencia_texto,
            evidencia_urls=urls,
            duracion=duracion,
        )
        registros.registrar_evento_cargo(
            usuario.id, "sancion",
            f"[{tipo.value}] {motivo}", interaction.user.id,
        )

        embed = sanciones.embed_sancion(reg, interaction.guild)
        await interaction.response.send_message(embed=embed)

        msg = await sanciones.enviar_log_sancion(bot, embed)
        if msg:
            # Actualizar IDs de log en el registro
            data = sanciones._load()
            for s in data["sanciones"]:
                if s.get("id") == reg["id"]:
                    s["canal_log_id"] = msg.channel.id
                    s["mensaje_log_id"] = msg.id
                    break
            sanciones._save(data)

    @bot.tree.command(name="historial_sanciones", description="Ver historial de sanciones de un usuario")
    @app_commands.describe(usuario="Usuario a consultar")
    @require_key("STAFF", "SUPERVISOR", "DIRECTOR", "OWNER", "CO_OWNER")
    async def historial_sanciones(interaction: discord.Interaction, usuario: discord.Member):
        lista = sanciones.sanciones_de(usuario.id)
        embed = sanciones.embed_historial(usuario, lista)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="quitar_sancion", description="Anula una sanción (si fue sin razón u otro motivo)")
    @app_commands.describe(
        sancion_id="ID de la sanción (número del historial)",
        motivo="Motivo de la anulación",
    )
    @require_key("DIRECTOR_DISCIPLINA", "DIRECTOR_ADMINISTRATIVO", "DIRECTOR_RRHH", "DIRECTOR_GENERAL", "OWNER", "CO_OWNER")
    async def quitar_sancion(interaction: discord.Interaction, sancion_id: int, motivo: str):
        reg = sanciones.anular_sancion(sancion_id, interaction.user.id, motivo)
        if not reg:
            await interaction.response.send_message(
                f"❌ No se encontró la sanción **#{sancion_id}** o ya estaba anulada.", ephemeral=True)
            return

        registros.registrar_evento_cargo(
            reg["usuario_id"], "sancion_anulada",
            f"#{sancion_id}: {motivo}", interaction.user.id,
        )

        embed = sanciones.embed_sancion(reg, interaction.guild)
        embed.title = f"🗑️ Sanción #{sancion_id} anulada"
        await interaction.response.send_message(embed=embed)
        await sanciones.enviar_log_sancion(bot, embed)

    @bot.tree.command(name="apelar_sancion", description="Apela una sanción y abre ticket con el Director Administrativo")
    @app_commands.describe(
        sancion_id="ID de la sanción a apelar",
        razon="Por qué consideras que debe revisarse",
    )
    async def apelar_sancion(interaction: discord.Interaction, sancion_id: int, razon: str):
        reg = sanciones.obtener_sancion(sancion_id)
        if not reg:
            await interaction.response.send_message(
                f"❌ No existe la sanción **#{sancion_id}**.", ephemeral=True)
            return
        if reg.get("anulada"):
            await interaction.response.send_message(
                f"⚠️ La sanción **#{sancion_id}** ya fue anulada.", ephemeral=True)
            return
        if int(reg.get("usuario_id", 0)) != interaction.user.id:
            # Staff también puede iniciar apelación en nombre de alguien
            if not isinstance(interaction.user, discord.Member) or not permisos.member_tiene_alguna_key(
                interaction.user, "DIRECTOR", "OWNER", "CO_OWNER", "SUPERVISOR"
            ):
                await interaction.response.send_message(
                    "❌ Solo puedes apelar tus propias sanciones (o ser staff).", ephemeral=True)
                return

        if not interaction.guild:
            await interaction.response.send_message("❌ Solo en el servidor.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        canal = await sanciones.abrir_ticket_apelacion(interaction.guild, interaction.user, reg)
        if not canal:
            await interaction.followup.send("❌ No pude crear el ticket de apelación.", ephemeral=True)
            return

        await canal.send(
            f"**Razón de la apelación:**\n{razon}\n\n"
            f"Puedes adjuntar más evidencias (imágenes, videos o texto) aquí."
        )
        await interaction.followup.send(
            f"✅ Ticket de apelación creado: {canal.mention}", ephemeral=True)

    # ------------------------------------------------------------------
    # MODERACIÓN (ban / kick / mute) — con registro
    # ------------------------------------------------------------------

    @bot.tree.command(name="banear", description="Banea a un miembro del servidor (con registro)")
    @app_commands.describe(
        usuario="Usuario a banear",
        motivo="Motivo",
        borrar_dias="Días de mensajes a borrar (0-7)",
    )
    @require_key("DIRECTOR_DISCIPLINA", "DIRECTOR_ADMINISTRATIVO", "DIRECTOR_GENERAL", "OWNER", "CO_OWNER")
    async def banear(
        interaction: discord.Interaction,
        usuario: discord.Member,
        motivo: str,
        borrar_dias: int = 0,
    ):
        if not permisos.puede_actuar_sobre(interaction.user, usuario):
            await interaction.response.send_message("❌ No puedes banear a ese usuario.", ephemeral=True)
            return
        borrar_dias = max(0, min(7, borrar_dias))
        try:
            await usuario.ban(reason=f"{motivo} — por {interaction.user}", delete_message_days=borrar_dias)
        except discord.Forbidden:
            await interaction.response.send_message("❌ No tengo permiso de Ban.", ephemeral=True)
            return

        registros.registrar_evento_cargo(usuario.id, "ban", motivo, interaction.user.id)
        embed = crear_embed(
            "error", "🔨 Usuario baneado",
            f"**Usuario:** {usuario} (`{usuario.id}`)\n**Motivo:** {motivo}\n**Por:** {interaction.user.mention}",
            autor=interaction.user,
        )
        await interaction.response.send_message(embed=embed)
        canal_id = config.CANALES.get("log_sanciones_ooc") or config.CANALES.get("log_sanciones")
        if canal_id:
            ch = bot.get_channel(canal_id)
            if ch:
                try:
                    await ch.send(embed=embed)
                except discord.Forbidden:
                    pass

    @bot.tree.command(name="expulsar", description="Expulsa (kick) a un miembro (con registro)")
    @app_commands.describe(usuario="Usuario a expulsar", motivo="Motivo")
    @require_key("DIRECTOR_DISCIPLINA", "DIRECTOR_ADMINISTRATIVO", "DIRECTOR_GENERAL", "OWNER", "CO_OWNER")
    async def expulsar(interaction: discord.Interaction, usuario: discord.Member, motivo: str):
        if not permisos.puede_actuar_sobre(interaction.user, usuario):
            await interaction.response.send_message("❌ No puedes expulsar a ese usuario.", ephemeral=True)
            return
        try:
            await usuario.kick(reason=f"{motivo} — por {interaction.user}")
        except discord.Forbidden:
            await interaction.response.send_message("❌ No tengo permiso de Kick.", ephemeral=True)
            return

        registros.registrar_evento_cargo(usuario.id, "kick", motivo, interaction.user.id)
        embed = crear_embed(
            "error", "👢 Usuario expulsado",
            f"**Usuario:** {usuario} (`{usuario.id}`)\n**Motivo:** {motivo}\n**Por:** {interaction.user.mention}",
            autor=interaction.user,
        )
        await interaction.response.send_message(embed=embed)
        canal_id = config.CANALES.get("log_sanciones_ooc") or config.CANALES.get("log_sanciones")
        if canal_id:
            ch = bot.get_channel(canal_id)
            if ch:
                try:
                    await ch.send(embed=embed)
                except discord.Forbidden:
                    pass

    @bot.tree.command(name="silenciar", description="Silencia (timeout) a un miembro (con registro)")
    @app_commands.describe(
        usuario="Usuario a silenciar",
        minutos="Minutos de silencio (máx 40320 = 28 días)",
        motivo="Motivo",
    )
    @require_key("DIRECTOR_DISCIPLINA", "DIRECTOR_ADMINISTRATIVO", "DIRECTOR_GENERAL", "SUPERVISOR", "OWNER", "CO_OWNER")
    async def silenciar(
        interaction: discord.Interaction,
        usuario: discord.Member,
        minutos: int,
        motivo: str,
    ):
        if not permisos.puede_actuar_sobre(interaction.user, usuario):
            await interaction.response.send_message("❌ No puedes silenciar a ese usuario.", ephemeral=True)
            return
        minutos = max(1, min(40320, minutos))
        try:
            await usuario.timeout(timedelta(minutes=minutos), reason=f"{motivo} — por {interaction.user}")
        except discord.Forbidden:
            await interaction.response.send_message("❌ No tengo permiso de Timeout.", ephemeral=True)
            return

        registros.registrar_evento_cargo(
            usuario.id, "timeout", f"{minutos} min: {motivo}", interaction.user.id)
        embed = crear_embed(
            "aviso", "🔇 Usuario silenciado",
            f"**Usuario:** {usuario.mention}\n**Duración:** {minutos} min\n**Motivo:** {motivo}\n**Por:** {interaction.user.mention}",
            autor=interaction.user,
        )
        await interaction.response.send_message(embed=embed)
        canal_id = config.CANALES.get("log_sanciones_ooc") or config.CANALES.get("log_sanciones")
        if canal_id:
            ch = bot.get_channel(canal_id)
            if ch:
                try:
                    await ch.send(embed=embed)
                except discord.Forbidden:
                    pass

    @bot.tree.command(name="quitar_silencio", description="Quita el timeout a un miembro")
    @app_commands.describe(usuario="Usuario")
    @require_key("DIRECTOR_DISCIPLINA", "DIRECTOR_ADMINISTRATIVO", "DIRECTOR_GENERAL", "SUPERVISOR", "OWNER", "CO_OWNER")
    async def quitar_silencio(interaction: discord.Interaction, usuario: discord.Member):
        try:
            await usuario.timeout(None, reason=f"Timeout removido por {interaction.user}")
        except discord.Forbidden:
            await interaction.response.send_message("❌ No tengo permiso.", ephemeral=True)
            return
        await interaction.response.send_message(f"✅ Se quitó el silencio a {usuario.mention}.")

    # ------------------------------------------------------------------
    # VERIFICACIÓN ROBLOX (Visitante → Miembro)
    # ------------------------------------------------------------------

    @bot.tree.command(
        name="verificar_roblox",
        description="Envía DM de verificación Roblox a miembros con rol Visitante",
    )
    @app_commands.describe(
        usuario="Un visitante específico (opcional; si no, se puede listar)",
    )
    @require_key("DIRECTOR_ADMINISTRATIVO", "DIRECTOR_GENERAL", "DIRECTOR_RRHH", "OWNER", "CO_OWNER", "SUPERVISOR")
    async def verificar_roblox(
        interaction: discord.Interaction,
        usuario: Optional[discord.Member] = None,
    ):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("❌ Solo en el servidor.", ephemeral=True)
            return

        r_vis = verificacion.rol_visitante(guild)
        r_miem = verificacion.rol_miembro(guild)
        if not r_vis:
            await interaction.response.send_message(
                "❌ No encontré el rol **Visitante**. Créalo con ese nombre exacto.", ephemeral=True)
            return
        if not r_miem:
            await interaction.response.send_message(
                "❌ No encontré el rol **Miembro**. Créalo con ese nombre exacto.", ephemeral=True)
            return

        if usuario:
            if r_vis not in usuario.roles:
                await interaction.response.send_message(
                    f"⚠️ {usuario.mention} no tiene el rol **Visitante**.", ephemeral=True)
                return
            ok = await verificacion.enviar_dm_verificacion(usuario, interaction.user)
            if ok:
                await interaction.response.send_message(
                    f"✅ DM de verificación enviado a {usuario.mention}.", ephemeral=True)
            else:
                await interaction.response.send_message(
                    f"❌ No pude enviarle DM a {usuario.mention} (tiene DMs cerrados).", ephemeral=True)
            return

        # Sin usuario: listar visitantes
        visitantes = [m for m in guild.members if r_vis in m.roles and not m.bot]
        if not visitantes:
            await interaction.response.send_message(
                "ℹ️ No hay miembros con rol **Visitante**.", ephemeral=True)
            return

        enviados = 0
        fallidos = 0
        await interaction.response.defer(ephemeral=True)
        for m in visitantes[:25]:  # límite de seguridad
            if await verificacion.enviar_dm_verificacion(m, interaction.user):
                enviados += 1
            else:
                fallidos += 1

        await interaction.followup.send(
            f"✅ DMs enviados: **{enviados}**\n❌ Fallidos (DM cerrado): **{fallidos}**\n"
            f"Roles detectados: Visitante=`{r_vis.name}` → Miembro=`{r_miem.name}`",
            ephemeral=True,
        )

    @bot.tree.command(name="ver_roblox", description="Consulta el usuario Roblox verificado de un miembro")
    @app_commands.describe(usuario="Usuario")
    @require_key("STAFF", "SUPERVISOR", "DIRECTOR", "OWNER")
    async def ver_roblox(interaction: discord.Interaction, usuario: discord.Member):
        roblox = verificacion.obtener_roblox(usuario.id)
        if not roblox:
            await interaction.response.send_message(
                f"⚠️ {usuario.mention} no tiene Roblox verificado.", ephemeral=True)
            return
        embed = crear_embed(
            "info", "🎮 Roblox verificado",
            f"**Discord:** {usuario.mention}\n**Roblox:** `{roblox}`",
            autor=usuario,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ------------------------------------------------------------------
    # CONTABILIDAD / FINANZAS ampliadas
    # ------------------------------------------------------------------

    @bot.tree.command(name="registrar_gasto", description="Registra un gasto contable del hospital")
    @app_commands.describe(
        monto="Monto del gasto",
        concepto="Concepto / descripción",
        categoria="Categoría contable",
    )
    @app_commands.choices(categoria=[
        app_commands.Choice(name="Insumos médicos", value="insumos"),
        app_commands.Choice(name="Salarios", value="salarios"),
        app_commands.Choice(name="Mantenimiento", value="mantenimiento"),
        app_commands.Choice(name="Equipamiento", value="equipamiento"),
        app_commands.Choice(name="Servicios", value="servicios"),
        app_commands.Choice(name="Otro", value="otro"),
    ])
    @require_key("DIRECTOR_FINANCIERO", "DIRECTOR_ADMINISTRATIVO", "DIRECTOR_GENERAL", "OWNER", "CO_OWNER")
    async def registrar_gasto(
        interaction: discord.Interaction,
        monto: float,
        concepto: str,
        categoria: app_commands.Choice[str],
    ):
        if monto <= 0:
            await interaction.response.send_message("❌ El monto debe ser positivo.", ephemeral=True)
            return
        # Usa el bot como emisor institucional (id 0) y el staff como receptor contable
        economia.registrar_movimiento(
            tipo=f"gasto:{categoria.value}",
            de_id=0,
            a_id=interaction.user.id,
            monto=monto,
            motivo=concepto,
        )
        embed = crear_embed(
            "finanzas",
            "📉 Gasto registrado",
            f"**Monto:** {config.MONEDA}{monto:,.2f}\n"
            f"**Categoría:** {categoria.name}\n"
            f"**Concepto:** {concepto}\n"
            f"**Registrado por:** {interaction.user.mention}",
            autor=interaction.user,
        )
        await interaction.response.send_message(embed=embed)
        canal_id = config.CANALES.get("log_finanzas")
        if canal_id:
            ch = bot.get_channel(canal_id)
            if ch:
                try:
                    await ch.send(embed=embed)
                except discord.Forbidden:
                    pass

    @bot.tree.command(name="registrar_ingreso", description="Registra un ingreso contable del hospital")
    @app_commands.describe(monto="Monto", concepto="Concepto / descripción")
    @require_key("DIRECTOR_FINANCIERO", "DIRECTOR_ADMINISTRATIVO", "DIRECTOR_GENERAL", "OWNER", "CO_OWNER")
    async def registrar_ingreso(interaction: discord.Interaction, monto: float, concepto: str):
        if monto <= 0:
            await interaction.response.send_message("❌ El monto debe ser positivo.", ephemeral=True)
            return
        economia.registrar_movimiento(
            tipo="ingreso",
            de_id=interaction.user.id,
            a_id=0,
            monto=monto,
            motivo=concepto,
        )
        embed = crear_embed(
            "finanzas",
            "📈 Ingreso registrado",
            f"**Monto:** {config.MONEDA}{monto:,.2f}\n"
            f"**Concepto:** {concepto}\n"
            f"**Registrado por:** {interaction.user.mention}",
            autor=interaction.user,
        )
        await interaction.response.send_message(embed=embed)
        canal_id = config.CANALES.get("log_finanzas")
        if canal_id:
            ch = bot.get_channel(canal_id)
            if ch:
                try:
                    await ch.send(embed=embed)
                except discord.Forbidden:
                    pass

    @bot.tree.command(name="libro_contable", description="Últimos movimientos contables del hospital")
    @app_commands.describe(limite="Cantidad de movimientos (máx 30)")
    @require_key("DIRECTOR_FINANCIERO", "DIRECTOR_ADMINISTRATIVO", "DIRECTOR_GENERAL", "OWNER", "CO_OWNER")
    async def libro_contable(interaction: discord.Interaction, limite: int = 15):
        limite = max(1, min(30, limite))
        resumen = economia.resumen_general(limite_movimientos=limite)
        movs = resumen.get("ultimos_movimientos", [])
        if not movs:
            await interaction.response.send_message("Sin movimientos registrados.", ephemeral=True)
            return
        lineas = []
        for m in movs:
            lineas.append(
                f"• `{str(m.get('fecha',''))[:16]}` **{m.get('tipo')}** "
                f"{config.MONEDA}{float(m.get('monto',0)):,.2f} — {m.get('motivo','')[:60]}"
            )
        embed = crear_embed(
            "finanzas",
            "📒 Libro contable",
            "\n".join(lineas),
        )
        embed.add_field(
            name="Total en circulación",
            value=f"{config.MONEDA}{resumen.get('total_en_circulacion',0):,.2f}",
            inline=True,
        )
        embed.add_field(
            name="Cuentas activas",
            value=str(resumen.get("cuentas_activas", 0)),
            inline=True,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ------------------------------------------------------------------
    # COMANDOS ÚTILES POR DIRECCIÓN
    # ------------------------------------------------------------------

    @bot.tree.command(name="anuncio_direccion", description="Anuncio oficial de una dirección del hospital")
    @app_commands.describe(
        direccion="Dirección que emite el anuncio",
        titulo="Título",
        mensaje="Contenido del anuncio",
    )
    @app_commands.choices(direccion=[
        app_commands.Choice(name="Director Médico", value="DIRECTOR_MEDICO"),
        app_commands.Choice(name="Director de Enfermería", value="DIRECTOR_ENFERMERIA"),
        app_commands.Choice(name="Director de RRHH", value="DIRECTOR_RRHH"),
        app_commands.Choice(name="Director Financiero", value="DIRECTOR_FINANCIERO"),
        app_commands.Choice(name="Director de Logística", value="DIRECTOR_LOGISTICA"),
        app_commands.Choice(name="Director de Seguridad", value="DIRECTOR_SEGURIDAD"),
        app_commands.Choice(name="Director Administrativo", value="DIRECTOR_ADMINISTRATIVO"),
        app_commands.Choice(name="Director de Disciplina", value="DIRECTOR_DISCIPLINA"),
        app_commands.Choice(name="Director General", value="DIRECTOR_GENERAL"),
    ])
    @require_key("DIRECTOR", "OWNER", "CO_OWNER")
    async def anuncio_direccion(
        interaction: discord.Interaction,
        direccion: app_commands.Choice[str],
        titulo: str,
        mensaje: str,
    ):
        # Solo esa dirección (o superior) puede usarlo
        if not permisos.member_tiene_alguna_key(
            interaction.user, direccion.value, "OWNER", "CO_OWNER", "DIRECTOR_GENERAL"
        ):
            await interaction.response.send_message(
                f"❌ Solo **{config.nombre_key(direccion.value)}** (o superior) puede emitir este anuncio.",
                ephemeral=True,
            )
            return

        embed = crear_embed(
            "info",
            f"📢 {titulo}",
            mensaje,
            autor=interaction.user,
        )
        embed.add_field(name="Dirección", value=config.nombre_key(direccion.value), inline=True)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="mi_sanciones", description="Consulta tu propio historial de sanciones")
    async def mi_sanciones(interaction: discord.Interaction):
        lista = sanciones.sanciones_de(interaction.user.id)
        embed = sanciones.embed_historial(interaction.user, lista)
        await interaction.response.send_message(embed=embed, ephemeral=True)
