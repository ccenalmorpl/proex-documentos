/**
 * Constantes del módulo Documentos PROEX
 */

// ── Tipos de documento ──────────────────────────────────────────────────────
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
  [DOC_TYPE_ORIGEN_BORRADOR]: "Origen Borrador",
  [DOC_TYPE_ORIGEN_FINAL]:    "Origen Final",
  [DOC_TYPE_SANITARIO]:       "Sanitario",
};

// ── Tabs ────────────────────────────────────────────────────────────────────
export const TAB_PENDIENTES = "pendientes";
export const TAB_HISTORICO  = "historico";

// ── Mensajes específicos de Documentos ─────────────────────────────────────
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

// ── Valores por defecto de los filtros ─────────────────────────────────────
export const DEFAULT_FILTROS = {
  empresa:                "",
  fecha_carga_desde:      "",
  fecha_carga_hasta:      "",
  fecha_cotizacion_desde: "",
  fecha_cotizacion_hasta: "",
  tipos_documento:        [] as string[],
};
