# -*- coding: utf-8 -*-
"""roles_setup.py — organigrama + Canciller/Vice Canciller."""
from __future__ import annotations

import asyncio
from typing import Dict, List, Optional, Set, Tuple

import discord

import roles_config
import roles_store

_KEY_LEGACY_ALIASES: Dict[str, Tuple[str, ...]] = {
    "CANCILLER": ("PREFECTO_OPERACIONES",),
    "FUNDADOR_OWNER": ("OWNER",),
    "DIR_GENERAL": ("DIRECTOR_GENERAL",),
    "DIR_MEDICO": ("DIRECTOR_MEDICO",),
    "DIR_ENFERMERIA": ("DIRECTOR_ENFERMERIA",),
    "DIR_RRHH": ("DIRECTOR_RRHH",),
    "DIR_DOCENCIA": ("DIRECTOR_DOCENCIA",),
    "DIR_LOGISTICA": ("DIRECTOR_LOGISTICA",),
    "INTERNO": ("PASANTE",),
    "JEFE_SEGURIDAD": ("jefe_seguridad",),
    "SUPERVISOR_SEGURIDAD": ("supervisor_seguridad",),
    "GUARDIA": ("guardia",),
}

_NOMBRES_LEGADOS: Dict[str, str] = {
    "gerente developer": "FUNDADOR_OWNER",
    "owner": "FUNDADOR_OWNER",
    "fundador": "FUNDADOR_OWNER",
    "fundador y owner": "FUNDADOR_OWNER",
    "co-owner": "CO_OWNER",
    "director general": "DIR_GENERAL",
    "director médico": "DIR_MEDICO",
    "director medico": "DIR_MEDICO",
    "director de enfermería": "DIR_ENFERMERIA",
    "director de enfermeria": "DIR_ENFERMERIA",
    "director de rrhh": "DIR_RRHH",
    "director de docencia": "DIR_DOCENCIA",
    "director de logística": "DIR_LOGISTICA",
    "director de logistica": "DIR_LOGISTICA",
    "prefecto": "CANCILLER",
    "canciller": "CANCILLER",
    "vice canciller": "VICE_CANCILLER",
    "prefecto de operaciones": "CANCILLER",
    "residente": "RESIDENTE",
    "pasante": "INTERNO",
    "interno": "INTERNO",
    "jefe de seguridad": "JEFE_SEGURIDAD",
    "supervisor de seguridad": "SUPERVISOR_SEGURIDAD",
    "guardia": "GUARDIA",
    "visitante": "VISITANTE",
    "miembro": "MIEMBRO",
    "comunidad": "COMUNIDAD",
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
    # Canciller también guarda PREFECTO
    if key == "CANCILLER":
        roles_store.guardar_key("PREFECTO_OPERACIONES", role_id)


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
    if key in ("VISITANTE", "MIEMBRO", "COMUNIDAD"):
        try:
            import roles_acceso
            fn = {
                "VISITANTE": roles_acceso.rol_visitante,
                "MIEMBRO": roles_acceso.rol_miembro,
                "COMUNIDAD": roles_acceso.rol_comunidad,
            }.get(key)
            if fn:
                r = fn(guild)
                if r:
                    return r
        except Exception:
            pass
    # Prefecto legado → Canciller
    if key in ("CANCILLER", "PREFECTO_OPERACIONES"):
        for r in guild.roles:
            rn = _norm(r.name)
            if "prefecto" in rn or "canciller" in rn and "vice" not in rn:
                return r
    return None


def _buscar_separador(guild: discord.Guild, nombre_nuevo: str) -> Optional[discord.Role]:
    r = _buscar_rol_por_nombre(guild, nombre_nuevo)
    if r:
        return r
    key = nombre_nuevo
    if "『" in nombre_nuevo and "』" in nombre_nuevo:
        key = nombre_nuevo.split("『", 1)[1].split("』", 1)[0].strip()
    key_low = "".join(c for c in key.lower() if c.isalnum() or c.isspace()).strip()
    for r in guild.roles:
        rn = r.name or ""
        if "『" not in rn and "━" not in rn and "─" not in rn:
            continue
        rn_low = "".join(c for c in rn.lower() if c.isalnum() or c.isspace())
        if key_low and key_low in rn_low:
            return r
    return None


async def _asegurar_rol(
    guild: discord.Guild, nombre: str, color_hex: str, *,
    renombrar_si_antiguo: bool = False, es_separador: bool = False,
    rol_existente: Optional[discord.Role] = None,
) -> Tuple[Optional[discord.Role], str]:
    existente = rol_existente or _buscar_rol_por_nombre(guild, nombre)
    if existente:
        if renombrar_si_antiguo and existente.name != nombre:
            try:
                kwargs = {"name": nombre, "reason": "Organigrama oficial"}
                if es_separador:
                    kwargs.update(colour=discord.Colour.default(), permissions=discord.Permissions.none(), hoist=False, mentionable=False)
                else:
                    kwargs["colour"] = _hex_to_colour(color_hex)
                await existente.edit(**kwargs)
                return existente, "renombrado"
            except Exception:
                return existente, "ok"
        if es_separador:
            try:
                await existente.edit(colour=discord.Colour.default(), permissions=discord.Permissions.none(), hoist=False, mentionable=False)
            except Exception:
                pass
        return existente, "ok"
    try:
        if es_separador:
            rol = await guild.create_role(name=nombre, colour=discord.Colour.default(), permissions=discord.Permissions.none(), hoist=False, mentionable=False, reason="Separador")
        else:
            rol = await guild.create_role(name=nombre, colour=_hex_to_colour(color_hex), permissions=discord.Permissions.none(), hoist=False, mentionable=False, reason="Organigrama")
        await asyncio.sleep(0.35)
        return rol, "nuevo"
    except Exception as e:
        return None, f"error:{e}"


def _linea_rol(nombre: str, estado: str, role_id: Optional[int] = None) -> str:
    icon = {"ok": "✅", "nuevo": "🆕", "renombrado": "🔄"}.get(estado, "❌")
    id_txt = f" `{role_id}`" if role_id else ""
    if estado.startswith("error:"):
        return f"❌ **{nombre}** — {estado[6:40]}"
    return f"{icon} **{nombre}**{id_txt}"


def _orden_deseado() -> List[Tuple[str, str]]:
    orden: List[Tuple[str, str]] = []
    seps = {s[0]: s[1] for s in roles_config.SEPARADORES_ROLES}

    def add_sep(key: str):
        if key in seps:
            orden.append(("sep", seps[key]))

    def add_section(sec_key: str):
        for key in roles_config.SECCIONES.get(sec_key, {}).get("keys", []):
            if key in roles_config.KEYS_NOMBRES:
                orden.append(("key", roles_config.KEYS_NOMBRES[key][0]))

    def add_grupo(grupo: dict):
        for _c, (nombre, _col) in grupo.items():
            orden.append(("otorgado", nombre))

    for sep_key, sec_key in [
        ("sep_autoridades", "autoridades"), ("sep_staff_server", "staff_server"),
        ("sep_gerencia", "gerencia"), ("sep_jefatura", "jefatura"), ("sep_area_medica", "area_medica"),
    ]:
        add_sep(sep_key)
        add_section(sec_key)
    add_sep("sep_especialidades")
    add_grupo(getattr(roles_config, "ESPECIALIDADES_MEDICAS", {}))
    for sep_key, sec_key in [
        ("sep_area_enfermeria", "area_enfermeria"), ("sep_apoyo_clinico", "apoyo_clinico"),
        ("sep_area_admin", "area_admin"), ("sep_seguridad", "seguridad"),
    ]:
        add_sep(sep_key)
        add_section(sec_key)
    add_sep("sep_certificados")
    add_grupo(getattr(roles_config, "CERTIFICADOS", {}))
    add_sep("sep_uniformes")
    add_grupo(getattr(roles_config, "UNIFORMES_CATEGORIA", {}))
    add_sep("sep_herramientas_pj")
    add_grupo(getattr(roles_config, "HERRAMIENTAS_PJ", {}))
    add_sep("sep_sistema")
    for sk in getattr(roles_config, "ROLES_SISTEMA_KEYS", ["VISITANTE", "MIEMBRO", "COMUNIDAD", "INACTIVIDAD_JUSTIFICADA"]):
        if sk in roles_config.KEYS_NOMBRES:
            orden.append(("key", roles_config.KEYS_NOMBRES[sk][0]))
    return orden


async def ordenar_roles(guild: discord.Guild) -> List[str]:
    resumen: List[str] = []
    if not guild.me:
        return ["❌ Sin miembro del bot"]
    bot_top = guild.me.top_role
    roles_ordenados: List[discord.Role] = []
    vistos: Set[int] = set()
    for _, nombre in _orden_deseado():
        rol = _buscar_rol_por_nombre(guild, nombre) or _buscar_separador(guild, nombre)
        if not rol or rol.id in vistos:
            continue
        if rol.is_default() or rol.managed or not (rol < bot_top):
            continue
        roles_ordenados.append(rol)
        vistos.add(rol.id)
    if not roles_ordenados:
        return ["⚠️ Nada que ordenar"]
    base = bot_top.position - 1
    positions = {rol: base - i for i, rol in enumerate(roles_ordenados) if base - i >= 1}
    try:
        await guild.edit_role_positions(positions=positions, reason="Organigrama oficial")
        resumen.append(f"✅ Reordenados **{len(positions)}** roles")
    except Exception as e:
        resumen.append(f"❌ Reordenar: {e}")
    return resumen


async def configurar_organigrama(guild: discord.Guild) -> List[str]:
    lineas: List[str] = ["**Organigrama completo**", "_Incluye Canciller y Vice Canciller._", ""]
    total_ok = total_nuevo = total_err = 0
    seps = {s[0]: s[1] for s in roles_config.SEPARADORES_ROLES}
    bloques = [
        ("sep_autoridades", "autoridades"), ("sep_staff_server", "staff_server"),
        ("sep_gerencia", "gerencia"), ("sep_jefatura", "jefatura"), ("sep_area_medica", "area_medica"),
        ("sep_area_enfermeria", "area_enfermeria"), ("sep_apoyo_clinico", "apoyo_clinico"),
        ("sep_area_admin", "area_admin"), ("sep_seguridad", "seguridad"),
    ]
    for sep_key, sec_key in bloques:
        sep_nombre = seps.get(sep_key, sec_key)
        lineas.append(f"**{sep_nombre}**")
        existente_sep = _buscar_separador(guild, sep_nombre)
        rol_s, est_s = await _asegurar_rol(guild, sep_nombre, "", es_separador=True, renombrar_si_antiguo=True, rol_existente=existente_sep)
        if rol_s:
            roles_store.guardar_extra(sep_key, rol_s.id)
            lineas.append(_linea_rol("(separador)", est_s, rol_s.id))
        for key in roles_config.SECCIONES.get(sec_key, {}).get("keys", []):
            if key not in roles_config.KEYS_NOMBRES:
                continue
            if key == "PREFECTO_OPERACIONES":
                continue  # usar CANCILLER
            nombre, color = roles_config.KEYS_NOMBRES[key]
            encontrado = _buscar_rol_para_key(guild, key)
            rol, est = await _asegurar_rol(
                guild, nombre, color,
                renombrar_si_antiguo=(key in ("FUNDADOR_OWNER", "DIR_DOCENCIA", "CANCILLER", "PREFECTO_OPERACIONES")),
                rol_existente=encontrado,
            )
            if rol:
                _guardar_key_con_aliases(key, rol.id)
                lineas.append(_linea_rol(f"{nombre}  · `{key}`", est, rol.id))
                total_nuevo += 1 if est == "nuevo" else 0
                total_ok += 0 if est == "nuevo" else 1
            else:
                lineas.append(_linea_rol(f"{nombre}  · `{key}`", est))
                total_err += 1
        lineas.append("")
    for sep_key, titulo, grupo in getattr(roles_config, "CATEGORIAS_OTORGADAS_ORDEN", []):
        sep_nombre = seps.get(sep_key, titulo)
        lineas.append(f"**{sep_nombre}**")
        existente_sep = _buscar_separador(guild, sep_nombre)
        rol_s, est_s = await _asegurar_rol(guild, sep_nombre, "", es_separador=True, renombrar_si_antiguo=True, rol_existente=existente_sep)
        if rol_s:
            roles_store.guardar_extra(sep_key, rol_s.id)
            lineas.append(_linea_rol("(separador)", est_s, rol_s.id))
        for clave, (nombre, color) in grupo.items():
            rol, est = await _asegurar_rol(guild, nombre, color)
            if rol:
                roles_store.guardar_extra(f"otorgado_{clave}", rol.id)
                lineas.append(_linea_rol(nombre, est, rol.id))
                total_nuevo += 1 if est == "nuevo" else 0
                total_ok += 0 if est == "nuevo" else 1
            else:
                lineas.append(_linea_rol(nombre, est))
                total_err += 1
        lineas.append("")
    if "sep_sistema" in seps:
        lineas.append(f"**{seps['sep_sistema']}**")
        existente_sep = _buscar_separador(guild, seps["sep_sistema"])
        rol_s, est_s = await _asegurar_rol(guild, seps["sep_sistema"], "", es_separador=True, renombrar_si_antiguo=True, rol_existente=existente_sep)
        if rol_s:
            roles_store.guardar_extra("sep_sistema", rol_s.id)
            lineas.append(_linea_rol("(separador)", est_s, rol_s.id))
    for sk in getattr(roles_config, "ROLES_SISTEMA_KEYS", ["VISITANTE", "MIEMBRO", "COMUNIDAD", "INACTIVIDAD_JUSTIFICADA"]):
        if sk not in roles_config.KEYS_NOMBRES:
            continue
        nombre, color = roles_config.KEYS_NOMBRES[sk]
        encontrado = _buscar_rol_para_key(guild, sk)
        rol, est = await _asegurar_rol(guild, nombre, color, renombrar_si_antiguo=True, rol_existente=encontrado)
        if rol:
            _guardar_key_con_aliases(sk, rol.id)
            lineas.append(_linea_rol(f"{nombre}  · `{sk}`", est, rol.id))
            total_nuevo += 1 if est == "nuevo" else 0
            total_ok += 0 if est == "nuevo" else 1
        else:
            lineas.append(_linea_rol(f"{nombre}  · `{sk}`", est))
            total_err += 1
    lineas.append("")
    lineas.append("━━━━━━━━━━━━━━━━━━━━")
    lineas.append(f"**Resumen:** ✅ {total_ok} · 🆕 {total_nuevo} · ❌ {total_err}")
    lineas.append("")
    lineas.append("**Orden**")
    lineas.extend(await ordenar_roles(guild))
    return lineas


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
