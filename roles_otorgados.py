# -*- coding: utf-8 -*
"""
roles_otorgados.py — Asigna roles DENTRO de las categorías del servidor
(『 GRADUADOS 』, 『 IDENTIFICACIÓN 』, 『 EQUIPO 』, 『 UNIFORMES 』).
Usa ROLES_OTORGADOS de config.py (mismos que crea /configurar_roles).
"""
from __future__ import annotations

import traceback
from typing import Optional, Tuple

import discord
from discord.ext import commands

import config
import roles_store


def _hex(c: str) -> discord.Colour:
    return discord.Colour(int(c.lstrip("#"), 16))


def _buscar_rol(guild: discord.Guild, nombre: str) -> Optional[discord.Role]:
    for r in guild.roles:
        if r.name == nombre:
            return r
    nl = nombre.lower()
    for r in guild.roles:
        if r.name.lower() == nl:
            return r
    return None


async def _asegurar_rol_otorgado(guild: discord.Guild, clave: str) -> Optional[discord.Role]:
    tabla = getattr(config, "ROLES_OTORGADOS", {}) or {}
    if clave not in tabla:
        return None
    nombre, color, _sep = tabla[clave]
    # ID guardado
    rid = roles_store.obtener_extra(f"otorgado_{clave}") if hasattr(roles_store, "obtener_extra") else None
    if rid:
        rol = guild.get_role(int(rid))
        if rol:
            return rol
    rol = _buscar_rol(guild, nombre)
    if rol:
        try:
            roles_store.guardar_extra(f"otorgado_{clave}", rol.id)
        except Exception:
            pass
        return rol
    try:
        if not guild.me.guild_permissions.manage_roles:
            return None
        rol = await guild.create_role(
            name=nombre[:100],
            colour=_hex(color),
            mentionable=False,
            hoist=False,
            reason=f"Rol otorgado categoría ({clave})",
        )
        roles_store.guardar_extra(f"otorgado_{clave}", rol.id)
        return rol
    except Exception as e:
        print("[roles_otorgados] crear:", e)
        return None


async def asignar_clave(member: discord.Member, clave: str, reason: str = "Otorgado") -> Tuple[bool, str]:
    """Asigna el rol fijo de ROLES_OTORGADOS[clave]."""
    if not isinstance(member, discord.Member):
        return False, "Miembro inválido"
    tabla = getattr(config, "ROLES_OTORGADOS", {}) or {}
    if clave not in tabla:
        return False, f"Clave de rol desconocida: {clave}"
    nombre = tabla[clave][0]
    rol = await _asegurar_rol_otorgado(member.guild, clave)
    if not rol:
        return False, f"No se pudo obtener el rol **{nombre}**"
    if rol >= member.guild.me.top_role:
        return False, f"El rol **{nombre}** está por encima del bot"
    if rol in member.roles:
        return True, f"Ya tenía {rol.mention}"
    try:
        await member.add_roles(rol, reason=reason[:200])
        return True, f"Asignado {rol.mention}"
    except Exception as e:
        return False, str(e)


def _clave_cert(nombre_cert: str) -> str:
    n = (nombre_cert or "").strip().lower()
    mapa = getattr(config, "MAP_CERT_A_ROL", {}) or {}
    for k, v in mapa.items():
        if k in n:
            return v
    return "certificado_general"


async def otorgar_certificado_rol(member: discord.Member, nombre_cert: str, numero: str = "") -> Tuple[bool, str]:
    """Graduado + certificado específico."""
    msgs = []
    ok1, m1 = await asignar_clave(member, "graduado", reason=f"Graduado {numero or nombre_cert}")
    msgs.append(m1)
    clave = _clave_cert(nombre_cert)
    ok2, m2 = await asignar_clave(member, clave, reason=f"Cert {nombre_cert}")
    msgs.append(m2)
    return ok1 or ok2, " · ".join(msgs)


async def otorgar_item_tienda_rol(member: discord.Member, item_id: str, info: dict) -> Tuple[bool, str]:
    cat = (info or {}).get("cat") or ""
    mapa = getattr(config, "MAP_TIENDA_CAT_A_ROL", {}) or {}
    clave = mapa.get(cat)
    n = ((info or {}).get("nombre") or item_id or "").lower()
    if any(x in n for x in ("enfermer", "bata enfer")):
        clave = "uniforme_enfermeria"
    elif any(x in n for x in ("uniforme", "bata", "casaca")):
        clave = clave or "uniforme_medico"
    elif any(x in n for x in ("credencial", "carnet")):
        clave = "credencial"
    elif any(x in n for x in ("licencia médica", "licencia medica")):
        clave = "licencia_medica"
    elif any(x in n for x in ("anillo", "reloj", "accesorio")):
        clave = "accesorio_rp"
    if not clave:
        clave = "eq_clinico" if cat == "instrumentos_medicos" else "eq_farmacia" if cat == "farmacia" else None
    if not clave:
        return False, "Sin categoría de rol para este ítem"
    return await asignar_clave(member, clave, reason=f"Tienda: {(info or {}).get('nombre', item_id)}")


def roles_por_categoria(member: discord.Member) -> dict:
    """Agrupa roles del miembro según ROLES_OTORGADOS / separadores."""
    tabla = getattr(config, "ROLES_OTORGADOS", {}) or {}
    seps = {s[0]: s[1] for s in getattr(config, "SEPARADORES_ROLES", [])}
    out = {}
    nombres_a_sep = {v[0]: v[2] for v in tabla.values()}
    for r in member.roles:
        if r.is_default():
            continue
        sk = nombres_a_sep.get(r.name)
        if not sk:
            continue
        titulo = seps.get(sk, sk)
        out.setdefault(titulo, []).append(r)
    return out


def registrar(bot: commands.Bot) -> None:
    print("[roles_otorgados] cargando…")
    try:
        _parche_tienda()
        _parche_firmas()
        _cmd_ver(bot)
        print("[roles_otorgados] ✓ OK")
    except Exception:
        print("[roles_otorgados] ✗ error:")
        traceback.print_exc()


def _parche_tienda() -> None:
    try:
        import tienda1
    except Exception:
        print("[roles_otorgados] tienda no importable")
        return
    if getattr(tienda1, "_roles_otorgados_patch", False):
        return
    orig = getattr(tienda1, "comprar", None)
    if not callable(orig):
        return

    def comprar_wrap(uid: int, item_id: str, cantidad: int = 1):
        ok, msg = orig(uid, item_id, cantidad)
        if ok:
            try:
                info = (getattr(tienda1, "CATALOGO", {}) or {}).get(item_id) or {"nombre": item_id}
                if getattr(tienda1, "_pend_roles", None) is None:
                    tienda1._pend_roles = []
                tienda1._pend_roles.append((uid, item_id, dict(info)))
            except Exception as e:
                print("[roles_otorgados] tienda pend:", e)
        return ok, msg

    tienda1.comprar = comprar_wrap
    tienda1._roles_otorgados_patch = True


def _parche_firmas() -> None:
    try:
        import firmas
    except Exception:
        return
    if getattr(firmas, "_roles_otorgados_patch", False):
        return
    orig = getattr(firmas, "_emitir_certificado_autorizado", None)
    if not callable(orig):
        return

    async def emitir_wrap(bot, inter: discord.Interaction, reg: dict):
        await orig(bot, inter, reg)
        try:
            uid = int(reg.get("receptor_id") or 0)
            guild = inter.guild
            if not guild or not uid:
                return
            member = guild.get_member(uid)
            if not member:
                try:
                    member = await guild.fetch_member(uid)
                except Exception:
                    return
            ok, msg = await otorgar_certificado_rol(
                member,
                reg.get("capacitacion") or "Certificación",
                reg.get("numero") or "",
            )
            print(f"[roles_otorgados] cert: {ok} {msg}")
            try:
                await inter.followup.send(f"🎭 Roles de graduado/certificado: {msg}", ephemeral=True)
            except Exception:
                pass
        except Exception as e:
            print("[roles_otorgados] emitir:", e)

    firmas._emitir_certificado_autorizado = emitir_wrap
    firmas._roles_otorgados_patch = True


def _cmd_ver(bot: commands.Bot) -> None:
    from discord import app_commands

    try:
        bot.tree.remove_command("mis_otorgados")
    except Exception:
        pass

    @bot.tree.command(
        name="mis_otorgados",
        description="Ver tus roles por categoría (graduados, ID, equipo, uniformes)",
    )
    async def mis_otorgados(inter: discord.Interaction):
        if not isinstance(inter.user, discord.Member):
            return await inter.response.send_message("❌ Solo en el servidor.", ephemeral=True)

        # Aplicar compras pendientes
        try:
            import tienda1
            pend = list(getattr(tienda1, "_pend_roles", []) or [])
            tienda1._pend_roles = []
            for uid, item_id, info in pend:
                if uid != inter.user.id:
                    tienda1._pend_roles.append((uid, item_id, info))
                    continue
                await otorgar_item_tienda_rol(inter.user, item_id, info)
        except Exception:
            pass

        grupos = roles_por_categoria(inter.user)
        emb = discord.Embed(
            title=f"🎭 Roles otorgados · {inter.user.display_name}",
            description=(
                "Roles **dentro de las categorías** del servidor.\n"
                "(Graduados, identificación, equipo RP, uniformes)"
            ),
            color=0x9B59B6,
        )
        if not grupos:
            emb.description += (
                "\n\n_Aún no tienes roles de estas categorías._\n"
                "Se asignan al certificar o comprar en la tienda.\n"
                "Un admin debe ejecutar **configurar roles** para crear las categorías."
            )
        for titulo, roles in grupos.items():
            emb.add_field(
                name=titulo,
                value="\n".join(r.mention for r in roles) or "—",
                inline=False,
            )
        await inter.response.send_message(embed=emb, ephemeral=True)

    @bot.listen("on_interaction")
    async def _aplicar_roles_tienda(inter: discord.Interaction):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return
        try:
            import tienda1
            pend = getattr(tienda1, "_pend_roles", None)
            if not pend:
                return
            quedan = []
            for uid, item_id, info in list(pend):
                if uid != inter.user.id:
                    quedan.append((uid, item_id, info))
                    continue
                m = inter.guild.get_member(uid) or inter.user
                if isinstance(m, discord.Member):
                    await otorgar_item_tienda_rol(m, item_id, info)
            tienda1._pend_roles = quedan
        except Exception:
            pass
