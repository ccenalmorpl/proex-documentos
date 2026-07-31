from typing import Optional

from pydantic import BaseModel, field_validator


class PreparaDocWebhookRequest(BaseModel):
    pedido_deal_id: str

    @field_validator("pedido_deal_id", mode="before")
    @classmethod
    def _coerce_id_a_str(cls, v):
        # HubSpot envía hs_object_id como número en la acción "Enviar webhook".
        return str(v) if v is not None else v


class WebhookDocumentoResponse(BaseModel):
    success: bool
    estado: str  # creado | saltado | saltado_camion | fallido
    pedido_deal_id: str
    contenedor_id: Optional[str] = None
    documento_deal_id: Optional[str] = None
    error: Optional[str] = None
