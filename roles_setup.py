# -*- coding: utf-8 -*-
"""
roles_setup.py — Crea y ordena roles según el organigrama oficial (roles_config).

Orden (arriba → abajo en Discord):
  Separador → roles de esa sección (jerarquía) → siguiente sección…

Keys:
  - Guarda key NUEVA (FUNDADOR_OWNER, DIR_*, …)
  - Y alias LEGADO (OWNER, DIRECTOR_*, …) con el mismo role_id
    para no romper el núcleo ni comandos antiguos.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import discord

import roles_config
import roles_store

# Key oficial → aliases legados que deben apuntar al MISMO role_id
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

# Nombres viejos → key oficial (detección por nombre en Discord)
_NOMBRES_LEGADOS: Dict[str, str] = {
    "gerente developer": "FUNDADOR_OWNER",
    "🛠️ gerente developer": "FUNDADOR_OWNER",
    "👑 owner": "FUNDADOR_OWNER",
    "owner": "FUNDADOR_OWNER",
    "director general": "DIR_GENERAL",
    "director médico": "DIR_MEDICO",
    "director medico": "DIR_MEDICO",
    "director de rrhh": "DIR_RRHH",
    "director de docencia": "DIR_DOCENCIA",
    "director de investigación y docencia": "DIR_DOCENCIA",
    "director de logística": "DIR_LOGISTICA",
    "director de logistica": "DIR_LOGISTICA",
    "director de enfermería": "DIR_ENFERMERIA",
    "director de enfermeria": "DIR_ENFERMERIA",
    "💉 director de enfermería": "DIR_ENFERMERIA",
    "pasante": "INTERNO",
}


def _hex_to_colour(hex_str: str) -> discord.Colour:
    h = (hex_str or "").lstrip("#")
    if not h or h.lower() in ("000000", "default", "none"):
        return discord.Colour.default()
    return discord.Colour(int(h, 16))


def _guardar_key_con_aliases(key: str, role_id: int) -> None:
    """Guarda la key oficial + todos sus alias legados."""
    roles_store.guardar_key(key, role_id)
    for alias in _KEY_LEGACY_ALIASES.get(key, ()):
        roles_store.guardar_key(alias, role_id)


def _buscar_rol_por_nombre(guild: discord.Guild, nombre: str) -> Optional[discord.Role]:
    for r in guild.roles:
        if r.name == nombre:
            return r
    nombre_l = nombre.lower().strip()
    for r in guild.roles:
        if (r.name or "").lower().strip() == nombre_l:
            return r
    return None


def _buscar_rol_para_key(guild: discord.Guild, key: str) -> Optional[discord.Role]:
    oficial = roles_config.KEYS_NOMBRES.get(key)
    if oficial:
        r = _buscar_rol_por_nombre(guild, oficial[0])
        if r:
            return r

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

    for nom, k in _NOMBRES_LEGADOS.items():
        if k != key:
            continue
        for r in guild.roles:
            if (r.name or "").lower().strip() == nom:
                return r
            if nom in (r.name or "").lower():
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
                kwargs = {"name": nombre, "reason": "Migración a organigrama oficial"}
                if es_separador:
                    kwargs["colour"] = discord.Colour.default()
                    kwargs["permissions"] = discord.Permissions.none()
                    kwargs["hoist"] = False
                    kwargs["mentionable"] = False
                else:
                    kwargs["colour"] = _hex_to_colour(color_hex)
                old = existente.name
                await existente.edit(**kwargs)
                resumen.append(f"🔄 Renombrado: **{old}** → **{nombre}**")
            except Exception:
                resumen.append(f"✅ Detectado: **{existente.name}** (`{existente.id}`)")
        else:
            if es_separador:
                try:
                    await existente.edit(
                        colour=discord.Colour.default(),
                        permissions=discord.Permissions.none(),
                        hoist=False,
                        mentionable=False,
                        reason="Separador: sin color ni permisos",
                    )
                except Exception:
                    pass
            elif color_hex:
                try:
                    await existente.edit(
                        colour=_hex_to_colour(color_hex),
                        reason="Ajuste color organigrama",
                    )
                except Exception:
                    pass
            resumen.append(f"✅ Detectado: **{nombre}** (`{existente.id}`)")
        return existente

    try:
        if es_separador:
            rol = await guild.create_role(
                name=nombre,
                colour=discord.Colour.default(),
                permissions=discord.Permissions.none(),
                hoist=False,
                mentionable=False,
                reason="Separador de categoría",
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
        resumen.append(f"🆕 Creado: **{nombre}** (`{rol.id}`)")
        return rol
    except discord.Forbidden:
        resumen.append(f"❌ Sin permisos para crear: **{nombre}**")
        return None
    except Exception as e:
        resumen.append(f"❌ Error al crear **{nombre}**: {e}")
        return None


def _orden_deseado() -> List[Tuple[str, str]]:
    """Lista (tipo, nombre) de arriba → abajo según roles_config."""
    orden: List[Tuple[str, str]] = []
    seps = {s[0]: s[1] for s in roles_config.SEPARADORES_ROLES}

    bloques_sep = [
        ("sep_autoridades", "autoridades"),
        ("sep_staff_server", "staff_server"),
        ("sep_gerencia", "gerencia"),
        ("sep_jefatura", "jefatura"),
        ("sep_area_medica", "area_medica"),
        ("sep_area_enfermeria", "area_enfermeria"),
        ("sep_apoyo_clinico", "apoyo_clinico"),
        ("sep_area_admin", "area_admin"),
    ]

    for sep_key, sec_key in bloques_sep:
        if sep_key in seps:
            orden.append(("sep", seps[sep_key]))
        sec = roles_config.SECCIONES.get(sec_key, {})
        for key in sec.get("keys", []):
            if key in roles_config.KEYS_NOMBRES:
                orden.append(("key", roles_config.KEYS_NOMBRES[key][0]))

    if "sep_sistema" in seps:
        orden.append(("sep", seps["sep_sistema"]))
    if "INACTIVIDAD_JUSTIFICADA" in roles_config.KEYS_NOMBRES:
        orden.append(("key", roles_config.KEYS_NOMBRES["INACTIVIDAD_JUSTIFICADA"][0]))

    for _clave, (nombre, _c) in roles_config.ROLES_OTORGADOS_CONSERVAR.items():
        orden.append(("otorgado", nombre))

    return orden


async def ordenar_roles(guild: discord.Guild) -> List[str]:
    resumen: List[str] = []
    bot_member = guild.me
    if not bot_member:
        return ["❌ No se pudo obtener el miembro del bot."]

    bot_top = bot_member.top_role
    orden = _orden_deseado()

    roles_ordenados: List[discord.Role] = []
    vistos: set = set()
    for _, nombre in orden:
        rol = _buscar_rol_por_nombre(guild, nombre)
        if not rol or rol.id in vistos:
            continue
        if rol.is_default() or rol.managed:
            continue
        if not (rol < bot_top):
            continue
        roles_ordenados.append(rol)
        vistos.add(rol.id)

    if not roles_ordenados:
        resumen.append("⚠️ No hay roles gestionables para ordenar.")
        return resumen

    base_pos = bot_top.position - 1
    positions = {}
    omitidos: List[str] = []
    for i, rol in enumerate(roles_ordenados):
        nueva = base_pos - i
        if nueva < 1:
            omitidos.append(rol.name)
            continue
        positions[rol] = nueva

    if not positions:
        resumen.append("⚠️ No hay espacio de posiciones bajo el rol del bot.")
        return resumen

    try:
        await guild.edit_role_positions(
            positions=positions, reason="Orden organigrama oficial"
        )
        resumen.append(f"✅ Roles reordenados ({len(positions)}).")
        resumen.append("**Orden (mayor → menor):**")
        for r in roles_ordenados:
            if r in positions:
                resumen.append(f"  • {r.name}")
        if omitidos:
            resumen.append(f"⚠️ Sin espacio: {', '.join(omitidos)}")
    except discord.Forbidden:
        resumen.append("❌ Sin permisos para reordenar roles (sube el rol del bot).")
    except Exception as e:
        resumen.append(f"❌ Error al reordenar: {e}")

    return resumen


async def configurar_organigrama(guild: discord.Guild) -> List[str]:
    resumen: List[str] = ["**Organigrama oficial — Roles y keys**"]

    keys_orden = list(roles_config.JERARQUIA_KEYS)
    if "INACTIVIDAD_JUSTIFICADA" in roles_config.KEYS_NOMBRES:
        keys_orden.append("INACTIVIDAD_JUSTIFICADA")

    for key in keys_orden:
        if key not in roles_config.KEYS_NOMBRES:
            continue
        nombre, color = roles_config.KEYS_NOMBRES[key]
        encontrado = _buscar_rol_para_key(guild, key)
        renombrar = key == "FUNDADOR_OWNER"
        rol = await _asegurar_rol(
            guild,
            nombre,
            color,
            resumen,
            renombrar_si_antiguo=renombrar,
            es_separador=False,
            rol_existente=encontrado,
        )
        if rol:
            _guardar_key_con_aliases(key, rol.id)
            aliases = _KEY_LEGACY_ALIASES.get(key, ())
            if aliases:
                resumen.append(
                    f"   🔑 `{key}` + alias {', '.join(f'`{a}`' for a in aliases)} → `{rol.id}`"
                )
            else:
                resumen.append(f"   🔑 `{key}` → `{rol.id}`")

    resumen.append("")
    resumen.append("**Roles otorgados (Docencia · Seguridad · Uniformes)**")
    for clave, (nombre, color) in roles_config.ROLES_OTORGADOS_CONSERVAR.items():
        rol = await _asegurar_rol(guild, nombre, color, resumen, es_separador=False)
        if rol:
            roles_store.guardar_extra(f"otorgado_{clave}", rol.id)

    resumen.append("")
    resumen.append("**Separadores (sin color · sin permisos)**")
    for sep_key, nombre, _color in roles_config.SEPARADORES_ROLES:
        rol = await _asegurar_rol(
            guild, nombre, "", resumen, es_separador=True
        )
        if rol:
            roles_store.guardar_extra(sep_key, rol.id)

    resumen.append("")
    resumen.append("**Orden jerárquico**")
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
        await member.add_roles(*a_dar, reason="Bienvenida — uniformes de categoría")
        return len(a_dar)
    except Exception:
        return -1


async def configurar_todo(guild: discord.Guild) -> List[str]:
    return await configurar_organigrama(guild)
