# -*- coding: utf-8 -*-
"""
cert_dg_fix.py
================
Director General NO puede firmar certificaciones por el solo hecho de ser DG.
Solo firma si tiene el rol/key concreto de esa firma (Docencia, Ala, Encargado).
OWNER / CO_OWNER sí pueden firmar las 3 (control del sistema).
"""
from __future__ import annotations

from typing import Set

import discord
from discord.ext import commands


def registrar(bot: commands.Bot) -> None:
    try:
        import cert_flujo_interno as C
    except Exception as e:
        print("[cert_dg_fix] no disponible:", e)
        return

    KEY_DOC = getattr(C, "KEY_DOC", "DIRECTOR_DOCENCIA")
    KEY_ENC = getattr(C, "KEY_ENC", "ENCARGADO")

    def _member_keys(member: discord.Member) -> Set[str]:
        out: Set[str] = set()
        if not isinstance(member, discord.Member):
            return out
        permisos = getattr(C, "permisos", None)
        roles_store = getattr(C, "roles_store", None)
        try:
            import config as cfg
        except Exception:
            cfg = None

        if permisos:
            for key in (
                "OWNER",
                "CO_OWNER",
                "DIRECTOR_GENERAL",
                KEY_DOC,
                KEY_ENC,
                "ENCARGADO_AREA",
                "JEFE_DEPARTAMENTO",
                "SUPERVISOR",
                "DIRECTOR_MEDICO",
                "DIRECTOR_ENFERMERIA",
                "DIRECTOR_ADMINISTRATIVO",
                "DIRECTOR_RRHH",
                "DIRECTOR_LOGISTICA",
                "DIRECTOR_FINANCIERO",
                "DIRECTOR_SEGURIDAD",
                "DIRECTOR_DISCIPLINA",
            ):
                try:
                    if permisos.member_tiene_alguna_key(member, key):
                        out.add(key)
                except Exception:
                    pass
            if cfg:
                try:
                    for key in list(getattr(cfg, "KEYS_NOMBRES", {}) or {}):
                        if permisos.member_tiene_alguna_key(member, key):
                            out.add(key)
                except Exception:
                    pass

        if roles_store and cfg:
            try:
                for key in list(getattr(cfg, "KEYS_NOMBRES", {}) or {}):
                    rid = roles_store.obtener_id_key(key)
                    if not rid:
                        continue
                    rol = member.guild.get_role(rid)
                    if rol and rol in member.roles:
                        out.add(key)
            except Exception:
                pass
        return out

    def _roles_firma_para(member: discord.Member, reg: dict) -> Set[str]:
        keys = _member_keys(member)
        puede: Set[str] = set()

        # Solo OWNER / CO_OWNER bypass — NO Director General
        if "OWNER" in keys or "CO_OWNER" in keys:
            return {"encargado", "docencia", "zona"}

        if (
            member.id == int(reg.get("encargado_id") or 0)
            or "ENCARGADO" in keys
            or "ENCARGADO_AREA" in keys
            or "JEFE_DEPARTAMENTO" in keys
            or "SUPERVISOR" in keys
        ):
            puede.add("encargado")

        if KEY_DOC in keys:
            puede.add("docencia")

        zona = reg.get("key_director_zona") or "DIRECTOR_ADMINISTRATIVO"
        if zona in keys:
            puede.add("zona")

        return puede

    C._member_keys = _member_keys
    C._roles_firma_para = _roles_firma_para
    print("[cert_dg_fix] OK — Director General NO firma sin el rol de esa firma")
