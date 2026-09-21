# -*- coding: utf-8 -*-
"""
solicitudes.py — Bootstrap: carga el módulo completo desde un commit conocido
y aplica el parche on_deny. Evita el crash por CartaSolicitudModal faltante.
"""
from __future__ import annotations

import urllib.request
import types
import sys

_GOOD_COMMIT = "f20e635067a95dbf3a8b14139e2003e6ca455e7d"
_URL = (
    "https://raw.githubusercontent.com/ellisfernando06-sketch/Test---Hospital/"
    f"{_GOOD_COMMIT}/solicitudes.py"
)

def _bootstrap():
    print("[solicitudes] Descargando módulo completo…")
    with urllib.request.urlopen(_URL, timeout=45) as resp:
        source = resp.read().decode("utf-8")
    print(f"[solicitudes] Descargado ({len(source)} bytes)")

    # Parche on_deny en negar()
    old = (
        "        pending = _load_pending()\n"
        "        pending.pop(self.solicitud_id, None)\n"
        "        _save_pending(pending)\n"
        "        for child in self.children:\n"
        "            child.disabled = True\n"
        "        embed = interaction.message.embeds[0] if interaction.message.embeds else crear_embed(\"error\", \"Negado\", \"\")\n"
        "        embed.color = discord.Colour.red()\n"
        "        embed.add_field(name=\"Estado\", value=f\"❌ **NEGADO** por {interaction.user.mention}\", inline=False)\n"
        "        await interaction.response.edit_message(embed=embed, view=self)"
    )
    new = (
        "        pending = _load_pending()\n"
        "        info = pending.pop(self.solicitud_id, None)\n"
        "        _save_pending(pending)\n"
        "        for child in self.children:\n"
        "            child.disabled = True\n"
        "        embed = interaction.message.embeds[0] if interaction.message.embeds else crear_embed(\"error\", \"Negado\", \"\")\n"
        "        embed.color = discord.Colour.red()\n"
        "        embed.add_field(name=\"Estado\", value=f\"❌ **NEGADO** por {interaction.user.mention}\", inline=False)\n"
        "        await interaction.response.edit_message(embed=embed, view=self)\n"
        "        if self._on_deny and info:\n"
        "            try:\n"
        "                await self._on_deny(interaction, info)\n"
        "            except Exception as e:\n"
        "                await interaction.followup.send(f\"⚠️ Negado, pero error al ejecutar callback: {e}\", ephemeral=True)"
    )
    if old in source:
        source = source.replace(old, new, 1)

    # Añadir on_deny al signature de enviar_solicitud_con_aprobacion
    old_sig = "on_approve: Optional[Callable] = None,\n) -> None:"
    new_sig = "on_approve: Optional[Callable] = None,\n    on_deny: Optional[Callable] = None,\n) -> None:"
    if old_sig in source:
        source = source.replace(old_sig, new_sig, 1)

    old_view = "AprobacionView(key_aprobador=key_aprobador, solicitud_id=solicitud_id, on_approve=on_approve)"
    new_view = "AprobacionView(key_aprobador=key_aprobador, solicitud_id=solicitud_id, on_approve=on_approve, on_deny=on_deny)"
    if old_view in source:
        source = source.replace(old_view, new_view, 1)

    # Ejecutar en este módulo
    mod = sys.modules[__name__]
    exec(compile(source, "solicitudes_remote.py", "exec"), mod.__dict__)
    print("[solicitudes] Módulo completo cargado (CartaSolicitudModal, AprobacionView, etc.)")

_bootstrap()
