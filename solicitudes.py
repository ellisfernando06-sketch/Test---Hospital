# -*- coding: utf-8 -*
"""
solicitudes.py — Bootstrap: carga el módulo completo desde un commit conocido
y aplica el parche on_deny + logs_store para canales de evaluación.
"""
from __future__ import annotations

import urllib.request
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

    old_sig = "on_approve: Optional[Callable] = None,\n) -> None:"
    new_sig = "on_approve: Optional[Callable] = None,\n    on_deny: Optional[Callable] = None,\n) -> None:"
    if old_sig in source:
        source = source.replace(old_sig, new_sig, 1)

    old_view = "AprobacionView(key_aprobador=key_aprobador, solicitud_id=solicitud_id, on_approve=on_approve)"
    new_view = "AprobacionView(key_aprobador=key_aprobador, solicitud_id=solicitud_id, on_approve=on_approve, on_deny=on_deny)"
    if old_view in source:
        source = source.replace(old_view, new_view, 1)

    mod = sys.modules[__name__]
    exec(compile(source, "solicitudes_remote.py", "exec"), mod.__dict__)
    print("[solicitudes] Módulo completo cargado")

    # Integrar logs_store (canales elegidos al publicar paneles)
    try:
        import logs_store as _ls
        import config as _cfg

        _orig = mod.__dict__.get("enviar_solicitud")
        _orig_apr = mod.__dict__.get("enviar_solicitud_con_aprobacion")

        if _orig:
            async def enviar_solicitud(interaction, key_destinatario, embed, canal_log="log_solicitudes"):
                cid = _ls.get_canal_id(canal_log)
                if cid and isinstance(getattr(_cfg, "CANALES", None), dict):
                    _cfg.CANALES[canal_log] = cid
                return await _orig(interaction, key_destinatario, embed, canal_log)
            mod.__dict__["enviar_solicitud"] = enviar_solicitud

        if _orig_apr:
            async def enviar_solicitud_con_aprobacion(
                interaction, key_aprobador, embed, tipo, datos=None,
                canal_key=None, on_approve=None, on_deny=None,
            ):
                ck = canal_key or "log_solicitudes"
                cid = _ls.get_canal_id(ck)
                if cid and isinstance(getattr(_cfg, "CANALES", None), dict):
                    _cfg.CANALES[ck] = cid
                return await _orig_apr(
                    interaction, key_aprobador, embed, tipo, datos,
                    canal_key=canal_key, on_approve=on_approve, on_deny=on_deny,
                )
            mod.__dict__["enviar_solicitud_con_aprobacion"] = enviar_solicitud_con_aprobacion

        print("[solicitudes] logs_store integrado")
    except Exception as e:
        print("[solicitudes] logs_store no aplicado:", e)

_bootstrap()
