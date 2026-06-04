import asyncio
import logging
from typing import List, Tuple

from hubspot.crm.companies import (
    Filter as CompFilter,
    FilterGroup as CompFilterGroup,
    PublicObjectSearchRequest as CompSearchRequest,
)

from app.empresas.schemas import EmpresaItem, EmpresasListaResponse
from app.shared.hubspot_client import hubspot_client

logger = logging.getLogger(__name__)

DEFAULT_SEARCH_LIMIT = 50


def _search_companies_by_name(client, q: str, limit: int = DEFAULT_SEARCH_LIMIT) -> List[Tuple[str, str]]:
    filters = [CompFilter(
        property_name="name",
        operator="CONTAINS_TOKEN",
        value=f"*{q}*",
    )]
    search_request = CompSearchRequest(
        filter_groups=[CompFilterGroup(filters=filters)],
        properties=["name"],
        limit=limit,
    )

    resp = client.crm.companies.search_api.do_search(
        public_object_search_request=search_request
    )

    return [(c.id, c.properties.get("name", "")) for c in (resp.results or [])]


async def search_empresas(q: str, limit: int = DEFAULT_SEARCH_LIMIT) -> EmpresasListaResponse:
    logger.info(f"[search_empresas] q={q!r} limit={limit}")

    try:
        client = hubspot_client.get_client()
        results = await asyncio.to_thread(_search_companies_by_name, client, q, limit)

        empresas = [EmpresaItem(id=cid, name=name) for cid, name in results]
        logger.info(f"[search_empresas] q={q!r} → {len(empresas)} resultados")

        return EmpresasListaResponse(
            success=True,
            empresas=empresas,
            total=len(empresas),
        )

    except Exception as e:
        logger.error(f"[search_empresas] ERROR q={q!r}: {e}", exc_info=True)
        return EmpresasListaResponse(success=False, error=str(e))
