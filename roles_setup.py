# -*- coding: utf-8 -*-
"""roles_setup.py — organigrama; respeta hoist y @mention en TODOS los roles."""
from __future__ import annotations

import sys
import types
import urllib.request

_URL = (
    "https://raw.githubusercontent.com/ellisfernando06-sketch/Test---Hospital/"
    "fd793aa8c736de6617c77e332e0ef850befe7c1c/roles_setup.py"
)


def _parchear_asegurar(mod: types.ModuleType) -> None:
    """
    Regla para TODOS los roles que ya existen:
    - No tocar hoist (Mostrar por separado)
    - No tocar mentionable (Permitir @mention)
    - No tocar permissions ni color personalizado
    Solo puede renombrar si el organigrama lo pide.
    """
    import asyncio
    from typing import Optional, Tuple

    import discord

    orig_buscar = mod._buscar_rol_por_nombre
    hex_to = mod._hex_to_colour

    async def _asegurar_rol(
        guild: discord.Guild,
        nombre: str,
        color_hex: str,
        *,
        renombrar_si_antiguo: bool = False,
        es_separador: bool = False,
        rol_existente: Optional[discord.Role] = None,
    ) -> Tuple[Optional[discord.Role], str]:
        existente = rol_existente or orig_buscar(guild, nombre)
        if existente:
            # Cualquier rol ya creado: el staff manda en Discord
            if renombrar_si_antiguo and existente.name != nombre:
                try:
                    await existente.edit(
                        name=nombre,
                        reason="Organigrama (solo nombre; hoist/@mention intactos)",
                    )
                    return existente, "renombrado"
                except Exception:
                    return existente, "ok"
            # No editar nada más (ni separadores: no forzar hoist/mentionable/perms)
            return existente, "ok"

        # Solo al CREAR se usan defaults; luego el staff puede cambiarlos y se quedan
        try:
            if es_separador:
                rol = await guild.create_role(
                    name=nombre,
                    colour=discord.Colour.default(),
                    permissions=discord.Permissions.none(),
                    hoist=False,
                    mentionable=False,
                    reason="Separador organigrama",
                )
            else:
                rol = await guild.create_role(
                    name=nombre,
                    colour=hex_to(color_hex),
                    permissions=discord.Permissions.none(),
                    hoist=False,
                    mentionable=False,
                    reason="Organigrama oficial",
                )
            await asyncio.sleep(0.35)
            return rol, "nuevo"
        except Exception as e:
            return None, f"error:{e}"

    mod._asegurar_rol = _asegurar_rol


def _cargar() -> types.ModuleType:
    req = urllib.request.Request(_URL, headers={"User-Agent": "HospitalBot/roles_setup"})
    with urllib.request.urlopen(req, timeout=40) as r:
        src = r.read().decode("utf-8", errors="replace")
    if len(src) < 500 or "PLACEHOLDER" in src:
        raise RuntimeError("roles_setup remoto inválido")
    mod = types.ModuleType("roles_setup")
    mod.__file__ = __file__
    exec(compile(src, "roles_setup_remote.py", "exec"), mod.__dict__)
    _parchear_asegurar(mod)
    sys.modules["roles_setup"] = mod
    return mod


_mod = _cargar()
globals().update({k: getattr(_mod, k) for k in dir(_mod) if not k.startswith("__")})
print("[roles_setup] OK — hoist/@mention preservados en TODOS los roles existentes")
