"""
roles_setup.py
==============
Crea (o detecta si ya existen por nombre exacto) todos los roles
necesarios en el servidor:
  - Uno por cada key en config.KEYS_NOMBRES.
  - Uno por cada peldaño de escalafón en config.DEPARTAMENTOS.
  - El rol especial de suspensión.

Guarda los IDs resultantes en roles_ids.json a través de
roles_store.py. Se ejecuta con /configurar_roles. No necesita edición.
"""

import discord

import config
import roles_store


def _color(hexstr: str) -> discord.Color:
    return discord.Color(int(hexstr.lstrip("#"), 16))


async def _obtener_o_crear(guild: discord.Guild, nombre: str, color: discord.Color = None) -> discord.Role:
    rol = discord.utils.get(guild.roles, name=nombre)
    if rol:
        return rol
    return await guild.create_role(
        name=nombre,
        color=color or discord.Color.default(),
        mentionable=True,
        reason="Configuración automática del bot de hospital",
    )


async def configurar_todo(guild: discord.Guild) -> list:
    resumen = []

    # 1) Keys generales (jerarquía y direcciones)
    resumen.append("__Keys / Cargos__")
    for key, (nombre, color_hex) in config.KEYS_NOMBRES.items():
        rol = await _obtener_o_crear(guild, nombre, _color(color_hex))
        roles_store.guardar_id_key(key, rol.id)
        resumen.append(f"🔑 **{key}** → {rol.mention} (`{rol.id}`)")

    # 2) Escalafones de cada departamento
    for slug, data in config.DEPARTAMENTOS.items():
        resumen.append(f"\n__{data['nombre']}__")
        for i, nombre_rango in enumerate(data["escalafon_nombres"]):
            rol = await _obtener_o_crear(guild, nombre_rango)
            roles_store.guardar_escalafon_id(slug, i, rol.id)
            resumen.append(f"  {i + 1}. **{nombre_rango}** → {rol.mention} (`{rol.id}`)")

    # 3) Rol especial de suspensión
    rol_susp = await _obtener_o_crear(
        guild, config.ROL_SUSPENDIDO_NOMBRE, _color(config.ROL_SUSPENDIDO_COLOR)
    )
    roles_store.guardar_extra("SUSPENDIDO", rol_susp.id)
    resumen.append(f"\n⛔ Rol de suspensión → {rol_susp.mention} (`{rol_susp.id}`)")

    resumen.append(
        "\n⚠️ Recuerda subir el rol del bot por encima de TODOS estos roles en "
        "Ajustes del servidor → Roles, o el bot no podrá asignarlos/quitarlos."
    )

    return resumen
