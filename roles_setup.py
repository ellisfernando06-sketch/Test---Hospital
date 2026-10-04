# -*- coding: utf-8 -*-
"""roles_setup.py — carga organigrama; respeta hoist y @mention manuales."""
from __future__ import annotations

import importlib
import sys
import types
import urllib.request

# Última versión buena conocida en el repo (antes del PLACEHOLDER)
_URL = (
    "https://raw.githubusercontent.com/ellisfernando06-sketch/Test---Hospital/"
    "fd793aa8c736de6617c77e332e0ef850befe7c1c/roles_setup.py"
)


def _parchear_asegurar(mod: types.ModuleType) -> None:
    """No tocar hoist / mentionable / permissions en roles que ya existen."""
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
            # Respetar edición manual (Mostrar por separado / Permitir @mention)
            if renombrar_si_antiguo and existente.name != nombre:
                try:
                    kw = {"name": nombre, "reason": "Organigrama (solo nombre)"}
                    if es_separador:
                        kw["colour"] = discord.Colour.default()
                    await existente.edit(**kw)
                    return existente, "renombrado"
                except Exception:
                    return existente, "ok"
            if es_separador:
                try:
                    kw = {"reason": "Separador: sin permisos/color"}
                    need = False
                    if existente.permissions.value != 0:
                        kw["permissions"] = discord.Permissions.none()
                        need = True
                    if existente.colour.value != 0:
                        kw["colour"] = discord.Colour.default()
                        need = True
                    if need:
                        await existente.edit(**kw)
                except Exception:
                    pass
            return existente, "ok"
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


try:
    _mod = _cargar()
except Exception as e:
    print(f"[roles_setup] fallback local falló descarga: {e}")
    raise

# Re-exportar API pública del módulo descargado
globals().update({k: getattr(_mod, k) for k in dir(_mod) if not k.startswith("__")})

print("[roles_setup] cargado + parche hoist/@mention")
