"""Helpers para consultas a HubDB (puertos, tipos de contenedor, etc.)."""

import logging
from typing import Optional

from app.shared.hubspot_client import hubspot_client

logger = logging.getLogger(__name__)

# TODO: Confirmar el table_id de la tabla de puertos en HubSpot HubDB
HUBDB_TABLE_PUERTOS = "puertos_proex"


def get_puerto_destination_country(puerto_id: str) -> Optional[str]:
    """Devuelve el país de destino asociado a un puerto.

    Usado en la generación del certificado sanitario (campo "País destino").

    Args:
        puerto_id: ID o nombre del puerto en HubDB.

    Returns:
        Nombre del país de destino, o None si no se encuentra.
    """
    client = hubspot_client.get_client()

    # TODO: Implementar lookup en HubDB
    # client.cms.hubdb.rows_api.get_table_rows(table_id_or_name=HUBDB_TABLE_PUERTOS, ...)
    raise NotImplementedError("get_puerto_destination_country: pendiente de implementación")
