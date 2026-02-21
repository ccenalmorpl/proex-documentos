/**
 * Configuración del microservicio backend Proex
 *
 * IMPORTANTE: Para cambiar entre entornos (desarrollo/producción),
 * solo modifica la variable baseURL
 *
 * Ejemplo de URLs por entorno:
 * - Desarrollo local: 'http://localhost:8000' o ngrok
 * - Producción: 'https://2tqk2gn9n3.execute-api.eu-south-2.amazonaws.com'
 */

export const API_CONFIG = {
  // URL del microservicio Lambda (PRODUCCIÓN)
  baseURL: 'https://2tqk2gn9n3.execute-api.eu-south-2.amazonaws.com',

  // Endpoints disponibles (para referencia)
  endpoints: {
    root: '/',
    health: '/health',
    documentosPending:   '/api/v1/documentos/pending',
    documentosGenerate:  '/api/v1/documentos/generate',
    documentosGenerated: '/api/v1/documentos/generated',
    documentosRollback:  '/api/v1/documentos/rollback',
  },

  // Timeout por defecto para las peticiones (30 segundos)
  timeout: 30000
};
