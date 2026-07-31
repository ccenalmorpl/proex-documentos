import logging
import threading
from typing import Dict, Optional

from app.core.constants import LANG_TO_NOMBRE_COLUMN
from app.shared.hubspot_client import hubspot_client

logger = logging.getLogger(__name__)

HUBDB_TABLE_PUERTOS = "puertos"
HUBDB_TABLE_FORMATO_PRODUCTO = "formato_producto"


def get_puerto_destination_country(puerto_id: str) -> Optional[str]:
    """País destino asociado al puerto (certificado sanitario)."""
    client = hubspot_client.get_client()

    # TODO: Implementar lookup en HubDB
    raise NotImplementedError("get_puerto_destination_country: pendiente de implementación")


# {valor_columna_id: {"ES": nombre_es, "EN": nombre_en, "FR": nombre_fr}}
_formato_cache: Optional[Dict[str, Dict[str, str]]] = None
_formato_lock = threading.Lock()


def _row_value(row, column: str) -> Optional[str]:
    """Lee `row.values[column]` tolerando dict (select/foreign) o escalar."""
    values = getattr(row, "values", None) or {}
    raw = values.get(column) if isinstance(values, dict) else None
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw.get("name") or raw.get("label") or raw.get("value")
    return str(raw)


def _fetch_formato_rows() -> list:
    client = hubspot_client.get_client()
    rows: list = []
    after = None
    while True:
        kwargs = {"limit": 1000}
        if after:
            kwargs["after"] = after
        page = client.cms.hubdb.rows_api.get_table_rows(HUBDB_TABLE_FORMATO_PRODUCTO, **kwargs)
        rows.extend(page.results or [])
        paging = getattr(page, "paging", None)
        nxt = getattr(paging, "next", None) if paging else None
        if not nxt or not getattr(nxt, "after", None):
            break
        after = nxt.after

    logger.info("[hubdb_formato] _fetch_formato_rows: %d filas leídas de %r", len(rows), HUBDB_TABLE_FORMATO_PRODUCTO)
    if rows:
        first = rows[0]
        values = getattr(first, "values", None)
        logger.info(
            "[hubdb_formato] primera fila: row.id=%r columnas=%r values=%r",
            getattr(first, "id", None),
            list(values.keys()) if isinstance(values, dict) else type(values).__name__,
            values,
        )
    else:
        logger.warning(
            "[hubdb_formato] 0 filas. ¿Tabla %r publicada? get_table_rows lee la versión PUBLICADA, "
            "no el draft.", HUBDB_TABLE_FORMATO_PRODUCTO,
        )
    return rows


def _build_formato_cache(rows) -> Dict[str, Dict[str, str]]:
    cache: Dict[str, Dict[str, str]] = {}
    sin_id = 0
    for row in rows or []:
        id_value = (_row_value(row, "id") or "").strip()
        if not id_value:
            sin_id += 1
            continue
        cache[id_value] = {
            "ES": (_row_value(row, "nombre_es") or "").strip(),
            "EN": (_row_value(row, "nombre_en") or "").strip(),
            "FR": (_row_value(row, "nombre_fr") or "").strip(),
        }
    if sin_id:
        logger.warning(
            "[hubdb_formato] %d/%d filas sin columna 'id' legible — ¿nombre interno real distinto de 'id'?",
            sin_id, len(rows or []),
        )
    logger.info("[hubdb_formato] cache construida: %d formatos indexados (ej: %r)", len(cache), list(cache.items())[:3])
    return cache


def _ensure_formato_cache() -> Dict[str, Dict[str, str]]:
    global _formato_cache
    if _formato_cache is None:
        with _formato_lock:
            if _formato_cache is None:
                try:
                    _formato_cache = _build_formato_cache(_fetch_formato_rows())
                    logger.info(
                        "[hubdb_formato] tabla %r cargada: %d formatos",
                        HUBDB_TABLE_FORMATO_PRODUCTO, len(_formato_cache),
                    )
                except Exception as e:
                    logger.error(
                        "[hubdb_formato] fallo cargando tabla %r: %s",
                        HUBDB_TABLE_FORMATO_PRODUCTO, e, exc_info=True,
                    )
                    _formato_cache = {}
    return _formato_cache


def get_formato_label_map(idioma: str) -> Dict[str, str]:
    """`{valor_interno_formato: nombre_<idioma>}` desde la HubDB `formato_producto`.

    El idioma se normaliza a ES/EN/FR (cualquier otro usa ES). Si una fila no
    tiene traducción para el idioma pedido, cae a ES. Las filas sin traducción
    se omiten del mapa, de modo que el llamante conserva el valor crudo.
    """
    lang = (idioma or "ES").strip().upper()
    if lang not in LANG_TO_NOMBRE_COLUMN:
        lang = "ES"
    label_map: Dict[str, str] = {}
    for id_value, nombres in _ensure_formato_cache().items():
        label = nombres.get(lang) or nombres.get("ES") or ""
        if label:
            label_map[id_value] = label
    logger.info(
        "[hubdb_formato] get_formato_label_map idioma=%r→lang=%r: %d etiquetas (claves=%r)",
        idioma, lang, len(label_map), list(label_map.keys())[:10],
    )
    return label_map


def reset_formato_cache() -> None:
    """Solo para tests."""
    global _formato_cache
    _formato_cache = None
