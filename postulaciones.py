"""
postulaciones.py
=================
Sistema de postulaciones al staff: cualquiera puede postularse a un
departamento con /postulacion aplicar (modal rellenable). La
postulación se enruta por DM al Director de ese departamento (o sube
de nivel si nadie tiene esa key todavía, igual que solicitudes.py) y
llega con dos botones: ✅ Aprobar / ❌ Rechazar.

- Aprobar contrata automáticamente al postulante (le da STAFF + el
  rol base del departamento, igual que /contratar) y lo notifica.
- Rechazar solo lo notifica y cierra la postulación.

Solo puede resolver la postulación el Director de ese departamento
(o DIRECTOR_RRHH / JEFE_JUNTA_DIRECTIVA / OWNER). Persistente en JSON
local (postulaciones.json).

Nota: al igual que VotacionView en bot_hospital.py, la vista con
botones NO es persistente entre reinicios del bot (una postulación
enviada antes de reiniciar deja de tener botones activos, pero sigue
"pendiente" y se puede resolver contratando/despidiendo manualmente).
No necesita edición.
"""

import json
import os
from datetime import datetime, timezone

import discord
from discord import ui

import config
import permisos
import registros
import roles_store
from estilos import crear_embed
from solicitudes import miembros_encargados

ARCHIVO = "postulaciones.json"


def _cargar() -> list:
    if not os.path.exists(ARCHIVO):
        return []
    with open(ARCHIVO, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _guardar(data: list):
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def crear(autor_id: int, departamento_slug: str, contenido: str) -> int:
    data = _cargar()
    postulacion_id = (data[-1]["id"] + 1) if data else 1
    data.append({
        "id": postulacion_id, "autor_id": autor_id, "departamento_slug": departamento_slug,
        "contenido": contenido, "estado": "pendiente", "resolutor_id": None,
        "fecha": datetime.now(timezone.utc).isoformat(),
    })
    _guardar(data[-300:])
    return postulacion_id


def obtener(postulacion_id: int) -> dict:
    for p in _cargar():
        if p["id"] == postulacion_id:
            return p
    return None


def tiene_pendiente(user_id: int) -> bool:
    return any(p["autor_id"] == user_id and p["estado"] == "pendiente" for p in _cargar())


def actualizar_estado(postulacion_id: int, estado: str, resolutor_id: int) -> bool:
    data = _cargar()
    for p in data:
        if p["id"] == postulacion_id:
            p["estado"] = estado
            p["resolutor_id"] = resolutor_id
            _guardar(data)
            return True
    return False


def pendientes() -> list:
    return [p for p in _cargar() if p["estado"] == "pendiente"]


def postulaciones_de(user_id: int) -> list:
    return [p for p in _cargar() if p["autor_id"] == user_id]


# ===========================================================================
# MODAL: formulario de postulación
# ===========================================================================

class PostulacionModal(ui.Modal):
    experiencia = ui.TextInput(
        label="Experiencia / motivación",
        style=discord.TextStyle.paragraph,
        max_length=1500,
        placeholder="Cuéntanos tu experiencia (RP) y por qué quieres unirte a este departamento...",
    )
    disponibilidad = ui.TextInput(
        label="Disponibilidad horaria (opcional)",
        required=False,
        max_length=200,
    )

    def __init__(self, departamento_slug: str, departamento_nombre: str):
        super().__init__(title=f"Postulación — {departamento_nombre}"[:45])
        self.departamento_slug = departamento_slug
        self.departamento_nombre = departamento_nombre

    async def on_submit(self, interaction: discord.Interaction):
        if tiene_pendiente(interaction.user.id):
            await interaction.response.send_message(
                "⚠️ Ya tienes una postulación pendiente de resolver. Espera a que la respondan.",
                ephemeral=True,
            )
            return

        contenido = str(self.experiencia.value)
        if self.disponibilidad.value:
            contenido += f"\n\n**Disponibilidad:** {self.disponibilidad.value}"

        postulacion_id = crear(interaction.user.id, self.departamento_slug, contenido)

        embed = crear_embed(
            "info", f"📋 Postulación #{postulacion_id} — {self.departamento_nombre}", contenido, autor=interaction.user
        )
        embed.add_field(name="Postulante", value=interaction.user.mention)
        embed.add_field(name="Departamento", value=self.departamento_nombre)
        embed.set_footer(text=f"{config.NOMBRE_HOSPITAL} · Postulación pendiente de aprobación")

        await _enviar_postulacion(interaction, postulacion_id, self.departamento_slug, self.departamento_nombre, embed)


# ===========================================================================
# VISTA: botones Aprobar / Rechazar
# ===========================================================================

class PostulacionView(ui.View):
    def __init__(self, postulacion_id: int, departamento_slug: str):
        super().__init__(timeout=None)
        self.postulacion_id = postulacion_id
        self.departamento_slug = departamento_slug

    def _autorizado(self, member: discord.Member) -> bool:
        if permisos.member_tiene_alguna_key(member, "DIRECTOR_RRHH", "JEFE_JUNTA_DIRECTIVA", "OWNER"):
            return True
        if self.departamento_slug in config.DEPARTAMENTOS:
            director_key = config.DEPARTAMENTOS[self.departamento_slug]["director_key"]
            return permisos.member_tiene_key(member, director_key)
        return False

    async def _resolver(self, interaction: discord.Interaction, aprobar: bool):
        member = interaction.user
        if not isinstance(member, discord.Member) or not self._autorizado(member):
            await interaction.response.send_message(
                "❌ No tienes autoridad para resolver esta postulación.", ephemeral=True
            )
            return

        postulacion = obtener(self.postulacion_id)
        if not postulacion or postulacion["estado"] != "pendiente":
            await interaction.response.send_message(
                "⚠️ Esta postulación ya fue resuelta.", ephemeral=True
            )
            return

        guild = interaction.guild or (member.mutual_guilds[0] if member.mutual_guilds else None)
        postulante = guild.get_member(postulacion["autor_id"]) if guild else None

        if aprobar:
            if guild and postulante:
                staff_id = roles_store.obtener_id_key("STAFF")
                base_id = None
                if self.departamento_slug in config.DEPARTAMENTOS:
                    base_id = roles_store.escalafon_ids(self.departamento_slug, 1)[0]
                roles_a_dar = [
                    r for r in (
                        guild.get_role(staff_id) if staff_id else None,
                        guild.get_role(base_id) if base_id else None,
                    ) if r
                ]
                if roles_a_dar:
                    try:
                        await postulante.add_roles(*roles_a_dar, reason=f"Postulación aprobada por {member}")
                    except discord.Forbidden:
                        await interaction.response.send_message(
                            "⚠️ Se aprobó, pero no tengo permisos para asignar los roles. Usa `/contratar` manualmente.",
                            ephemeral=True,
                        )
                registros.registrar_evento_cargo(
                    postulacion["autor_id"], "contratacion",
                    f"Postulación #{postulacion['id']} aprobada", member.id,
                )
            estado, verbo, tipo = "aprobada", "✅ Aprobada", "exito"
        else:
            estado, verbo, tipo = "rechazada", "❌ Rechazada", "error"

        actualizar_estado(self.postulacion_id, estado, member.id)

        embed = interaction.message.embeds[0]
        embed.color = crear_embed(tipo, "x", "").color
        embed.set_footer(text=f"{verbo} por {member.display_name}")
        for item in self.children:
            item.disabled = True

        if interaction.response.is_done():
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

        if postulante:
            try:
                await postulante.send(embed=crear_embed(
                    tipo, f"Tu postulación fue {estado}",
                    f"Tu postulación #{postulacion['id']} fue **{estado}** por {member.mention}.",
                ))
            except discord.Forbidden:
                pass

    @ui.button(label="✅ Aprobar", style=discord.ButtonStyle.success, custom_id="hospital:postulacion_aprobar")
    async def aprobar(self, interaction: discord.Interaction, button: ui.Button):
        await self._resolver(interaction, aprobar=True)

    @ui.button(label="❌ Rechazar", style=discord.ButtonStyle.danger, custom_id="hospital:postulacion_rechazar")
    async def rechazar(self, interaction: discord.Interaction, button: ui.Button):
        await self._resolver(interaction, aprobar=False)


async def _enviar_postulacion(
    interaction: discord.Interaction, postulacion_id: int, departamento_slug: str, departamento_nombre: str,
    embed: discord.Embed,
):
    guild = interaction.guild
    if departamento_slug in config.DEPARTAMENTOS:
        key_destino = config.DEPARTAMENTOS[departamento_slug]["director_key"]
    else:
        key_destino = config.SOLICITUD_GENERAL_KEY

    destinatarios = await miembros_encargados(guild, key_destino)
    view = PostulacionView(postulacion_id, departamento_slug)

    entregados = 0
    for miembro in destinatarios:
        try:
            await miembro.send(embed=embed, view=view)
            entregados += 1
        except discord.Forbidden:
            continue

    canal_id = config.CANALES.get("log_postulaciones") or config.CANALES.get("log_personal")
    if canal_id:
        canal = interaction.client.get_channel(canal_id)
        if canal:
            try:
                await canal.send(embed=embed, view=view)
            except discord.Forbidden:
                pass

    if entregados:
        await interaction.response.send_message(
            f"✅ Tu postulación #{postulacion_id} fue enviada a {entregados} encargado(s).", ephemeral=True
        )
    elif canal_id:
        await interaction.response.send_message(
            f"⚠️ No se pudo entregar tu postulación #{postulacion_id} por DM, pero quedó publicada en el "
            "canal de registro correspondiente para que la revisen.",
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            "⚠️ No hay nadie con el cargo encargado todavía, y no hay canal de registro configurado en "
            "config.CANALES. Avisa a un Director o al Owner.",
            ephemeral=True,
        )
