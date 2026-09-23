# -*- coding: utf-8 -*-
"""centro_solicitudes_ui.py — Formularios, tickets y comandos del Centro de Solicitudes."""
from __future__ import annotations

import asyncio
from typing import Dict, Optional

import discord
from discord import ui, app_commands
from discord.ext import commands

import config
import permisos
import roles_store
from centro_solicitudes import (
    CATEGORIAS,
    ESTADOS,
    PRIORIDADES,
    embed_panel_principal,
    embed_ticket,
    embed_log_accion,
    guardar_solicitud,
    obtener_solicitud,
    actualizar_solicitud,
    _siguiente_numero,
    _rol_staff,
    _categoria_canal,
    enviar_log_solicitud,
    _now,
    _fecha_legible,
)

# AnadirUsuario* viven en ticket_adduser.py
from ticket_adduser import AnadirUsuarioView  # noqa: E402
