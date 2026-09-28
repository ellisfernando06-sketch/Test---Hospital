# -*- coding: utf-8 -*-
"""Carga la implementación de certificaciones internas y aplica parche Director General."""
from __future__ import annotations

import traceback
import urllib.request
from typing import Set

import discord
from discord.ext import commands

_GOOD = (
    "https://raw.githubusercontent.com/ellisfernando06-sketch/Test---Hospital/"
    "3a48da439894f1645c57b66acce9e76d4a1df7fd/cert_flujo_interno.py"
)


def _apply_dg_patch(ns: dict) -> None:
    """Director General / OWNER / CO_OWNER pueden firmar las 3."""
    KEY_DOC = ns.get("KEY_DOC", "DIRECTOR_DOCENCIA")
    KEY_ENC = ns.get("KEY_ENC", "ENCARGADO")
    permisos = ns.get("permisos")
    roles_store = ns.get("roles_store")
    config = ns.get("config")

    def _member_keys(member: discord.Member) -> Set[str]:
        out: Set[str] = set()
        if not isinstance(member, discord.Member):
            return out
        if member.guild_permissions.administrator:
            out.update({"OWNER", "CO_OWNER", KEY_DOC, KEY_ENC, "DIRECTOR_GENERAL"})
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
            try:
                for key in list(getattr(config, "KEYS_NOMBRES", {}) or {}):
                    if permisos.member_tiene_alguna_key(member, key):
                        out.add(key)
            except Exception:
                pass
        if roles_store and config:
            try:
                for key in list(getattr(config, "KEYS_NOMBRES", {}) or {}):
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
        if "DIRECTOR_GENERAL" in keys or "OWNER" in keys or "CO_OWNER" in keys:
            return {"encargado", "docencia", "zona"}
        if member.guild_permissions.administrator:
            return {"encargado", "docencia", "zona"}
        puede: Set[str] = set()
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

    ns["_member_keys"] = _member_keys
    ns["_roles_firma_para"] = _roles_firma_para


def registrar(bot: commands.Bot) -> None:
    try:
        src = urllib.request.urlopen(_GOOD, timeout=45).read().decode("utf-8")
        # Evitar recursión: el archivo bueno define registrar; ejecutamos en namespace propio
        ns: dict = {"__name__": "cert_flujo_interno_impl"}
        exec(compile(src, "cert_flujo_interno_remote.py", "exec"), ns)
        _apply_dg_patch(ns)
        # Reexportar símbolos usados por otros módulos
        g = globals()
        for k, v in ns.items():
            if k.startswith("__"):
                continue
            g[k] = v
        if "registrar" in ns and callable(ns["registrar"]):
            ns["registrar"](bot)
        print("[cert_flujo_interno] OK (remoto + DG puede firmar las 3)")
    except Exception:
        print("[cert_flujo_interno] ERROR cargando implementación:")
        traceback.print_exc()
