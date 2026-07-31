import React, { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Flex,
  Form,
  Heading,
  LoadingSpinner,
  Select,
  Text,
} from "@hubspot/ui-extensions";
import { CrmDataHighlight } from "@hubspot/ui-extensions/crm";

import {
  fetchPedidoDetalle,
  fetchPedidosByEmpresa,
} from "../utils/gestion.api";
import {
  buildEstadoOrigen,
  buildEstadoSanitario,
  ESTADO_COBRO_TOLERANCIA,
  parseFloatOrZero,
  type PedidoDetalle,
  type PedidoMock,
  type PedidoResumen,
} from "../utils/documentos.utils";
import {
  COMPANY_HIGHLIGHT_PROPS,
  TIPO_PEDIDO_CONTENEDOR,
  TIPO_PEDIDO_CONTENEDOR_SAN_ROQUE,
  TIPO_PEDIDO_CAMION,
  TIPO_PEDIDO_CAMION_SAN_ROQUE,
  type TipoPedido,
} from "../constants/documentos.constants";

interface SelectorEmpresaPedidoProps {
  companyId: string;
  onCargarPedido: (pedido: PedidoMock) => void;
  pedidoNumero: string;
  onPedidoNumeroChange: (numero: string) => void;
  pedidosCache: { empresaId: string; items: PedidoResumen[] } | null;
  onPedidosLoaded: (empresaId: string, items: PedidoResumen[]) => void;
}

const FALLBACK_DASH = "—";

const valueOrDash = (raw: string | null | undefined): string =>
  raw && raw.trim() !== "" ? raw : FALLBACK_DASH;

const tipoFlujoToTipoPedido = (tipoFlujo: string | null): TipoPedido => {
  switch (tipoFlujo) {
    case TIPO_PEDIDO_CAMION:
    case "nacional": // legacy (pre-renombrado)
      return TIPO_PEDIDO_CAMION;
    case TIPO_PEDIDO_CAMION_SAN_ROQUE:
    case "nacional_san_roque": // legacy
      return TIPO_PEDIDO_CAMION_SAN_ROQUE;
    case TIPO_PEDIDO_CONTENEDOR_SAN_ROQUE:
      return TIPO_PEDIDO_CONTENEDOR_SAN_ROQUE;
    case TIPO_PEDIDO_CONTENEDOR:
    case "exportacion": // legacy
    default:
      return TIPO_PEDIDO_CONTENEDOR;
  }
};

const aggregateDocumentosAGenerar = (
  contenedores: PedidoDetalle["contenedores"],
): string[] => {
  const seen = new Set<string>();
  contenedores.forEach((c) => c.documentos_a_generar.forEach((d) => seen.add(d)));
  return Array.from(seen);
};

const sumTotalCajas = (
  contenedores: PedidoDetalle["contenedores"],
): number | null => {
  let total = 0;
  let alguno = false;
  for (const c of contenedores) {
    const n = Number(c.total_cajas);
    if (Number.isFinite(n)) {
      total += n;
      alguno = true;
    }
  }
  return alguno ? total : null;
};

const buildPedidoFromDetalle = (detalle: PedidoDetalle): PedidoMock => {
  const importePendienteTotal = detalle.contenedores.reduce(
    (acc, c) => acc + parseFloatOrZero(c.importe_pendiente_cobro),
    0,
  );

  return {
    id:             detalle.empresa.id,
    numero:         detalle.numero_de_pedido,
    companyId:      detalle.empresa.id,
    empresa:        detalle.empresa.name ?? "",
    tipo_pedido:    tipoFlujoToTipoPedido(detalle.tipo_flujo),
    carga_por_palets: detalle.carga_por_palets ?? false,
    fotos_de_carga: detalle.fotos_de_carga,
    info: {
      etd:                   detalle.info.etd,
      eta:                   detalle.info.eta,
      consignee:             detalle.info.consignee ?? "",
      notify:                detalle.info.notify ?? "",
      numero_contenedores:   detalle.contenedores.length,
      total_cajas_pedido:    sumTotalCajas(detalle.contenedores),
      puerto_destino:        detalle.info.puerto_destino ?? "",
      puerto_salida:         detalle.info.puerto_salida ?? "",
      tipo_de_venta:         detalle.info.tipo_de_venta ?? "",
      descripcion_mercancia: detalle.info.descripcion_mercancia ?? "",
      fecha_de_entrega:      detalle.info.fecha_de_entrega,
      lugar_carga:           detalle.info.lugar_carga ?? "",
      localidad_destino:     detalle.info.localidad_destino ?? "",
      direccion_de_entrega:  detalle.info.direccion_de_entrega ?? "",
      datos_del_chofer:      detalle.info.datos_del_chofer ?? "",
      comentarios_logistica: detalle.info.comentarios_logistica ?? "",
    },
    pedidoInfo:           detalle.info,
    contenedores: detalle.contenedores.map((c) => ({
      id:                    c.id,
      nombre:                valueOrDash(c.nombre),
      numero:                valueOrDash(c.numero_contenedor ?? c.nombre),
      precinto:              valueOrDash(c.numero_precinto),
      peso_bruto:            valueOrDash(c.peso_bruto),
      peso_neto:             valueOrDash(c.peso_neto),
      tara:                  valueOrDash(c.tara),
      vgm:                   valueOrDash(c.vgm),
      descripcion_mercancia: c.descripcion_mercancia_agregada ?? "",
    })),
    contenedoresDetalle:  detalle.contenedores,
    documentos_a_generar: aggregateDocumentosAGenerar(detalle.contenedores),
    estado_cobro:         importePendienteTotal <= ESTADO_COBRO_TOLERANCIA ? "cobrado" : "pendiente",
    importe_pendiente:    importePendienteTotal,
    estado_origen:        buildEstadoOrigen(detalle.info),
    estado_sanitario:     buildEstadoSanitario(detalle.info),
    select_options:       detalle.select_options ?? {},
  };
};

const SelectorEmpresaPedido: React.FC<SelectorEmpresaPedidoProps> = ({
  companyId,
  onCargarPedido,
  pedidoNumero,
  onPedidoNumeroChange,
  pedidosCache,
  onPedidosLoaded,
}) => {
  const [loadingPedidos, setLoadingPedidos] = useState(false);
  const [errorPedidos, setErrorPedidos] = useState<string | null>(null);

  const [loadingDetalle, setLoadingDetalle] = useState(false);
  const [errorDetalle, setErrorDetalle] = useState<string | null>(null);

  const pedidos: PedidoResumen[] =
    pedidosCache && pedidosCache.empresaId === companyId
      ? pedidosCache.items
      : [];

  useEffect(() => {
    if (!companyId) {
      setErrorPedidos(null);
      setLoadingPedidos(false);
      return;
    }
    if (pedidosCache && pedidosCache.empresaId === companyId) {
      setLoadingPedidos(false);
      setErrorPedidos(null);
      return;
    }

    let cancelled = false;
    setLoadingPedidos(true);
    setErrorPedidos(null);

    fetchPedidosByEmpresa(companyId)
      .then((items) => {
        if (cancelled) return;
        onPedidosLoaded(companyId, items);
      })
      .catch((err: any) => {
        if (cancelled) return;
        // No sembramos la caché en el error: así el Alert persiste. Si cacheáramos
        // items:[], el cambio de referencia de pedidosCache re-dispararía el efecto,
        // que entraría en la rama de cache-hit y limpiaría el error (bug).
        setErrorPedidos(err?.message ?? "Error cargando pedidos.");
      })
      .finally(() => {
        if (!cancelled) setLoadingPedidos(false);
      });

    return () => {
      cancelled = true;
    };
  }, [companyId, pedidosCache, onPedidosLoaded]);

  const pedidoOptions = useMemo(
    () =>
      pedidos.map((p) => {
        const base = `${p.numero_de_pedido} · ${p.numero_contenedores_pedido} contenedor${p.numero_contenedores_pedido === 1 ? "" : "es"}`;
        return {
          label: p.nombre_cotizacion ? `${base} (${p.nombre_cotizacion})` : base,
          value: p.numero_de_pedido,
        };
      }),
    [pedidos],
  );

  const pedidoSeleccionado = pedidos.find((p) => p.numero_de_pedido === pedidoNumero) ?? null;

  const canSubmit = !!pedidoSeleccionado && !loadingDetalle;

  const handleCargar = async () => {
    if (!pedidoSeleccionado || !companyId) return;

    setLoadingDetalle(true);
    setErrorDetalle(null);

    try {
      const detalle = await fetchPedidoDetalle(
        pedidoSeleccionado.numero_de_pedido,
        companyId,
      );
      onCargarPedido(buildPedidoFromDetalle(detalle));
    } catch (err: any) {
      setErrorDetalle(err?.message ?? "Error cargando el detalle del pedido.");
    } finally {
      setLoadingDetalle(false);
    }
  };

  return (
    <Box>
      <Heading>Selecciona el pedido</Heading>
      <Text variant="microcopy">
        Carga los contenedores ya gestionados en el pipeline de pedidos de esta empresa para gestionar su documentación.
      </Text>

      {companyId && (
        <CrmDataHighlight properties={COMPANY_HIGHLIGHT_PROPS} />
      )}

      <Form>
        <Flex direction="column" gap="small">
          {!companyId && (
            <Alert title="Falta la empresa en el contexto" variant="warning">
              La card no recibió un objectId de Company en el contexto de HubSpot.
              Asegúrate de instalar la card sobre un registro de Empresa.
            </Alert>
          )}

          {loadingPedidos && <LoadingSpinner label="Cargando pedidos..." />}
          {errorPedidos && (
            <Alert title="Error cargando pedidos" variant="error">
              {errorPedidos}
            </Alert>
          )}

          <Select
            label="Nº de pedido"
            name="pedido_numero"
            value={pedidoNumero}
            options={pedidoOptions}
            onChange={(v) => onPedidoNumeroChange(String(v ?? ""))}
            placeholder="Seleccionar..."
            required
            readOnly={!companyId || pedidos.length === 0}
            description="Pedidos asociados a la empresa del contexto."
          />

          {loadingDetalle && <LoadingSpinner label="Cargando detalle del pedido..." />}
          {errorDetalle && (
            <Alert title="Error cargando el pedido" variant="error">
              {errorDetalle}
            </Alert>
          )}

          <Button variant="primary" onClick={handleCargar} disabled={!canSubmit}>
            {loadingDetalle ? "Cargando..." : "Cargar pedido"}
          </Button>
        </Flex>
      </Form>
    </Box>
  );
};

export default SelectorEmpresaPedido;
