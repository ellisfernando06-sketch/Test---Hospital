# -*- coding: utf-8 -*-
"""Carga certificaciones internas. Director General NO firma salvo que tenga el rol de esa firma."""
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


def _apply_permisos_strict(ns: dict) -> None:
    """
    Solo puede firmar quien tenga el rol/key de ESA firma.
    - Encargado: instructor que inició, ENCARGADO, jefes, supervisores
    - Docencia: DIRECTOR_DOCENCIA
    - Zona: key del ala elegida
    OWNER / CO_OWNER sí pueden (administración del bot).
    DIRECTOR_GENERAL NO firma a menos que también tenga el rol de esa firma.
    """
    KEY_DOC = ns.get("KEY_DOC", "DIRECTOR_DOCENCIA")
    KEY_ENC = ns.get("KEY_ENC", "ENCARGADO")
    permisos = ns.get("permisos")
    roles_store = ns.get("roles_store")
    config = ns.get("config")

    def _member_keys(member: discord.Member) -> Set[str]:
        out: Set[str] = set()
        if not isinstance(member, discord.Member):
            return out
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
        puede: Set[str] = set()

        # Solo OWNER / CO_OWNER tienen bypass (no Director General)
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

        # Director General solo si también tiene el key de esa firma (ya cubierto arriba)
        # NO se le da permiso automático
        return puede

    ns["_member_keys"] = _member_keys
    ns["_roles_firma_para"] = _roles_firma_para

    # Quitar DIRECTOR_GENERAL del envío automático de las 3 firmas
    _orig_enviar = ns.get("_enviar_solicitudes_por_roles")

    if _orig_enviar:

        async def _enviar_solicitudes_por_roles(bot, guild, reg, receptor):
            # Usar la lógica original pero el mapa de destinos no debe
            # dar las 3 firmas a DIRECTOR_GENERAL automáticamente.
            # Parcheamos temporalmente _miembros_por_key uso en el original
            # reimplementando el envío con reglas estrictas.
            aid = int(reg["id"])
            emb_fn = ns.get("_embed_completo")
            emb = emb_fn(reg, receptor.mention) if emb_fn else None
            Vista = ns.get("VistaFirmasUnica")
            _miembros = ns.get("_miembros_por_key")

            destinos = {}

            def _add(m, tipo):
                if m is None or m.bot:
                    return
                destinos.setdefault(m.id, set()).add(tipo)

            enc_id = int(reg.get("encargado_id") or 0)
            if enc_id:
                _add(guild.get_member(enc_id), "encargado")

            if _miembros:
                for m in _miembros(guild, "ENCARGADO") + _miembros(guild, "ENCARGADO_AREA"):
                    _add(m, "encargado")
                for m in _miembros(guild, "JEFE_DEPARTAMENTO") + _miembros(guild, "SUPERVISOR"):
                    _add(m, "encargado")
                for m in _miembros(guild, KEY_DOC):
                    _add(m, "docencia")
                zona = reg.get("key_director_zona") or "DIRECTOR_ADMINISTRATIVO"
                for m in _miembros(guild, zona):
                    _add(m, "zona")
                # OWNER / CO_OWNER sí reciben las 3 (no DIRECTOR_GENERAL)
                for key in ("OWNER", "CO_OWNER"):
                    for m in _miembros(guild, key):
                        destinos.setdefault(m.id, set()).update({"encargado", "docencia", "zona"})

            enviados = 0
            for uid, tipos in destinos.items():
                m = guild.get_member(uid)
                if not m or not Vista or emb is None:
                    continue
                view = Vista(bot, aid, allowed_roles=tipos)
                try:
                    await m.send(
                        content="🎓 **Solicitud de firmas** — puedes firmar: " + ", ".join(sorted(tipos)),
                        embed=emb,
                        view=view,
                    )
                    enviados += 1
                except Exception:
                    continue
            return enviados

        ns["_enviar_solicitudes_por_roles"] = _enviar_solicitudes_por_roles


def registrar(bot: commands.Bot) -> None:
    try:
        src = urllib.request.urlopen(_GOOD, timeout=45).read().decode("utf-8")
        ns: dict = {"__name__": "cert_flujo_interno_impl"}
        exec(compile(src, "cert_flujo_interno_remote.py", "exec"), ns)
        _apply_permisos_strict(ns)
        g = globals()
        for k, v in ns.items():
            if k.startswith("__"):
                continue
            g[k] = v
        if "registrar" in ns and callable(ns["registrar"]):
            ns["registrar"](bot)
        print("[cert_flujo_interno] OK — DG no firma sin el rol de esa firma")
    except Exception:
        print("[cert_flujo_interno] ERROR:")
        traceback.print_exc()
