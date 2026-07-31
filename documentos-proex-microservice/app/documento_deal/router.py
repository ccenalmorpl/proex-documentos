import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.documento_deal import service
from app.documento_deal.schemas import PreparaDocWebhookRequest, WebhookDocumentoResponse
from app.documento_deal.webhook_auth import verify_webhook_token

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/webhooks/pedido-preparar-doc",
    response_model=WebhookDocumentoResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_webhook_token)],
)
async def webhook_pedido_preparar_doc(
    request: Request,
    payload: PreparaDocWebhookRequest,
) -> WebhookDocumentoResponse:
    """Disparado por workflow HubSpot cuando un Negocio Pedido entra en la etapa
    terminal "Preparar Documentación". Crea (1:1) su Negocio Documento.

    Idempotente y con guard estricto (solo crea si el pedido está en esa etapa).
    Auth: header `X-Webhook-Token` con el secreto compartido.
    """
    started = time.perf_counter()
    client_ip = request.client.host if request.client else "unknown"
    try:
        return await service.crear_documento_desde_pedido(
            pedido_deal_id=payload.pedido_deal_id,
        )
    except Exception as e:
        logger.error(
            f"Error en POST /api/v1/documento-deal/webhooks/pedido-preparar-doc: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        duration_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            f"[documento_webhook_audit] ip={client_ip} "
            f"pedido_deal_id={payload.pedido_deal_id!r} duration_ms={duration_ms}"
        )


@router.post(
    "/sync/{pedido_deal_id}",
    response_model=WebhookDocumentoResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_webhook_token)],
)
async def sync_documento_desde_pedido(pedido_deal_id: str) -> WebhookDocumentoResponse:
    """Re-disparo manual (operaciones), mismo guard estricto + idempotencia. Como
    "Preparar Documentación" es terminal, sirve para recuperar un documento que el
    Workflow no llegara a crear.
    """
    try:
        return await service.crear_documento_desde_pedido(pedido_deal_id=pedido_deal_id)
    except Exception as e:
        logger.error(
            f"Error en POST /api/v1/documento-deal/sync/{pedido_deal_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))
