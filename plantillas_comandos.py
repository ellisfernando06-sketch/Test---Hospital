# -*- coding: utf-8 -*
"""plantillas_comandos.py — Una plantilla funcional por comando/módulo."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

import discord

import config

C = {
    "finanzas": 0xF1C40F,
    "sancion": 0xED4245,
    "info": 0x3498DB,
    "exito": 0x2ECC71,
    "aviso": 0xF39C12,
    "medico": 0x1ABC9C,
    "docencia": 0x8E44AD,
    "logistica": 0xE67E22,
    "dark": 0x2C3E50,
}


def _footer(modulo: str) -> str:
    return f"{getattr(config, 'NOMBRE_HOSPITAL', 'Hospital General')}  ·  {modulo}"


def _ts(embed: discord.Embed) -> discord.Embed:
    embed.timestamp = datetime.now(timezone.utc)
    return embed


class PlantillaBalance:
    MOD = "Balance personal"

    @staticmethod
    def principal(usuario, saldo: float, movimientos: List[dict]) -> discord.Embed:
        emb = discord.Embed(
            title=f"💰 Balance · {getattr(usuario, 'display_name', usuario)}",
            description=f"### Saldo disponible\n# `${saldo:,.2f}`",
            color=C["finanzas"],
        )
        if movimientos:
            lineas = []
            for m in movimientos[:5]:
                tipo = m.get("tipo", "?")
                monto = float(m.get("monto") or 0)
                signo = "+" if tipo in ("deposito", "ingreso", "transferencia_in") else "−"
                fecha = str(m.get("fecha") or "")[:10]
                lineas.append(f"`{fecha}` {signo}${monto:,.2f} · {tipo}")
            emb.add_field(name="Últimos movimientos", value="\n".join(lineas), inline=False)
        else:
            emb.add_field(name="Últimos movimientos", value="_Sin movimientos recientes_", inline=False)
        emb.set_footer(text=_footer(PlantillaBalance.MOD))
        return _ts(emb)


class PlantillaBalanceGeneral:
    MOD = "Balance general"

    @staticmethod
    def principal(resumen: dict) -> discord.Embed:
        emb = discord.Embed(
            title="📊 Balance general del hospital",
            description="Resumen de caja, circulación y actividad financiera.",
            color=C["finanzas"],
        )
        emb.add_field(
            name="💵 En circulación",
            value=f"`${float(resumen.get('total_en_circulacion') or 0):,.2f}`",
            inline=True,
        )
        emb.add_field(
            name="👤 Cuentas activas",
            value=str(resumen.get("cuentas_activas") or 0),
            inline=True,
        )
        movs = resumen.get("ultimos") or resumen.get("movimientos") or []
        if movs:
            lineas = []
            for m in movs[:8]:
                lineas.append(
                    f"`{str(m.get('fecha', ''))[:10]}` **{m.get('tipo', '?')}** "
                    f"${float(m.get('monto') or 0):,.2f}"
                )
            emb.add_field(name="Pagos y acciones financieras", value="\n".join(lineas), inline=False)
        emb.set_footer(text=_footer(PlantillaBalanceGeneral.MOD))
        return _ts(emb)


class PlantillaHistorialFinanciero:
    MOD = "Historial financiero"

    @staticmethod
    def principal(usuario, movimientos: List[dict]) -> discord.Embed:
        emb = discord.Embed(
            title=f"📜 Historial financiero · {getattr(usuario, 'display_name', usuario)}",
            description="Movimientos del más reciente al más antiguo.",
            color=C["finanzas"],
        )
        if not movimientos:
            emb.description = "No hay movimientos registrados."
        else:
            for i, m in enumerate(movimientos[:12], 1):
                emb.add_field(
                    name=f"{i}. {str(m.get('tipo', 'mov')).upper()}",
                    value=(
                        f"**${float(m.get('monto') or 0):,.2f}**\n"
                        f"{m.get('motivo') or '—'}\n"
                        f"`{str(m.get('fecha', ''))[:16]}`"
                    ),
                    inline=True,
                )
        emb.set_footer(text=_footer(PlantillaHistorialFinanciero.MOD))
        return _ts(emb)


class PlantillaAnuncio:
    MOD = "Anuncios oficiales"

    @staticmethod
    def publicar(titulo: str, cuerpo: str, autor) -> discord.Embed:
        emb = discord.Embed(title=f"📢 {titulo}", description=cuerpo, color=C["dark"])
        emb.set_author(
            name=f"Publicado por {getattr(autor, 'display_name', autor)}",
            icon_url=getattr(getattr(autor, "display_avatar", None), "url", None),
        )
        emb.set_footer(text=_footer(PlantillaAnuncio.MOD))
        return _ts(emb)


class PlantillaTarea:
    MOD = "Gestión de tareas"

    @staticmethod
    def asignacion(asignado, asignador, titulo: str, detalle: str, plazo: str = "") -> discord.Embed:
        emb = discord.Embed(
            title=f"📋 Nueva tarea · {titulo}",
            description=detalle or "_Sin detalle adicional_",
            color=C["info"],
        )
        emb.add_field(name="Asignado a", value=getattr(asignado, "mention", str(asignado)), inline=True)
        emb.add_field(name="Asignada por", value=getattr(asignador, "mention", str(asignador)), inline=True)
        if plazo:
            emb.add_field(name="Plazo", value=plazo, inline=True)
        emb.set_footer(text=_footer(PlantillaTarea.MOD))
        return _ts(emb)

    @staticmethod
    def confirmacion(asignado, titulo: str) -> discord.Embed:
        emb = discord.Embed(
            title="✅ Tarea asignada",
            description=f"Se notificó a {getattr(asignado, 'mention', asignado)}\n**{titulo}**",
            color=C["exito"],
        )
        emb.set_footer(text=_footer(PlantillaTarea.MOD))
        return _ts(emb)


class PlantillaSancion:
    MOD = "Régimen disciplinario"

    @staticmethod
    def registro(sancionado, emisor, tipo: str, motivo: str, abierta: bool, con_apelacion: bool) -> discord.Embed:
        modo = "🔓 Sanción abierta" if abierta else "🔒 Sanción cerrada"
        ape = "✅ Con derecho a apelación" if con_apelacion else "⛔ Sin apelación"
        emb = discord.Embed(title=f"⚖️ Sanción · {tipo}", description=motivo, color=C["sancion"])
        emb.add_field(name="Personal", value=getattr(sancionado, "mention", str(sancionado)), inline=True)
        emb.add_field(name="Emitida por", value=getattr(emisor, "mention", str(emisor)), inline=True)
        emb.add_field(name="Modalidad", value=f"{modo}\n{ape}", inline=False)
        emb.set_footer(text=_footer(PlantillaSancion.MOD))
        return _ts(emb)


class PlantillaBan:
    MOD = "Moderación OOC"

    @staticmethod
    def dm_baneado(motivo: str, staff, guild_name: str) -> discord.Embed:
        emb = discord.Embed(
            title=f"🔨 Has sido baneado de {guild_name}",
            description=(
                f"**Motivo:**\n{motivo or 'No especificado'}\n\n"
                f"Si consideras que es un error, puedes **apelar** con el botón."
            ),
            color=C["sancion"],
        )
        emb.add_field(name="Staff", value=getattr(staff, "display_name", str(staff)), inline=True)
        emb.set_footer(text=_footer(PlantillaBan.MOD))
        return _ts(emb)

    @staticmethod
    def log(staff, usuario, motivo: str) -> discord.Embed:
        emb = discord.Embed(
            title="🔨 Ban aplicado",
            description=f"**Usuario:** {getattr(usuario, 'mention', usuario)}\n**Motivo:** {motivo}",
            color=C["sancion"],
        )
        emb.add_field(name="Por", value=getattr(staff, "mention", str(staff)), inline=True)
        emb.set_footer(text=_footer(PlantillaBan.MOD))
        return _ts(emb)


class PlantillaDespido:
    MOD = "RRHH · Despidos"

    @staticmethod
    def solicitud(objetivo, solicitante, motivo: str, evidencia: str = "") -> discord.Embed:
        emb = discord.Embed(
            title="🚫 Solicitud de despido",
            description=f"**Motivo del despido:**\n{motivo}",
            color=C["sancion"],
        )
        emb.add_field(name="Personal", value=getattr(objetivo, "mention", str(objetivo)), inline=True)
        emb.add_field(name="Solicita", value=getattr(solicitante, "mention", str(solicitante)), inline=True)
        if evidencia:
            emb.add_field(name="Pruebas / evidencia", value=evidencia[:1000], inline=False)
        emb.set_footer(text=_footer(PlantillaDespido.MOD))
        return _ts(emb)


class PlantillaExpediente:
    MOD = "Expediente de personal"

    @staticmethod
    def principal(
        usuario,
        *,
        balance: float = 0.0,
        sanciones: Optional[List[str]] = None,
        licencias: Optional[List[str]] = None,
        notas: Optional[List[str]] = None,
        extra_fields: Optional[Dict[str, str]] = None,
    ) -> discord.Embed:
        emb = discord.Embed(
            title=f"📁 Expediente · {getattr(usuario, 'display_name', usuario)}",
            description="Registro profesional consolidado del personal.",
            color=C["info"],
        )
        emb.add_field(name="💰 Balance", value=f"`${balance:,.2f}`", inline=True)
        if extra_fields:
            for k, v in extra_fields.items():
                emb.add_field(name=k, value=v or "—", inline=True)
        if sanciones:
            emb.add_field(name="⚖️ Sanciones", value="\n".join(sanciones[:8]), inline=False)
        if licencias:
            emb.add_field(name="🗓️ Licencias", value="\n".join(licencias[:5]), inline=False)
        if notas:
            emb.add_field(name="📝 Notas", value="\n".join(notas[:5]), inline=False)
        emb.set_footer(text=_footer(PlantillaExpediente.MOD))
        return _ts(emb)


class PlantillaFicha:
    MOD = "Ficha personal"

    @staticmethod
    def mostrar(usuario, campos: Dict[str, str]) -> discord.Embed:
        emb = discord.Embed(
            title=f"🪪 Ficha · {getattr(usuario, 'display_name', usuario)}",
            color=C["medico"],
        )
        for k, v in campos.items():
            emb.add_field(name=k, value=v or "—", inline=True)
        emb.set_footer(text=_footer(PlantillaFicha.MOD))
        return _ts(emb)


class PlantillaCapacitacion:
    MOD = "Docencia · Capacitaciones"

    @staticmethod
    def historial(usuario, items: List[dict]) -> discord.Embed:
        emb = discord.Embed(
            title=f"🎓 Historial · {getattr(usuario, 'display_name', usuario)}",
            color=C["docencia"],
        )
        if not items:
            emb.description = "Sin capacitaciones registradas."
        else:
            for c in items[:15]:
                emb.add_field(
                    name=c.get("titulo") or "Capacitación",
                    value=f"`{str(c.get('fecha', ''))[:10]}`",
                    inline=True,
                )
        emb.set_footer(text=_footer(PlantillaCapacitacion.MOD))
        return _ts(emb)


class PlantillaBienvenida:
    MOD = "Recepción"

    @staticmethod
    def gift(member: discord.Member, texto: str = "") -> discord.Embed:
        emb = discord.Embed(
            title=f"🎁 Bienvenido/a a {member.guild.name}",
            description=texto or (
                f"Hola {member.mention}:\n"
                f"Gracias por unirte al **{getattr(config, 'NOMBRE_HOSPITAL', 'Hospital')}**.\n"
                f"Revisa las normas, verifica tu cuenta y postúlate cuando estés listo."
            ),
            color=C["exito"],
        )
        av = getattr(getattr(member, "display_avatar", None), "url", None)
        if av:
            emb.set_thumbnail(url=av)
        emb.set_footer(text=_footer(PlantillaBienvenida.MOD))
        return _ts(emb)


class PlantillaInventario:
    MOD = "Inventario"

    @staticmethod
    def lista(items: List[dict]) -> discord.Embed:
        emb = discord.Embed(title="📦 Inventario hospitalario", color=C["logistica"])
        if not items:
            emb.description = "Inventario vacío."
        else:
            for it in items[:15]:
                emb.add_field(
                    name=it.get("nombre") or "?",
                    value=f"x{it.get('cantidad', 0)} · {it.get('categoria') or 'General'}",
                    inline=True,
                )
        emb.set_footer(text=_footer(PlantillaInventario.MOD))
        return _ts(emb)


class PlantillaLogistica:
    MOD = "Logística e insumos"

    @staticmethod
    def solicitud_insumo(solicitante, item: str, cantidad: int, area: str = "", notas: str = "") -> discord.Embed:
        emb = discord.Embed(
            title="🚚 Solicitud de insumo",
            description=f"**Ítem:** {item}\n**Cantidad:** {cantidad}",
            color=C["logistica"],
        )
        emb.add_field(name="Solicita", value=getattr(solicitante, "mention", str(solicitante)), inline=True)
        if area:
            emb.add_field(name="Área", value=area, inline=True)
        if notas:
            emb.add_field(name="Notas", value=notas[:500], inline=False)
        emb.set_footer(text=_footer(PlantillaLogistica.MOD))
        return _ts(emb)


class PlantillaLicencia:
    MOD = "Licencias / permisos"

    @staticmethod
    def solicitud(usuario, desde: str, hasta: str, motivo: str, solicitante) -> discord.Embed:
        emb = discord.Embed(title="🗓️ Solicitud de licencia", description=motivo, color=C["aviso"])
        emb.add_field(name="Personal", value=getattr(usuario, "mention", str(usuario)), inline=True)
        emb.add_field(name="Desde", value=desde, inline=True)
        emb.add_field(name="Hasta", value=hasta, inline=True)
        emb.add_field(name="Solicita aprobación", value=getattr(solicitante, "mention", str(solicitante)), inline=False)
        emb.set_footer(text=_footer(PlantillaLicencia.MOD) + " · Requiere Director competente")
        return _ts(emb)
