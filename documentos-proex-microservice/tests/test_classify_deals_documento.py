"""_classify_deals separa cotización / pedido / documento por pipeline. El Negocio
Documento es el tercer tipo y NO debe colarse como cotización (regresión).
"""

from app.core.constants import (
    DOC_DEALSTAGE_EN_PROCESO,
    DOCUMENTO_PIPELINE_ID,
    PEDIDO_PIPELINE_ID,
)
from app.pedidos import service


def test_clasifica_los_tres_tipos():
    props = {
        "dCot": {"pipeline": "1111", "numero_de_pedido": ""},
        "dPed": {"pipeline": PEDIDO_PIPELINE_ID, "numero_de_pedido": "P-1"},
        "dDoc": {"pipeline": DOCUMENTO_PIPELINE_ID, "numero_de_pedido": "P-1"},
    }
    cot, pedido, documento = service._classify_deals(["dCot", "dPed", "dDoc"], props)
    assert cot[0] == "dCot"
    assert pedido[0] == "dPed"
    assert documento[0] == "dDoc"


def test_documento_no_se_clasifica_como_cotizacion():
    # Sin la rama de documento, un documento-deal caería en cotización.
    props = {"dDoc": {"pipeline": DOCUMENTO_PIPELINE_ID, "numero_de_pedido": "P-1"}}
    cot, pedido, documento = service._classify_deals(["dDoc"], props)
    assert cot is None
    assert pedido is None
    assert documento[0] == "dDoc"


def test_sin_documento_devuelve_none():
    props = {"dPed": {"pipeline": PEDIDO_PIPELINE_ID, "numero_de_pedido": "P-1"}}
    cot, pedido, documento = service._classify_deals(["dPed"], props)
    assert pedido[0] == "dPed"
    assert documento is None


def test_build_contenedor_item_expone_tiene_negocio_documento():
    item = service._build_contenedor_item(
        "c1", {}, {}, tiene_negocio_documento=True, documento_dealstage=DOC_DEALSTAGE_EN_PROCESO,
    )
    assert item.tiene_negocio_documento is True
    assert item.documento_dealstage == DOC_DEALSTAGE_EN_PROCESO

    item2 = service._build_contenedor_item("c2", {}, {})
    assert item2.tiene_negocio_documento is False
    assert item2.documento_dealstage is None
