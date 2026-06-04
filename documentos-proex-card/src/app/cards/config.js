export const API_CONFIG = {
  baseURL: 'https://2tqk2gn9n3.execute-api.eu-south-2.amazonaws.com',

  endpoints: {
    root: '/',
    health: '/health',
    documentosPending:    '/api/v1/documentos/pending',
    documentosGenerate:   '/api/v1/documentos/generate',
    documentosGenerated:  '/api/v1/documentos/generated',
    documentosRollback:   '/api/v1/documentos/rollback',
    documentosDealContext: (dealId) => `/api/v1/documentos/deal-context/${encodeURIComponent(dealId)}`,
    empresasSearch:      '/api/v1/empresas',
    pedidosByCompany:    '/api/v1/pedidos',
    pedidoDetalle:       (numero) => `/api/v1/pedidos/${encodeURIComponent(numero)}`,
  },

  timeout: 30000
};
