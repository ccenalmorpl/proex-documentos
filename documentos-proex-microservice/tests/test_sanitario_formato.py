"""Certificado sanitario: resolución de `formato` vía HubDB y traducción de
nombres de producto según el idioma del certificado.
"""

from types import SimpleNamespace

from app.documentos.domain.sanitario import build_sanitario_payload

SETTINGS = SimpleNamespace(
    sanitario_establecimiento="EST-FIJO",
    sanitario_jefe_salud="JEFE-FIJO",
    sanitario_firmado_en="VALENCIA",
)

CONTAINERS = {
    "c1": {"numero_contenedor": "CONT-1", "nombre": "Contenedor Uno", "tipo_contenedor": "20DRY"},
}

DEAL_PROPS = {"shipper": "Bodega SA", "consignee": "Importer Ltd", "puerto_destino": "ROTTERDAM"}


def _elemento(**over):
    base = {
        "nombre": "123456 - Vino Tinto",
        "nombre_es": "Vino Tinto",
        "nombre_en": "Red Wine",
        "nombre_fr": "Vin Rouge",
        "cantidad": "10",
        "peso_neto_total": "100",
        "peso_bruto_total": "120",
        "formato": "1",
        "marca": "MarcaX",
    }
    base.update(over)
    return base


def _build(idioma, formato_labels=None, elementos=None):
    return build_sanitario_payload(
        ["c1"],
        CONTAINERS,
        DEAL_PROPS,
        {"c1": elementos if elementos is not None else [_elemento()]},
        SETTINGS,
        idioma=idioma,
        formato_labels=formato_labels,
    )


def test_formato_se_traduce_por_el_mapa():
    payload = _build("EN", formato_labels={"1": "Box 6x1L"})
    assert payload["formatos_unicos"] == ["Box 6x1L"]


def test_formato_sin_match_conserva_valor_crudo():
    payload = _build("ES", formato_labels={"99": "Otro"})
    assert payload["formatos_unicos"] == ["1"]


def test_formato_sin_mapa_conserva_valor_crudo():
    payload = _build("ES", formato_labels=None)
    assert payload["formatos_unicos"] == ["1"]


def test_formatos_unicos_deduplica():
    elementos = [
        _elemento(formato="1", nombre="123456 - Vino Tinto"),
        _elemento(formato="1", nombre="999999 - Vino Blanco", nombre_es="Vino Blanco", nombre_en="White Wine"),
    ]
    payload = _build("EN", formato_labels={"1": "Box"}, elementos=elementos)
    assert payload["formatos_unicos"] == ["Box"]


def test_nombre_producto_respeta_idioma_en():
    # Fija el fix del bug case-mismatch: EN debe usar nombre_en, no caer a ES.
    payload = _build("EN", formato_labels={"1": "Box"})
    assert "Red Wine" in payload["mercancias_text"]
    assert "Vino Tinto" not in payload["mercancias_text"]


def test_nombre_producto_respeta_idioma_fr():
    payload = _build("FR", formato_labels={"1": "Boîte"})
    assert "Vin Rouge" in payload["mercancias_text"]


def test_nombre_producto_es_por_defecto():
    payload = _build("ES", formato_labels={"1": "Caja"})
    assert "Vino Tinto" in payload["mercancias_text"]


def test_idioma_minusculas_se_normaliza():
    # Defensa: aunque llegue "en" en minúsculas, debe resolver a EN, no caer a ES.
    payload = _build("en", formato_labels={"1": "Box"})
    assert "Red Wine" in payload["mercancias_text"]
    assert "Vino Tinto" not in payload["mercancias_text"]
