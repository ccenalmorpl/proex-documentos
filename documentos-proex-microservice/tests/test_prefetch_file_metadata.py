from app.pedidos import service
from app.shared.files import FileMetadata


def _meta(file_id):
    return FileMetadata(file_id=file_id, name=f"{file_id}.pdf", url=None, created_at=None)


def test_prefetch_pide_cada_fichero_una_vez_y_respeta_la_cache(monkeypatch):
    pedidos = []

    def fake_fetch(file_id):
        pedidos.append(file_id)
        return None if file_id == "roto" else _meta(file_id)

    monkeypatch.setattr(service, "fetch_file_metadata", fake_fetch)
    cache = {"ya": _meta("ya")}

    service._prefetch_file_metadata(["a", "b", "a", "ya", "roto"], cache)

    assert sorted(pedidos) == ["a", "b", "roto"]
    assert set(cache) == {"ya", "a", "b", "roto"}
    assert cache["roto"] is None

    archivos = service._build_archivos_simples("roto;a", cache)
    assert [a.name for a in archivos] == ["", "a.pdf"]
    assert sorted(pedidos) == ["a", "b", "roto"]
