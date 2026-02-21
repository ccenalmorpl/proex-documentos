"""Helpers para subida y borrado de archivos en HubSpot File Manager."""

import logging
from dataclasses import dataclass
from typing import Optional

from app.shared.hubspot_client import hubspot_client
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class FileUploadResult:
    file_id: str
    file_url: str
    name: str


def upload_pdf(
    file_bytes: bytes,
    filename: str,
    folder_path: Optional[str] = None,
) -> FileUploadResult:
    """Sube un PDF al HubSpot File Manager.

    Args:
        file_bytes: Contenido del PDF como bytes.
        filename: Nombre del archivo (ej. "origen_borrador_2026.pdf").
        folder_path: Carpeta destino en File Manager. Si es None usa settings.files_folder.

    Returns:
        FileUploadResult con file_id y file_url públicos.

    Raises:
        Exception: Si la subida falla.
    """
    folder = folder_path or settings.files_folder
    client = hubspot_client.get_client()

    # TODO: Implementar subida con hubspot Files API
    # La API de Files de HubSpot requiere multipart/form-data.
    # Referencia: client.files.files_api.upload(...)
    # o bien vía requests directo a https://api.hubapi.com/files/v3/files
    raise NotImplementedError("upload_pdf: pendiente de implementación")


def delete_file(file_id: str) -> bool:
    """Borra un archivo del HubSpot File Manager por su ID.

    Args:
        file_id: ID del archivo en HubSpot File Manager.

    Returns:
        True si el borrado fue exitoso.

    Raises:
        Exception: Si el borrado falla (no borra parcialmente — ver rollback).
    """
    client = hubspot_client.get_client()

    # TODO: Implementar borrado con hubspot Files API
    # client.files.files_api.archive(file_id=file_id)
    raise NotImplementedError("delete_file: pendiente de implementación")
