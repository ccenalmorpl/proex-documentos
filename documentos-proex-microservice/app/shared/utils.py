"""Utilidades compartidas del microservicio."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel


def generate_group_id() -> str:
    """Genera un UUID único para identificar un grupo de generación."""
    return str(uuid.uuid4())


def utcnow_iso() -> str:
    """Devuelve la fecha/hora UTC actual en formato ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


def safe_convert(value: Any, target_type: type) -> Any:
    """Convierte un valor de HubSpot (normalmente string) al tipo Python destino."""
    if value is None or value == "":
        return None

    import typing
    if hasattr(target_type, '__origin__') and target_type.__origin__ is typing.Union:
        actual_types = [t for t in target_type.__args__ if t is not type(None)]
        if actual_types:
            target_type = actual_types[0]

    if target_type is float:
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    elif target_type is int:
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
    elif target_type is str:
        return str(value) if value else None

    return value


def get_model_property_names(model_class: Type[BaseModel], exclude: List[str] = None) -> List[str]:
    """Extrae los nombres de campos de un modelo Pydantic para usarlos en queries HubSpot."""
    exclude = exclude or []
    return [f for f in model_class.model_fields.keys() if f not in exclude]


def parse_hubspot_properties(
    object_id: str,
    properties: Dict[str, Any],
    model_class: Type[BaseModel],
) -> Dict[str, Any]:
    """Convierte las propiedades de respuesta de HubSpot a un dict compatible con un modelo Pydantic."""
    result = {"id": object_id}
    for field_name, field_info in model_class.model_fields.items():
        if field_name == 'id':
            continue
        value = properties.get(field_name)
        result[field_name] = safe_convert(value, field_info.annotation)
    return result
