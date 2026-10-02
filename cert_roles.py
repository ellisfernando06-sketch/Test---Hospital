# -*- coding: utf-8 -*-
"""
cert_roles.py — Mapeo tipo de certificación → rol CERTIFICADOS.
Al certificarse se otorga el rol de la certificación tomada.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import discord
from discord import app_commands
from discord.ext import commands

# tipo (docencia / firmas / capacitaciones) → clave en roles_config.CERTIFICADOS
TIPO_A_CERT: Dict[str, str] = {
    # claves organigrama
    "cert_rcp": "cert_rcp",
    "cert_primeros_auxilios": "cert_primeros_auxilios",
    "cert_bioseguridad": "cert_bioseguridad",
    "cert_atencion_paciente": "cert_atencion_paciente",
    "cert_etica": "cert_etica",
    "cert_formador": "cert_formador",
    "cert_evaluacion": "cert_evaluacion",
    "cert_investigacion": "cert_investigacion",
    "cert_cuidados_enf": "cert_cuidados_enf",
    # tipos docencia.py
    "rcp": "cert_rcp",
    "bls": "cert_rcp",
    "trauma": "cert_primeros_auxilios",
    "primeros_auxilios": "cert_primeros_auxilios",
    "medicacion": "cert_atencion_paciente",
    "medicación": "cert_atencion_paciente",
    "quirurgico": "cert_bioseguridad",
    "quirúrgico": "cert_bioseguridad",
    "emergencias": "cert_primeros_auxilios",
    "enfermeria": "cert_cuidados_enf",
    "enfermería": "cert_cuidados_enf",
    "docente": "cert_formador",
    "instructor": "cert_formador",
    "formador": "cert_formador",
    "bioseguridad": "cert_bioseguridad",
    "etica": "cert_etica",
    "ética": "cert_etica",
    "evaluacion": "cert_evaluacion",
    "investigacion": "cert_investigacion",
}


def certificados_dict() -> Dict[str, Tuple[str, str]]:
    try:
        import roles_config

        return dict(getattr(roles_config, "CERTIFICADOS", {}) or {})
    except Exception:
        return {}


def choices_certificados() -> List[app_commands.Choice[str]]:
    out: List[app_commands.Choice[str]] = []
    for clave, (nombre, _col) in certificados_dict().items():
        label = nombre if len(nombre) <= 100 else nombre[:97] + "…"
        out.append(app_commands.Choice(name=label, value=clave))
    return out[:25]


def resolver_clave_cert(tipo_o_titulo: str) -> Optional[str]:
    if not tipo_o_titulo:
        return None
    t = str(tipo_o_titulo).strip().lower()
    if t in TIPO_A_CERT:
        return TIPO_A_CERT[t]
    # por nombre de rol
    for clave, (nombre, _) in certificados_dict().items():
        nl = nombre.lower()
        if t == clave.lower() or t in nl or nl in t:
            return clave
        plain = "".join(c for c in nl if c.isalnum() or c.isspace())
        if t in plain or any(w in plain for w in t.split() if len(w) > 3):
            return clave
    # palabras clave en título
    if "rcp" in t or "bls" in t:
        return "cert_rcp"
    if "trauma" in t or "primeros" in t:
        return "cert_primeros_auxilios"
    if "biosegur" in t or "quirurg" in t:
        return "cert_bioseguridad"
    if "medic" in t or "paciente" in t:
        return "cert_atencion_paciente"
    if "etic" in t or "ética" in t:
        return "cert_etica"
    if "formador" in t or "instructor" in t or "docente" in t:
        return "cert_formador"
    if "evalu" in t:
        return "cert_evaluacion"
    if "investiga" in t:
        return "cert_investigacion"
    if "enfermer" in t or "cuidados" in t:
        return "cert_cuidados_enf"
    return None


def _buscar_rol_cert(guild: discord.Guild, clave: str) -> Optional[discord.Role]:
    certs = certificados_dict()
    if clave not in certs:
        return None
    nombre = certs[clave][0]
    try:
        import roles_store

        rid = roles_store.obtener_extra(f"otorgado_{clave}")
        if rid:
            r = guild.get_role(int(rid))
            if r:
                return r
    except Exception:
        pass
    for r in guild.roles:
        if r.name == nombre:
            return r
    nl = nombre.lower()
    for r in guild.roles:
        if (r.name or "").lower() == nl or nl in (r.name or "").lower():
            return r
    return None


async def otorgar_rol_certificado(
    member: discord.Member,
    clave_o_tipo: str,
    *,
    reason: str = "Certificación completada",
) -> Tuple[bool, str]:
    """Otorga el rol de la certificación que tomó el miembro."""
    clave = resolver_clave_cert(clave_o_tipo) or (
        clave_o_tipo if clave_o_tipo in certificados_dict() else None
    )
    if not clave:
        return False, f"Sin rol mapeado para `{clave_o_tipo}`"

    certs = certificados_dict()
    if clave not in certs:
        return False, f"Clave desconocida `{clave}`"

    rol = _buscar_rol_cert(member.guild, clave)
    if not rol:
        nombre, color = certs[clave]
        try:
            hex_c = (color or "#9B59B6").lstrip("#")
            try:
                colour = discord.Colour(int(hex_c, 16))
            except Exception:
                colour = discord.Colour.purple()
            rol = await member.guild.create_role(
                name=nombre,
                colour=colour,
                permissions=discord.Permissions.none(),
                reason="Rol de certificación",
            )
            try:
                import roles_store

                roles_store.guardar_extra(f"otorgado_{clave}", rol.id)
            except Exception:
                pass
        except Exception as e:
            return False, f"No se pudo crear el rol: {e}"

    if rol in member.roles:
        return True, f"Ya tenía **{rol.name}**"
    try:
        await member.add_roles(rol, reason=reason)
        return True, f"Rol otorgado: **{rol.name}**"
    except Exception as e:
        return False, f"Error al otorgar {rol.name}: {e}"


async def otorgar_por_certificacion(
    member: discord.Member,
    *,
    tipo: str = "",
    titulo: str = "",
    reason: str = "Certificación completada",
) -> Tuple[bool, str]:
    """Resuelve tipo/título de la certificación tomada y otorga su rol."""
    clave = resolver_clave_cert(tipo) or resolver_clave_cert(titulo)
    if not clave:
        return False, "No se pudo identificar el rol de esta certificación"
    return await otorgar_rol_certificado(member, clave, reason=reason)


def registrar(bot: commands.Bot) -> None:
    for name in ("otorgar_rol_certificado",):
        try:
            bot.tree.remove_command(name)
        except Exception:
            pass

    choices = choices_certificados()
    if not choices:
        print("[cert_roles] sin CERTIFICADOS")
        return

    @bot.tree.command(
        name="otorgar_rol_certificado",
        description="[Docencia] Otorga el rol de una certificación del organigrama",
    )
    @app_commands.describe(miembro="Beneficiario", certificado="Certificación / rol")
    @app_commands.choices(certificado=choices)
    async def otorgar_cmd(
        inter: discord.Interaction,
        miembro: discord.Member,
        certificado: app_commands.Choice[str],
    ):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        ok_perm = inter.user.guild_permissions.manage_roles
        try:
            import permisos

            ok_perm = ok_perm or permisos.member_tiene_alguna_key(
                inter.user,
                "DIR_DOCENCIA",
                "DIRECTOR_DOCENCIA",
                "FUNDADOR_OWNER",
                "CO_OWNER",
                "OWNER",
                "CANCILLER",
            )
        except Exception:
            pass
        if not ok_perm:
            return await inter.response.send_message(
                "❌ Solo Docencia / dirección.", ephemeral=True
            )

        ok, msg = await otorgar_rol_certificado(
            miembro, certificado.value, reason=f"Certificación por {inter.user}"
        )
        await inter.response.send_message(
            embed=discord.Embed(
                title="🎓 Rol de certificación",
                description=f"{miembro.mention}\n{msg}",
                color=0x2ECC71 if ok else 0xE74C3C,
            ),
            ephemeral=True,
        )

    print("[cert_roles] OK — rol al certificarse")
