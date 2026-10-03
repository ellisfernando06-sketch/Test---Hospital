# -*- coding: utf-8 -*-
"""
certificado_oficial_gen.py
Diploma institucional: plantilla oficial + firmas registradas SOBRE las rayas.
"""
from __future__ import annotations

import io
import os
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

from PIL import Image, ImageDraw, ImageFont

W, H = 1536, 1024

NAVY = (18, 38, 78)
NAVY_DEEP = (10, 24, 52)
GOLD = (176, 140, 52)
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
]

# Centros de las 3 rayas de firma (plantilla 1536×1024)
# (centro_x, y_linea) — la imagen de firma se coloca ENCIMA de la raya
_FIRMAS_SLOTS = (
    (255, 868),   # Director de Docencia
    (620, 868),   # Director del Ala / Departamento
    (985, 868),   # Encargado de Otorgamiento
)
_FIRMA_MAX_W = 220
_FIRMA_MAX_H = 70


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
    prohibido = (
        "nombre completo",
        "nombres de los beneficiarios",
        "[nombre]",
        "nombre del director",
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
            if p.is_file():
                im = Image.open(p).convert("RGB")
                if im.size != (W, H):
                    im = im.resize((W, H), Image.Resampling.LANCZOS)
                return im
        except Exception:
            continue
    return None


def _abrir_firma(src: Optional[Union[str, Path, bytes, Image.Image]]) -> Optional[Image.Image]:
    """Carga una firma registrada (archivo, bytes o imagen)."""
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
        # eliminar fondo casi blanco para que se vea como firma real sobre el diploma
        pixels = im.load()
        w, h = im.size
        for y in range(h):
            for x in range(w):
                r, g, b, a = pixels[x, y]
                if r > 245 and g > 245 and b > 245:
                    pixels[x, y] = (r, g, b, 0)
        # escalar manteniendo proporción
        im.thumbnail((_FIRMA_MAX_W, _FIRMA_MAX_H), Image.Resampling.LANCZOS)
        return im
    except Exception:
        return None


def _pegar_firma(base: Image.Image, firma: Image.Image, cx: int, y_linea: int) -> None:
    """Coloca la firma centrada SOBRE la raya (no el nombre debajo)."""
    fw, fh = firma.size
    x = int(cx - fw / 2)
    y = int(y_linea - fh - 4)  # justo encima de la línea
    if base.mode != "RGBA":
        base_rgba = base.convert("RGBA")
        base_rgba.paste(firma, (x, y), firma)
        base.paste(base_rgba.convert("RGB"))
    else:
        base.paste(firma, (x, y), firma)


def _dibujar_base_limpia() -> Image.Image:
    img = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(img)
    for i, col, w in ((12, NAVY_DEEP, 5), (22, GOLD, 3), (30, NAVY, 2)):
        draw.rectangle([i, i, W - i, H - i], outline=col, width=w)

    main_right = W - 320
    f_h = _font(42, bold=True)
    t = "HOSPITAL GENERAL"
    draw.text(((main_right - _tw(draw, t, f_h)) // 2 + 40, 55), t, font=f_h, fill=NAVY)
    f_lema = _font(14)
    lema = "SALUD  ·  DISCIPLINA  ·  SERVICIO"
    draw.text(((main_right - _tw(draw, lema, f_lema)) // 2 + 40, 108), lema, font=f_lema, fill=GOLD)
    f_co = _font(32, bold=True)
    t1 = "CERTIFICADO OFICIAL"
    draw.text(((main_right - _tw(draw, t1, f_co)) // 2 + 40, 150), t1, font=f_co, fill=NAVY)
    f_rec = _font(22, bold=True)
    t2 = "DE RECONOCIMIENTO"
    draw.text(((main_right - _tw(draw, t2, f_rec)) // 2 + 40, 195), t2, font=f_rec, fill=GOLD)

    cx = main_right // 2 + 40
    y = 240
    draw.line([(cx - 150, y), (cx - 14, y)], fill=GOLD, width=2)
    draw.ellipse([cx - 5, y - 5, cx + 5, y + 5], outline=GOLD, width=2)
    draw.line([(cx + 14, y), (cx + 150, y)], fill=GOLD, width=2)

    # panel lateral
    px0, py0, px1, py1 = W - 295, 130, W - 38, 490
    draw.rounded_rectangle([px0, py0, px1, py1], radius=8, outline=GOLD, width=2, fill=SIDE_BG)
    f_st = _font(11, bold=True)
    st = "DATOS DEL CERTIFICADO"
    draw.text((px0 + (px1 - px0 - _tw(draw, st, f_st)) // 2, py0 + 14), st, font=f_st, fill=NAVY)
    draw.line([(px0 + 14, py0 + 36), (px1 - 14, py0 + 36)], fill=GOLD, width=1)

    # rayas de firma
    f_lab = _font(9)
    cargos = (
        "DIRECTOR DE DOCENCIA",
        "DIRECTOR DEL ALA / DEPARTAMENTO",
        "ENCARGADO DE OTORGAMIENTO",
    )
    for (cx, yl), lab in zip(_FIRMAS_SLOTS, cargos):
        draw.line([(cx - 110, yl), (cx + 110, yl)], fill=NAVY, width=1)
        draw.text((cx - _tw(draw, lab, f_lab) // 2, yl + 8), lab, font=f_lab, fill=INK_SOFT)

    # sello
    sx, sy, r = W - 115, H - 115, 58
    draw.ellipse([sx - r, sy - r, sx + r, sy + r], outline=GOLD, width=3)
    draw.ellipse([sx - r + 5, sy - r + 5, sx + r - 5, sy + r - 5], outline=NAVY, width=2)
    f_s = _font(9, bold=True)
    for i, line in enumerate(("HOSPITAL", "GENERAL")):
        draw.text((sx - _tw(draw, line, f_s) // 2, sy - 6 + i * 13), line, font=f_s, fill=NAVY)

    pie = "HOSPITAL GENERAL  ·  DIRECCIÓN INSTITUCIONAL  ·  ADMINISTRACIÓN SUPERIOR"
    fp = _font(10)
    draw.text(((W - 320 - _tw(draw, pie, fp)) // 2 + 40, H - 36), pie, font=fp, fill=INK_SOFT)
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
    firma_docencia: Optional[Union[str, Path, bytes, Image.Image]] = None,
    firma_departamento: Optional[Union[str, Path, bytes, Image.Image]] = None,
    firma_encargado: Optional[Union[str, Path, bytes, Image.Image]] = None,
) -> io.BytesIO:
    """
    Genera el diploma.
    Las firmas registradas se dibujan SOBRE cada raya (no el nombre debajo).
    """
    _ensure_assets()
    plantilla = _cargar_plantilla()
    usar = plantilla is not None
    img = plantilla.copy() if usar else _dibujar_base_limpia()
    draw = ImageDraw.Draw(img)

    # Beneficiarios
    names = [_limpiar_nombre(n) for n in (beneficiarios or [])]
    names = [n for n in names if n]
    bloque = names[0] if len(names) == 1 else ("  ·  ".join(names) if names else "")
    name_box = (90, 295, W - 340, 395)
    if bloque:
        if usar:
            # cubrir zona de placeholder de la plantilla
            draw.rectangle(
                [name_box[0], name_box[1] - 6, name_box[2], name_box[3] + 6],
                fill=(250, 246, 236),
            )
        f_names = _fit_font(draw, bloque, name_box[2] - name_box[0] - 16, 34, 13, bold=True)
        _center_in_box(draw, bloque, name_box, f_names, NAVY, line_gap=8)

    if not usar:
        intro = "El Hospital General, por medio de su autoridad institucional, hace constar que:"
        _center_in_box(draw, intro, (90, 255, W - 340, 290), _font(14), INK_SOFT, line_gap=4)
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
            _center_in_box(draw, cuerpo, (90, 405, W - 340, 510), _font(14), INK, line_gap=5)
        cierre = (
            "El presente certificado se expide como constancia oficial de reconocimiento "
            "institucional, para los fines que correspondan dentro de la organización."
        )
        _center_in_box(draw, cierre, (90, 520, W - 340, 575), _font(13), INK_SOFT, line_gap=4)

    # Panel lateral (valores)
    side_x0, side_x1 = W - 285, W - 48
    f_val = _font(13)
    slots = [
        (188, codigo_certificado),
        (248, fecha_expedicion),
        (308, departamento),
        (368, cargo),
        (428, motivo),
    ]
    if usar:
        for sy, val in slots:
            val = (val or "").strip()
            draw.rectangle([side_x0 - 2, sy, side_x1, sy + 34], fill=SIDE_BG)
            if val:
                fv = _fit_font(draw, val, side_x1 - side_x0 - 6, 14, 10, bold=False)
                for i, ln in enumerate(_wrap(draw, val, fv, side_x1 - side_x0 - 6)[:2]):
                    draw.text((side_x0, sy + 4 + i * 15), ln, font=fv, fill=NAVY)
    else:
        labels = (
            "Código del certificado",
            "Fecha de expedición",
            "Departamento / Ala",
            "Cargo / Rango",
            "Motivo del reconocimiento",
        )
        f_lab = _font(10, bold=True)
        y = 180
        for lab, (_, val) in zip(labels, slots):
            draw.text((side_x0, y), lab, font=f_lab, fill=INK_SOFT)
            val = (val or "").strip()
            if val:
                for i, ln in enumerate(_wrap(draw, val, f_val, side_x1 - side_x0)[:2]):
                    draw.text((side_x0, y + 16 + i * 15), ln, font=f_val, fill=NAVY)
            y += 55

    # Firmas registradas SOBRE las rayas
    firmas_src = (firma_docencia, firma_departamento, firma_encargado)
    # si no hay imagen, no escribimos el nombre en la raya (queda lista para firmar)
    for (cx, yl), src in zip(_FIRMAS_SLOTS, firmas_src):
        im_f = _abrir_firma(src)
        if im_f is not None:
            # cubrir zona por encima de la raya para no superponer texto de plantilla
            draw.rectangle(
                [cx - 115, yl - _FIRMA_MAX_H - 6, cx + 115, yl - 2],
                fill=CREAM if not usar else (248, 244, 232),
            )
            _pegar_firma(img, im_f, cx, yl)
            draw = ImageDraw.Draw(img)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf


def resolver_ruta_firma_usuario(uid: int) -> Optional[str]:
    """Obtiene la ruta de la firma registrada de un usuario (módulo firmas)."""
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
