# -*- coding: utf-8 -*-
"""Al emitir certificado (docencia/firmas), otorga el rol CERTIFICADOS correspondiente."""
from __future__ import annotations


def aplicar_docencia():
    try:
        import docencia
    except Exception as e:
        print("[cert_roles_hook] no docencia:", e)
        return

    if getattr(docencia, "_cert_roles_hook", False):
        return

    # Parchear Modal on_submit si existe CertificadoModal / similar
    for attr in dir(docencia):
        obj = getattr(docencia, attr, None)
        if not isinstance(obj, type):
            continue
        if not hasattr(obj, "on_submit"):
            continue
        # solo modales de certificado
        name = attr.lower()
        if "cert" not in name and "modal" not in name:
            continue
        orig = obj.on_submit

        async def _wrapped(self, inter, _orig=orig):
            await _orig(self, inter)
            try:
                import cert_roles

                tipo = getattr(self, "tipo", None) or ""
                titulo = ""
                try:
                    titulo = str(getattr(self, "titulo", "") or "")
                    if hasattr(titulo, "value"):
                        titulo = str(titulo.value)
                except Exception:
                    pass
                member = getattr(self, "usuario", None)
                if member and inter.guild:
                    clave = cert_roles.resolver_clave_cert(tipo) or cert_roles.resolver_clave_cert(titulo)
                    if clave:
                        ok, msg = await cert_roles.otorgar_rol_certificado(
                            member, clave, reason="Certificado emitido (docencia)"
                        )
                        print(f"[cert_roles_hook] {member}: {msg}", flush=True)
                        try:
                            await inter.followup.send(
                                f"🎓 Rol de certificado: {msg}", ephemeral=True
                            )
                        except Exception:
                            pass
            except Exception as e:
                print("[cert_roles_hook] docencia grant:", e)

        obj.on_submit = _wrapped
        print(f"[cert_roles_hook] parche modal {attr}")

    docencia._cert_roles_hook = True


def aplicar_firmas():
    try:
        import firmas
    except Exception:
        return
    if getattr(firmas, "_cert_roles_hook", False):
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
            cap = reg.get("capacitacion") or reg.get("titulo") or ""
            tipo = reg.get("tipo_cert") or reg.get("certificacion_id") or ""
            clave = cert_roles.resolver_clave_cert(str(tipo)) or cert_roles.resolver_clave_cert(str(cap))
            if not clave:
                return
            ok, msg = await cert_roles.otorgar_rol_certificado(
                member, clave, reason="Certificado autorizado (triple firma)"
            )
            print(f"[cert_roles_hook] firmas {member}: {msg}", flush=True)
            try:
                await inter.followup.send(f"🎓 Rol de certificado: {msg}", ephemeral=True)
            except Exception:
                pass
        except Exception as e:
            print("[cert_roles_hook] firmas grant:", e)

    firmas._emitir_certificado_autorizado = _wrapped
    firmas._cert_roles_hook = True
    print("[cert_roles_hook] firmas._emitir_certificado_autorizado parcheado")


def registrar(bot):
    aplicar_docencia()
    aplicar_firmas()
    try:
        import cert_roles

        cert_roles.registrar(bot)
    except Exception as e:
        print("[cert_roles_hook] cert_roles.registrar:", e)
