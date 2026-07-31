"""Creación 1:1 del Negocio Documento desde un pedido en "Preparar Documentación".
Idempotente, con guard estricto de etapa y defensivos. La red HubSpot se mockea.
"""

from types import SimpleNamespace

from hubspot.crm.deals.exceptions import NotFoundException

from app.core.constants import (
    DOC_DEALSTAGE_EN_PROCESO,
    DOCUMENTO_PIPELINE_ID,
    PEDIDO_DEALSTAGE_PREPARAR_DOC,
    PEDIDO_PIPELINE_ID,
)
from app.documento_deal import service


def _fake_client(pedido_props, not_found=False):
    def get_by_id(deal_id, properties=None):
        if not_found:
            raise NotFoundException(status=404, reason="not found")
        return SimpleNamespace(properties=pedido_props)
    return SimpleNamespace(
        crm=SimpleNamespace(deals=SimpleNamespace(basic_api=SimpleNamespace(get_by_id=get_by_id)))
    )


def _patch_common(monkeypatch, client, contenedor_map, deals_min):
    monkeypatch.setattr(service.hubspot_client, "get_client", lambda: client)
    monkeypatch.setattr(
        service, "batch_read_associations",
        lambda c, frm, to, ids: {ids[0]: contenedor_map} if ids else {},
    )
    monkeypatch.setattr(
        service, "_get_deal_ids_for_contenedores",
        lambda c, cids: {cids[0]: list(deals_min.keys())},
    )
    monkeypatch.setattr(service, "_batch_read_deals_min", lambda c, dids: deals_min)
    monkeypatch.setattr(service, "_read_documento_replica_props", lambda c, pid: {"numero_de_pedido": "P-1"})
    monkeypatch.setattr(service, "batch_read_objects", lambda c, ot, ids, props: {ids[0]: {"nombre": "CN-uno"}})
    monkeypatch.setattr(service, "_recalcular_dealstage_para_documento", lambda c, did: False)


def _pedido_props(dealstage=PEDIDO_DEALSTAGE_PREPARAR_DOC, pipeline=PEDIDO_PIPELINE_ID):
    return {"pipeline": pipeline, "dealstage": dealstage, "numero_de_pedido": "P-1"}


def test_crea_documento_con_asociaciones(monkeypatch):
    deals_min = {
        "dCot": {"pipeline": "otro", "numero_de_pedido": ""},
        "dPed": {"pipeline": PEDIDO_PIPELINE_ID, "numero_de_pedido": "P-1"},
    }
    _patch_common(monkeypatch, _fake_client(_pedido_props()), ["cA"], deals_min)

    created = {}
    monkeypatch.setattr(
        service, "_create_documento_deal",
        lambda c, props, dealname: created.update(props=props, dealname=dealname) or "dDoc",
    )
    assocs = {}
    monkeypatch.setattr(
        service, "_crear_asociaciones_documento",
        lambda c, doc, cn, ped, cot: assocs.update(doc=doc, cn=cn, ped=ped, cot=cot),
    )

    resp = service._crear_documento_desde_pedido_sync("dPed")

    assert resp.success is True
    assert resp.estado == "creado"
    assert resp.documento_deal_id == "dDoc"
    assert resp.contenedor_id == "cA"
    assert created["dealname"] == "DOC P-1 (CN-uno)"
    assert assocs == {"doc": "dDoc", "cn": "cA", "ped": "dPed", "cot": "dCot"}


def test_create_documento_deal_fija_pipeline_y_etapa(monkeypatch):
    captured = {}

    def _create(simple_public_object_input_for_create=None):
        captured["props"] = dict(simple_public_object_input_for_create.properties)
        return SimpleNamespace(id="dDoc")

    client = SimpleNamespace(
        crm=SimpleNamespace(deals=SimpleNamespace(basic_api=SimpleNamespace(create=_create)))
    )
    did = service._create_documento_deal(client, {"numero_de_pedido": "P-1"}, "DOC P-1")

    assert did == "dDoc"
    assert captured["props"]["pipeline"] == DOCUMENTO_PIPELINE_ID
    assert captured["props"]["dealstage"] == DOC_DEALSTAGE_EN_PROCESO
    assert captured["props"]["numero_de_pedido"] == "P-1"
    assert captured["props"]["dealname"] == "DOC P-1"


def test_responsables_se_replican_al_crear_documento(monkeypatch):
    pedido_props = {
        "numero_de_pedido": "P-1",
        "responsable_comercial": "Ana",
        "responsable_administracion": "Bea",
        "responsable_logistica": "Cris",
    }
    captured = {}

    def get_by_id(deal_id, properties=None):
        captured["properties"] = properties
        return SimpleNamespace(properties=pedido_props)

    client = SimpleNamespace(
        crm=SimpleNamespace(deals=SimpleNamespace(basic_api=SimpleNamespace(get_by_id=get_by_id)))
    )

    result = service._read_documento_replica_props(client, "dPed")

    assert {"responsable_comercial", "responsable_administracion", "responsable_logistica"} <= set(
        captured["properties"]
    )
    assert result["responsable_comercial"] == "Ana"
    assert result["responsable_administracion"] == "Bea"
    assert result["responsable_logistica"] == "Cris"


def test_idempotente_si_ya_existe_documento(monkeypatch):
    deals_min = {
        "dDocPrev": {"pipeline": DOCUMENTO_PIPELINE_ID, "numero_de_pedido": "P-1"},
        "dPed": {"pipeline": PEDIDO_PIPELINE_ID, "numero_de_pedido": "P-1"},
    }
    _patch_common(monkeypatch, _fake_client(_pedido_props()), ["cA"], deals_min)

    def _no_crear(*a, **k):
        raise AssertionError("no debe crear un documento si ya existe")

    monkeypatch.setattr(service, "_create_documento_deal", _no_crear)
    monkeypatch.setattr(service, "_crear_asociaciones_documento", _no_crear)

    resp = service._crear_documento_desde_pedido_sync("dPed")

    assert resp.success is True
    assert resp.estado == "saltado"
    assert resp.documento_deal_id == "dDocPrev"


def test_camion_no_crea_documento(monkeypatch):
    deals_min = {
        "dCot": {"pipeline": "otro", "numero_de_pedido": ""},
        "dPed": {"pipeline": PEDIDO_PIPELINE_ID, "numero_de_pedido": "P-1"},
    }
    _patch_common(monkeypatch, _fake_client(_pedido_props()), ["cCamion"], deals_min)
    monkeypatch.setattr(
        service, "batch_read_objects",
        lambda c, ot, ids, props: {ids[0]: {"tipo_contenedor": "TRAILER 80"}},
    )

    def _no_crear(*a, **k):
        raise AssertionError("camión no debe crear Negocio Documento")

    monkeypatch.setattr(service, "_create_documento_deal", _no_crear)
    monkeypatch.setattr(service, "_crear_asociaciones_documento", _no_crear)

    resp = service._crear_documento_desde_pedido_sync("dPed")

    assert resp.success is True
    assert resp.estado == "saltado_camion"
    assert resp.contenedor_id == "cCamion"
    assert resp.documento_deal_id is None


def test_guard_estricto_rechaza_si_no_esta_en_preparar_doc(monkeypatch):
    _patch_common(
        monkeypatch,
        _fake_client(_pedido_props(dealstage="1368383243")),  # facturado, no preparar doc
        ["cA"], {},
    )
    resp = service._crear_documento_desde_pedido_sync("dPed")
    assert resp.success is False
    assert resp.estado == "fallido"
    assert resp.error == "pedido_no_en_preparar_documentacion"


def test_rechaza_si_no_es_pedido(monkeypatch):
    _patch_common(
        monkeypatch, _fake_client(_pedido_props(pipeline="otro")), ["cA"], {},
    )
    resp = service._crear_documento_desde_pedido_sync("dX")
    assert resp.success is False
    assert resp.error == "deal_no_es_pedido"


def test_pedido_no_encontrado(monkeypatch):
    monkeypatch.setattr(service.hubspot_client, "get_client", lambda: _fake_client({}, not_found=True))
    resp = service._crear_documento_desde_pedido_sync("dNo")
    assert resp.success is False
    assert resp.error == "pedido_deal_no_encontrado"


def test_pedido_sin_contenedor(monkeypatch):
    client = _fake_client(_pedido_props())
    monkeypatch.setattr(service.hubspot_client, "get_client", lambda: client)
    monkeypatch.setattr(service, "batch_read_associations", lambda c, frm, to, ids: {ids[0]: []})
    resp = service._crear_documento_desde_pedido_sync("dPed")
    assert resp.success is False
    assert resp.error == "pedido_sin_contenedor"
