# -*- coding: utf-8 -*-
"""
roles_separadores_auto.py
Refuerza roles_setup para otorgar TODOS los separadores al entrar.
No rompe el arranque: solo parchea funciones si roles_setup ya cargó.
"""
from __future__ import annotations

from typing import List, Optional, Set

import discord


def _aplicar_parche() -> None:
    try:
        import roles_setup
        import roles_config
        import roles_store
    except Exception as e:
        print("[roles_separadores_auto] skip:", e, flush=True)
        return

    def roles_separadores(guild: discord.Guild) -> List[discord.Role]:
        out: List[discord.Role] = []
        vistos: Set[int] = set()

        def _add(rol: Optional[discord.Role]) -> None:
            if (
                rol
                and rol.id not in vistos
                and not rol.is_default()
                and not rol.managed
            ):
                out.append(rol)
                vistos.add(rol.id)

        for sep_key, nombre, _col in getattr(roles_config, "SEPARADORES_ROLES", []) or []:
            rol = None
            try:
                rid = roles_store.obtener_extra(sep_key)
                if rid:
                    rol = guild.get_role(int(rid))
            except Exception:
                pass
            if not rol:
                try:
                    rol = roles_setup._buscar_rol_por_nombre(guild, nombre)
                except Exception:
                    rol = None
                if not rol:
                    try:
                        rol = roles_setup._buscar_separador(guild, nombre)
                    except Exception:
                        rol = None
            _add(rol)

        nombres = {
            (n or "").strip().lower()
            for _, n, _ in getattr(roles_config, "SEPARADORES_ROLES", []) or []
            if n
        }
        for rol in guild.roles:
            if rol.id in vistos or rol.is_default() or rol.managed:
                continue
            nm = (rol.name or "").strip().lower()
            if nm in nombres or (
                "━━━━━━━━" in (rol.name or "") and "『" in (rol.name or "")
            ):
                _add(rol)
        return out

    async def asignar_separadores_miembro(member: discord.Member) -> int:
        if member.bot or not member.guild:
            return 0
        seps = roles_separadores(member.guild)
        if not seps:
            return 0
        a_dar = [r for r in seps if r not in member.roles]
        if not a_dar:
            return 0
        try:
            await member.add_roles(
                *a_dar, reason="Separadores del organigrama (automático al entrar)"
            )
            return len(a_dar)
        except Exception:
            n = 0
            for r in a_dar:
                try:
                    await member.add_roles(
                        r, reason="Separador organigrama (automático al entrar)"
                    )
                    n += 1
                except Exception:
                    pass
            return n

    roles_setup.roles_separadores = roles_separadores
    roles_setup.asignar_separadores_miembro = asignar_separadores_miembro
    print("[roles_separadores_auto] parche aplicado", flush=True)


def registrar(bot) -> None:
    _aplicar_parche()


# Al importar (hospital_core lo carga como módulo)
try:
    _aplicar_parche()
except Exception as e:
    print("[roles_separadores_auto]", e, flush=True)
