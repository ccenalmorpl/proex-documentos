"""Derivación de flags del calculador desde las señales reales: la obligatoriedad
de cada documento sale de documentos_a_generar (lista autoritativa). Los builders
de archivos (que tocarían red) se mockean.
"""

from types import SimpleNamespace

from app.documento_deal import service


def _arch(tipo=None, name=""):
    return SimpleNamespace(tipo=tipo, name=name)


def _mock_builders(monkeypatch, bl=None, origen=None, sanitario=None, documentos=None):
    monkeypatch.setattr(service, "_build_bl_archivos", lambda raw: list(bl or []))
    monkeypatch.setattr(service, "_build_origen_archivos", lambda b, v: list(origen or []))
    monkeypatch.setattr(service, "_build_sanitario_archivos", lambda raw: list(sanitario or []))
    monkeypatch.setattr(service, "_build_documentos_archivos", lambda raw: list(documentos or []))


def test_nada_obligatorio_todo_ok(monkeypatch):
    _mock_builders(monkeypatch)
    flags = service._derivar_flags_documento({}, {"documentos_a_generar": ""})
    # Sin obligatorios, los gates valen True (no bloquean).
    assert flags["bl_borrador_ok"] is True
    assert flags["bl_final_ok"] is True
    assert flags["certs_borrador_ok"] is True
    assert flags["certs_validado_ok"] is True
    assert flags["otros_obligatorios_ok"] is True


def test_mercancia_retirada_desde_prop_contenedor(monkeypatch):
    _mock_builders(monkeypatch)
    base = {"documentos_a_generar": ""}
    assert service._derivar_flags_documento({}, base)["mercancia_retirada"] is False
    assert service._derivar_flags_documento(
        {}, {**base, "mercancia_retirada": "true"}
    )["mercancia_retirada"] is True


def test_bl_requerido_gatea(monkeypatch):
    _mock_builders(monkeypatch, bl=[])  # sin BL subido
    cn = {"documentos_a_generar": "bl"}
    flags = service._derivar_flags_documento({}, cn)
    assert flags["bl_borrador_ok"] is False
    assert flags["bl_final_ok"] is False

    _mock_builders(monkeypatch, bl=[_arch(tipo="borrador"), _arch(tipo="final")])
    flags = service._derivar_flags_documento({}, cn)
    assert flags["bl_borrador_ok"] is True
    assert flags["bl_final_ok"] is True


def test_certificados_solo_los_requeridos_bloquean(monkeypatch):
    # origen requerido, sanitario NO. Solo origen gatea.
    _mock_builders(monkeypatch, origen=[_arch(tipo="borrador")], sanitario=[])
    cn = {"documentos_a_generar": "certificado_de_origen"}
    flags = service._derivar_flags_documento({}, cn)
    assert flags["certs_borrador_ok"] is True   # origen borrador presente, sanitario no requerido
    assert flags["certs_validado_ok"] is False  # origen validado ausente


def test_certificado_validado_por_flag(monkeypatch):
    _mock_builders(monkeypatch, origen=[_arch(tipo="borrador")])
    cn = {
        "documentos_a_generar": "certificado_de_origen",
        "certificado_origen_validado": "true",
    }
    flags = service._derivar_flags_documento({}, cn)
    assert flags["certs_validado_ok"] is True


def test_otros_obligatorios_por_prefijo(monkeypatch):
    cn = {"documentos_a_generar": "arc;eur1"}
    # solo ARC subido → falta EUR.1
    _mock_builders(monkeypatch, documentos=[_arch(name="arc_doc.pdf")])
    assert service._derivar_flags_documento({}, cn)["otros_obligatorios_ok"] is False
    # ambos subidos
    _mock_builders(monkeypatch, documentos=[_arch(name="arc_x.pdf"), _arch(name="eur1_y.pdf")])
    assert service._derivar_flags_documento({}, cn)["otros_obligatorios_ok"] is True


def test_otros_valor_otros_usa_su_propia_prop(monkeypatch):
    _mock_builders(monkeypatch, documentos=[])
    cn = {"documentos_a_generar": "otros", "otros_documentos": ""}
    assert service._derivar_flags_documento({}, cn)["otros_obligatorios_ok"] is False
    cn = {"documentos_a_generar": "otros", "otros_documentos": "999"}
    assert service._derivar_flags_documento({}, cn)["otros_obligatorios_ok"] is True


def test_camion_sin_bl_ni_certs(monkeypatch):
    # documentos_a_generar no incluye bl/certificados → no gatean (flujo camión).
    _mock_builders(monkeypatch, bl=[], origen=[], sanitario=[], documentos=[_arch(name="arc_a.pdf")])
    cn = {"documentos_a_generar": "arc"}
    flags = service._derivar_flags_documento({}, cn)
    assert flags["bl_borrador_ok"] is True
    assert flags["bl_final_ok"] is True
    assert flags["certs_borrador_ok"] is True
    assert flags["certs_validado_ok"] is True
    assert flags["otros_obligatorios_ok"] is True
