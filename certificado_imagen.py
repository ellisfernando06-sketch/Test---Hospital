# -*- coding: utf-8 -*
"""Generación profesional de certificados del hospital."""
from __future__ import annotations

import io
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
PLANTILLAS = [
    os.path.join(ROOT, "assets", x)
    for x in ("certificado_base.png", "certificado_base.jpg", "certificado_base.jpeg")
]

W, H = 1600, 1131  # proporción documento formal

# Paleta institucional
TINTA = (22, 36, 58)
TINTA_SUAVE = (55, 70, 95)
ORO = (168, 132, 55)
ORO_CLARO = (196, 168, 98)
CREMA = (250, 246, 236)
BORDE = (40, 55, 80)
ROJO_SELLO = (140, 35, 45)


def _font(size: int, bold: bool = False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/timesbd.ttf" if bold else "C:/Windows/Fonts/times.ttf",
        "C:/Windows/Fonts/georgia.ttf",
    ]
    for p in paths:
        if os.path.isfile(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _tw(draw, text, font):
    b = draw.textbbox((0, 0), text, font=font)
    return b[2] - b[0]


def _th(draw, text, font):
    b = draw.textbbox((0, 0), text, font=font)
    return b[3] - b[1]


def _center(draw, text, y, font, fill=TINTA, max_w=None):
    max_w = max_w or int(W * 0.72)
    lines, cur = [], ""
    for word in (text or "").split():
        test = (cur + " " + word).strip()
        if _tw(draw, test, font) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur or not lines:
        lines.append(cur)
    lh = getattr(font, "size", 18) + 10
    for i, line in enumerate(lines):
        x = (W - _tw(draw, line, font)) // 2
        draw.text((x, y + i * lh), line, font=font, fill=fill)
    return len(lines) * lh


def _draw_double_border(draw, margin=36):
    """Marco doble dorado + línea interior."""
    # exterior grueso
    for i in range(4):
        draw.rectangle(
            [margin + i, margin + i, W - margin - i, H - margin - i],
            outline=ORO if i < 2 else ORO_CLARO,
            width=1,
        )
    inner = margin + 18
    draw.rectangle([inner, inner, W - inner, H - inner], outline=BORDE, width=2)
    # esquinas decorativas
    c = 42
    for (x, y, dx, dy) in [
        (inner, inner, 1, 1),
        (W - inner, inner, -1, 1),
        (inner, H - inner, 1, -1),
        (W - inner, H - inner, -1, -1),
    ]:
        draw.line([(x, y), (x + dx * c, y)], fill=ORO, width=2)
        draw.line([(x, y), (x, y + dy * c)], fill=ORO, width=2)


def _draw_header_band(draw):
    y0, y1 = 70, 155
    draw.rectangle([80, y0, W - 80, y1], fill=(245, 240, 228, 255))
    draw.line([(100, y1), (W - 100, y1)], fill=ORO, width=2)


def _signature(img, path, box):
    if not path or not os.path.isfile(path):
        return
    try:
        sign = Image.open(path).convert("RGBA")
        sign.thumbnail((box[2], box[3]), Image.Resampling.LANCZOS)
        px = box[0] + (box[2] - sign.width) // 2
        py = box[1] + (box[3] - sign.height) // 2
        img.paste(sign, (px, py), sign)
    except Exception as exc:
        print("[certificado] firma:", exc)


def _draw_seal(draw, cx, cy, r=52):
    """Sello circular institucional."""
    for w, col in ((4, ROJO_SELLO), (2, ORO), (1, ROJO_SELLO)):
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=w)
    draw.ellipse([cx - r + 10, cy - r + 10, cx + r - 10, cy + r - 10], outline=ORO, width=1)
    f = _font(11, True)
    t1 = "HOSPITAL"
    t2 = "OFICIAL"
    draw.text((cx - _tw(draw, t1, f) // 2, cy - 14), t1, font=f, fill=ROJO_SELLO)
    draw.text((cx - _tw(draw, t2, f) // 2, cy + 2), t2, font=f, fill=ROJO_SELLO)


def generar_certificado(
    *,
    nombre_receptor,
    titulo,
    hospital="Hospital General",
    emisor="Encargado",
    fecha="",
    numero="",
    descripcion="",
    departamento="",
    capacitacion="",
    cedula="",
    firma_encargado_path=None,
    firma_director_path=None,
    firma_director_zona_path=None,
    label_encargado="Encargado de formación",
    label_director="Dir. Investigación y Docencia",
    label_director_zona="Director de Ala / Departamento",
):
    # Fondo: plantilla o crema profesional
    base = None
    for path in PLANTILLAS:
        if os.path.isfile(path):
            try:
                base = Image.open(path).convert("RGBA")
                break
            except Exception:
                pass

    if base is None:
        img = Image.new("RGBA", (W, H), (*CREMA, 255))
    else:
        img = base.resize((W, H), Image.Resampling.LANCZOS) if base.size != (W, H) else base

    draw = ImageDraw.Draw(img)

    # Si no hay plantilla rica, dibujar marco completo
    if base is None:
        _draw_double_border(draw)
        _draw_header_band(draw)

    # Tipografías
    f_hosp = _font(20, True)
    f_doc = _font(14)
    f_title = _font(28, True)
    f_cert = _font(16)
    f_name = _font(48, True)
    f_body = _font(18)
    f_cap = _font(32, True)
    f_meta = _font(16)
    f_small = _font(13)
    f_label = _font(12)

    # Encabezado
    y = 88
    y += _center(draw, (hospital or "Hospital General").upper(), y, f_hosp, fill=TINTA)
    y += 2
    y += _center(draw, "Dirección de Investigación, Docencia y Desarrollo Profesional", y, f_doc, fill=TINTA_SUAVE)
    y += 8
    # línea ornamentada
    mid = W // 2
    draw.line([(mid - 220, y), (mid + 220, y)], fill=ORO, width=2)
    draw.ellipse([mid - 5, y - 5, mid + 5, y + 5], outline=ORO, width=2)
    y += 22

    y += _center(draw, "CERTIFICADO DE COMPETENCIA", y, f_title, fill=TINTA)
    y += 6
    y += _center(
        draw,
        "Documento oficial de formación hospitalaria · Uso de roleplay",
        y,
        f_small,
        fill=TINTA_SUAVE,
    )
    y += 28

    y += _center(draw, "Por medio del presente se hace constar que",
                 y, f_cert, fill=TINTA_SUAVE)
    y += 16

    # Nombre del graduado destacado
    name = (nombre_receptor or "—").strip()
    y += _center(draw, name, y, f_name, fill=TINTA)
    # subrayado dorado bajo el nombre
    nw = min(_tw(draw, name, f_name) + 40, int(W * 0.7))
    draw.line([((W - nw) // 2, y + 4), ((W + nw) // 2, y + 4)], fill=ORO, width=2)
    y += 22

    if cedula:
        y += _center(draw, f"Identificación / cédula: {cedula}", y, f_meta, fill=TINTA_SUAVE)
        y += 8

    y += _center(
        draw,
        "ha aprobado y completado de forma satisfactoria el programa de certificación:",
        y,
        f_body,
        fill=TINTA_SUAVE,
        max_w=int(W * 0.7),
    )
    y += 14

    cap = f"« {(capacitacion or titulo or 'Certificación').strip()} »"
    y += _center(draw, cap, y, f_cap, fill=TINTA)
    y += 12

    if departamento:
        y += _center(draw, f"Área / departamento: {departamento}", y, f_meta, fill=TINTA_SUAVE)
        y += 6
    if descripcion:
        y += _center(draw, descripcion, y, f_small, fill=TINTA_SUAVE, max_w=int(W * 0.62))
        y += 8

    fecha = fecha or datetime.utcnow().strftime("%d de %B de %Y").replace(
        "January", "enero"
    ).replace("February", "febrero").replace("March", "marzo").replace(
        "April", "abril"
    ).replace("May", "mayo").replace("June", "junio").replace(
        "July", "julio"
    ).replace("August", "agosto").replace("September", "septiembre").replace(
        "October", "octubre"
    ).replace("November", "noviembre").replace("December", "diciembre")
    # fallback simple if English month names remain partially
    if any(m in fecha for m in ("January", "February", "March", "April", "May", "June",
                                  "July", "August", "September", "October", "November", "December")):
        fecha = datetime.utcnow().strftime("%d/%m/%Y")

    numero = numero or "CERT-00000"
    y = max(y + 12, int(H * 0.58))
    y += _center(
        draw,
        f"Expedido el {fecha}    ·    Folio {numero}",
        y,
        f_meta,
        fill=TINTA,
    )
    y += 6
    y += _center(
        draw,
        "Este documento acredita la competencia del titular conforme a los estándares del hospital.",
        y,
        f_small,
        fill=TINTA_SUAVE,
        max_w=int(W * 0.68),
    )

    # Firmas
    boxes = [
        (int(W * 0.08), int(H * 0.72), int(W * 0.24), int(H * 0.11)),
        (int(W * 0.38), int(H * 0.72), int(W * 0.24), int(H * 0.11)),
        (int(W * 0.68), int(H * 0.72), int(W * 0.24), int(H * 0.11)),
    ]
    labels = (label_encargado, label_director, label_director_zona)
    paths = (firma_encargado_path, firma_director_path, firma_director_zona_path)

    for box, path, label in zip(boxes, paths, labels):
        _signature(img, path, box)
        ly = int(H * 0.85)
        draw.line((box[0], ly, box[0] + box[2], ly), fill=ORO, width=1)
        # nombre del firmante bajo línea si no hay imagen
        tw = _tw(draw, label, f_label)
        draw.text((box[0] + (box[2] - tw) // 2, ly + 8), label, font=f_label, fill=TINTA)

    # Sello
    _draw_seal(draw, W - 130, int(H * 0.62), r=48)

    # Pie
    pie = f"{hospital} · Registro de certificaciones · {numero} · Documento generado electrónicamente"
    draw.text(
        ((W - _tw(draw, pie, f_small)) // 2, H - 58),
        pie,
        font=f_small,
        fill=TINTA_SUAVE,
    )

    out = io.BytesIO()
    img.convert("RGB").save(out, "PNG", optimize=True)
    out.seek(0)
    return out
