"""Cambio 2 — Fase 4: docs por EMBARQUE. La subida se aplica a un SUBCONJUNTO
de contenedores seleccionado (no a todos ni solo al primero). Para scope 'deal'
(BL) se replica a los pedido-deals de ese subconjunto.
"""

from app.pedidos import service


def test_resolve_target_contenedores_usa_subconjunto(monkeypatch):
    # Con selección explícita → ese subconjunto (dedup, orden preservado).
    monkeypatch.setattr(
        service, "_get_contenedores_of_pedido",
        lambda client, dids: ["cA", "cB", "cC"],
    )
    assert service._resolve_target_contenedor_ids(None, ["d1"], ["cB", "cC", "cB"]) == ["cB", "cC"]


def test_resolve_target_contenedores_sin_seleccion_todos(monkeypatch):
    # Sin selección → todos los del pedido (subir una vez y replicar a todos).
    monkeypatch.setattr(
        service, "_get_contenedores_of_pedido",
        lambda client, dids: ["cA", "cB", "cC"],
    )
    assert service._resolve_target_contenedor_ids(None, ["d1"], None) == ["cA", "cB", "cC"]


def test_resolve_target_pedido_deals_del_subconjunto(monkeypatch):
    # BL (scope deal): replica solo a los pedido-deals de los contenedores
    # seleccionados, intersecando con los pedido-deals del pedido.
    monkeypatch.setattr(
        service, "_get_deal_ids_for_contenedores",
        lambda client, cids: {"cA": ["dCotA", "dPedA"], "cB": ["dPedB"]},
    )
    pedido_deal_ids = ["dPedA", "dPedB", "dPedC"]
    out = service._resolve_target_pedido_deal_ids(None, pedido_deal_ids, ["cA", "cB"])
    assert out == ["dPedA", "dPedB"]  # dCotA (cotización) excluido, dPedC no seleccionado


def test_resolve_target_pedido_deals_fallback_todos(monkeypatch):
    # Si no se resuelve ninguno, cae a todos los pedido-deals (no romper).
    monkeypatch.setattr(
        service, "_get_deal_ids_for_contenedores",
        lambda client, cids: {},
    )
    assert service._resolve_target_pedido_deal_ids(None, ["d1", "d2"], ["cX"]) == ["d1", "d2"]
