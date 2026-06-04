import io
import json
import logging
from dataclasses import dataclass
from typing import List, Optional

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

FILES_API_URL = "https://api.hubapi.com/files/v3/files"


def parse_file_ids(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    return [chunk.strip() for chunk in raw.split(";") if chunk.strip()]


def serialize_file_ids(ids: List[str]) -> str:
    return ";".join(ids)


@dataclass
class FileMetadata:
    file_id: str
    name: str
    url: Optional[str]


def fetch_file_metadata(file_id: str) -> Optional[FileMetadata]:
    headers = {"Authorization": f"Bearer {settings.proex_access_token}"}
    url = f"{FILES_API_URL}/{file_id}"
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 404:
            logger.warning(f"[FILE_METADATA] file_id={file_id!r} no existe (404)")
            return None
        resp.raise_for_status()
        data = resp.json()
        return FileMetadata(
            file_id=str(data.get("id") or file_id),
            name=str(data.get("name") or ""),
            url=data.get("url"),
        )
    except Exception as e:
        logger.warning(f"[FILE_METADATA] fallo file_id={file_id!r}: {e}")
        return None


@dataclass
class FileUploadResult:
    file_id: str
    file_url: str
    name: str


def upload_file(
    file_bytes: bytes,
    filename: str,
    mime_type: str = "application/pdf",
    folder_path: Optional[str] = None,
) -> FileUploadResult:
    """Sube un archivo al HubSpot File Manager y devuelve su file_id y URL."""
    folder = folder_path or settings.files_folder
    headers = {"Authorization": f"Bearer {settings.proex_access_token}"}
    options = json.dumps({"access": "PUBLIC_NOT_INDEXABLE", "overwrite": False})

    logger.info(f"[FILE_UPLOAD] Subiendo {filename!r} ({mime_type}) a {folder!r}")

    resp = requests.post(
        FILES_API_URL,
        headers=headers,
        files={"file": (filename, io.BytesIO(file_bytes), mime_type)},
        data={"options": options, "folderPath": folder, "fileName": filename},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    file_id = str(data["id"])
    file_url = data.get("url", "")
    logger.info(f"[FILE_UPLOADED] file_id={file_id} url={file_url!r}")

    return FileUploadResult(file_id=file_id, file_url=file_url, name=filename)


def upload_pdf(
    file_bytes: bytes,
    filename: str,
    folder_path: Optional[str] = None,
) -> FileUploadResult:
    return upload_file(file_bytes, filename, "application/pdf", folder_path)


def delete_file(file_id: str) -> bool:
    headers = {"Authorization": f"Bearer {settings.proex_access_token}"}
    url = f"{FILES_API_URL}/{file_id}"

    logger.info(f"[FILE_DELETE] Borrando file_id={file_id!r}")
    resp = requests.delete(url, headers=headers, timeout=30)

    if resp.status_code == 404:
        logger.info(f"[FILE_DELETE] file_id={file_id!r} no existe (404), tratado como éxito")
        return True

    resp.raise_for_status()
    logger.info(f"[FILE_DELETED] file_id={file_id!r} status={resp.status_code}")
    return True
