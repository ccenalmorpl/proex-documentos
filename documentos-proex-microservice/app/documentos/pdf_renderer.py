import io
import logging
import os
from typing import Dict, List, Optional

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter

logger = logging.getLogger(__name__)

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
ORIGEN_BORRADOR_TEMPLATE = os.path.join(TEMPLATES_DIR, "origen_borrador_plantilla.pdf")
SANITARIO_TEMPLATE       = os.path.join(TEMPLATES_DIR, "sanitario_plantilla.pdf")

# A4 = 595x842 pt, origen bottom-left, y = borde superior de la caja.
LAYOUT: Dict[str, dict] = {
    "expeditor":     {"x": 75,  "y": 780, "w": 235, "h": 45,  "font": "Helvetica", "size": 8, "leading": 10},
    "destinatario":  {"x": 75, "y": 710, "w": 235, "h": 95,  "font": "Helvetica", "size": 8, "leading": 10},
    "pais_origen":   {"x": 325,  "y": 635, "w": 235, "h": 20,  "font": "Helvetica", "size": 8, "leading": 10},
    "transporte":    {"x": 75, "y": 570, "w": 235, "h": 55,  "font": "Helvetica", "size": 8, "leading": 10},
    "observaciones": {"x": 325, "y": 590, "w": 235, "h": 75,  "font": "Helvetica", "size": 8, "leading": 10},
    "mercancias":    {"x": 75,  "y": 430, "w": 360, "h": 205, "font": "Helvetica", "size": 8, "leading": 10},
    "cantidad":      {"x": 450, "y": 430, "w": 110, "h": 205, "font": "Helvetica", "size": 8, "leading": 10},
}


def _draw_text_in_box(
    c: canvas.Canvas,
    text: str,
    box: dict,
    debug_label: Optional[str] = None,
) -> None:
    """Dibuja texto en la caja con word-wrap y clip vertical. Si debug_label, dibuja un rectángulo de calibración."""
    x      = box["x"]
    y_top  = box["y"]
    w      = box["w"]
    h      = box["h"]
    font   = box.get("font", "Helvetica")
    size   = box.get("size", 8)
    leading = box.get("leading", 10)

    if debug_label is not None:
        c.saveState()
        c.setStrokeColorRGB(1, 0, 0)
        c.setLineWidth(0.5)
        c.rect(x, y_top - h, w, h, stroke=1, fill=0)
        c.setFillColorRGB(1, 0, 0)
        c.setFont("Helvetica", 5)
        c.drawString(x + 2, y_top - 7, debug_label)
        c.restoreState()

    if not text:
        return

    c.setFont(font, size)
    color = box.get("color")
    if color:
        r, g, b = color
        c.setFillColorRGB(r / 255, g / 255, b / 255)
    else:
        c.setFillColorRGB(0, 0, 0)

    if box.get("single_line"):
        single = text.replace("\n", "  ").strip()
        c.drawString(x, y_top - leading, single)
        return

    raw_lines = text.split("\n")
    wrapped: List[str] = []
    for raw in raw_lines:
        words = raw.split(" ") if raw.strip() else [""]
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip() if line else word
            if pdfmetrics.stringWidth(candidate, font, size) <= w:
                line = candidate
            else:
                if line:
                    wrapped.append(line)
                line = word
        wrapped.append(line)

    y_bottom = y_top - h
    y_cursor = y_top - leading
    for line in wrapped:
        if y_cursor < y_bottom:
            break
        c.drawString(x, y_cursor, line)
        y_cursor -= leading


def _strip_container_names(line: str, nombres: List[str]) -> str:
    for nombre in nombres:
        line = line.replace(nombre + " - ", "")
        line = line.replace(nombre, "")
    return line.strip()


def render_origen_borrador_v2(payload: dict, debug: bool = False) -> bytes:
    """Genera el PDF origen_borrador (overlay ReportLab sobre la plantilla)."""
    totales = payload.get("totales", {})
    _tp = payload.get("totales_pdf", {})
    _contenedores = payload.get("contenedores", {})
    _nombres = _contenedores.get("nombres", [])
    _mercancias_text = payload.get("mercancias_text", "")
    _neto_fallback   = "NET " + str(totales.get("total_peso_neto", 0)) + " KG"
    _bruto_fallback  = "GROSS " + str(totales.get("total_peso_bruto", 0)) + " KG"
    _cantidad_text = (
        f"{_tp.get('cases_line', str(totales.get('total_cases', 0)))}\n"
        f"\n"
        f"{_tp.get('net_line', _neto_fallback)}\n"
        f"\n"
        f"{_tp.get('gross_line', _bruto_fallback)}"
    )
    texts = {
        "expeditor":     payload.get("expedidor", ""),
        "destinatario":  payload.get("consignee") or "",
        "pais_origen":   payload.get("pais_origen", ""),
        "transporte":    "\n".join([
            payload.get("transporte", ""),
            _contenedores.get("resumen_texto", ""),
            " ".join(_nombres),
        ]),
        "observaciones": payload.get("observaciones", ""),
        "mercancias":    _mercancias_text,
        "cantidad":      _cantidad_text,
    }

    logger.info(
        f"[PDF_V2_FILL] expeditor={texts['expeditor'][:30]!r} "
        f"mercancias_lines={len(texts['mercancias'].splitlines())} "
        f"debug={debug}"
    )

    buf_overlay = io.BytesIO()
    c = canvas.Canvas(buf_overlay, pagesize=A4)

    for field_name, box in LAYOUT.items():
        text = texts.get(field_name, "")
        label = field_name if debug else None
        _draw_text_in_box(c, text, box, debug_label=label)

    c.save()
    buf_overlay.seek(0)
    logger.info(f"[PDF_V2_OVERLAY_READY] size={buf_overlay.getbuffer().nbytes} bytes")

    reader_template = PdfReader(ORIGEN_BORRADOR_TEMPLATE)
    reader_overlay  = PdfReader(buf_overlay)

    base_page    = reader_template.pages[0]
    overlay_page = reader_overlay.pages[0]
    base_page.merge_page(overlay_page)

    writer = PdfWriter()
    writer.add_page(base_page)

    buf_final = io.BytesIO()
    writer.write(buf_final)
    pdf_bytes = buf_final.getvalue()

    logger.info(f"[PDF_V2_MERGED] size={len(pdf_bytes)} bytes debug={debug}")
    return pdf_bytes


def render_origen_final_v2(payload: dict, debug: bool = False) -> bytes:
    """Genera el PDF origen_final sobre A4 blanco (sin plantilla de fondo)."""
    totales = payload.get("totales", {})
    _tp = payload.get("totales_pdf", {})
    _contenedores = payload.get("contenedores", {})
    _nombres = _contenedores.get("nombres", [])
    _mercancias_text = payload.get("mercancias_text", "")
    _neto_fallback   = "NET " + str(totales.get("total_peso_neto", 0)) + " KG"
    _bruto_fallback  = "GROSS " + str(totales.get("total_peso_bruto", 0)) + " KG"
    _cantidad_text = (
        f"{_tp.get('cases_line', str(totales.get('total_cases', 0)))}\n"
        f"\n"
        f"{_tp.get('net_line', _neto_fallback)}\n"
        f"\n"
        f"{_tp.get('gross_line', _bruto_fallback)}"
    )
    texts = {
        "expeditor":     payload.get("expedidor", ""),
        "destinatario":  payload.get("consignee") or "",
        "pais_origen":   payload.get("pais_origen", ""),
        "transporte":    "\n".join([
            payload.get("transporte", ""),
            _contenedores.get("resumen_texto", ""),
            " ".join(_nombres),
        ]),
        "observaciones": payload.get("observaciones", ""),
        "mercancias":    _mercancias_text,
        "cantidad":      _cantidad_text,
    }

    logger.info(
        f"[PDF_V2_ORIGEN_FINAL_FILL] expeditor={texts['expeditor'][:30]!r} "
        f"mercancias_lines={len(texts['mercancias'].splitlines())} "
        f"debug={debug}"
    )

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)

    for field_name, box in LAYOUT.items():
        text = texts.get(field_name, "")
        label = field_name if debug else None
        _draw_text_in_box(c, text, box, debug_label=label)

    c.save()
    pdf_bytes = buf.getvalue()

    logger.info(f"[PDF_V2_ORIGEN_FINAL_BLANK_READY] size={len(pdf_bytes)} bytes debug={debug}")
    return pdf_bytes


SANITARIO_LAYOUT: Dict[str, dict] = {
    "serie":               {"x": 455, "y": 785, "w": 80, "h": 17,  "font": "Helvetica", "size": 14, "leading": 11},
    "num_certificado":     {"x": 447, "y": 760, "w": 130, "h": 20,  "font": "Helvetica", "size": 18, "leading": 11, "color": (65, 105, 227)},
    "expedidor":           {"x": 65,  "y": 467, "w": 470, "h": 15,  "font": "Helvetica", "size": 7, "leading": 10},
    "consignee":           {"x": 65, "y": 365, "w": 470, "h": 15,  "font": "Helvetica", "size": 8, "leading": 10, "single_line": True},
    "pais_origen":         {"x": 233,  "y": 504, "w": 285, "h": 15,  "font": "Helvetica", "size": 8, "leading": 10},
    "pais_destino":        {"x": 325, "y": 405, "w": 230, "h": 15,  "font": "Helvetica", "size": 8, "leading": 10},
    "nombres_productos":   {"x": 307,  "y": 680, "w": 245, "h": 15, "font": "Helvetica", "size": 5, "leading": 10, "single_line": True},
    "formatos_productos":  {"x": 65, "y": 646, "w": 480, "h": 35, "font": "Helvetica", "size": 8, "leading": 10},
    "marcas_productos":    {"x": 65, "y": 586, "w": 480, "h": 15, "font": "Helvetica", "size": 8, "leading": 10},
    "total_cajas":         {"x": 273,  "y": 565, "w": 250, "h": 14,  "font": "Helvetica", "size": 8, "leading": 10},
    "total_peso_neto":     {"x": 183, "y": 545, "w": 320, "h": 14,  "font": "Helvetica", "size": 8, "leading": 10},
    "contenedores":        {"x": 274,  "y": 344, "w": 275, "h": 15,  "font": "Helvetica", "size": 5, "leading": 10},
    "establecimiento":     {"x": 343,  "y": 447, "w": 205, "h": 15,  "font": "Helvetica", "size": 8, "leading": 10},
    "jefe_salud":          {"x": 240, "y": 303, "w": 275, "h": 15,  "font": "Helvetica", "size": 8, "leading": 10},
    "firmado_en":          {"x": 208, "y": 119, "w": 90, "h": 15,  "font": "Helvetica", "size": 8, "leading": 10},
    "fecha_primera_factura":{"x": 140, "y": 100, "w": 90, "h": 15, "font": "Helvetica", "size": 8, "leading": 10},
}


def render_sanitario_v2(payload: dict, debug: bool = False) -> bytes:
    """Genera el PDF certificado sanitario (overlay ReportLab sobre la plantilla)."""
    totales = payload.get("totales", {})
    contenedores = payload.get("contenedores", [])
    texts = {
        "serie":               payload.get("serie", ""),
        "num_certificado":     payload.get("num_certificado", ""),
        "expedidor":           payload.get("expedidor", ""),
        "consignee":           payload.get("consignee") or "",
        "pais_origen":         payload.get("pais_origen", ""),
        "pais_destino":        payload.get("pais_destino", ""),
        "nombres_productos":   payload.get("mercancias_text", ""),
        "formatos_productos":  "  ".join(payload.get("formatos_unicos", [])),
        "marcas_productos":    "  ".join(payload.get("marcas_unicas", [])),
        "total_cajas":         payload.get("total_cajas_text", str(totales.get("total_cases", 0))),
        "total_peso_neto":     payload.get("total_peso_neto_text", f"{totales.get('total_peso_neto', 0)} KGS"),
        "contenedores":        " ".join(c["nombre"] for c in contenedores),
        "establecimiento":     payload.get("establecimiento", ""),
        "jefe_salud":          payload.get("jefe_salud", ""),
        "firmado_en":          payload.get("firmado_en", ""),
        "fecha_primera_factura": payload.get("fecha_primera_factura", ""),
    }

    logger.info(
        f"[PDF_V2_SANITARIO_FILL] expedidor={texts['expedidor'][:30]!r} "
        f"productos={len(payload.get('productos', []))} debug={debug}"
    )
    logger.info(
        f"[PDF_V2_SANITARIO_FIXED_FIELDS] "
        f"establecimiento={texts['establecimiento']!r} "
        f"jefe_salud={texts['jefe_salud']!r} "
        f"firmado_en={texts['firmado_en']!r}"
    )

    buf_overlay = io.BytesIO()
    c = canvas.Canvas(buf_overlay, pagesize=A4)
    for field_name, box in SANITARIO_LAYOUT.items():
        text = texts.get(field_name, "")
        label = field_name if debug else None
        _draw_text_in_box(c, text, box, debug_label=label)
    c.save()
    buf_overlay.seek(0)
    logger.info(f"[PDF_V2_SANITARIO_OVERLAY_READY] size={buf_overlay.getbuffer().nbytes} bytes")

    reader_template = PdfReader(SANITARIO_TEMPLATE)
    reader_overlay  = PdfReader(buf_overlay)
    base_page    = reader_template.pages[0]
    overlay_page = reader_overlay.pages[0]
    base_page.merge_page(overlay_page)

    writer = PdfWriter()
    writer.add_page(base_page)
    buf_final = io.BytesIO()
    writer.write(buf_final)
    pdf_bytes = buf_final.getvalue()

    logger.info(f"[PDF_V2_SANITARIO_MERGED] size={len(pdf_bytes)} bytes debug={debug}")
    return pdf_bytes
