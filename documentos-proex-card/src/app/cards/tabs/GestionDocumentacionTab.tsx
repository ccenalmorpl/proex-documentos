import React, { useState, useCallback } from "react";
import {
  Box,
  Flex,
  Button,
} from "@hubspot/ui-extensions";

import SelectorEmpresaPedido from "../components/SelectorEmpresaPedido";
import InfoPedidoReadonly from "../components/InfoPedidoReadonly";
import ContenedoresGestionTable from "../components/ContenedoresGestionTable";
import DetalleContenedorPanel from "../components/DetalleContenedorPanel";

import {
  baseDateToIso,
  buildEstadoBL,
  buildEstadoEntrega,
  buildEstadoOrigen,
  buildEstadoOtrosDocs,
  buildEstadoSanitario,
  initialEstadoContenedor,
  type EmpresaItem,
  type PedidoDetalleContenedor,
  type PedidoMock,
  type PedidoResumen,
  type EstadoBL,
  type EstadoCertificado,
  type EstadoContenedor,
  type EstadoEntrega,
} from "../utils/documentos.utils";
import {
  fetchPedidoDetalle,
  updateContenedorEntrega,
  type UpdateContenedorEntregaPayload,
} from "../utils/gestion.api";

interface GestionDocumentacionTabProps {
  context: any;
  actions: any;
}

const ENTREGA_FIELD_LABELS: Record<keyof UpdateContenedorEntregaPayload, string> = {
  enviar_por_mensajeria:         "Envío por mensajería",
  permitir_enviar_documentacion: "Permiso de envío",
  documentacion_recibida:        "Documentación recibida",
  mercancia_retirada:            "Mercancía retirada",
  fecha_llegada_contenedor:      "Fecha de envío de originales al cliente",
  fecha_retirada_mercancia:      "Fecha de retirada",
};

const describeEntregaPayload = (payload: UpdateContenedorEntregaPayload): string => {
  const labels = Object.keys(payload)
    .map((k) => ENTREGA_FIELD_LABELS[k as keyof UpdateContenedorEntregaPayload])
    .filter(Boolean);
  if (labels.length === 0) return "";
  if (labels.length === 1) return `${labels[0]} actualizado`;
  return `Campos actualizados: ${labels.join(", ")}`;
};

const buildEntregaDiff = (
  prev: EstadoEntrega | undefined,
  next: EstadoEntrega,
): UpdateContenedorEntregaPayload => {
  const payload: UpdateContenedorEntregaPayload = {};
  if (!prev || prev.enviarPorMensajeria !== next.enviarPorMensajeria)
    payload.enviar_por_mensajeria = next.enviarPorMensajeria;
  if (!prev || prev.permitirEnviar !== next.permitirEnviar)
    payload.permitir_enviar_documentacion = next.permitirEnviar;
  if (!prev || prev.documentacionRecibida !== next.documentacionRecibida)
    payload.documentacion_recibida = next.documentacionRecibida;
  if (!prev || prev.mercanciaRetirada !== next.mercanciaRetirada)
    payload.mercancia_retirada = next.mercanciaRetirada;

  const prevFL = baseDateToIso(prev?.fechaLlegadaContenedor);
  const nextFL = baseDateToIso(next.fechaLlegadaContenedor);
  if (prevFL !== nextFL) payload.fecha_llegada_contenedor = nextFL;

  const prevFR = baseDateToIso(prev?.fechaRetirada);
  const nextFR = baseDateToIso(next.fechaRetirada);
  if (prevFR !== nextFR) payload.fecha_retirada_mercancia = nextFR;

  return payload;
};

const hidratarEstadosContenedor = (
  contenedores: PedidoDetalleContenedor[],
  _prev: Record<string, EstadoContenedor>,
): Record<string, EstadoContenedor> => {
  const next: Record<string, EstadoContenedor> = {};
  for (const c of contenedores) {
    next[c.id] = {
      otrosDocs: buildEstadoOtrosDocs(c),
      entrega:   buildEstadoEntrega(c),
    };
  }
  return next;
};

const GestionDocumentacionTab: React.FC<GestionDocumentacionTabProps> = ({ actions }) => {
  const [pedido, setPedido] = useState<PedidoMock | null>(null);
  const [contenedorActivoId, setContenedorActivoId] = useState<string | null>(null);

  const [estadoBL, setEstadoBL] = useState<EstadoBL>(() => buildEstadoBL({}));
  const [estadoOrigen, setEstadoOrigen] = useState<EstadoCertificado>(() => buildEstadoOrigen({}));
  const [estadoSanitario, setEstadoSanitario] = useState<EstadoCertificado>(() => buildEstadoSanitario({}));
  const [estadosContenedor, setEstadosContenedor] = useState<Record<string, EstadoContenedor>>({});

  const [selectorEmpresaQuery, setSelectorEmpresaQuery] = useState<string>("");
  const [selectorEmpresaId, setSelectorEmpresaId] = useState<string>("");
  const [selectorPedidoNumero, setSelectorPedidoNumero] = useState<string>("");
  const [selectorEmpresasCache, setSelectorEmpresasCache] = useState<{
    query: string;
    items: EmpresaItem[];
  } | null>(null);
  const [selectorPedidosCache, setSelectorPedidosCache] = useState<{
    empresaId: string;
    items: PedidoResumen[];
  } | null>(null);

  const handleEmpresasLoaded = useCallback((query: string, items: EmpresaItem[]) => {
    setSelectorEmpresasCache({ query, items });
  }, []);
  const handlePedidosLoaded = useCallback((empresaId: string, items: PedidoResumen[]) => {
    setSelectorPedidosCache({ empresaId, items });
  }, []);

  const handleCargarPedido = useCallback((p: PedidoMock) => {
    setPedido(p);
    setContenedorActivoId(null);
    setEstadoBL(p.estado_bl);
    setEstadoOrigen(p.estado_origen);
    setEstadoSanitario(p.estado_sanitario);
    setEstadosContenedor(hidratarEstadosContenedor(p.contenedoresDetalle, {}));
  }, []);

  const refetchPedido = useCallback(async () => {
    if (!pedido) return;
    try {
      const detalle = await fetchPedidoDetalle(pedido.numero, pedido.companyId);
      const nextBL = buildEstadoBL(detalle.info);
      const nextOrigen = buildEstadoOrigen(detalle.info);
      const nextSanitario = buildEstadoSanitario(detalle.info);
      setEstadoBL(nextBL);
      setEstadoOrigen(nextOrigen);
      setEstadoSanitario(nextSanitario);
      setEstadosContenedor((prev) => hidratarEstadosContenedor(detalle.contenedores, prev));
      setPedido((prev) =>
        prev
          ? {
              ...prev,
              pedidoInfo:          detalle.info,
              contenedoresDetalle: detalle.contenedores,
              estado_bl:           nextBL,
              estado_origen:       nextOrigen,
              estado_sanitario:    nextSanitario,
              select_options:      detalle.select_options ?? prev.select_options,
            }
          : prev,
      );
    } catch (e) {
      console.error("[GestionTab] refetch error:", e);
    }
  }, [pedido]);

  const handleCambiarPedido = useCallback(() => {
    setPedido(null);
    setContenedorActivoId(null);
  }, []);

  const handleSeleccionarContenedor = useCallback((id: string) => {
    setContenedorActivoId(id);
  }, []);

  const handleChangeEntrega = useCallback(
    async (next: EstadoEntrega) => {
      if (!contenedorActivoId || !pedido) return;

      const cid = contenedorActivoId;
      const prevSnapshot = estadosContenedor[cid];
      const payload = buildEntregaDiff(prevSnapshot?.entrega, next);

      setEstadosContenedor((prev) => {
        const current = prev[cid] ?? initialEstadoContenedor();
        return { ...prev, [cid]: { ...current, entrega: next } };
      });

      if (Object.keys(payload).length === 0) return;

      try {
        const resp = await updateContenedorEntrega(
          pedido.numero, pedido.companyId, cid, payload,
        );
        if (!resp.success) throw new Error(resp.error ?? "Error guardando entrega");
        actions?.addAlert?.({
          type: "success",
          title: "Entrega actualizada",
          message: describeEntregaPayload(payload),
        });
      } catch (e: any) {
        if (prevSnapshot) {
          setEstadosContenedor((prev) => ({ ...prev, [cid]: prevSnapshot }));
        }
        actions?.addAlert?.({
          type: "danger",
          title: "Entrega — error",
          message: e?.message ?? "No se pudo guardar el cambio.",
        });
      }
    },
    [contenedorActivoId, pedido, estadosContenedor, actions],
  );

  if (!pedido) {
    return (
      <Flex direction="column" gap="medium">
        <SelectorEmpresaPedido
          onCargarPedido={handleCargarPedido}
          empresaQuery={selectorEmpresaQuery}
          empresaId={selectorEmpresaId}
          pedidoNumero={selectorPedidoNumero}
          onEmpresaQueryChange={setSelectorEmpresaQuery}
          onEmpresaIdChange={setSelectorEmpresaId}
          onPedidoNumeroChange={setSelectorPedidoNumero}
          empresasCache={selectorEmpresasCache}
          pedidosCache={selectorPedidosCache}
          onEmpresasLoaded={handleEmpresasLoaded}
          onPedidosLoaded={handlePedidosLoaded}
        />
      </Flex>
    );
  }

  const contenedorActivo =
    contenedorActivoId !== null
      ? pedido.contenedores.find((c) => c.id === contenedorActivoId)
      : null;

  const contenedorActivoDetalle =
    contenedorActivoId !== null
      ? pedido.contenedoresDetalle.find((c) => c.id === contenedorActivoId)
      : null;

  const estadoContenedor =
    contenedorActivoId !== null
      ? estadosContenedor[contenedorActivoId] ?? initialEstadoContenedor()
      : null;

  const documentosAGenerarContenedor =
    contenedorActivoDetalle?.documentos_a_generar ?? pedido.documentos_a_generar;

  const docsAGenerarPedido = new Set<string>(
    pedido.contenedoresDetalle.flatMap((c) => c.documentos_a_generar ?? []),
  );
  const requiereBL        = docsAGenerarPedido.has("bl");
  const requiereOrigen    = docsAGenerarPedido.has("certificado_de_origen");
  const requiereSanitario = docsAGenerarPedido.has("certificado_sanitario");

  return (
    <Flex direction="column" gap="medium">
      <Flex direction="row" justify="end">
        <Button variant="secondary" size="sm" onClick={handleCambiarPedido}>
          Cambiar pedido
        </Button>
      </Flex>

      <InfoPedidoReadonly
        numeroPedido={pedido.numero}
        companyId={pedido.companyId}
        info={pedido.info}
        tipoPedido={pedido.tipo_pedido}
        cargaPorPalets={pedido.carga_por_palets}
      />

      <ContenedoresGestionTable
        contenedores={pedido.contenedores}
        contenedoresDetalle={pedido.contenedoresDetalle}
        pedidoInfo={pedido.pedidoInfo}
        fotosDeCarga={pedido.fotos_de_carga}
        contenedorActivoId={contenedorActivoId}
        tipoPedido={pedido.tipo_pedido}
        cargaPorPalets={pedido.carga_por_palets}
        onSeleccionar={handleSeleccionarContenedor}
      />

      {contenedorActivo && estadoContenedor && contenedorActivoDetalle && (
        <Box>
          <DetalleContenedorPanel
            contenedor={contenedorActivo}
            contenedorDetalle={contenedorActivoDetalle}
            numContenedoresPedido={pedido.contenedores.length}
            documentosAGenerar={documentosAGenerarContenedor}
            requiereBL={requiereBL}
            requiereOrigen={requiereOrigen}
            requiereSanitario={requiereSanitario}
            tipoPedido={pedido.tipo_pedido}
            fotosDeCarga={pedido.fotos_de_carga}
            estadoBL={estadoBL}
            estadoOrigen={estadoOrigen}
            estadoSanitario={estadoSanitario}
            estadoContenedor={estadoContenedor}
            numeroPedido={pedido.numero}
            companyId={pedido.companyId}
            pedidoInfo={pedido.pedidoInfo}
            selectOptions={pedido.select_options}
            onChangeBL={setEstadoBL}
            onUpdated={refetchPedido}
            onChangeOrigen={setEstadoOrigen}
            onChangeSanitario={setEstadoSanitario}
            onChangeEntrega={handleChangeEntrega}
            actions={actions}
          />
        </Box>
      )}
    </Flex>
  );
};

export default GestionDocumentacionTab;
