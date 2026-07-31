"""Herencia de las rutas de la cotización al Negocio Documento.

Al crear el Negocio Documento (1:1 con el pedido/contenedor), hereda las
asociaciones a Rutas (custom object) preservando category+type_id de cada
etiqueta Deal→Ruta (714 terrestre / 716 marítima), leyéndolas de la cotización
(fallback al pedido si no se resolvió la cotización).
"""

from types import SimpleNamespace

from app.core.constants import (
    ASSOC_CATEGORY_USER_DEFINED,
    OBJECT_TYPE_DEAL,
    OBJECT_TYPE_RUTA,
)
from app.documento_deal import service


def _assoc(to_id, types):
    return SimpleNamespace(
        to_object_id=to_id,
        association_types=[
            SimpleNamespace(category=cat, type_id=tid) for cat, tid in types
        ],
    )


def _client_with_ruta_page(recorder):
    def get_page(object_type, object_id, to_object_type, limit=100):
        recorder.append((object_type, object_id, to_object_type))
        if to_object_type == OBJECT_TYPE_RUTA:
            return SimpleNamespace(results=[
                _assoc("R_TERR", [(ASSOC_CATEGORY_USER_DEFINED, 714)]),
                _assoc("R_MAR", [(ASSOC_CATEGORY_USER_DEFINED, 716)]),
            ])
        return SimpleNamespace(results=[])

    return SimpleNamespace(
        crm=SimpleNamespace(
            associations=SimpleNamespace(
                v4=SimpleNamespace(basic_api=SimpleNamespace(get_page=get_page))
            )
        )
    )


def _mute_otras_asociaciones(monkeypatch, ud_calls):
    monkeypatch.setattr(service, "batch_read_associations", lambda c, frm, to, ids: {})
    monkeypatch.setattr(service, "_get_proveedor_assocs_for_deal", lambda c, d: [])
    monkeypatch.setattr(
        service, "_batch_create_user_defined_assocs",
        lambda c, frm, to, triples: (ud_calls.append((frm, to, list(triples))) or 0),
    )
    monkeypatch.setattr(service, "_batch_create_default_assocs", lambda c, frm, to, pairs: 0)


def test_get_ruta_assocs_preserva_category_y_type_id():
    client = _client_with_ruta_page([])
    out = service._get_ruta_assocs_for_deal(client, "dCot")
    assert sorted(out) == sorted([
        ("R_TERR", ASSOC_CATEGORY_USER_DEFINED, 714),
        ("R_MAR", ASSOC_CATEGORY_USER_DEFINED, 716),
    ])


def test_get_ruta_assocs_error_no_propaga():
    def _boom(**k):
        raise RuntimeError("hubspot down")

    client = SimpleNamespace(
        crm=SimpleNamespace(
            associations=SimpleNamespace(
                v4=SimpleNamespace(basic_api=SimpleNamespace(get_page=_boom))
            )
        )
    )
    assert service._get_ruta_assocs_for_deal(client, "d1") == []


def test_build_batches_una_triple_por_ruta_preservando_type_id():
    ruta_assocs = [
        ("R_TERR", ASSOC_CATEGORY_USER_DEFINED, 714),
        ("R_MAR", ASSOC_CATEGORY_USER_DEFINED, 716),
    ]
    user_by_type, default_pairs = service._build_documento_ruta_batches(ruta_assocs, "dDoc")
    assert default_pairs == []
    assert user_by_type == {
        714: [("dDoc", "R_TERR", 714)],
        716: [("dDoc", "R_MAR", 716)],
    }


def test_build_batches_categoria_no_user_defined_va_a_default():
    user_by_type, default_pairs = service._build_documento_ruta_batches(
        [("R", "HUBSPOT_DEFINED", 999)], "dDoc",
    )
    assert user_by_type == {}
    assert default_pairs == [("dDoc", "R")]


def test_crear_asociaciones_hereda_rutas_de_la_cotizacion(monkeypatch):
    reads = []
    ud_calls = []
    client = _client_with_ruta_page(reads)
    _mute_otras_asociaciones(monkeypatch, ud_calls)

    service._crear_asociaciones_documento(client, "dDoc", "cA", "dPed", "dCot")

    # Fuente = la COTIZACIÓN, no el pedido.
    assert [oid for (_, oid, to) in reads if to == OBJECT_TYPE_RUTA] == ["dCot"]
    # Crea documento→ruta preservando el type_id de la etiqueta.
    emitted = sorted(
        t for frm, to, triples in ud_calls if to == OBJECT_TYPE_RUTA for t in triples
    )
    assert emitted == sorted([("dDoc", "R_TERR", 714), ("dDoc", "R_MAR", 716)])
    assert all(frm == OBJECT_TYPE_DEAL for frm, to, _ in ud_calls if to == OBJECT_TYPE_RUTA)


def test_crear_asociaciones_fallback_al_pedido_si_no_hay_cotizacion(monkeypatch):
    reads = []
    ud_calls = []
    client = _client_with_ruta_page(reads)
    _mute_otras_asociaciones(monkeypatch, ud_calls)

    service._crear_asociaciones_documento(client, "dDoc", "cA", "dPed", None)

    assert [oid for (_, oid, to) in reads if to == OBJECT_TYPE_RUTA] == ["dPed"]
