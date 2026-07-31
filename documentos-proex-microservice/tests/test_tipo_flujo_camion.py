"""El transporte camión se detecta aunque el valor de tipo_contenedor venga con
guion bajo ("trailer_80") y no solo con espacio ("TRAILER 80")."""

import pytest

from app.pedidos import service
from app.pedidos.service import _compute_tipo_flujo
from app.core.constants import (
    TIPO_FLUJO_CAMION,
    TIPO_FLUJO_CAMION_SAN_ROQUE,
    TIPO_FLUJO_CONTENEDOR,
)


@pytest.mark.parametrize(
    "raw", ["trailer_80", "TRAILER_80", "TRAILER 80", "TRAILER80", "trailer-80", " trailer_80 "],
)
def test_trailer_es_camion(raw):
    assert service._es_camion(raw) is True


@pytest.mark.parametrize("raw", ["D40DR", "D20DR", "CAMION16P", "", None])
def test_resto_es_contenedor(raw):
    assert service._es_camion(raw) is False


def test_compute_tipo_flujo_trailer_underscore():
    assert _compute_tipo_flujo("trailer_80", "12") == TIPO_FLUJO_CAMION
    assert _compute_tipo_flujo("trailer_80", "01") == TIPO_FLUJO_CAMION_SAN_ROQUE
    assert _compute_tipo_flujo("D40DR", "12") == TIPO_FLUJO_CONTENEDOR
