# -*- coding: utf-8 -*-
"""
setup_servidor.py
=================
Comando /setup_servidor (solo Fundador y Owner / Co-Owner):
- Crea roles del organigrama oficial si faltan.
- Crea 3 canales de normativas (RP, Discord, General) con el contenido separado.
- Solicita por botones/modales los canales de bienvenida y verificación Roblox.
- Idempotente: no duplica categorías ni canales existentes.
"""
from __future__ import annotations

from typing import List, Optional

import discord
from discord import app_commands, ui
from discord.ext import commands

import roles_config
import roles_setup
import roles_store
from estilos import crear_embed

# ═══════════════════════════════════════════════════════════════
# CONTENIDO DE LAS 3 NORMATIVAS (separado por secciones)
# ═══════════════════════════════════════════════════════════════

NORMATIVA_RP = """
# 🩺 Normativa de Roleplay (Hospital)

## 1. Organigrama oficial
El organigrama es la única fuente de verdad de cargos y jerarquía.

**Autoridades Competentes**
• Fundador y Owner
• Co-Owner

**Staff del Server**
• Admin en Jefe
• Admin
• Admin en Prueba

**Gerencia**
• Prefecto de Operaciones Hospitalarias
• Director General
• Director Médico
• Director de RRHH
• Director de Docencia e Investigación
• Director de Logística

**Jefatura de Departamento**
• Jefe de Departamento

**Área Médica**
• Jefe de Servicio
• Médico Especialista
• Médico General
• Jefe y Guía/Docente de Residentes
• Residente
• Interno / Practicante

**Área Administrativa**
• Administrativo Senior
• Administrativo Junior / Auxiliar

**Rol del sistema**
• Inactividad Justificada (no forma parte de la jerarquía de permisos)

## 2. Conducta en rol
• Mantén el personaje coherente con tu cargo.
• Respeta la cadena de mando del organigrama.
• No uses información OOC dentro del rol sin justificación.
• Las sanciones internas, despidos e investigaciones se gestionan por RRHH / Gerencia.

## 3. Inactividad
• Aviso: 7 días · Inactivo: 14 días · Revisión: 30 días.
• Puedes solicitar **Inactividad Justificada** (máx. 10 días, 1 vez cada 14 días).
• Con el rol de Inactividad Justificada no se aplican sanciones por ausencia.
""".strip()

NORMATIVA_DISCORD = """
# 💬 Normativa de Discord (OOC)

## 1. Respeto y convivencia
• Prohibido el acoso, discriminación, toxicidad o ataques personales.
• No spam, flood ni publicidad no autorizada.
• Respeta los canales: cada uno tiene su propósito.

## 2. Staff del Server
• Admin en Jefe, Admin y Admin en Prueba gestionan moderación OOC.
• Las decisiones de Staff del Server en temas de Discord prevalecen en canales OOC.

## 3. Verificación y acceso
• Debes completar la verificación de Roblox y aceptar las políticas del servidor.
• Al entrar se te asignan los roles de categoría de uniforme automáticamente.
• El incumplimiento reiterado de las normas puede derivar en sanción o expulsión.

## 4. Canales y privacidad
• No compartas datos personales de otros miembros.
• Los logs y canales de staff son de uso interno.
""".strip()

NORMATIVA_GENERAL = """
# ⚙️ Normativa General / Sistema

## 1. Autoridad del organigrama
Todo el sistema de permisos del bot se rige por el organigrama oficial.
No existen cargos fuera de esa lista para efectos de comandos y jerarquía.

## 2. Roles del sistema
• **Inactividad Justificada**: se asigna solo tras aprobación de Gerencia/RRHH.
• No otorga permisos de mando; solo exime del conteo de inactividad.

## 3. Certificaciones y Docencia
• Las certificaciones y roles de formación dependen del **Director de Docencia e Investigación**.

## 4. Seguridad (rama conservada)
• Existe una rama de roles de Seguridad (Jefe de Seguridad, Supervisor, Guardia) para el funcionamiento del servidor, sin alterar el organigrama de permisos principal.

## 5. Uniformes
• Al unirte al servidor se te asignan automáticamente los roles de categoría de uniforme.
• No otorgan permisos; son solo de apariencia/organización.

## 6. Modificaciones
• Cualquier cambio al organigrama o a estas normativas debe ser aprobado por Fundador y Owner / Co-Owner.
""".strip()


# ═══════════════════════════════════════════════════════════════
# VISTAS INTERACTIVAS (pedir canales)
# ═══════════════════════════════════════════════════════════════

class CanalSelect(ui.ChannelSelect):
    def __init__(self, clave: str, placeholder: str):
        super().__init__(
            placeholder=placeholder,
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            custom_id=f"setup_canal_{clave}",
        )
        self.clave = clave

    async def callback(self, interaction: discord.Interaction):
        canal = self.values[0]
        # Guardar en roles_store como extra
        roles_store.guardar_extra(f"canal_{self.clave}", canal.id)
        await interaction.response.send_message(
            embed=crear_embed(
                "exito",
                f"Canal guardado: {self.clave}",
                f"**{canal.mention}** (`{canal.id}`) se usará para **{self.clave}**."
            ),
            ephemeral=True,
        )


class PedirCanalesView(ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(CanalSelect("bienvenida", "Selecciona canal de BIENVENIDA"))
        self.add_item(CanalSelect("verificacion_roblox", "Selecciona canal de VERIFICACIÓN ROBLOX"))
        self.add_item(CanalSelect("solicitudes_inactividad", "Selecciona canal de SOLICITUDES INACTIVIDAD"))
        self.add_item(CanalSelect("log_staff", "Selecciona canal de LOG STAFF"))


# ═══════════════════════════════════════════════════════════════
# CREACIÓN DE CANALES DE NORMATIVAS
# ═══════════════════════════════════════════════════════════════

async def _asegurar_categoria(
    guild: discord.Guild,
    nombre: str,
    resumen: List[str],
) -> Optional[discord.CategoryChannel]:
    for c in guild.categories:
        if c.name == nombre or c.name.lower() == nombre.lower():
            resumen.append(f"✅ Categoría existente: **{c.name}**")
            return c
    try:
        cat = await guild.create_category(
            name=nombre,
            reason="Setup servidor — normativas",
        )
        resumen.append(f"🆕 Categoría creada: **{nombre}**")
        return cat
    except discord.Forbidden:
        resumen.append(f"❌ Sin permisos para crear categoría **{nombre}**")
        return None
    except Exception as e:
        resumen.append(f"❌ Error categoría **{nombre}**: {e}")
        return None


async def _asegurar_canal_texto(
    guild: discord.Guild,
    nombre: str,
    categoria: Optional[discord.CategoryChannel],
    resumen: List[str],
    *,
    topic: str = "",
) -> Optional[discord.TextChannel]:
    # Buscar existente (por nombre, en cualquier categoría)
    for ch in guild.text_channels:
        if ch.name == nombre or ch.name.replace("-", " ") == nombre.replace("-", " "):
            resumen.append(f"✅ Canal existente: **#{ch.name}**")
            return ch
    try:
        ch = await guild.create_text_channel(
            name=nombre,
            category=categoria,
            topic=topic or None,
            reason="Setup servidor — normativas",
        )
        resumen.append(f"🆕 Canal creado: **#{nombre}**")
        return ch
    except discord.Forbidden:
        resumen.append(f"❌ Sin permisos para crear canal **#{nombre}**")
        return None
    except Exception as e:
        resumen.append(f"❌ Error canal **#{nombre}**: {e}")
        return None


async def crear_canales_normativas(guild: discord.Guild) -> List[str]:
    resumen: List[str] = ["**Canales de Normativas**"]

    cat = await _asegurar_categoria(guild, "【📜】normativas", resumen)

    canales_def = [
        ("normativa-rp", "Normativa de Roleplay del Hospital", NORMATIVA_RP, "normativa_rp"),
        ("normativa-discord", "Normativa de Discord (OOC)", NORMATIVA_DISCORD, "normativa_discord"),
        ("normativa-general", "Normativa General y del Sistema", NORMATIVA_GENERAL, "normativa_general"),
    ]

    for nombre, topic, contenido, clave in canales_def:
        ch = await _asegurar_canal_texto(guild, nombre, cat, resumen, topic=topic)
        if ch:
            roles_store.guardar_extra(f"canal_{clave}", ch.id)
            # Publicar contenido si el canal está vacío o casi vacío
            try:
                async for _ in ch.history(limit=3):
                    break
                else:
                    # Canal vacío → publicar
                    embed = crear_embed("info", topic, contenido[:4000])
                    await ch.send(embed=embed)
                    resumen.append(f"📄 Contenido publicado en **#{nombre}**")
            except Exception as e:
                resumen.append(f"⚠️ No se pudo publicar en **#{nombre}**: {e}")

    return resumen


# ═══════════════════════════════════════════════════════════════
# COMANDO PRINCIPAL
# ═══════════════════════════════════════════════════════════════

def registrar(bot: commands.Bot) -> None:

    @bot.tree.command(
        name="setup_servidor",
        description="Configura roles del organigrama, canales de normativas y solicita canales clave",
    )
    @app_commands.describe(dry_run="Solo muestra lo que haría, sin crear nada")
    async def setup_servidor(
        interaction: discord.Interaction,
        dry_run: bool = False,
    ):
        if not isinstance(interaction.user, discord.Member) or not interaction.guild:
            await interaction.response.send_message(
                "❌ Solo usable dentro del servidor.", ephemeral=True
            )
            return

        # Solo Fundador y Owner / Co-Owner
        from permisos import member_tiene_alguna_key  # import tardío para evitar ciclos

        # Durante la migración aún puede existir la key antigua OWNER
        autorizado = False
        try:
            autorizado = member_tiene_alguna_key(
                interaction.user,
                "FUNDADOR_OWNER", "CO_OWNER", "OWNER",  # OWNER = compatibilidad temporal
            )
        except Exception:
            # Fallback: administrador del servidor
            autorizado = interaction.user.guild_permissions.administrator

        if not autorizado:
            await interaction.response.send_message(
                "❌ Solo **Fundador y Owner** o **Co-Owner** pueden usar este comando.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        if dry_run:
            embed = crear_embed(
                "info",
                "🔍 Vista previa — /setup_servidor",
                "Se crearían/verificarían:\n"
                "• Todos los roles del organigrama oficial\n"
                "• Rol Inactividad Justificada\n"
                "• Separadores de categoría (sin color ni permisos)\n"
                "• Roles de uniforme / docencia / seguridad conservados\n"
                "• Categoría 【📜】normativas + 3 canales\n"
                "• Luego se pedirán los canales de bienvenida y verificación\n\n"
                "Ejecuta sin `dry_run` para aplicar.",
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        lineas: List[str] = []

        # 1. Roles del organigrama
        try:
            lineas.extend(await roles_setup.configurar_organigrama(interaction.guild))
        except Exception as e:
            lineas.append(f"❌ Error al configurar roles: {e}")

        # 2. Canales de normativas
        try:
            lineas.extend(await crear_canales_normativas(interaction.guild))
        except Exception as e:
            lineas.append(f"❌ Error al crear canales de normativas: {e}")

        # Resumen
        texto = "\n".join(lineas)
        if len(texto) > 3900:
            texto = texto[:3900] + "\n…"

        embed = crear_embed(
            "exito",
            "✅ Setup parcial completado",
            texto or "Sin cambios detectados.",
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

        # 3. Pedir canales clave
        embed_canales = crear_embed(
            "info",
            "📌 Selecciona los canales clave",
            "Usa los menús de abajo para indicar:\n"
            "• Canal de **Bienvenida**\n"
            "• Canal de **Verificación Roblox**\n"
            "• Canal de **Solicitudes de Inactividad**\n"
            "• Canal de **Log Staff**\n\n"
            "Puedes cambiarlos más tarde volviendo a ejecutar este comando.",
        )
        await interaction.followup.send(
            embed=embed_canales,
            view=PedirCanalesView(),
            ephemeral=True,
        )
