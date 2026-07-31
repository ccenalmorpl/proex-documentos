"""Los certificados de la cabecera (origen/sanitario) se agregan de TODOS los
contenedores del pedido, no de uno 'muestra'. Así un validado/sellado subido a un
subconjunto del embarque aparece en la etapa correspondiente aunque el contenedor
muestra (orden no determinista) no lo tenga.
"""

from app.core.constants import (
    CONTENEDOR_PROP_CERT_SANITARIO,
    CONTENEDOR_PROP_CERT_SANITARIO_VALIDADO,
)
from app.pedidos import service


def test_merge_cert_props_agrega_ficheros_de_todos_los_contenedores():
    # cA solo tiene el borrador; cB tiene borrador + validado (subido a un subconjunto).
    props = {
        "cA": {CONTENEDOR_PROP_CERT_SANITARIO: service.serialize_file_ids(["fBorrador"])},
        "cB": {CONTENEDOR_PROP_CERT_SANITARIO: service.serialize_file_ids(["fBorrador", "fValidado"])},
    }
    merged = service._merge_cert_props(props, ["cA", "cB"])
    assert service.parse_file_ids(merged[CONTENEDOR_PROP_CERT_SANITARIO]) == ["fBorrador", "fValidado"]


def test_merge_cert_props_validado_flag_es_or():
    props = {
        "cA": {CONTENEDOR_PROP_CERT_SANITARIO_VALIDADO: "false"},
        "cB": {CONTENEDOR_PROP_CERT_SANITARIO_VALIDADO: "true"},
    }
    merged = service._merge_cert_props(props, ["cA", "cB"])
    assert merged[CONTENEDOR_PROP_CERT_SANITARIO_VALIDADO] == "true"
