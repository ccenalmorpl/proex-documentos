export const DOC_TYPE_ORIGEN_BORRADOR = "origen_borrador";
export const DOC_TYPE_ORIGEN_FINAL    = "origen_final";
export const DOC_TYPE_SANITARIO       = "sanitario";

export const ALL_DOC_TYPES = [
  DOC_TYPE_ORIGEN_BORRADOR,
  DOC_TYPE_ORIGEN_FINAL,
  DOC_TYPE_SANITARIO,
] as const;

export type DocType = typeof ALL_DOC_TYPES[number];

export const DOC_TYPE_LABELS: Record<string, string> = {
  [DOC_TYPE_ORIGEN_BORRADOR]: "Certificado de Origen (Borrador)",
  [DOC_TYPE_ORIGEN_FINAL]:    "Certificado de Origen",
  [DOC_TYPE_SANITARIO]:       "Certificado Sanitario",
};

// "origen_final" se publica como "origen" en el contrato del endpoint rollback
export const DOC_TYPE_TO_API: Record<string, string> = {
  [DOC_TYPE_ORIGEN_BORRADOR]: "origen_borrador",
  [DOC_TYPE_ORIGEN_FINAL]:    "origen",
  [DOC_TYPE_SANITARIO]:       "sanitario",
};

export const TAB_PENDIENTES = "pendientes";
export const TAB_HISTORICO  = "historico";
export const TAB_GESTION    = "gestion";


// Readonly: vienen pre-rellenados desde el pipeline del pedido
export const OTROS_DOC_TYPE_FACTURA      = "factura";
export const OTROS_DOC_TYPE_PACKING_LIST = "packing_list";
export const OTROS_DOC_TYPE_CARTA_PORTE  = "carta_porte";
// Subibles a nivel contenedor según "documentación a generar" del pedido
export const OTROS_DOC_TYPE_DUA          = "dua";
export const OTROS_DOC_TYPE_ARC          = "arc";
export const OTROS_DOC_TYPE_EUR1         = "eur1";
export const OTROS_DOC_TYPE_ANEXO_I      = "anexo_i";
export const OTROS_DOC_TYPE_INSPECCION   = "inspeccion";
export const OTROS_DOC_TYPE_WAIVER           = "waiver";
export const OTROS_DOC_TYPE_WAIVER_BORRADOR  = "waiver_borrador";
export const OTROS_DOC_TYPE_WAIVER_FINAL     = "waiver_final";
export const OTROS_DOC_TYPE_OTROS            = "otros";

export const OTROS_DOC_LABELS: Record<string, string> = {
  [OTROS_DOC_TYPE_FACTURA]:      "Factura de venta",
  [OTROS_DOC_TYPE_PACKING_LIST]: "Packing list",
  [OTROS_DOC_TYPE_CARTA_PORTE]:  "Carta de porte",
  [OTROS_DOC_TYPE_DUA]:          "DUA",
  [OTROS_DOC_TYPE_ARC]:          "ARC",
  [OTROS_DOC_TYPE_EUR1]:         "EUR.1",
  [OTROS_DOC_TYPE_ANEXO_I]:      "Anexo I",
  [OTROS_DOC_TYPE_INSPECCION]:        "Inspección",
  [OTROS_DOC_TYPE_WAIVER]:            "Waiver",
  [OTROS_DOC_TYPE_WAIVER_BORRADOR]:   "Waiver borrador",
  [OTROS_DOC_TYPE_WAIVER_FINAL]:      "Waiver final",
  [OTROS_DOC_TYPE_OTROS]:             "Otros",
};

export const OTROS_DOC_READONLY: string[] = [
  OTROS_DOC_TYPE_FACTURA,
  OTROS_DOC_TYPE_PACKING_LIST,
  OTROS_DOC_TYPE_CARTA_PORTE,
];

// Tipos discriminados (1 archivo por tipo) que viven en contenedor.documentos y se renderizan en el loop genérico.
// Waiver no está aquí porque se renderiza en su propio sub-bloque (borrador + check + final).
export const OTROS_DOC_SUBIBLES_DISCRIMINADOS = [
  OTROS_DOC_TYPE_DUA,
  OTROS_DOC_TYPE_ARC,
  OTROS_DOC_TYPE_EUR1,
  OTROS_DOC_TYPE_ANEXO_I,
  OTROS_DOC_TYPE_INSPECCION,
] as const;

// Cambio 2 — el DUA abre el timeline de exportación (etapa previa al BL) y por
// eso se saca de "Otros documentos". El resto de documentos sin etapa (ARC,
// EUR.1, Anexo I, inspección, waiver, otros, fotos) se gestionan en "Otros
// documentos". Las subidas se replican al subconjunto seleccionado.
export const EMBARQUE_DOC_TIPO_DUA = OTROS_DOC_TYPE_DUA;

export const EMBARQUE_DOC_TIPOS_EXPORT = [EMBARQUE_DOC_TIPO_DUA] as const;

// Documentos que NO deben renderizarse en "Documentos a aportar" (van en otra etapa o son readonly)
export const OTROS_DOC_GESTIONADOS_EN_OTRAS_ETAPAS = new Set<string>([
  "bl",
  "certificado_de_origen",
  "certificado_sanitario",
  OTROS_DOC_TYPE_FACTURA,
  OTROS_DOC_TYPE_PACKING_LIST,
  OTROS_DOC_TYPE_CARTA_PORTE,
]);

// Sólo estos tipos del checklist renderizan en "Documentos a aportar"
export const OTROS_DOC_SUBIBLES_VALIDOS = new Set<string>([
  ...OTROS_DOC_SUBIBLES_DISCRIMINADOS,
  OTROS_DOC_TYPE_WAIVER,
  OTROS_DOC_TYPE_OTROS,
]);

// Mapping checklist tipo → tipo_documento del endpoint backend
export const OTROS_DOC_TYPE_TO_FILE_TYPE: Record<string, string> = {
  [OTROS_DOC_TYPE_DUA]:               "doc_dua",
  [OTROS_DOC_TYPE_ARC]:               "doc_arc",
  [OTROS_DOC_TYPE_EUR1]:              "doc_eur1",
  [OTROS_DOC_TYPE_ANEXO_I]:           "doc_anexo_i",
  [OTROS_DOC_TYPE_INSPECCION]:        "doc_inspeccion",
  [OTROS_DOC_TYPE_WAIVER_BORRADOR]:   "doc_waiver_borrador",
  [OTROS_DOC_TYPE_WAIVER_FINAL]:      "doc_waiver_final",
  [OTROS_DOC_TYPE_OTROS]:             "otro_doc",
};

export const FOTO_CARGA_FILE_TYPE = "foto_carga";

export const OTROS_DOC_MAX_FILES   = 10;
export const FOTOS_CARGA_MAX_FILES = 10;

// Apariencia y etapas por transporte (contenedor vs camión) y origen (San Roque).
export const TIPO_PEDIDO_CONTENEDOR             = "contenedor";
export const TIPO_PEDIDO_CONTENEDOR_SAN_ROQUE  = "contenedor_san_roque";
export const TIPO_PEDIDO_CAMION                = "camion";
export const TIPO_PEDIDO_CAMION_SAN_ROQUE      = "camion_san_roque";

export type TipoPedido =
  | typeof TIPO_PEDIDO_CONTENEDOR
  | typeof TIPO_PEDIDO_CONTENEDOR_SAN_ROQUE
  | typeof TIPO_PEDIDO_CAMION
  | typeof TIPO_PEDIDO_CAMION_SAN_ROQUE;

export const TIPO_PEDIDO_OPTIONS: Array<{ label: string; value: TipoPedido }> = [
  { label: "Contenedor",             value: TIPO_PEDIDO_CONTENEDOR },
  { label: "Contenedor · San Roque", value: TIPO_PEDIDO_CONTENEDOR_SAN_ROQUE },
  { label: "Camión",                 value: TIPO_PEDIDO_CAMION },
  { label: "Camión · San Roque",     value: TIPO_PEDIDO_CAMION_SAN_ROQUE },
];

export const FLUJO_LABELS: Record<TipoPedido, string> = {
  [TIPO_PEDIDO_CONTENEDOR]:             "Contenedor",
  [TIPO_PEDIDO_CONTENEDOR_SAN_ROQUE]:  "Contenedor · San Roque",
  [TIPO_PEDIDO_CAMION]:                "Camión",
  [TIPO_PEDIDO_CAMION_SAN_ROQUE]:      "Camión · San Roque",
};

export const esAparienciaCamion = (tipo: TipoPedido): boolean =>
  tipo === TIPO_PEDIDO_CAMION || tipo === TIPO_PEDIDO_CAMION_SAN_ROQUE;

export const esAparienciaContenedor = (tipo: TipoPedido): boolean =>
  tipo === TIPO_PEDIDO_CONTENEDOR || tipo === TIPO_PEDIDO_CONTENEDOR_SAN_ROQUE;

export const esOrigenSanRoque = (tipo: TipoPedido): boolean =>
  tipo === TIPO_PEDIDO_CONTENEDOR_SAN_ROQUE || tipo === TIPO_PEDIDO_CAMION_SAN_ROQUE;

export const DOCUMENTOS_ERRORS = {
  NO_CONTAINERS_SELECTED: "Selecciona al menos un contenedor.",
  NO_DOC_TYPES_SELECTED:  "Selecciona al menos un tipo de documento.",
  GENERATE_ERROR:         "Error al generar los documentos. Inténtalo de nuevo.",
  ROLLBACK_ERROR:         "Error al realizar el rollback. Inténtalo de nuevo.",
  LOAD_PENDING_ERROR:     "Error al cargar los contenedores pendientes.",
  LOAD_GENERATED_ERROR:   "Error al cargar el histórico de documentos.",
};

export const DOCUMENTOS_SUCCESS = {
  GENERATED: "Documentos generados correctamente.",
  ROLLBACK:  "Rollback realizado correctamente.",
};

export const DOCUMENTOS_LOADING = {
  LOADING_PENDING:   "Cargando contenedores pendientes...",
  LOADING_GENERATED: "Cargando histórico...",
  GENERATING:        "Generando documentos...",
  ROLLING_BACK:      "Realizando rollback...",
};

export type Idioma = "ES" | "EN" | "FR";

export const IDIOMA_OPTIONS: Array<{ label: string; value: Idioma }> = [
  { label: "Español",  value: "ES" },
  { label: "Inglés",   value: "EN" },
  { label: "Francés",  value: "FR" },
];

export const DEFAULT_IDIOMA: Idioma = "ES";

export const DEFAULT_FILTROS = {
  tipos_documento: [] as string[],
};

// Propiedades de la Company que se muestran en la sección fija (CrmDataHighlight)
// de la empresa del contexto, en los tres tabs. Alineado con Pedidos.
export const COMPANY_HIGHLIGHT_PROPS = [
  "name",
  "cif",
  "tipo_cliente",
  "residennum",
  "phone",
  "credito_concedido",
];
