OBJECT_TYPE_CONTENEDOR = "2-54989406"
OBJECT_TYPE_ELEMENTO   = "2-54989407"
OBJECT_TYPE_DEAL       = "deals"
OBJECT_TYPE_COMPANY    = "0-2"
OBJECT_TYPE_PROVEEDOR  = "2-43108800"
OBJECT_TYPE_RUTA       = "2-53295516"

PEDIDO_PIPELINE_ID = "725914649"

DEAL_PROP_NUMERO_DE_PEDIDO       = "numero_de_pedido"
DEAL_PROP_PIPELINE               = "pipeline"
DEAL_PROP_ETD                    = "etd"
DEAL_PROP_ETA                    = "eta"

DEAL_PROP_BL_VALIDADO_LOGISTICA      = "bl_validado_logistica"
DEAL_PROP_BL_VALIDADO_ADMINISTRACION = "bl_validado_administracion"
DEAL_PROP_BL_ENVIADO_CLIENTE         = "bl_enviado_cliente"
DEAL_PROP_TIPO_DE_BL                 = "tipo_de_bl"
DEAL_PROP_BORRADOR_BL                = "borrador_bl"
DEAL_PROP_NUMERO_DE_BOOKING          = "numero_de_booking"
DEAL_PROP_CAMBIOS_EN_BL              = "cambios_en_bl"

DEAL_PROP_FACTURA_DEL_PEDIDO       = "factura_del_pedido"
DEAL_PROP_PACKING_LIST_PROEX       = "packing_list_proex"
DEAL_PROP_CARTA_DE_PORTE_PROEX     = "carta_de_porte_proex"
DEAL_PROP_FECHA_FACTURACION_PEDIDO = "fecha_de_facturacion_pedido"
DEAL_PROP_FECHA_VENCIMIENTO_FACTURA = "fecha_de_vencimiento_factura"
DEAL_PROP_NUMERO_DE_FACTURA        = "numero_de_factura"

DEAL_PROP_FECHA_DE_ENTREGA      = "fecha_de_entrega"
DEAL_PROP_DIRECCION_DE_ENTREGA  = "direccion_de_entrega"
DEAL_PROP_DATOS_DEL_CHOFER      = "datos_del_chofer"
DEAL_PROP_TRANSITARIO_DEL_PEDIDO = "transitario_del_pedido"
# Doble transitario (camión + tramo marítimo): la prop legada pasa a significar
# tramo marítimo/principal y esta lleva el terrestre. Puede no existir aún en el portal.
DEAL_PROP_TRANSITARIO_TERRESTRE_DEL_PEDIDO = "transitario_terrestre_del_pedido"

BL_FILE_PREFIX_BORRADOR = "borrador_BL_"
BL_FILE_PREFIX_FINAL    = "final_BL_"
BL_FILES_FOLDER         = "/documentos-proex/bl"

DEAL_SELECT_PROPERTIES = [
    ("deals", DEAL_PROP_TIPO_DE_BL),
]

FILE_TYPE_BL_BORRADOR = "bl_borrador"
FILE_TYPE_BL_FINAL    = "bl_final"

FILE_TYPE_ORIGEN_BORRADOR    = "origen_borrador"
FILE_TYPE_ORIGEN_VALIDADO    = "origen_validado"
FILE_TYPE_ORIGEN_SELLADO     = "origen_sellado"
FILE_TYPE_SANITARIO_BORRADOR = "sanitario_borrador"
FILE_TYPE_SANITARIO_VALIDADO = "sanitario_validado"
FILE_TYPE_ALBARAN_MENSAJERIA = "albaran_mensajeria"
ALBARAN_MENSAJERIA_PREFIX    = "albaran_mensajeria_"
FILE_TYPE_SANITARIO_SELLADO  = "sanitario_sellado"

CERT_ORIGEN_FOLDER    = "/documentos-proex/origen"
CERT_SANITARIO_FOLDER = "/documentos-proex/sanitario"

CONTENEDOR_PROP_CERT_ORIGEN_BORRADOR    = "certificado_origen_borrador"
CONTENEDOR_PROP_CERT_ORIGEN             = "certificado_origen"
CONTENEDOR_PROP_CERT_SANITARIO          = "certificado_sanitario"
CONTENEDOR_PROP_CERT_ORIGEN_VALIDADO    = "certificado_origen_validado"
CONTENEDOR_PROP_CERT_SANITARIO_VALIDADO = "certificado_sanitario_validado"
CONTENEDOR_PROP_CERT_ORIGEN_ENVIAR_FIRMAR    = "certificado_origen_enviar_a_firmar"
CONTENEDOR_PROP_CERT_SANITARIO_ENVIAR_FIRMAR = "certificado_sanitario_enviar_a_firmar"

CONTENEDOR_PROP_DOCUMENTOS        = "documentos"
CONTENEDOR_PROP_OTROS_DOCUMENTOS  = "otros_documentos"
CONTENEDOR_PROP_FOTOS_DE_CARGA    = "fotos_de_carga"
CONTENEDOR_PROP_TIPO_CONTENEDOR   = "tipo_contenedor"
CONTENEDOR_PROP_WAIVER_VALIDADO   = "waiver_validado"

# El nombre interno real en HubSpot es `envio_por_mensajeria` (verificado contra
# el portal); antes apuntaba a `enviar_por_mensajeria`, que no existe.
CONTENEDOR_PROP_ENVIAR_POR_MENSAJERIA         = "envio_por_mensajeria"
CONTENEDOR_PROP_PERMITIR_ENVIAR_DOCUMENTACION = "permitir_enviar_documentacion"
CONTENEDOR_PROP_DOCUMENTACION_RECIBIDA        = "documentacion_recibida"
CONTENEDOR_PROP_MERCANCIA_RETIRADA            = "mercancia_retirada"
CONTENEDOR_PROP_FECHA_LLEGADA_CONTENEDOR      = "fecha_llegada_contenedor"
CONTENEDOR_PROP_FECHA_RETIRADA_MERCANCIA      = "fecha_retirada_mercancia"
# Envío por mensajería — gestión de administración: datos de admin (text) + albarán
# de recogida (subida real). Sin fechas.
CONTENEDOR_PROP_DATOS_ENVIO_MENSAJERIA          = "datos_envio_mensajeria"
CONTENEDOR_PROP_ALBARAN_MENSAJERIA              = "albaran_mensajeria"

CONTENEDOR_DOCS_FOLDER  = "/documentos-proex/contenedor-docs"
OTROS_DOCS_FOLDER       = "/documentos-proex/otros-documentos"
FOTOS_CARGA_FOLDER      = "/documentos-proex/fotos-carga"

CONTENEDOR_DOC_PREFIX_DUA              = "dua_"
CONTENEDOR_DOC_PREFIX_ARC              = "arc_"
CONTENEDOR_DOC_PREFIX_EUR1             = "eur1_"
CONTENEDOR_DOC_PREFIX_ANEXO_I          = "anexo_i_"
CONTENEDOR_DOC_PREFIX_INSPECCION       = "inspeccion_"
CONTENEDOR_DOC_PREFIX_SEGURO           = "seguro_"
CONTENEDOR_DOC_PREFIX_WAIVER_BORRADOR  = "borrador_waiver_"
CONTENEDOR_DOC_PREFIX_WAIVER_FINAL     = "final_waiver_"
OTROS_DOCS_PREFIX     = "otros_"
FOTO_CARGA_PREFIX     = "foto_carga_"

FILE_TYPE_DOC_DUA              = "doc_dua"
FILE_TYPE_DOC_ARC              = "doc_arc"
FILE_TYPE_DOC_EUR1             = "doc_eur1"
FILE_TYPE_DOC_ANEXO_I          = "doc_anexo_i"
FILE_TYPE_DOC_INSPECCION       = "doc_inspeccion"
FILE_TYPE_DOC_SEGURO           = "doc_seguro"
FILE_TYPE_DOC_WAIVER_BORRADOR  = "doc_waiver_borrador"
FILE_TYPE_DOC_WAIVER_FINAL     = "doc_waiver_final"
FILE_TYPE_OTRO_DOC             = "otro_doc"
FILE_TYPE_FOTO_CARGA           = "foto_carga"

MAX_FILES_PER_PROPERTY = 10

MIME_PDF_ONLY = ("application/pdf",)
MIME_OTROS_DOCUMENTOS = (
    "application/pdf",
    "image/jpeg",
    "image/png",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
)
MIME_FOTOS_CARGA = (
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
)

FILE_TYPE_CONFIG: dict[str, dict] = {
    FILE_TYPE_BL_BORRADOR: {
        "scope":              "deal",
        "prop":               DEAL_PROP_BORRADOR_BL,
        "filename_prefix":    BL_FILE_PREFIX_BORRADOR,
        "folder":             BL_FILES_FOLDER,
        "label":              "borrador BL",
        "replace_by_prefix":  True,
        "allowed_mime_types": MIME_PDF_ONLY,
    },
    FILE_TYPE_BL_FINAL: {
        "scope":              "deal",
        "prop":               DEAL_PROP_BORRADOR_BL,
        "filename_prefix":    BL_FILE_PREFIX_FINAL,
        "folder":             BL_FILES_FOLDER,
        "label":              "BL final",
        "replace_by_prefix":  True,
        "allowed_mime_types": MIME_PDF_ONLY,
    },
    FILE_TYPE_ORIGEN_BORRADOR: {
        "scope":              "contenedor",
        "prop":               CONTENEDOR_PROP_CERT_ORIGEN_BORRADOR,
        "filename_prefix":    "origen_borrador_",
        "folder":             CERT_ORIGEN_FOLDER,
        "label":              "origen borrador",
        "replace_by_prefix":  True,
        "allowed_mime_types": MIME_PDF_ONLY,
    },
    FILE_TYPE_ORIGEN_VALIDADO: {
        "scope":              "contenedor",
        "prop":               CONTENEDOR_PROP_CERT_ORIGEN,
        "filename_prefix":    "origen_validado_",
        "folder":             CERT_ORIGEN_FOLDER,
        "label":              "origen validado por cliente",
        "replace_by_prefix":  True,
        "allowed_mime_types": MIME_PDF_ONLY,
    },
    FILE_TYPE_ORIGEN_SELLADO: {
        "scope":              "contenedor",
        "prop":               CONTENEDOR_PROP_CERT_ORIGEN,
        "filename_prefix":    "origen_sellado_",
        "folder":             CERT_ORIGEN_FOLDER,
        "label":              "origen sellado y firmado",
        "replace_by_prefix":  True,
        "allowed_mime_types": MIME_PDF_ONLY,
    },
    FILE_TYPE_SANITARIO_BORRADOR: {
        "scope":              "contenedor",
        "prop":               CONTENEDOR_PROP_CERT_SANITARIO,
        "filename_prefix":    "sanitario_borrador_",
        "folder":             CERT_SANITARIO_FOLDER,
        "label":              "sanitario borrador",
        "replace_by_prefix":  True,
        "allowed_mime_types": MIME_PDF_ONLY,
    },
    FILE_TYPE_SANITARIO_VALIDADO: {
        "scope":              "contenedor",
        "prop":               CONTENEDOR_PROP_CERT_SANITARIO,
        "filename_prefix":    "sanitario_validado_",
        "folder":             CERT_SANITARIO_FOLDER,
        "label":              "sanitario validado por cliente",
        "replace_by_prefix":  True,
        "allowed_mime_types": MIME_PDF_ONLY,
    },
    FILE_TYPE_SANITARIO_SELLADO: {
        "scope":              "contenedor",
        "prop":               CONTENEDOR_PROP_CERT_SANITARIO,
        "filename_prefix":    "sanitario_sellado_",
        "folder":             CERT_SANITARIO_FOLDER,
        "label":              "sanitario sellado y firmado",
        "replace_by_prefix":  True,
        "allowed_mime_types": MIME_PDF_ONLY,
    },
    FILE_TYPE_DOC_DUA: {
        "scope":              "contenedor",
        "prop":               CONTENEDOR_PROP_DOCUMENTOS,
        "filename_prefix":    CONTENEDOR_DOC_PREFIX_DUA,
        "folder":             CONTENEDOR_DOCS_FOLDER,
        "label":              "DUA",
        "replace_by_prefix":  True,
        "allowed_mime_types": MIME_PDF_ONLY,
    },
    FILE_TYPE_DOC_ARC: {
        "scope":              "contenedor",
        "prop":               CONTENEDOR_PROP_DOCUMENTOS,
        "filename_prefix":    CONTENEDOR_DOC_PREFIX_ARC,
        "folder":             CONTENEDOR_DOCS_FOLDER,
        "label":              "ARC",
        "replace_by_prefix":  True,
        "allowed_mime_types": MIME_PDF_ONLY,
    },
    FILE_TYPE_DOC_EUR1: {
        "scope":              "contenedor",
        "prop":               CONTENEDOR_PROP_DOCUMENTOS,
        "filename_prefix":    CONTENEDOR_DOC_PREFIX_EUR1,
        "folder":             CONTENEDOR_DOCS_FOLDER,
        "label":              "EUR.1",
        "replace_by_prefix":  True,
        "allowed_mime_types": MIME_PDF_ONLY,
    },
    FILE_TYPE_DOC_ANEXO_I: {
        "scope":              "contenedor",
        "prop":               CONTENEDOR_PROP_DOCUMENTOS,
        "filename_prefix":    CONTENEDOR_DOC_PREFIX_ANEXO_I,
        "folder":             CONTENEDOR_DOCS_FOLDER,
        "label":              "Anexo I",
        "replace_by_prefix":  True,
        "allowed_mime_types": MIME_PDF_ONLY,
    },
    FILE_TYPE_DOC_INSPECCION: {
        "scope":              "contenedor",
        "prop":               CONTENEDOR_PROP_DOCUMENTOS,
        "filename_prefix":    CONTENEDOR_DOC_PREFIX_INSPECCION,
        "folder":             CONTENEDOR_DOCS_FOLDER,
        "label":              "Inspección",
        "replace_by_prefix":  True,
        "allowed_mime_types": MIME_PDF_ONLY,
    },
    FILE_TYPE_DOC_SEGURO: {
        "scope":              "contenedor",
        "prop":               CONTENEDOR_PROP_DOCUMENTOS,
        "filename_prefix":    CONTENEDOR_DOC_PREFIX_SEGURO,
        "folder":             CONTENEDOR_DOCS_FOLDER,
        "label":              "Seguro",
        "replace_by_prefix":  True,
        "allowed_mime_types": MIME_PDF_ONLY,
    },
    FILE_TYPE_DOC_WAIVER_BORRADOR: {
        "scope":              "contenedor",
        "prop":               CONTENEDOR_PROP_DOCUMENTOS,
        "filename_prefix":    CONTENEDOR_DOC_PREFIX_WAIVER_BORRADOR,
        "folder":             CONTENEDOR_DOCS_FOLDER,
        "label":              "Waiver borrador",
        "replace_by_prefix":  True,
        "allowed_mime_types": MIME_PDF_ONLY,
    },
    FILE_TYPE_DOC_WAIVER_FINAL: {
        "scope":              "contenedor",
        "prop":               CONTENEDOR_PROP_DOCUMENTOS,
        "filename_prefix":    CONTENEDOR_DOC_PREFIX_WAIVER_FINAL,
        "folder":             CONTENEDOR_DOCS_FOLDER,
        "label":              "Waiver final",
        "replace_by_prefix":  True,
        "allowed_mime_types": MIME_PDF_ONLY,
    },
    FILE_TYPE_OTRO_DOC: {
        "scope":                     "contenedor",
        "prop":                      CONTENEDOR_PROP_OTROS_DOCUMENTOS,
        "filename_prefix":           OTROS_DOCS_PREFIX,
        "folder":                    OTROS_DOCS_FOLDER,
        "label":                     "otro documento",
        "replace_by_prefix":         False,
        "preserve_original_filename": True,
        "max_files":                 MAX_FILES_PER_PROPERTY,
        "allowed_mime_types":        MIME_OTROS_DOCUMENTOS,
    },
    FILE_TYPE_FOTO_CARGA: {
        "scope":              "contenedor",
        "prop":               CONTENEDOR_PROP_FOTOS_DE_CARGA,
        "filename_prefix":    FOTO_CARGA_PREFIX,
        "folder":             FOTOS_CARGA_FOLDER,
        "label":              "foto de carga",
        "replace_by_prefix":  False,
        "max_files":          MAX_FILES_PER_PROPERTY,
        "allowed_mime_types": MIME_FOTOS_CARGA,
    },
    FILE_TYPE_ALBARAN_MENSAJERIA: {
        "scope":              "contenedor",
        "prop":               CONTENEDOR_PROP_ALBARAN_MENSAJERIA,
        "filename_prefix":    ALBARAN_MENSAJERIA_PREFIX,
        "folder":             CONTENEDOR_DOCS_FOLDER,
        "label":              "albarán de recogida",
        "replace_by_prefix":  True,
        "allowed_mime_types": MIME_OTROS_DOCUMENTOS,
    },
}

DOC_TIPO_TO_PREFIX = {
    "dua":             CONTENEDOR_DOC_PREFIX_DUA,
    "arc":             CONTENEDOR_DOC_PREFIX_ARC,
    "eur1":            CONTENEDOR_DOC_PREFIX_EUR1,
    "anexo_i":         CONTENEDOR_DOC_PREFIX_ANEXO_I,
    "inspeccion":      CONTENEDOR_DOC_PREFIX_INSPECCION,
    "seguro":          CONTENEDOR_DOC_PREFIX_SEGURO,
    "waiver_borrador": CONTENEDOR_DOC_PREFIX_WAIVER_BORRADOR,
    "waiver_final":    CONTENEDOR_DOC_PREFIX_WAIVER_FINAL,
}

CONTENEDOR_PROP_ETD = "etd"
CONTENEDOR_PROP_ETA = "eta"
DEAL_PROP_DESCRIPCION_MERCANCIA  = "certificado_origen_mercancia"
DEAL_PROP_OBSERVACIONES          = "observaciones"
DEAL_PROP_FOTOS_DE_CARGA         = "fotos_de_carga"

DEAL_PROP_RESPONSABLE_COMERCIAL      = "responsable_comercial"
DEAL_PROP_RESPONSABLE_ADMINISTRACION = "responsable_administracion"
DEAL_PROP_RESPONSABLE_LOGISTICA      = "responsable_logistica"

# Estas propiedades viven en el Deal de cotización (NO en el pipeline de pedidos)
COTIZACION_PROP_CONSIGNEE             = "consignee"
COTIZACION_PROP_NOTIFY                = "notify"
COTIZACION_PROP_PUERTO_DESTINO        = "puerto_destino"
COTIZACION_PROP_PUERTO_SALIDA         = "puerto_salida"
COTIZACION_PROP_ALMACEN               = "almacen"
COTIZACION_PROP_LUGAR_CARGA           = "lugar_carga"
COTIZACION_PROP_LOCALIDAD_DESTINO     = "localidad_destino"
COTIZACION_PROP_COMENTARIOS_LOGISTICA = "comentarios_logistica"
COTIZACION_PROP_TIPO_DE_VENTA         = "tipo_de_venta"
COTIZACION_ALMACEN_PROEX_SAN_ROQUE    = "01"

COMPANY_PROP_NAME          = "name"
COMPANY_PROP_TIPO_CLIENTE  = "tipo_cliente"

# Flujo derivado del transporte (tipo_contenedor) y el origen (Cotización.almacen).
# El tipo de cliente ya no decide la apariencia.
TIPO_FLUJO_CONTENEDOR             = "contenedor"
TIPO_FLUJO_CONTENEDOR_SAN_ROQUE  = "contenedor_san_roque"
TIPO_FLUJO_CAMION                = "camion"
TIPO_FLUJO_CAMION_SAN_ROQUE      = "camion_san_roque"

# Camión = valores de esta allowlist (normalizados); el resto, contenedor.
# CAMION16P a confirmar con cliente (de momento contenedor).
CAMION_TIPO_CONTENEDOR = frozenset({"TRAILER80"})

DEAL_DETALLE_PROPERTIES = [
    DEAL_PROP_NUMERO_DE_PEDIDO,
    DEAL_PROP_PIPELINE,
    "dealstage",
    "dealname",
    DEAL_PROP_ETD,
    DEAL_PROP_ETA,
    DEAL_PROP_DESCRIPCION_MERCANCIA,
    DEAL_PROP_OBSERVACIONES,
    DEAL_PROP_FOTOS_DE_CARGA,
    DEAL_PROP_BL_VALIDADO_LOGISTICA,
    DEAL_PROP_BL_VALIDADO_ADMINISTRACION,
    DEAL_PROP_BL_ENVIADO_CLIENTE,
    DEAL_PROP_TIPO_DE_BL,
    DEAL_PROP_BORRADOR_BL,
    DEAL_PROP_NUMERO_DE_BOOKING,
    DEAL_PROP_CAMBIOS_EN_BL,
    DEAL_PROP_FACTURA_DEL_PEDIDO,
    DEAL_PROP_PACKING_LIST_PROEX,
    DEAL_PROP_CARTA_DE_PORTE_PROEX,
    DEAL_PROP_FECHA_FACTURACION_PEDIDO,
    DEAL_PROP_FECHA_VENCIMIENTO_FACTURA,
    DEAL_PROP_NUMERO_DE_FACTURA,
    COTIZACION_PROP_CONSIGNEE,
    COTIZACION_PROP_NOTIFY,
    COTIZACION_PROP_PUERTO_DESTINO,
    COTIZACION_PROP_PUERTO_SALIDA,
    COTIZACION_PROP_ALMACEN,
    COTIZACION_PROP_LUGAR_CARGA,
    COTIZACION_PROP_LOCALIDAD_DESTINO,
    COTIZACION_PROP_COMENTARIOS_LOGISTICA,
    COTIZACION_PROP_TIPO_DE_VENTA,
    DEAL_PROP_FECHA_DE_ENTREGA,
    DEAL_PROP_DIRECCION_DE_ENTREGA,
    DEAL_PROP_DATOS_DEL_CHOFER,
    DEAL_PROP_TRANSITARIO_DEL_PEDIDO,
    DEAL_PROP_TRANSITARIO_TERRESTRE_DEL_PEDIDO,
    "carga_por_palets",
    "preprints_language",
]

CONTENEDOR_DETALLE_PROPERTIES = [
    "nombre",
    "numero_contenedor",
    "numero_precinto",
    "peso_bruto",
    "peso_neto",
    "tara",
    "total_cajas",
    "documentos_a_generar",
    "importe_pendiente_cobro",
    "price",
    CONTENEDOR_PROP_ETD,
    CONTENEDOR_PROP_ETA,
    CONTENEDOR_PROP_TIPO_CONTENEDOR,
    CONTENEDOR_PROP_CERT_ORIGEN_BORRADOR,
    CONTENEDOR_PROP_CERT_ORIGEN,
    CONTENEDOR_PROP_CERT_SANITARIO,
    CONTENEDOR_PROP_CERT_ORIGEN_VALIDADO,
    CONTENEDOR_PROP_CERT_SANITARIO_VALIDADO,
    CONTENEDOR_PROP_CERT_ORIGEN_ENVIAR_FIRMAR,
    CONTENEDOR_PROP_CERT_SANITARIO_ENVIAR_FIRMAR,
    CONTENEDOR_PROP_DOCUMENTOS,
    CONTENEDOR_PROP_OTROS_DOCUMENTOS,
    CONTENEDOR_PROP_FOTOS_DE_CARGA,
    CONTENEDOR_PROP_WAIVER_VALIDADO,
    CONTENEDOR_PROP_ENVIAR_POR_MENSAJERIA,
    CONTENEDOR_PROP_PERMITIR_ENVIAR_DOCUMENTACION,
    CONTENEDOR_PROP_DOCUMENTACION_RECIBIDA,
    CONTENEDOR_PROP_MERCANCIA_RETIRADA,
    CONTENEDOR_PROP_FECHA_LLEGADA_CONTENEDOR,
    CONTENEDOR_PROP_FECHA_RETIRADA_MERCANCIA,
    CONTENEDOR_PROP_DATOS_ENVIO_MENSAJERIA,
    CONTENEDOR_PROP_ALBARAN_MENSAJERIA,
]

# USER_DEFINED, label "elementos" (Contenedor → Elemento)
ASSOCIATION_TYPE_CONTENEDOR_TO_ELEMENTO = 491

# Multi-select que indica qué tipos de documento deben generarse para este contenedor
CONTENEDOR_PROP_DOCUMENTOS_A_GENERAR = "documentos_a_generar"

DOC_TYPE_ORIGEN_BORRADOR = "origen_borrador"
DOC_TYPE_ORIGEN_FINAL = "origen_final"
DOC_TYPE_SANITARIO = "sanitario"

ALL_DOC_TYPES = [
    DOC_TYPE_ORIGEN_BORRADOR,
    DOC_TYPE_ORIGEN_FINAL,
    DOC_TYPE_SANITARIO,
]

# Borrador y final comparten valor en HubSpot (`certificado_de_origen`)
DOC_TYPE_TO_HUBSPOT_FILTER = {
    DOC_TYPE_ORIGEN_BORRADOR: "certificado_de_origen",
    DOC_TYPE_ORIGEN_FINAL:    "certificado_de_origen",
    DOC_TYPE_SANITARIO:       "certificado_sanitario",
}

DOC_TYPE_TO_FILE_PROPERTY = {
    DOC_TYPE_ORIGEN_BORRADOR: "certificado_origen_borrador",
    DOC_TYPE_ORIGEN_FINAL:    "certificado_origen",
    DOC_TYPE_SANITARIO:       "certificado_sanitario",
}

ALL_CONTENEDOR_FILE_PROPERTY_NAMES: list[str] = list(set(DOC_TYPE_TO_FILE_PROPERTY.values()))

CONTENEDOR_DOC_PROPERTIES = {
    DOC_TYPE_ORIGEN_BORRADOR: {
        "group_generation_id": "doc_group_id_origen_borrador",
    },
    DOC_TYPE_ORIGEN_FINAL: {
        "group_generation_id": "doc_group_id_origen_final",
    },
    DOC_TYPE_SANITARIO: {
        "group_generation_id": "doc_group_id_sanitario",
    },
}

ALL_CONTENEDOR_DOC_PROPERTY_NAMES: list[str] = [
    prop
    for props in CONTENEDOR_DOC_PROPERTIES.values()
    for prop in props.values()
]

CONTENEDOR_BASE_PROPERTIES = [
    "nombre",
    CONTENEDOR_PROP_ETD,
    CONTENEDOR_PROP_ETA,
]

CONTENEDOR_ALL_PROPERTIES = CONTENEDOR_BASE_PROPERTIES + ALL_CONTENEDOR_DOC_PROPERTY_NAMES

CONTENEDOR_GENERATE_PROPERTIES = [
    "nombre",
    "numero_contenedor",
    "tipo_contenedor",
    "documentos_a_generar",
    *ALL_CONTENEDOR_FILE_PROPERTY_NAMES,
]

DOC_TYPE_LABELS_ES: dict[str, str] = {
    DOC_TYPE_ORIGEN_BORRADOR: "Certificado de Origen (Borrador)",
    DOC_TYPE_ORIGEN_FINAL:    "Certificado de Origen",
    DOC_TYPE_SANITARIO:       "Certificado Sanitario",
}

ELEMENTO_PROPERTIES = [
    "nombre",
    "nombre_es",
    "nombre_en",
    "nombre_fr",
    "cantidad",
    "peso_neto_total",
    "peso_bruto_total",
    "peso_neto_unitario",
    "peso_bruto_unitario",
    "tipo_articulo",
    "formato",
    "marca",
]

ELEMENTO_TIPO_FABRICANTE = "fabricante"

DEAL_GENERATE_PROPERTIES = [
    "consignee",
    "shipper",
    "puerto_destino",
    "certificado_origen_mercancia",
    "observaciones",
]

# tipo_contenedor HubSpot → (prefijo_tamaño, clave_traducción en TRANSLATIONS)
CONTAINER_TYPE_DISPLAY: dict[str, tuple[str, str]] = {
    "D20DR": ("20", "dry_container"),
    "d20dr": ("20", "dry_container"),
    "D40DR": ("40", "dry_container"),
    "d40dr": ("40", "dry_container"),
}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "EN": {
        "cases":         "CASES",
        "cases_of":      "CASES OF",
        "net_weight":    "NET WEIGHT",
        "gross_weight":  "GROSS WEIGHT",
        "dry_container": "DRY CONTAINER",
        "sea_transport": "SEA TRANSPORT",
    },
    "FR": {
        "cases":         "CAISSES",
        "cases_of":      "CAISSES DE",
        "net_weight":    "POIDS NET",
        "gross_weight":  "POIDS BRUT",
        "dry_container": "CONTENEUR SEC",
        "sea_transport": "TRANSPORT MARITIME",
    },
    "ES": {
        "cases":         "CAJAS",
        "cases_of":      "CAJAS DE",
        "net_weight":    "PESO NETO",
        "gross_weight":  "PESO BRUTO",
        "dry_container": "CONTENEDOR SECO",
        "sea_transport": "TRANSPORTE MARÍTIMO",
    },
}

# idioma del certificado (ES/EN/FR, en mayúsculas como las claves de TRANSLATIONS)
# → columna de nombre traducido en Elementos y en la HubDB formato_producto.
LANG_TO_NOMBRE_COLUMN: dict[str, str] = {
    "ES": "nombre_es",
    "EN": "nombre_en",
    "FR": "nombre_fr",
}

ROLLBACK_VALID_DOC_TYPES: set = {"origen_borrador", "origen", "sanitario"}

# "origen" en la API equivale a "origen_final" internamente
ROLLBACK_API_TO_INTERNAL_DOC_TYPE: dict = {
    "origen_borrador": DOC_TYPE_ORIGEN_BORRADOR,
    "origen":          DOC_TYPE_ORIGEN_FINAL,
    "sanitario":       DOC_TYPE_SANITARIO,
}

OBJECT_TYPE_COBRO = "2-44408688"
ASSOC_CATEGORY_USER_DEFINED = "USER_DEFINED"

# Negocio Documento: se crea (1:1) cuando un Negocio Pedido entra en la etapa
# terminal "Preparar Documentación" del pipeline de pedidos. Vive en su propio
# pipeline y arranca en "En proceso".
PEDIDO_DEALSTAGE_PREPARAR_DOC = "1368383244"

DOCUMENTO_PIPELINE_ID = "905179456"

DOC_DEALSTAGE_EN_PROCESO     = "1371580054"
DOC_DEALSTAGE_PTE_CONFIRMAR  = "1371580055"
DOC_DEALSTAGE_CONFIRMADO     = "1371580056"
DOC_DEALSTAGE_ENVIADA        = "1371580059"
DOC_DEALSTAGE_RETIRADO       = "1380233754"
DOC_DEALSTAGE_CIERRE_PERDIDO = "1371580060"

# Cadena auto-calculada de menor a mayor. "En proceso" es el suelo; "Retirado"
# es la etapa ganada (mercancía retirada por el cliente). "Cierre perdido" queda
# fuera (solo manual, intocable por el calculador).
DOC_DEALSTAGE_CADENA = [
    DOC_DEALSTAGE_EN_PROCESO,
    DOC_DEALSTAGE_PTE_CONFIRMAR,
    DOC_DEALSTAGE_CONFIRMADO,
    DOC_DEALSTAGE_ENVIADA,
    DOC_DEALSTAGE_RETIRADO,
]

DOC_DEALSTAGE_LABELS = {
    DOC_DEALSTAGE_EN_PROCESO:     "En proceso",
    DOC_DEALSTAGE_PTE_CONFIRMAR:  "Pte. confirmar",
    DOC_DEALSTAGE_CONFIRMADO:     "Confirmado",
    DOC_DEALSTAGE_ENVIADA:        "Enviada",
    DOC_DEALSTAGE_RETIRADO:       "Retirado",
    DOC_DEALSTAGE_CIERRE_PERDIDO: "Cierre perdido",
}

# TypeIds dedicados del Negocio Documento (USER_DEFINED, direccionales). Cada uno
# se crea desde el lado en que se definió en HubSpot:
#   682 documento → contenedor (definida desde Documento)
#   681 pedido → documento     (definida desde Pedido; se crea desde el pedido)
#   684 cotización → documento (definida desde Cotización; se crea desde la cotización)
ASSOC_TYPE_ID_DOCUMENTO_TO_CONTENEDOR = 682
ASSOC_TYPE_ID_PEDIDO_TO_DOCUMENTO     = 681
ASSOC_TYPE_ID_COTIZACION_TO_DOCUMENTO = 684

# Cabecera del pedido-deal que se copia al documento-deal al crearlo. No se
# copian archivos ni flags vivos: el calculador los lee en caliente.
PEDIDO_PROPS_A_REPLICAR_EN_DOCUMENTO = [
    DEAL_PROP_NUMERO_DE_PEDIDO,
    DEAL_PROP_ETD,
    DEAL_PROP_ETA,
    DEAL_PROP_TIPO_DE_BL,
    DEAL_PROP_NUMERO_DE_BOOKING,
    DEAL_PROP_CAMBIOS_EN_BL,
    DEAL_PROP_DESCRIPCION_MERCANCIA,
    DEAL_PROP_OBSERVACIONES,
    COTIZACION_PROP_CONSIGNEE,
    COTIZACION_PROP_NOTIFY,
    COTIZACION_PROP_PUERTO_SALIDA,
    COTIZACION_PROP_PUERTO_DESTINO,
    "preprints_language",
    DEAL_PROP_RESPONSABLE_COMERCIAL,
    DEAL_PROP_RESPONSABLE_ADMINISTRACION,
    DEAL_PROP_RESPONSABLE_LOGISTICA,
]

# Valores del multi-select documentos_a_generar que marcan obligatoriedad. La
# lista es autoritativa: un documento solo gatea la etapa si está aquí.
DOC_GENERAR_VALUE_BL        = "bl"
DOC_GENERAR_VALUE_ORIGEN    = DOC_TYPE_TO_HUBSPOT_FILTER[DOC_TYPE_ORIGEN_BORRADOR]
DOC_GENERAR_VALUE_SANITARIO = DOC_TYPE_TO_HUBSPOT_FILTER[DOC_TYPE_SANITARIO]
DOC_GENERAR_VALUE_OTROS     = "otros"

# Otros documentos obligatorios: valor de documentos_a_generar → prefijos de
# nombre que cuentan como "subido" dentro de la prop `documentos`. "otros" vive
# en su propia prop (otros_documentos) y se trata aparte.
DOC_GENERAR_OTROS_TO_PREFIXES = {
    "dua":        (CONTENEDOR_DOC_PREFIX_DUA,),
    "arc":        (CONTENEDOR_DOC_PREFIX_ARC,),
    "eur1":       (CONTENEDOR_DOC_PREFIX_EUR1,),
    "anexo_i":    (CONTENEDOR_DOC_PREFIX_ANEXO_I,),
    "inspeccion": (CONTENEDOR_DOC_PREFIX_INSPECCION,),
    "seguro":     (CONTENEDOR_DOC_PREFIX_SEGURO,),
    "waiver":     (CONTENEDOR_DOC_PREFIX_WAIVER_BORRADOR, CONTENEDOR_DOC_PREFIX_WAIVER_FINAL),
}
