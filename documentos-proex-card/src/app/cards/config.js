export const API_CONFIG = {
  baseURL: 'https://2tqk2gn9n3.execute-api.eu-south-2.amazonaws.com',

  // Compartido con el microservicio (PROEX_CARD_SECRET). hubspot.fetch()
  // descarta cualquier header custom salvo Authorization, así que viaja como
  // "Bearer <cardSecret>". Vive en el bundle igual que baseURL: mismo modelo
  // de confianza (ver auditoría de seguridad del traspaso). Reemplazar antes
  // de desplegar.
  cardSecret: '87b2c2c650565dd7b954d18804ed9c38c4c8ce1e4e448eafad71a3d43bbee68a',

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
