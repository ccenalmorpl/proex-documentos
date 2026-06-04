import logging
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from fastapi.responses import HTMLResponse

from app.pedidos import service
from app.core.constants import FILE_TYPE_CONFIG
from app.pedidos.schemas import (
    DeleteFileResponse,
    PedidoDetalleResponse,
    PedidosListaResponse,
    UpdateContenedorEntregaRequest,
    UpdateContenedoresCertificadosRequest,
    UpdatePedidoBLRequest,
    UpdatePedidoResponse,
    UploadFileResponse,
)
from app.pedidos.service import PedidoNoEncontradoError

logger = logging.getLogger(__name__)
router = APIRouter()

TIPO_DOCUMENTO_PATTERN = "^(" + "|".join(FILE_TYPE_CONFIG.keys()) + ")$"


@router.get(
    "",
    response_model=PedidosListaResponse,
    response_model_by_alias=True,
)
async def list_pedidos(
    company_id: str = Query(..., min_length=1, description="ID de la empresa en HubSpot"),
) -> PedidosListaResponse:
    try:
        return await service.list_pedidos_for_company(company_id)
    except Exception as e:
        logger.error(f"Error en GET /api/v1/pedidos: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{numero_de_pedido}",
    response_model=PedidoDetalleResponse,
)
async def get_pedido_detalle(
    numero_de_pedido: str,
    company_id: str = Query(..., min_length=1, description="ID de la empresa en HubSpot"),
) -> PedidoDetalleResponse:
    """Detalle de un pedido. Valida que pertenezca a `company_id`."""
    try:
        return await service.get_pedido_detalle(numero_de_pedido, company_id)
    except PedidoNoEncontradoError as e:
        logger.warning(f"GET /api/v1/pedidos/{numero_de_pedido} → 404: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "numero_de_pedido_no_encontrado",
                "numero_de_pedido": e.numero_de_pedido,
            },
        )
    except Exception as e:
        logger.error(
            f"Error en GET /api/v1/pedidos/{numero_de_pedido}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{numero_de_pedido}", response_model=UpdatePedidoResponse)
async def update_pedido_bl(
    numero_de_pedido: str,
    payload: UpdatePedidoBLRequest,
    company_id: str = Query(..., min_length=1),
) -> UpdatePedidoResponse:
    try:
        return await service.update_pedido_bl(numero_de_pedido, company_id, payload)
    except PedidoNoEncontradoError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "numero_de_pedido_no_encontrado", "numero_de_pedido": e.numero_de_pedido},
        )
    except Exception as e:
        logger.error(f"PATCH /api/v1/pedidos/{numero_de_pedido}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{numero_de_pedido}/contenedores/properties", response_model=UpdatePedidoResponse)
async def update_contenedores_certificados_endpoint(
    numero_de_pedido: str,
    payload: UpdateContenedoresCertificadosRequest,
    company_id: str = Query(..., min_length=1),
) -> UpdatePedidoResponse:
    try:
        return await service.update_contenedores_certificados(numero_de_pedido, company_id, payload)
    except PedidoNoEncontradoError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "numero_de_pedido_no_encontrado", "numero_de_pedido": e.numero_de_pedido},
        )
    except Exception as e:
        logger.error(f"PATCH /api/v1/pedidos/{numero_de_pedido}/contenedores/properties: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/{numero_de_pedido}/contenedores/{contenedor_id}/entrega",
    response_model=UpdatePedidoResponse,
)
async def update_contenedor_entrega_endpoint(
    numero_de_pedido: str,
    contenedor_id: str,
    payload: UpdateContenedorEntregaRequest,
    company_id: str = Query(..., min_length=1),
) -> UpdatePedidoResponse:
    try:
        return await service.update_contenedor_entrega(
            numero_de_pedido, company_id, contenedor_id, payload,
        )
    except PedidoNoEncontradoError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "numero_de_pedido_no_encontrado", "numero_de_pedido": e.numero_de_pedido},
        )
    except Exception as e:
        logger.error(
            f"PATCH /api/v1/pedidos/{numero_de_pedido}/contenedores/{contenedor_id}/entrega: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{numero_de_pedido}/files/upload", response_model=UploadFileResponse)
async def upload_pedido_file_endpoint(
    numero_de_pedido: str,
    company_id: str = Query(..., min_length=1),
    tipo_documento: str = Query(..., pattern=TIPO_DOCUMENTO_PATTERN),
    contenedor_id: Optional[str] = Query(None, min_length=1),
    file: UploadFile = File(...),
) -> UploadFileResponse:
    try:
        config = FILE_TYPE_CONFIG[tipo_documento]
        allowed_mimes = config.get("allowed_mime_types") or ("application/pdf",)
        if file.content_type and file.content_type not in allowed_mimes:
            return UploadFileResponse(
                success=False,
                error=f"Tipo de archivo no admitido: {file.content_type}",
                error_code="tipo_archivo_invalido",
            )
        file_bytes = await file.read()
        return await service.upload_pedido_file(
            numero_de_pedido,
            company_id,
            file_bytes,
            tipo_documento,
            original_filename=file.filename,
            mime_type=file.content_type,
            contenedor_id=contenedor_id,
        )
    except PedidoNoEncontradoError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "numero_de_pedido_no_encontrado", "numero_de_pedido": e.numero_de_pedido},
        )
    except Exception as e:
        logger.error(f"POST /api/v1/pedidos/{numero_de_pedido}/files/upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{numero_de_pedido}/files/upload-modal", response_class=HTMLResponse)
async def upload_pedido_file_modal(
    numero_de_pedido: str,
    company_id: str = Query(..., min_length=1),
    tipo_documento: str = Query(..., pattern=TIPO_DOCUMENTO_PATTERN),
    contenedor_id: Optional[str] = Query(None, min_length=1),
) -> HTMLResponse:
    html = service.render_upload_iframe_html(
        numero_de_pedido, company_id, tipo_documento, contenedor_id,
    )
    return HTMLResponse(content=html)


@router.delete("/{numero_de_pedido}/files/{file_id}", response_model=DeleteFileResponse)
async def delete_pedido_file_endpoint(
    numero_de_pedido: str,
    file_id: str,
    company_id: str = Query(..., min_length=1),
    tipo_documento: str = Query(..., pattern=TIPO_DOCUMENTO_PATTERN),
    contenedor_id: Optional[str] = Query(None, min_length=1),
) -> DeleteFileResponse:
    try:
        return await service.delete_pedido_file(
            numero_de_pedido, company_id, file_id, tipo_documento, contenedor_id=contenedor_id,
        )
    except PedidoNoEncontradoError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "numero_de_pedido_no_encontrado", "numero_de_pedido": e.numero_de_pedido},
        )
    except Exception as e:
        logger.error(f"DELETE /api/v1/pedidos/{numero_de_pedido}/files/{file_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
