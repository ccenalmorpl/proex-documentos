"""Application constants — IDs de objetos HubSpot y tipos de documento."""

# ── HubSpot Custom Object IDs ──────────────────────────────────────────────
OBJECT_TYPE_CONTENEDOR = "2-54989406"
OBJECT_TYPE_DEAL = "deals"

# ── Tipos de documento soportados ─────────────────────────────────────────
DOC_TYPE_ORIGEN_BORRADOR = "origen_borrador"
DOC_TYPE_ORIGEN_FINAL = "origen_final"
DOC_TYPE_SANITARIO = "sanitario"

ALL_DOC_TYPES = [
    DOC_TYPE_ORIGEN_BORRADOR,
    DOC_TYPE_ORIGEN_FINAL,
    DOC_TYPE_SANITARIO,
]

# ── Propiedades del Contenedor para cada tipo de documento ─────────────────
# Estructura: {doc_type: {campo_logico: nombre_propiedad_hubspot}}
CONTENEDOR_DOC_PROPERTIES = {
    DOC_TYPE_ORIGEN_BORRADOR: {
        "group_generation_id": "doc_group_generation_id_origen_borrador",
        "file_id":             "doc_file_id_origen_borrador",
        "file_url":            "doc_file_url_origen_borrador",
        "generated_at":        "doc_generated_at_origen_borrador",
    },
    DOC_TYPE_ORIGEN_FINAL: {
        "group_generation_id": "doc_group_generation_id_origen_final",
        "file_id":             "doc_file_id_origen_final",
        "file_url":            "doc_file_url_origen_final",
        "generated_at":        "doc_generated_at_origen_final",
    },
    DOC_TYPE_SANITARIO: {
        "group_generation_id": "doc_group_generation_id_sanitario",
        "file_id":             "doc_file_id_sanitario",
        "file_url":            "doc_file_url_sanitario",
        "generated_at":        "doc_generated_at_sanitario",
    },
}

# Lista plana de todas las propiedades de documentos del Contenedor
ALL_CONTENEDOR_DOC_PROPERTY_NAMES: list[str] = [
    prop
    for props in CONTENEDOR_DOC_PROPERTIES.values()
    for prop in props.values()
]

# Propiedades base del Contenedor necesarias para los listados
CONTENEDOR_BASE_PROPERTIES = [
    "hs_object_id",
    "name",
    "fecha_carga",
    # nombre del cliente / empresa asociada (ajustar al nombre real de la propiedad)
    "nombre_cliente",
    # fecha de creación de la cotización asociada
    "fecha_cotizacion",
]

# Todas las propiedades a solicitar al buscar contenedores
CONTENEDOR_ALL_PROPERTIES = CONTENEDOR_BASE_PROPERTIES + ALL_CONTENEDOR_DOC_PROPERTY_NAMES
