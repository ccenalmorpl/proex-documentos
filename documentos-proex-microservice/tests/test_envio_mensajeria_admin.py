"""Gestión de administración del envío por mensajería: el text area de datos
(nº copias/dirección/contacto) se escribe en el Contenedor; el check solo escribe
su booleano (sin fechas asociadas).
"""

from app.core.constants import (
    CONTENEDOR_PROP_DATOS_ENVIO_MENSAJERIA,
    CONTENEDOR_PROP_ENVIAR_POR_MENSAJERIA,
)
from app.pedidos import service
from app.pedidos.schemas import UpdateContenedorEntregaRequest


def _common(monkeypatch):
    monkeypatch.setattr(service.hubspot_client, "get_client", lambda: object())
    monkeypatch.setattr(service, "_verify_pedido_belongs_to_company", lambda c, n, comp: ["dPed"])
    monkeypatch.setattr(service, "_get_contenedores_of_pedido", lambda c, dids: ["cA"])
    monkeypatch.setattr(service, "_recalcular_documentos_best_effort", lambda c, n: None)
    captured = []
    monkeypatch.setattr(
        service, "_patch_contenedores_batch",
        lambda c, cids, props: captured.append(dict(props)) or len(cids),
    )
    return captured


def test_datos_envio_se_escribe(monkeypatch):
    captured = _common(monkeypatch)
    resp = service._update_contenedor_entrega_sync(
        "P1", "comp", "cA",
        UpdateContenedorEntregaRequest(datos_envio_mensajeria="3 copias / Calle X 1 / Juan"),
    )
    assert resp.success is True
    assert captured[0][CONTENEDOR_PROP_DATOS_ENVIO_MENSAJERIA] == "3 copias / Calle X 1 / Juan"


def test_check_solo_escribe_el_booleano(monkeypatch):
    captured = _common(monkeypatch)
    resp = service._update_contenedor_entrega_sync(
        "P1", "comp", "cA", UpdateContenedorEntregaRequest(enviar_por_mensajeria=True),
    )
    assert resp.success is True
    props = captured[0]
    assert props[CONTENEDOR_PROP_ENVIAR_POR_MENSAJERIA] == "true"
    # No hay fechas asociadas al check.
    assert list(props.keys()) == [CONTENEDOR_PROP_ENVIAR_POR_MENSAJERIA]


def test_desmarcar_check_limpia_datos_via_diff(monkeypatch):
    # El front, al desmarcar, envía datos="" en el mismo payload; el backend lo escribe.
    captured = _common(monkeypatch)
    resp = service._update_contenedor_entrega_sync(
        "P1", "comp", "cA",
        UpdateContenedorEntregaRequest(enviar_por_mensajeria=False, datos_envio_mensajeria=""),
    )
    assert resp.success is True
    props = captured[0]
    assert props[CONTENEDOR_PROP_ENVIAR_POR_MENSAJERIA] == "false"
    assert props[CONTENEDOR_PROP_DATOS_ENVIO_MENSAJERIA] == ""
