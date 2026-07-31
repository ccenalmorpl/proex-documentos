"""Cambio 2 — el borrado de un documento es simétrico a la subida por EMBARQUE:
si un doc se replicó a un subconjunto de contenedores, al quitarlo se elimina de
TODOS ellos (scope contenedor) o de los pedido-deals del subconjunto (scope deal).
Los helpers de HubSpot se sustituyen por mocks; no toca red.
"""

from app.core.constants import (
    CONTENEDOR_PROP_DOCUMENTOS,
    FILE_TYPE_BL_BORRADOR,
    FILE_TYPE_DOC_DUA,
)
from app.pedidos import service


def _common(monkeypatch, deal_ids):
    monkeypatch.setattr(service.hubspot_client, "get_client", lambda: object())
    monkeypatch.setattr(service, "_verify_pedido_belongs_to_company", lambda c, n, comp: deal_ids)
    # Por defecto sin Negocio Documento (los tests scope-deal aíslan el pedido).
    monkeypatch.setattr(service, "_resolve_target_documento_deal_ids", lambda c, cids: [])


def test_delete_contenedor_scope_quita_de_cada_seleccionado(monkeypatch):
    _common(monkeypatch, ["dPed1", "dPed2"])
    monkeypatch.setattr(service, "_resolve_target_contenedor_ids", lambda c, pd, cids: list(cids or []))

    props = {
        "cA": service.serialize_file_ids(["f1", "f2"]),
        "cB": service.serialize_file_ids(["f1"]),
    }
    monkeypatch.setattr(service, "_read_contenedor_prop_value", lambda c, cid, prop: props.get(cid))

    patches = []
    monkeypatch.setattr(
        service, "_patch_contenedores_batch",
        lambda c, cids, p: patches.append((list(cids), dict(p))),
    )
    deleted = []
    monkeypatch.setattr(service, "delete_file", lambda fid: deleted.append(fid))

    resp = service._delete_pedido_file_sync("P1", "comp", "f1", FILE_TYPE_DOC_DUA, ["cA", "cB"])

    assert resp.success is True
    # f1 se quita de los dos: cA queda con f2, cB queda vacío.
    assert ([["cA"], {CONTENEDOR_PROP_DOCUMENTOS: service.serialize_file_ids(["f2"])}]
            in [list(p) for p in patches])
    assert ([["cB"], {CONTENEDOR_PROP_DOCUMENTOS: service.serialize_file_ids([])}]
            in [list(p) for p in patches])
    assert deleted == ["f1"]


def test_delete_contenedor_scope_file_no_presente_no_borra(monkeypatch):
    _common(monkeypatch, ["dPed1"])
    monkeypatch.setattr(service, "_resolve_target_contenedor_ids", lambda c, pd, cids: list(cids or []))
    monkeypatch.setattr(
        service, "_read_contenedor_prop_value",
        lambda c, cid, prop: service.serialize_file_ids(["f1"]),
    )
    patches = []
    monkeypatch.setattr(service, "_patch_contenedores_batch", lambda c, cids, p: patches.append(cids))
    deleted = []
    monkeypatch.setattr(service, "delete_file", lambda fid: deleted.append(fid))

    resp = service._delete_pedido_file_sync("P1", "comp", "fX", FILE_TYPE_DOC_DUA, ["cA", "cB"])

    assert resp.success is False
    assert "no presente" in (resp.error or "")
    assert patches == []   # no se parchea nada
    assert deleted == []   # ni se borra el fichero físico


def test_delete_deal_scope_subconjunto_resuelve_pedido_deals(monkeypatch):
    _common(monkeypatch, ["dPedA", "dPedB", "dPedC"])
    monkeypatch.setattr(service, "_resolve_target_contenedor_ids", lambda c, pd, cids: list(cids or []))
    monkeypatch.setattr(
        service, "_resolve_target_pedido_deal_ids",
        lambda c, pd, tcids, allow_fallback=True: ["dPedA"],
    )
    monkeypatch.setattr(
        service, "_read_deal_prop_value",
        lambda c, did, prop: service.serialize_file_ids(["f1", "f9"]),
    )
    patches = []
    monkeypatch.setattr(service, "_patch_pedido_deals", lambda c, dids, p: patches.append((list(dids), dict(p))))
    monkeypatch.setattr(service, "delete_file", lambda fid: None)

    resp = service._delete_pedido_file_sync("P1", "comp", "f1", FILE_TYPE_BL_BORRADOR, ["cA"])

    assert resp.success is True
    # Solo se parchea el pedido-deal del subconjunto, dejando f9.
    assert patches == [(["dPedA"], {service.FILE_TYPE_CONFIG[FILE_TYPE_BL_BORRADOR]["prop"]:
                                    service.serialize_file_ids(["f9"])})]


def test_delete_deal_scope_per_deal_no_pisa_divergentes(monkeypatch):
    # Props divergentes entre pedido-deals (subidas a subconjuntos distintos):
    # borrar f1 NO debe pisar fB del deal que no lo tiene.
    _common(monkeypatch, ["dPedA", "dPedB"])
    monkeypatch.setattr(service, "_resolve_target_contenedor_ids", lambda c, pd, cids: ["cA", "cB"])
    monkeypatch.setattr(
        service, "_resolve_target_pedido_deal_ids",
        lambda c, pd, tcids, allow_fallback=True: ["dPedA", "dPedB"],
    )
    valores = {
        "dPedA": service.serialize_file_ids(["f1", "fA"]),
        "dPedB": service.serialize_file_ids(["fB"]),  # NO tiene f1
    }
    monkeypatch.setattr(service, "_read_deal_prop_value", lambda c, did, prop: valores[did])
    patches = []
    monkeypatch.setattr(service, "_patch_pedido_deals", lambda c, dids, p: patches.append((list(dids), dict(p))))
    monkeypatch.setattr(service, "delete_file", lambda fid: None)

    resp = service._delete_pedido_file_sync("P1", "comp", "f1", FILE_TYPE_BL_BORRADOR, ["cA", "cB"])

    assert resp.success is True
    prop = service.FILE_TYPE_CONFIG[FILE_TYPE_BL_BORRADOR]["prop"]
    # Solo se toca dPedA (dejando fA); dPedB intacto (conserva fB).
    assert patches == [(["dPedA"], {prop: service.serialize_file_ids(["fA"])})]


def test_delete_deal_scope_file_solo_en_deal_no_primero(monkeypatch):
    # f1 está en el segundo pedido-deal pero no en el primero: igual se borra.
    _common(monkeypatch, ["dPedA", "dPedB"])
    monkeypatch.setattr(service, "_resolve_target_contenedor_ids", lambda c, pd, cids: ["cA", "cB"])
    monkeypatch.setattr(
        service, "_resolve_target_pedido_deal_ids",
        lambda c, pd, tcids, allow_fallback=True: ["dPedA", "dPedB"],
    )
    valores = {"dPedA": service.serialize_file_ids(["fA"]), "dPedB": service.serialize_file_ids(["f1"])}
    monkeypatch.setattr(service, "_read_deal_prop_value", lambda c, did, prop: valores[did])
    patches = []
    monkeypatch.setattr(service, "_patch_pedido_deals", lambda c, dids, p: patches.append(list(dids)))
    deleted = []
    monkeypatch.setattr(service, "delete_file", lambda fid: deleted.append(fid))

    resp = service._delete_pedido_file_sync("P1", "comp", "f1", FILE_TYPE_BL_BORRADOR, ["cA", "cB"])

    assert resp.success is True
    assert patches == [["dPedB"]]   # solo el deal que lo tenía
    assert deleted == ["f1"]


def test_delete_deal_scope_sin_seleccion_todos_los_pedido_deals(monkeypatch):
    _common(monkeypatch, ["dPedA", "dPedB"])
    monkeypatch.setattr(service, "_get_contenedores_of_pedido", lambda c, dids: ["cA", "cB"])
    monkeypatch.setattr(
        service, "_read_deal_prop_value",
        lambda c, did, prop: service.serialize_file_ids(["f1"]),
    )
    patches = []
    monkeypatch.setattr(service, "_patch_pedido_deals", lambda c, dids, p: patches.append(list(dids)))
    monkeypatch.setattr(service, "delete_file", lambda fid: None)

    resp = service._delete_pedido_file_sync("P1", "comp", "f1", FILE_TYPE_BL_BORRADOR, None)

    assert resp.success is True
    # sin selección → cada pedido-deal se recalcula y parchea por separado.
    assert patches == [["dPedA"], ["dPedB"]]


def test_delete_deal_scope_seleccion_sin_pedido_deal_no_ensancha(monkeypatch):
    # Selección válida de contenedores pero sin pedido-deal resoluble: NO debe
    # caer a "todos los pedido-deals" (sería borrado global destructivo).
    _common(monkeypatch, ["dPedA", "dPedB"])
    monkeypatch.setattr(service, "_resolve_target_contenedor_ids", lambda c, pd, cids: ["cA"])
    monkeypatch.setattr(
        service, "_resolve_target_pedido_deal_ids",
        lambda c, pd, tcids, allow_fallback=True: [] if not allow_fallback else list(pd),
    )
    patches = []
    monkeypatch.setattr(service, "_patch_pedido_deals", lambda c, dids, p: patches.append(list(dids)))
    deleted = []
    monkeypatch.setattr(service, "delete_file", lambda fid: deleted.append(fid))

    resp = service._delete_pedido_file_sync("P1", "comp", "f1", FILE_TYPE_BL_BORRADOR, ["cA"])

    assert resp.success is False
    assert patches == []   # no se parchea nada
    assert deleted == []   # ni se borra el fichero físico


def test_resolve_target_contenedores_intersecta_con_pedido(monkeypatch):
    # IDOR: una selección con cids ajenos al pedido se descarta (no se confía en el cliente).
    monkeypatch.setattr(
        service, "_get_contenedores_of_pedido", lambda client, dids: ["cA", "cB", "cC"],
    )
    assert service._resolve_target_contenedor_ids(None, ["d1"], ["cB", "cX", "cB"]) == ["cB"]
    assert service._resolve_target_contenedor_ids(None, ["d1"], ["cZ"]) == []
