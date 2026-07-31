"""Cambio 2 — el booking es INDIVIDUAL por contenedor: editarlo en Documentos
escribe SOLO en los deals (Negocio Pedido + Negocio Documento) de ese contenedor,
NO se replica a todos. Un pedido puede tener bookings distintos por embarque.
"""

from app.core.constants import DEAL_PROP_NUMERO_DE_BOOKING
from app.pedidos import service
from app.pedidos.schemas import UpdateContenedorBookingRequest


def _common(monkeypatch, pedido_deal_ids, contenedores):
    monkeypatch.setattr(service.hubspot_client, "get_client", lambda: object())
    monkeypatch.setattr(service, "_verify_pedido_belongs_to_company", lambda c, n, comp: pedido_deal_ids)
    monkeypatch.setattr(service, "_get_contenedores_of_pedido", lambda c, dids: contenedores)


def test_booking_se_escribe_en_pedido_y_documento_del_contenedor(monkeypatch):
    _common(monkeypatch, ["dPedA", "dPedB"], ["cA", "cB"])
    # cA está asociado a su cotización y a su pedido-deal; solo el pedido-deal cuenta.
    monkeypatch.setattr(
        service, "_get_deal_ids_for_contenedores",
        lambda c, cids: {"cA": ["dCotA", "dPedA"]},
    )
    # Documento manda: el booking se escribe también en el Negocio Documento de cA.
    monkeypatch.setattr(service, "_resolve_target_documento_deal_ids", lambda c, cids: ["dDocA"])
    patches = []
    monkeypatch.setattr(service, "_patch_pedido_deals", lambda c, dids, p: patches.append((list(dids), dict(p))) or len(dids))

    resp = service._update_contenedor_booking_sync(
        "P1", "comp", "cA", UpdateContenedorBookingRequest(numero_de_booking="BK-A"),
    )

    assert resp.success is True
    # Pedido-deal y Documento-deal del contenedor; NO dPedB (de otro contenedor).
    assert patches == [
        (["dPedA"], {DEAL_PROP_NUMERO_DE_BOOKING: "BK-A"}),
        (["dDocA"], {DEAL_PROP_NUMERO_DE_BOOKING: "BK-A"}),
    ]


def test_booking_contenedor_ajeno_al_pedido_rechazado(monkeypatch):
    _common(monkeypatch, ["dPedA"], ["cA"])
    patches = []
    monkeypatch.setattr(service, "_patch_pedido_deals", lambda c, dids, p: patches.append(dids))

    resp = service._update_contenedor_booking_sync(
        "P1", "comp", "cZ", UpdateContenedorBookingRequest(numero_de_booking="BK-X"),
    )

    assert resp.success is False
    assert "no pertenece" in (resp.error or "")
    assert patches == []


def test_booking_vacio_permitido_para_borrar(monkeypatch):
    _common(monkeypatch, ["dPedA"], ["cA"])
    monkeypatch.setattr(
        service, "_get_deal_ids_for_contenedores", lambda c, cids: {"cA": ["dPedA"]},
    )
    monkeypatch.setattr(service, "_resolve_target_documento_deal_ids", lambda c, cids: ["dDocA"])
    patches = []
    monkeypatch.setattr(service, "_patch_pedido_deals", lambda c, dids, p: patches.append((list(dids), dict(p))) or len(dids))

    resp = service._update_contenedor_booking_sync(
        "P1", "comp", "cA", UpdateContenedorBookingRequest(numero_de_booking=""),
    )

    assert resp.success is True
    assert patches == [
        (["dPedA"], {DEAL_PROP_NUMERO_DE_BOOKING: ""}),
        (["dDocA"], {DEAL_PROP_NUMERO_DE_BOOKING: ""}),
    ]


def test_booking_none_es_obligatorio(monkeypatch):
    _common(monkeypatch, ["dPedA"], ["cA"])
    resp = service._update_contenedor_booking_sync(
        "P1", "comp", "cA", UpdateContenedorBookingRequest(),
    )
    assert resp.success is False
    assert "obligatorio" in (resp.error or "")
