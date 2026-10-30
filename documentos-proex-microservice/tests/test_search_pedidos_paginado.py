"""La búsqueda de Negocios Pedido por número recorre todas las páginas: un
expediente de 20 contenedores son 20 deals y la card no puede quedarse con 10.
"""

from types import SimpleNamespace

from app.core.constants import PEDIDO_PIPELINE_ID
from app.pedidos import service


def _pagina(ids, after=None):
    paging = SimpleNamespace(next=SimpleNamespace(after=after)) if after else None
    return SimpleNamespace(results=[SimpleNamespace(id=i) for i in ids], paging=paging)


class _SearchApi:
    def __init__(self, paginas):
        self.paginas = paginas
        self.requests = []

    def do_search(self, public_object_search_request):
        self.requests.append(public_object_search_request)
        return self.paginas[len(self.requests) - 1]


def _client(search_api):
    return SimpleNamespace(crm=SimpleNamespace(deals=SimpleNamespace(search_api=search_api)))


def test_search_pedidos_recorre_todas_las_paginas():
    ids = [f"d{n:02d}" for n in range(1, 21)]
    api = _SearchApi([_pagina(ids[:12], after="12"), _pagina(ids[12:])])

    resultado = service._search_pedidos_by_numero(_client(api), "P-1", PEDIDO_PIPELINE_ID)

    assert resultado == ids
    assert [r.after for r in api.requests] == [None, "12"]
    assert all(r.limit == 100 for r in api.requests)


def test_search_pedidos_una_sola_pagina():
    api = _SearchApi([_pagina(["d1", "d2"])])

    assert service._search_pedidos_by_numero(_client(api), "P-1", PEDIDO_PIPELINE_ID) == ["d1", "d2"]
    assert len(api.requests) == 1
