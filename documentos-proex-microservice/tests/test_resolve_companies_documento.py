"""Los tabs de Documentos usan SIEMPRE la empresa del contexto (company_id): el
filtrado resuelve por esa empresa exacta y NO cae a la búsqueda difusa por nombre.
Además, la columna 'Negocio' de cada contenedor es SIEMPRE el Negocio Cotización padre.
"""

from app.core.constants import (
    DEAL_PROP_PIPELINE,
    DOCUMENTO_PIPELINE_ID,
    PEDIDO_PIPELINE_ID,
)
from app.documentos import service


def test_resolve_company_ids_prioriza_company_id(monkeypatch):
    llamadas_nombre = []
    monkeypatch.setattr(
        service, "_search_companies_by_name",
        lambda client, empresa: llamadas_nombre.append(empresa) or [("999", "otra")],
    )

    out = service._resolve_company_ids(None, company_id="123", empresa="")

    assert out == ["123"]
    assert llamadas_nombre == []


def test_resolve_company_ids_fallback_por_nombre(monkeypatch):
    monkeypatch.setattr(
        service, "_search_companies_by_name",
        lambda client, empresa: [("111", "Agro"), ("222", "Agro 2")],
    )
    out = service._resolve_company_ids(None, company_id="", empresa="Agro")
    assert out == ["111", "222"]


def test_pick_cotizacion_deal_elige_la_cotizacion():
    # Contenedor asociado a cotización + pedido + documentación → devuelve la cotización.
    deals = ["dPed", "dDoc", "dCot"]
    props = {
        "dPed": {DEAL_PROP_PIPELINE: PEDIDO_PIPELINE_ID, "dealname": "Pedido"},
        "dDoc": {DEAL_PROP_PIPELINE: DOCUMENTO_PIPELINE_ID, "dealname": "Doc"},
        "dCot": {DEAL_PROP_PIPELINE: "otro_pipeline", "dealname": "Cotización"},
    }
    did, dprops = service._pick_cotizacion_deal(deals, props)
    assert did == "dCot"
    assert dprops["dealname"] == "Cotización"


def test_pick_cotizacion_deal_vacio_si_solo_pedido_y_doc():
    # Sin cotización identificable (solo pedido y/o documentación) → vacío: nunca se
    # etiqueta el pedido/documentación como 'Negocio'.
    deals = ["dPed", "dDoc"]
    props = {
        "dPed": {DEAL_PROP_PIPELINE: PEDIDO_PIPELINE_ID, "dealname": "Pedido"},
        "dDoc": {DEAL_PROP_PIPELINE: DOCUMENTO_PIPELINE_ID, "dealname": "Doc"},
    }
    assert service._pick_cotizacion_deal(deals, props) == ("", {})


def test_pick_cotizacion_deal_sin_deals():
    assert service._pick_cotizacion_deal([], {}) == ("", {})
