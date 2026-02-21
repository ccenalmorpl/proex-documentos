/**
 * Utilidades específicas del módulo Documentos
 */

import { DOC_TYPE_LABELS } from "../constants/documentos.constants";

// ── Tipos locales ───────────────────────────────────────────────────────────

export interface FiltrosState {
  empresa: string;
  fecha_carga_desde: string;
  fecha_carga_hasta: string;
  fecha_cotizacion_desde: string;
  fecha_cotizacion_hasta: string;
  tipos_documento: string[];
}

export interface DocInfo {
  doc_type: string;
  file_id?: string;
  file_url?: string;
  generated_at?: string;
  group_generation_id?: string;
}

export interface ContenedorItem {
  id: string;
  name: string;
  nombre_cliente?: string;
  fecha_carga?: string;
  fecha_cotizacion?: string;
  docs: DocInfo[];
}

// ── Builders de payloads para la API ────────────────────────────────────────

export const buildPendingPayload = (dealId: string, filtros: FiltrosState) => ({
  deal_id: dealId,
  filtros: {
    empresa:                filtros.empresa || null,
    fecha_carga_desde:      filtros.fecha_carga_desde || null,
    fecha_carga_hasta:      filtros.fecha_carga_hasta || null,
    fecha_cotizacion_desde: filtros.fecha_cotizacion_desde || null,
    fecha_cotizacion_hasta: filtros.fecha_cotizacion_hasta || null,
    tipos_documento:        filtros.tipos_documento.length ? filtros.tipos_documento : null,
  },
});

export const buildGeneratePayload = (
  dealId: string,
  containerIds: string[],
  docTypes: string[]
) => ({
  deal_id:       dealId,
  container_ids: containerIds,
  doc_types:     docTypes,
});

export const buildGeneratedPayload = (dealId: string, filtros: FiltrosState) =>
  buildPendingPayload(dealId, filtros);

export const buildRollbackPayload = (
  containerId: string,
  docType: string,
  groupGenerationId?: string
) => ({
  container_id:        containerId,
  doc_type:            docType,
  group_generation_id: groupGenerationId ?? null,
});

// ── Helpers de presentación ─────────────────────────────────────────────────

/**
 * Devuelve el label legible de un tipo de documento.
 */
export const getDocTypeLabel = (docType: string): string =>
  DOC_TYPE_LABELS[docType] ?? docType;

/**
 * Devuelve los DocInfo generados de un contenedor.
 */
export const getGeneratedDocs = (contenedor: ContenedorItem): DocInfo[] =>
  contenedor.docs.filter((d) => !!d.file_url);

/**
 * Devuelve los DocInfo pendientes (sin file_url) de un contenedor.
 */
export const getPendingDocs = (contenedor: ContenedorItem): DocInfo[] =>
  contenedor.docs.filter((d) => !d.file_url);

/**
 * Formatea una fecha ISO como string legible (DD/MM/YYYY).
 */
export const formatDate = (isoDate?: string): string => {
  if (!isoDate) return "—";
  try {
    const d = new Date(isoDate);
    return d.toLocaleDateString("es-ES");
  } catch {
    return isoDate;
  }
};
