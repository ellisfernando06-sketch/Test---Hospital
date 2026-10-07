# -*- coding: utf-8 -*-
"""Banco difícil: 20 preguntas/dirección, opciones casi iguales."""
from __future__ import annotations

from typing import Dict, List, Tuple

from examen_preguntas_a import BANCO_PART as _A
from examen_preguntas_b import BANCO_PART as _B

BANCO: Dict[str, List[Tuple[str, List[str], int]]] = {}
BANCO.update(_A)
BANCO.update(_B)
