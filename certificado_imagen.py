# -*- coding: utf-8 -*
"""
certificado_imagen.py — Diploma PNG (solo Roleplay).
Tipografía unificada: un color principal y tamaños proporcionales.
Plantilla opcional: assets/certificado_base.png (o .jpg).
"""
from __future__ import annotations

import io
import os
from datetime import datetime
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

_DIR = os.path.dirname(os.path.abspath(__file__))
_PLANTILLA = os.path.join(_DIR, "assets", "certificado_base.png")
_PLANTILLA_JPG = os.path.join(_DIR, "assets", "certificado_base.jpg")

# Lienzo por defecto
W, H = 1600, 1131

# ── Paleta única (misma familia de color en todo el diploma) ─────────────
# Tinta principal: casi negro cálido (legible sobre crema y plantillas claras)
TINTA = (45, 40, 48)
TINTA_SUAVE = (45, 40, 48)       # mismo tono; se usa alpha visual vía tono idéntico
TINTA_ACENTO = (45, 40, 48)      # títulos y nombre también en el mismo color
ORO_LINEA = (160, 130, 70)       # solo líneas decorativas, no texto
CREMA = (248, 243, 232)


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


def _escala(w: int) -> dict:
    """
    Escala tipográfica congruente según el ancho del diploma.
    Proporción ~ base 1000px → tamaños de referencia de imprenta.
    """
    u = w / 1000.0  # unidad de escala
    return {
        # Jerarquía fija (todos en la misma tinta)
        "hospital": max(26, int(34 * u)),      # cabecera
        "subtitulo": max(14, int(16 * u)),     # Dirección de Docencia
        "certificado": max(30, int(40 * u)),   # CERTIFICADO
        "frase": max(15, int(18 * u)),         # "Se certifica que…"
        "nombre": max(32, int(44 * u)),        # nombre del graduado (destacado)
        "capacitacion": max(24, int(30 * u)),  # título de la capacitación
        "cuerpo": max(14, int(16 * u)),        # descripción / área
        "pie": max(13, int(15 * u)),           # fecha, nº, emisor (idénticos entre sí)
        "nota": max(11, int(12 * u)),          # nota RP al pie
        "gap": max(8, int(10 * u)),            # espacio entre bloques
    }


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


def _centrar(draw, text, y, font, fill, width, max_w=None):
    max_w = max_w or int(width * 0.78)
    lines = _wrap(draw, text, font, max_w)
    size = getattr(font, "size", 18)
    lh = size + max(6, size // 5)
    for i, line in enumerate(lines):
        tw, _ = _text_size(draw, line, font)
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


def _fondo_elegante(w: int, h: int) -> Image.Image:
    img = Image.new("RGB", (w, h), CREMA)
    draw = ImageDraw.Draw(img)
    for i in range(60):
        col = (235 - i // 3, 228 - i // 3, 212 - i // 3)
        draw.rectangle([i, i, w - 1 - i, h - 1 - i], outline=col)
    for i, c in enumerate([ORO_LINEA, (120, 95, 45), ORO_LINEA]):
        draw.rectangle([36 + i * 3, 36 + i * 3, w - 36 - i * 3, h - 36 - i * 3], outline=c, width=2)
    draw.rectangle([62, 62, w - 62, h - 62], outline=ORO_LINEA, width=1)
    for cx, cy in [(85, 85), (w - 85, 85), (85, h - 85), (w - 85, h - 85)]:
        draw.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], outline=ORO_LINEA, width=2)
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
    if not fecha:
        fecha = datetime.utcnow().strftime("%d/%m/%Y")
    if not numero:
        numero = "CERT-00000"

    cap = (capacitacion or titulo or "Capacitación").strip()
    nombre = (nombre_receptor or "—").strip()
    hospital = (hospital or "Hospital").strip()
    emisor = (emisor or "Dirección de Docencia").strip()

    plantilla = _cargar_plantilla()
    if plantilla is not None:
        img = plantilla
        w, h = img.size
        if w < 900 or w > 2200:
            ratio = 1600 / w
            img = img.resize((1600, max(1, int(h * ratio))), Image.Resampling.LANCZOS)
            w, h = img.size
    else:
        w, h = W, H
        img = _fondo_elegante(w, h)

    draw = ImageDraw.Draw(img)
    sc = _escala(w)
    gap = sc["gap"]

    # Todas las fuentes de la misma familia; tamaños de la escala
    f_hospital = _font(sc["hospital"], bold=True)
    f_sub = _font(sc["subtitulo"], bold=False)
    f_cert = _font(sc["certificado"], bold=True)
    f_frase = _font(sc["frase"], bold=False)
    f_nombre = _font(sc["nombre"], bold=True)
    f_cap = _font(sc["capacitacion"], bold=True)
    f_cuerpo = _font(sc["cuerpo"], bold=False)
    f_pie = _font(sc["pie"], bold=False)
    f_nota = _font(sc["nota"], bold=False)

    # Un solo color de texto en todo el certificado
    ink = TINTA

    if plantilla is None:
        y = int(h * 0.11)
        y += _centrar(draw, hospital.upper(), y, f_hospital, ink, w)
        y += gap // 2
        y += _centrar(draw, "Dirección de Docencia y Capacitación", y, f_sub, ink, w)
        y += gap
        draw.line([(int(w * 0.22), y), (int(w * 0.78), y)], fill=ORO_LINEA, width=2)
        y += gap + 4
        y += _centrar(draw, "CERTIFICADO", y, f_cert, ink, w)
        y += gap // 2
        y += _centrar(draw, "Documento de Roleplay", y, f_nota, ink, w)
        y += gap * 2
    else:
        y = int(h * 0.30)

    y += _centrar(draw, "Se certifica que", y, f_frase, ink, w)
    y += gap
    y += _centrar(draw, nombre, y, f_nombre, ink, w)
    y += gap // 2

    nw, _ = _text_size(draw, nombre, f_nombre)
    line_w = min(nw + int(w * 0.06), int(w * 0.55))
    lx0 = (w - line_w) // 2
    draw.line([(lx0, y), (lx0 + line_w, y)], fill=ORO_LINEA, width=1)
    y += gap + 4

    y += _centrar(draw, "ha completado satisfactoriamente la capacitación:", y, f_frase, ink, w)
    y += gap
    y += _centrar(draw, f'"{cap}"', y, f_cap, ink, w)

    if descripcion:
        y += gap
        y += _centrar(draw, descripcion, y, f_cuerpo, ink, w, max_w=int(w * 0.70))

    if departamento:
        y += gap
        y += _centrar(draw, f"Área / Departamento: {departamento}", y, f_cuerpo, ink, w)

    # Pie: tres columnas, MISMO tamaño y MISMO color
    pie_y = int(h * 0.78)
    if plantilla is None:
        draw.line([(int(w * 0.14), pie_y), (int(w * 0.86), pie_y)], fill=ORO_LINEA, width=1)

    col_y = pie_y + gap + 4
    cols = [
        (0.14, f"Fecha\n{fecha}"),
        (0.40, f"N.º de certificado\n{numero}"),
        (0.66, f"Emitido por\n{emisor}"),
    ]
    for frac, txt in cols:
        draw.text((int(w * frac), col_y), txt, font=f_pie, fill=ink)

    if plantilla is None:
        note = "Documento interno de roleplay · Sin validez fuera del servidor"
        tw, _ = _text_size(draw, note, f_nota)
        draw.text(((w - tw) // 2, h - int(h * 0.045)), note, font=f_nota, fill=ink)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf
