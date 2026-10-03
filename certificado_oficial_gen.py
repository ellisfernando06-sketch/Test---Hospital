# -*- coding: utf-8 -*-
"""
certificado_oficial_gen.py
Certificado institucional Hospital General — texto en español correcto,
sin placeholders de nombres y sin trazos defectuosos.

Prioridad: usar plantilla oficial (assets/certificado_plantilla.jpg|png).
Si no existe, dibuja un diploma limpio con la misma estructura.
"""
from __future__ import annotations

import io
import os
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1536, 1024

NAVY = (18, 38, 78)
NAVY_DEEP = (10, 24, 52)
GOLD = (176, 140, 52)
GOLD_SOFT = (198, 168, 90)
CREAM = (250, 246, 236)
INK = (24, 42, 72)
INK_SOFT = (72, 88, 112)
SIDE_BG = (253, 251, 246)

_ROOT = Path(__file__).resolve().parent
_PLANTILLAS = [
    _ROOT / "assets" / "certificado_plantilla.jpg",
    _ROOT / "assets" / "certificado_plantilla.png",
    _ROOT / "certificado_plantilla.jpg",
    _ROOT / "certificado_plantilla.png",
    Path("/home/workdir/attachments/image.png"),
    Path("/home/workdir/artifacts/certificado_plantilla.jpg"),
]


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if bold:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "C:/Windows/Fonts/timesbd.ttf",
            "C:/Windows/Fonts/georgia.ttf",
        ]
    else:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/times.ttf",
            "C:/Windows/Fonts/georgia.ttf",
        ]
    for p in paths:
        if os.path.isfile(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _tw(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    b = draw.textbbox((0, 0), text or "", font=font)
    return max(0, b[2] - b[0])


def _th(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    b = draw.textbbox((0, 0), text or "", font=font)
    return max(0, b[3] - b[1])


def _fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_w: int,
    max_size: int,
    min_size: int = 12,
    bold: bool = True,
):
    size = max_size
    while size >= min_size:
        f = _font(size, bold=bold)
        if _tw(draw, text, f) <= max_w:
            return f
        size -= 1
    return _font(min_size, bold=bold)


def _wrap(draw, text: str, font, max_w: int) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []
    words = text.split()
    lines: List[str] = []
    cur = ""
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
    return lines


def _center_in_box(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: Tuple[int, int, int, int],
    font,
    fill,
    line_gap: int = 6,
) -> int:
    """Dibuja texto centrado en caja (x0,y0,x1,y1). Devuelve altura usada."""
    x0, y0, x1, y1 = box
    max_w = x1 - x0
    lines = _wrap(draw, text, font, max_w)
    if not lines:
        return 0
    lh = _th(draw, "Áy", font) + line_gap
    total_h = len(lines) * lh - line_gap
    y = y0 + max(0, (y1 - y0 - total_h) // 2)
    for line in lines:
        x = x0 + (max_w - _tw(draw, line, font)) // 2
        draw.text((x, y), line, font=font, fill=fill)
        y += lh
    return total_h


def _limpiar_nombre(s: str) -> str:
    """Quita artefactos; no inventa nombres."""
    s = (s or "").strip()
    # evitar restos de plantilla
    prohibido = (
        "nombre completo",
        "nombres de los beneficiarios",
        "[nombre]",
        "nombre del director",
        "nombre del encargado",
        "beneficiario",
        "________________",
    )
    low = s.lower()
    for p in prohibido:
        if p in low:
            return ""
    return s


def _cargar_plantilla() -> Optional[Image.Image]:
    for p in _PLANTILLAS:
        try:
            if p and Path(p).is_file():
                im = Image.open(p).convert("RGB")
                if im.size != (W, H):
                    im = im.resize((W, H), Image.Resampling.LANCZOS)
                return im
        except Exception:
            continue
    return None


def _dibujar_base_limpia() -> Image.Image:
    """Diploma limpio si no hay plantilla (sin rayones)."""
    img = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(img)

    # marcos limpios (líneas rectas, sin ruido)
    for i, col, w in (
        (14, NAVY_DEEP, 6),
        (26, GOLD, 3),
        (34, NAVY, 2),
    ):
        draw.rectangle([i, i, W - i, H - i], outline=col, width=w)

    # bandas laterales
    draw.rectangle([0, 0, 22, H], fill=NAVY_DEEP)
    draw.rectangle([W - 22, 0, W, H], fill=NAVY_DEEP)
    draw.rectangle([0, 0, W, 16], fill=NAVY_DEEP)
    draw.rectangle([0, H - 16, W, H], fill=NAVY_DEEP)

    main_right = W - 320

    # encabezado
    f_h = _font(40, bold=True)
    t = "HOSPITAL GENERAL"
    draw.text(((main_right - _tw(draw, t, f_h)) // 2 + 30, 58), t, font=f_h, fill=NAVY)
    f_lema = _font(13)
    lema = "SALUD  ·  DISCIPLINA  ·  SERVICIO"
    draw.text(((main_right - _tw(draw, lema, f_lema)) // 2 + 30, 108), lema, font=f_lema, fill=GOLD)

    f_co = _font(34, bold=True)
    t1 = "CERTIFICADO OFICIAL"
    draw.text(((main_right - _tw(draw, t1, f_co)) // 2 + 30, 155), t1, font=f_co, fill=NAVY)
    f_rec = _font(24, bold=True)
    t2 = "DE RECONOCIMIENTO"
    draw.text(((main_right - _tw(draw, t2, f_rec)) // 2 + 30, 200), t2, font=f_rec, fill=GOLD)

    # línea ornamental limpia
    cx = main_right // 2 + 30
    y = 245
    draw.line([(cx - 160, y), (cx - 16, y)], fill=GOLD, width=2)
    draw.ellipse([cx - 5, y - 5, cx + 5, y + 5], outline=GOLD, width=2)
    draw.line([(cx + 16, y), (cx + 160, y)], fill=GOLD, width=2)

    # panel lateral
    px0, py0, px1, py1 = W - 300, 140, W - 40, 500
    draw.rounded_rectangle([px0, py0, px1, py1], radius=10, outline=GOLD, width=2, fill=SIDE_BG)
    f_st = _font(12, bold=True)
    st = "DATOS DEL CERTIFICADO"
    draw.text((px0 + (px1 - px0 - _tw(draw, st, f_st)) // 2, py0 + 12), st, font=f_st, fill=NAVY)
    draw.line([(px0 + 16, py0 + 34), (px1 - 16, py0 + 34)], fill=GOLD, width=1)

    # sello circular simple
    sx, sy, r = W - 120, H - 120, 70
    draw.ellipse([sx - r, sy - r, sx + r, sy + r], outline=GOLD, width=3)
    draw.ellipse([sx - r + 6, sy - r + 6, sx + r - 6, sy + r - 6], outline=NAVY, width=2)
    f_s = _font(10, bold=True)
    for i, line in enumerate(("HOSPITAL", "GENERAL")):
        draw.text((sx - _tw(draw, line, f_s) // 2, sy - 8 + i * 14), line, font=f_s, fill=NAVY)

    return img


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
    Los nombres solo se imprimen si vienen del bot (menús); si faltan, la zona queda en blanco.
    Todo el texto fijo está en español correcto.
    """
    plantilla = _cargar_plantilla()
    if plantilla is not None:
        img = plantilla.copy()
        usar_plantilla = True
    else:
        img = _dibujar_base_limpia()
        usar_plantilla = False

    draw = ImageDraw.Draw(img)

    # --- Beneficiarios (centro) ---
    names = [_limpiar_nombre(n) for n in (beneficiarios or [])]
    names = [n for n in names if n]
    if len(names) == 1:
        bloque = names[0]
        cuerpo_verbo = (
            "ha sido reconocido(a) oficialmente por su participación, compromiso, desempeño "
            "y contribución dentro de la institución, demostrando responsabilidad, disciplina "
            "y vocación de servicio en el cumplimiento de los objetivos del Hospital General."
        )
    elif names:
        bloque = "  ·  ".join(names)
        cuerpo_verbo = (
            "han sido reconocidos oficialmente por su participación, compromiso, desempeño "
            "y contribución dentro de la institución, demostrando responsabilidad, disciplina "
            "y vocación de servicio en el cumplimiento de los objetivos del Hospital General."
        )
    else:
        bloque = ""
        cuerpo_verbo = ""

    # Caja de nombres (zona central de la plantilla)
    name_box = (80, 300, W - 340, 400)
    if bloque:
        f_names = _fit_font(draw, bloque, name_box[2] - name_box[0] - 20, 36, 14, bold=True)
        # si hay plantilla, cubrir suavemente el área de placeholder con rectángulo crema semi
        if usar_plantilla:
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            od.rectangle([name_box[0], name_box[1] - 8, name_box[2], name_box[3] + 8], fill=(250, 246, 236, 230))
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
            draw = ImageDraw.Draw(img)
        _center_in_box(draw, bloque, name_box, f_names, NAVY, line_gap=8)

    # Intro y cuerpo solo si no hay plantilla (la plantilla ya los trae bien escritos)
    if not usar_plantilla:
        f_body = _font(15)
        intro = "El Hospital General, por medio de su autoridad institucional, hace constar que:"
        _center_in_box(draw, intro, (80, 260, W - 340, 295), f_body, INK_SOFT, line_gap=4)
        if cuerpo_verbo:
            _center_in_box(draw, cuerpo_verbo, (80, 410, W - 340, 520), _font(14), INK, line_gap=5)
        cierre = (
            "El presente certificado se expide como constancia oficial de reconocimiento "
            "institucional, para los fines que correspondan dentro de la organización."
        )
        _center_in_box(draw, cierre, (80, 530, W - 340, 590), _font(13), INK_SOFT, line_gap=4)

    # --- Panel lateral: solo valores reales (español correcto en etiquetas de base) ---
    # Coordenadas alineadas a la plantilla
    side_x0, side_x1 = W - 290, W - 48
    side_y = 200
    f_lab = _font(11, bold=True)
    f_val = _font(13)

    def side_pair(label: str, value: str, y: int) -> int:
        value = (value or "").strip()
        if usar_plantilla:
            # cubrir valor de plantilla y escribir limpio
            draw.rectangle([side_x0, y + 14, side_x1 - 4, y + 48], fill=SIDE_BG)
        else:
            draw.text((side_x0, y), label, font=f_lab, fill=INK_SOFT)
        if value:
            lines = _wrap(draw, value, f_val, side_x1 - side_x0 - 8)
            yy = y + (16 if not usar_plantilla else 16)
            for ln in lines[:3]:
                draw.text((side_x0 + 2, yy), ln, font=f_val, fill=NAVY)
                yy += 16
            return yy + 8
        return y + 52

    # En plantilla las etiquetas ya están; solo valores
    y = side_y
    if not usar_plantilla:
        y = side_pair("Código del certificado", codigo_certificado, y)
        y = side_pair("Fecha de expedición", fecha_expedicion, y)
        y = side_pair("Departamento / Ala", departamento, y)
        y = side_pair("Cargo / Rango", cargo, y)
        y = side_pair("Motivo del reconocimiento", motivo, y)
    else:
        # posiciones aproximadas del panel de la imagen oficial
        slots = [
            (188, codigo_certificado),
            (248, fecha_expedicion),
            (308, departamento),
            (368, cargo),
            (428, motivo),
        ]
        for sy, val in slots:
            val = (val or "").strip()
            draw.rectangle([side_x0 - 4, sy, side_x1, sy + 36], fill=SIDE_BG)
            if val:
                fv = _fit_font(draw, val, side_x1 - side_x0 - 6, 14, 10, bold=False)
                for i, ln in enumerate(_wrap(draw, val, fv, side_x1 - side_x0 - 6)[:2]):
                    draw.text((side_x0, sy + 4 + i * 15), ln, font=fv, fill=NAVY)

    # --- Firmas (solo nombres seleccionados; español en cargos ya en plantilla) ---
    firmas = [
        (200, _limpiar_nombre(director_docencia)),
        (540, _limpiar_nombre(director_departamento)),
        (880, _limpiar_nombre(encargado_certificados)),
    ]
    fy = H - 168
    for cx, nom in firmas:
        if not nom:
            continue
        # limpiar zona de nombre sobre la línea
        draw.rectangle([cx - 120, fy + 4, cx + 120, fy + 28], fill=CREAM if not usar_plantilla else (248, 244, 232))
        fn = _fit_font(draw, nom, 230, 15, 10, bold=True)
        draw.text((cx - _tw(draw, nom, fn) // 2, fy + 6), nom, font=fn, fill=NAVY)

    if not usar_plantilla:
        # etiquetas de cargo en español correcto
        f_lab2 = _font(9)
        cargos = [
            (200, "DIRECTOR DE DOCENCIA"),
            (540, "DIRECTOR DEL ALA / DEPARTAMENTO"),
            (880, "ENCARGADO DE OTORGAMIENTO"),
        ]
        for cx, lab in cargos:
            draw.line([(cx - 110, fy), (cx + 110, fy)], fill=NAVY, width=1)
            draw.text((cx - _tw(draw, lab, f_lab2) // 2, fy + 32), lab, font=f_lab2, fill=INK_SOFT)
        pie = "HOSPITAL GENERAL  ·  DIRECCIÓN INSTITUCIONAL  ·  ADMINISTRACIÓN SUPERIOR"
        fp = _font(10)
        draw.text(((W - 320 - _tw(draw, pie, fp)) // 2 + 30, H - 42), pie, font=fp, fill=INK_SOFT)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf
