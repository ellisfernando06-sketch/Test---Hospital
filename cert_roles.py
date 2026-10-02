# -*- coding: utf-8 -*-
"""
cert_roles.py — Enlaza tipos de certificado con roles de CERTIFICADOS.
Al emitir/obtener un certificado se otorga el rol correspondiente.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import discord
from discord import app_commands
from discord.ext import commands

# Mapeo tipo legacy / alias → clave en roles_config.CERTIFICADOS
TIPO_A_CERT: Dict[str, str] = {
    "rcp": "cert_rcp",
    "bls": "cert_rcp",
    "rcp / bls": "cert_rcp",
    "cert_rcp": "cert_rcp",
    "trauma": "cert_primeros_auxilios",
    "primeros_auxilios": "cert_primeros_auxilios",
    "primeros auxilios": "cert_primeros_auxilios",
    "cert_primeros_auxilios": "cert_primeros_auxilios",
    "bioseguridad": "cert_bioseguridad",
    "cert_bioseguridad": "cert_bioseguridad",
    "atencion_paciente": "cert_atencion_paciente",
    "atención al paciente": "cert_atencion_paciente",
    "cert_atencion_paciente": "cert_atencion_paciente",
    "etica": "cert_etica",
    "ética hospitalaria": "cert_etica",
    "cert_etica": "cert_etica",
    "formador": "cert_formador",
    "docente": "cert_formador",
    "instructor": "cert_formador",
    "cert_formador": "cert_formador",
    "evaluacion": "cert_evaluacion",
    "cert_evaluacion": "cert_evaluacion",
    "investigacion": "cert_investigacion",
    "cert_investigacion": "cert_investigacion",
    "enfermeria": "cert_cuidados_enf",
    "cuidados_enf": "cert_cuidados_enf",
    "cuidados de enfermería": "cert_cuidados_enf",
    "cert_cuidados_enf": "cert_cuidados_enf",
    "medicacion": "cert_atencion_paciente",
    "quirurgico": "cert_bioseguridad",
    "emergencias": "cert_primeros_auxilios",
}


def certificados_dict() -> Dict[str, Tuple[str, str]]:
    try:
        import roles_config

        return dict(getattr(roles_config, "CERTIFICADOS", {}) or {})
    except Exception:
        return {}


def choices_certificados() -> List[app_commands.Choice[str]]:
    """Choices para slash commands (máx 25)."""
    out: List[app_commands.Choice[str]] = []
    for clave, (nombre, _col) in certificados_dict().items():
        label = nombre if len(nombre) <= 100 else nombre[:97] + "…"
        out.append(app_commands.Choice(name=label, value=clave))
    return out[:25]


def resolver_clave_cert(tipo_o_titulo: str) -> Optional[str]:
    if not tipo_o_titulo:
        return None
    t = tipo_o_titulo.strip().lower()
    if t in TIPO_A_CERT:
        return TIPO_A_CERT[t]
    # match por nombre de rol
    for clave, (nombre, _) in certificados_dict().items():
        nl = nombre.lower()
        if t == clave.lower() or t in nl or nl in t:
            return clave
        # sin emoji
        plain = "".join(c for c in nl if c.isalnum() or c.isspace())
        if t in plain or plain in t:
            return clave
    return TIPO_A_CERT.get(t)


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
    reason: str = "Certificado RP otorgado",
) -> Tuple[bool, str]:
    """
    Otorga el rol de certificado. Devuelve (ok, mensaje).
    """
    clave = resolver_clave_cert(clave_o_tipo) or clave_o_tipo
    certs = certificados_dict()
    if clave not in certs:
        return False, f"No hay rol mapeado para `{clave_o_tipo}`"

    rol = _buscar_rol_cert(member.guild, clave)
    if not rol:
        # crear si falta
        nombre, color = certs[clave]
        try:
            import roles_setup

            # create via guild
            hex_c = (color or "#9B59B6").lstrip("#")
            try:
                colour = discord.Colour(int(hex_c, 16))
            except Exception:
                colour = discord.Colour.purple()
            rol = await member.guild.create_role(
                name=nombre,
                colour=colour,
                permissions=discord.Permissions.none(),
                reason="Rol de certificado",
            )
            try:
                import roles_store

                roles_store.guardar_extra(f"otorgado_{clave}", rol.id)
            except Exception:
                pass
        except Exception as e:
            return False, f"No se encontró/creó el rol: {e}"

    if rol in member.roles:
        return True, f"Ya tenía {rol.mention}"
    try:
        await member.add_roles(rol, reason=reason)
        return True, f"+ {rol.mention}"
    except Exception as e:
        return False, f"Sin permiso para dar {rol.name}: {e}"


def registrar(bot: commands.Bot) -> None:
    """Comando auxiliar: otorgar rol de cert a mano + choices visibles."""
    for name in ("otorgar_rol_certificado",):
        try:
            bot.tree.remove_command(name)
        except Exception:
            pass

    choices = choices_certificados()
    if not choices:
        print("[cert_roles] sin CERTIFICADOS en roles_config")
        return

    @bot.tree.command(
        name="otorgar_rol_certificado",
        description="[Docencia] Otorga un rol de certificado del organigrama",
    )
    @app_commands.describe(
        miembro="Quien recibe el rol",
        certificado="Certificado del organigrama",
    )
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
            miembro,
            certificado.value,
            reason=f"Certificado por {inter.user}",
        )
        color = 0x2ECC71 if ok else 0xE74C3C
        await inter.response.send_message(
            embed=discord.Embed(
                title="🎓 Rol de certificado",
                description=f"**Miembro:** {miembro.mention}\n**Resultado:** {msg}",
                color=color,
            ),
            ephemeral=True,
        )

    print("[cert_roles] OK — roles de certificado enlazados")
