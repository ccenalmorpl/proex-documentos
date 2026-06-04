from collections import OrderedDict
from datetime import datetime
from decimal import Decimal
from typing import List

from app.core.config import Settings
from app.core.constants import TRANSLATIONS
from app.documentos.domain.origen import _safe_decimal, format_european_number


def _peso_efectivo(element: dict, total_key: str, unitario_key: str) -> Decimal:
    """Peso efectivo: usa total si existe, si no unitario × cantidad. 0 si faltan datos."""
    total = element.get(total_key)
    if total:
        return _safe_decimal(total)
    return _safe_decimal(element.get(unitario_key)) * _safe_decimal(element.get("cantidad"))


def build_sanitario_payload(
    container_ids: List[str],
    containers: dict,
    deal_props: dict,
    elementos_by_container: dict,
    settings: Settings,
    idioma: str = "ES",
) -> dict:
    """Construye el payload para Certificado Sanitario. `deal_props["puerto_destino"]` debe llegar ya resuelto a label visible."""

    lang = idioma if idioma in TRANSLATIONS else "ES"
    t = TRANSLATIONS[lang]

    contenedores_list = [
        {
            "posicion":        i + 1,
            "nombre":          ((containers[cid].get("numero_contenedor") or "").strip()
                                or (containers[cid].get("nombre") or "").strip()),
            "tipo_contenedor": containers[cid].get("tipo_contenedor", ""),
        }
        for i, cid in enumerate(container_ids)
        if cid in containers
    ]

    # _strip_nombre necesita el `nombre` largo del Contenedor, no el `numero_contenedor` corto.
    _nombres_contenedores = [
        (containers[cid].get("nombre") or "").strip()
        for cid in container_ids
        if cid in containers
    ]

    def _strip_nombre(nombre: str) -> str:
        for n in _nombres_contenedores:
            if n:
                nombre = nombre.replace(n + " - ", "")
                nombre = nombre.replace(n, "")
        return nombre.strip()

    _lang_field = {"en": "nombre_en", "fr": "nombre_fr", "es": "nombre_es"}.get(lang, "nombre_es")

    product_map: "OrderedDict[str, dict]" = OrderedDict()
    for cid in container_ids:
        for e in elementos_by_container.get(cid, []):
            nombre_lang = (e.get(_lang_field) or "").strip()
            nombre_base = nombre_lang if nombre_lang else (e.get("nombre") or "").strip()
            descripcion = _strip_nombre(nombre_base)
            formato = (e.get("formato") or "").strip()
            marca   = (e.get("marca")   or "").strip()
            if descripcion not in product_map:
                product_map[descripcion] = {
                    "total_cases": Decimal("0"),
                    "peso_neto":   Decimal("0"),
                    "peso_bruto":  Decimal("0"),
                    "formato":     formato,
                    "marca":       marca,
                }
            product_map[descripcion]["total_cases"] += _safe_decimal(e.get("cantidad"))
            product_map[descripcion]["peso_neto"]   += _peso_efectivo(e, "peso_neto_total",  "peso_neto_unitario")
            product_map[descripcion]["peso_bruto"]  += _peso_efectivo(e, "peso_bruto_total", "peso_bruto_unitario")

    productos = [
        {
            "descripcion": desc,
            "total_cases": int(vals["total_cases"]),
            "linea_pdf":   f"{int(vals['total_cases'])} {t['cases_of']} {desc}",
        }
        for desc, vals in product_map.items()
    ]

    formatos_unicos = list(
        dict.fromkeys(
            vals["formato"]
            for vals in product_map.values()
            if vals["formato"]
        )
    )

    marcas_unicas = list(
        dict.fromkeys(
            vals["marca"]
            for vals in product_map.values()
            if vals["marca"]
        )
    )

    total_cases      = sum((int(v["total_cases"]) for v in product_map.values()), 0)
    total_peso_neto  = sum((v["peso_neto"]  for v in product_map.values()), Decimal("0"))
    total_peso_bruto = sum((v["peso_bruto"] for v in product_map.values()), Decimal("0"))

    neto_float  = float(total_peso_neto.quantize(Decimal("0.01")))
    bruto_float = float(total_peso_bruto.quantize(Decimal("0.01")))

    return {
        "expedidor":             (deal_props.get("shipper") or "").replace("\n", " ").strip(),
        "serie":                 f"01/{datetime.now().year}",
        "num_certificado":       f"CS{datetime.now().strftime('%H%M%d%m%y')}",
        "consignee":             (deal_props.get("consignee") or "").replace("\n", " ").strip(),
        "pais_origen":           "ESPAÑA - SPAIN",
        # "pais_destino" es la key del layout del PDF; el valor viene de Deal.puerto_destino.
        "pais_destino":          deal_props.get("puerto_destino", ""),
        "contenedores":          contenedores_list,
        "productos":             productos,
        "formatos_unicos":       formatos_unicos,
        "marcas_unicas":         marcas_unicas,
        "mercancias_text":       "\n".join(k for k in product_map if k),
        "totales": {
            "total_cases":       total_cases,
            "total_peso_neto":   neto_float,
            "total_peso_bruto":  bruto_float,
        },
        "total_cajas_text":      f"{format_european_number(total_cases)} {t['cases']}",
        # "KGS" fijo per spec — no se traduce por idioma
        "total_peso_neto_text":  f"{format_european_number(neto_float, 2)} KGS",
        "fecha_primera_factura": datetime.now().strftime("%d/%m/%Y"),
        "establecimiento":       settings.sanitario_establecimiento,
        "jefe_salud":            settings.sanitario_jefe_salud,
        "firmado_en":            settings.sanitario_firmado_en,
    }
