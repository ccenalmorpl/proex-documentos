import logging
from collections import OrderedDict
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from app.core.config import Settings
from app.core.constants import LANG_TO_NOMBRE_COLUMN, TRANSLATIONS
from app.documentos.domain.origen import _safe_decimal, format_european_number, pesos_embarque

logger = logging.getLogger(__name__)


def build_sanitario_payload(
    container_ids: List[str],
    containers: dict,
    deal_props: dict,
    elementos_by_container: dict,
    settings: Settings,
    idioma: str = "ES",
    formato_labels: Optional[Dict[str, str]] = None,
) -> dict:
    """Construye el payload para Certificado Sanitario. `deal_props["puerto_destino"]` debe llegar ya resuelto a label visible.

    `formato_labels` mapea el valor interno de `elemento.formato` (select) al
    nombre traducido del idioma elegido (HubDB `formato_producto`). Si falta o
    no contiene el valor, se conserva el valor interno crudo.
    """

    lang = (idioma or "ES").strip().upper()
    if lang not in TRANSLATIONS:
        lang = "ES"
    t = TRANSLATIONS[lang]
    formato_labels = formato_labels or {}

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

    _lang_field = LANG_TO_NOMBRE_COLUMN.get(lang, "nombre_es")

    logger.info(
        "[sanitario_formato] idioma=%r lang=%r formato_labels=%d claves=%r",
        idioma, lang, len(formato_labels), list(formato_labels.keys())[:10],
    )
    _formato_debug: list = []

    product_map: "OrderedDict[str, dict]" = OrderedDict()
    for cid in container_ids:
        for e in elementos_by_container.get(cid, []):
            nombre_lang = (e.get(_lang_field) or "").strip()
            nombre_base = nombre_lang if nombre_lang else (e.get("nombre") or "").strip()
            descripcion = _strip_nombre(nombre_base)
            formato_raw = (e.get("formato") or "").strip()
            formato = formato_labels.get(formato_raw, formato_raw)
            _formato_debug.append((formato_raw, formato, formato_raw in formato_labels))
            marca   = (e.get("marca")   or "").strip()
            if descripcion not in product_map:
                product_map[descripcion] = {
                    "total_cases": Decimal("0"),
                    "formato":     formato,
                    "marca":       marca,
                }
            product_map[descripcion]["total_cases"] += _safe_decimal(e.get("cantidad"))

    productos = [
        {
            "descripcion": desc,
            "total_cases": int(vals["total_cases"]),
            "linea_pdf":   f"{int(vals['total_cases'])} {t['cases_of']} {desc}",
        }
        for desc, vals in product_map.items()
    ]

    logger.info(
        "[sanitario_formato] resolución por elemento (raw, resuelto, ¿match?): %r",
        _formato_debug,
    )

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
    total_peso_neto, total_peso_bruto = pesos_embarque(
        container_ids, containers, elementos_by_container
    )

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
