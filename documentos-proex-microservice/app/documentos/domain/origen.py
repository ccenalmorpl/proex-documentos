import random
from collections import Counter
from decimal import Decimal, InvalidOperation
from typing import List, Tuple

from app.core.constants import CONTAINER_TYPE_DISPLAY, LANG_TO_NOMBRE_COLUMN, TRANSLATIONS


def _safe_decimal(v) -> Decimal:
    try:
        return Decimal(str(v or 0))
    except InvalidOperation:
        return Decimal("0")


def format_european_number(value: float, decimals: int = 0) -> str:
    """Formato europeo: separador de miles '.', decimal ','. Ej: 22800.0 → '22.800,00'."""
    formatted = f"{value:,.{decimals}f}"
    return formatted.replace(",", "MILES").replace(".", ",").replace("MILES", ".")


def _peso_elemento(element: dict, total_key: str, unitario_key: str) -> Decimal:
    total = element.get(total_key)
    if total:
        return _safe_decimal(total)
    return _safe_decimal(element.get(unitario_key)) * _safe_decimal(element.get("cantidad"))


def pesos_embarque(
    container_ids: List[str], containers: dict, elementos_by_container: dict
) -> Tuple[Decimal, Decimal]:
    """Peso neto y bruto del grupo de contenedores.

    Manda lo que se graba en el Contenedor en el Día de carga; el teórico de los
    Elementos (cajas × peso unitario de la proforma) solo cubre un contenedor sin pesos.
    """
    neto = Decimal("0")
    bruto = Decimal("0")
    for cid in container_ids:
        props = containers.get(cid) or {}
        elementos = elementos_by_container.get(cid, [])
        neto_cargado = _safe_decimal(props.get("peso_neto"))
        bruto_cargado = _safe_decimal(props.get("peso_bruto"))
        neto += neto_cargado if neto_cargado > 0 else sum(
            (_peso_elemento(e, "peso_neto_total", "peso_neto_unitario") for e in elementos),
            Decimal("0"),
        )
        bruto += bruto_cargado if bruto_cargado > 0 else sum(
            (_peso_elemento(e, "peso_bruto_total", "peso_bruto_unitario") for e in elementos),
            Decimal("0"),
        )
    return neto, bruto


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

    lang = (idioma or "ES").strip().upper()
    if lang not in TRANSLATIONS:
        lang = "ES"
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

    _lang_field = LANG_TO_NOMBRE_COLUMN.get(lang, "nombre_es")

    cases_por_producto: dict[str, Decimal] = {}
    for cid in container_ids:
        for e in elementos_by_container.get(cid, []):
            nombre_lang = (e.get(_lang_field) or "").strip()
            nombre = nombre_lang if nombre_lang else (e.get("nombre") or "").strip()
            cases_por_producto[nombre] = (
                cases_por_producto.get(nombre, Decimal("0")) + _safe_decimal(e.get("cantidad"))
            )

    total_cases = sum((int(v) for v in cases_por_producto.values()), 0)
    total_peso_neto, total_peso_bruto = pesos_embarque(
        container_ids, containers, elementos_by_container
    )

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
