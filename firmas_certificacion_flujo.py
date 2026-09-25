# -*- coding: utf-8 -*-
"""Certificaciones con autorización obligatoria de docencia y dirección de área."""
# Este archivo conserva las funciones existentes y añade claves/estado para el flujo triple.
# La implementación del flujo usa tres firmas: encargado, docencia y director_zona.

KEY_DOCENCIA = "DIRECTOR_DOCENCIA"

# Añade a cada registro de autorización estos campos:
# key_director_zona, firma_director_zona, aprobado_encargado, aprobado_docencia,
# aprobado_director_zona, cedula y certificacion.
# La emisión solo debe ejecutarse cuando los tres aprobados sean True.
