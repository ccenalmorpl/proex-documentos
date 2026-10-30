import logging
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

from hubspot.crm.objects import (
    BatchReadInputSimplePublicObjectId,
    SimplePublicObjectId,
)

from app.core.constants import (
    OBJECT_TYPE_CONTENEDOR,
    OBJECT_TYPE_ELEMENTO,
    ELEMENTO_PROPERTIES,
    ELEMENTO_TIPO_FABRICANTE,
)

logger = logging.getLogger(__name__)

ASSOC_WORKERS = 8


def get_elementos_fabricante_por_contenedor(
    client, container_ids: List[str]
) -> Dict[str, List[Dict]]:
    """Devuelve los Elementos `tipo_articulo=fabricante` asociados a cada contenedor.

    Resultado: { contenedor_id: [props_dict, ...] }. Contenedores sin elementos
    devuelven lista vacía. Lectura en batches de 100 para no exceder el límite
    del SDK de HubSpot.
    """
    logger.info(
        f"obteniendo elementos para {len(container_ids)} contenedores"
    )

    def _elemento_ids(cid: str) -> List[str]:
        resp = client.crm.associations.v4.basic_api.get_page(
            object_type=OBJECT_TYPE_CONTENEDOR,
            object_id=cid,
            to_object_type=OBJECT_TYPE_ELEMENTO,
            limit=250,
        )
        return [r.to_object_id for r in (resp.results or [])]

    # Una llamada por contenedor: en serie, 20 contenedores eran 7 s y la card
    # corta a los 15 s (P-65571985983).
    with ThreadPoolExecutor(max_workers=ASSOC_WORKERS) as pool:
        elemento_ids_per_container: Dict[str, List[str]] = dict(
            zip(container_ids, pool.map(_elemento_ids, container_ids))
        )

    total_assoc = sum(len(v) for v in elemento_ids_per_container.values())
    logger.info(f"asociaciones encontradas: {total_assoc}")

    all_elemento_ids = list({eid for ids in elemento_ids_per_container.values() for eid in ids})
    if not all_elemento_ids:
        logger.warning("ningún elemento encontrado para estos contenedores")
        return {cid: [] for cid in container_ids}

    elemento_props: Dict[str, Dict] = {}
    chunk_size = 100
    for i in range(0, len(all_elemento_ids), chunk_size):
        chunk = all_elemento_ids[i : i + chunk_size]
        batch_input = BatchReadInputSimplePublicObjectId(
            properties=ELEMENTO_PROPERTIES,
            inputs=[SimplePublicObjectId(id=eid) for eid in chunk],
        )
        resp = client.crm.objects.batch_api.read(
            object_type=OBJECT_TYPE_ELEMENTO,
            batch_read_input_simple_public_object_id=batch_input,
        )
        for obj in (resp.results or []):
            elemento_props[obj.id] = obj.properties

    result = {
        cid: [
            elemento_props[eid]
            for eid in elemento_ids_per_container.get(cid, [])
            if eid in elemento_props
            and elemento_props[eid].get("tipo_articulo") == ELEMENTO_TIPO_FABRICANTE
        ]
        for cid in container_ids
    }

    total_filtrados = sum(len(v) for v in result.values())
    logger.info(
        f"OK → {len(elemento_props)} elementos leídos, "
        f"{total_filtrados} tras filtrar por tipo_articulo=fabricante"
    )
    return result


_ID_PREFIX_RE = re.compile(r"^\s*\d{6,}(?:-\d+)?\s*-\s*")


def _strip_id_prefix(nombre: Optional[str]) -> Optional[str]:
    if not nombre:
        return nombre
    cleaned = _ID_PREFIX_RE.sub("", nombre, count=1).strip()
    return cleaned or nombre


def calcular_descripcion_mercancia_agregada(
    elementos: List[Dict],
) -> Optional[str]:
    """Descripción interna del contenedor: una línea por elemento fabricante
    con formato `<nº cajas> CAJAS <nombre interno>`, sin el prefijo de SKU y
    siempre en español. Se calcula en runtime desde `cantidad` + `nombre`."""
    lineas: List[str] = []
    for el in elementos:
        nombre = _strip_id_prefix((el.get("nombre") or "").strip())
        if not nombre:
            continue
        try:
            cajas = int(float(el.get("cantidad")))
        except (TypeError, ValueError):
            cajas = 0
        lineas.append(f"{cajas} CAJAS {nombre}")
    return "\n".join(lineas) if lineas else None
