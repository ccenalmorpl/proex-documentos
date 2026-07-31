import {
  DOC_TYPE_LABELS,
  DOC_TYPE_TO_API,
  OTROS_DOC_LABELS,
  OTROS_DOC_SUBIBLES_DISCRIMINADOS,
  OTROS_DOC_TYPE_CARTA_PORTE,
  OTROS_DOC_TYPE_OTROS,
  OTROS_DOC_TYPE_PACKING_LIST,
  OTROS_DOC_TYPE_WAIVER,
  TIPO_PEDIDO_CONTENEDOR,
  esAparienciaContenedor,
  type Idioma,
  type TipoPedido,
} from "../constants/documentos.constants";

/** Formato de fecha que usa HubSpot DateInput ({ year, month (0-indexed), date }) */
export type BaseDate = { year: number; month: number; date: number };

export interface FiltrosState {
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
  created_at?: string | null;
}

export interface CertificadoArchivo {
  file_id: string;
  name: string;
  url: string | null;
  tipo: "borrador" | "validado" | "sellado" | "desconocido";
  created_at?: string | null;
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
  created_at?: string | null;
}

export interface ArchivoSimple {
  file_id: string;
  name: string;
  url: string | null;
  // Fecha de subida (ISO YYYY-MM-DD) derivada del createdAt del fichero en HubSpot.
  created_at?: string | null;
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
  tipo_de_venta: string | null;
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
  certificado_origen_enviar_a_firmar: boolean;
  certificado_sanitario_enviar_a_firmar: boolean;
  origen_archivos: CertificadoArchivo[];
  sanitario_archivos: CertificadoArchivo[];
  factura_pedido: DealFile | null;
  packing_list_pedido: DealFile | null;
  carta_porte_pedido: DealFile | null;
  fecha_de_facturacion_pedido: string | null;
  fecha_de_vencimiento_factura: string | null;
  numero_de_factura: string | null;
  // Cambio 2 — el booking es individual por contenedor (PedidoDetalleContenedor.numero_de_booking);
  // ya no se usa a nivel de cabecera.
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
  // Transitario asignado al pedido-deal del contenedor (readonly, solo se muestra).
  // En modo doble flete (camión con tramo marítimo) `transitario` es el marítimo
  // y `transitario_terrestre` el terrestre; en legacy solo viene el primero.
  transitario?: string | null;
  transitario_terrestre?: string | null;
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
  // Envío por mensajería — gestión de administración. datos_envio_mensajeria es
  // editable; albaran_mensajeria es la subida real del albarán de recogida.
  datos_envio_mensajeria?: string | null;
  albaran_mensajeria?: ArchivoSimple | null;
  // Cambio 2 — datos de factura de SAP por contenedor (solo lectura).
  numero_de_factura: string | null;
  fecha_de_vencimiento_factura: string | null;
  // Cambio 2 — booking INDIVIDUAL por contenedor (sin fallback al del pedido).
  // Conduce el agrupado por embarque.
  numero_de_booking?: string | null;
  // Cambio 2 — documentos de cabecera por contenedor (factura/packing/carta de porte).
  // Cada contenedor genera los suyos (Fase 2). Si el backend aún no los expone por
  // contenedor, se cae al valor compartido del pedido (pedidoInfo).
  factura_pedido?: DealFile | null;
  packing_list_pedido?: DealFile | null;
  carta_porte_pedido?: DealFile | null;
  // BL por contenedor: el backend lo lee del Negocio Documento (autoritativo) con
  // fallback al Negocio Pedido. La escritura aplica solo a los seleccionados.
  bl_validado_logistica?: boolean;
  bl_validado_administracion?: boolean;
  bl_enviado_cliente?: boolean;
  tipo_de_bl?: string | null;
  cambios_en_bl?: string | null;
  bl_archivos?: BLArchivo[];
  // Negocio Documento del contenedor: si no existe, el pedido aún no completó su
  // pipeline y el contenedor no es gestionable en este asistente.
  tiene_negocio_documento: boolean;
  documento_dealstage?: string | null;
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


export interface PedidoInfo {
  etd: string | null;
  eta: string | null;
  consignee: string;
  notify: string;
  numero_contenedores: number;
  total_cajas_pedido: number | null;
  puerto_destino: string;
  puerto_salida: string;
  tipo_de_venta: string;
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
  // El BL es por contenedor (estadosContenedor[cid].bl); ya no se guarda a nivel de pedido.
  estado_origen: EstadoCertificado;
  estado_sanitario: EstadoCertificado;
  select_options: Record<string, SelectOption[]>;
}

export const DEFAULT_TIPO_PEDIDO: TipoPedido = TIPO_PEDIDO_CONTENEDOR;

export interface EstadoCertificado {
  borrador: CertificadoArchivo | null;
  validadoCliente: boolean;
  validado: CertificadoArchivo | null;
  sellado: CertificadoArchivo | null;
  enviarAFirmar: boolean;
}

export interface EstadoBL {
  borrador: BLArchivo | null;
  validadoLogistica: boolean;
  validadoAdministracion: boolean;
  enviadoCliente: boolean;
  tipo: string | null;
  cambiosEnBL: string | null;
  final: BLArchivo | null;
}

export interface EstadoEntrega {
  enviarPorMensajeria: boolean;
  permitirEnviar: boolean;
  // Datos de gestión de administración para la mensajería (nº copias, dirección de
  // envío, contacto). Editable y bulk a los contenedores seleccionados.
  datosEnvioMensajeria: string;
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
  bl: EstadoBL;
  otrosDocs: EstadoOtrosDocs;
  entrega: EstadoEntrega;
}

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
  enviarAFirmar:   false,
});

export const buildEstadoOrigen = (info: Partial<PedidoDetalleInfo>): EstadoCertificado => {
  const archivos = info.origen_archivos ?? [];
  return {
    borrador:        archivos.find((a) => a.tipo === "borrador") ?? null,
    validadoCliente: info.certificado_origen_validado ?? false,
    validado:        archivos.find((a) => a.tipo === "validado") ?? null,
    sellado:         archivos.find((a) => a.tipo === "sellado") ?? null,
    enviarAFirmar:   info.certificado_origen_enviar_a_firmar ?? false,
  };
};

export const buildEstadoSanitario = (info: Partial<PedidoDetalleInfo>): EstadoCertificado => {
  const archivos = info.sanitario_archivos ?? [];
  return {
    borrador:        archivos.find((a) => a.tipo === "borrador") ?? null,
    validadoCliente: info.certificado_sanitario_validado ?? false,
    validado:        archivos.find((a) => a.tipo === "validado") ?? null,
    sellado:         archivos.find((a) => a.tipo === "sellado") ?? null,
    enviarAFirmar:   info.certificado_sanitario_enviar_a_firmar ?? false,
  };
};

export const initialBL = (): EstadoBL => ({
  borrador:               null,
  validadoLogistica:      false,
  validadoAdministracion: false,
  enviadoCliente:         false,
  tipo:                   null,
  cambiosEnBL:            null,
  final:                  null,
});

// El BL es por contenedor: se lee del item de contenedor (Negocio Documento
// autoritativo, con fallback al Pedido, ya resuelto en el backend).
export const buildEstadoBLFromContenedor = (
  c: Partial<PedidoDetalleContenedor>,
): EstadoBL => {
  const archivos = c.bl_archivos ?? [];
  return {
    borrador:               archivos.find((a) => a.tipo === "borrador") ?? null,
    validadoLogistica:      c.bl_validado_logistica ?? false,
    validadoAdministracion: c.bl_validado_administracion ?? false,
    enviadoCliente:         c.bl_enviado_cliente ?? false,
    tipo:                   c.tipo_de_bl ?? null,
    cambiosEnBL:            c.cambios_en_bl ?? null,
    final:                  archivos.find((a) => a.tipo === "final") ?? null,
  };
};

export const initialEntrega = (): EstadoEntrega => ({
  enviarPorMensajeria:    false,
  permitirEnviar:         false,
  datosEnvioMensajeria:   "",
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
  datosEnvioMensajeria:   c.datos_envio_mensajeria ?? "",
  documentacionRecibida:  c.documentacion_recibida ?? false,
  fechaLlegadaContenedor: isoToBaseDate(c.fecha_llegada_contenedor),
  mercanciaRetirada:      c.mercancia_retirada ?? false,
  fechaRetirada:          isoToBaseDate(c.fecha_retirada_mercancia),
});

export const initialEstadoContenedor = (): EstadoContenedor => ({
  bl:        initialBL(),
  otrosDocs: initialEstadoOtrosDocs(),
  entrega:   initialEntrega(),
});

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

// La card vive en una Company: el filtrado es SIEMPRE por la empresa del contexto
// (companyId), no por texto. deal_id se mantiene por compat del contrato (el
// backend no lo usa para filtrar).
export const buildPendingPayload = (companyId: string, filtros: FiltrosState) => ({
  deal_id: String(companyId),
  filtros: {
    company_id:      String(companyId),
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

export const buildGeneratedPayload = (companyId: string, filtros: FiltrosState) =>
  buildPendingPayload(companyId, filtros);

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

  // Solo se muestran los documentos que el contenedor tiene marcados en
  // `documentos_a_generar` (o que ya estén generados): nada se pinta fijo.
  const docsAGenerar = contenedor.documentos_a_generar ?? [];

  if (esAparienciaContenedor(tipoPedido)) {
    // BL final POR CONTENEDOR (autoritativo desde su Negocio Documento), no el del
    // pedido compartido: cada contenedor puede tener su propio BL.
    const blFinal = (contenedor.bl_archivos ?? []).find((a) => a.tipo === "final") ?? null;
    if (docsAGenerar.includes("bl") || blFinal) {
      result.push({
        key:      "bl_final",
        label:    "BL final",
        generado: !!blFinal,
        url:      blFinal?.url ?? null,
        filename: blFinal?.name ?? null,
      });
    }

    const origenSellado = pedidoInfo.origen_archivos.find((a) => a.tipo === "sellado") ?? null;
    if (docsAGenerar.includes("certificado_de_origen") || origenSellado) {
      result.push({
        key:      "origen_sellado",
        label:    "Certificado de Origen",
        generado: !!origenSellado,
        url:      origenSellado?.url ?? null,
        filename: origenSellado?.name ?? null,
      });
    }

    const sanitarioSellado = pedidoInfo.sanitario_archivos.find((a) => a.tipo === "sellado") ?? null;
    if (docsAGenerar.includes("certificado_sanitario") || sanitarioSellado) {
      result.push({
        key:      "sanitario_sellado",
        label:    "Certificado Sanitario",
        generado: !!sanitarioSellado,
        url:      sanitarioSellado?.url ?? null,
        filename: sanitarioSellado?.name ?? null,
      });
    }
  }

  // Cabecera POR CONTENEDOR: el backend ya expone factura/packing/carta del
  // pedido-deal del contenedor. No se cae al doc del pedido (sería el del primer
  // contenedor y se mostraría como propio en los que aún no lo tienen).
  const facturaFile     = contenedor.factura_pedido ?? null;
  const packingFile     = contenedor.packing_list_pedido ?? null;
  const cartaPorteFile  = contenedor.carta_porte_pedido ?? null;

  result.push({
    key:      "factura",
    label:    "Factura",
    generado: !!facturaFile?.url,
    url:      facturaFile?.url ?? null,
    filename: facturaFile?.name ?? null,
  });

  if (docsAGenerar.includes(OTROS_DOC_TYPE_PACKING_LIST) || packingFile?.url) {
    result.push({
      key:      "packing_list",
      label:    "Packing list",
      generado: !!packingFile?.url,
      url:      packingFile?.url ?? null,
      filename: packingFile?.name ?? null,
    });
  }

  if (docsAGenerar.includes(OTROS_DOC_TYPE_CARTA_PORTE) || cartaPorteFile?.url) {
    result.push({
      key:      "carta_porte",
      label:    "Carta de porte",
      generado: !!cartaPorteFile?.url,
      url:      cartaPorteFile?.url ?? null,
      filename: cartaPorteFile?.name ?? null,
    });
  }

  for (const tipo of OTROS_DOC_SUBIBLES_DISCRIMINADOS) {
    const archivo =
      contenedor.documentos_archivos.find((a) => a.tipo === tipo) ?? null;
    // Se muestra si está marcado en documentos_a_generar O ya se subió.
    if (!docsAGenerar.includes(tipo) && !archivo) continue;
    result.push({
      key:      tipo,
      label:    OTROS_DOC_LABELS[tipo] ?? tipo,
      generado: !!archivo,
      url:      archivo?.url ?? null,
      filename: archivo?.name ?? null,
    });
  }

  const waiverBorrador = contenedor.documentos_archivos.find((a) => a.tipo === "waiver_borrador") ?? null;
  const waiverFinal    = contenedor.documentos_archivos.find((a) => a.tipo === "waiver_final") ?? null;
  if (docsAGenerar.includes(OTROS_DOC_TYPE_WAIVER) || waiverBorrador || waiverFinal) {
    const completo = !!waiverBorrador && contenedor.waiver_validado === true && !!waiverFinal;
    result.push({
      key:      OTROS_DOC_TYPE_WAIVER,
      label:    OTROS_DOC_LABELS[OTROS_DOC_TYPE_WAIVER] ?? OTROS_DOC_TYPE_WAIVER,
      generado: completo,
      url:      waiverFinal?.url ?? waiverBorrador?.url ?? null,
      filename: waiverFinal?.name ?? waiverBorrador?.name ?? null,
    });
  }

  if (docsAGenerar.includes(OTROS_DOC_TYPE_OTROS) || contenedor.otros_documentos.length > 0) {
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

export type EstadoDocFila = "completo" | "en_progreso" | "pendiente" | "vacio";

export interface ResumenDocFila {
  estado: EstadoDocFila;
  generados: number;
  total: number;
  label: string;
  variant: "success" | "info" | "warning" | "default";
}

/** Estado agregado de la documentación de un contenedor, para el color de su fila. */
export const resumenEstadoDocFila = (docs: DocStatus[]): ResumenDocFila => {
  const total = docs.length;
  const generados = docs.filter((d) => d.generado).length;
  if (total === 0) {
    return { estado: "vacio", generados, total, label: "Sin requisitos", variant: "default" };
  }
  if (generados === total) {
    return { estado: "completo", generados, total, label: "Completo", variant: "success" };
  }
  if (generados === 0) {
    return { estado: "pendiente", generados, total, label: `0/${total}`, variant: "warning" };
  }
  return { estado: "en_progreso", generados, total, label: `${generados}/${total}`, variant: "info" };
};

/** Booking del contenedor. Cambio 2 — el booking es individual por contenedor;
 *  no se cae al del pedido (cada contenedor lleva el suyo, puede diferir por embarque). */
export const bookingDeContenedor = (
  contenedor: Pick<PedidoDetalleContenedor, "numero_de_booking">,
): string | null => {
  const propio = contenedor.numero_de_booking;
  return propio && propio.trim() !== "" ? propio.trim() : null;
};

export interface DocsCabeceraContenedor {
  factura: DealFile | null;
  packing: DealFile | null;
  cartaPorte: DealFile | null;
}

/** Documentos de cabecera (factura/packing/carta) del contenedor con fallback al pedido. */
export const docsCabeceraDeContenedor = (
  contenedor: Pick<
    PedidoDetalleContenedor,
    "factura_pedido" | "packing_list_pedido" | "carta_porte_pedido"
  >,
): DocsCabeceraContenedor => ({
  // Por contenedor: el backend ya expone los docs de su pedido-deal. Sin fallback
  // al pedido para no mostrar el doc del primer contenedor como propio.
  factura:    contenedor.factura_pedido ?? null,
  packing:    contenedor.packing_list_pedido ?? null,
  cartaPorte: contenedor.carta_porte_pedido ?? null,
});

export interface CobroAcumulado {
  precioTotal: number;
  pendienteTotal: number;
  porcentajePendiente: number;
  cobradoCompleto: boolean;
  precioDisponible: boolean;
}

/** Acumula precio/pendiente de varios contenedores para el resumen de cobro multi-contenedor. */
export const acumularCobro = (
  contenedores: Array<Pick<PedidoDetalleContenedor, "price" | "importe_pendiente_cobro">>,
): CobroAcumulado => {
  let precioTotal = 0;
  let pendienteTotal = 0;
  let precioDisponible = false;
  for (const c of contenedores) {
    const precio = parseFloatOrZero(c.price);
    // Solo se acumulan los contenedores con precio informado, para que el % global
    // no mezcle pendientes de contenedores sin precio con el total de precios.
    if (precio > ESTADO_COBRO_TOLERANCIA) {
      precioDisponible = true;
      precioTotal += precio;
      pendienteTotal += parseFloatOrZero(c.importe_pendiente_cobro);
    }
  }
  const porcentajePendiente =
    precioTotal > ESTADO_COBRO_TOLERANCIA
      ? Math.max(0, Math.min(100, (pendienteTotal / precioTotal) * 100))
      : 0;
  return {
    precioTotal,
    pendienteTotal,
    porcentajePendiente,
    cobradoCompleto: precioDisponible && pendienteTotal <= ESTADO_COBRO_TOLERANCIA,
    precioDisponible,
  };
};
