import logging
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

    elemento_ids_per_container: Dict[str, List[str]] = {}
    for cid in container_ids:
        resp = client.crm.associations.v4.basic_api.get_page(
            object_type=OBJECT_TYPE_CONTENEDOR,
            object_id=cid,
            to_object_type=OBJECT_TYPE_ELEMENTO,
            limit=250,
        )
        elemento_ids_per_container[cid] = [r.to_object_id for r in (resp.results or [])]

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


def calcular_descripcion_mercancia_agregada(
    elementos: List[Dict], idioma: Optional[str]
) -> Optional[str]:
    """Concatena `descripcion_mercancia_{idioma}` de cada elemento fabricante,
    una línea por elemento. Idioma normalizado a es|en|fr (default es)."""
    lang = (idioma or "").strip().lower()
    if lang not in {"es", "en", "fr"}:
        lang = "es"
    campo = f"descripcion_mercancia_{lang}"
    lineas: List[str] = []
    for el in elementos:
        valor = (el.get(campo) or "").strip()
        if valor:
            lineas.append(valor)
    return "\n".join(lineas) if lineas else None
