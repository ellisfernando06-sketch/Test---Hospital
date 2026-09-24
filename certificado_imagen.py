# -*- coding: utf-8 -*
"""
certificado_imagen.py — Diploma sobre plantilla Hospital General + firmas IC.
Plantilla: assets/certificado_base.jpg (o .png)
"""
from __future__ import annotations

import io
import os
from datetime import datetime
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

_DIR = os.path.dirname(os.path.abspath(__file__))
_PLANTILLAS = [
    os.path.join(_DIR, "assets", "certificado_base.jpg"),
    os.path.join(_DIR, "assets", "certificado_base.png"),
    os.path.join(_DIR, "assets", "certificado_base.jpeg"),
]

W, H = 1536, 1024  # tamaño de la plantilla oficial

# Tinta única (azul noche, coherente con el marco HG)
TINTA = (28, 42, 68)
ORO = (176, 141, 68)


def _font(size: int, bold: bool = False):
    cands = []
    if bold:
        cands += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf",
            "C:/Windows/Fonts/timesbd.ttf",
            "C:/Windows/Fonts/georgiab.ttf",
        ]
    cands += [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
        "C:/Windows/Fonts/times.ttf",
        "C:/Windows/Fonts/georgia.ttf",
    ]
    for p in cands:
        if os.path.isfile(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _ts(draw, text, font):
    b = draw.textbbox((0, 0), text, font=font)
    return b[2] - b[0], b[3] - b[1]


def _wrap(draw, text, font, max_w):
    words = (text or "").split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if _ts(draw, t, font)[0] <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def _centrar(draw, text, y, font, fill, width, max_w=None):
    max_w = max_w or int(width * 0.72)
    lines = _wrap(draw, text, font, max_w)
    size = getattr(font, "size", 18)
    lh = size + max(6, size // 5)
    for i, line in enumerate(lines):
        tw, _ = _ts(draw, line, font)
        draw.text(((width - tw) // 2, y + i * lh), line, font=font, fill=fill)
    return len(lines) * lh


def _cargar_plantilla() -> Optional[Image.Image]:
    for path in _PLANTILLAS:
        if os.path.isfile(path):
            try:
                return Image.open(path).convert("RGBA")
            except Exception as e:
                print("[certificado] plantilla:", path, e)
    return None


def _pegar_firma(base: Image.Image, path: Optional[str], box: Tuple[int, int, int, int]) -> None:
    """Pega firma escalada dentro del rectángulo (x, y, w, h)."""
    if not path or not os.path.isfile(path):
        return
    try:
        fir = Image.open(path).convert("RGBA")
        bw, bh = box[2], box[3]
        fir.thumbnail((bw, bh), Image.Resampling.LANCZOS)
        fx = box[0] + (bw - fir.width) // 2
        fy = box[1] + (bh - fir.height) // 2
        base.paste(fir, (fx, fy), fir)
    except Exception as e:
        print("[certificado] firma:", e)


def generar_certificado(
    *,
    nombre_receptor: str,
    titulo: str,
    hospital: str = "Hospital General",
    emisor: str = "Encargado",
    fecha: str = "",
    numero: str = "",
    descripcion: str = "",
    departamento: str = "",
    capacitacion: str = "",
    firma_encargado_path: Optional[str] = None,
    firma_director_path: Optional[str] = None,
    label_encargado: str = "Firma del encargado",
    label_director: str = "Director de Investigación y Docencia",
) -> io.BytesIO:
    if not fecha:
        fecha = datetime.utcnow().strftime("%d/%m/%Y")
    if not numero:
        numero = "CERT-00000"

    cap = (capacitacion or titulo or "Capacitación").strip()
    nombre = (nombre_receptor or "—").strip()

    plantilla = _cargar_plantilla()
    if plantilla is not None:
        img = plantilla
        if img.size != (W, H):
            img = img.resize((W, H), Image.Resampling.LANCZOS)
    else:
        img = Image.new("RGBA", (W, H), (248, 243, 232, 255))

    draw = ImageDraw.Draw(img)
    w, h = img.size
    ink = TINTA

    # Escala tipográfica única
    f_frase = _font(22, bold=False)
    f_nombre = _font(48, bold=True)
    f_cap = _font(32, bold=True)
    f_cuerpo = _font(18, bold=False)
    f_pie = _font(16, bold=False)
    f_label = _font(14, bold=False)

    # Zona de texto (debajo del encabezado HOSPITAL GENERAL de la plantilla)
    y = int(h * 0.34)
    y += _centrar(draw, "Se certifica que", y, f_frase, ink, w)
    y += 14
    y += _centrar(draw, nombre, y, f_nombre, ink, w)
    y += 8
    nw, _ = _ts(draw, nombre, f_nombre)
    lw = min(nw + 60, int(w * 0.5))
    lx = (w - lw) // 2
    draw.line([(lx, y), (lx + lw, y)], fill=ORO, width=1)
    y += 18
    y += _centrar(draw, "ha completado satisfactoriamente la capacitación:", y, f_frase, ink, w)
    y += 12
    y += _centrar(draw, f'"{cap}"', y, f_cap, ink, w)

    if descripcion:
        y += 12
        y += _centrar(draw, descripcion, y, f_cuerpo, ink, w, max_w=int(w * 0.65))
    if departamento:
        y += 10
        y += _centrar(draw, f"Área: {departamento}", y, f_cuerpo, ink, w)

    # Datos centrales inferiores
    mid_y = int(h * 0.68)
    y = max(y + 16, mid_y)
    _centrar(draw, f"Fecha: {fecha}    ·    N.º {numero}", y, f_pie, ink, w)

    # Firmas: izquierda encargado | derecha Director de Investigación y Docencia
    # Cajas de firma (relativas a plantilla 1536x1024)
    box_enc = (int(w * 0.12), int(h * 0.74), int(w * 0.28), int(h * 0.12))
    box_dir = (int(w * 0.60), int(h * 0.74), int(w * 0.28), int(h * 0.12))

    _pegar_firma(img, firma_encargado_path, box_enc)
    _pegar_firma(img, firma_director_path, box_dir)

    # Líneas y etiquetas bajo firmas
    ly = int(h * 0.87)
    draw.line([(box_enc[0], ly), (box_enc[0] + box_enc[2], ly)], fill=ORO, width=1)
    draw.line([(box_dir[0], ly), (box_dir[0] + box_dir[2], ly)], fill=ORO, width=1)

    # Etiquetas centradas bajo cada línea
    for box, label in ((box_enc, label_encargado), (box_dir, label_director)):
        tw, _ = _ts(draw, label, f_label)
        tx = box[0] + (box[2] - tw) // 2
        draw.text((tx, ly + 6), label, font=f_label, fill=ink)

    # Nombre del encargado bajo su etiqueta (si cabe)
    if emisor and emisor != "Encargado":
        te = f_label
        tw, _ = _ts(draw, emisor, te)
        draw.text((box_enc[0] + (box_enc[2] - tw) // 2, ly + 24), emisor, font=te, fill=ink)

    out = img.convert("RGB")
    buf = io.BytesIO()
    out.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf
