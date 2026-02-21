/**
 * Common constants used across the application
 */

// API and timing constants
export const API_TIMEOUT_MS = 30000;
export const DEBOUNCE_DELAY_MS = 500;
export const INITIAL_RENDER_DELAY_MS = 300;

// Error messages
export const ERROR_MESSAGES = {
  NO_DEAL_ID: "No se pudo obtener el ID del Deal desde el contexto.",
  NETWORK_ERROR: "Error de conexión. Por favor, verifica tu conexión a internet.",
  UNKNOWN_ERROR: "Error desconocido. Por favor, intenta de nuevo.",
  LOAD_ERROR: "Error al cargar los datos",
  SAVE_ERROR: "Error al guardar los datos",
};

// Success messages
export const SUCCESS_MESSAGES = {
  DATA_SAVED: "Datos guardados correctamente",
  CONTAINER_ADDED: "Contenedor agregado correctamente",
  PRODUCT_ADDED: "Producto agregado correctamente",
};

// Loading messages
export const LOADING_MESSAGES = {
  LOADING_DATA: "Cargando datos...",
  LOADING_DOCUMENTACION: "Cargando documentación...",
  SAVING: "Guardando...",
};
