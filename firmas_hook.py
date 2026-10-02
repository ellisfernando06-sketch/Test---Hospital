# -*- coding: utf-8 -*-
"""Hook: reescribe solicitar_autorizacion_certificado para canal de dirección + DM."""
from __future__ import annotations

def aplicar():
    try:
        import firmas
    except Exception as e:
        print("[firmas_hook] no firmas:", e)
        return
    if getattr(firmas, "_hook_canales", False):
        return

    import discord
    from firmas import (
        nueva_autorizacion,
        VistaAutorizarEncargado,
        VistaAutorizarDocencia,
        VistaAutorizarDirectorZona,
        KEY_DOCENCIA,
    )

    async def solicitar_autorizacion_certificado(
        bot, inter, *, receptor, certificacion, cedula="", descripcion="", departamento="", firma_encargado_file=None,
    ) -> int:
        num = "CERT-PEND"
        try:
            import docencia as _doc
            reg_d = _doc.emitir(
                receptor.id, certificacion.get("nombre"), "personalizado", descripcion,
                inter.user.id, notas="pendiente autorización triple", departamento=departamento,
            )
            num = "CERT-%05d" % int(reg_d.get("id") or 0)
        except Exception as e:
            print("[firmas] docencia.emitir:", e)

        director_zona_key = certificacion.get("director_zona_key", "DIRECTOR_ADMINISTRATIVO")
        aid = nueva_autorizacion({
            "tipo": "certificado",
            "key_docencia": KEY_DOCENCIA,
            "key_director_zona": director_zona_key,
            "receptor_id": receptor.id,
            "nombre_receptor": getattr(receptor, "display_name", str(receptor)),
            "capacitacion": certificacion.get("nombre", "Certificación"),
            "descripcion": descripcion,
            "departamento": departamento,
            "cedula": cedula,
            "certificacion_id": certificacion.get("id"),
            "encargado_id": inter.user.id,
            "encargado_nombre": getattr(inter.user, "display_name", str(inter.user)),
            "firma_encargado": firma_encargado_file,
            "canal_id": inter.channel.id if inter.channel else None,
            "numero": num,
        })

        emb1 = discord.Embed(
            title="Certificado #%s — Confirmación del Encargado" % aid,
            description=(
                "**Graduado:** %s\n**Certificación:** %s\n**ID:** %s\n**N.:** `%s`\n\n"
                "Confirma que el estudiante completó la certificación."
            ) % (receptor.mention, certificacion.get("nombre", "Certificación"), cedula, num),
            color=0xF39C12,
            timestamp=discord.utils.utcnow(),
        )
        emb2 = discord.Embed(
            title="Certificado #%s — Firma Docencia" % aid,
            description=(
                "**Graduado:** %s\n**Certificación:** %s\n**N.:** `%s`\n\n"
                "Firma requerida: **Director de Docencia**."
            ) % (receptor.mention, certificacion.get("nombre", "Certificación"), num),
            color=0x8E44AD,
            timestamp=discord.utils.utcnow(),
        )
        emb3 = discord.Embed(
            title="Certificado #%s — Director de zona" % aid,
            description=(
                "**Graduado:** %s\n**Certificación:** %s\n**N.:** `%s`\n\n"
                "Firma requerida: **Director de zona** (`%s`)."
            ) % (receptor.mention, certificacion.get("nombre", "Certificación"), num, director_zona_key),
            color=0x2980B9,
            timestamp=discord.utils.utcnow(),
        )
        view1 = VistaAutorizarEncargado(bot, aid)
        view2 = VistaAutorizarDocencia(bot, aid)
        view3 = VistaAutorizarDirectorZona(bot, aid, director_zona_key)

        try:
            await inter.followup.send(embed=emb1, view=view1)
        except Exception:
            if inter.channel:
                await inter.channel.send(embed=emb1, view=view1)

        guild = inter.guild
        if guild:
            try:
                import canales_direccion as _cd
                await _cd.enviar_solicitud_area(
                    bot, guild, area="docencia", embed=emb2, view=view2,
                    content="📚 Firma requerida · Director de Docencia",
                )
                zk = (director_zona_key or "").upper()
                area_zona = "general"
                if "MEDICO" in zk:
                    area_zona = "medico"
                elif "ENFERM" in zk:
                    area_zona = "enfermeria"
                elif "RRHH" in zk:
                    area_zona = "rrhh"
                elif "LOGIST" in zk:
                    area_zona = "logistica"
                elif "SEGUR" in zk:
                    area_zona = "seguridad"
                await _cd.enviar_solicitud_area(
                    bot, guild, area=area_zona, embed=emb3, view=view3,
                    content="🖋️ Firma requerida · Director de zona",
                )
            except Exception as e:
                print("[firmas_hook] envío:", e)
                if inter.channel:
                    await inter.channel.send(embed=emb2, view=view2)
                    await inter.channel.send(embed=emb3, view=view3)
        return aid

    firmas.solicitar_autorizacion_certificado = solicitar_autorizacion_certificado
    firmas._hook_canales = True
    print("[firmas_hook] OK — certificados a canal/DM de dirección", flush=True)


def registrar(bot):
    aplicar()
