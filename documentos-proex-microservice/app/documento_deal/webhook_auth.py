"""Auth para los endpoints `/webhooks/*` del módulo documento_deal."""

import hmac
import logging
from typing import Optional

from fastapi import Header, HTTPException, Request, status

from app.core.config import settings

logger = logging.getLogger(__name__)


async def verify_webhook_token(
    request: Request,
    x_webhook_token: Optional[str] = Header(default=None),
) -> None:
    """Valida el header `X-Webhook-Token` contra `HUBSPOT_WEBHOOK_SECRET`.

    503 si el secreto no está configurado en el server; 401 si el header falta
    o no coincide (mensaje genérico para no filtrar información al cliente).
    """
    expected = settings.hubspot_webhook_secret
    if not expected:
        logger.error(
            "[webhook_auth] HUBSPOT_WEBHOOK_SECRET no configurado en el server"
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "webhook_secret_not_configured"},
        )

    received = x_webhook_token or ""
    if not hmac.compare_digest(received, expected):
        client_ip = request.client.host if request.client else "unknown"
        logger.warning(
            f"[webhook_auth] token inválido o ausente desde ip={client_ip}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_or_missing_token"},
        )
