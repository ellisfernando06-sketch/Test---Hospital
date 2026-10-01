# -*- coding: utf-8 -*-
"""roles_setup.py — escanea, reutiliza keys, crea faltantes, ordena."""
from __future__ import annotations

import asyncio
from typing import Dict, List, Optional, Set, Tuple

import discord

import roles_config
import roles_store

_KEY_LEGACY_ALIASES: Dict[str, Tuple[str, ...]] = {
    "FUNDADOR_OWNER": ("OWNER",),
    "DIR_GENERAL": ("DIRECTOR_GENERAL",),
    "DIR_MEDICO": ("DIRECTOR_MEDICO",),
    "DIR_ENFERMERIA": ("DIRECTOR_ENFERMERIA",),
    "DIR_RRHH": ("DIRECTOR_RRHH",),
    "DIR_DOCENCIA": ("DIRECTOR_DOCENCIA",),
    "DIR_LOGISTICA": ("DIRECTOR_LOGISTICA",),
    "INTERNO": ("PASANTE",),
}

_NOMBRES_LEGADOS: Dict[str, str] = {
    "gerente developer": "FUNDADOR_OWNER",
    "🛠️ gerente developer": "FUNDADOR_OWNER",
    "👑 owner": "FUNDADOR_OWNER",
    "owner": "FUNDADOR_OWNER",
    "fundador": "FUNDADOR_OWNER",
    "fundador y owner": "FUNDADOR_OWNER",
    "co-owner": "CO_OWNER",
    "co owner": "CO_OWNER",
    "director general": "DIR_GENERAL",
    "director médico": "DIR_MEDICO",
    "director medico": "DIR_MEDICO",
    "director de enfermería": "DIR_ENFERMERIA",
    "director de enfermeria": "DIR_ENFERMERIA",
    "director de rrhh": "DIR_RRHH",
    "director de docencia": "DIR_DOCENCIA",
    "director de docencia e investigación": "DIR_DOCENCIA",
    "director de investigación y docencia": "DIR_DOCENCIA",
    "director de logística": "DIR_LOGISTICA",
    "director de logistica": "DIR_LOGISTICA",
    "prefecto": "PREFECTO_OPERACIONES",
    "prefecto de operaciones": "PREFECTO_OPERACIONES",
    "residente": "RESIDENTE",
    "pasante": "INTERNO",
    "interno": "INTERNO",
    "practicante": "INTERNO",
}


def _hex_to_colour(hex_str: str) -> discord.Colour:
    h = (hex_str or "").lstrip("#")
    if not h or h.lower() in ("000000", "default", "none"):
        return discord.Colour.default()
    try:
        return discord.Colour(int(h, 16))
    except Exception:
        return discord.Colour.default()


def _guardar_key_con_aliases(key: str, role_id: int) -> None:
    roles_store.guardar_key(key, role_id)
    for alias in _KEY_LEGACY_ALIASES.get(key, ()):
        roles_store.guardar_key(alias, role_id)


def _norm(s: str) -> str:
    return (s or "").lower().strip()


def _buscar_rol_por_nombre(guild: discord.Guild, nombre: str) -> Optional[discord.Role]:
    for r in guild.roles:
        if r.name == nombre:
            return r
    nl = _norm(nombre)
    for r in guild.roles:
        if _norm(r.name) == nl:
            return r
    nl2 = "".join(c for c in nl if c.isalnum() or c.isspace())
    for r in guild.roles:
        rn = "".join(c for c in _norm(r.name) if c.isalnum() or c.isspace())
        if rn and rn == nl2:
            return r
    return None


def _buscar_rol_para_key(guild: discord.Guild, key: str) -> Optional[discord.Role]:
    rid = roles_store.obtener_id_key(key)
    if rid:
        r = guild.get_role(rid)
        if r:
            return r
    for alias in _KEY_LEGACY_ALIASES.get(key, ()):
        rid = roles_store.obtener_id_key(alias)
        if rid:
            r = guild.get_role(rid)
            if r:
                return r
    oficial = roles_config.KEYS_NOMBRES.get(key)
    if oficial:
        r = _buscar_rol_por_nombre(guild, oficial[0])
        if r:
            return r
    for nom, k in _NOMBRES_LEGADOS.items():
        if k != key:
            continue
        for r in guild.roles:
            rn = _norm(r.name)
            if rn == nom or nom in rn:
                return r
    return None


async def _asegurar_rol(
    guild: discord.Guild,
    nombre: str,
    color_hex: str,
    resumen: List[str],
    *,
    renombrar_si_antiguo: bool = False,
    es_separador: bool = False,
    rol_existente: Optional[discord.Role] = None,
) -> Optional[discord.Role]:
    existente = rol_existente or _buscar_rol_por_nombre(guild, nombre)
    if existente:
        if renombrar_si_antiguo and existente.name != nombre:
            try:
                kwargs = {"name": nombre, "reason": "Organigrama oficial"}
                if es_separador:
                    kwargs.update(
                        colour=discord.Colour.default(),
                        permissions=discord.Permissions.none(),
                        hoist=False,
                        mentionable=False,
                    )
                else:
                    kwargs["colour"] = _hex_to_colour(color_hex)
                old = existente.name
                await existente.edit(**kwargs)
                resumen.append(f"🔄 **{old}** → **{nombre}**")
            except Exception:
                resumen.append(f"✅ **{existente.name}** (`{existente.id}`)")
        else:
            if es_separador:
                try:
                    await existente.edit(
                        colour=discord.Colour.default(),
                        permissions=discord.Permissions.none(),
                        hoist=False,
                        mentionable=False,
                    )
                except Exception:
                    pass
            resumen.append(f"✅ **{nombre}** (`{existente.id}`)")
        return existente

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
                colour=_hex_to_colour(color_hex),
                permissions=discord.Permissions.none(),
                hoist=False,
                mentionable=False,
                reason="Organigrama oficial",
            )
        resumen.append(f"🆕 **{nombre}** (`{rol.id}`)")
        await asyncio.sleep(0.45)
        return rol
    except discord.Forbidden:
        resumen.append(f"❌ Sin permisos: **{nombre}** (sube el rol del bot)")
        return None
    except Exception as e:
        resumen.append(f"❌ **{nombre}**: {e}")
        return None


def _orden_deseado() -> List[Tuple[str, str]]:
    orden: List[Tuple[str, str]] = []
    seps = {s[0]: s[1] for s in roles_config.SEPARADORES_ROLES}
    bloques = [
        ("sep_autoridades", "autoridades"),
        ("sep_staff_server", "staff_server"),
        ("sep_gerencia", "gerencia"),
        ("sep_jefatura", "jefatura"),
        ("sep_area_medica", "area_medica"),
        ("sep_area_enfermeria", "area_enfermeria"),
        ("sep_apoyo_clinico", "apoyo_clinico"),
        ("sep_area_admin", "area_admin"),
    ]
    for sep_key, sec_key in bloques:
        if sep_key in seps:
            orden.append(("sep", seps[sep_key]))
        for key in roles_config.SECCIONES.get(sec_key, {}).get("keys", []):
            if key in roles_config.KEYS_NOMBRES:
                orden.append(("key", roles_config.KEYS_NOMBRES[key][0]))
    if "sep_sistema" in seps:
        orden.append(("sep", seps["sep_sistema"]))
    if "INACTIVIDAD_JUSTIFICADA" in roles_config.KEYS_NOMBRES:
        orden.append(("key", roles_config.KEYS_NOMBRES["INACTIVIDAD_JUSTIFICADA"][0]))
    for _, (nombre, _) in roles_config.ROLES_OTORGADOS_CONSERVAR.items():
        orden.append(("otorgado", nombre))
    return orden


async def ordenar_roles(guild: discord.Guild) -> List[str]:
    resumen: List[str] = []
    if not guild.me:
        return ["❌ Sin miembro del bot"]
    bot_top = guild.me.top_role
    roles_ordenados: List[discord.Role] = []
    vistos: Set[int] = set()
    for _, nombre in _orden_deseado():
        rol = _buscar_rol_por_nombre(guild, nombre)
        if not rol or rol.id in vistos:
            continue
        if rol.is_default() or rol.managed or not (rol < bot_top):
            continue
        roles_ordenados.append(rol)
        vistos.add(rol.id)
    if not roles_ordenados:
        return ["⚠️ Nada que ordenar"]
    base = bot_top.position - 1
    positions = {}
    for i, rol in enumerate(roles_ordenados):
        pos = base - i
        if pos >= 1:
            positions[rol] = pos
    try:
        await guild.edit_role_positions(positions=positions, reason="Organigrama oficial")
        resumen.append(f"✅ Reordenados ({len(positions)})")
        for r in roles_ordenados:
            if r in positions:
                resumen.append(f"  • {r.name}")
    except Exception as e:
        resumen.append(f"❌ Reordenar: {e}")
    return resumen


async def configurar_organigrama(guild: discord.Guild) -> List[str]:
    resumen: List[str] = [
        "**Organigrama — escaneo + creación**",
        "_Existentes se reutilizan · faltantes se crean · keys se guardan._",
        "",
    ]
    keys_orden = list(roles_config.JERARQUIA_KEYS)
    if "INACTIVIDAD_JUSTIFICADA" in roles_config.KEYS_NOMBRES:
        keys_orden.append("INACTIVIDAD_JUSTIFICADA")

    detectados = creados = fallidos = 0
    for key in keys_orden:
        if key not in roles_config.KEYS_NOMBRES:
            continue
        nombre, color = roles_config.KEYS_NOMBRES[key]
        encontrado = _buscar_rol_para_key(guild, key)
        era = encontrado is not None
        rol = await _asegurar_rol(
            guild, nombre, color, resumen,
            renombrar_si_antiguo=(key in ("FUNDADOR_OWNER", "DIR_DOCENCIA")),
            rol_existente=encontrado,
        )
        if rol:
            _guardar_key_con_aliases(key, rol.id)
            aliases = _KEY_LEGACY_ALIASES.get(key, ())
            extra = f" + {', '.join(f'`{a}`' for a in aliases)}" if aliases else ""
            resumen.append(f"   🔑 `{key}`{extra} → `{rol.id}`")
            if era:
                detectados += 1
            else:
                creados += 1
        else:
            fallidos += 1

    resumen.append("")
    resumen.append(f"**Keys:** {detectados} detectados · {creados} creados · {fallidos} fallidos")
    resumen.append("")
    resumen.append("**Otorgados (certs · seguridad · uniformes)**")
    for clave, (nombre, color) in roles_config.ROLES_OTORGADOS_CONSERVAR.items():
        rol = await _asegurar_rol(guild, nombre, color, resumen)
        if rol:
            roles_store.guardar_extra(f"otorgado_{clave}", rol.id)

    resumen.append("")
    resumen.append("**Separadores**")
    for sep_key, nombre, _ in roles_config.SEPARADORES_ROLES:
        rol = await _asegurar_rol(guild, nombre, "", resumen, es_separador=True)
        if rol:
            roles_store.guardar_extra(sep_key, rol.id)

    resumen.append("")
    resumen.append("**Orden**")
    resumen.extend(await ordenar_roles(guild))
    return resumen


def roles_uniforme(guild: discord.Guild) -> List[discord.Role]:
    out: List[discord.Role] = []
    for clave in ("uniforme_medico", "uniforme_enfermeria", "accesorio_rp"):
        rid = roles_store.obtener_extra(f"otorgado_{clave}")
        if rid:
            rol = guild.get_role(rid)
            if rol:
                out.append(rol)
                continue
        nombre = roles_config.ROLES_OTORGADOS_CONSERVAR.get(clave, (None,))[0]
        if nombre:
            r = _buscar_rol_por_nombre(guild, nombre)
            if r:
                out.append(r)
    return out


async def asignar_uniformes_al_entrar(member: discord.Member) -> int:
    roles = roles_uniforme(member.guild)
    if not roles:
        return 0
    a_dar = [r for r in roles if r not in member.roles]
    if not a_dar:
        return 0
    try:
        await member.add_roles(*a_dar, reason="Bienvenida — categorías")
        return len(a_dar)
    except Exception:
        return -1


async def configurar_todo(guild: discord.Guild) -> List[str]:
    return await configurar_organigrama(guild)
