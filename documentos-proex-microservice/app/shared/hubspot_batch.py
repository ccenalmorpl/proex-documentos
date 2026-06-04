"""Helpers batch para HubSpot. Reducen O(N) calls síncronas a O(N/100)."""

import logging
import time
from typing import Any, Iterable, Optional

from hubspot import HubSpot
from hubspot.crm.associations.v4 import (
    BatchInputPublicFetchAssociationsBatchRequest,
    PublicFetchAssociationsBatchRequest,
)
from hubspot.crm.objects import (
    BatchReadInputSimplePublicObjectId,
    SimplePublicObjectId,
)

logger = logging.getLogger(__name__)

_BATCH_SIZE = 100
_OWNERS_TTL_SECONDS = 600

_owners_cache: dict[str, tuple[float, Optional[dict]]] = {}


def _chunks(seq: list, size: int):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def batch_read_objects(
    client: HubSpot,
    object_type: str,
    ids: Iterable[str],
    properties: list[str],
) -> dict[str, dict[str, Any]]:
    """Lee N objetos en una sola pasada (HubSpot batch_api.read).

    Devuelve `{id: properties_dict}`. IDs no encontrados se omiten. Chunkea
    automáticamente a 100 IDs por call (límite HubSpot).
    """
    unique_ids = [i for i in dict.fromkeys(ids) if i]
    if not unique_ids:
        return {}

    out: dict[str, dict[str, Any]] = {}
    started = time.monotonic()
    for chunk in _chunks(unique_ids, _BATCH_SIZE):
        batch_input = BatchReadInputSimplePublicObjectId(
            inputs=[SimplePublicObjectId(id=str(oid)) for oid in chunk],
            properties=properties,
            properties_with_history=[],
        )
        resp = client.crm.objects.batch_api.read(
            object_type=object_type,
            batch_read_input_simple_public_object_id=batch_input,
        )
        for item in getattr(resp, "results", None) or []:
            out[item.id] = dict(item.properties or {})
    logger.info(
        f"[batch_read_objects] type={object_type} requested={len(unique_ids)} "
        f"found={len(out)} elapsed={time.monotonic() - started:.2f}s"
    )
    return out


def batch_read_associations(
    client: HubSpot,
    from_object_type: str,
    to_object_type: str,
    from_ids: Iterable[str],
) -> dict[str, list[str]]:
    """Lee asociaciones de N objetos en una sola pasada.

    Devuelve `{from_id: [to_id, ...]}` (lista posiblemente vacía para los IDs
    sin asociaciones). Chunkea a 100 IDs por call.
    """
    unique_ids = [i for i in dict.fromkeys(from_ids) if i]
    if not unique_ids:
        return {}

    out: dict[str, list[str]] = {oid: [] for oid in unique_ids}
    started = time.monotonic()
    for chunk in _chunks(unique_ids, _BATCH_SIZE):
        batch_input = BatchInputPublicFetchAssociationsBatchRequest(
            inputs=[PublicFetchAssociationsBatchRequest(id=str(oid)) for oid in chunk],
        )
        resp = client.crm.associations.v4.batch_api.get_page(
            from_object_type=from_object_type,
            to_object_type=to_object_type,
            batch_input_public_fetch_associations_batch_request=batch_input,
        )
        for row in getattr(resp, "results", None) or []:
            from_id = getattr(getattr(row, "_from", None), "id", None) or getattr(row, "from_object_id", None)
            if not from_id:
                continue
            tos = [
                getattr(t, "to_object_id", None) or getattr(t, "id", None)
                for t in (getattr(row, "to", None) or [])
            ]
            out[str(from_id)] = [str(t) for t in tos if t]
    logger.info(
        f"[batch_read_associations] {from_object_type}->{to_object_type} "
        f"requested={len(unique_ids)} elapsed={time.monotonic() - started:.2f}s"
    )
    return out


def get_owner_cached(client: HubSpot, owner_id: str) -> Optional[dict]:
    """Devuelve `{email, firstName, lastName}` del owner; cachea 10 min."""
    if not owner_id:
        return None
    now = time.monotonic()
    cached = _owners_cache.get(owner_id)
    if cached and (now - cached[0]) < _OWNERS_TTL_SECONDS:
        return cached[1]
    try:
        owner = client.crm.owners.owners_api.get_by_id(owner_id=owner_id)
    except Exception as e:
        logger.warning(f"[get_owner_cached] owner_id={owner_id} fallo: {e}")
        _owners_cache[owner_id] = (now, None)
        return None
    data = {
        "email": getattr(owner, "email", None),
        "firstName": getattr(owner, "first_name", None),
        "lastName": getattr(owner, "last_name", None),
    }
    _owners_cache[owner_id] = (now, data)
    return data
