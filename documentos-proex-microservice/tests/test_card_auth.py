"""Auth de la card: sin exigencia en debug, 503 sin secreto, 401 header
inválido/ausente, OK con Bearer correcto en producción.
"""

import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core import card_auth


def _req():
    return SimpleNamespace(client=SimpleNamespace(host="1.2.3.4"))


def test_debug_no_exige_header(monkeypatch):
    monkeypatch.setattr(card_auth.settings, "debug", True)
    asyncio.run(card_auth.verify_card_secret(_req(), None))


def test_503_sin_secreto_configurado(monkeypatch):
    monkeypatch.setattr(card_auth.settings, "debug", False)
    monkeypatch.setattr(card_auth.settings, "proex_card_secret", None)
    with pytest.raises(HTTPException) as ei:
        asyncio.run(card_auth.verify_card_secret(_req(), "Bearer lo-que-sea"))
    assert ei.value.status_code == 503


def test_401_header_ausente(monkeypatch):
    monkeypatch.setattr(card_auth.settings, "debug", False)
    monkeypatch.setattr(card_auth.settings, "proex_card_secret", "S3CRET")
    with pytest.raises(HTTPException) as ei:
        asyncio.run(card_auth.verify_card_secret(_req(), None))
    assert ei.value.status_code == 401


def test_401_secreto_incorrecto(monkeypatch):
    monkeypatch.setattr(card_auth.settings, "debug", False)
    monkeypatch.setattr(card_auth.settings, "proex_card_secret", "S3CRET")
    with pytest.raises(HTTPException) as ei:
        asyncio.run(card_auth.verify_card_secret(_req(), "Bearer incorrecto"))
    assert ei.value.status_code == 401


def test_ok_con_bearer_correcto(monkeypatch):
    monkeypatch.setattr(card_auth.settings, "debug", False)
    monkeypatch.setattr(card_auth.settings, "proex_card_secret", "S3CRET")
    asyncio.run(card_auth.verify_card_secret(_req(), "Bearer S3CRET"))
