"""ETD/ETA por contenedor (tab Gestión de Documentación): editarlas escribe en los
deals del contenedor (Negocio Pedido + Negocio Documento), convirtiendo la fecha ISO
a epoch-ms de HubSpot y escribiendo solo los campos enviados.
"""

from app.core.constants import DEAL_PROP_ETA, DEAL_PROP_ETD
from app.pedidos import service
from app.pedidos.schemas import UpdateContenedorFechasRequest


def _common(monkeypatch, pedido_deal_ids, contenedores):
    monkeypatch.setattr(service.hubspot_client, "get_client", lambda: object())
    monkeypatch.setattr(service, "_verify_pedido_belongs_to_company", lambda c, n, comp: pedido_deal_ids)
    monkeypatch.setattr(service, "_get_contenedores_of_pedido", lambda c, dids: contenedores)


def test_etd_se_escribe_en_pedido_y_documento_convertida_a_ms(monkeypatch):
    _common(monkeypatch, ["dPedA", "dPedB"], ["cA", "cB"])
    monkeypatch.setattr(
        service, "_get_deal_ids_for_contenedores",
        lambda c, cids: {"cA": ["dCotA", "dPedA"]},
    )
    monkeypatch.setattr(service, "_resolve_target_documento_deal_ids", lambda c, cids: ["dDocA"])
    patches = []
    monkeypatch.setattr(service, "_patch_pedido_deals", lambda c, dids, p: patches.append((list(dids), dict(p))) or len(dids))

    resp = service._update_contenedor_fechas_sync(
        "P1", "comp", "cA", UpdateContenedorFechasRequest(etd="2026-01-15"),
    )

    assert resp.success is True
    ms = service._hubspot_date_from_iso("2026-01-15")
    # Solo etd (eta no enviada), en pedido-deal y documento-deal del contenedor.
    assert patches == [
        (["dPedA"], {DEAL_PROP_ETD: ms}),
        (["dDocA"], {DEAL_PROP_ETD: ms}),
    ]


def test_solo_se_escriben_los_campos_enviados(monkeypatch):
    _common(monkeypatch, ["dPedA"], ["cA"])
    monkeypatch.setattr(service, "_get_deal_ids_for_contenedores", lambda c, cids: {"cA": ["dPedA"]})
    monkeypatch.setattr(service, "_resolve_target_documento_deal_ids", lambda c, cids: [])
    patches = []
    monkeypatch.setattr(
        service, "_patch_pedido_deals",
        lambda c, dids, p: (patches.append(dict(p)) if dids else None) or len(dids),
    )

    # eta="" (borrar) sin etd → solo la clave eta.
    resp = service._update_contenedor_fechas_sync(
        "P1", "comp", "cA", UpdateContenedorFechasRequest(eta=""),
    )

    assert resp.success is True
    assert patches == [{DEAL_PROP_ETA: ""}]


def test_sin_campos_es_noop(monkeypatch):
    _common(monkeypatch, ["dPedA"], ["cA"])
    patches = []
    monkeypatch.setattr(service, "_patch_pedido_deals", lambda c, dids, p: patches.append(dids))

    resp = service._update_contenedor_fechas_sync(
        "P1", "comp", "cA", UpdateContenedorFechasRequest(),
    )

    assert resp.success is True
    assert patches == []


def test_contenedor_ajeno_al_pedido_rechazado(monkeypatch):
    _common(monkeypatch, ["dPedA"], ["cA"])
    patches = []
    monkeypatch.setattr(service, "_patch_pedido_deals", lambda c, dids, p: patches.append(dids))

    resp = service._update_contenedor_fechas_sync(
        "P1", "comp", "cZ", UpdateContenedorFechasRequest(etd="2026-01-15"),
    )

    assert resp.success is False
    assert "no pertenece" in (resp.error or "")
    assert patches == []
