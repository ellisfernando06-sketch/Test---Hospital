# -*- coding: utf-8 -*-
"""cert_roles.py — Certificación tomada → rol CERTIFICADOS automático."""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import discord
from discord import app_commands
from discord.ext import commands

TIPO_A_CERT: Dict[str, str] = {
    "cert_rcp": "cert_rcp",
    "cert_rcp_avanzado": "cert_rcp_avanzado",
    "cert_primeros_auxilios": "cert_primeros_auxilios",
    "cert_soporte_vital": "cert_soporte_vital",
    "cert_trauma": "cert_trauma",
    "cert_emergencias": "cert_emergencias",
    "cert_bioseguridad": "cert_bioseguridad",
    "cert_atencion_paciente": "cert_atencion_paciente",
    "cert_medicacion": "cert_medicacion",
    "cert_via_aerea": "cert_via_aerea",
    "cert_venopuncion": "cert_venopuncion",
    "cert_electrocardiografia": "cert_electrocardiografia",
    "cert_quirurgico": "cert_quirurgico",
    "cert_uci": "cert_uci",
    "cert_pediatria": "cert_pediatria",
    "cert_obstetricia": "cert_obstetricia",
    "cert_cuidados_enf": "cert_cuidados_enf",
    "cert_curaciones": "cert_curaciones",
    "cert_movilizacion": "cert_movilizacion",
    "cert_toma_muestras": "cert_toma_muestras",
    "cert_etica": "cert_etica",
    "cert_formador": "cert_formador",
    "cert_evaluacion": "cert_evaluacion",
    "cert_investigacion": "cert_investigacion",
    "cert_comunicacion": "cert_comunicacion",
    "cert_trabajo_equipo": "cert_trabajo_equipo",
    "cert_evacuacion": "cert_evacuacion",
    "cert_radioproteccion": "cert_radioproteccion",
    "cert_triage": "cert_triage",
    # aliases docencia / texto
    "rcp": "cert_rcp",
    "bls": "cert_soporte_vital",
    "acls": "cert_rcp_avanzado",
    "rcp avanzado": "cert_rcp_avanzado",
    "trauma": "cert_trauma",
    "primeros_auxilios": "cert_primeros_auxilios",
    "primeros auxilios": "cert_primeros_auxilios",
    "emergencias": "cert_emergencias",
    "medicacion": "cert_medicacion",
    "medicación": "cert_medicacion",
    "quirurgico": "cert_quirurgico",
    "quirúrgico": "cert_quirurgico",
    "enfermeria": "cert_cuidados_enf",
    "enfermería": "cert_cuidados_enf",
    "docente": "cert_formador",
    "instructor": "cert_formador",
    "formador": "cert_formador",
    "bioseguridad": "cert_bioseguridad",
    "triage": "cert_triage",
    "uci": "cert_uci",
    "pediatria": "cert_pediatria",
    "pediatría": "cert_pediatria",
    "obstetricia": "cert_obstetricia",
    "via aerea": "cert_via_aerea",
    "vía aérea": "cert_via_aerea",
    "venopuncion": "cert_venopuncion",
    "ecg": "cert_electrocardiografia",
    "electrocardi": "cert_electrocardiografia",
}


def certificados_dict() -> Dict[str, Tuple[str, str]]:
    try:
        import roles_config

        return dict(getattr(roles_config, "CERTIFICADOS", {}) or {})
    except Exception:
        return {}


def choices_certificados() -> List[app_commands.Choice[str]]:
    """Discord permite máx. 25 choices."""
    out: List[app_commands.Choice[str]] = []
    for clave, (nombre, _col) in certificados_dict().items():
        label = nombre if len(nombre) <= 100 else nombre[:97] + "…"
        out.append(app_commands.Choice(name=label, value=clave))
        if len(out) >= 25:
            break
    return out


def resolver_clave_cert(tipo_o_titulo: str) -> Optional[str]:
    if not tipo_o_titulo:
        return None
    t = str(tipo_o_titulo).strip().lower()
    if t in TIPO_A_CERT:
        return TIPO_A_CERT[t]
    for clave, (nombre, _) in certificados_dict().items():
        nl = nombre.lower()
        if t == clave.lower() or t in nl or nl in t:
            return clave
    # keywords
    checks = [
        (("acls", "rcp avanzado"), "cert_rcp_avanzado"),
        (("rcp",), "cert_rcp"),
        (("bls", "soporte vital"), "cert_soporte_vital"),
        (("trauma",), "cert_trauma"),
        (("primeros",), "cert_primeros_auxilios"),
        (("emergencia", "código", "codigo"), "cert_emergencias"),
        (("biosegur",), "cert_bioseguridad"),
        (("medic",), "cert_medicacion"),
        (("paciente",), "cert_atencion_paciente"),
        (("vía aérea", "via aerea", "aerea"), "cert_via_aerea"),
        (("venop", "vascular"), "cert_venopuncion"),
        (("electro", "ecg"), "cert_electrocardiografia"),
        (("quirurg",), "cert_quirurgico"),
        (("uci", "intensivo"), "cert_uci"),
        (("pediatr",), "cert_pediatria"),
        (("obstetr", "parto"), "cert_obstetricia"),
        (("curacion", "herida"), "cert_curaciones"),
        (("moviliz",), "cert_movilizacion"),
        (("muestra", "laboratorio"), "cert_toma_muestras"),
        (("enfermer", "cuidados de enf"), "cert_cuidados_enf"),
        (("etic", "ética"), "cert_etica"),
        (("formador", "instructor", "docente"), "cert_formador"),
        (("evalu",), "cert_evaluacion"),
        (("investiga",), "cert_investigacion"),
        (("comunic",), "cert_comunicacion"),
        (("equipo",), "cert_trabajo_equipo"),
        (("evacu",), "cert_evacuacion"),
        (("radio",), "cert_radioproteccion"),
        (("triage",), "cert_triage"),
    ]
    for keys, clave in checks:
        if any(k in t for k in keys):
            return clave
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
    clave = resolver_clave_cert(clave_o_tipo) or (
        clave_o_tipo if clave_o_tipo in certificados_dict() else None
    )
    if not clave:
        return False, f"Sin rol para `{clave_o_tipo}`"
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
        return False, f"Error: {e}"


async def otorgar_por_certificacion(
    member: discord.Member,
    *,
    tipo: str = "",
    titulo: str = "",
    reason: str = "Certificación completada",
) -> Tuple[bool, str]:
    clave = resolver_clave_cert(tipo) or resolver_clave_cert(titulo)
    if not clave:
        return False, "No se identificó el rol de esta certificación"
    return await otorgar_rol_certificado(member, clave, reason=reason)


def registrar(bot: commands.Bot) -> None:
    for name in ("otorgar_rol_certificado",):
        try:
            bot.tree.remove_command(name)
        except Exception:
            pass
    choices = choices_certificados()
    if not choices:
        return

    @bot.tree.command(
        name="otorgar_rol_certificado",
        description="[Docencia] Otorga el rol de una certificación",
    )
    @app_commands.describe(miembro="Beneficiario", certificado="Certificación")
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
                "❌ Solo Docencia.", ephemeral=True
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

    print(f"[cert_roles] OK — {len(certificados_dict())} certificaciones")
