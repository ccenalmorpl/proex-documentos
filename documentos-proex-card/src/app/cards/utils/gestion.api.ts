import { API_CONFIG } from "../config";
import { fetchFromAPI } from "./api.utils";
import type {
  PedidoDetalle,
  PedidoResumen,
  SelectOption,
} from "./documentos.utils";

interface PedidosResponse {
  success: boolean;
  error?: string | null;
  pedidosCompany?: PedidoResumen[];
}

interface PedidoDetalleResponse {
  success: boolean;
  error?: string | null;
  pedido?: PedidoDetalle;
  select_options?: Record<string, SelectOption[]>;
  selectOptions?: Record<string, SelectOption[]>;
}

export async function fetchPedidosByEmpresa(companyId: string): Promise<PedidoResumen[]> {
  const endpoint = `${API_CONFIG.endpoints.pedidosByCompany}?company_id=${encodeURIComponent(companyId)}`;
  const data = (await fetchFromAPI(endpoint)) as PedidosResponse;
  return data.pedidosCompany ?? [];
}

export async function fetchPedidoDetalle(
  numeroDePedido: string,
  companyId: string,
): Promise<PedidoDetalle> {
  const endpoint = `${API_CONFIG.endpoints.pedidoDetalle(numeroDePedido)}?company_id=${encodeURIComponent(companyId)}`;
  const data = (await fetchFromAPI(endpoint)) as PedidoDetalleResponse;
  if (!data.pedido) {
    throw new Error("La respuesta del backend no incluye 'pedido'.");
  }
  const selectOptions = data.select_options ?? data.selectOptions ?? {};
  return { ...data.pedido, select_options: selectOptions };
}

export interface UpdatePedidoBLPayload {
  bl_validado_logistica?: boolean;
  bl_validado_administracion?: boolean;
  bl_enviado_cliente?: boolean;
  tipo_de_bl?: string | null;
  cambios_en_bl?: string | null;
}

// El BL aplica solo a los contenedores seleccionados (su Negocio Documento +
// Negocio Pedido). Sin contenedorIds → todos los del pedido.
export async function updatePedidoBL(
  numeroDePedido: string,
  companyId: string,
  payload: UpdatePedidoBLPayload,
  contenedorIds?: string[],
): Promise<{ success: boolean; error?: string | null }> {
  const endpoint = `${API_CONFIG.endpoints.pedidoDetalle(numeroDePedido)}?company_id=${encodeURIComponent(companyId)}`;
  const body =
    contenedorIds && contenedorIds.length > 0
      ? { ...payload, contenedor_ids: contenedorIds }
      : payload;
  return (await fetchFromAPI(endpoint, {
    method: "PATCH",
    body,
  })) as { success: boolean; error?: string | null };
}

// Cambio 2 — el booking es INDIVIDUAL por contenedor: se escribe solo en el
// pedido-deal de ese contenedor (un pedido puede tener bookings distintos).
export async function updateContenedorBooking(
  numeroDePedido: string,
  companyId: string,
  contenedorId: string,
  numeroBooking: string,
): Promise<{ success: boolean; error?: string | null }> {
  const endpoint =
    `${API_CONFIG.endpoints.pedidoDetalle(numeroDePedido)}` +
    `/contenedores/${encodeURIComponent(contenedorId)}/booking` +
    `?company_id=${encodeURIComponent(companyId)}`;
  return (await fetchFromAPI(endpoint, {
    method: "PATCH",
    body: { numero_de_booking: numeroBooking },
  })) as { success: boolean; error?: string | null };
}

export interface UpdateContenedorFechasPayload {
  etd?: string | null;
  eta?: string | null;
}

// ETD/ETA por contenedor: el backend escribe en el pedido-deal y el documento-deal
// del contenedor (Documento manda en la lectura). Fecha ISO "YYYY-MM-DD" o null.
export async function updateContenedorFechas(
  numeroDePedido: string,
  companyId: string,
  contenedorId: string,
  payload: UpdateContenedorFechasPayload,
): Promise<{ success: boolean; error?: string | null }> {
  const endpoint =
    `${API_CONFIG.endpoints.pedidoDetalle(numeroDePedido)}` +
    `/contenedores/${encodeURIComponent(contenedorId)}/fechas` +
    `?company_id=${encodeURIComponent(companyId)}`;
  return (await fetchFromAPI(endpoint, {
    method: "PATCH",
    body: payload,
  })) as { success: boolean; error?: string | null };
}

export interface UpdateContenedoresCertificadosPayload {
  certificado_origen_validado?: boolean;
  certificado_sanitario_validado?: boolean;
  certificado_origen_enviar_a_firmar?: boolean;
  certificado_sanitario_enviar_a_firmar?: boolean;
}

export async function updateContenedoresCertificados(
  numeroDePedido: string,
  companyId: string,
  payload: UpdateContenedoresCertificadosPayload,
): Promise<{ success: boolean; error?: string | null }> {
  const endpoint =
    `${API_CONFIG.endpoints.pedidoDetalle(numeroDePedido)}` +
    `/contenedores/properties?company_id=${encodeURIComponent(companyId)}`;
  return (await fetchFromAPI(endpoint, {
    method: "PATCH",
    body: payload,
  })) as { success: boolean; error?: string | null };
}

export interface UpdateContenedorEntregaPayload {
  enviar_por_mensajeria?: boolean;
  permitir_enviar_documentacion?: boolean;
  documentacion_recibida?: boolean;
  mercancia_retirada?: boolean;
  waiver_validado?: boolean;
  fecha_llegada_contenedor?: string | null;
  fecha_retirada_mercancia?: string | null;
  datos_envio_mensajeria?: string | null;
}

export async function updateContenedorEntrega(
  numeroDePedido: string,
  companyId: string,
  contenedorId: string,
  payload: UpdateContenedorEntregaPayload,
): Promise<{ success: boolean; error?: string | null }> {
  const endpoint =
    `${API_CONFIG.endpoints.pedidoDetalle(numeroDePedido)}` +
    `/contenedores/${encodeURIComponent(contenedorId)}/entrega` +
    `?company_id=${encodeURIComponent(companyId)}`;
  return (await fetchFromAPI(endpoint, {
    method: "PATCH",
    body: payload,
  })) as { success: boolean; error?: string | null };
}

export interface UpdateContenedorDatosPayload {
  numero_contenedor?: string | null;
  numero_precinto?: string | null;
  peso_bruto?: string | null;
  peso_neto?: string | null;
  tara?: string | null;
}

export async function updateContenedorDatos(
  numeroDePedido: string,
  companyId: string,
  contenedorId: string,
  payload: UpdateContenedorDatosPayload,
): Promise<{ success: boolean; error?: string | null }> {
  const endpoint =
    `${API_CONFIG.endpoints.pedidoDetalle(numeroDePedido)}` +
    `/contenedores/${encodeURIComponent(contenedorId)}/datos` +
    `?company_id=${encodeURIComponent(companyId)}`;
  return (await fetchFromAPI(endpoint, {
    method: "PATCH",
    body: payload,
  })) as { success: boolean; error?: string | null };
}

export function buildUploadModalUri(
  numeroDePedido: string,
  companyId: string,
  tipoDocumento: string,
  contenedorId?: string,
  contenedorIds?: string[],
): string {
  // Cambio 2 — docs por embarque: `contenedor_ids` (subconjunto) tiene
  // prioridad; `contenedor_id` se mantiene para subida a un único contenedor.
  let destinoQ = "";
  if (contenedorIds && contenedorIds.length > 0) {
    destinoQ = `&contenedor_ids=${encodeURIComponent(contenedorIds.join(","))}`;
  } else if (contenedorId) {
    destinoQ = `&contenedor_id=${encodeURIComponent(contenedorId)}`;
  }
  // El iframe (GET modal + POST upload) no pasa por hubspot.fetch y no puede llevar
  // el header Authorization; su endpoint se monta sin verify_card_secret (igual que Pedidos).
  return (
    `${API_CONFIG.baseURL}${API_CONFIG.endpoints.pedidoDetalle(numeroDePedido)}` +
    `/files/upload-modal?company_id=${encodeURIComponent(companyId)}` +
    `&tipo_documento=${encodeURIComponent(tipoDocumento)}${destinoQ}`
  );
}

export async function deletePedidoFile(
  numeroDePedido: string,
  companyId: string,
  fileId: string,
  tipoDocumento: string,
  contenedorId?: string,
  contenedorIds?: string[],
): Promise<{ success: boolean; error?: string | null }> {
  // Cambio 2 — borrado simétrico a la subida por embarque: si el doc se subió a un
  // subconjunto, se quita de esos mismos contenedores. `contenedor_ids` tiene
  // prioridad; `contenedor_id` (single) se mantiene por compatibilidad.
  let destinoQ = "";
  if (contenedorIds && contenedorIds.length > 0) {
    destinoQ = `&contenedor_ids=${encodeURIComponent(contenedorIds.join(","))}`;
  } else if (contenedorId) {
    destinoQ = `&contenedor_id=${encodeURIComponent(contenedorId)}`;
  }
  const endpoint =
    `${API_CONFIG.endpoints.pedidoDetalle(numeroDePedido)}` +
    `/files/${encodeURIComponent(fileId)}` +
    `?company_id=${encodeURIComponent(companyId)}` +
    `&tipo_documento=${encodeURIComponent(tipoDocumento)}${destinoQ}`;
  return (await fetchFromAPI(endpoint, { method: "DELETE" })) as {
    success: boolean;
    error?: string | null;
  };
}
