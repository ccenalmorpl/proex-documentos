"""Auth del webhook del Negocio Documento: 503 sin secreto, 401 token inválido/
ausente, OK con token correcto.
"""

import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.documento_deal import webhook_auth


def _req():
    return SimpleNamespace(client=SimpleNamespace(host="1.2.3.4"))


def test_503_sin_secreto_configurado(monkeypatch):
    monkeypatch.setattr(webhook_auth.settings, "hubspot_webhook_secret", None)
    with pytest.raises(HTTPException) as ei:
        asyncio.run(webhook_auth.verify_webhook_token(_req(), "lo-que-sea"))
    assert ei.value.status_code == 503


def test_401_token_invalido(monkeypatch):
    monkeypatch.setattr(webhook_auth.settings, "hubspot_webhook_secret", "S3CRET")
    with pytest.raises(HTTPException) as ei:
        asyncio.run(webhook_auth.verify_webhook_token(_req(), "incorrecto"))
    assert ei.value.status_code == 401


def test_401_token_ausente(monkeypatch):
    monkeypatch.setattr(webhook_auth.settings, "hubspot_webhook_secret", "S3CRET")
    with pytest.raises(HTTPException) as ei:
        asyncio.run(webhook_auth.verify_webhook_token(_req(), None))
    assert ei.value.status_code == 401


def test_ok_con_token_valido(monkeypatch):
    monkeypatch.setattr(webhook_auth.settings, "hubspot_webhook_secret", "S3CRET")
    asyncio.run(webhook_auth.verify_webhook_token(_req(), "S3CRET"))


def test_payload_acepta_id_numerico_de_hubspot():
    # HubSpot manda hs_object_id como número en la acción "Enviar webhook".
    from app.documento_deal.schemas import PreparaDocWebhookRequest

    req = PreparaDocWebhookRequest(pedido_deal_id=60314473089)
    assert req.pedido_deal_id == "60314473089"
    assert isinstance(req.pedido_deal_id, str)

    req_str = PreparaDocWebhookRequest(pedido_deal_id="60314473089")
    assert req_str.pedido_deal_id == "60314473089"
