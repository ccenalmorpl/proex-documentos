"""Router FastAPI para el módulo documentos.

Routers sin lógica: solo validación de entrada y delegación al service.
"""

import logging
from fastapi import APIRouter, HTTPException

from app.documentos.schemas import (
    PendingRequest, PendingResponse,
    GenerateRequest, GenerateResponse,
    GeneratedRequest, GeneratedResponse,
    RollbackRequest, RollbackResponse,
)
from app.documentos import service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/pending", response_model=PendingResponse)
async def get_pending_containers(request: PendingRequest) -> PendingResponse:
    """Devuelve contenedores con documentos pendientes según filtros (Tab 1)."""
    try:
        return await service.get_pending_containers(request)
    except Exception as e:
        logger.error(f"Error en /pending: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=GenerateResponse)
async def generate_documents(request: GenerateRequest) -> GenerateResponse:
    """Genera 1–3 tipos de documento para un grupo de contenedores (Tab 1)."""
    try:
        return await service.generate_documents(request)
    except Exception as e:
        logger.error(f"Error en /generate: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generated", response_model=GeneratedResponse)
async def get_generated_containers(request: GeneratedRequest) -> GeneratedResponse:
    """Devuelve contenedores con documentos ya generados según filtros (Tab 2)."""
    try:
        return await service.get_generated_containers(request)
    except Exception as e:
        logger.error(f"Error en /generated: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rollback", response_model=RollbackResponse)
async def rollback_document(request: RollbackRequest) -> RollbackResponse:
    """Borra un documento y limpia propiedades en todos los contenedores del grupo (Tab 2)."""
    try:
        return await service.rollback_document(request)
    except Exception as e:
        logger.error(f"Error en /rollback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
