"""Los certificados imprimen el peso grabado en el Contenedor tras la carga, no
el teórico de la proforma (P-64424030979-001: 23.800,5 kg frente a 23.247,36)."""

from types import SimpleNamespace

from app.documentos.domain.origen import build_origen_payload
from app.documentos.domain.sanitario import build_sanitario_payload

SETTINGS = SimpleNamespace(
    sanitario_establecimiento="EST",
    sanitario_jefe_salud="JEFE",
    sanitario_firmado_en="VALENCIA",
)
DEAL_PROPS = {"shipper": "PROEX", "consignee": "SUMBER URIP"}


def _elemento(nombre, cajas, bruto_u="8.072", neto_u="4.5"):
    return {
        "nombre": nombre,
        "nombre_es": nombre,
        "cantidad": str(cajas),
        "peso_bruto_total": f"{cajas * float(bruto_u):.4f}",
        "peso_neto_total": f"{cajas * float(neto_u):.2f}",
        "peso_bruto_unitario": bruto_u,
        "peso_neto_unitario": neto_u,
    }


ELEMENTOS_001 = [
    _elemento("UVA BLANCA", 500),
    _elemento("UVA TINTA", 2265),
    _elemento("UVA ROSA", 115),
]


def _origen(containers, elementos_by_container):
    return build_origen_payload(
        list(containers), containers, DEAL_PROPS, elementos_by_container,
        descripcion_mercancia="STAR VILLAGE",
    )


def test_origen_usa_peso_del_contenedor_cargado():
    containers = {"c1": {"nombre": "64424030979-001", "tipo_contenedor": "40DRY",
                         "peso_bruto": "23800.5", "peso_neto": "12960.0"}}
    payload = _origen(containers, {"c1": ELEMENTOS_001})

    assert payload["totales"]["total_cases"] == 2880
    assert payload["totales"]["total_peso_bruto"] == 23800.5
    assert payload["totales"]["total_peso_neto"] == 12960.0
    assert payload["totales_pdf"]["gross_line"].startswith("23.800,50")


def test_origen_sin_peso_en_contenedor_cae_al_teorico():
    containers = {"c1": {"nombre": "X-001", "tipo_contenedor": "40DRY",
                         "peso_bruto": "", "peso_neto": None}}
    payload = _origen(containers, {"c1": ELEMENTOS_001})

    assert payload["totales"]["total_peso_bruto"] == 23247.36
    assert payload["totales"]["total_peso_neto"] == 12960.0


def test_origen_varios_contenedores_mezcla_cargado_y_teorico():
    containers = {
        "c1": {"nombre": "X-001", "tipo_contenedor": "40DRY", "peso_bruto": "23800.5", "peso_neto": "12960"},
        "c2": {"nombre": "X-002", "tipo_contenedor": "40DRY", "peso_bruto": "0", "peso_neto": ""},
    }
    payload = _origen(containers, {"c1": ELEMENTOS_001, "c2": [_elemento("UVA TINTA", 100)]})

    assert payload["totales"]["total_cases"] == 2980
    assert payload["totales"]["total_peso_bruto"] == 24607.7
    assert payload["totales"]["total_peso_neto"] == 13410.0


def test_sanitario_usa_peso_neto_del_contenedor():
    containers = {"c1": {"nombre": "X-001", "numero_contenedor": "FSCU7163117",
                         "tipo_contenedor": "40DRY", "peso_bruto": "23800.5", "peso_neto": "13001.25"}}
    payload = build_sanitario_payload(
        ["c1"], containers, DEAL_PROPS, {"c1": ELEMENTOS_001}, SETTINGS,
    )

    assert payload["totales"]["total_peso_neto"] == 13001.25
    assert payload["totales"]["total_peso_bruto"] == 23800.5
    assert payload["total_peso_neto_text"] == "13.001,25 KGS"
