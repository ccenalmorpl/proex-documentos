import {
  DOC_TYPE_LABELS,
  DOC_TYPE_TO_API,
  OTROS_DOC_LABELS,
  OTROS_DOC_SUBIBLES_DISCRIMINADOS,
  OTROS_DOC_TYPE_OTROS,
  OTROS_DOC_TYPE_WAIVER,
  TIPO_PEDIDO_EXPORTACION,
  isFlujoNacional,
  type Idioma,
  type TipoPedido,
} from "../constants/documentos.constants";

/** Formato de fecha que usa HubSpot DateInput ({ year, month (0-indexed), date }) */
export type BaseDate = { year: number; month: number; date: number };

export interface FiltrosState {
  empresa: string;
  etd_desde: BaseDate | null;
  etd_hasta: BaseDate | null;
  eta_desde: BaseDate | null;
  eta_hasta: BaseDate | null;
  tipos_documento: string[];
}

export interface DocInfo {
  doc_type: string;
  generated: boolean;
  required: boolean;
  group_id?: string | null;
  file_url?: string | null;
}

export interface ContenedorItem {
  id: string;
  name: string;
  nombre_cliente?: string;
  etd?: string;
  eta?: string;
  deal_id?: string | null;
  deal_name?: string | null;
  docs: DocInfo[];
  deal_properties?: {
    certificado_origen_mercancia?: string;
    observaciones?: string;
    preprints_language?: string;
  };
}

export interface GeneratedDoc {
  doc_type: string;
  file_id: string;
  file_url: string;
  group_generation_id: string;
}

export interface EmpresaItem {
  id: string;
  name: string;
}

export interface PedidoResumen {
  numero_de_pedido: string;
  numero_contenedores_pedido: number;
  nombre_cotizacion?: string | null;
}

export interface BLArchivo {
  file_id: string;
  name: string;
  url: string | null;
  tipo: "borrador" | "final" | "desconocido";
}

export interface CertificadoArchivo {
  file_id: string;
  name: string;
  url: string | null;
  tipo: "borrador" | "validado" | "sellado" | "desconocido";
}

export type OtroDocTipoDiscriminado =
  | "dua"
  | "arc"
  | "eur1"
  | "anexo_i"
  | "inspeccion"
  | "waiver_borrador"
  | "waiver_final";

export type OtroDocTipo = OtroDocTipoDiscriminado | "desconocido";

export interface OtroDocArchivo {
  file_id: string;
  name: string;
  url: string | null;
  tipo: OtroDocTipo;
}

export interface ArchivoSimple {
  file_id: string;
  name: string;
  url: string | null;
}

export interface DealFile {
  file_id: string | null;
  name: string | null;
  url: string | null;
}

export interface SelectOption {
  label: string;
  value: string;
}

export interface PedidoDetalleInfo {
  etd: string | null;
  eta: string | null;
  consignee: string | null;
  notify: string | null;
  puerto_destino: string | null;
  puerto_salida: string | null;
  descripcion_mercancia: string | null;
  observaciones: string | null;
  fecha_de_entrega: string | null;
  lugar_carga: string | null;
  localidad_destino: string | null;
  direccion_de_entrega: string | null;
  datos_del_chofer: string | null;
  comentarios_logistica: string | null;
  bl_validado_logistica: boolean;
  bl_validado_administracion: boolean;
  bl_enviado_cliente: boolean;
  tipo_de_bl: string | null;
  bl_archivos: BLArchivo[];
  certificado_origen_validado: boolean;
  certificado_sanitario_validado: boolean;
  origen_archivos: CertificadoArchivo[];
  sanitario_archivos: CertificadoArchivo[];
  factura_pedido: DealFile | null;
  packing_list_pedido: DealFile | null;
  carta_porte_pedido: DealFile | null;
  fecha_de_facturacion_pedido: string | null;
  fecha_de_vencimiento_factura: string | null;
  numero_de_factura: string | null;
}

export interface PedidoDetalleEmpresa {
  id: string;
  name: string | null;
  tipo_cliente: string | null;
}

export interface PedidoDetalleContenedor {
  id: string;
  nombre: string | null;
  numero_contenedor: string | null;
  numero_precinto: string | null;
  peso_bruto: string | null;
  peso_neto: string | null;
  tara: string | null;
  vgm: string | null;
  etd: string | null;
  eta: string | null;
  tipo_contenedor: string | null;
  total_cajas: string | null;
  descripcion_mercancia_agregada: string | null;
  documentos_a_generar: string[];
  importe_pendiente_cobro: string | null;
  price: string | null;
  documentos_archivos: OtroDocArchivo[];
  otros_documentos: ArchivoSimple[];
  fotos_de_carga_archivos: ArchivoSimple[];
  enviar_por_mensajeria: boolean;
  permitir_enviar_documentacion: boolean;
  documentacion_recibida: boolean;
  mercancia_retirada: boolean;
  waiver_validado: boolean;
  fecha_llegada_contenedor: string | null;
  fecha_retirada_mercancia: string | null;
}

export interface PedidoDetalle {
  numero_de_pedido: string;
  empresa: PedidoDetalleEmpresa;
  info: PedidoDetalleInfo;
  tipo_flujo: string | null;
  carga_por_palets: boolean | null;
  fotos_de_carga: boolean;
  contenedores: PedidoDetalleContenedor[];
  select_options?: Record<string, SelectOption[]>;
}

export interface FileSlot {
  filename: string | null;
}

export interface PedidoInfo {
  etd: string | null;
  eta: string | null;
  consignee: string;
  notify: string;
  numero_contenedores: number;
  total_cajas_pedido: number | null;
  puerto_destino: string;
  puerto_salida: string;
  descripcion_mercancia: string;
  fecha_de_entrega: string | null;
  lugar_carga: string;
  localidad_destino: string;
  direccion_de_entrega: string;
  datos_del_chofer: string;
  comentarios_logistica: string;
}

export interface ContenedorGestionItem {
  id: string;
  nombre: string;
  numero: string;
  precinto: string;
  peso_bruto: string;
  peso_neto: string;
  tara: string;
  vgm: string;
  descripcion_mercancia: string;
}

export interface PedidoMock {
  id: string;
  numero: string;
  companyId: string;
  empresa: string;
  tipo_pedido: TipoPedido;
  carga_por_palets: boolean;
  fotos_de_carga: boolean;
  contenedores: ContenedorGestionItem[];
  contenedoresDetalle: PedidoDetalleContenedor[];
  info: PedidoInfo;
  pedidoInfo: PedidoDetalleInfo;
  documentos_a_generar: string[];
  estado_cobro: "pendiente" | "cobrado";
  importe_pendiente?: number;
  estado_bl: EstadoBL;
  estado_origen: EstadoCertificado;
  estado_sanitario: EstadoCertificado;
  select_options: Record<string, SelectOption[]>;
}

export const DEFAULT_TIPO_PEDIDO: TipoPedido = TIPO_PEDIDO_EXPORTACION;

export interface EstadoCertificado {
  borrador: CertificadoArchivo | null;
  validadoCliente: boolean;
  validado: CertificadoArchivo | null;
  sellado: CertificadoArchivo | null;
}

export interface EstadoBL {
  borrador: BLArchivo | null;
  validadoLogistica: boolean;
  validadoAdministracion: boolean;
  enviadoCliente: boolean;
  tipo: string | null;
  final: BLArchivo | null;
}

export interface EstadoEntrega {
  enviarPorMensajeria: boolean;
  permitirEnviar: boolean;
  albaranMensajeria: FileSlot;
  documentacionRecibida: boolean;
  fechaLlegadaContenedor: BaseDate | null;
  mercanciaRetirada: boolean;
  fechaRetirada: BaseDate | null;
}

export interface EstadoOtrosDocs {
  dua:            OtroDocArchivo | null;
  arc:            OtroDocArchivo | null;
  eur1:           OtroDocArchivo | null;
  anexo_i:        OtroDocArchivo | null;
  inspeccion:     OtroDocArchivo | null;
  waiverBorrador: OtroDocArchivo | null;
  waiverValidado: boolean;
  waiverFinal:    OtroDocArchivo | null;
  otros:          ArchivoSimple[];
  fotos:          ArchivoSimple[];
}

export interface EstadoContenedor {
  otrosDocs: EstadoOtrosDocs;
  entrega: EstadoEntrega;
}

export const emptyFileSlot = (): FileSlot => ({ filename: null });

export const initialEstadoOtrosDocs = (): EstadoOtrosDocs => ({
  dua:            null,
  arc:            null,
  eur1:           null,
  anexo_i:        null,
  inspeccion:     null,
  waiverBorrador: null,
  waiverValidado: false,
  waiverFinal:    null,
  otros:          [],
  fotos:          [],
});

export const buildEstadoOtrosDocs = (
  contenedor: Partial<PedidoDetalleContenedor>,
): EstadoOtrosDocs => {
  const docs = contenedor.documentos_archivos ?? [];
  const findTipo = (t: OtroDocTipoDiscriminado) =>
    docs.find((a) => a.tipo === t) ?? null;
  return {
    dua:            findTipo("dua"),
    arc:            findTipo("arc"),
    eur1:           findTipo("eur1"),
    anexo_i:        findTipo("anexo_i"),
    inspeccion:     findTipo("inspeccion"),
    waiverBorrador: findTipo("waiver_borrador"),
    waiverValidado: contenedor.waiver_validado ?? false,
    waiverFinal:    findTipo("waiver_final"),
    otros:          contenedor.otros_documentos ?? [],
    fotos:          contenedor.fotos_de_carga_archivos ?? [],
  };
};

export const initialCertificado = (): EstadoCertificado => ({
  borrador:        null,
  validadoCliente: false,
  validado:        null,
  sellado:         null,
});

export const buildEstadoOrigen = (info: Partial<PedidoDetalleInfo>): EstadoCertificado => {
  const archivos = info.origen_archivos ?? [];
  return {
    borrador:        archivos.find((a) => a.tipo === "borrador") ?? null,
    validadoCliente: info.certificado_origen_validado ?? false,
    validado:        archivos.find((a) => a.tipo === "validado") ?? null,
    sellado:         archivos.find((a) => a.tipo === "sellado") ?? null,
  };
};

export const buildEstadoSanitario = (info: Partial<PedidoDetalleInfo>): EstadoCertificado => {
  const archivos = info.sanitario_archivos ?? [];
  return {
    borrador:        archivos.find((a) => a.tipo === "borrador") ?? null,
    validadoCliente: info.certificado_sanitario_validado ?? false,
    validado:        archivos.find((a) => a.tipo === "validado") ?? null,
    sellado:         archivos.find((a) => a.tipo === "sellado") ?? null,
  };
};

export const initialBL = (): EstadoBL => ({
  borrador:               null,
  validadoLogistica:      false,
  validadoAdministracion: false,
  enviadoCliente:         false,
  tipo:                   null,
  final:                  null,
});

export const buildEstadoBL = (info: Partial<PedidoDetalleInfo>): EstadoBL => {
  const archivos = info.bl_archivos ?? [];
  return {
    borrador:               archivos.find((a) => a.tipo === "borrador") ?? null,
    validadoLogistica:      info.bl_validado_logistica ?? false,
    validadoAdministracion: info.bl_validado_administracion ?? false,
    enviadoCliente:         info.bl_enviado_cliente ?? false,
    tipo:                   info.tipo_de_bl ?? null,
    final:                  archivos.find((a) => a.tipo === "final") ?? null,
  };
};

export const initialEntrega = (): EstadoEntrega => ({
  enviarPorMensajeria:    false,
  permitirEnviar:         false,
  albaranMensajeria:      emptyFileSlot(),
  documentacionRecibida:  false,
  fechaLlegadaContenedor: null,
  mercanciaRetirada:      false,
  fechaRetirada:          null,
});

export const isoToBaseDate = (iso: string | null | undefined): BaseDate | null => {
  if (!iso) return null;
  const [y, m, d] = iso.split("-").map(Number);
  if (!y || !m || !d) return null;
  return { year: y, month: m - 1, date: d };
};

export const baseDateToIso = (d: BaseDate | null | undefined): string | null => {
  if (!d) return null;
  const m = String(d.month + 1).padStart(2, "0");
  const day = String(d.date).padStart(2, "0");
  return `${d.year}-${m}-${day}`;
};

export const buildEstadoEntrega = (
  c: Partial<PedidoDetalleContenedor>,
): EstadoEntrega => ({
  enviarPorMensajeria:    c.enviar_por_mensajeria ?? false,
  permitirEnviar:         c.permitir_enviar_documentacion ?? false,
  albaranMensajeria:      emptyFileSlot(),
  documentacionRecibida:  c.documentacion_recibida ?? false,
  fechaLlegadaContenedor: isoToBaseDate(c.fecha_llegada_contenedor),
  mercanciaRetirada:      c.mercancia_retirada ?? false,
  fechaRetirada:          isoToBaseDate(c.fecha_retirada_mercancia),
});

export const initialEstadoContenedor = (): EstadoContenedor => ({
  otrosDocs: initialEstadoOtrosDocs(),
  entrega:   initialEntrega(),
});

// month es 0-indexed en BaseDate
const baseDateToISO = (d: BaseDate | null): string | null => {
  if (!d) return null;
  const m = String(d.month + 1).padStart(2, "0");
  const day = String(d.date).padStart(2, "0");
  return `${d.year}-${m}-${day}`;
};

export const formatDateES = (value: string | null | undefined): string => {
  if (!value) return "";
  const iso = value.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (iso) return `${iso[3]}/${iso[2]}/${iso[1]}`;
  const dmy = value.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (dmy) return value;
  const ms = /^-?\d+$/.test(value) ? Number(value) : NaN;
  if (Number.isFinite(ms)) {
    const d = new Date(ms);
    if (!isNaN(d.getTime())) {
      const dd = String(d.getUTCDate()).padStart(2, "0");
      const mm = String(d.getUTCMonth() + 1).padStart(2, "0");
      return `${dd}/${mm}/${d.getUTCFullYear()}`;
    }
  }
  return "";
};

const parseHubspotDate = (value: string | null | undefined): Date | null => {
  if (!value) return null;
  const iso = value.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (iso) return new Date(Date.UTC(+iso[1], +iso[2] - 1, +iso[3]));
  const dmy = value.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (dmy) return new Date(Date.UTC(+dmy[3], +dmy[2] - 1, +dmy[1]));
  const ms = /^-?\d+$/.test(value) ? Number(value) : NaN;
  if (Number.isFinite(ms)) {
    const d = new Date(ms);
    return isNaN(d.getTime()) ? null : d;
  }
  return null;
};

const MS_PER_DAY = 86_400_000;

const todayUTC = (): Date => {
  const now = new Date();
  return new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
};

export const daysSince = (value: string | null | undefined): number | null => {
  const d = parseHubspotDate(value);
  if (!d) return null;
  return Math.floor((todayUTC().getTime() - d.getTime()) / MS_PER_DAY);
};

export const daysUntil = (value: string | null | undefined): number | null => {
  const d = parseHubspotDate(value);
  if (!d) return null;
  return Math.ceil((d.getTime() - todayUTC().getTime()) / MS_PER_DAY);
};

export const buildPendingPayload = (dealId: string, filtros: FiltrosState) => ({
  deal_id: String(dealId),
  filtros: {
    empresa:         filtros.empresa || null,
    etd_desde:       baseDateToISO(filtros.etd_desde),
    etd_hasta:       baseDateToISO(filtros.etd_hasta),
    eta_desde:       baseDateToISO(filtros.eta_desde),
    eta_hasta:       baseDateToISO(filtros.eta_hasta),
    tipos_documento: filtros.tipos_documento.length ? filtros.tipos_documento : null,
  },
});

export const buildGeneratePayload = (
  dealId: string,
  containerIds: string[],
  docTypes: string[],
  descripcionMercancia?: string,
  observaciones?: string,
  idioma: Idioma = "ES"
) => ({
  deal_id:       String(dealId),
  container_ids: containerIds,
  doc_types:     docTypes,
  idioma,
  ...(descripcionMercancia ? { descripcion_mercancia: descripcionMercancia } : {}),
  ...(observaciones ? { observaciones } : {}),
});

export const buildGeneratedPayload = (dealId: string, filtros: FiltrosState) =>
  buildPendingPayload(dealId, filtros);

export const buildRollbackPayload = (
  contenedorNombre: string,
  docType: string,
  groupId?: string | null
) => ({
  contenedor_nombre: contenedorNombre,
  doc_type:          DOC_TYPE_TO_API[docType] ?? docType,
  group_id:          groupId ?? null,
});

export const getDocTypeLabel = (docType: string): string =>
  DOC_TYPE_LABELS[docType] ?? docType;

export const getGeneratedDocs = (contenedor: ContenedorItem): DocInfo[] =>
  contenedor.docs.filter((d) => d.generated);

export const getPendingDocs = (contenedor: ContenedorItem): DocInfo[] =>
  contenedor.docs.filter((d) => !d.generated);

export const formatDate = (isoDate?: string): string => {
  if (!isoDate) return "—";
  try {
    const d = new Date(isoDate);
    return d.toLocaleDateString("es-ES");
  } catch {
    return isoDate;
  }
};

export const ESTADO_COBRO_TOLERANCIA = 0.001;

export const parseFloatOrZero = (raw: string | number | null | undefined): number => {
  if (raw === null || raw === undefined) return 0;
  if (typeof raw === "number") return Number.isFinite(raw) ? raw : 0;
  const n = parseFloat(raw);
  return Number.isFinite(n) ? n : 0;
};

export const formatImporte = (raw: string | number | null | undefined): string => {
  if (raw === null || raw === undefined || raw === "") return "—";
  const n = typeof raw === "number" ? raw : parseFloat(raw);
  if (!Number.isFinite(n)) return "—";
  try {
    return new Intl.NumberFormat("es-ES", {
      style: "currency",
      currency: "EUR",
    }).format(n);
  } catch {
    return `${n} €`;
  }
};

export interface PorcentajeCobro {
  precio: number;
  pendiente: number;
  porcentajePendiente: number;
  cobradoCompleto: boolean;
  precioDisponible: boolean;
}

export const calcularPorcentajePendiente = (
  importePendiente: string | number | null | undefined,
  price: string | number | null | undefined,
): PorcentajeCobro => {
  const precio = parseFloatOrZero(price);
  const pendiente = parseFloatOrZero(importePendiente);
  const precioDisponible = precio > ESTADO_COBRO_TOLERANCIA;

  if (!precioDisponible) {
    return {
      precio,
      pendiente,
      porcentajePendiente: 0,
      cobradoCompleto: false,
      precioDisponible: false,
    };
  }

  const pct = Math.max(0, Math.min(100, (pendiente / precio) * 100));
  const cobradoCompleto = pendiente <= ESTADO_COBRO_TOLERANCIA;

  return {
    precio,
    pendiente,
    porcentajePendiente: pct,
    cobradoCompleto,
    precioDisponible: true,
  };
};

export const formatPorcentaje = (pct: number): string => {
  const v = Number.isFinite(pct) ? pct : 0;
  return `${v.toLocaleString("es-ES", { maximumFractionDigits: 1 })} %`;
};

export interface DocStatus {
  key:      string;
  label:    string;
  generado: boolean;
  url:      string | null;
  filename: string | null;
}

const labelConConteo = (base: string, n: number): string =>
  n > 0 ? `${base} (${n})` : base;

export const buildDocumentosContenedorResumen = (params: {
  contenedor:    PedidoDetalleContenedor;
  pedidoInfo:    PedidoDetalleInfo;
  tipoPedido:    TipoPedido;
  fotosDeCarga:  boolean;
}): DocStatus[] => {
  const { contenedor, pedidoInfo, tipoPedido, fotosDeCarga } = params;
  const result: DocStatus[] = [];

  if (!isFlujoNacional(tipoPedido)) {
    const blFinal = pedidoInfo.bl_archivos.find((a) => a.tipo === "final") ?? null;
    result.push({
      key:      "bl_final",
      label:    "BL final",
      generado: !!blFinal,
      url:      blFinal?.url ?? null,
      filename: blFinal?.name ?? null,
    });

    const origenSellado = pedidoInfo.origen_archivos.find((a) => a.tipo === "sellado") ?? null;
    result.push({
      key:      "origen_sellado",
      label:    "Certificado de Origen",
      generado: !!origenSellado,
      url:      origenSellado?.url ?? null,
      filename: origenSellado?.name ?? null,
    });

    const sanitarioSellado = pedidoInfo.sanitario_archivos.find((a) => a.tipo === "sellado") ?? null;
    result.push({
      key:      "sanitario_sellado",
      label:    "Certificado Sanitario",
      generado: !!sanitarioSellado,
      url:      sanitarioSellado?.url ?? null,
      filename: sanitarioSellado?.name ?? null,
    });
  }

  result.push({
    key:      "factura",
    label:    "Factura",
    generado: !!pedidoInfo.factura_pedido?.url,
    url:      pedidoInfo.factura_pedido?.url ?? null,
    filename: pedidoInfo.factura_pedido?.name ?? null,
  });

  result.push({
    key:      "packing_list",
    label:    "Packing list",
    generado: !!pedidoInfo.packing_list_pedido?.url,
    url:      pedidoInfo.packing_list_pedido?.url ?? null,
    filename: pedidoInfo.packing_list_pedido?.name ?? null,
  });

  if (pedidoInfo.carta_porte_pedido?.url) {
    result.push({
      key:      "carta_porte",
      label:    "Carta de porte",
      generado: true,
      url:      pedidoInfo.carta_porte_pedido.url,
      filename: pedidoInfo.carta_porte_pedido.name ?? null,
    });
  }

  const docsAGenerar = contenedor.documentos_a_generar ?? [];
  for (const tipo of OTROS_DOC_SUBIBLES_DISCRIMINADOS) {
    if (!docsAGenerar.includes(tipo)) continue;
    const archivo =
      contenedor.documentos_archivos.find((a) => a.tipo === tipo) ?? null;
    result.push({
      key:      tipo,
      label:    OTROS_DOC_LABELS[tipo] ?? tipo,
      generado: !!archivo,
      url:      archivo?.url ?? null,
      filename: archivo?.name ?? null,
    });
  }

  if (docsAGenerar.includes(OTROS_DOC_TYPE_WAIVER)) {
    const waiverBorrador = contenedor.documentos_archivos.find((a) => a.tipo === "waiver_borrador") ?? null;
    const waiverFinal    = contenedor.documentos_archivos.find((a) => a.tipo === "waiver_final") ?? null;
    const completo = !!waiverBorrador && contenedor.waiver_validado === true && !!waiverFinal;
    result.push({
      key:      OTROS_DOC_TYPE_WAIVER,
      label:    OTROS_DOC_LABELS[OTROS_DOC_TYPE_WAIVER] ?? OTROS_DOC_TYPE_WAIVER,
      generado: completo,
      url:      waiverFinal?.url ?? waiverBorrador?.url ?? null,
      filename: waiverFinal?.name ?? waiverBorrador?.name ?? null,
    });
  }

  if (docsAGenerar.includes(OTROS_DOC_TYPE_OTROS)) {
    const n = contenedor.otros_documentos.length;
    result.push({
      key:      "otros",
      label:    labelConConteo(OTROS_DOC_LABELS[OTROS_DOC_TYPE_OTROS], n),
      generado: n > 0,
      url:      contenedor.otros_documentos[0]?.url ?? null,
      filename: n > 0 ? `${n} archivo${n === 1 ? "" : "s"}` : null,
    });
  }

  if (fotosDeCarga) {
    const n = contenedor.fotos_de_carga_archivos.length;
    result.push({
      key:      "fotos_carga",
      label:    labelConConteo("Fotos de carga", n),
      generado: n > 0,
      url:      contenedor.fotos_de_carga_archivos[0]?.url ?? null,
      filename: n > 0 ? `${n} foto${n === 1 ? "" : "s"}` : null,
    });
  }

  return result;
};
