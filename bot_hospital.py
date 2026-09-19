"""
bot_hospital.py
================
Bot de Discord para un servidor de roleplay hospitalario, con un
sistema de permisos por "keys" (llaves) según el cargo de cada quien:

    OWNER                              -> control total
    CO_OWNER / DIRECTOR_DISCIPLINA    -> control administrativo
    DIRECTOR_* (cada dirección)        -> comandos de su dirección
    JEFE_DEPARTAMENTO / SUPERVISOR     -> comandos de su nivel
    STAFF                              -> comandos básicos

Toda la configuración vive en config.py — es el ÚNICO archivo que
necesitas editar para adaptar el bot a tu servidor.

Requisitos:
    pip install -r requirements.txt

Antes de ejecutar:
    1. En Railway (o tu hosting): Variables → TOKEN = <token del bot>
       (también acepta DISCORD_TOKEN / BOT_TOKEN). NUNCA en el código.
    2. Ajusta config.py: nombres de roles (con emoji), departamentos,
       IDs de canales de log si los usas.
    3. Developer Portal → Privileged Gateway Intents:
       Server Members Intent + Message Content Intent.
    4. Sube el rol del bot por encima de los roles que gestione.
    5. Crea en el servidor los roles con los nombres exactos de config.py
       (incluido el emoji). El bot NUNCA crea roles.
    6. Ejecuta /configurar_roles una vez (OWNER): detecta roles existentes
       por nombre, guarda IDs y ordena por categorías.
"""

import discord
from discord import app_commands
from discord.ext import commands

import capacitaciones
import codigos
import os
import config
import economia
import ficha_personal
import inventario
import pacientes
import permisos
import postulaciones
import quejas
import registros
import roles_setup
import roles_store
import turnos
from estado import PanelEstadoView, construir_embed as construir_embed_estado
import bot_control
from estilos import crear_embed
from paneles import AbrirTicketView, CerrarTicketView, PanelAccionesView
from permisos import SinPermiso, require_key
from quejas import QuejaModal
from solicitudes import CartaSolicitudModal, SolicitudDescargoModal, SolicitudPermisoModal, enviar_solicitud

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


async def enviar_log(canal_key: str, embed: discord.Embed):
    canal_id = config.CANALES.get(canal_key)
    if not canal_id:
        return
    canal = bot.get_channel(canal_id)
    if canal:
        try:
            await canal.send(embed=embed)
        except discord.Forbidden:
            pass


@bot.event
async def on_ready():
    # Registra las vistas persistentes para que los botones sigan
    # funcionando después de reiniciar el bot.
    bot.add_view(AbrirTicketView())
    bot.add_view(CerrarTicketView())
    bot.add_view(PanelAccionesView())
    bot.add_view(PanelEstadoView())

    print(f"Conectado como {bot.user} (ID: {bot.user.id})")
    # Estado del bot
    if bot_control.get_mode() == "offline":
        bot_control.set_mode("online", "Bot reiniciado y operativo.", None)
    await bot_control.publicar_estado(bot)
    try:
        sincronizados = await bot.tree.sync()
        print(f"Sincronizados {len(sincronizados)} comandos slash (global).")
    except Exception as e:
        print(f"Error al sincronizar comandos globales: {e}")

    # Sincronización directa a tu servidor: aparece al instante, sin esperar
    # la propagación global de Discord (que puede tardar hasta 1 hora).
    try:
        MI_SERVIDOR = discord.Object(id=1381360019467014184)
        bot.tree.copy_global_to(guild=MI_SERVIDOR)
        sincronizados_guild = await bot.tree.sync(guild=MI_SERVIDOR)
        print(f"Sincronizados {len(sincronizados_guild)} comandos slash (tu servidor, instantáneo).")
    except Exception as e:
        print(f"Error al sincronizar comandos en el servidor: {e}")


# ---------------------------------------------------------------------------
# Manejador global de errores de permisos (para todos los comandos)
# ---------------------------------------------------------------------------
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, SinPermiso):
        legibles = ", ".join(error.keys_requeridas)
        msg = f"❌ No tienes el cargo/key necesario para esto. Se requiere: **{legibles}**."
    elif isinstance(error, app_commands.MissingPermissions):
        msg = "❌ No tienes permiso para usar este comando."
    else:
        msg = f"❌ Ocurrió un error: {error}"

    if interaction.response.is_done():
        await interaction.followup.send(msg, ephemeral=True)
    else:
        await interaction.response.send_message(msg, ephemeral=True)


# ===========================================================================
# 0-A) ARRANQUE INICIAL (bootstrap) — rompe el candado de "nadie tiene key"
#      Solo lo puede usar el DUEÑO REAL del servidor de Discord (guild.owner_id),
#      y solo funciona si todavía nadie tiene la key OWNER asignada.
#      Una vez usado, se recomienda borrar este comando del código.
# ===========================================================================

@bot.tree.command(name="bootstrap_owner", description="[Solo primer uso] Te asigna la key OWNER para poder configurar el bot")
async def bootstrap_owner(interaction: discord.Interaction):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("❌ Este comando solo funciona dentro de un servidor.", ephemeral=True)
        return

    if interaction.user.id != guild.owner_id:
        await interaction.response.send_message(
            "❌ Solo el dueño del servidor de Discord puede ejecutar la configuración inicial.",
            ephemeral=True)
        return

    owner_role_id = roles_store.obtener_id_key("OWNER")
    if owner_role_id:
        rol_existente = guild.get_role(owner_role_id)
        if rol_existente and rol_existente.members:
            await interaction.response.send_message(
                "⚠️ Ya hay alguien con la key OWNER configurada. Pide que te la otorgue con `/otorgar_key`.",
                ephemeral=True)
            return

    await interaction.response.defer(ephemeral=True)

    nombre, color = config.KEYS_NOMBRES["OWNER"]
    resumen: list[str] = []
    rol = await roles_setup._asegurar_rol(guild, nombre, color, resumen)
    if not rol:
        await interaction.followup.send(
            "❌ No se pudo crear/detectar el rol Owner. Revisa que el rol del bot tenga permiso 'Gestionar roles'.",
            ephemeral=True)
        return

    roles_store.guardar_key("OWNER", rol.id)

    try:
        await interaction.user.add_roles(rol, reason="Bootstrap inicial del sistema de keys")
    except discord.Forbidden:
        await interaction.followup.send(
            f"⚠️ Se creó/detectó el rol {rol.mention} y se guardó, pero no pude asignártelo "
            "(sube el rol del bot por encima de él en Ajustes → Roles). Asígnatelo manualmente en Discord.",
            ephemeral=True)
        return

    await interaction.followup.send(
        f"✅ Listo, {rol.mention} creado/detectado y asignado. Ahora ya puedes usar `/configurar_roles` "
        "para el resto del sistema (departamentos, escalafones, etc.).",
        ephemeral=True)


# ===========================================================================
# 0) CONFIGURACIÓN AUTOMÁTICA DE ROLES (keys) Y OTORGAMIENTO
# ===========================================================================

@bot.tree.command(name="configurar_roles", description="Detecta roles existentes por nombre (no duplica), guarda IDs y ordena por categorías")
@require_key("OWNER")
async def configurar_roles(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    resumen = await roles_setup.configurar_todo(interaction.guild)
    texto = "\n".join(resumen)
    # Discord limita los embeds a 4096 caracteres en la descripción; se parte si hace falta
    bloques = [texto[i:i + 3800] for i in range(0, len(texto), 3800)] or ["(sin roles definidos)"]
    for i, bloque in enumerate(bloques):
        embed = crear_embed(
            "exito",
            "✅ Roles configurados" if i == 0 else "✅ Roles configurados (cont.)",
            bloque)
        await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(name="ordenar_roles", description="Reordena los roles del servidor por categorías (RRHH, Médico, etc.)")
@require_key("OWNER")
async def ordenar_roles_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    resumen = await roles_setup.ordenar_roles(interaction.guild)
    texto = "\n".join(resumen)
    embed = crear_embed("info", "📑 Orden de roles", texto[:4000])
    await interaction.followup.send(embed=embed, ephemeral=True)


KEY_CHOICES = [app_commands.Choice(name=k, value=k) for k in config.KEYS_NOMBRES]


@bot.tree.command(name="otorgar_key", description="Otorga una key (rol de cargo) a un usuario")
@app_commands.describe(usuario="Usuario objetivo", key="Key/cargo a otorgar")
@app_commands.choices(key=KEY_CHOICES)
@require_key(
    "OWNER",
    "DIRECTOR", "JEFE_DEPARTAMENTO")
async def otorgar_key(interaction: discord.Interaction, usuario: discord.Member, key: app_commands.Choice[str]):
    emisor = interaction.user
    nivel_emisor = permisos.nivel_del_member(emisor)

    role_id = roles_store.obtener_id_key(key.value)
    if not role_id or not interaction.guild.get_role(role_id):
        await interaction.response.send_message(
            "❌ Esa key todavía no tiene un rol detectado. Crea el rol en el servidor con el nombre exacto de config.py y ejecuta `/configurar_roles`.",
            ephemeral=True)
        return
    rol = interaction.guild.get_role(role_id)
    nivel_rol = permisos.nivel_de_rol(role_id)

    if not permisos.member_tiene_key(emisor, "OWNER") and nivel_rol >= nivel_emisor:
        await interaction.response.send_message(
            "❌ No puedes otorgar una key igual o superior a tu propio nivel.", ephemeral=True
        )
        return

    if rol in usuario.roles:
        await interaction.response.send_message(
            f"⚠️ {usuario.mention} ya tiene la key **{key.value}**.", ephemeral=True
        )
        return

    try:
        await usuario.add_roles(rol, reason=f"Key otorgada por {emisor}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ No tengo permisos suficientes.", ephemeral=True)
        return

    await interaction.response.send_message(f"✅ Se le otorgó la key **{key.value}** ({rol.mention}) a {usuario.mention}.")
    await enviar_log("log_roles", crear_embed(
        "exito", "Key otorgada", f"**{emisor}** otorgó **{key.value}** a **{usuario}**"))


@bot.tree.command(name="quitar_key", description="Quita una key (rol de cargo) a un usuario")
@app_commands.describe(usuario="Usuario objetivo", key="Key/cargo a quitar")
@app_commands.choices(key=KEY_CHOICES)
@require_key(
    "OWNER",
    "DIRECTOR", "JEFE_DEPARTAMENTO")
async def quitar_key(interaction: discord.Interaction, usuario: discord.Member, key: app_commands.Choice[str]):
    emisor = interaction.user
    nivel_emisor = permisos.nivel_del_member(emisor)

    role_id = roles_store.obtener_id_key(key.value)
    if not role_id or not interaction.guild.get_role(role_id):
        await interaction.response.send_message(
            "❌ Esa key todavía no tiene un rol detectado. Crea el rol en el servidor con el nombre exacto de config.py y ejecuta `/configurar_roles`.",
            ephemeral=True)
        return
    rol = interaction.guild.get_role(role_id)
    nivel_rol = permisos.nivel_de_rol(role_id)

    if not permisos.member_tiene_key(emisor, "OWNER") and nivel_rol >= nivel_emisor:
        await interaction.response.send_message(
            "❌ No puedes quitar una key igual o superior a tu propio nivel.", ephemeral=True
        )
        return

    if rol not in usuario.roles:
        await interaction.response.send_message(
            f"⚠️ {usuario.mention} no tiene la key **{key.value}**.", ephemeral=True
        )
        return

    try:
        await usuario.remove_roles(rol, reason=f"Key removida por {emisor}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ No tengo permisos suficientes.", ephemeral=True)
        return

    await interaction.response.send_message(f"✅ Se le quitó la key **{key.value}** a {usuario.mention}.")
    await enviar_log("log_roles", crear_embed(
        "error", "Key removida", f"**{emisor}** quitó **{key.value}** a **{usuario}**"))


# ===========================================================================
# 1) GESTIÓN DE ROLES LIBRES (dar / quitar cualquier rol del servidor)
#    Solo puede dar/quitar un rol quien tenga un nivel jerárquico MAYOR
#    al nivel de ese rol (si el rol forma parte de la jerarquía de keys).
#    Si el rol no pertenece a la jerarquía (ej. un rol cosmético), se
#    exige como mínimo nivel de DIRECTOR o superior.
# ===========================================================================

@bot.tree.command(name="dar_rol", description="Asigna un rol a un usuario (según tu jerarquía)")
@app_commands.describe(usuario="Usuario objetivo", rol="Rol a asignar")
@require_key(
    "OWNER",
    "DIRECTOR", "JEFE_DEPARTAMENTO")
async def dar_rol(interaction: discord.Interaction, usuario: discord.Member, rol: discord.Role):
    emisor = interaction.user
    nivel_emisor = permisos.nivel_del_member(emisor)
    nivel_rol = permisos.nivel_de_rol(rol.id)

    if not permisos.member_tiene_key(emisor, "OWNER"):
        if nivel_rol == -1:
            # Rol fuera de la jerarquía: exige al menos nivel DIRECTOR
            if nivel_emisor < config.JERARQUIA_KEYS.index("DIRECTOR"):
                raise SinPermiso(["DIRECTOR o superior"])
        elif nivel_rol >= nivel_emisor:
            await interaction.response.send_message(
                "❌ No puedes asignar un rol igual o superior a tu propio nivel.",
                ephemeral=True)
            return

    if rol in usuario.roles:
        await interaction.response.send_message(
            f"⚠️ {usuario.mention} ya tiene el rol **{rol.name}**.", ephemeral=True
        )
        return

    try:
        await usuario.add_roles(rol, reason=f"Asignado por {emisor}")
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ No tengo permisos suficientes (revisa jerarquía de roles del bot).",
            ephemeral=True)
        return

    await interaction.response.send_message(f"✅ Se le dio **{rol.name}** a {usuario.mention}.")
    await enviar_log("log_roles", crear_embed(
        "exito", "Rol asignado",
        f"**{emisor}** dio el rol **{rol.name}** a **{usuario}**"))


@bot.tree.command(name="quitar_rol", description="Quita un rol a un usuario (según tu jerarquía)")
@app_commands.describe(usuario="Usuario objetivo", rol="Rol a quitar")
@require_key(
    "OWNER",
    "DIRECTOR", "JEFE_DEPARTAMENTO")
async def quitar_rol(interaction: discord.Interaction, usuario: discord.Member, rol: discord.Role):
    emisor = interaction.user
    nivel_emisor = permisos.nivel_del_member(emisor)
    nivel_rol = permisos.nivel_de_rol(rol.id)

    if not permisos.member_tiene_key(emisor, "OWNER"):
        if nivel_rol == -1:
            if nivel_emisor < config.JERARQUIA_KEYS.index("DIRECTOR"):
                raise SinPermiso(["DIRECTOR o superior"])
        elif nivel_rol >= nivel_emisor:
            await interaction.response.send_message(
                "❌ No puedes quitar un rol igual o superior a tu propio nivel.",
                ephemeral=True)
            return

    if rol not in usuario.roles:
        await interaction.response.send_message(
            f"⚠️ {usuario.mention} no tiene el rol **{rol.name}**.", ephemeral=True
        )
        return

    try:
        await usuario.remove_roles(rol, reason=f"Removido por {emisor}")
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ No tengo permisos suficientes (revisa jerarquía de roles del bot).",
            ephemeral=True)
        return

    await interaction.response.send_message(f"✅ Se le quitó **{rol.name}** a {usuario.mention}.")
    await enviar_log("log_roles", crear_embed(
        "error", "Rol removido",
        f"**{emisor}** quitó el rol **{rol.name}** a **{usuario}**"))


# ===========================================================================
# 2) ASCENSOS, DESCENSOS Y TRANSFERENCIAS por departamento
# ===========================================================================

DEPARTAMENTO_CHOICES = [
    app_commands.Choice(name=data["nombre"], value=slug)
    for slug, data in config.DEPARTAMENTOS.items()
]

# Igual que DEPARTAMENTO_CHOICES pero con la opción de solicitud general
# (RRHH / Administración general), usada por cartas de solicitud.
SOLICITUD_CHOICES = DEPARTAMENTO_CHOICES + [
    app_commands.Choice(name="General / RRHH", value="general")
]


async def _puede_gestionar_departamento(interaction: discord.Interaction, slug: str) -> bool:
    emisor = interaction.user
    if permisos.member_tiene_alguna_key(emisor, "OWNER"):
        return True
    director_key = config.DEPARTAMENTOS[slug]["director_key"]
    return permisos.member_tiene_key(emisor, director_key)


@bot.tree.command(name="ascenso", description="Asciende a un usuario dentro de un departamento")
@app_commands.describe(usuario="Usuario a ascender", departamento="Departamento")
@app_commands.choices(departamento=DEPARTAMENTO_CHOICES)
async def ascenso(interaction: discord.Interaction, usuario: discord.Member, departamento: app_commands.Choice[str]):
    slug = departamento.value
    if not await _puede_gestionar_departamento(interaction, slug):
        raise SinPermiso([config.DEPARTAMENTOS[slug]["director_key"], "OWNER"])

    cantidad = len(config.DEPARTAMENTOS[slug]["escalafon_nombres"])
    escalafon = roles_store.escalafon_ids(slug, cantidad)
    roles_usuario = {r.id for r in usuario.roles}
    posiciones = [i for i, rid in enumerate(escalafon) if rid and rid in roles_usuario]

    if not posiciones:
        await interaction.response.send_message(
            f"⚠️ {usuario.mention} no tiene ningún rol de este departamento todavía. "
            f"Usa `/contratar` o `/dar_rol` para darle el rol base primero.",
            ephemeral=True)
        return

    actual = max(posiciones)
    if actual + 1 >= len(escalafon):
        await interaction.response.send_message(
            f"⚠️ {usuario.mention} ya está en el rango máximo de {departamento.name}.",
            ephemeral=True)
        return

    guild = interaction.guild
    rol_actual = guild.get_role(escalafon[actual])
    rol_nuevo = guild.get_role(escalafon[actual + 1])

    try:
        if rol_actual:
            await usuario.remove_roles(rol_actual, reason="Ascenso")
        await usuario.add_roles(rol_nuevo, reason=f"Ascenso otorgado por {interaction.user}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ No tengo permisos suficientes.", ephemeral=True)
        return

    registros.registrar_evento_cargo(usuario.id, "ascenso", f"{departamento.name} → {rol_nuevo.name}", interaction.user.id)
    await interaction.response.send_message(
        f"⬆️ {usuario.mention} fue ascendido a **{rol_nuevo.name}** en {departamento.name}."
    )
    await enviar_log("log_ascensos", crear_embed(
        "finanzas", "⬆️ Ascenso",
        f"**{interaction.user}** ascendió a **{usuario}** a **{rol_nuevo.name}** ({departamento.name})"))


@bot.tree.command(name="descenso", description="Desciende a un usuario dentro de un departamento")
@app_commands.describe(usuario="Usuario a descender", departamento="Departamento")
@app_commands.choices(departamento=DEPARTAMENTO_CHOICES)
async def descenso(interaction: discord.Interaction, usuario: discord.Member, departamento: app_commands.Choice[str]):
    slug = departamento.value
    if not await _puede_gestionar_departamento(interaction, slug):
        raise SinPermiso([config.DEPARTAMENTOS[slug]["director_key"], "OWNER"])

    cantidad = len(config.DEPARTAMENTOS[slug]["escalafon_nombres"])
    escalafon = roles_store.escalafon_ids(slug, cantidad)
    roles_usuario = {r.id for r in usuario.roles}
    posiciones = [i for i, rid in enumerate(escalafon) if rid and rid in roles_usuario]

    if not posiciones:
        await interaction.response.send_message(
            f"⚠️ {usuario.mention} no tiene ningún rol de este departamento.", ephemeral=True
        )
        return

    actual = max(posiciones)
    if actual == 0:
        await interaction.response.send_message(
            f"⚠️ {usuario.mention} ya está en el rango más bajo de {departamento.name}.",
            ephemeral=True)
        return

    guild = interaction.guild
    rol_actual = guild.get_role(escalafon[actual])
    rol_nuevo = guild.get_role(escalafon[actual - 1])

    try:
        if rol_actual:
            await usuario.remove_roles(rol_actual, reason="Descenso")
        await usuario.add_roles(rol_nuevo, reason=f"Descenso otorgado por {interaction.user}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ No tengo permisos suficientes.", ephemeral=True)
        return

    registros.registrar_evento_cargo(usuario.id, "descenso", f"{departamento.name} → {rol_nuevo.name}", interaction.user.id)
    await interaction.response.send_message(
        f"⬇️ {usuario.mention} fue descendido a **{rol_nuevo.name}** en {departamento.name}."
    )
    await enviar_log("log_ascensos", crear_embed(
        "aviso", "⬇️ Descenso",
        f"**{interaction.user}** descendió a **{usuario}** a **{rol_nuevo.name}** ({departamento.name})"))


@bot.tree.command(name="transferir_departamento", description="Transfiere a un usuario de un departamento a otro")
@app_commands.describe(usuario="Usuario a transferir", origen="Departamento actual", destino="Departamento nuevo")
@app_commands.choices(origen=DEPARTAMENTO_CHOICES, destino=DEPARTAMENTO_CHOICES)
async def transferir_departamento(
    interaction: discord.Interaction,
    usuario: discord.Member,
    origen: app_commands.Choice[str],
    destino: app_commands.Choice[str]):
    autorizado = permisos.member_tiene_alguna_key(interaction.user, "OWNER") or (
        await _puede_gestionar_departamento(interaction, origen.value)
        and await _puede_gestionar_departamento(interaction, destino.value)
    )
    if not autorizado:
        raise SinPermiso(["Director de ambos departamentos", "OWNER"])

    guild = interaction.guild
    ids_origen = roles_store.escalafon_ids(origen.value, len(config.DEPARTAMENTOS[origen.value]["escalafon_nombres"]))
    roles_origen_usuario = [
        r for rid in ids_origen if rid and (r := guild.get_role(rid)) and r in usuario.roles
    ]

    ids_destino = roles_store.escalafon_ids(destino.value, len(config.DEPARTAMENTOS[destino.value]["escalafon_nombres"]))
    rol_base_destino = guild.get_role(ids_destino[0]) if ids_destino and ids_destino[0] else None

    if not rol_base_destino:
        await interaction.response.send_message(
            "❌ El rol base del departamento destino no existe todavía. Ejecuta `/configurar_roles`.",
            ephemeral=True)
        return

    try:
        if roles_origen_usuario:
            await usuario.remove_roles(*roles_origen_usuario, reason=f"Transferido por {interaction.user}")
        await usuario.add_roles(rol_base_destino, reason=f"Transferido por {interaction.user}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ No tengo permisos suficientes.", ephemeral=True)
        return

    registros.registrar_evento_cargo(
        usuario.id, "transferencia", f"{origen.name} → {destino.name}", interaction.user.id
    )
    await interaction.response.send_message(
        f"🔄 {usuario.mention} fue transferido de **{origen.name}** a **{destino.name}**."
    )
    await enviar_log("log_ascensos", crear_embed(
        "info", "🔄 Transferencia de departamento",
        f"**{interaction.user}** transfirió a **{usuario}** de **{origen.name}** a **{destino.name}**"))


# ===========================================================================
# 3) GESTIÓN DE PERSONAL (contratación, despido, suspensión, expedientes)
# ===========================================================================

@bot.tree.command(name="contratar", description="Contrata a un usuario y lo asigna a un departamento")
@app_commands.describe(usuario="Usuario a contratar", departamento="Departamento de destino")
@app_commands.choices(departamento=DEPARTAMENTO_CHOICES)
async def contratar(interaction: discord.Interaction, usuario: discord.Member, departamento: app_commands.Choice[str]):
    slug = departamento.value
    director_key = config.DEPARTAMENTOS[slug]["director_key"]
    if not permisos.member_tiene_alguna_key(
        interaction.user, "DIRECTOR_RRHH", director_key, "OWNER"
    ):
        raise SinPermiso(["DIRECTOR_RRHH", director_key, "OWNER"])

    guild = interaction.guild
    staff_id = roles_store.obtener_id_key("STAFF")
    base_id = roles_store.escalafon_ids(slug, 1)[0]
    roles_a_dar = [r for r in (guild.get_role(staff_id) if staff_id else None,
                               guild.get_role(base_id) if base_id else None) if r]

    if not roles_a_dar:
        await interaction.response.send_message(
            "❌ Los roles necesarios no existen todavía. Ejecuta `/configurar_roles` primero.", ephemeral=True
        )
        return

    try:
        await usuario.add_roles(*roles_a_dar, reason=f"Contratado por {interaction.user}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ No tengo permisos suficientes.", ephemeral=True)
        return

    registros.registrar_evento_cargo(usuario.id, "contratacion", f"Contratado en {departamento.name}", interaction.user.id)
    await interaction.response.send_message(f"✅ {usuario.mention} fue contratado en **{departamento.name}**.")
    await enviar_log("log_personal", crear_embed(
        "exito", "🆕 Contratación", f"**{interaction.user}** contrató a **{usuario}** en **{departamento.name}**"))


@bot.tree.command(name="despedir", description="Despide a un usuario (quita todas sus keys y roles de departamento)")
@app_commands.describe(usuario="Usuario a despedir", motivo="Motivo del despido")
@require_key("DIRECTOR_RRHH", "OWNER")
async def despedir(interaction: discord.Interaction, usuario: discord.Member, motivo: str = ""):
    emisor = interaction.user
    if not permisos.puede_actuar_sobre(emisor, usuario):
        await interaction.response.send_message(
            "❌ No puedes despedir a alguien de tu mismo nivel o superior.", ephemeral=True
        )
        return

    guild = interaction.guild
    roles_a_quitar = []
    for key in config.KEYS_NOMBRES:
        rid = roles_store.obtener_id_key(key)
        rol = guild.get_role(rid) if rid else None
        if rol and rol in usuario.roles:
            roles_a_quitar.append(rol)
    for slug, data in config.DEPARTAMENTOS.items():
        for rid in roles_store.escalafon_ids(slug, len(data["escalafon_nombres"])):
            rol = guild.get_role(rid) if rid else None
            if rol and rol in usuario.roles:
                roles_a_quitar.append(rol)

    if roles_a_quitar:
        try:
            await usuario.remove_roles(*roles_a_quitar, reason=f"Despedido por {emisor}: {motivo or 'sin motivo especificado'}")
        except discord.Forbidden:
            await interaction.response.send_message("❌ No tengo permisos suficientes.", ephemeral=True)
            return

    registros.registrar_evento_cargo(usuario.id, "despido", motivo or "sin motivo especificado", emisor.id)
    await interaction.response.send_message(f"✅ {usuario.mention} fue despedido.")
    await enviar_log("log_personal", crear_embed(
        "error", "🚫 Despido", f"**{emisor}** despidió a **{usuario}**\nMotivo: {motivo or '—'}"))



@bot.tree.command(name="sancion_interna", description="Registra una sanción interna y notifica a RRHH")
@app_commands.describe(usuario="Usuario sancionado", tipo="Tipo de sanción", motivo="Motivo")
@require_key("DIRECTOR_RRHH", "DIRECTOR_DISCIPLINA", "OWNER")
async def sancion_interna(interaction: discord.Interaction, usuario: discord.Member, tipo: str, motivo: str):
    embed = crear_embed(
        "aviso", "⚠️ Sanción interna",
        f"**Usuario:** {usuario.mention}\n**Tipo:** {tipo}\n**Motivo:** {motivo}",
        autor=interaction.user,
    )
    await enviar_solicitud(interaction, config.KEY_SANCIONES, embed, "log_sanciones")
    registros.registrar_evento_cargo(usuario.id, "sancion", f"{tipo}: {motivo}", interaction.user.id)
    await interaction.response.send_message(f"✅ Sanción registrada y enviada a RRHH para {usuario.mention}.")


@bot.tree.command(name="solicitud_investigacion", description="Solicita una investigación interna (se envía a RRHH)")
@app_commands.describe(usuario="Persona a investigar (opcional)", motivo="Motivo de la investigación")
@require_key("DIRECTOR", "JEFE_DEPARTAMENTO", "SUPERVISOR", "DIRECTOR_DISCIPLINA", "OWNER")
async def solicitud_investigacion(interaction: discord.Interaction, motivo: str, usuario: discord.Member = None):
    texto = f"**Motivo:** {motivo}"
    if usuario:
        texto = f"**Implicado:** {usuario.mention}\n" + texto
    embed = crear_embed("aviso", "🔎 Solicitud de investigación interna", texto, autor=interaction.user)
    await enviar_solicitud(interaction, config.KEY_INVESTIGACIONES, embed, "log_investigaciones")
    await interaction.response.send_message("✅ Solicitud de investigación enviada a **RRHH**.", ephemeral=True)


@bot.tree.command(name="suspender", description="Suspende temporalmente a un miembro (RRHH)")
@app_commands.describe(usuario="Usuario", motivo="Motivo de la suspensión")
@require_key("DIRECTOR_RRHH", "OWNER")
async def suspender(interaction: discord.Interaction, usuario: discord.Member, motivo: str):
    if not permisos.puede_actuar_sobre(interaction.user, usuario):
        await interaction.response.send_message(
            "❌ No puedes suspender a alguien de tu mismo nivel o superior.", ephemeral=True
        )
        return

    rol_id = roles_store.obtener_extra("SUSPENDIDO")
    rol = interaction.guild.get_role(rol_id) if rol_id else None
    if not rol:
        await interaction.response.send_message(
            "❌ El rol de suspensión no existe todavía. Ejecuta `/configurar_roles`.", ephemeral=True
        )
        return
    if rol in usuario.roles:
        await interaction.response.send_message(f"⚠️ {usuario.mention} ya está suspendido.", ephemeral=True)
        return

    try:
        await usuario.add_roles(rol, reason=f"Suspendido por {interaction.user}: {motivo}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ No tengo permisos suficientes.", ephemeral=True)
        return

    registros.registrar_evento_cargo(usuario.id, "suspension", motivo, interaction.user.id)
    embed = crear_embed("aviso", "⛔ Suspensión", motivo, autor=interaction.user)
    embed.add_field(name="Suspendido", value=usuario.mention)
    await interaction.response.send_message(embed=embed)
    await enviar_log("log_personal", embed)


@bot.tree.command(name="reincorporar", description="Reincorpora a un miembro suspendido")
@app_commands.describe(usuario="Usuario a reincorporar")
@require_key("SUPERVISOR", "JEFE_DEPARTAMENTO", "DIRECTOR", "OWNER")
async def reincorporar(interaction: discord.Interaction, usuario: discord.Member):
    rol_id = roles_store.obtener_extra("SUSPENDIDO")
    rol = interaction.guild.get_role(rol_id) if rol_id else None
    if not rol or rol not in usuario.roles:
        await interaction.response.send_message(f"⚠️ {usuario.mention} no está suspendido.", ephemeral=True)
        return

    try:
        await usuario.remove_roles(rol, reason=f"Reincorporado por {interaction.user}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ No tengo permisos suficientes.", ephemeral=True)
        return

    registros.registrar_evento_cargo(usuario.id, "reincorporacion", "Reincorporado", interaction.user.id)
    await interaction.response.send_message(f"✅ {usuario.mention} fue reincorporado.")
    await enviar_log("log_personal", crear_embed(
        "exito", "🔓 Reincorporación", f"**{interaction.user}** reincorporó a **{usuario}**"))


@bot.tree.command(name="licencia", description="Otorga una licencia/permiso oficial a un miembro del personal")
@app_commands.describe(usuario="Usuario", desde="Fecha de inicio", hasta="Fecha de fin", motivo="Motivo")
@require_key("SUPERVISOR", "JEFE_DEPARTAMENTO", "DIRECTOR", "OWNER")
async def licencia(interaction: discord.Interaction, usuario: discord.Member, desde: str, hasta: str, motivo: str):
    registros.registrar_licencia(usuario.id, motivo, desde, hasta, interaction.user.id)

    embed = crear_embed("aviso", "🗓️ Licencia/Permiso Otorgado", motivo, autor=interaction.user)
    embed.add_field(name="Beneficiario", value=usuario.mention)
    embed.add_field(name="Desde", value=desde)
    embed.add_field(name="Hasta", value=hasta)

    await interaction.response.send_message(embed=embed)
    await enviar_log("log_personal", embed)
    try:
        await usuario.send(embed=embed)
    except discord.Forbidden:
        pass


@bot.tree.command(name="expediente", description="Muestra el expediente completo de un miembro del personal")
@app_commands.describe(usuario="Usuario a consultar")
@require_key(
    "SUPERVISOR", "JEFE_DEPARTAMENTO", "DIRECTOR", "DIRECTOR_RRHH",
    "OWNER")
async def expediente(interaction: discord.Interaction, usuario: discord.Member):
    await _mostrar_expediente(interaction, usuario)


@bot.tree.command(name="mi_expediente", description="Muestra tu propio expediente")
async def mi_expediente(interaction: discord.Interaction):
    await _mostrar_expediente(interaction, interaction.user)


async def _mostrar_expediente(interaction: discord.Interaction, usuario: discord.Member):
    data = registros.expediente_completo(usuario.id)
    advertencias = data.get("advertencias", [])
    asistencia = data.get("asistencia", [])
    cargos = data.get("cargos", [])
    licencias = data.get("licencias", [])

    embed = crear_embed("info", f"📁 Expediente de {usuario.display_name}", "", autor=usuario)
    embed.add_field(name="Advertencias", value=str(len(advertencias)), inline=True)
    embed.add_field(name="Registros de asistencia", value=str(len(asistencia)), inline=True)
    embed.add_field(name="Balance", value=f"${economia.obtener_balance(usuario.id):,.2f}", inline=True)
    keys_actuales = permisos.keys_del_member(usuario)
    embed.add_field(name="Keys actuales", value=", ".join(keys_actuales) or "Ninguna", inline=False)

    if cargos:
        ultimos = "\n".join(f"`{c['fecha'][:10]}` {c['tipo']}: {c['detalle']}" for c in cargos[-5:])
        embed.add_field(name="Últimos movimientos de cargo", value=ultimos, inline=False)
    if licencias:
        ultimas = "\n".join(f"`{l['fecha'][:10]}` {l['desde']}–{l['hasta']}: {l['motivo']}" for l in licencias[-3:])
        embed.add_field(name="Últimas licencias", value=ultimas, inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ===========================================================================
# 4) DOCUMENTOS Y FORMULARIOS
# ===========================================================================

@bot.tree.command(name="documento_medico", description="Emite un documento médico oficial")
@app_commands.describe(paciente="Paciente", contenido="Contenido del documento")
@require_key("DIRECTOR_MEDICO", "OWNER")
async def documento_medico(interaction: discord.Interaction, paciente: discord.Member, contenido: str):
    embed = crear_embed("medico", "📋 Documento Médico Oficial", contenido)
    embed.add_field(name="Paciente", value=paciente.mention)
    embed.add_field(name="Emitido por", value=interaction.user.mention)

    await interaction.response.send_message(embed=embed)
    await enviar_log("log_documentos", embed)


@bot.tree.command(name="formulario", description="Emite un formulario/reporte oficial de tu dirección")
@app_commands.describe(titulo="Título del formulario", contenido="Contenido")
@require_key("DIRECTOR", "JEFE_DEPARTAMENTO", "OWNER")
async def formulario(interaction: discord.Interaction, titulo: str, contenido: str):
    embed = crear_embed("info", f"📄 {titulo}", contenido, autor=interaction.user)

    await interaction.response.send_message(embed=embed)
    await enviar_log("log_documentos", embed)


@bot.tree.command(name="reporte_departamento", description="Emite un reporte oficial de un departamento")
@app_commands.describe(departamento="Departamento", titulo="Título del reporte", contenido="Contenido")
@app_commands.choices(departamento=DEPARTAMENTO_CHOICES)
async def reporte_departamento(
    interaction: discord.Interaction, departamento: app_commands.Choice[str], titulo: str, contenido: str
):
    slug = departamento.value
    autorizado = await _puede_gestionar_departamento(interaction, slug) or (
        permisos.member_tiene_alguna_key(interaction.user, "JEFE_DEPARTAMENTO", "SUPERVISOR")
        and permisos.departamento_del_member(interaction.user) == slug
    )
    if not autorizado:
        raise SinPermiso([config.DEPARTAMENTOS[slug]["director_key"], "JEFE_DEPARTAMENTO", "SUPERVISOR"])

    embed = crear_embed("info", f"📊 Reporte de {departamento.name}: {titulo}", contenido, autor=interaction.user)
    await interaction.response.send_message(embed=embed)
    await enviar_log("log_documentos", embed)


# ===========================================================================
# 5) SISTEMA FINANCIERO
# ===========================================================================

@bot.tree.command(name="balance", description="Consulta tu balance o el de otro usuario")
@app_commands.describe(usuario="Usuario a consultar (opcional)")
async def balance(interaction: discord.Interaction, usuario: discord.Member = None):
    objetivo = usuario or interaction.user
    if usuario and usuario != interaction.user:
        if not permisos.member_tiene_alguna_key(
            interaction.user, "OWNER", "DIRECTOR_FINANCIERO"
        ):
            await interaction.response.send_message(
                "❌ Solo puedes consultar tu propio balance.", ephemeral=True
            )
            return
    saldo = economia.obtener_balance(objetivo.id)
    await interaction.response.send_message(f"💰 Balance de {objetivo.mention}: **${saldo:,.2f}**", ephemeral=True)


@bot.tree.command(name="depositar", description="Deposita fondos a un usuario")
@app_commands.describe(usuario="Usuario", monto="Monto a depositar", motivo="Motivo (opcional)")
@require_key("OWNER", "DIRECTOR_FINANCIERO")
async def depositar(interaction: discord.Interaction, usuario: discord.Member, monto: float, motivo: str = ""):
    if monto <= 0:
        await interaction.response.send_message("❌ El monto debe ser mayor a 0.", ephemeral=True)
        return
    nuevo = economia.modificar_balance(usuario.id, monto)
    economia.registrar_movimiento("deposito", interaction.user.id, usuario.id, monto, motivo)
    await interaction.response.send_message(
        f"✅ Se depositaron **${monto:,.2f}** a {usuario.mention}. Nuevo balance: **${nuevo:,.2f}**"
    )
    await enviar_log("log_finanzas", crear_embed(
        "exito", "💰 Depósito",
        f"**{interaction.user}** depositó **${monto:,.2f}** a **{usuario}**\nMotivo: {motivo or '—'}"))


@bot.tree.command(name="retirar", description="Retira fondos a un usuario")
@app_commands.describe(usuario="Usuario", monto="Monto a retirar", motivo="Motivo (opcional)")
@require_key("OWNER", "DIRECTOR_FINANCIERO")
async def retirar(interaction: discord.Interaction, usuario: discord.Member, monto: float, motivo: str = ""):
    if monto <= 0:
        await interaction.response.send_message("❌ El monto debe ser mayor a 0.", ephemeral=True)
        return
    try:
        nuevo = economia.modificar_balance(usuario.id, -monto)
    except ValueError:
        await interaction.response.send_message(
            f"❌ {usuario.mention} no tiene fondos suficientes para retirar esa cantidad.", ephemeral=True
        )
        return
    economia.registrar_movimiento("retiro", interaction.user.id, usuario.id, -monto, motivo)
    await interaction.response.send_message(
        f"✅ Se retiraron **${monto:,.2f}** a {usuario.mention}. Nuevo balance: **${nuevo:,.2f}**"
    )
    await enviar_log("log_finanzas", crear_embed(
        "error", "💸 Retiro",
        f"**{interaction.user}** retiró **${monto:,.2f}** a **{usuario}**\nMotivo: {motivo or '—'}"))


@bot.tree.command(name="transferir", description="Transfiere fondos de tu balance a otro usuario")
@app_commands.describe(usuario="Usuario destino", monto="Monto a transferir")
async def transferir(interaction: discord.Interaction, usuario: discord.Member, monto: float):
    if monto <= 0:
        await interaction.response.send_message("❌ El monto debe ser mayor a 0.", ephemeral=True)
        return
    if usuario.id == interaction.user.id:
        await interaction.response.send_message("❌ No puedes transferirte a ti mismo.", ephemeral=True)
        return
    try:
        economia.modificar_balance(interaction.user.id, -monto)
    except ValueError:
        await interaction.response.send_message("❌ No tienes fondos suficientes.", ephemeral=True)
        return
    economia.modificar_balance(usuario.id, monto)
    economia.registrar_movimiento("transferencia", interaction.user.id, usuario.id, monto)
    await interaction.response.send_message(
        f"✅ Transferiste **${monto:,.2f}** a {usuario.mention}."
    )
    await enviar_log("log_finanzas", crear_embed(
        "info", "🔄 Transferencia",
        f"**{interaction.user}** transfirió **${monto:,.2f}** a **{usuario}**"))


@bot.tree.command(name="pagar_salario", description="Paga salario a todos los usuarios con un rol")
@app_commands.describe(rol="Rol a pagar", monto="Monto por persona")
@require_key("OWNER", "DIRECTOR_FINANCIERO")
async def pagar_salario(interaction: discord.Interaction, rol: discord.Role, monto: float):
    if monto <= 0:
        await interaction.response.send_message("❌ El monto debe ser mayor a 0.", ephemeral=True)
        return
    await interaction.response.defer()
    miembros = [m for m in rol.members if not m.bot]
    for m in miembros:
        economia.modificar_balance(m.id, monto)
        economia.registrar_movimiento("salario", interaction.user.id, m.id, monto, f"Pago masivo: {rol.name}")
    await interaction.followup.send(
        f"✅ Se pagaron **${monto:,.2f}** a **{len(miembros)}** miembros con el rol **{rol.name}**."
    )
    await enviar_log("log_finanzas", crear_embed(
        "finanzas", "💵 Pago de salarios",
        f"**{interaction.user}** pagó **${monto:,.2f}** a {len(miembros)} miembros de **{rol.name}**"))


@bot.tree.command(name="historial_financiero", description="Muestra tus últimos movimientos financieros")
async def historial_financiero(interaction: discord.Interaction):
    movimientos = economia.ultimos_movimientos(interaction.user.id, limite=10)
    if not movimientos:
        await interaction.response.send_message("No tienes movimientos registrados.", ephemeral=True)
        return
    lineas = []
    for m in movimientos:
        signo = "+" if m["monto"] >= 0 else "-"
        lineas.append(f"`{m['fecha'][:10]}` {m['tipo']}: {signo}${abs(m['monto']):,.2f}")
    await interaction.response.send_message("\n".join(lineas), ephemeral=True)


@bot.tree.command(name="balance_general", description="Muestra un resumen financiero general del hospital")
@require_key("DIRECTOR_FINANCIERO", "OWNER")
async def balance_general(interaction: discord.Interaction):
    resumen = economia.resumen_general()
    embed = crear_embed("finanzas", "📊 Resumen Financiero General", "")
    embed.add_field(name="Total en circulación", value=f"${resumen['total_en_circulacion']:,.2f}", inline=True)
    embed.add_field(name="Cuentas activas", value=str(resumen["cuentas_activas"]), inline=True)
    if resumen["ultimos_movimientos"]:
        lineas = [f"`{m['fecha'][:10]}` {m['tipo']}: ${m['monto']:,.2f}" for m in resumen["ultimos_movimientos"]]
        embed.add_field(name="Últimos movimientos", value="\n".join(lineas), inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ===========================================================================
# 6) PANELES INTERACTIVOS (botones / menús)
# ===========================================================================

@bot.tree.command(name="panel_tickets", description="Publica el panel de tickets con botón interactivo")
@require_key("OWNER", "DIRECTOR")
async def panel_tickets(interaction: discord.Interaction):
    embed = crear_embed(
        "info",
        "🎫 Centro de Soporte",
        "¿Necesitas ayuda, reportar una situación o hacer una solicitud?\n"
        "Presiona el botón de abajo para abrir un ticket privado con el personal correspondiente.")
    await interaction.response.send_message(embed=embed, view=AbrirTicketView())


@bot.tree.command(name="panel_acciones", description="Publica el panel de acciones rápidas (botones)")
async def panel_acciones(interaction: discord.Interaction):
    embed = crear_embed(
        "info",
        "⚙️ Panel de Acciones Rápidas",
        "Usa los botones de abajo para acceder rápido a las funciones más comunes del bot. "
        "Cada botón respeta tu cargo/key actual.")
    await interaction.response.send_message(embed=embed, view=PanelAccionesView())


# ===========================================================================
# 7) ACCIONES DE JEFATURA (Directores / Dirección)
# ===========================================================================

@bot.tree.command(name="convocar_directores", description="Convoca una reunión de los Directores")
@app_commands.describe(titulo="Motivo de la reunión", fecha_hora="Fecha y hora", detalles="Detalles adicionales (opcional)")
@require_key("OWNER", "CO_OWNER", "DIRECTOR")
async def convocar_directores(interaction: discord.Interaction, titulo: str, fecha_hora: str, detalles: str = ""):
    embed = crear_embed("info", f"🏛️ Convocatoria de Directores: {titulo}", detalles, autor=interaction.user)
    embed.add_field(name="Fecha y hora", value=fecha_hora)

    menciones = []
    for dk in config.DIRECTOR_KEYS:
        rid = roles_store.obtener_id_key(dk)
        if rid:
            rol = interaction.guild.get_role(rid)
            if rol:
                menciones.append(rol.mention)
    content = " ".join(menciones) if menciones else None

    await interaction.response.send_message(content=content, embed=embed)




@bot.tree.command(name="anuncio", description="Publica un anuncio oficial del hospital")
@app_commands.describe(titulo="Título del anuncio", mensaje="Contenido del anuncio")
@require_key("DIRECTOR", "OWNER")
async def anuncio(interaction: discord.Interaction, titulo: str, mensaje: str):
    embed = crear_embed("info", f"📢 {titulo}", mensaje, autor=interaction.user)
    await interaction.response.send_message(embed=embed)


class VotacionView(discord.ui.View):
    """
    Vista de votación para Directores. No es persistente entre
    reinicios del bot (cada votación vive mientras el bot siga
    corriendo) — suficiente para una sesión de votación puntual.
    """

    def __init__(self, key_autorizada: str):
        super().__init__(timeout=None)
        self.votos = {}
        self.key_autorizada = key_autorizada

    def _autorizado(self, member: discord.Member) -> bool:
        return permisos.member_tiene_alguna_key(member, self.key_autorizada, "OWNER")

    def _resultado(self) -> str:
        conteo = {"si": 0, "no": 0, "abstencion": 0}
        for v in self.votos.values():
            conteo[v] += 1
        return f"✅ Sí: {conteo['si']} | ❌ No: {conteo['no']} | ⚪ Abstención: {conteo['abstencion']}"

    async def _votar(self, interaction: discord.Interaction, opcion: str):
        if not self._autorizado(interaction.user):
            await interaction.response.send_message("❌ No tienes voto en esta votación.", ephemeral=True)
            return
        self.votos[interaction.user.id] = opcion
        embed = interaction.message.embeds[0]
        embed.set_field_at(0, name="Resultados", value=self._resultado())
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="✅ Sí", style=discord.ButtonStyle.success, custom_id="hospital:voto_si")
    async def si(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._votar(interaction, "si")

    @discord.ui.button(label="❌ No", style=discord.ButtonStyle.danger, custom_id="hospital:voto_no")
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._votar(interaction, "no")

    @discord.ui.button(label="⚪ Abstención", style=discord.ButtonStyle.secondary, custom_id="hospital:voto_abstencion")
    async def abstencion(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._votar(interaction, "abstencion")


@bot.tree.command(name="votacion", description="Abre una votación entre Directores")
@app_commands.describe(titulo="Tema a votar")
@require_key("OWNER", "CO_OWNER", "DIRECTOR")
async def votacion(interaction: discord.Interaction, titulo: str):
    embed = crear_embed(
        "info", f"🗳️ Votación: {titulo}", "Directores, emitan su voto.", autor=interaction.user
    )
    embed.add_field(name="Resultados", value="✅ Sí: 0 | ❌ No: 0 | ⚪ Abstención: 0")
    await interaction.response.send_message(embed=embed, view=VotacionView("DIRECTOR"))


@bot.tree.command(name="organigrama", description="Muestra el organigrama jerárquico del hospital")
async def organigrama(interaction: discord.Interaction):
    lineas = []
    for i, key in enumerate(reversed(config.JERARQUIA_KEYS)):
        if key == "DIRECTOR":
            nombre = "Director(es) de Área"
        else:
            nombre = config.KEYS_NOMBRES.get(key, (key))[0]
        lineas.append(f"{'　' * i}└ {nombre}")
    embed = crear_embed("info", "🏥 Organigrama General", "\n".join(lineas))

    depto_texto = "\n\n".join(
        f"**{d['nombre']}**\n" + " → ".join(d["escalafon_nombres"])
        for d in config.DEPARTAMENTOS.values()
    )
    embed2 = crear_embed("info", "🗂️ Escalafones por Departamento", depto_texto[:4000])
    await interaction.response.send_message(embeds=[embed, embed2])


# ===========================================================================
# 8) ACCIONES DE JEFES DE DEPARTAMENTO Y SUPERVISORES
# ===========================================================================

ESTADO_ASISTENCIA_CHOICES = [
    app_commands.Choice(name="Presente", value="Presente"),
    app_commands.Choice(name="Tardanza", value="Tardanza"),
    app_commands.Choice(name="Ausente", value="Ausente"),
]


@bot.tree.command(name="marcar_asistencia", description="Registra la asistencia de un miembro del personal")
@app_commands.describe(usuario="Usuario", estado="Estado de asistencia")
@app_commands.choices(estado=ESTADO_ASISTENCIA_CHOICES)
@require_key("SUPERVISOR", "JEFE_DEPARTAMENTO", "DIRECTOR", "OWNER")
async def marcar_asistencia(interaction: discord.Interaction, usuario: discord.Member, estado: app_commands.Choice[str]):
    registros.registrar_asistencia(usuario.id, estado.value, interaction.user.id)
    await interaction.response.send_message(
        f"✅ Asistencia registrada: {usuario.mention} — **{estado.value}**"
    )
    await enviar_log("log_personal", crear_embed(
        "info", "Asistencia registrada",
        f"**{interaction.user}** marcó a **{usuario}** como **{estado.value}**"))


@bot.tree.command(name="advertencia", description="Emite una advertencia formal a un miembro del personal")
@app_commands.describe(usuario="Usuario", motivo="Motivo de la advertencia")
@require_key("SUPERVISOR", "JEFE_DEPARTAMENTO", "DIRECTOR", "OWNER")
async def advertencia(interaction: discord.Interaction, usuario: discord.Member, motivo: str):
    registros.registrar_advertencia(usuario.id, motivo, interaction.user.id)

    embed = crear_embed("aviso", "⚠️ Advertencia Formal", motivo, autor=interaction.user)
    embed.add_field(name="Emitida a", value=usuario.mention)

    await interaction.response.send_message(embed=embed)
    await enviar_log("log_personal", embed)

    try:
        await usuario.send(embed=embed)
    except discord.Forbidden:
        pass


@bot.tree.command(name="historial_advertencias", description="Muestra las advertencias registradas de un usuario")
@app_commands.describe(usuario="Usuario a consultar")
@require_key("SUPERVISOR", "JEFE_DEPARTAMENTO", "DIRECTOR", "OWNER")
async def historial_advertencias(interaction: discord.Interaction, usuario: discord.Member):
    lista = registros.advertencias_de(usuario.id)
    if not lista:
        await interaction.response.send_message(f"{usuario.mention} no tiene advertencias registradas.", ephemeral=True)
        return
    lineas = [f"`{a['fecha'][:10]}` — {a['motivo']}" for a in lista[-10:]]
    await interaction.response.send_message(
        f"⚠️ Advertencias de {usuario.mention}:\n" + "\n".join(lineas), ephemeral=True
    )


@bot.tree.command(name="convocar_reunion_departamento", description="Convoca una reunión para tu departamento")
@app_commands.describe(
    departamento="Departamento", titulo="Motivo de la reunión",
    fecha_hora="Fecha y hora", detalles="Detalles adicionales (opcional)")
@app_commands.choices(departamento=DEPARTAMENTO_CHOICES)
async def convocar_reunion_departamento(
    interaction: discord.Interaction,
    departamento: app_commands.Choice[str],
    titulo: str,
    fecha_hora: str,
    detalles: str = ""):
    slug = departamento.value
    autorizado = await _puede_gestionar_departamento(interaction, slug) or (
        permisos.member_tiene_alguna_key(interaction.user, "JEFE_DEPARTAMENTO", "SUPERVISOR")
        and permisos.departamento_del_member(interaction.user) == slug
    )
    if not autorizado:
        raise SinPermiso([config.DEPARTAMENTOS[slug]["director_key"], "JEFE_DEPARTAMENTO", "SUPERVISOR"])

    ids = roles_store.escalafon_ids(slug, len(config.DEPARTAMENTOS[slug]["escalafon_nombres"]))
    roles_mencionables = [interaction.guild.get_role(i) for i in ids if i and interaction.guild.get_role(i)]
    menciones = " ".join(r.mention for r in roles_mencionables)

    embed = crear_embed("info", f"📅 Reunión de {departamento.name}: {titulo}", detalles, autor=interaction.user)
    embed.add_field(name="Fecha y hora", value=fecha_hora)
    await interaction.response.send_message(content=menciones, embed=embed)


@bot.tree.command(name="asignar_tarea", description="Asigna una tarea a un miembro del personal (se le envía por DM)")
@app_commands.describe(usuario="Usuario", tarea="Descripción de la tarea", plazo="Plazo (opcional)")
@require_key("SUPERVISOR", "JEFE_DEPARTAMENTO", "DIRECTOR", "OWNER")
async def asignar_tarea(interaction: discord.Interaction, usuario: discord.Member, tarea: str, plazo: str = "Sin plazo definido"):
    embed = crear_embed("info", "📌 Nueva tarea asignada", tarea, autor=interaction.user)
    embed.add_field(name="Plazo", value=plazo)
    embed.add_field(name="Asignada por", value=interaction.user.mention)

    try:
        await usuario.send(embed=embed)
        await interaction.response.send_message(f"✅ Tarea asignada a {usuario.mention} (enviada por DM).", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message(
            f"⚠️ No pude enviarle DM a {usuario.mention} (mensajes privados cerrados). "
            "La tarea no se pudo notificar.",
            ephemeral=True)


# ===========================================================================
# 9) CARTAS DE SOLICITUD (rellenables, enviadas por DM a la entidad superior)
# ===========================================================================

@bot.tree.command(name="carta_solicitud", description="Envía una carta de solicitud rellenable al encargado de un área")
@app_commands.describe(departamento="Área destinataria", asunto="Asunto de la carta")
@app_commands.choices(departamento=SOLICITUD_CHOICES)
async def carta_solicitud(interaction: discord.Interaction, departamento: app_commands.Choice[str], asunto: str):
    # BUG CORREGIDO: se llamaba a CartaSolicitudModal(asunto, departamento.value,
    # departamento.name) — 3 argumentos en el orden equivocado respecto al
    # constructor de la clase (departamento_slug, departamento_nombre,
    # asunto_sugerido), lo que hacía truenar el comando con TypeError.
    await interaction.response.send_modal(
        CartaSolicitudModal(departamento.value, departamento.name, asunto)
    )


@bot.tree.command(name="solicitud_descargo", description="Envía una solicitud de descargo/degradación al encargado de RRHH")
@app_commands.describe(
    usuario="Persona afectada", cargo_actual="Cargo actual", cargo_propuesto="Cargo propuesto tras el descargo"
)
@require_key("SUPERVISOR", "JEFE_DEPARTAMENTO", "DIRECTOR", "OWNER")
async def solicitud_descargo(
    interaction: discord.Interaction, usuario: discord.Member, cargo_actual: str, cargo_propuesto: str
):
    await interaction.response.send_modal(
        SolicitudDescargoModal(usuario, cargo_actual, cargo_propuesto)
    )


@bot.tree.command(name="solicitud_permiso", description="Solicita un permiso/licencia; se envía a tu propio departamento")
async def solicitud_permiso(interaction: discord.Interaction):
    slug = permisos.departamento_del_member(interaction.user)
    if slug:
        nombre = config.DEPARTAMENTOS[slug]["nombre"]
    else:
        slug = "general"
        nombre = "General / RRHH"
    await interaction.response.send_modal(SolicitudPermisoModal(slug, nombre))


# ===========================================================================
# 10) INFO DE PERMISOS
# ===========================================================================

@bot.tree.command(name="mis_permisos", description="Muestra tus keys de permisos actuales")
async def mis_permisos(interaction: discord.Interaction):
    keys = permisos.keys_del_member(interaction.user)
    if not keys:
        await interaction.response.send_message(
            "No tienes ninguna key de permisos asignada.", ephemeral=True
        )
        return
    await interaction.response.send_message(
        f"🔑 Tus keys: **{', '.join(keys)}**", ephemeral=True
    )


# ===========================================================================
# 11) PACIENTES
# ===========================================================================

GRAVEDAD_CHOICES = [app_commands.Choice(name=g, value=g) for g in config.GRAVEDAD_PACIENTE]


def _es_personal_medico(member: discord.Member) -> bool:
    if permisos.member_tiene_alguna_key(
        member, "DIRECTOR_MEDICO", "DIRECTOR_ENFERMERIA", "OWNER"
    ):
        return True
    return permisos.departamento_del_member(member) in ("medico", "enfermeria")


def _require_personal_medico(interaction: discord.Interaction):
    if not _es_personal_medico(interaction.user):
        raise SinPermiso(["Cuerpo Médico", "Enfermería", "DIRECTOR_MEDICO", "DIRECTOR_ENFERMERIA", "OWNER"])


grupo_paciente = app_commands.Group(name="paciente", description="Sistema de pacientes del hospital")


@grupo_paciente.command(name="admitir", description="Admite a un paciente")
@app_commands.describe(usuario="Paciente", gravedad="Gravedad", motivo="Motivo de ingreso", cama="Cama (opcional)", area="Área/ala (opcional)")
@app_commands.choices(gravedad=GRAVEDAD_CHOICES)
async def paciente_admitir(
    interaction: discord.Interaction, usuario: discord.Member, gravedad: app_commands.Choice[str],
    motivo: str, cama: str = "", area: str = ""):
    _require_personal_medico(interaction)
    if pacientes.esta_admitido(usuario.id):
        await interaction.response.send_message(f"⚠️ {usuario.mention} ya está admitido.", ephemeral=True)
        return

    pacientes.admitir(usuario.id, gravedad.value, motivo, interaction.user.id, cama, area)
    embed = crear_embed("medico", "🛏️ Paciente Admitido", motivo, autor=interaction.user)
    embed.add_field(name="Paciente", value=usuario.mention)
    embed.add_field(name="Gravedad", value=gravedad.value)
    if area:
        embed.add_field(name="Área", value=area)
    if cama:
        embed.add_field(name="Cama", value=cama)

    await interaction.response.send_message(embed=embed)
    await enviar_log("log_pacientes", embed)


@grupo_paciente.command(name="alta", description="Da de alta a un paciente admitido")
@app_commands.describe(usuario="Paciente", resumen="Resumen clínico del alta")
async def paciente_alta(interaction: discord.Interaction, usuario: discord.Member, resumen: str):
    _require_personal_medico(interaction)
    if not pacientes.esta_admitido(usuario.id):
        await interaction.response.send_message(f"⚠️ {usuario.mention} no está admitido actualmente.", ephemeral=True)
        return

    pacientes.dar_alta(usuario.id, resumen, interaction.user.id)
    embed = crear_embed("exito", "✅ Alta Médica", resumen, autor=interaction.user)
    embed.add_field(name="Paciente", value=usuario.mention)

    await interaction.response.send_message(embed=embed)
    await enviar_log("log_pacientes", embed)


@grupo_paciente.command(name="nota", description="Agrega una nota clínica a la ficha de un paciente")
@app_commands.describe(usuario="Paciente", texto="Nota clínica")
async def paciente_nota(interaction: discord.Interaction, usuario: discord.Member, texto: str):
    _require_personal_medico(interaction)
    pacientes.agregar_nota(usuario.id, texto, interaction.user.id)
    embed = crear_embed("medico", "📝 Nota Clínica Agregada", texto, autor=interaction.user)
    embed.add_field(name="Paciente", value=usuario.mention)
    await interaction.response.send_message(embed=embed)
    await enviar_log("log_pacientes", embed)


@grupo_paciente.command(name="gravedad", description="Actualiza el nivel de gravedad de un paciente admitido")
@app_commands.describe(usuario="Paciente", gravedad="Nueva gravedad")
@app_commands.choices(gravedad=GRAVEDAD_CHOICES)
async def paciente_gravedad(interaction: discord.Interaction, usuario: discord.Member, gravedad: app_commands.Choice[str]):
    _require_personal_medico(interaction)
    if not pacientes.esta_admitido(usuario.id):
        await interaction.response.send_message(f"⚠️ {usuario.mention} no está admitido actualmente.", ephemeral=True)
        return
    pacientes.cambiar_gravedad(usuario.id, gravedad.value)
    await interaction.response.send_message(f"✅ Gravedad de {usuario.mention} actualizada a **{gravedad.value}**.")
    await enviar_log("log_pacientes", crear_embed(
        "aviso", "Gravedad actualizada", f"**{interaction.user}** cambió la gravedad de **{usuario}** a **{gravedad.value}**"))


@grupo_paciente.command(name="transferir", description="Transfiere a un paciente admitido a otra área/cama")
@app_commands.describe(usuario="Paciente", area="Área/ala nueva", cama="Cama nueva (opcional)")
async def paciente_transferir(interaction: discord.Interaction, usuario: discord.Member, area: str, cama: str = ""):
    _require_personal_medico(interaction)
    if not pacientes.esta_admitido(usuario.id):
        await interaction.response.send_message(f"⚠️ {usuario.mention} no está admitido actualmente.", ephemeral=True)
        return
    pacientes.transferir_area(usuario.id, area, cama or None)
    await interaction.response.send_message(f"🔄 {usuario.mention} fue transferido a **{area}**{f' (cama {cama})' if cama else ''}.")
    await enviar_log("log_pacientes", crear_embed(
        "info", "Traslado de paciente", f"**{interaction.user}** trasladó a **{usuario}** a **{area}**"))


@grupo_paciente.command(name="ver", description="Muestra la ficha clínica de un paciente")
@app_commands.describe(usuario="Paciente a consultar")
async def paciente_ver(interaction: discord.Interaction, usuario: discord.Member):
    _require_personal_medico(interaction)
    ficha = pacientes.ficha_de(usuario.id)
    if not ficha:
        await interaction.response.send_message(f"{usuario.mention} no tiene ficha clínica registrada.", ephemeral=True)
        return

    embed = crear_embed("medico", f"🩺 Ficha Clínica de {usuario.display_name}", "", autor=usuario)
    if ficha.get("admitido"):
        embed.add_field(name="Estado", value=f"🛏️ Admitido — {ficha.get('gravedad', 'Sin clasificar')}", inline=False)
        embed.add_field(name="Motivo de ingreso", value=ficha.get("motivo") or "—", inline=False)
        if ficha.get("area"):
            embed.add_field(name="Área", value=ficha["area"], inline=True)
        if ficha.get("cama"):
            embed.add_field(name="Cama", value=ficha["cama"], inline=True)
    else:
        embed.add_field(name="Estado", value="No admitido actualmente.", inline=False)

    notas = ficha.get("notas", [])
    if notas:
        texto_notas = "\n".join(f"`{n['fecha'][:10]}` {n['texto']}" for n in notas[-5:])
        embed.add_field(name="Últimas notas clínicas", value=texto_notas[:1024], inline=False)

    historial = ficha.get("historial", [])
    if historial:
        texto_hist = "\n".join(
            f"`{h['fecha_admision'][:10] if h.get('fecha_admision') else '?'}` {h['motivo']} ({h['gravedad']})"
            for h in historial[-5:]
        )
        embed.add_field(name="Admisiones anteriores", value=texto_hist[:1024], inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


@grupo_paciente.command(name="listar", description="Lista todos los pacientes admitidos actualmente")
async def paciente_listar(interaction: discord.Interaction):
    _require_personal_medico(interaction)
    admitidos = pacientes.admitidos()
    if not admitidos:
        await interaction.response.send_message("No hay pacientes admitidos actualmente.", ephemeral=True)
        return
    lineas = []
    for uid, ficha in admitidos:
        member = interaction.guild.get_member(uid)
        nombre = member.mention if member else f"`{uid}`"
        lineas.append(f"{nombre} — {ficha.get('gravedad', '?')} ({ficha.get('area') or 'sin área'})")
    embed = crear_embed("medico", f"🛏️ Pacientes Admitidos ({len(admitidos)})", "\n".join(lineas)[:4000])
    await interaction.response.send_message(embed=embed, ephemeral=True)


bot.tree.add_command(grupo_paciente)


# ===========================================================================
# 12) INVENTARIO / LOGÍSTICA
# ===========================================================================

CATEGORIA_CHOICES = [app_commands.Choice(name=c, value=c) for c in config.CATEGORIAS_INVENTARIO]

grupo_inventario = app_commands.Group(name="inventario", description="Sistema de inventario y logística del hospital")


@grupo_inventario.command(name="agregar", description="Agrega stock de un ítem al inventario")
@app_commands.describe(item="Nombre del ítem", cantidad="Cantidad a agregar", categoria="Categoría (opcional)")
@app_commands.choices(categoria=CATEGORIA_CHOICES)
@require_key("DIRECTOR_LOGISTICA", "OWNER")
async def inventario_agregar(
    interaction: discord.Interaction, item: str, cantidad: int, categoria: app_commands.Choice[str] = None
):
    try:
        nuevo_total = inventario.agregar_stock(item, cantidad, categoria.value if categoria else "", interaction.user.id)
    except ValueError as e:
        await interaction.response.send_message(f"❌ {e}", ephemeral=True)
        return
    await interaction.response.send_message(f"✅ Se agregaron **{cantidad}** de **{item}**. Stock actual: **{nuevo_total}**.")
    await enviar_log("log_inventario", crear_embed(
        "exito", "📦 Entrada de inventario", f"**{interaction.user}** agregó **{cantidad}** de **{item}**"))


@grupo_inventario.command(name="retirar", description="Retira/consume stock de un ítem del inventario")
@app_commands.describe(item="Nombre del ítem", cantidad="Cantidad a retirar", motivo="Motivo (opcional)")
@require_key("DIRECTOR_LOGISTICA", "OWNER")
async def inventario_retirar(interaction: discord.Interaction, item: str, cantidad: int, motivo: str = ""):
    try:
        nuevo_total = inventario.retirar_stock(item, cantidad, interaction.user.id, motivo)
    except ValueError as e:
        await interaction.response.send_message(f"❌ {e}", ephemeral=True)
        return
    except LookupError as e:
        await interaction.response.send_message(f"❌ {e}", ephemeral=True)
        return
    await interaction.response.send_message(f"✅ Se retiraron **{cantidad}** de **{item}**. Stock actual: **{nuevo_total}**.")
    await enviar_log("log_inventario", crear_embed(
        "aviso", "📦 Salida de inventario", f"**{interaction.user}** retiró **{cantidad}** de **{item}**\nMotivo: {motivo or '—'}"))
    item_data = inventario.obtener_item(item)
    if item_data and item_data["cantidad"] <= item_data.get("minimo", 0):
        await enviar_log("log_inventario", crear_embed(
            "error", "⚠️ Stock bajo mínimo", f"**{item_data['nombre']}** quedó en **{item_data['cantidad']}** (mínimo {item_data['minimo']})."))


@grupo_inventario.command(name="set_minimo", description="Define el mínimo de alerta de un ítem")
@app_commands.describe(item="Nombre del ítem", minimo="Cantidad mínima antes de alertar")
@require_key("DIRECTOR_LOGISTICA", "OWNER")
async def inventario_set_minimo(interaction: discord.Interaction, item: str, minimo: int):
    try:
        inventario.set_minimo(item, minimo)
    except LookupError as e:
        await interaction.response.send_message(f"❌ {e}", ephemeral=True)
        return
    await interaction.response.send_message(f"✅ Mínimo de **{item}** establecido en **{minimo}**.")


@grupo_inventario.command(name="stock", description="Consulta el stock de un ítem, o el resumen general si no indicas uno")
@app_commands.describe(item="Nombre del ítem (opcional)")
async def inventario_stock(interaction: discord.Interaction, item: str = None):
    if item:
        data = inventario.obtener_item(item)
        if not data:
            await interaction.response.send_message(f"No hay registro del ítem **{item}**.", ephemeral=True)
            return
        embed = crear_embed("info", f"📦 {data['nombre']}", "")
        embed.add_field(name="Cantidad", value=str(data["cantidad"]), inline=True)
        embed.add_field(name="Mínimo", value=str(data.get("minimo", 0)), inline=True)
        embed.add_field(name="Categoría", value=data.get("categoria", "—"), inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    items = inventario.todos_los_items()
    if not items:
        await interaction.response.send_message("El inventario está vacío.", ephemeral=True)
        return
    lineas = [f"{'⚠️ ' if i['cantidad'] <= i.get('minimo', 0) else ''}{i['nombre']}: {i['cantidad']}" for i in items[:30]]
    embed = crear_embed("info", "📦 Inventario General", "\n".join(lineas)[:4000])
    await interaction.response.send_message(embed=embed, ephemeral=True)


@grupo_inventario.command(name="solicitar", description="Solicita insumos a Logística")
@app_commands.describe(item="Ítem solicitado", cantidad="Cantidad", motivo="Motivo (opcional)")
async def inventario_solicitar(interaction: discord.Interaction, item: str, cantidad: int, motivo: str = ""):
    embed = crear_embed("aviso", "📦 Solicitud de Insumos", motivo or "Sin motivo especificado.", autor=interaction.user)
    embed.add_field(name="Ítem", value=item)
    embed.add_field(name="Cantidad", value=str(cantidad))
    embed.add_field(name="Solicitante", value=interaction.user.mention)
    await enviar_solicitud(interaction, "DIRECTOR_LOGISTICA", embed, "log_inventario")


bot.tree.add_command(grupo_inventario)


# ===========================================================================
# 13) TURNOS
# ===========================================================================

grupo_turno = app_commands.Group(name="turno", description="Sistema de turnos del personal")


@grupo_turno.command(name="asignar", description="Asigna un turno programado a un miembro del personal")
@app_commands.describe(usuario="Usuario", dia="Día (Ej: Lunes, 20/09)", hora_inicio="Hora de inicio", hora_fin="Hora de fin", area="Área/departamento (opcional)")
@require_key("SUPERVISOR", "JEFE_DEPARTAMENTO", "DIRECTOR", "OWNER")
async def turno_asignar(interaction: discord.Interaction, usuario: discord.Member, dia: str, hora_inicio: str, hora_fin: str, area: str = ""):
    turno_id = turnos.asignar_turno(usuario.id, dia, hora_inicio, hora_fin, area, interaction.user.id)
    embed = crear_embed("info", f"🗓️ Turno Asignado #{turno_id}", "", autor=interaction.user)
    embed.add_field(name="Personal", value=usuario.mention)
    embed.add_field(name="Día", value=dia)
    embed.add_field(name="Horario", value=f"{hora_inicio} – {hora_fin}")
    if area:
        embed.add_field(name="Área", value=area)
    await interaction.response.send_message(embed=embed)
    await enviar_log("log_turnos", embed)
    try:
        await usuario.send(embed=embed)
    except discord.Forbidden:
        pass


@grupo_turno.command(name="entrar", description="Marca tu entrada de turno (quedas en servicio)")
@app_commands.describe(area="Área en la que trabajarás este turno (opcional)")
async def turno_entrar(interaction: discord.Interaction, area: str = ""):
    if not turnos.marcar_entrada(interaction.user.id, area):
        await interaction.response.send_message("⚠️ Ya estás marcado en servicio.", ephemeral=True)
        return
    await interaction.response.send_message(f"✅ {interaction.user.mention} entró de turno" + (f" en **{area}**." if area else "."))
    await enviar_log("log_turnos", crear_embed("exito", "🟢 Entrada de turno", f"**{interaction.user}** entró de turno" + (f" en **{area}**." if area else ".")))


@grupo_turno.command(name="salir", description="Marca tu salida de turno")
async def turno_salir(interaction: discord.Interaction):
    registro = turnos.marcar_salida(interaction.user.id)
    if not registro:
        await interaction.response.send_message("⚠️ No estabas marcado en servicio.", ephemeral=True)
        return
    await interaction.response.send_message(f"✅ {interaction.user.mention} salió de turno.")
    await enviar_log("log_turnos", crear_embed("info", "🔴 Salida de turno", f"**{interaction.user}** salió de turno."))


@grupo_turno.command(name="en_servicio", description="Lista al personal actualmente en servicio")
async def turno_en_servicio(interaction: discord.Interaction):
    lista = turnos.en_servicio_lista()
    if not lista:
        await interaction.response.send_message("Nadie está marcado en servicio ahora mismo.", ephemeral=True)
        return
    lineas = []
    for uid, registro in lista:
        member = interaction.guild.get_member(uid)
        nombre = member.mention if member else f"`{uid}`"
        area = f" — {registro['area']}" if registro.get("area") else ""
        lineas.append(f"{nombre}{area}")
    embed = crear_embed("info", f"👥 Personal en Servicio ({len(lista)})", "\n".join(lineas)[:4000])
    await interaction.response.send_message(embed=embed, ephemeral=True)


@grupo_turno.command(name="mis_turnos", description="Muestra tus turnos asignados")
async def turno_mis_turnos(interaction: discord.Interaction):
    lista = turnos.turnos_de(interaction.user.id)
    if not lista:
        await interaction.response.send_message("No tienes turnos asignados.", ephemeral=True)
        return
    lineas = [f"`{t['dia']}` {t['hora_inicio']}–{t['hora_fin']}" + (f" ({t['area']})" if t.get("area") else "") for t in lista[-10:]]
    await interaction.response.send_message("🗓️ Tus turnos:\n" + "\n".join(lineas), ephemeral=True)


@grupo_turno.command(name="horario", description="Muestra los turnos asignados de otro usuario")
@app_commands.describe(usuario="Usuario a consultar")
@require_key("SUPERVISOR", "JEFE_DEPARTAMENTO", "DIRECTOR", "OWNER")
async def turno_horario(interaction: discord.Interaction, usuario: discord.Member):
    lista = turnos.turnos_de(usuario.id)
    if not lista:
        await interaction.response.send_message(f"{usuario.mention} no tiene turnos asignados.", ephemeral=True)
        return
    lineas = [f"`{t['dia']}` {t['hora_inicio']}–{t['hora_fin']}" + (f" ({t['area']})" if t.get("area") else "") for t in lista[-10:]]
    await interaction.response.send_message(f"🗓️ Turnos de {usuario.mention}:\n" + "\n".join(lineas), ephemeral=True)


bot.tree.add_command(grupo_turno)


# ===========================================================================
# 14) CAPACITACIONES
# ===========================================================================

CAPACITACION_DEPTO_CHOICES = DEPARTAMENTO_CHOICES + [app_commands.Choice(name="General / Todo el personal", value="")]

grupo_capacitacion = app_commands.Group(name="capacitacion", description="Sistema de capacitaciones del personal")


@grupo_capacitacion.command(name="programar", description="Programa una capacitación y la anuncia")
@app_commands.describe(titulo="Título", fecha_hora="Fecha y hora", departamento="Departamento destinatario (opcional)", descripcion="Descripción")
@app_commands.choices(departamento=CAPACITACION_DEPTO_CHOICES)
@require_key("SUPERVISOR", "JEFE_DEPARTAMENTO", "DIRECTOR", "OWNER")
async def capacitacion_programar(
    interaction: discord.Interaction, titulo: str, fecha_hora: str, descripcion: str,
    departamento: app_commands.Choice[str] = None):
    slug = departamento.value if departamento else ""
    cap_id = capacitaciones.programar(titulo, fecha_hora, slug, descripcion, interaction.user.id)

    embed = crear_embed("info", f"🎓 Capacitación #{cap_id}: {titulo}", descripcion, autor=interaction.user)
    embed.add_field(name="Fecha y hora", value=fecha_hora)

    mencion = ""
    if slug and slug in config.DEPARTAMENTOS:
        ids = roles_store.escalafon_ids(slug, len(config.DEPARTAMENTOS[slug]["escalafon_nombres"]))
        roles_mencionables = [interaction.guild.get_role(i) for i in ids if i and interaction.guild.get_role(i)]
        mencion = " ".join(r.mention for r in roles_mencionables)
        embed.add_field(name="Departamento", value=config.DEPARTAMENTOS[slug]["nombre"])
    else:
        embed.add_field(name="Departamento", value="General / Todo el personal")

    await interaction.response.send_message(content=mencion, embed=embed)
    await enviar_log("log_capacitaciones", embed)


@grupo_capacitacion.command(name="certificar", description="Certifica a un usuario como que completó una capacitación")
@app_commands.describe(usuario="Usuario", titulo="Título de la capacitación completada")
@require_key("SUPERVISOR", "JEFE_DEPARTAMENTO", "DIRECTOR", "OWNER")
async def capacitacion_certificar(interaction: discord.Interaction, usuario: discord.Member, titulo: str):
    capacitaciones.certificar(usuario.id, titulo, interaction.user.id)
    await interaction.response.send_message(f"🎓 {usuario.mention} fue certificado en **{titulo}**.")
    await enviar_log("log_capacitaciones", crear_embed(
        "exito", "🎓 Capacitación certificada", f"**{interaction.user}** certificó a **{usuario}** en **{titulo}**"))


@grupo_capacitacion.command(name="mis_capacitaciones", description="Muestra las capacitaciones que has completado")
async def capacitacion_mis(interaction: discord.Interaction):
    lista = capacitaciones.completadas_de(interaction.user.id)
    if not lista:
        await interaction.response.send_message("No tienes capacitaciones certificadas todavía.", ephemeral=True)
        return
    lineas = [f"`{c['fecha'][:10]}` {c['titulo']}" for c in lista[-15:]]
    await interaction.response.send_message("🎓 Tus capacitaciones:\n" + "\n".join(lineas), ephemeral=True)


@grupo_capacitacion.command(name="historial", description="Muestra las capacitaciones completadas de otro usuario")
@app_commands.describe(usuario="Usuario a consultar")
@require_key("SUPERVISOR", "JEFE_DEPARTAMENTO", "DIRECTOR", "OWNER")
async def capacitacion_historial(interaction: discord.Interaction, usuario: discord.Member):
    lista = capacitaciones.completadas_de(usuario.id)
    if not lista:
        await interaction.response.send_message(f"{usuario.mention} no tiene capacitaciones certificadas.", ephemeral=True)
        return
    lineas = [f"`{c['fecha'][:10]}` {c['titulo']}" for c in lista[-15:]]
    await interaction.response.send_message(f"🎓 Capacitaciones de {usuario.mention}:\n" + "\n".join(lineas), ephemeral=True)


@grupo_capacitacion.command(name="listar", description="Lista las próximas capacitaciones programadas")
async def capacitacion_listar(interaction: discord.Interaction):
    lista = capacitaciones.listar_programadas()
    if not lista:
        await interaction.response.send_message("No hay capacitaciones programadas.", ephemeral=True)
        return
    lineas = [f"`#{c['id']}` **{c['titulo']}** — {c['fecha_hora']}" for c in lista[-15:]]
    embed = crear_embed("info", "🎓 Capacitaciones Programadas", "\n".join(lineas)[:4000])
    await interaction.response.send_message(embed=embed, ephemeral=True)


bot.tree.add_command(grupo_capacitacion)


# ===========================================================================
# 15) CÓDIGOS DE EMERGENCIA
# ===========================================================================

CODIGO_CHOICES = [
    app_commands.Choice(name=data["nombre"], value=key) for key, data in config.CODIGOS_EMERGENCIA.items()
]

grupo_codigo = app_commands.Group(name="codigo", description="Códigos de emergencia hospitalarios")


@grupo_codigo.command(name="activar", description="Activa un código de emergencia y alerta al personal correspondiente")
@app_commands.describe(codigo="Código a activar", ubicacion="Ubicación del incidente", detalles="Detalles adicionales (opcional)")
@app_commands.choices(codigo=CODIGO_CHOICES)
@require_key("STAFF", "SUPERVISOR", "JEFE_DEPARTAMENTO", "DIRECTOR", "OWNER")
async def codigo_activar(interaction: discord.Interaction, codigo: app_commands.Choice[str], ubicacion: str, detalles: str = ""):
    info = config.CODIGOS_EMERGENCIA[codigo.value]
    codigos.activar(codigo.value, ubicacion, detalles, interaction.user.id)

    embed = discord.Embed(
        title=f"🚨 {info['nombre']} ACTIVADO 🚨",
        description=f"**{info['descripcion']}**\n\n{detalles}" if detalles else f"**{info['descripcion']}**",
        color=discord.Color(int(info["color"].lstrip("#"), 16)),
        timestamp=discord.utils.utcnow())
    embed.add_field(name="Ubicación", value=ubicacion)
    embed.add_field(name="Activado por", value=interaction.user.mention)
    embed.set_footer(text=config.NOMBRE_HOSPITAL)

    menciones = []
    for key in info["mencion_keys"]:
        rid = roles_store.obtener_id_key(key)
        rol = interaction.guild.get_role(rid) if rid else None
        if rol:
            menciones.append(rol.mention)

    await interaction.response.send_message(content=" ".join(menciones), embed=embed)
    await enviar_log("alerta_codigos", embed)


@grupo_codigo.command(name="cancelar", description="Cancela (da por resuelto) un código de emergencia activo")
@app_commands.describe(codigo="Código a cancelar")
@app_commands.choices(codigo=CODIGO_CHOICES)
@require_key("SUPERVISOR", "JEFE_DEPARTAMENTO", "DIRECTOR", "OWNER")
async def codigo_cancelar(interaction: discord.Interaction, codigo: app_commands.Choice[str]):
    info = config.CODIGOS_EMERGENCIA[codigo.value]
    cerradas = codigos.cancelar_todos(codigo.value)
    if not cerradas:
        await interaction.response.send_message(f"⚠️ No hay ninguna activación vigente de **{info['nombre']}**.", ephemeral=True)
        return

    embed = crear_embed("exito", f"✅ {info['nombre']} — Resuelto", "El código fue cancelado.", autor=interaction.user)
    await interaction.response.send_message(embed=embed)
    await enviar_log("alerta_codigos", embed)


@grupo_codigo.command(name="activos", description="Lista los códigos de emergencia activos actualmente")
async def codigo_activos(interaction: discord.Interaction):
    lista = codigos.activos()
    if not lista:
        await interaction.response.send_message("✅ No hay códigos de emergencia activos.", ephemeral=True)
        return
    lineas = []
    for c in lista:
        info = config.CODIGOS_EMERGENCIA.get(c["codigo"], {})
        lineas.append(f"{info.get('nombre', c['codigo'])} — {c['ubicacion']}")
    embed = crear_embed("error", "🚨 Códigos de Emergencia Activos", "\n".join(lineas))
    await interaction.response.send_message(embed=embed)


bot.tree.add_command(grupo_codigo)


# ===========================================================================
# 16) FICHA DE PERSONAL
# ===========================================================================

FICHA_CAMPO_CHOICES = [app_commands.Choice(name=v, value=k) for k, v in config.FICHA_CAMPOS.items()]

grupo_ficha = app_commands.Group(name="ficha", description="Ficha administrativa de personal")


@grupo_ficha.command(name="editar", description="Edita un campo de la ficha de personal de un usuario")
@app_commands.describe(usuario="Usuario", campo="Campo a editar", valor="Nuevo valor")
@app_commands.choices(campo=FICHA_CAMPO_CHOICES)
@require_key("DIRECTOR_RRHH", "DIRECTOR", "OWNER")
async def ficha_editar(interaction: discord.Interaction, usuario: discord.Member, campo: app_commands.Choice[str], valor: str):
    ficha_personal.set_campo(usuario.id, campo.value, valor)
    await interaction.response.send_message(f"✅ **{campo.name}** de {usuario.mention} actualizado a: {valor}")
    await enviar_log("log_personal", crear_embed(
        "info", "Ficha de personal actualizada",
        f"**{interaction.user}** actualizó **{campo.name}** de **{usuario}**: {valor}"))


@grupo_ficha.command(name="ver", description="Muestra la ficha administrativa de personal de un usuario (o la tuya)")
@app_commands.describe(usuario="Usuario a consultar (opcional, por defecto tú mismo)")
async def ficha_ver(interaction: discord.Interaction, usuario: discord.Member = None):
    objetivo = usuario or interaction.user
    if usuario and usuario != interaction.user:
        if not permisos.member_tiene_alguna_key(
            interaction.user, "SUPERVISOR", "JEFE_DEPARTAMENTO", "DIRECTOR", "DIRECTOR_RRHH",
            "OWNER"):
            await interaction.response.send_message("❌ Solo puedes consultar tu propia ficha.", ephemeral=True)
            return

    datos = ficha_personal.obtener(objetivo.id)
    embed = crear_embed("info", f"🗂️ Ficha de Personal — {objetivo.display_name}", "", autor=objetivo)
    depto = permisos.departamento_del_member(objetivo)
    embed.add_field(name="Departamento", value=config.DEPARTAMENTOS[depto]["nombre"] if depto else "—", inline=True)
    keys_actuales = permisos.keys_del_member(objetivo)
    embed.add_field(name="Keys", value=", ".join(keys_actuales) or "Ninguna", inline=True)
    for campo, etiqueta in config.FICHA_CAMPOS.items():
        embed.add_field(name=etiqueta, value=datos.get(campo) or "—", inline=True)

    await interaction.response.send_message(embed=embed, ephemeral=True)


bot.tree.add_command(grupo_ficha)


# ===========================================================================
# 17) POSTULACIONES AL STAFF
# ===========================================================================

grupo_postulacion = app_commands.Group(name="postulacion", description="Postulaciones al staff del hospital")


@grupo_postulacion.command(name="aplicar", description="Postúlate a un departamento del hospital")
@app_commands.describe(departamento="Departamento al que quieres postularte")
@app_commands.choices(departamento=SOLICITUD_CHOICES)
async def postulacion_aplicar(interaction: discord.Interaction, departamento: app_commands.Choice[str]):
    if postulaciones.tiene_pendiente(interaction.user.id):
        await interaction.response.send_message(
            "⚠️ Ya tienes una postulación pendiente de resolver.", ephemeral=True
        )
        return
    await interaction.response.send_modal(
        postulaciones.PostulacionModal(departamento.value, departamento.name)
    )


@grupo_postulacion.command(name="pendientes", description="Lista las postulaciones al staff sin resolver")
@require_key("DIRECTOR", "DIRECTOR_RRHH", "OWNER")
async def postulacion_pendientes(interaction: discord.Interaction):
    lista = postulaciones.pendientes()
    if not lista:
        await interaction.response.send_message("✅ No hay postulaciones pendientes.", ephemeral=True)
        return
    lineas = []
    for p in lista[:20]:
        nombre_depto = config.DEPARTAMENTOS.get(p["departamento_slug"], {}).get("nombre", "General / RRHH")
        lineas.append(f"`#{p['id']}` {nombre_depto} — <@{p['autor_id']}>")
    embed = crear_embed("info", f"📋 Postulaciones Pendientes ({len(lista)})", "\n".join(lineas)[:4000])
    await interaction.response.send_message(embed=embed, ephemeral=True)


@grupo_postulacion.command(name="mias", description="Muestra el estado de tus propias postulaciones")
async def postulacion_mias(interaction: discord.Interaction):
    propias = postulaciones.postulaciones_de(interaction.user.id)
    if not propias:
        await interaction.response.send_message("No tienes postulaciones registradas.", ephemeral=True)
        return
    iconos = {"pendiente": "🕓", "aprobada": "✅", "rechazada": "❌"}
    lineas = []
    for p in propias[-10:]:
        nombre_depto = config.DEPARTAMENTOS.get(p["departamento_slug"], {}).get("nombre", "General / RRHH")
        lineas.append(f"{iconos.get(p['estado'], '•')} `#{p['id']}` {nombre_depto} — {p['estado']}")
    await interaction.response.send_message("📋 Tus postulaciones:\n" + "\n".join(lineas), ephemeral=True)


@grupo_postulacion.command(name="resolver", description="Aprueba o rechaza una postulación pendiente")
@app_commands.describe(id_postulacion="Número de la postulación (visible en /postulacion pendientes)", estado="Resultado")
@app_commands.choices(estado=[
    app_commands.Choice(name="Aprobada", value="aprobada"),
    app_commands.Choice(name="Rechazada", value="rechazada"),
])
@require_key("DIRECTOR", "DIRECTOR_RRHH", "OWNER")
async def postulacion_resolver(interaction: discord.Interaction, id_postulacion: int, estado: app_commands.Choice[str]):
    # BUG CORREGIDO: postulaciones.resolver() existía en postulaciones.py
    # pero ningún comando la llamaba, así que el staff no tenía forma de
    # aprobar o rechazar postulaciones — quedaban "pendiente" para siempre.
    if not postulaciones.resolver(id_postulacion, estado.value):
        await interaction.response.send_message(f"❌ No existe la postulación #{id_postulacion}.", ephemeral=True)
        return
    await interaction.response.send_message(
        f"✅ Postulación #{id_postulacion} marcada como **{estado.value}**."
    )
    await enviar_log("log_postulaciones", crear_embed(
        "exito" if estado.value == "aprobada" else "error",
        "Postulación resuelta",
        f"**{interaction.user}** marcó la postulación #{id_postulacion} como **{estado.value}**."))


bot.tree.add_command(grupo_postulacion)


# ===========================================================================
# 18) QUEJAS FORMALES
# ===========================================================================

@bot.tree.command(name="queja", description="Presenta una queja formal (rellenable); se envía a Recursos Humanos")
@app_commands.describe(area="Área relacionada con la queja")
@app_commands.choices(area=SOLICITUD_CHOICES)
async def queja(interaction: discord.Interaction, area: app_commands.Choice[str]):
    await interaction.response.send_modal(QuejaModal(area.value, area.name))


@bot.tree.command(name="quejas_pendientes", description="Lista las quejas formales sin resolver")
@require_key("DIRECTOR_RRHH", "OWNER")
async def quejas_pendientes(interaction: discord.Interaction):
    lista = quejas.pendientes()
    if not lista:
        await interaction.response.send_message("✅ No hay quejas pendientes.", ephemeral=True)
        return
    lineas = [f"`#{q['id']}` **{q['departamento']}** — contra: {q['contra']}" for q in lista[:20]]
    embed = crear_embed("aviso", f"📢 Quejas Pendientes ({len(lista)})", "\n".join(lineas)[:4000])
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="queja_resolver", description="Marca una queja formal como resuelta")
@app_commands.describe(id_queja="Número de la queja (visible en /quejas_pendientes)")
@require_key("DIRECTOR_RRHH", "OWNER")
async def queja_resolver(interaction: discord.Interaction, id_queja: int):
    if not quejas.resolver(id_queja):
        await interaction.response.send_message(f"❌ No existe la queja #{id_queja}.", ephemeral=True)
        return
    await interaction.response.send_message(f"✅ Queja #{id_queja} marcada como resuelta.")
    await enviar_log("log_quejas", crear_embed(
        "exito", "Queja resuelta", f"**{interaction.user}** marcó la queja #{id_queja} como resuelta."))


# ===========================================================================
# 19) PANEL DE ESTADO GENERAL
# ===========================================================================

@bot.tree.command(name="panel_estado", description="Publica el panel de estado general del hospital (con botón de refrescar)")
@require_key("DIRECTOR", "OWNER")
async def panel_estado(interaction: discord.Interaction):
    embed = construir_embed_estado(interaction.guild)
    await interaction.response.send_message(embed=embed, view=PanelEstadoView())


@bot.tree.command(name="estado_hospital", description="Muestra un resumen puntual del estado general del hospital")
async def estado_hospital(interaction: discord.Interaction):
    embed = construir_embed_estado(interaction.guild)
    await interaction.response.send_message(embed=embed, ephemeral=True)



# ===========================================================================
# 20) CONTROL DEL BOT (solo OWNER; CO_OWNER pide aprobación)
# ===========================================================================

@bot.tree.command(name="apagar_bot", description="Apaga el bot (solo OWNER; CO_OWNER requiere aprobación)")
@app_commands.describe(mensaje="Mensaje de estado opcional")
async def apagar_bot(interaction: discord.Interaction, mensaje: str = ""):
    await bot_control.solicitar_o_ejecutar(interaction, bot, "apagar", mensaje)


@bot.tree.command(name="encender_bot", description="Pone el bot en modo online (solo OWNER; CO_OWNER requiere aprobación)")
@app_commands.describe(mensaje="Mensaje de estado opcional")
async def encender_bot(interaction: discord.Interaction, mensaje: str = ""):
    await bot_control.solicitar_o_ejecutar(interaction, bot, "encender", mensaje)


@bot.tree.command(name="mantenimiento_bot", description="Pone el bot en mantenimiento (solo OWNER; CO_OWNER requiere aprobación)")
@app_commands.describe(mensaje="Mensaje de estado opcional")
async def mantenimiento_bot(interaction: discord.Interaction, mensaje: str = ""):
    await bot_control.solicitar_o_ejecutar(interaction, bot, "mantenimiento", mensaje)


@bot.tree.command(name="reiniciar_bot", description="Reinicia el bot (solo OWNER; CO_OWNER requiere aprobación)")
@app_commands.describe(mensaje="Mensaje de estado opcional")
async def reiniciar_bot(interaction: discord.Interaction, mensaje: str = ""):
    await bot_control.solicitar_o_ejecutar(interaction, bot, "reiniciar", mensaje)


@bot.tree.command(name="estado_bot", description="Muestra el estado actual del bot (online / mantenimiento / offline)")
async def estado_bot(interaction: discord.Interaction):
    await interaction.response.send_message(embed=bot_control.status_embed(), ephemeral=True)


# ===========================================================================
if not config.TOKEN:
    raise SystemExit(
        "No hay TOKEN. En Railway ve a Variables y crea TOKEN "
        "(o DISCORD_TOKEN / BOT_TOKEN) con el token del bot. "
        "No lo pongas en config.py."
    )
bot.run(config.TOKEN)
