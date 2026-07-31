"""Lookup de la HubDB `formato_producto`: traduce el valor interno del select
`elemento.formato` al nombre del idioma del certificado, con fallback a ES y al
valor crudo. El cliente HubSpot se sustituye por filas fake; no toca red.
"""

from types import SimpleNamespace

import pytest

from app.shared import hubdb


def _row(values: dict):
    return SimpleNamespace(values=values)


@pytest.fixture(autouse=True)
def _clean_cache():
    hubdb.reset_formato_cache()
    yield
    hubdb.reset_formato_cache()


def _patch_rows(monkeypatch, rows):
    monkeypatch.setattr(hubdb, "_fetch_formato_rows", lambda: rows)


def test_build_cache_indexa_por_columna_id():
    rows = [
        _row({"id": "1", "nombre_es": "Caja 6x1L", "nombre_en": "Box 6x1L", "nombre_fr": "Boîte 6x1L"}),
        _row({"id": "2", "nombre_es": "Palet", "nombre_en": "Pallet", "nombre_fr": "Palette"}),
    ]
    cache = hubdb._build_formato_cache(rows)
    assert cache["1"] == {"ES": "Caja 6x1L", "EN": "Box 6x1L", "FR": "Boîte 6x1L"}
    assert cache["2"]["FR"] == "Palette"


def test_label_map_devuelve_idioma_pedido(monkeypatch):
    _patch_rows(monkeypatch, [
        _row({"id": "1", "nombre_es": "Caja", "nombre_en": "Box", "nombre_fr": "Boîte"}),
    ])
    assert hubdb.get_formato_label_map("EN") == {"1": "Box"}
    assert hubdb.get_formato_label_map("FR") == {"1": "Boîte"}
    assert hubdb.get_formato_label_map("ES") == {"1": "Caja"}


def test_label_map_cae_a_es_si_falta_traduccion(monkeypatch):
    _patch_rows(monkeypatch, [
        _row({"id": "1", "nombre_es": "Caja", "nombre_en": "", "nombre_fr": "Boîte"}),
    ])
    assert hubdb.get_formato_label_map("EN") == {"1": "Caja"}


def test_label_map_idioma_invalido_usa_es(monkeypatch):
    _patch_rows(monkeypatch, [
        _row({"id": "1", "nombre_es": "Caja", "nombre_en": "Box", "nombre_fr": "Boîte"}),
    ])
    assert hubdb.get_formato_label_map("DE") == {"1": "Caja"}
    assert hubdb.get_formato_label_map("") == {"1": "Caja"}


def test_filas_sin_id_o_sin_nombre_se_omiten(monkeypatch):
    _patch_rows(monkeypatch, [
        _row({"id": "", "nombre_es": "Sin id"}),
        _row({"id": "3", "nombre_es": "", "nombre_en": "", "nombre_fr": ""}),
        _row({"id": "4", "nombre_es": "Bidón", "nombre_en": "Drum", "nombre_fr": "Fût"}),
    ])
    assert hubdb.get_formato_label_map("EN") == {"4": "Drum"}


def test_valores_dict_de_hubdb_se_resuelven(monkeypatch):
    # Columnas foreignid/select de HubDB llegan como dict {name/label/value}.
    _patch_rows(monkeypatch, [
        _row({"id": {"name": "1"}, "nombre_es": {"label": "Caja"}, "nombre_en": "Box", "nombre_fr": "Boîte"}),
    ])
    assert hubdb.get_formato_label_map("ES") == {"1": "Caja"}


def test_cache_se_carga_una_sola_vez(monkeypatch):
    calls = {"n": 0}

    def _fake_fetch():
        calls["n"] += 1
        return [_row({"id": "1", "nombre_es": "Caja", "nombre_en": "Box", "nombre_fr": "Boîte"})]

    monkeypatch.setattr(hubdb, "_fetch_formato_rows", _fake_fetch)
    hubdb.get_formato_label_map("ES")
    hubdb.get_formato_label_map("EN")
    assert calls["n"] == 1
