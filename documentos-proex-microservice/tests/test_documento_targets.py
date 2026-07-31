"""Migración BL/booking a Negocio Documento + Negocio Pedido (Documento manda).
Cubre el resolver de Documento-deals (filtra por pipeline) y la réplica del
borrado de fichero BL a los Documento-deals. Mocks de HubSpot; no toca red.
"""

from app.core.constants import (
    DEAL_PROP_PIPELINE,
    DOCUMENTO_PIPELINE_ID,
    FILE_TYPE_BL_BORRADOR,
    PEDIDO_PIPELINE_ID,
)
from app.pedidos import service
from app.pedidos.schemas import UpdatePedidoBLRequest


def test_resolve_documento_deal_ids_filtra_por_pipeline(monkeypatch):
    monkeypatch.setattr(
        service, "_get_deal_ids_for_contenedores",
        lambda c, cids: {"cA": ["dCot", "dPed", "dDoc"]},
    )
    monkeypatch.setattr(
        service, "_batch_read_deals_min",
        lambda c, dids: {
            "dCot": {DEAL_PROP_PIPELINE: "otro"},
            "dPed": {DEAL_PROP_PIPELINE: PEDIDO_PIPELINE_ID},
            "dDoc": {DEAL_PROP_PIPELINE: DOCUMENTO_PIPELINE_ID},
        },
    )
    assert service._resolve_target_documento_deal_ids(None, ["cA"]) == ["dDoc"]


def test_resolve_documento_deal_ids_sin_contenedores_vacio():
    assert service._resolve_target_documento_deal_ids(None, []) == []


def test_delete_deal_scope_quita_tambien_del_documento(monkeypatch):
    monkeypatch.setattr(service.hubspot_client, "get_client", lambda: object())
    monkeypatch.setattr(service, "_verify_pedido_belongs_to_company", lambda c, n, comp: ["dPedA"])
    monkeypatch.setattr(service, "_resolve_target_contenedor_ids", lambda c, pd, cids: ["cA"])
    monkeypatch.setattr(
        service, "_resolve_target_pedido_deal_ids",
        lambda c, pd, tcids, allow_fallback=True: ["dPedA"],
    )
    monkeypatch.setattr(service, "_resolve_target_documento_deal_ids", lambda c, cids: ["dDocA"])
    monkeypatch.setattr(
        service, "_read_deal_prop_value",
        lambda c, did, prop: service.serialize_file_ids(["f1", "f9"]),
    )
    patches = []
    monkeypatch.setattr(service, "_patch_pedido_deals", lambda c, dids, p: patches.append((list(dids), dict(p))))
    monkeypatch.setattr(service, "delete_file", lambda fid: None)

    resp = service._delete_pedido_file_sync("P1", "comp", "f1", FILE_TYPE_BL_BORRADOR, ["cA"])

    assert resp.success is True
    prop = service.FILE_TYPE_CONFIG[FILE_TYPE_BL_BORRADOR]["prop"]
    # Se quita f1 tanto del pedido-deal como del documento-deal del contenedor.
    assert patches == [
        (["dPedA"], {prop: service.serialize_file_ids(["f9"])}),
        (["dDocA"], {prop: service.serialize_file_ids(["f9"])}),
    ]


def test_bl_seleccion_sin_pedido_deal_no_ensancha(monkeypatch):
    # Selección explícita pero sin pedido-deal resoluble: NO debe caer a "todos los
    # pedido-deals" (sería una escritura BL global). Igual criterio que el borrado.
    monkeypatch.setattr(service.hubspot_client, "get_client", lambda: object())
    monkeypatch.setattr(service, "_verify_pedido_belongs_to_company", lambda c, n, comp: ["dPedA", "dPedB"])
    monkeypatch.setattr(service, "_resolve_target_contenedor_ids", lambda c, pd, cids: ["cA"])
    monkeypatch.setattr(
        service, "_resolve_target_pedido_deal_ids",
        lambda c, pd, tcids, allow_fallback=True: [] if not allow_fallback else list(pd),
    )
    monkeypatch.setattr(service, "_resolve_target_documento_deal_ids", lambda c, cids: [])
    patches = []
    monkeypatch.setattr(service, "_patch_pedido_deals", lambda c, dids, p: patches.append(list(dids)) or len(dids))
    monkeypatch.setattr(service, "_recalcular_documentos_best_effort", lambda c, n: None)

    resp = service._update_pedido_bl_sync(
        "P1", "comp", UpdatePedidoBLRequest(bl_validado_administracion=True, contenedor_ids=["cA"]),
    )

    assert resp.success is False
    assert patches == []  # no se escribió en ningún deal (no se ensanchó al pedido)
