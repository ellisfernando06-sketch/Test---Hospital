# -*- coding: utf-8 -*-
"""comandos_nuevos.py — Bootstrap desde commit conocido + parches multi-evidencia y ver_roblox."""
from __future__ import annotations
import urllib.request
import sys

_GOOD = "f20e635067a95dbf3a8b14139e2003e6ca455e7d"
_URL = f"https://raw.githubusercontent.com/ellisfernando06-sketch/Test---Hospital/{_GOOD}/comandos_nuevos.py"

def _bootstrap():
    print("[comandos_nuevos] Descargando módulo completo…")
    with urllib.request.urlopen(_URL, timeout=45) as resp:
        source = resp.read().decode("utf-8")
    print(f"[comandos_nuevos] Descargado ({len(source)} bytes)")

    # Multi-evidencia en /sancionar
    source = source.replace(
        '''evidencia_archivo="Imagen/video/clip de evidencia (opcional)",
        duracion="Duración si aplica (ej: 3 días)",''',
        '''evidencia_archivo="Imagen/video de evidencia #1 (opcional)",
        evidencia_archivo2="Imagen/video de evidencia #2 (opcional)",
        evidencia_archivo3="Imagen/video de evidencia #3 (opcional)",
        duracion="Duración si aplica (ej: 3 días)",'''
    )
    source = source.replace(
        '''evidencia_archivo: Optional[discord.Attachment] = None,
        duracion: str = "",
    ):
        if not permisos.puede_actuar_sobre(interaction.user, usuario):
            await interaction.response.send_message(
                "❌ No puedes sancionar a alguien de tu mismo nivel o superior.", ephemeral=True)
            return

        urls: List[str] = []
        if evidencia_archivo:
            urls.append(evidencia_archivo.url)''',
        '''evidencia_archivo: Optional[discord.Attachment] = None,
        evidencia_archivo2: Optional[discord.Attachment] = None,
        evidencia_archivo3: Optional[discord.Attachment] = None,
        duracion: str = "",
    ):
        if not permisos.puede_actuar_sobre(interaction.user, usuario):
            await interaction.response.send_message(
                "❌ No puedes sancionar a alguien de tu mismo nivel o superior.", ephemeral=True)
            return

        urls: List[str] = []
        for att in (evidencia_archivo, evidencia_archivo2, evidencia_archivo3):
            if att:
                urls.append(att.url)'''
    )

    # ver_roblox enriquecido
    old_ver = '''    @bot.tree.command(name="ver_roblox", description="Consulta el usuario Roblox verificado de un miembro")
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
            f"**Discord:** {usuario.mention}\\n**Roblox:** `{roblox}`",
            autor=usuario,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)'''
    new_ver = '''    @bot.tree.command(name="ver_roblox", description="Consulta el usuario Roblox verificado de un miembro")
    @app_commands.describe(usuario="Usuario")
    @require_key("STAFF", "SUPERVISOR", "DIRECTOR", "OWNER")
    async def ver_roblox(interaction: discord.Interaction, usuario: discord.Member):
        info = verificacion.obtener_roblox_completo(usuario.id)
        if not info:
            await interaction.response.send_message(
                f"⚠️ {usuario.mention} no tiene Roblox verificado.", ephemeral=True)
            return
        roblox_data = {
            "name": info.get("roblox"),
            "id": info.get("roblox_id"),
            "displayName": info.get("displayName") or info.get("roblox"),
            "avatar_url": info.get("avatar_url"),
            "created": None,
        }
        from estilos import embed_roblox_verificacion
        embed = embed_roblox_verificacion(
            discord_user=usuario,
            roblox_data=roblox_data,
            staff=None,
            aprobado=True,
        )
        embed.title = "🎮 Roblox verificado"
        await interaction.response.send_message(embed=embed, ephemeral=True)'''
    if old_ver in source:
        source = source.replace(old_ver, new_ver)

    mod = sys.modules[__name__]
    exec(compile(source, "comandos_nuevos_remote.py", "exec"), mod.__dict__)
    print("[comandos_nuevos] Módulo completo cargado")

_bootstrap()
