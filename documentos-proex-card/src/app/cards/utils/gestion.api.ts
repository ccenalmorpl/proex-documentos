import { API_CONFIG } from "../config";
import { fetchFromAPI } from "./api.utils";
import type {
  EmpresaItem,
  PedidoDetalle,
  PedidoResumen,
  SelectOption,
} from "./documentos.utils";

interface EmpresasResponse {
  success: boolean;
  error?: string | null;
  empresas?: EmpresaItem[];
  total?: number;
}

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

export async function searchEmpresas(q: string): Promise<EmpresaItem[]> {
  const trimmed = q.trim();
  if (!trimmed) return [];
  const endpoint = `${API_CONFIG.endpoints.empresasSearch}?q=${encodeURIComponent(trimmed)}`;
  const data = (await fetchFromAPI(endpoint)) as EmpresasResponse;
  return data.empresas ?? [];
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
}

export async function updatePedidoBL(
  numeroDePedido: string,
  companyId: string,
  payload: UpdatePedidoBLPayload,
): Promise<{ success: boolean; error?: string | null }> {
  const endpoint = `${API_CONFIG.endpoints.pedidoDetalle(numeroDePedido)}?company_id=${encodeURIComponent(companyId)}`;
  return (await fetchFromAPI(endpoint, {
    method: "PATCH",
    body: payload,
  })) as { success: boolean; error?: string | null };
}

export interface UpdateContenedoresCertificadosPayload {
  certificado_origen_validado?: boolean;
  certificado_sanitario_validado?: boolean;
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

export function buildUploadModalUri(
  numeroDePedido: string,
  companyId: string,
  tipoDocumento: string,
  contenedorId?: string,
): string {
  const cidQ = contenedorId ? `&contenedor_id=${encodeURIComponent(contenedorId)}` : "";
  return (
    `${API_CONFIG.baseURL}${API_CONFIG.endpoints.pedidoDetalle(numeroDePedido)}` +
    `/files/upload-modal?company_id=${encodeURIComponent(companyId)}` +
    `&tipo_documento=${encodeURIComponent(tipoDocumento)}${cidQ}`
  );
}

export async function deletePedidoFile(
  numeroDePedido: string,
  companyId: string,
  fileId: string,
  tipoDocumento: string,
  contenedorId?: string,
): Promise<{ success: boolean; error?: string | null }> {
  const cidQ = contenedorId ? `&contenedor_id=${encodeURIComponent(contenedorId)}` : "";
  const endpoint =
    `${API_CONFIG.endpoints.pedidoDetalle(numeroDePedido)}` +
    `/files/${encodeURIComponent(fileId)}` +
    `?company_id=${encodeURIComponent(companyId)}` +
    `&tipo_documento=${encodeURIComponent(tipoDocumento)}${cidQ}`;
  return (await fetchFromAPI(endpoint, { method: "DELETE" })) as {
    success: boolean;
    error?: string | null;
  };
}
