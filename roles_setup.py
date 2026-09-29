# -*- coding: utf-8 -*-
"""
roles_setup.py — Crea y ordena roles según el organigrama oficial (roles_config).
- Roles de organigrama: con color y sin permisos especiales.
- Separadores de categoría: SIN color y SIN permisos (solo visual).
- Uniformes: se asignan todos al entrar al servidor.
No borra roles antiguos aquí; eso se hace en un paso posterior con respaldo.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

import discord

import roles_config
import roles_store


def _hex_to_colour(hex_str: str) -> discord.Colour:
    h = (hex_str or "").lstrip("#")
    if not h or h.lower() in ("000000", "default", "none"):
        return discord.Colour.default()
    return discord.Colour(int(h, 16))


def _buscar_rol_por_nombre(guild: discord.Guild, nombre: str) -> Optional[discord.Role]:
    for r in guild.roles:
        if r.name == nombre:
            return r
    nombre_l = nombre.lower()
    for r in guild.roles:
        if r.name.lower() == nombre_l:
            return r
    # Compatibilidad: detectar el antiguo "Gerente Developer" / Owner
    if "fundador" in nombre_l or "owner" in nombre_l:
        for r in guild.roles:
            rn = (r.name or "").lower()
            if any(x in rn for x in ("gerente developer", "👑 owner", "owner", "fundador")):
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
) -> Optional[discord.Role]:
    """
    Crea o detecta un rol.
    - es_separador=True → sin color y sin permisos (solo visual de categoría).
    """
    existente = _buscar_rol_por_nombre(guild, nombre)

    if existente:
        if renombrar_si_antiguo and existente.name != nombre:
            try:
                kwargs = {
                    "name": nombre,
                    "reason": "Migración a organigrama oficial",
                }
                if es_separador:
                    kwargs["colour"] = discord.Colour.default()
                    kwargs["permissions"] = discord.Permissions.none()
                    kwargs["hoist"] = False
                    kwargs["mentionable"] = False
                else:
                    kwargs["colour"] = _hex_to_colour(color_hex)
                await existente.edit(**kwargs)
                resumen.append(f"🔄 Renombrado: **{existente.name}** → **{nombre}**")
            except Exception:
                resumen.append(f"✅ Detectado: **{existente.name}** (ID `{existente.id}`)")
        else:
            # Ajustar separadores existentes: quitar color y permisos
            if es_separador:
                try:
                    await existente.edit(
                        colour=discord.Colour.default(),
                        permissions=discord.Permissions.none(),
                        hoist=False,
                        mentionable=False,
                        reason="Separador de categoría: sin color ni permisos",
                    )
                except Exception:
                    pass
            else:
                try:
                    color_actual = str(existente.colour)
                    if color_hex and color_hex.lower() not in color_actual.lower():
                        await existente.edit(
                            colour=_hex_to_colour(color_hex),
                            reason="Ajuste color organigrama",
                        )
                except Exception:
                    pass
            resumen.append(f"✅ Detectado: **{nombre}** (ID `{existente.id}`)")
        return existente

    # Crear nuevo
    try:
        if es_separador:
            rol = await guild.create_role(
                name=nombre,
                colour=discord.Colour.default(),
                permissions=discord.Permissions.none(),
                hoist=False,
                mentionable=False,
                reason="Separador de categoría — sin color ni permisos",
            )
        else:
            rol = await guild.create_role(
                name=nombre,
                colour=_hex_to_colour(color_hex),
                permissions=discord.Permissions.none(),
                hoist=False,
                mentionable=False,
                reason="Organigrama oficial — creación automática",
            )
        resumen.append(f"🆕 Creado: **{nombre}** (ID `{rol.id}`)")
        return rol
    except discord.Forbidden:
        resumen.append(f"❌ Sin permisos para crear: **{nombre}**")
        return None
    except Exception as e:
        resumen.append(f"❌ Error al crear **{nombre}**: {e}")
        return None


def _orden_deseado() -> List[Tuple[str, str]]:
    """Orden de arriba → abajo según organigrama oficial."""
    orden: List[Tuple[str, str]] = []

    seps = {s[0]: s[1] for s in roles_config.SEPARADORES_ROLES}

    def sep(key: str):
        if key in seps:
            orden.append(("sep", seps[key]))

    # Autoridades
    sep("sep_autoridades")
    for key in ("FUNDADOR_OWNER", "CO_OWNER"):
        if key in roles_config.KEYS_NOMBRES:
            orden.append(("key", roles_config.KEYS_NOMBRES[key][0]))

    # Staff del Server
    sep("sep_staff_server")
    for key in ("ADMIN_JEFE", "ADMIN", "ADMIN_PRUEBA"):
        if key in roles_config.KEYS_NOMBRES:
            orden.append(("key", roles_config.KEYS_NOMBRES[key][0]))

    # Gerencia
    sep("sep_gerencia")
    for key in (
        "PREFECTO_OPERACIONES", "DIR_GENERAL", "DIR_MEDICO",
        "DIR_RRHH", "DIR_DOCENCIA", "DIR_LOGISTICA",
    ):
        if key in roles_config.KEYS_NOMBRES:
            orden.append(("key", roles_config.KEYS_NOMBRES[key][0]))

    # Jefatura
    sep("sep_jefatura")
    if "JEFE_DEPARTAMENTO" in roles_config.KEYS_NOMBRES:
        orden.append(("key", roles_config.KEYS_NOMBRES["JEFE_DEPARTAMENTO"][0]))

    # Área Médica
    sep("sep_area_medica")
    for key in (
        "JEFE_SERVICIO", "MEDICO_ESPECIALISTA", "MEDICO_GENERAL",
        "JEFE_GUIA_RESIDENTES", "RESIDENTE", "INTERNO",
    ):
        if key in roles_config.KEYS_NOMBRES:
            orden.append(("key", roles_config.KEYS_NOMBRES[key][0]))

    # Área Administrativa
    sep("sep_area_admin")
    for key in ("ADMINISTRATIVO_SENIOR", "ADMINISTRATIVO_JUNIOR"):
        if key in roles_config.KEYS_NOMBRES:
            orden.append(("key", roles_config.KEYS_NOMBRES[key][0]))

    # Sistema
    sep("sep_sistema")
    if "INACTIVIDAD_JUSTIFICADA" in roles_config.KEYS_NOMBRES:
        orden.append(("key", roles_config.KEYS_NOMBRES["INACTIVIDAD_JUSTIFICADA"][0]))

    # Roles otorgados conservados (Docencia + Seguridad + Uniformes)
    for _clave, (nombre, _color) in roles_config.ROLES_OTORGADOS_CONSERVAR.items():
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
    for _, nombre in orden:
        rol = _buscar_rol_por_nombre(guild, nombre)
        if rol and rol < bot_top and not rol.is_default() and not rol.managed:
            roles_ordenados.append(rol)

    if not roles_ordenados:
        resumen.append("⚠️ No hay roles gestionables para ordenar.")
        return resumen

    base_pos = bot_top.position - 1
    positions = {}
    roles_omitidos: List[discord.Role] = []
    for i, rol in enumerate(roles_ordenados):
        nueva = base_pos - i
        if nueva < 1:
            roles_omitidos.append(rol)
            continue
        positions[rol] = nueva

    if not positions:
        resumen.append("⚠️ No hay espacio de posiciones.")
        return resumen

    try:
        await guild.edit_role_positions(positions=positions, reason="Orden organigrama oficial")
        resumen.append(f"✅ Roles reordenados ({len(positions)}).")
        resumen.append("**Orden (organigrama oficial):**")
        for r in roles_ordenados:
            if r in positions:
                resumen.append(f"  • {r.name}")
        if roles_omitidos:
            resumen.append(f"⚠️ Omitidos por posición: {', '.join(r.name for r in roles_omitidos)}")
    except discord.Forbidden:
        resumen.append("❌ Sin permisos para reordenar roles.")
    except Exception as e:
        resumen.append(f"❌ Error al reordenar: {e}")

    return resumen


async def configurar_organigrama(guild: discord.Guild) -> List[str]:
    """
    Crea / detecta todos los roles del organigrama oficial +
    Inactividad Justificada + roles otorgados conservados +
    separadores SIN color ni permisos.
    Guarda los IDs en roles_store.
    """
    resumen: List[str] = ["**Organigrama oficial — Roles de permiso**"]

    for key, (nombre, color) in roles_config.KEYS_NOMBRES.items():
        renombrar = key == "FUNDADOR_OWNER"
        rol = await _asegurar_rol(
            guild, nombre, color, resumen,
            renombrar_si_antiguo=renombrar,
            es_separador=False,
        )
        if rol:
            roles_store.guardar_key(key, rol.id)

    resumen.append("")
    resumen.append("**Roles otorgados conservados (Docencia + Seguridad + Uniformes)**")
    for clave, (nombre, color) in roles_config.ROLES_OTORGADOS_CONSERVAR.items():
        rol = await _asegurar_rol(guild, nombre, color, resumen, es_separador=False)
        if rol:
            roles_store.guardar_extra(f"otorgado_{clave}", rol.id)

    resumen.append("")
    resumen.append("**Separadores de categoría (sin color · sin permisos)**")
    for sep_key, nombre, _color in roles_config.SEPARADORES_ROLES:
        rol = await _asegurar_rol(
            guild, nombre, "", resumen,
            es_separador=True,  # ← sin color, sin permisos
        )
        if rol:
            roles_store.guardar_extra(sep_key, rol.id)

    resumen.append("")
    resumen.append("**Orden jerárquico**")
    resumen.extend(await ordenar_roles(guild))

    return resumen


def roles_uniforme(guild: discord.Guild) -> List[discord.Role]:
    """Devuelve todos los roles de uniforme/categoría que se asignan al entrar."""
    out: List[discord.Role] = []
    for clave in ("uniforme_medico", "uniforme_enfermeria", "accesorio_rp"):
        rid = roles_store.obtener_extra(f"otorgado_{clave}")
        if rid:
            rol = guild.get_role(rid)
            if rol:
                out.append(rol)
        else:
            # Fallback por nombre
            nombre = roles_config.ROLES_OTORGADOS_CONSERVAR.get(clave, (None,))[0]
            if nombre:
                r = _buscar_rol_por_nombre(guild, nombre)
                if r:
                    out.append(r)
    return out


async def asignar_uniformes_al_entrar(member: discord.Member) -> int:
    """
    Asigna TODOS los roles de categorías de uniforme al miembro que entra.
    Devuelve cuántos roles se añadieron.
    """
    roles = roles_uniforme(member.guild)
    if not roles:
        return 0
    # Solo los que aún no tiene
    a_dar = [r for r in roles if r not in member.roles]
    if not a_dar:
        return 0
    try:
        await member.add_roles(*a_dar, reason="Bienvenida — roles de categoría de uniforme")
        return len(a_dar)
    except discord.Forbidden:
        return -1
    except Exception:
        return -1


# Alias de compatibilidad con el código antiguo
async def configurar_todo(guild: discord.Guild) -> List[str]:
    return await configurar_organigrama(guild)
