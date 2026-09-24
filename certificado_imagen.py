# -*- coding: utf-8 -*
"""
certificado_imagen.py — Diploma PNG profesional (solo Roleplay).
Si existe assets/certificado_base.png se usa como plantilla.
"""
from __future__ import annotations

import io
import os
from datetime import datetime
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

_DIR = os.path.dirname(os.path.abspath(__file__))
_PLANTILLA = os.path.join(_DIR, "assets", "certificado_base.png")
_PLANTILLA_JPG = os.path.join(_DIR, "assets", "certificado_base.jpg")

# Tamaño por defecto si no hay plantilla
W, H = 1600, 1131


def _font(size: int, bold: bool = False):
    cands = []
    if bold:
        cands += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf",
            "C:/Windows/Fonts/timesbd.ttf",
            "C:/Windows/Fonts/georgiab.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ]
    cands += [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/times.ttf",
        "C:/Windows/Fonts/georgia.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for p in cands:
        if os.path.isfile(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _text_size(draw, text, font) -> Tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _wrap(draw, text: str, font, max_w: int):
    words = (text or "").split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        tw, _ = _text_size(draw, test, font)
        if tw <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def _centrar_texto(draw, text, y, font, fill, max_w=None, width=None):
    width = width or W
    max_w = max_w or (width - 200)
    lines = _wrap(draw, text, font, max_w)
    lh = getattr(font, "size", 22) + 10
    for i, line in enumerate(lines):
        tw, th = _text_size(draw, line, font)
        x = (width - tw) // 2
        draw.text((x, y + i * lh), line, font=font, fill=fill)
    return len(lines) * lh


def _cargar_plantilla() -> Optional[Image.Image]:
    for path in (_PLANTILLA, _PLANTILLA_JPG):
        if os.path.isfile(path):
            try:
                return Image.open(path).convert("RGB")
            except Exception as e:
                print("[certificado] plantilla:", e)
    return None


def _fondo_elegante() -> Image.Image:
    """Fondo tipo pergamino premium si no hay plantilla."""
    img = Image.new("RGB", (W, H), (248, 243, 232))
    draw = ImageDraw.Draw(img)

    # Viñeta suave en bordes
    for i in range(80):
        alpha = int(40 * (1 - i / 80))
        col = (230 - alpha // 2, 220 - alpha // 2, 200 - alpha // 2)
        draw.rectangle([i, i, W - 1 - i, H - 1 - i], outline=col)

    oro = (176, 141, 68)
    oro_osc = (120, 90, 40)
    morado = (72, 38, 98)

    # Marco exterior
    for i, c in enumerate([oro, oro_osc, oro]):
        draw.rectangle([40 + i * 3, 40 + i * 3, W - 40 - i * 3, H - 40 - i * 3], outline=c, width=2)

    # Marco interior fino
    draw.rectangle([70, 70, W - 70, H - 70], outline=oro, width=1)

    # Esquinas ornamentales
    for cx, cy in [(95, 95), (W - 95, 95), (95, H - 95), (W - 95, H - 95)]:
        draw.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], outline=oro, width=3)
        draw.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], outline=oro_osc, width=2)

    # Franja superior decorativa
    draw.rectangle([120, 130, W - 120, 134], fill=oro)
    return img


def generar_certificado(
    *,
    nombre_receptor: str,
    titulo: str,
    hospital: str = "Hospital",
    emisor: str = "Dirección de Docencia",
    fecha: str = "",
    numero: str = "",
    descripcion: str = "",
    departamento: str = "",
    capacitacion: str = "",
) -> io.BytesIO:
    """
    Genera el diploma.
    - capacitacion: nombre de la capacitación recibida (prioridad sobre titulo si viene).
    - titulo: título del certificado / capacitación.
    """
    if not fecha:
        fecha = datetime.utcnow().strftime("%d/%m/%Y")
    if not numero:
        numero = "CERT-00000"

    cap = (capacitacion or titulo or "Capacitación").strip()
    nombre = (nombre_receptor or "—").strip()
    hospital = (hospital or "Hospital").strip()

    plantilla = _cargar_plantilla()
    if plantilla is not None:
        img = plantilla
        w, h = img.size
        # Escalar a ancho razonable si es muy grande/pequeña
        if w < 900 or w > 2200:
            ratio = 1600 / w
            img = img.resize((1600, int(h * ratio)), Image.Resampling.LANCZOS)
            w, h = img.size
    else:
        img = _fondo_elegante()
        w, h = W, H

    draw = ImageDraw.Draw(img)
    global W, H
    W, H = w, h

    # Paleta según si hay plantilla (texto más contrastado)
    if plantilla is not None:
        c_titulo = (55, 35, 75)
        c_nombre = (30, 25, 40)
        c_suave = (70, 60, 80)
        c_oro = (140, 110, 50)
    else:
        c_titulo = (72, 38, 98)
        c_nombre = (40, 30, 50)
        c_suave = (90, 80, 100)
        c_oro = (176, 141, 68)

    f_h = _font(max(28, w // 40), bold=True)
    f_sub = _font(max(16, w // 70))
    f_cert = _font(max(36, w // 32), bold=True)
    f_nombre = _font(max(40, w // 28), bold=True)
    f_cap = _font(max(28, w // 38), bold=True)
    f_body = _font(max(18, w // 60))
    f_small = _font(max(15, w // 75))
    f_tiny = _font(max(13, w // 90))

    # Zonas verticales proporcionales
    y = int(h * 0.12)

    if plantilla is None:
        y += _centrar_texto(draw, hospital.upper(), y, f_h, c_titulo, width=w)
        y += 6
        y += _centrar_texto(draw, "Dirección de Docencia y Capacitación", y, f_sub, c_suave, width=w)
        y += 16
        draw.line([(int(w * 0.2), y), (int(w * 0.8), y)], fill=c_oro, width=2)
        y += 22
        y += _centrar_texto(draw, "CERTIFICADO", y, f_cert, c_titulo, width=w)
        y += 8
        y += _centrar_texto(draw, "Documento de Roleplay", y, f_tiny, c_suave, width=w)
        y += 28
    else:
        # Con plantilla: solo rellenar campos en el centro
        y = int(h * 0.28)

    y += _centrar_texto(draw, "Se certifica que", y, f_body, c_suave, width=w)
    y += 14
    y += _centrar_texto(draw, nombre, y, f_nombre, c_nombre, width=w)
    y += 10
    # Línea bajo el nombre
    nw, _ = _text_size(draw, nombre, f_nombre)
    lx0 = (w - min(nw + 80, int(w * 0.6))) // 2
    lx1 = w - lx0
    draw.line([(lx0, y), (lx1, y)], fill=c_oro, width=1)
    y += 20

    y += _centrar_texto(
        draw,
        "ha completado satisfactoriamente la capacitación:",
        y,
        f_body,
        c_suave,
        width=w,
    )
    y += 16
    y += _centrar_texto(draw, f'"{cap}"', y, f_cap, c_titulo, width=w)

    if descripcion:
        y += 14
        y += _centrar_texto(draw, descripcion, y, f_small, c_suave, max_w=int(w * 0.7), width=w)

    if departamento:
        y += 12
        y += _centrar_texto(draw, f"Área / Departamento: {departamento}", y, f_small, c_nombre, width=w)

    # Pie de datos
    pie_y = int(h * 0.78)
    if plantilla is None:
        draw.line([(int(w * 0.15), pie_y), (int(w * 0.85), pie_y)], fill=c_oro, width=1)

    col_y = pie_y + 20
    draw.text((int(w * 0.14), col_y), f"Fecha\n{fecha}", font=f_small, fill=c_nombre)
    draw.text((int(w * 0.42), col_y), f"N.º de certificado\n{numero}", font=f_small, fill=c_nombre)
    draw.text((int(w * 0.68), col_y), f"Emitido por\n{emisor}", font=f_small, fill=c_nombre)

    if plantilla is None:
        # Sello
        sx, sy, sr = int(w * 0.88), int(h * 0.86), 55
        draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], outline=(150, 45, 55), width=4)
        draw.ellipse([sx - sr + 8, sy - sr + 8, sx + sr - 8, sy + sr - 8], outline=(150, 45, 55), width=2)
        fs = _font(13, bold=True)
        draw.text((sx - 26, sy - 16), "SOLO", font=fs, fill=(150, 45, 55))
        draw.text((sx - 16, sy + 4), "RP", font=fs, fill=(150, 45, 55))

        note = "Documento interno de roleplay · Sin validez fuera del servidor"
        tw, _ = _text_size(draw, note, f_tiny)
        draw.text(((w - tw) // 2, h - 48), note, font=f_tiny, fill=c_suave)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf
