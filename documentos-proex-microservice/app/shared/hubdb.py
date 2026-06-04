import logging
from typing import Optional

from app.shared.hubspot_client import hubspot_client

logger = logging.getLogger(__name__)

HUBDB_TABLE_PUERTOS = "puertos"

def get_puerto_destination_country(puerto_id: str) -> Optional[str]:
    """País destino asociado al puerto (certificado sanitario)."""
    client = hubspot_client.get_client()

    # TODO: Implementar lookup en HubDB
    raise NotImplementedError("get_puerto_destination_country: pendiente de implementación")
