# -*- coding: utf-8 -*-
"""
certificado_oficial_gen.py — Genera el certificado institucional (plantilla Hospital General).
Todos los campos variables llegan vacíos salvo que se pasen desde el bot (menús Discord).
NO incluye nombres de ejemplo ni placeholders de persona en la imagen final.
"""
from __future__ import annotations

import io
import math
from datetime import datetime
from typing import List, Optional, Sequence

from PIL import Image, ImageDraw, ImageFont

W, H = 1536, 1024

# Paleta institucional (plantilla)
NAVY = (20, 42, 82)
NAVY_DEEP = (12, 28, 58)
GOLD = (184, 148, 58)
GOLD_SOFT = (210, 180, 100)
CREAM = (248, 244, 232)
CREAM_DARK = (238, 230, 210)
INK = (28, 48, 78)
INK_SOFT = (70, 90, 120)
WHITE = (255, 255, 255)
SIDE_BG = (252, 250, 244)


def _font(size: int, bold: bool = False):
    import os

    cands = []
    if bold:
        cands += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    else:
        cands += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    for p in cands:
        if os.path.isfile(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _tw(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    b = draw.textbbox((0, 0), text or "", font=font)
    return max(0, b[2] - b[0])


def _fit_font(draw, text: str, max_w: int, max_size: int, min_size: int = 14, bold: bool = True):
    size = max_size
    while size >= min_size:
        f = _font(size, bold=bold)
        if _tw(draw, text, f) <= max_w:
            return f
        size -= 1
    return _font(min_size, bold=bold)


def _center_text(draw, text: str, y: int, font, fill, max_w: Optional[int] = None):
    text = text or ""
    if not text.strip():
        return 0
    max_w = max_w or int(W * 0.58)
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if _tw(draw, t, font) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    lh = getattr(font, "size", 18) + 8
    for i, line in enumerate(lines):
        x = (W - _tw(draw, line, font)) // 2 - 80  # dejar espacio al panel lateral
        # centrar en zona principal (sin panel derecho ~320px)
        main_w = W - 340
        x = (main_w - _tw(draw, line, font)) // 2 + 40
        draw.text((x, y + i * lh), line, font=font, fill=fill)
    return len(lines) * lh


def _draw_ornament_line(draw, y: int, cx: int, half: int = 180):
    draw.line([(cx - half, y), (cx - 18, y)], fill=GOLD, width=2)
    draw.ellipse([cx - 6, y - 6, cx + 6, y + 6], outline=GOLD, width=2)
    draw.line([(cx + 18, y), (cx + half, y)], fill=GOLD, width=2)


def _draw_caduceus(draw, cx: int, cy: int, scale: float = 1.0):
    """Escudo simplificado caduceo + laureles."""
    s = scale
    # círculo exterior dorado
    r = int(42 * s)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=GOLD, width=3)
    draw.ellipse([cx - r + 5, cy - r + 5, cx + r - 5, cy + r - 5], outline=NAVY, width=2)
    # asta
    draw.line([(cx, cy - int(28 * s)), (cx, cy + int(30 * s))], fill=GOLD, width=3)
    # serpientes (arcos)
    draw.arc(
        [cx - int(22 * s), cy - int(18 * s), cx + int(8 * s), cy + int(18 * s)],
        200, 340, fill=GOLD, width=2,
    )
    draw.arc(
        [cx - int(8 * s), cy - int(18 * s), cx + int(22 * s), cy + int(18 * s)],
        20, 160, fill=GOLD, width=2,
    )
    # alas
    draw.polygon(
        [
            (cx - int(28 * s), cy - int(8 * s)),
            (cx - int(8 * s), cy - int(22 * s)),
            (cx - int(4 * s), cy - int(10 * s)),
        ],
        outline=GOLD,
    )
    draw.polygon(
        [
            (cx + int(28 * s), cy - int(8 * s)),
            (cx + int(8 * s), cy - int(22 * s)),
            (cx + int(4 * s), cy - int(10 * s)),
        ],
        outline=GOLD,
    )
    # estrella
    draw.ellipse([cx - 4, cy - int(32 * s) - 4, cx + 4, cy - int(32 * s) + 4], fill=GOLD)


def _draw_seal(draw, cx: int, cy: int, r: int = 78):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=NAVY_DEEP, outline=GOLD, width=4)
    draw.ellipse([cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8], outline=GOLD, width=2)
    _draw_caduceus(draw, cx, cy - 6, scale=0.85)
    f = _font(11, bold=True)
    t = "HOSPITAL GENERAL"
    tw = _tw(draw, t, f)
    draw.text((cx - tw // 2, cy + 28), t, font=f, fill=GOLD)
    f2 = _font(9)
    t2 = "SALUD · DISCIPLINA · SERVICIO"
    tw2 = _tw(draw, t2, f2)
    draw.text((cx - tw2 // 2, cy + 44), t2, font=f2, fill=GOLD_SOFT)


def generar_certificado_oficial(
    *,
    beneficiarios: Sequence[str],
    director_docencia: str = "",
    director_departamento: str = "",
    encargado_certificados: str = "",
    departamento: str = "",
    cargo: str = "",
    motivo: str = "",
    codigo_certificado: str = "",
    fecha_expedicion: str = "",
    hospital: str = "HOSPITAL GENERAL",
) -> io.BytesIO:
    """
    Genera PNG del certificado.
    Los strings de personas deben venir del bot (menús). Si están vacíos, la zona queda en blanco
    (sin texto de ejemplo).
    """
    img = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(img)

    # Marcos ornamentales
    for i, col in enumerate([NAVY, GOLD, NAVY]):
        m = 18 + i * 5
        draw.rectangle([m, m, W - m, H - m], outline=col, width=2 if i < 2 else 3)
    # esquinas decorativas
    for (x0, y0, x1, y1) in [
        (40, 40, 120, 50), (40, 40, 50, 120),
        (W - 120, 40, W - 40, 50), (W - 50, 40, W - 40, 120),
        (40, H - 50, 120, H - 40), (40, H - 120, 50, H - 40),
        (W - 120, H - 50, W - 40, H - 40), (W - 50, H - 120, W - 40, H - 40),
    ]:
        draw.rectangle([x0, y0, x1, y1], fill=NAVY)

    # Bandas laterales azul marino
    draw.rectangle([0, 0, 28, H], fill=NAVY_DEEP)
    draw.rectangle([W - 28, 0, W, H], fill=NAVY_DEEP)
    draw.rectangle([0, 0, W, 22], fill=NAVY_DEEP)
    draw.rectangle([0, H - 22, W, H], fill=NAVY_DEEP)

    # Marca de agua caduceo
    _draw_caduceus(draw, 280, H // 2 + 20, scale=3.2)
    # suavizar marca de agua: no hay alpha fácil sin capa; dejar fino

    # ── Encabezado ──
    _draw_caduceus(draw, 200, 95, scale=1.15)
    f_hosp = _font(42, bold=True)
    title = (hospital or "HOSPITAL GENERAL").upper()
    main_w = W - 340
    draw.text(
        ((main_w - _tw(draw, title, f_hosp)) // 2 + 40, 70),
        title, font=f_hosp, fill=NAVY,
    )
    f_lema = _font(14)
    lema = "SALUD  ·  DISCIPLINA  ·  SERVICIO"
    draw.text(
        ((main_w - _tw(draw, lema, f_lema)) // 2 + 40, 120),
        lema, font=f_lema, fill=GOLD,
    )

    # Título principal
    f_co = _font(36, bold=True)
    t1 = "CERTIFICADO OFICIAL"
    draw.text(
        ((main_w - _tw(draw, t1, f_co)) // 2 + 40, 165),
        t1, font=f_co, fill=NAVY,
    )
    f_rec = _font(26, bold=True)
    t2 = "DE RECONOCIMIENTO"
    draw.text(
        ((main_w - _tw(draw, t2, f_rec)) // 2 + 40, 210),
        t2, font=f_rec, fill=GOLD,
    )
    _draw_ornament_line(draw, 255, main_w // 2 + 40, half=200)

    # Texto intro
    f_body = _font(15)
    intro = (
        "El Hospital General, por medio de su autoridad institucional, hace constar que:"
    )
    _center_text(draw, intro, 275, f_body, INK_SOFT, max_w=main_w - 100)

    # ── beneficiarios (solo lo seleccionado en Discord) ──
    names = [n.strip() for n in (beneficiarios or []) if (n or "").strip()]
    if names:
        if len(names) == 1:
            block = names[0]
        elif len(names) == 2:
            block = f"{names[0]}  ·  {names[1]}"
        else:
            block = "  ·  ".join(names)
        f_names = _fit_font(draw, block, main_w - 120, max_size=34, min_size=13, bold=True)
        h_names = _center_text(draw, block, 320, f_names, NAVY, max_w=main_w - 100)
    else:
        h_names = 40  # espacio vacío, sin placeholder

    y_after = 320 + max(h_names, 40) + 16
    _draw_ornament_line(draw, y_after, main_w // 2 + 40, half=120)

    cuerpo = (
        "han sido reconocidos oficialmente por su participación, compromiso, desempeño "
        "y contribución dentro de la institución, demostrando responsabilidad, disciplina "
        "y vocación de servicio en el cumplimiento de los objetivos del Hospital General."
    )
    if len(names) == 1:
        cuerpo = (
            "ha sido reconocido(a) oficialmente por su participación, compromiso, desempeño "
            "y contribución dentro de la institución, demostrando responsabilidad, disciplina "
            "y vocación de servicio en el cumplimiento de los objetivos del Hospital General."
        )
    f_c = _font(14)
    h_c = _center_text(draw, cuerpo, y_after + 20, f_c, INK, max_w=main_w - 120)

    cierre = (
        "El presente certificado se expide como constancia oficial de reconocimiento institucional, "
        "para los fines que correspondan dentro de la organización."
    )
    _center_text(draw, cierre, y_after + 20 + h_c + 18, _font(13), INK_SOFT, max_w=main_w - 120)

    # ── Panel lateral DATOS DEL CERTIFICADO ──
    px0, py0, px1, py1 = W - 310, 150, W - 48, 520
    draw.rounded_rectangle([px0, py0, px1, py1], radius=12, outline=GOLD, width=2, fill=SIDE_BG)
    f_side_t = _font(13, bold=True)
    st = "DATOS DEL CERTIFICADO"
    draw.text((px0 + (px1 - px0 - _tw(draw, st, f_side_t)) // 2, py0 + 14), st, font=f_side_t, fill=NAVY)
    draw.line([(px0 + 20, py0 + 38), (px1 - 20, py0 + 38)], fill=GOLD, width=1)

    def side_row(y, label, value):
        fl = _font(11, bold=True)
        fv = _font(12)
        draw.text((px0 + 18, y), label, font=fl, fill=INK_SOFT)
        val = (value or "").strip()
        # sin valor: dejar en blanco (no poner corchetes ni ejemplos)
        if val:
            # wrap
            maxw = px1 - px0 - 36
            words, lines, cur = val.split(), [], ""
            for w in words:
                t = (cur + " " + w).strip()
                if _tw(draw, t, fv) <= maxw:
                    cur = t
                else:
                    if cur:
                        lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)
            for i, ln in enumerate(lines[:3]):
                draw.text((px0 + 18, y + 16 + i * 15), ln, font=fv, fill=NAVY)
            return 16 + max(1, len(lines[:3])) * 15 + 12
        return 34

    yy = py0 + 50
    yy += side_row(yy, "Código del certificado", codigo_certificado)
    yy += side_row(yy, "Fecha de expedición", fecha_expedicion)
    yy += side_row(yy, "Departamento / Ala", departamento)
    yy += side_row(yy, "Cargo / Rango", cargo)
    yy += side_row(yy, "Motivo del reconocimiento", motivo)

    # ── Firmas (solo nombres seleccionados; si vacío, línea en blanco) ──
    fy = H - 175
    slots = [
        (180, director_docencia, "DIRECTOR DE DOCENCIA"),
        (520, director_departamento, "DIRECTOR DEL ALA / DEPARTAMENTO"),
        (860, encargado_certificados, "ENCARGADO DE OTORGAMIENTO\nDE CERTIFICADOS"),
    ]
    f_sig = _font(13, bold=True)
    f_lab = _font(10)
    for cx, nombre, label in slots:
        draw.line([(cx - 110, fy), (cx + 110, fy)], fill=NAVY, width=1)
        nom = (nombre or "").strip()
        if nom:
            fn = _fit_font(draw, nom, 220, 14, 10, bold=True)
            draw.text((cx - _tw(draw, nom, fn) // 2, fy + 8), nom, font=fn, fill=NAVY)
        for i, lab in enumerate(label.split("\n")):
            draw.text(
                (cx - _tw(draw, lab, f_lab) // 2, fy + 30 + i * 12),
                lab, font=f_lab, fill=INK_SOFT,
            )

    # Sello fijo (sin nombre dinámico)
    _draw_seal(draw, W - 130, H - 130, r=72)

    # Pie
    f_pie = _font(10)
    pie = "HOSPITAL GENERAL  ·  DIRECCIÓN INSTITUCIONAL  ·  ADMINISTRACIÓN SUPERIOR"
    draw.text(((main_w - _tw(draw, pie, f_pie)) // 2 + 40, H - 48), pie, font=f_pie, fill=INK_SOFT)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf
