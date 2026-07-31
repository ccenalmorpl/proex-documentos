"""Checkbox 'Enviar a firmar' por certificado (origen/sanitario).

Flag persistido a nivel de pedido en el Contenedor, con la misma mecánica que
'Validado por cliente': el PATCH escribe la prop en todos los contenedores y la
lectura de cabecera OR-ea el flag entre los contenedores del embarque.
"""

from app.pedidos import service
from app.pedidos.schemas import UpdateContenedoresCertificadosRequest
from app.core.constants import (
    CONTENEDOR_PROP_CERT_ORIGEN_ENVIAR_FIRMAR,
    CONTENEDOR_PROP_CERT_SANITARIO_ENVIAR_FIRMAR,
    CONTENEDOR_PROP_CERT_ORIGEN_VALIDADO,
)


def _patch_collaborators(monkeypatch, captured):
    monkeypatch.setattr(service.hubspot_client, "get_client", lambda: object())
    monkeypatch.setattr(service, "_verify_pedido_belongs_to_company", lambda c, n, co: ["dPed"])
    monkeypatch.setattr(service, "_get_contenedores_of_pedido", lambda c, pids: ["c1", "c2"])
    monkeypatch.setattr(service, "_recalcular_documentos_best_effort", lambda c, n: None)
    monkeypatch.setattr(
        service, "_patch_contenedores_batch",
        lambda c, cids, props: (captured.update(cids=cids, props=props) or len(cids)),
    )


def test_patch_escribe_enviar_a_firmar_origen(monkeypatch):
    captured = {}
    _patch_collaborators(monkeypatch, captured)

    resp = service._update_contenedores_certificados_sync(
        "P-1", "co1",
        UpdateContenedoresCertificadosRequest(certificado_origen_enviar_a_firmar=True),
    )

    assert resp.success is True
    assert captured["cids"] == ["c1", "c2"]
    assert captured["props"] == {CONTENEDOR_PROP_CERT_ORIGEN_ENVIAR_FIRMAR: "true"}


def test_patch_escribe_enviar_a_firmar_sanitario_false(monkeypatch):
    captured = {}
    _patch_collaborators(monkeypatch, captured)

    service._update_contenedores_certificados_sync(
        "P-1", "co1",
        UpdateContenedoresCertificadosRequest(certificado_sanitario_enviar_a_firmar=False),
    )

    assert captured["props"] == {CONTENEDOR_PROP_CERT_SANITARIO_ENVIAR_FIRMAR: "false"}


def test_patch_combina_validado_y_enviar_a_firmar(monkeypatch):
    captured = {}
    _patch_collaborators(monkeypatch, captured)

    service._update_contenedores_certificados_sync(
        "P-1", "co1",
        UpdateContenedoresCertificadosRequest(
            certificado_origen_validado=True,
            certificado_origen_enviar_a_firmar=True,
        ),
    )

    assert captured["props"] == {
        CONTENEDOR_PROP_CERT_ORIGEN_VALIDADO: "true",
        CONTENEDOR_PROP_CERT_ORIGEN_ENVIAR_FIRMAR: "true",
    }


def test_merge_orea_enviar_a_firmar_entre_contenedores():
    props = {
        "c1": {CONTENEDOR_PROP_CERT_ORIGEN_ENVIAR_FIRMAR: "false"},
        "c2": {CONTENEDOR_PROP_CERT_ORIGEN_ENVIAR_FIRMAR: "true"},
    }
    merged = service._merge_cert_props(props, ["c1", "c2"])
    assert merged[CONTENEDOR_PROP_CERT_ORIGEN_ENVIAR_FIRMAR] == "true"
    # Sin ninguno marcado → false.
    assert service._merge_cert_props(
        {"c1": {}, "c2": {}}, ["c1", "c2"],
    )[CONTENEDOR_PROP_CERT_SANITARIO_ENVIAR_FIRMAR] == "false"
