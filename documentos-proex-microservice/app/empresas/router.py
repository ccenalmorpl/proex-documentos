import logging

from fastapi import APIRouter, HTTPException, Query

from app.empresas import service
from app.empresas.schemas import EmpresasListaResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=EmpresasListaResponse)
async def search_empresas(
    q: str = Query(..., min_length=1, description="Texto a buscar en el nombre de la empresa"),
) -> EmpresasListaResponse:
    try:
        return await service.search_empresas(q)
    except Exception as e:
        logger.error(f"Error en GET /api/v1/empresas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
