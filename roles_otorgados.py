# -*- coding: utf-8 -*
"""
roles_otorgados.py — Todo lo otorgado (certificados, tienda, licencias…)
se refleja como ROL de Discord, con prefijo de categoría.
"""
from __future__ import annotations

import traceback
from typing import Optional, Tuple

import discord
from discord.ext import commands

# Prefijo visible en el nombre del rol → categoría RP
CATEGORIA_ROL = {
    "certificados": ("📜 Cert", 0x8E44AD),
    "licencias": ("📋 Lic", 0x2980B9),
    "identificacion": ("🪪 ID", 0x1ABC9C),
    "uniformes": ("👔 Ropa", 0x34495E),
    "accesorios": ("💍 Acc", 0xE91E63),
    "instrumentos_medicos": ("🩺 Eq", 0xE74C3C),
    "farmacia": ("💊 Farm", 0x27AE60),
    "tecnologia": ("💻 Tec", 0x3498DB),
    "documentos": ("📄 Doc", 0x95A5A6),
    "otros": ("📦 Item", 0x7F8C8D),
}

_MAP_TIENDA = {
    "instrumentos_medicos": "instrumentos_medicos",
    "farmacia": "farmacia",
    "uniformes": "uniformes",
    "tecnologia": "tecnologia",
    "alimentacion": "otros",
    "bienestar": "otros",
    "hospedaje": "otros",
    "casas": "otros",
    "combustible": "otros",
}


def _slug_nombre(nombre: str) -> str:
    n = (nombre or "item").strip()
    # Discord role name max 100
    return n[:60]


def nombre_rol(categoria: str, nombre_item: str) -> str:
    pref, _ = CATEGORIA_ROL.get(categoria, CATEGORIA_ROL["otros"])
    return f"{pref} · {_slug_nombre(nombre_item)}"


async def _buscar_o_crear_rol(
    guild: discord.Guild,
    nombre: str,
    color: int,
    reason: str = "Rol otorgado RP",
) -> Optional[discord.Role]:
    """Busca por nombre exacto; si no existe, crea (sin duplicar)."""
    for r in guild.roles:
        if r.name == nombre:
            return r
    # Fallback case-insensitive
    nl = nombre.lower()
    for r in guild.roles:
        if r.name.lower() == nl:
            return r
    try:
        if not guild.me.guild_permissions.manage_roles:
            print("[roles_otorgados] sin permiso Manage Roles")
            return None
        rol = await guild.create_role(
            name=nombre[:100],
            colour=discord.Colour(color),
            mentionable=False,
            hoist=False,
            reason=reason,
        )
        # Intentar colocar el rol bajo el del bot (visible pero no top)
        try:
            pos = max(1, guild.me.top_role.position - 1)
            await rol.edit(position=pos, reason="Orden categoría otorgados")
        except Exception:
            pass
        return rol
    except Exception as e:
        print(f"[roles_otorgados] crear rol: {e}")
        return None


async def otorgar_rol(
    member: discord.Member,
    *,
    categoria: str,
    nombre: str,
    reason: str = "Otorgado",
) -> Tuple[bool, str]:
    """
    Asigna el rol de categoría al miembro.
    Devuelve (ok, mensaje).
    """
    if not isinstance(member, discord.Member) or not member.guild:
        return False, "Miembro inválido"
    cat = categoria if categoria in CATEGORIA_ROL else "otros"
    pref, color = CATEGORIA_ROL[cat]
    rol_nombre = nombre_rol(cat, nombre)
    rol = await _buscar_o_crear_rol(member.guild, rol_nombre, color, reason=reason)
    if not rol:
        return False, f"No se pudo crear/encontrar el rol `{rol_nombre}`"
    if rol >= member.guild.me.top_role:
        return False, f"El rol `{rol_nombre}` está por encima del bot"
    if rol in member.roles:
        return True, f"Ya tenía {rol.mention}"
    try:
        await member.add_roles(rol, reason=reason[:200])
        return True, f"Rol asignado: {rol.mention}"
    except discord.Forbidden:
        return False, "Sin permiso para asignar roles"
    except Exception as e:
        return False, str(e)


def _categoria_desde_tienda(info: dict, item_id: str = "") -> str:
    cat_t = (info or {}).get("cat") or "otros"
    cat = _MAP_TIENDA.get(cat_t, "otros")
    n = ((info or {}).get("nombre") or item_id or "").lower()
    if any(x in n for x in ("uniforme", "bata", "casaca", "pantal", "zapat", "gorro", "ropa")):
        return "uniformes"
    if any(x in n for x in ("credencial", "carnet", "identific", "placa")):
        return "identificacion"
    if any(x in n for x in ("licencia", "habilit")):
        return "licencias"
    if any(x in n for x in ("anillo", "reloj", "collar", "lentes", "gafa", "accesorio")):
        return "accesorios"
    return cat


async def otorgar_certificado_rol(member: discord.Member, nombre_cert: str, numero: str = "") -> Tuple[bool, str]:
    label = nombre_cert
    if numero:
        label = f"{nombre_cert}"
    return await otorgar_rol(
        member,
        categoria="certificados",
        nombre=label,
        reason=f"Certificado {numero or nombre_cert}",
    )


async def otorgar_item_tienda_rol(member: discord.Member, item_id: str, info: dict) -> Tuple[bool, str]:
    cat = _categoria_desde_tienda(info, item_id)
    nombre = (info or {}).get("nombre") or item_id
    return await otorgar_rol(
        member,
        categoria=cat,
        nombre=nombre,
        reason=f"Compra tienda: {nombre}",
    )


def roles_otorgados_del_member(member: discord.Member) -> dict:
    """Agrupa los roles del miembro que son 'otorgados' por prefijo de categoría."""
    out = {k: [] for k in CATEGORIA_ROL}
    prefs = {CATEGORIA_ROL[k][0]: k for k in CATEGORIA_ROL}
    for r in member.roles:
        if r.is_default():
            continue
        for pref, cat in prefs.items():
            if r.name.startswith(pref):
                out[cat].append(r)
                break
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
    """Tras comprar en tienda → asignar rol de categoría."""
    try:
        import tienda1
    except Exception:
        try:
            import tienda as tienda1  # type: ignore
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
            # Guardar pendiente de rol; se aplica en el siguiente event loop vía bot si hay member
            try:
                info = (getattr(tienda1, "CATALOGO", {}) or {}).get(item_id) or {"nombre": item_id}
                # Marcar para asignación asíncrona
                pendientes = getattr(tienda1, "_pend_roles", None)
                if pendientes is None:
                    tienda1._pend_roles = []
                    pendientes = tienda1._pend_roles
                pendientes.append((uid, item_id, dict(info)))
            except Exception as e:
                print("[roles_otorgados] tienda pend:", e)
        return ok, msg

    tienda1.comprar = comprar_wrap
    tienda1._roles_otorgados_patch = True
    print("[roles_otorgados] tienda.comprar parchado")


def _parche_firmas() -> None:
    """Al emitir certificado autorizado → rol 📜 Cert."""
    try:
        import firmas
    except Exception:
        print("[roles_otorgados] firmas no importable")
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
            nombre = reg.get("capacitacion") or "Certificación"
            numero = reg.get("numero") or ""
            ok, msg = await otorgar_certificado_rol(member, nombre, numero)
            print(f"[roles_otorgados] cert rol: {ok} {msg}")
            try:
                await inter.followup.send(
                    f"🎭 Rol de certificado: {msg}",
                    ephemeral=True,
                )
            except Exception:
                pass
        except Exception as e:
            print("[roles_otorgados] emitir cert:", e)

    firmas._emitir_certificado_autorizado = emitir_wrap
    firmas._roles_otorgados_patch = True
    print("[roles_otorgados] firmas._emitir parchado")


def _cmd_ver(bot: commands.Bot) -> None:
    from discord import app_commands

    # Reemplaza mi_inventario si estaba quitado: comando liviano de roles otorgados
    for n in ("mis_otorgados", "mi_equipo"):
        try:
            bot.tree.remove_command(n)
        except Exception:
            pass

    @bot.tree.command(
        name="mis_otorgados",
        description="Ver tus roles otorgados por categoría (certificados, ropa, equipo…)",
    )
    async def mis_otorgados(inter: discord.Interaction):
        if not isinstance(inter.user, discord.Member):
            return await inter.response.send_message("❌ Solo en el servidor.", ephemeral=True)

        # Aplicar compras pendientes de tienda (roles)
        try:
            import tienda1
            pend = list(getattr(tienda1, "_pend_roles", []) or [])
            tienda1._pend_roles = []
            for uid, item_id, info in pend:
                if uid != inter.user.id:
                    # reencolar otras
                    tienda1._pend_roles.append((uid, item_id, info))
                    continue
                await otorgar_item_tienda_rol(inter.user, item_id, info)
        except Exception:
            pass

        grupos = roles_otorgados_del_member(inter.user)
        emb = discord.Embed(
            title=f"🎭 Otorgados de {inter.user.display_name}",
            description=(
                "Lo que tienes **como roles** del servidor, por categoría.\n"
                "Úsalos en RP según corresponda (uniforme, equipo, certificado…)."
            ),
            color=0x9B59B6,
        )
        vacio = True
        for cat, (pref, color) in CATEGORIA_ROL.items():
            roles = grupos.get(cat) or []
            if not roles:
                continue
            vacio = False
            lineas = [r.mention for r in roles[:20]]
            if len(roles) > 20:
                lineas.append(f"… +{len(roles) - 20}")
            emb.add_field(
                name=f"{pref} ({len(roles)})",
                value="\n".join(lineas),
                inline=False,
            )
        if vacio:
            emb.description = (
                "No tienes roles de otorgados aún.\n"
                "Se asignan al **certificar**, al **comprar en la tienda** u otros sistemas."
            )
        await inter.response.send_message(embed=emb, ephemeral=True)

    # Listener: tras interacciones de tienda, vaciar pendientes del comprador
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
                try:
                    m = inter.guild.get_member(uid) or inter.user
                    if isinstance(m, discord.Member):
                        await otorgar_item_tienda_rol(m, item_id, info)
                except Exception as e:
                    print("[roles_otorgados] apply shop:", e)
            tienda1._pend_roles = quedan
        except Exception:
            pass
