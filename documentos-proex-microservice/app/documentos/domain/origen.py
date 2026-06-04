import random
from collections import Counter
from decimal import Decimal, InvalidOperation
from typing import List

from app.core.constants import CONTAINER_TYPE_DISPLAY, TRANSLATIONS


def _safe_decimal(v) -> Decimal:
    try:
        return Decimal(str(v or 0))
    except InvalidOperation:
        return Decimal("0")


def format_european_number(value: float, decimals: int = 0) -> str:
    """Formato europeo: separador de miles '.', decimal ','. Ej: 22800.0 → '22.800,00'."""
    formatted = f"{value:,.{decimals}f}"
    return formatted.replace(",", "MILES").replace(".", ",").replace("MILES", ".")


def build_origen_payload(
    container_ids: List[str],
    containers: dict,
    deal_props: dict,
    elementos_by_container: dict,
    descripcion_mercancia: str = "",
    observaciones: str = "",
    idioma: str = "ES",
) -> dict:
    """Construye el payload para Certificado de Origen. Borrador y Final comparten payload; difieren solo en plantilla."""

    lang = idioma if idioma in TRANSLATIONS else "ES"
    t = TRANSLATIONS[lang]

    nombres = [
        ((containers[cid].get("numero_contenedor") or "").strip()
         or (containers[cid].get("nombre") or "").strip())
        for cid in container_ids
        if cid in containers
    ]

    type_counter = Counter(
        containers[cid].get("tipo_contenedor", "UNKNOWN")
        for cid in container_ids
        if cid in containers
    )
    por_tipo = [
        {"tipo": tipo, "cantidad": cant}
        for tipo, cant in type_counter.most_common()
    ]

    resumen_partes: List[str] = []
    for tipo_code, cantidad in type_counter.most_common():
        if tipo_code in CONTAINER_TYPE_DISPLAY:
            size_prefix, type_key = CONTAINER_TYPE_DISPLAY[tipo_code]
            type_label = t.get(type_key, tipo_code)
            resumen_partes.append(f"{cantidad} X {size_prefix} {type_label}")
        else:
            resumen_partes.append(f"{cantidad} X {tipo_code}")
    resumen_texto = "  ".join(resumen_partes)

    _lang_field = {"en": "nombre_en", "fr": "nombre_fr", "es": "nombre_es"}.get(lang, "nombre_es")

    product_map: dict[str, dict] = {}
    for cid in container_ids:
        for e in elementos_by_container.get(cid, []):
            nombre_lang = (e.get(_lang_field) or "").strip()
            nombre = nombre_lang if nombre_lang else (e.get("nombre") or "").strip()
            if nombre not in product_map:
                product_map[nombre] = {
                    "total_cases": Decimal("0"),
                    "peso_neto":   Decimal("0"),
                    "peso_bruto":  Decimal("0"),
                }
            product_map[nombre]["total_cases"] += _safe_decimal(e.get("cantidad"))

            # Pesos: usa peso_*_total si existe, si no peso_*_unitario × cantidad
            neto_total = e.get("peso_neto_total")
            bruto_total = e.get("peso_bruto_total")
            if neto_total:
                product_map[nombre]["peso_neto"] += _safe_decimal(neto_total)
            else:
                product_map[nombre]["peso_neto"] += (
                    _safe_decimal(e.get("peso_neto_unitario")) * _safe_decimal(e.get("cantidad"))
                )
            if bruto_total:
                product_map[nombre]["peso_bruto"] += _safe_decimal(bruto_total)
            else:
                product_map[nombre]["peso_bruto"] += (
                    _safe_decimal(e.get("peso_bruto_unitario")) * _safe_decimal(e.get("cantidad"))
                )

    total_cases      = sum((int(v["total_cases"]) for v in product_map.values()), 0)
    total_peso_neto  = sum((v["peso_neto"]  for v in product_map.values()), Decimal("0"))
    total_peso_bruto = sum((v["peso_bruto"] for v in product_map.values()), Decimal("0"))

    neto_float  = float(total_peso_neto.quantize(Decimal("0.01")))
    bruto_float = float(total_peso_bruto.quantize(Decimal("0.01")))

    mercancias_text = descripcion_mercancia.strip()

    return {
        "expedidor":   deal_props.get("shipper") or "",
        "consignee":   deal_props.get("consignee") or "",
        "pais_origen": "ESPAÑA - SPAIN",
        "transporte":  t.get("sea_transport", "SEA TRANSPORT"),
        "contenedores": {
            "total":         len(container_ids),
            "por_tipo":      por_tipo,
            "resumen_texto": resumen_texto,
            "nombres":       nombres,
        },
        "observaciones": observaciones,
        "mercancias_text": mercancias_text,
        "totales": {
            "total_cases":      total_cases,
            "total_peso_neto":  neto_float,
            "total_peso_bruto": bruto_float,
        },
        "totales_pdf": {
            "cases_line": f"{format_european_number(total_cases)} {t['cases']}",
            "net_line":   f"{format_european_number(neto_float, 2)} {t['net_weight']}",
            "gross_line": f"{format_european_number(bruto_float, 2)} {t['gross_weight']}",
        },
        "num_certificado": str(random.randint(1_000_000, 9_999_999)),
    }
