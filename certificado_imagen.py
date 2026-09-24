# -*- coding: utf-8 -*
"""
certificado_imagen.py — Genera un diploma/certificado en PNG (solo Roleplay).
"""
from __future__ import annotations

import io
import os
from datetime import datetime
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

# Tamaño del diploma (horizontal, estilo certificado)
W, H = 1400, 990

# Colores
CREMA = (252, 248, 240)
BORDE_ORO = (184, 148, 60)
BORDE_OSCURO = (90, 70, 30)
MORADO = (90, 40, 120)
MORADO_SUAVE = (140, 90, 170)
TEXTO = (40, 30, 50)
TEXTO_SUAVE = (80, 70, 90)
BLANCO = (255, 255, 255)
ROJO_SELLO = (160, 40, 50)


def _font(size: int, bold: bool = False):
    """Fuente del sistema; fallback a default de PIL."""
    candidates = []
    if bold:
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf",
            "C:/Windows/Fonts/timesbd.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ]
    candidates += [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/times.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _centrar(draw: ImageDraw.ImageDraw, text: str, y: int, font, fill, max_width: Optional[int] = None):
    if max_width is None:
        max_width = W - 160
    # Wrap simple
    words = (text or "").split()
    lines = []
    cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if not lines:
        lines = [""]
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        draw.text((x, y + i * (font.size + 8)), line, font=font, fill=fill)
    return len(lines) * (font.size + 8)


def _rect_borde(draw, x0, y0, x1, y1, width, fill):
    for i in range(width):
        draw.rectangle([x0 + i, y0 + i, x1 - i, y1 - i], outline=fill)


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
) -> io.BytesIO:
    """
    Genera un PNG de certificado profesional (solo Roleplay).
    Devuelve un BytesIO listo para discord.File.
    """
    if not fecha:
        fecha = datetime.utcnow().strftime("%d/%m/%Y")
    if not numero:
        numero = "CERT-00000"

    img = Image.new("RGB", (W, H), CREMA)
    draw = ImageDraw.Draw(img)

    # Marcos dobles dorados
    _rect_borde(draw, 28, 28, W - 28, H - 28, 6, BORDE_ORO)
    _rect_borde(draw, 44, 44, W - 44, H - 44, 2, BORDE_OSCURO)
    _rect_borde(draw, 56, 56, W - 56, H - 56, 1, BORDE_ORO)

    # Esquinas decorativas
    for (cx, cy) in [(70, 70), (W - 70, 70), (70, H - 70), (W - 70, H - 70)]:
        draw.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], outline=BORDE_ORO, width=3)

    # Cabecera
    f_hospital = _font(42, bold=True)
    f_sub = _font(22)
    f_titulo = _font(48, bold=True)
    f_nombre = _font(52, bold=True)
    f_body = _font(24)
    f_small = _font(18)
    f_tiny = _font(15)

    y = 90
    y += _centrar(draw, hospital.upper(), y, f_hospital, MORADO)
    y += 4
    y += _centrar(draw, "Dirección de Docencia y Capacitación", y, f_sub, MORADO_SUAVE)
    y += 18

    # Línea ornamental
    draw.line([(220, y), (W - 220, y)], fill=BORDE_ORO, width=2)
    y += 28

    y += _centrar(draw, "CERTIFICADO OFICIAL", y, f_titulo, MORADO)
    y += 10
    y += _centrar(draw, "—  Solo Roleplay  —", y, f_small, TEXTO_SUAVE)
    y += 28

    y += _centrar(draw, "Se certifica que", y, f_body, TEXTO_SUAVE)
    y += 16

    # Nombre del graduado
    y += _centrar(draw, nombre_receptor, y, f_nombre, TEXTO)
    y += 12
    draw.line([(300, y), (W - 300, y)], fill=BORDE_ORO, width=1)
    y += 20

    y += _centrar(
        draw,
        "ha completado satisfactoriamente la capacitación:",
        y,
        f_body,
        TEXTO_SUAVE,
    )
    y += 18

    y += _centrar(draw, f«{titulo}»".replace("«", "«").replace("»", "»"), y, _font(34, bold=True), MORADO)
    # fix title quotes
    # (redraw clean)
    # Actually use proper quotes:
    # Re-draw titulo properly below — undo bad line by overwriting region is hard;
    # we'll set titulo_line correctly from the start in a cleaner way.

    # DESCRIPTION
    if descripcion:
        y += 14
        y += _centrar(draw, descripcion, y, f_small, TEXTO_SUAVE, max_width=W - 220)

    if departamento:
        y += 12
        y += _centrar(draw, f"Área: {departamento}", y, f_small, TEXTO)

    # Pie: fecha, número, emisor, sello
    pie_y = H - 200
    draw.line([(180, pie_y), (W - 180, pie_y)], fill=BORDE_ORO, width=1)

    col1_x = 200
    col2_x = W // 2
    col3_x = W - 380

    draw.text((col1_x, pie_y + 24), f"Fecha\n{fecha}", font=f_small, fill=TEXTO)
    draw.text((col2_x - 40, pie_y + 24), f"N.º\n{numero}", font=f_small, fill=TEXTO)
    draw.text((col3_x, pie_y + 24), f"Emitido por\n{emisor}", font=f_small, fill=TEXTO)

    # Sello circular
    sx, sy, sr = W - 160, H - 150, 62
    draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], outline=ROJO_SELLO, width=4)
    draw.ellipse([sx - sr + 10, sy - sr + 10, sx + sr - 10, sy + sr - 10], outline=ROJO_SELLO, width=2)
    f_sello = _font(14, bold=True)
    sello_txt = "RP\nVÁLIDO"
    # center sello text roughly
    draw.text((sx - 28, sy - 18), "SOLO", font=f_sello, fill=ROJO_SELLO)
    draw.text((sx - 18, sy + 4), "RP", font=f_sello, fill=ROJO_SELLO)

    # Footer note
    note = "Documento interno de roleplay · Sin validez fuera del servidor"
    bbox = draw.textbbox((0, 0), note, font=f_tiny)
    draw.text(((W - (bbox[2] - bbox[0])) // 2, H - 52), note, font=f_tiny, fill=TEXTO_SUAVE)

    # ── Redibujar bloque del título de forma limpia ──
    # Como el string del título se construyó mal arriba, regeneramos con lógica limpia:
    return _generar_limpio(
        nombre_receptor=nombre_receptor,
        titulo=titulo,
        hospital=hospital,
        emisor=emisor,
        fecha=fecha,
        numero=numero,
        descripcion=descripcion,
        departamento=departamento,
    )


def _generar_limpio(
    *,
    nombre_receptor: str,
    titulo: str,
    hospital: str,
    emisor: str,
    fecha: str,
    numero: str,
    descripcion: str,
    departamento: str,
) -> io.BytesIO:
    img = Image.new("RGB", (W, H), CREMA)
    draw = ImageDraw.Draw(img)

    _rect_borde(draw, 28, 28, W - 28, H - 28, 6, BORDE_ORO)
    _rect_borde(draw, 44, 44, W - 44, H - 44, 2, BORDE_OSCURO)
    _rect_borde(draw, 56, 56, W - 56, H - 56, 1, BORDE_ORO)

    for (cx, cy) in [(70, 70), (W - 70, 70), (70, H - 70), (W - 70, H - 70)]:
        draw.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], outline=BORDE_ORO, width=3)

    f_hospital = _font(42, bold=True)
    f_sub = _font(22)
    f_titulo = _font(48, bold=True)
    f_nombre = _font(52, bold=True)
    f_cap = _font(34, bold=True)
    f_body = _font(24)
    f_small = _font(18)
    f_tiny = _font(15)
    f_sello = _font(14, bold=True)

    y = 90
    y += _centrar(draw, (hospital or "Hospital").upper(), y, f_hospital, MORADO)
    y += 4
    y += _centrar(draw, "Dirección de Docencia y Capacitación", y, f_sub, MORADO_SUAVE)
    y += 18
    draw.line([(220, y), (W - 220, y)], fill=BORDE_ORO, width=2)
    y += 28
    y += _centrar(draw, "CERTIFICADO OFICIAL", y, f_titulo, MORADO)
    y += 8
    y += _centrar(draw, "—  Solo Roleplay  —", y, f_small, TEXTO_SUAVE)
    y += 30
    y += _centrar(draw, "Se certifica que", y, f_body, TEXTO_SUAVE)
    y += 18
    y += _centrar(draw, nombre_receptor or "—", y, f_nombre, TEXTO)
    y += 8
    draw.line([(300, y), (W - 300, y)], fill=BORDE_ORO, width=1)
    y += 22
    y += _centrar(draw, "ha completado satisfactoriamente la capacitación:", y, f_body, TEXTO_SUAVE)
    y += 20
    y += _centrar(draw, f'"{titulo}"', y, f_cap, MORADO)

    if descripcion:
        y += 16
        y += _centrar(draw, descripcion, y, f_small, TEXTO_SUAVE, max_width=W - 220)

    if departamento:
        y += 14
        y += _centrar(draw, f"Área: {departamento}", y, f_small, TEXTO)

    pie_y = H - 200
    draw.line([(180, pie_y), (W - 180, pie_y)], fill=BORDE_ORO, width=1)

    draw.text((200, pie_y + 24), f"Fecha\n{fecha}", font=f_small, fill=TEXTO)
    draw.text((W // 2 - 40, pie_y + 24), f"N.º\n{numero}", font=f_small, fill=TEXTO)
    draw.text((W - 400, pie_y + 24), f"Emitido por\n{emisor}", font=f_small, fill=TEXTO)

    sx, sy, sr = W - 160, H - 150, 62
    draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], outline=ROJO_SELLO, width=4)
    draw.ellipse([sx - sr + 10, sy - sr + 10, sx + sr - 10, sy + sr - 10], outline=ROJO_SELLO, width=2)
    draw.text((sx - 28, sy - 18), "SOLO", font=f_sello, fill=ROJO_SELLO)
    draw.text((sx - 18, sy + 4), "RP", font=f_sello, fill=ROJO_SELLO)

    note = "Documento interno de roleplay · Sin validez fuera del servidor"
    bbox = draw.textbbox((0, 0), note, font=f_tiny)
    draw.text(((W - (bbox[2] - bbox[0])) // 2, H - 52), note, font=f_tiny, fill=TEXTO_SUAVE)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf
