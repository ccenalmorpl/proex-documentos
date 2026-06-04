import React, { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Flex,
  Form,
  Heading,
  LoadingSpinner,
  SearchInput,
  Select,
  Text,
} from "@hubspot/ui-extensions";

import { useDebounce } from "../hooks/useDebounce";
import {
  fetchPedidoDetalle,
  fetchPedidosByEmpresa,
  searchEmpresas,
} from "../utils/gestion.api";
import {
  buildEstadoBL,
  buildEstadoOrigen,
  buildEstadoSanitario,
  ESTADO_COBRO_TOLERANCIA,
  parseFloatOrZero,
  type EmpresaItem,
  type PedidoDetalle,
  type PedidoMock,
  type PedidoResumen,
} from "../utils/documentos.utils";
import {
  TIPO_PEDIDO_EXPORTACION,
  TIPO_PEDIDO_NACIONAL,
  TIPO_PEDIDO_NACIONAL_SAN_ROQUE,
  type TipoPedido,
} from "../constants/documentos.constants";

interface SelectorEmpresaPedidoProps {
  onCargarPedido: (pedido: PedidoMock) => void;
  empresaQuery: string;
  empresaId: string;
  pedidoNumero: string;
  onEmpresaQueryChange: (q: string) => void;
  onEmpresaIdChange: (id: string) => void;
  onPedidoNumeroChange: (numero: string) => void;
  empresasCache: { query: string; items: EmpresaItem[] } | null;
  pedidosCache: { empresaId: string; items: PedidoResumen[] } | null;
  onEmpresasLoaded: (query: string, items: EmpresaItem[]) => void;
  onPedidosLoaded: (empresaId: string, items: PedidoResumen[]) => void;
}

const MIN_EMPRESA_QUERY = 2;
const DEBOUNCE_MS = 300;

const FALLBACK_DASH = "—";

const valueOrDash = (raw: string | null | undefined): string =>
  raw && raw.trim() !== "" ? raw : FALLBACK_DASH;

const tipoFlujoToTipoPedido = (tipoFlujo: string | null): TipoPedido => {
  switch (tipoFlujo) {
    case TIPO_PEDIDO_NACIONAL:
      return TIPO_PEDIDO_NACIONAL;
    case TIPO_PEDIDO_NACIONAL_SAN_ROQUE:
      return TIPO_PEDIDO_NACIONAL_SAN_ROQUE;
    default:
      return TIPO_PEDIDO_EXPORTACION;
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
    estado_bl:            buildEstadoBL(detalle.info),
    estado_origen:        buildEstadoOrigen(detalle.info),
    estado_sanitario:     buildEstadoSanitario(detalle.info),
    select_options:       detalle.select_options ?? {},
  };
};

const SelectorEmpresaPedido: React.FC<SelectorEmpresaPedidoProps> = ({
  onCargarPedido,
  empresaQuery,
  empresaId: empresaSeleccionadaId,
  pedidoNumero,
  onEmpresaQueryChange,
  onEmpresaIdChange,
  onPedidoNumeroChange,
  empresasCache,
  pedidosCache,
  onEmpresasLoaded,
  onPedidosLoaded,
}) => {
  const debouncedQuery = useDebounce(empresaQuery, DEBOUNCE_MS);

  const [loadingEmpresas, setLoadingEmpresas] = useState(false);
  const [errorEmpresas, setErrorEmpresas] = useState<string | null>(null);

  const [loadingPedidos, setLoadingPedidos] = useState(false);
  const [errorPedidos, setErrorPedidos] = useState<string | null>(null);

  const [loadingDetalle, setLoadingDetalle] = useState(false);
  const [errorDetalle, setErrorDetalle] = useState<string | null>(null);

  const empresas: EmpresaItem[] =
    empresasCache && empresasCache.query === debouncedQuery.trim()
      ? empresasCache.items
      : [];
  const pedidos: PedidoResumen[] =
    pedidosCache && pedidosCache.empresaId === empresaSeleccionadaId
      ? pedidosCache.items
      : [];

  useEffect(() => {
    const q = debouncedQuery.trim();
    if (q.length < MIN_EMPRESA_QUERY) {
      setErrorEmpresas(null);
      setLoadingEmpresas(false);
      return;
    }
    if (empresasCache && empresasCache.query === q) {
      setLoadingEmpresas(false);
      setErrorEmpresas(null);
      return;
    }

    let cancelled = false;
    setLoadingEmpresas(true);
    setErrorEmpresas(null);

    searchEmpresas(q)
      .then((items) => {
        if (cancelled) return;
        onEmpresasLoaded(q, items);
      })
      .catch((err: any) => {
        if (cancelled) return;
        onEmpresasLoaded(q, []);
        setErrorEmpresas(err?.message ?? "Error buscando empresas.");
      })
      .finally(() => {
        if (!cancelled) setLoadingEmpresas(false);
      });

    return () => {
      cancelled = true;
    };
  }, [debouncedQuery, empresasCache, onEmpresasLoaded]);

  useEffect(() => {
    if (!empresaSeleccionadaId) {
      setErrorPedidos(null);
      setLoadingPedidos(false);
      return;
    }
    if (pedidosCache && pedidosCache.empresaId === empresaSeleccionadaId) {
      setLoadingPedidos(false);
      setErrorPedidos(null);
      return;
    }

    let cancelled = false;
    setLoadingPedidos(true);
    setErrorPedidos(null);

    fetchPedidosByEmpresa(empresaSeleccionadaId)
      .then((items) => {
        if (cancelled) return;
        onPedidosLoaded(empresaSeleccionadaId, items);
      })
      .catch((err: any) => {
        if (cancelled) return;
        onPedidosLoaded(empresaSeleccionadaId, []);
        setErrorPedidos(err?.message ?? "Error cargando pedidos.");
      })
      .finally(() => {
        if (!cancelled) setLoadingPedidos(false);
      });

    return () => {
      cancelled = true;
    };
  }, [empresaSeleccionadaId, pedidosCache, onPedidosLoaded]);

  const empresaOptions = useMemo(
    () => empresas.map((e) => ({ label: e.name || `(sin nombre · ${e.id})`, value: e.id })),
    [empresas],
  );

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

  const empresaSeleccionada = empresas.find((e) => e.id === empresaSeleccionadaId) ?? null;
  const pedidoSeleccionado  = pedidos.find((p) => p.numero_de_pedido === pedidoNumero) ?? null;

  const canSubmit = !!empresaSeleccionada && !!pedidoSeleccionado && !loadingDetalle;

  const handleCargar = async () => {
    if (!empresaSeleccionada || !pedidoSeleccionado) return;

    setLoadingDetalle(true);
    setErrorDetalle(null);

    try {
      const detalle = await fetchPedidoDetalle(
        pedidoSeleccionado.numero_de_pedido,
        empresaSeleccionada.id,
      );
      onCargarPedido(buildPedidoFromDetalle(detalle));
    } catch (err: any) {
      setErrorDetalle(err?.message ?? "Error cargando el detalle del pedido.");
    } finally {
      setLoadingDetalle(false);
    }
  };

  const empresaDescription =
    empresaQuery.trim().length < MIN_EMPRESA_QUERY
      ? `Escribe al menos ${MIN_EMPRESA_QUERY} caracteres para buscar.`
      : loadingEmpresas
        ? "Buscando..."
        : `${empresas.length} resultado${empresas.length === 1 ? "" : "s"}.`;

  return (
    <Box>
      <Heading>Selecciona empresa y pedido</Heading>
      <Text variant="microcopy">
        Carga los contenedores ya gestionados en el pipeline de pedidos para gestionar su documentación.
      </Text>
      <Form>
        <Flex direction="column" gap="small">
          <SearchInput
            label="Empresa"
            name="empresa_gestion"
            value={empresaQuery}
            onInput={(v: string) => {
              onEmpresaQueryChange(v);
              onEmpresaIdChange("");
              onPedidoNumeroChange("");
            }}
            placeholder=""
            required
            description={empresaDescription}
          />

          {loadingEmpresas && <LoadingSpinner label="Buscando empresas..." />}
          {errorEmpresas && (
            <Alert title="Error buscando empresas" variant="error">
              {errorEmpresas}
            </Alert>
          )}

          <Select
            label="Empresa encontrada"
            name="empresa_id"
            value={empresaSeleccionadaId}
            options={empresaOptions}
            onChange={(v) => {
              const next = String(v ?? "");
              if (next !== empresaSeleccionadaId) onPedidoNumeroChange("");
              onEmpresaIdChange(next);
            }}
            placeholder="Seleccionar..."
            required
            readOnly={empresas.length === 0}
            description="Empresas que coinciden con la búsqueda."
          />

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
            readOnly={!empresaSeleccionadaId || pedidos.length === 0}
            description="Pedidos asociados a la empresa seleccionada."
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
