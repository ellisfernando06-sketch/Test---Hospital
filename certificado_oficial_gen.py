# -*- coding: utf-8 -*-
"""
certificado_oficial_gen.py
Diploma institucional Hospital General.
- Diseño profesional integrado (no hace falta subir JPG a mano).
- Si existe assets/certificado_plantilla.jpg, se usa como base.
- Firmas registradas se colocan SOBRE cada raya.
"""
from __future__ import annotations

import io
import math
import os
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1536, 1024

NAVY = (18, 38, 78)
NAVY_DEEP = (12, 28, 58)
GOLD = (184, 148, 58)
GOLD_SOFT = (210, 180, 100)
CREAM = (252, 248, 238)
CREAM2 = (248, 244, 232)
INK = (28, 48, 78)
INK_SOFT = (90, 105, 130)
SIDE_BG = (255, 252, 246)

_ROOT = Path(__file__).resolve().parent
_PLANTILLAS = [
    _ROOT / "assets" / "certificado_plantilla.jpg",
    _ROOT / "assets" / "certificado_plantilla.png",
]

# Centros de las 3 rayas (x, y_linea)
_FIRMAS_SLOTS = ((280, 875), (640, 875), (1000, 875))
_FIRMA_MAX_W, _FIRMA_MAX_H = 230, 72


def _ensure_assets() -> None:
    try:
        import cert_plantilla_install

        cert_plantilla_install.ensure_plantilla()
    except Exception:
        pass


def _font(size: int, bold: bool = False):
    paths = (
        [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        if bold
        else [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    )
    for p in paths:
        if os.path.isfile(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _tw(draw, text, font) -> int:
    b = draw.textbbox((0, 0), text or "", font=font)
    return max(0, b[2] - b[0])


def _th(draw, text, font) -> int:
    b = draw.textbbox((0, 0), text or "", font=font)
    return max(0, b[3] - b[1])


def _fit_font(draw, text, max_w, max_size, min_size=12, bold=True):
    size = max_size
    while size >= min_size:
        f = _font(size, bold=bold)
        if _tw(draw, text, f) <= max_w:
            return f
        size -= 1
    return _font(min_size, bold=bold)


def _wrap(draw, text, font, max_w) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []
    words, lines, cur = text.split(), [], ""
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


def _center_text(draw, text, cx, y, font, fill):
    draw.text((cx - _tw(draw, text, font) // 2, y), text, font=font, fill=fill)


def _center_in_box(draw, text, box, font, fill, line_gap=6) -> int:
    x0, y0, x1, y1 = box
    max_w = x1 - x0
    lines = _wrap(draw, text, font, max_w)
    if not lines:
        return 0
    lh = _th(draw, "Ay", font) + line_gap
    total_h = len(lines) * lh - line_gap
    y = y0 + max(0, (y1 - y0 - total_h) // 2)
    for line in lines:
        x = x0 + (max_w - _tw(draw, line, font)) // 2
        draw.text((x, y), line, font=font, fill=fill)
        y += lh
    return total_h


def _limpiar_nombre(s: str) -> str:
    s = (s or "").strip()
    for p in (
        "nombre completo",
        "nombres de los beneficiarios",
        "[nombre]",
        "________________",
    ):
        if p in s.lower():
            return ""
    return s


def _cargar_plantilla() -> Optional[Image.Image]:
    for p in _PLANTILLAS:
        try:
            if p.is_file() and p.stat().st_size > 20000:
                im = Image.open(p).convert("RGB")
                if im.size != (W, H):
                    im = im.resize((W, H), Image.Resampling.LANCZOS)
                return im
        except Exception:
            continue
    return None


def _escudo(draw, cx, cy, r=38):
    """Escudo médico simple."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=GOLD, width=3)
    draw.ellipse([cx - r + 5, cy - r + 5, cx + r - 5, cy + r - 5], outline=NAVY, width=2)
    # cruz
    w, h = 8, 22
    draw.rectangle([cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2], fill=NAVY)
    draw.rectangle([cx - h // 2, cy - w // 2, cx + h // 2, cy + w // 2], fill=NAVY)


def _dibujar_diploma_profesional() -> Image.Image:
    """Diploma completo estilo institucional (reemplaza la plantilla si no está)."""
    img = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(img)

    # Marcos dobles elegantes
    for i, col, wd in ((10, NAVY_DEEP, 6), (20, GOLD, 3), (28, NAVY, 1)):
        draw.rectangle([i, i, W - i - 1, H - i - 1], outline=col, width=wd)

    # Franja superior e inferior navy
    draw.rectangle([28, 28, W - 29, 48], fill=NAVY_DEEP)
    draw.rectangle([28, H - 48, W - 29, H - 29], fill=NAVY_DEEP)

    main_right = W - 310
    cx_main = main_right // 2 + 20

    # Escudo
    _escudo(draw, cx_main, 95, 36)

    # Encabezado
    _center_text(draw, "HOSPITAL GENERAL", cx_main, 140, _font(36, True), NAVY)
    _center_text(draw, "SALUD  ·  DISCIPLINA  ·  SERVICIO", cx_main, 185, _font(13), GOLD)

    # Ornamento
    y = 215
    draw.line([(cx_main - 160, y), (cx_main - 16, y)], fill=GOLD, width=2)
    draw.ellipse([cx_main - 5, y - 5, cx_main + 5, y + 5], outline=GOLD, width=2)
    draw.line([(cx_main + 16, y), (cx_main + 160, y)], fill=GOLD, width=2)

    _center_text(draw, "CERTIFICADO OFICIAL", cx_main, 235, _font(30, True), NAVY)
    _center_text(draw, "DE RECONOCIMIENTO", cx_main, 275, _font(20, True), GOLD)

    # Intro
    intro = "El Hospital General, por medio de su autoridad institucional, hace constar que:"
    _center_in_box(draw, intro, (70, 320, main_right - 20, 355), _font(14), INK_SOFT, 4)

    # Cuerpo (se rellena después con nombres)
    # Panel lateral
    px0, py0, px1, py1 = W - 290, 120, W - 40, 500
    draw.rounded_rectangle([px0, py0, px1, py1], radius=10, outline=GOLD, width=2, fill=SIDE_BG)
    st = "DATOS DEL CERTIFICADO"
    f_st = _font(11, True)
    draw.text((px0 + (px1 - px0 - _tw(draw, st, f_st)) // 2, py0 + 14), st, font=f_st, fill=NAVY)
    draw.line([(px0 + 16, py0 + 38), (px1 - 16, py0 + 38)], fill=GOLD, width=1)

    # Rayas de firma + cargos
    f_lab = _font(9)
    cargos = (
        "DIRECTOR DE DOCENCIA",
        "DIRECTOR DEL ALA / DEPARTAMENTO",
        "ENCARGADO DE OTORGAMIENTO",
    )
    for (cx, yl), lab in zip(_FIRMAS_SLOTS, cargos):
        draw.line([(cx - 115, yl), (cx + 115, yl)], fill=NAVY, width=1)
        _center_text(draw, lab, cx, yl + 10, f_lab, INK_SOFT)

    # Sello circular
    sx, sy, r = W - 120, H - 120, 62
    draw.ellipse([sx - r, sy - r, sx + r, sy + r], outline=GOLD, width=3)
    draw.ellipse([sx - r + 6, sy - r + 6, sx + r - 6, sy + r - 6], outline=NAVY, width=2)
    f_s = _font(10, True)
    _center_text(draw, "HOSPITAL", sx, sy - 12, f_s, NAVY)
    _center_text(draw, "GENERAL", sx, sy + 4, f_s, NAVY)

    pie = "HOSPITAL GENERAL  ·  DIRECCIÓN INSTITUCIONAL  ·  ADMINISTRACIÓN SUPERIOR"
    _center_text(draw, pie, cx_main, H - 70, _font(10), INK_SOFT)

    return img


def _abrir_firma(src: Optional[Union[str, Path, bytes, Image.Image]]) -> Optional[Image.Image]:
    if src is None:
        return None
    try:
        if isinstance(src, Image.Image):
            im = src.convert("RGBA")
        elif isinstance(src, (bytes, bytearray)):
            im = Image.open(io.BytesIO(src)).convert("RGBA")
        else:
            p = Path(str(src))
            if not p.is_file():
                return None
            im = Image.open(p).convert("RGBA")
        px = im.load()
        w, h = im.size
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if r > 242 and g > 242 and b > 242:
                    px[x, y] = (r, g, b, 0)
        im.thumbnail((_FIRMA_MAX_W, _FIRMA_MAX_H), Image.Resampling.LANCZOS)
        return im
    except Exception:
        return None


def _pegar_firma(base: Image.Image, firma: Image.Image, cx: int, y_linea: int) -> Image.Image:
    fw, fh = firma.size
    x = int(cx - fw / 2)
    y = int(y_linea - fh - 6)
    base = base.convert("RGBA")
    base.paste(firma, (x, y), firma)
    return base.convert("RGB")


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
    firma_docencia=None,
    firma_departamento=None,
    firma_encargado=None,
) -> io.BytesIO:
    _ensure_assets()
    plantilla = _cargar_plantilla()
    if plantilla is not None:
        img = plantilla.copy()
        usar = True
    else:
        img = _dibujar_diploma_profesional()
        usar = False

    draw = ImageDraw.Draw(img)
    main_right = W - 310

    # Beneficiarios
    names = [_limpiar_nombre(n) for n in (beneficiarios or [])]
    names = [n for n in names if n]
    bloque = names[0] if len(names) == 1 else ("  ·  ".join(names) if names else "")

    name_box = (80, 360, main_right - 30, 430)
    if bloque:
        draw.rectangle(
            [name_box[0], name_box[1] - 4, name_box[2], name_box[3] + 4],
            fill=CREAM2,
        )
        f_n = _fit_font(draw, bloque, name_box[2] - name_box[0] - 20, 32, 14, bold=True)
        _center_in_box(draw, bloque, name_box, f_n, NAVY, 8)

    # Texto cuerpo
    if names:
        cuerpo = (
            "ha sido reconocido(a) oficialmente por su participación, compromiso, desempeño "
            "y contribución dentro de la institución, demostrando responsabilidad, disciplina "
            "y vocación de servicio en el cumplimiento de los objetivos del Hospital General."
            if len(names) == 1
            else (
                "han sido reconocidos oficialmente por su participación, compromiso, desempeño "
                "y contribución dentro de la institución, demostrando responsabilidad, disciplina "
                "y vocación de servicio en el cumplimiento de los objetivos del Hospital General."
            )
        )
        if not usar:
            _center_in_box(
                draw, cuerpo, (80, 445, main_right - 30, 545), _font(14), INK, 5
            )
            cierre = (
                "El presente certificado se expide como constancia oficial de reconocimiento "
                "institucional, para los fines que correspondan dentro de la organización."
            )
            _center_in_box(
                draw, cierre, (80, 555, main_right - 30, 610), _font(13), INK_SOFT, 4
            )

    # Panel lateral valores
    side_x0, side_x1 = W - 275, W - 50
    f_lab = _font(10, True)
    f_val = _font(13)
    campos = [
        ("Código del certificado", codigo_certificado),
        ("Fecha de expedición", fecha_expedicion),
        ("Departamento / Ala", departamento),
        ("Cargo / Rango", cargo),
        ("Motivo del reconocimiento", motivo),
    ]
    y = 175
    for lab, val in campos:
        draw.rectangle([side_x0 - 4, y - 2, side_x1 + 4, y + 48], fill=SIDE_BG)
        draw.text((side_x0, y), lab, font=f_lab, fill=INK_SOFT)
        val = (val or "").strip()
        if val:
            fv = _fit_font(draw, val, side_x1 - side_x0, 14, 10, bold=False)
            for i, ln in enumerate(_wrap(draw, val, fv, side_x1 - side_x0)[:2]):
                draw.text((side_x0, y + 16 + i * 15), ln, font=fv, fill=NAVY)
        y += 58

    # Firmas SOBRE las rayas
    for (cx, yl), src in zip(
        _FIRMAS_SLOTS, (firma_docencia, firma_departamento, firma_encargado)
    ):
        im_f = _abrir_firma(src)
        if im_f is not None:
            draw.rectangle(
                [cx - 120, yl - _FIRMA_MAX_H - 8, cx + 120, yl - 2],
                fill=CREAM2,
            )
            img = _pegar_firma(img, im_f, cx, yl)
            draw = ImageDraw.Draw(img)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf


def resolver_ruta_firma_usuario(uid: int) -> Optional[str]:
    try:
        import firmas

        info = firmas.obtener_firma_usuario(int(uid))
        if not info:
            return None
        fname = info.get("file") or info.get("filename")
        if not fname:
            return None
        path = firmas.ruta_firma(fname)
        if path and os.path.isfile(path):
            return path
    except Exception:
        pass
    return None
