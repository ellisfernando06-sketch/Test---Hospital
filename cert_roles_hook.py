# -*- coding: utf-8 -*-
"""
Al completarse una certificación (docencia / firmas / capacitaciones),
otorga automáticamente el rol CERTIFICADOS de esa certificación.
"""
from __future__ import annotations


def _grant_async_safe(coro):
    """Programa una corrutina en el loop del bot si hace falta."""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.ensure_future(coro)
        return loop.run_until_complete(coro)
    except Exception:
        return None


def aplicar_docencia():
    try:
        import docencia
    except Exception as e:
        print("[cert_roles_hook] no docencia:", e)
        return

    if getattr(docencia, "_cert_roles_hook_v2", False):
        return

    # 1) Envolver emitir (síncrono) para anotar clave
    if hasattr(docencia, "emitir"):
        _orig_emitir = docencia.emitir

        def emitir_wrapped(uid, titulo, tipo="personalizado", descripcion="", emitido_por=0, **kwargs):
            reg = _orig_emitir(
                uid, titulo, tipo=tipo, descripcion=descripcion, emitido_por=emitido_por, **kwargs
            )
            try:
                import cert_roles

                clave = cert_roles.resolver_clave_cert(tipo) or cert_roles.resolver_clave_cert(
                    titulo
                )
                if isinstance(reg, dict) and clave:
                    reg["clave_cert"] = clave
            except Exception:
                pass
            return reg

        docencia.emitir = emitir_wrapped
        print("[cert_roles_hook] docencia.emitir envuelto")

    # 2) Modal de emisión: al terminar, otorgar rol al usuario certificado
    for attr in dir(docencia):
        obj = getattr(docencia, attr, None)
        if not isinstance(obj, type) or not hasattr(obj, "on_submit"):
            continue
        name = attr.lower()
        if "modal" not in name and "cert" not in name:
            continue

        orig = obj.on_submit

        async def _on_submit_wrapped(self, inter, _orig=orig):
            await _orig(self, inter)
            try:
                import cert_roles

                member = getattr(self, "usuario", None)
                tipo = getattr(self, "tipo", "") or ""
                titulo = ""
                try:
                    t = getattr(self, "titulo", None)
                    titulo = str(getattr(t, "value", t) or "")
                except Exception:
                    pass
                if not member or not inter.guild:
                    return
                ok, msg = await cert_roles.otorgar_por_certificacion(
                    member,
                    tipo=tipo,
                    titulo=titulo,
                    reason="Certificación emitida (docencia)",
                )
                print(f"[cert_roles_hook] docencia → {member}: {msg}", flush=True)
                try:
                    await inter.followup.send(
                        f"🎓 Al certificarse se otorgó el rol:\n{msg}",
                        ephemeral=True,
                    )
                except Exception:
                    try:
                        await inter.channel.send(
                            f"🎓 {member.mention} — {msg}"
                        )
                    except Exception:
                        pass
            except Exception as e:
                print("[cert_roles_hook] grant docencia:", e)

        obj.on_submit = _on_submit_wrapped
        print(f"[cert_roles_hook] modal {attr} → otorga rol al certificarse")

    docencia._cert_roles_hook_v2 = True


def aplicar_firmas():
    try:
        import firmas
    except Exception:
        return
    if getattr(firmas, "_cert_roles_hook_v2", False):
        return

    orig = getattr(firmas, "_emitir_certificado_autorizado", None)
    if not callable(orig):
        return

    async def _wrapped(bot, inter, reg):
        await orig(bot, inter, reg)
        try:
            import cert_roles

            uid = int(reg.get("receptor_id") or 0)
            member = inter.guild.get_member(uid) if inter.guild else None
            if not member:
                return
            tipo = str(
                reg.get("clave_cert")
                or reg.get("tipo_cert")
                or reg.get("certificacion_id")
                or ""
            )
            titulo = str(reg.get("capacitacion") or reg.get("titulo") or "")
            ok, msg = await cert_roles.otorgar_por_certificacion(
                member,
                tipo=tipo,
                titulo=titulo,
                reason="Certificación autorizada (firmas)",
            )
            print(f"[cert_roles_hook] firmas → {member}: {msg}", flush=True)
            try:
                await inter.followup.send(
                    f"🎓 Rol de la certificación: {msg}", ephemeral=True
                )
            except Exception:
                pass
        except Exception as e:
            print("[cert_roles_hook] firmas grant:", e)

    firmas._emitir_certificado_autorizado = _wrapped
    firmas._cert_roles_hook_v2 = True
    print("[cert_roles_hook] firmas → rol al autorizar certificado")


def aplicar_capacitaciones():
    try:
        import capacitaciones
    except Exception:
        return
    if getattr(capacitaciones, "_cert_roles_hook_v2", False):
        return
    if not hasattr(capacitaciones, "certificar"):
        return

    _orig = capacitaciones.certificar

    def certificar_wrapped(uid, titulo, emitido_por=0, *a, **kw):
        out = _orig(uid, titulo, emitido_por, *a, **kw)
        # rol se otorga en flujos async; aquí solo dejamos rastro
        try:
            import cert_roles

            clave = cert_roles.resolver_clave_cert(str(titulo))
            if isinstance(out, dict) and clave:
                out["clave_cert"] = clave
        except Exception:
            pass
        return out

    capacitaciones.certificar = certificar_wrapped
    capacitaciones._cert_roles_hook_v2 = True
    print("[cert_roles_hook] capacitaciones.certificar anotado")


def registrar(bot):
    aplicar_docencia()
    aplicar_firmas()
    aplicar_capacitaciones()
    try:
        import cert_roles

        cert_roles.registrar(bot)
    except Exception as e:
        print("[cert_roles_hook] cert_roles:", e)

    # Listener: si algún sistema emite y deja clave en un evento custom, no aplica.
    # Asegurar que crear_certificado del tree use tipos mapeados.
    print("[cert_roles_hook] OK — al certificarse se otorga el rol de esa certificación")
