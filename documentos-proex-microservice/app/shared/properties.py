import logging

logger = logging.getLogger(__name__)


def fetch_select_options(client, properties: list[tuple[str, str]]) -> dict[str, list[dict]]:
    """Carga options (label, value) de propiedades select de HubSpot. Best-effort: si falla una propiedad, devuelve lista vacía."""
    result: dict[str, list[dict]] = {}
    for object_type, prop_name in properties:
        try:
            prop = client.crm.properties.core_api.get_by_name(
                object_type=object_type,
                property_name=prop_name,
                archived=False,
            )
            options = []
            for opt in (prop.options or []):
                if getattr(opt, "hidden", False):
                    continue
                options.append({"label": opt.label, "value": opt.value})
            result[prop_name] = options
        except Exception as e:
            logger.warning(
                f"[FETCH_SELECT_OPTIONS] fallo cargando {object_type}.{prop_name}: {e}"
            )
            result[prop_name] = []
    return result


def resolve_enum_label(client, object_type: str, property_name: str, internal_value: str) -> str:
    """Resuelve el label visible de un campo SELECT. Devuelve internal_value como fallback."""
    if not internal_value:
        return internal_value
    try:
        prop = client.crm.properties.core_api.get_by_name(
            object_type=object_type,
            property_name=property_name,
        )
        for option in (prop.options or []):
            if option.value == internal_value:
                return option.label
    except Exception as e:
        logger.warning(
            f"[RESOLVE_ENUM_LABEL] fallo resolviendo {object_type}.{property_name}"
            f"={internal_value!r}: {e}"
        )
    return internal_value
