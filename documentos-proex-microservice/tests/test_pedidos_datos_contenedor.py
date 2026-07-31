"""Edición desde Documentos de los datos físicos del contenedor (número, precinto,
pesos, tara) y del número de booking. Las 4 primeras viven en el Contenedor; el
booking vive en el Negocio Pedido y se replica a los N deals del grupo. Los
helpers de HubSpot se sustituyen por mocks; no toca red.
"""

import pytest

from app.pedidos import service
from app.pedidos.schemas import UpdateContenedorDatosRequest, UpdatePedidoBLRequest


def _patch_contenedor_common(monkeypatch, deal_ids, contenedor_ids):
    monkeypatch.setattr(service.hubspot_client, "get_client", lambda: object())
    monkeypatch.setattr(service, "_verify_pedido_belongs_to_company", lambda client, num, comp: deal_ids)
    monkeypatch.setattr(service, "_get_contenedores_of_pedido", lambda client, dids: contenedor_ids)


def test_datos_contenedor_patchea_solo_campos_enviados(monkeypatch):
    captured = {}
    _patch_contenedor_common(monkeypatch, ["d1"], ["c1"])

    def _fake_patch(client, ids, props):
        captured["ids"] = ids
        captured["props"] = props
        return len(ids)

    monkeypatch.setattr(service, "_patch_contenedores_batch", _fake_patch)

    payload = UpdateContenedorDatosRequest(numero_contenedor="MSKU123", peso_bruto="2200")
    res = service._update_contenedor_datos_sync("PED-1", "comp1", "c1", payload)

    assert res.success is True
    assert captured["ids"] == ["c1"]
    assert captured["props"] == {"numero_contenedor": "MSKU123", "peso_bruto": "2200"}
    assert "numero_precinto" not in captured["props"]
    assert "tara" not in captured["props"]


def test_datos_contenedor_permite_vaciar_campo(monkeypatch):
    captured = {}
    _patch_contenedor_common(monkeypatch, ["d1"], ["c1"])
    monkeypatch.setattr(
        service, "_patch_contenedores_batch",
        lambda client, ids, props: captured.update(props) or len(ids),
    )

    payload = UpdateContenedorDatosRequest(numero_precinto="")
    res = service._update_contenedor_datos_sync("PED-1", "comp1", "c1", payload)

    assert res.success is True
    assert captured["numero_precinto"] == ""


def test_datos_contenedor_rechaza_contenedor_ajeno_al_pedido(monkeypatch):
    _patch_contenedor_common(monkeypatch, ["d1"], ["c1"])

    def _no_debe_patchear(*_a, **_k):
        raise AssertionError("no debe llegar a patchear un contenedor ajeno")

    monkeypatch.setattr(service, "_patch_contenedores_batch", _no_debe_patchear)

    payload = UpdateContenedorDatosRequest(numero_contenedor="X")
    res = service._update_contenedor_datos_sync("PED-1", "comp1", "c-ajeno", payload)

    assert res.success is False
    assert "no pertenece" in (res.error or "")


def test_datos_contenedor_sin_campos_es_error(monkeypatch):
    _patch_contenedor_common(monkeypatch, ["d1"], ["c1"])
    monkeypatch.setattr(service, "_patch_contenedores_batch", lambda *a, **k: 1)

    res = service._update_contenedor_datos_sync("PED-1", "comp1", "c1", UpdateContenedorDatosRequest())

    assert res.success is False


def _bl_common(monkeypatch, pedido_deal_ids, target_pedido, target_documento):
    monkeypatch.setattr(service.hubspot_client, "get_client", lambda: object())
    monkeypatch.setattr(service, "_verify_pedido_belongs_to_company", lambda c, n, comp: pedido_deal_ids)
    monkeypatch.setattr(service, "_resolve_target_contenedor_ids", lambda c, pd, cids: list(cids or ["cA"]))
    monkeypatch.setattr(service, "_resolve_target_pedido_deal_ids", lambda c, pd, tcids, allow_fallback=True: target_pedido)
    monkeypatch.setattr(service, "_resolve_target_documento_deal_ids", lambda c, tcids: target_documento)
    monkeypatch.setattr(service, "_recalcular_documentos_best_effort", lambda c, n: None)


def test_bl_se_escribe_en_pedido_y_documento(monkeypatch):
    # El BL aplica a los contenedores seleccionados y se escribe en su Negocio
    # Pedido Y su Negocio Documento (Documento manda). El booking ya no va por aquí.
    _bl_common(monkeypatch, ["dPedA", "dPedB"], ["dPedA"], ["dDocA"])
    patches = []
    monkeypatch.setattr(service, "_patch_pedido_deals", lambda c, dids, p: patches.append((list(dids), dict(p))) or len(dids))

    res = service._update_pedido_bl_sync(
        "PED-1", "comp1", UpdatePedidoBLRequest(bl_validado_logistica=True, contenedor_ids=["cA"]),
    )

    assert res.success is True
    assert patches == [
        (["dPedA"], {"bl_validado_logistica": "true"}),
        (["dDocA"], {"bl_validado_logistica": "true"}),
    ]
    assert "numero_de_booking" not in patches[0][1]


def test_bl_cambios_solicitados_se_persiste(monkeypatch):
    # El nuevo campo de texto libre cambios_en_bl se escribe en Pedido + Documento.
    _bl_common(monkeypatch, ["dPedA"], ["dPedA"], ["dDocA"])
    patches = []
    monkeypatch.setattr(service, "_patch_pedido_deals", lambda c, dids, p: patches.append((list(dids), dict(p))) or len(dids))

    res = service._update_pedido_bl_sync(
        "PED-1", "comp1", UpdatePedidoBLRequest(cambios_en_bl="Cambiar consignee", contenedor_ids=["cA"]),
    )

    assert res.success is True
    assert patches == [
        (["dPedA"], {"cambios_en_bl": "Cambiar consignee"}),
        (["dDocA"], {"cambios_en_bl": "Cambiar consignee"}),
    ]


def test_bl_request_ignora_booking():
    # UpdatePedidoBLRequest ya no expone numero_de_booking; un payload que lo
    # incluyera no debe abrir una vía de escritura compartida del booking.
    assert "numero_de_booking" not in UpdatePedidoBLRequest.model_fields
