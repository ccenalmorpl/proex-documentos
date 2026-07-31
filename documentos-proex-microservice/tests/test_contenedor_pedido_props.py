"""Cambio 2 — booking y documentos de cabecera (factura/packing/carta) son props
del PEDIDO-deal de cada contenedor (1:1) y se exponen por contenedor en el detalle,
para que cada uno muestre los suyos en las tablas multi-contenedor de la card.
"""

from app.pedidos.schemas import DealFile
from app.pedidos import service


def test_build_contenedor_item_expone_booking_y_docs_cabecera():
    factura = DealFile(file_id="f1", name="factura.pdf", url="http://x/f1")
    packing = DealFile(file_id="p1", name="packing.pdf", url="http://x/p1")

    item = service._build_contenedor_item(
        "cA",
        {"nombre": "CONT-A"},
        {},
        numero_de_factura="FAC-001",
        fecha_de_vencimiento_factura="2026-01-31",
        numero_de_booking="BK-123",
        factura_pedido=factura,
        packing_list_pedido=packing,
        carta_porte_pedido=None,
    )

    assert item.numero_de_booking == "BK-123"
    assert item.factura_pedido == factura
    assert item.packing_list_pedido == packing
    assert item.carta_porte_pedido is None
    assert item.numero_de_factura == "FAC-001"


def test_build_contenedor_item_booking_vacio_es_none():
    item = service._build_contenedor_item(
        "cB", {"nombre": "CONT-B"}, {}, numero_de_booking="",
    )
    assert item.numero_de_booking is None
    assert item.factura_pedido is None


def test_build_contenedor_item_transitarios_por_tramo():
    item = service._build_contenedor_item(
        "cC",
        {"nombre": "CAM-1"},
        {},
        transitario="TRANSITARIO MARITIMO SA",
        transitario_terrestre="TRANSITARIO TERRESTRE SL",
    )
    assert item.transitario == "TRANSITARIO MARITIMO SA"
    assert item.transitario_terrestre == "TRANSITARIO TERRESTRE SL"


def test_build_contenedor_item_transitario_terrestre_vacio_es_none():
    item = service._build_contenedor_item(
        "cD", {"nombre": "CAM-2"}, {}, transitario="T1", transitario_terrestre="",
    )
    assert item.transitario == "T1"
    assert item.transitario_terrestre is None
