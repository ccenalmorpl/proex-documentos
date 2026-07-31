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
  bookingDeContenedor,
  buildEstadoBLFromContenedor,
  buildEstadoEntrega,
  buildEstadoOrigen,
  buildEstadoOtrosDocs,
  buildEstadoSanitario,
  initialEstadoContenedor,
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
  waiver_validado:               "Validación de waiver",
  fecha_llegada_contenedor:      "Fecha de envío de originales al cliente",
  fecha_retirada_mercancia:      "Fecha de retirada",
  datos_envio_mensajeria:        "Datos de envío por mensajería",
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
  if (!prev || prev.datosEnvioMensajeria !== next.datosEnvioMensajeria)
    payload.datos_envio_mensajeria = next.datosEnvioMensajeria;

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
      bl:        buildEstadoBLFromContenedor(c),
      otrosDocs: buildEstadoOtrosDocs(c),
      entrega:   buildEstadoEntrega(c),
    };
  }
  return next;
};

const GestionDocumentacionTab: React.FC<GestionDocumentacionTabProps> = ({ context, actions }) => {
  const companyId: string = context?.crm?.objectId ?? "";

  const [pedido, setPedido] = useState<PedidoMock | null>(null);
  const [seleccionados, setSeleccionados] = useState<string[]>([]);

  // El BL es por contenedor: vive en estadosContenedor[cid].bl (no a nivel de pedido).
  const [estadoOrigen, setEstadoOrigen] = useState<EstadoCertificado>(() => buildEstadoOrigen({}));
  const [estadoSanitario, setEstadoSanitario] = useState<EstadoCertificado>(() => buildEstadoSanitario({}));
  const [estadosContenedor, setEstadosContenedor] = useState<Record<string, EstadoContenedor>>({});

  const [selectorPedidoNumero, setSelectorPedidoNumero] = useState<string>("");
  const [selectorPedidosCache, setSelectorPedidosCache] = useState<{
    empresaId: string;
    items: PedidoResumen[];
  } | null>(null);

  const handlePedidosLoaded = useCallback((empresaId: string, items: PedidoResumen[]) => {
    setSelectorPedidosCache({ empresaId, items });
  }, []);

  const handleCargarPedido = useCallback((p: PedidoMock) => {
    setPedido(p);
    setSeleccionados([]);
    setEstadoOrigen(p.estado_origen);
    setEstadoSanitario(p.estado_sanitario);
    setEstadosContenedor(hidratarEstadosContenedor(p.contenedoresDetalle, {}));
  }, []);

  const refetchPedido = useCallback(async () => {
    if (!pedido) return;
    try {
      const detalle = await fetchPedidoDetalle(pedido.numero, pedido.companyId);
      const nextOrigen = buildEstadoOrigen(detalle.info);
      const nextSanitario = buildEstadoSanitario(detalle.info);
      setEstadoOrigen(nextOrigen);
      setEstadoSanitario(nextSanitario);
      setEstadosContenedor((prev) => hidratarEstadosContenedor(detalle.contenedores, prev));
      setPedido((prev) =>
        prev
          ? {
              ...prev,
              pedidoInfo:          detalle.info,
              contenedoresDetalle: detalle.contenedores,
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
    setSeleccionados([]);
  }, []);

  const handleToggleSeleccion = useCallback((id: string) => {
    const gestionable =
      pedido?.contenedoresDetalle.find((c) => c.id === id)?.tiene_negocio_documento ?? false;
    if (!gestionable) return;
    setSeleccionados((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }, [pedido]);

  const handleSeleccionarTodos = useCallback(() => {
    setSeleccionados(
      pedido
        ? pedido.contenedoresDetalle
            .filter((c) => c.tiene_negocio_documento)
            .map((c) => c.id)
        : [],
    );
  }, [pedido]);

  const handleLimpiarSeleccion = useCallback(() => {
    setSeleccionados([]);
  }, []);

  const handleAgruparPorBooking = useCallback(() => {
    if (!pedido) return;
    const detalleById = new Map(pedido.contenedoresDetalle.map((c) => [c.id, c]));
    const bookingDe = (id: string): string | null => {
      const d = detalleById.get(id);
      return d ? bookingDeContenedor(d) : null;
    };

    setSeleccionados((prev) => {
      const bookingsSel = new Set(
        prev.map(bookingDe).filter((b): b is string => !!b),
      );
      if (bookingsSel.size === 0) {
        actions?.addAlert?.({
          type: "warning",
          title: "Agrupar por booking",
          message: "Los contenedores seleccionados no tienen nº de booking.",
        });
        return prev;
      }
      const expandido = pedido.contenedores
        .filter((c) => {
          const d = detalleById.get(c.id);
          if (!d?.tiene_negocio_documento) return false;
          const b = bookingDe(c.id);
          return !!b && bookingsSel.has(b);
        })
        .map((c) => c.id);
      actions?.addAlert?.({
        type: "success",
        title: "Embarque agrupado por booking",
        message: `${expandido.length} contenedor(es) con booking ${Array.from(bookingsSel).join(", ")}.`,
      });
      return expandido;
    });
  }, [pedido, actions]);

  // El BL se muestra para el contenedor de referencia (1º seleccionado) pero el
  // PATCH (en BLAccordion) escribe en TODOS los seleccionados, así que el estado
  // optimista se propaga a todos: la referencia toma 'next' completo y el resto el
  // diff de campos escalares (los ficheros se sincronizan por refetch). Calcular el
  // diff contra el estado actual hace que el revert (onChange(snapshot)) también
  // se propague correctamente.
  const handleChangeBL = useCallback((next: EstadoBL) => {
    const refId = seleccionados[0];
    if (!refId) return;
    setEstadosContenedor((prev) => {
      const refBL = (prev[refId] ?? initialEstadoContenedor()).bl;
      const changed: Partial<EstadoBL> = {};
      if (refBL.validadoLogistica !== next.validadoLogistica)
        changed.validadoLogistica = next.validadoLogistica;
      if (refBL.validadoAdministracion !== next.validadoAdministracion)
        changed.validadoAdministracion = next.validadoAdministracion;
      if (refBL.enviadoCliente !== next.enviadoCliente)
        changed.enviadoCliente = next.enviadoCliente;
      if (refBL.tipo !== next.tipo) changed.tipo = next.tipo;
      if (refBL.cambiosEnBL !== next.cambiosEnBL) changed.cambiosEnBL = next.cambiosEnBL;

      const out = { ...prev };
      for (const id of seleccionados) {
        const current = prev[id] ?? initialEstadoContenedor();
        out[id] = {
          ...current,
          bl: id === refId ? next : { ...current.bl, ...changed },
        };
      }
      return out;
    });
  }, [seleccionados]);

  // El envío/recepción afecta a TODOS los contenedores seleccionados: el diff se
  // calcula contra el contenedor de referencia (el que ven los controles) y se
  // aplica a cada contenedor del embarque.
  const handleChangeEntrega = useCallback(
    async (next: EstadoEntrega) => {
      const refId = seleccionados[0];
      if (!refId || !pedido) return;

      const refSnapshot = estadosContenedor[refId];
      const payload = buildEntregaDiff(refSnapshot?.entrega, next);

      // Campos camelCase que cambiaron (para el estado optimista de cada contenedor).
      const ref = refSnapshot?.entrega;
      const changed: Partial<EstadoEntrega> = {};
      if (!ref || ref.enviarPorMensajeria !== next.enviarPorMensajeria)
        changed.enviarPorMensajeria = next.enviarPorMensajeria;
      if (!ref || ref.permitirEnviar !== next.permitirEnviar)
        changed.permitirEnviar = next.permitirEnviar;
      if (!ref || ref.documentacionRecibida !== next.documentacionRecibida)
        changed.documentacionRecibida = next.documentacionRecibida;
      if (!ref || ref.mercanciaRetirada !== next.mercanciaRetirada)
        changed.mercanciaRetirada = next.mercanciaRetirada;
      if (!ref || ref.datosEnvioMensajeria !== next.datosEnvioMensajeria)
        changed.datosEnvioMensajeria = next.datosEnvioMensajeria;
      if (baseDateToIso(ref?.fechaLlegadaContenedor) !== baseDateToIso(next.fechaLlegadaContenedor))
        changed.fechaLlegadaContenedor = next.fechaLlegadaContenedor;
      if (baseDateToIso(ref?.fechaRetirada) !== baseDateToIso(next.fechaRetirada))
        changed.fechaRetirada = next.fechaRetirada;

      const objetivos = [...seleccionados];
      const prevSnapshots = new Map(objetivos.map((id) => [id, estadosContenedor[id]]));

      setEstadosContenedor((prev) => {
        const out = { ...prev };
        for (const id of objetivos) {
          const current = prev[id] ?? initialEstadoContenedor();
          out[id] = {
            ...current,
            // El de referencia toma 'next' completo; el resto, solo el diff de campos escalares.
            entrega: id === refId ? next : { ...current.entrega, ...changed },
          };
        }
        return out;
      });

      if (Object.keys(payload).length === 0) return;

      try {
        const resps = await Promise.all(
          objetivos.map((id) =>
            updateContenedorEntrega(pedido.numero, pedido.companyId, id, payload),
          ),
        );
        const fallo = resps.find((r) => !r.success);
        if (fallo) throw new Error(fallo.error ?? "Error guardando entrega");
        actions?.addAlert?.({
          type: "success",
          title: "Entrega actualizada",
          message:
            objetivos.length > 1
              ? `${describeEntregaPayload(payload)} en ${objetivos.length} contenedores`
              : describeEntregaPayload(payload),
        });
      } catch (e: any) {
        setEstadosContenedor((prev) => {
          const out = { ...prev };
          for (const id of objetivos) {
            const snap = prevSnapshots.get(id);
            if (snap) out[id] = snap;
          }
          return out;
        });
        actions?.addAlert?.({
          type: "danger",
          title: "Entrega — error",
          message: e?.message ?? "No se pudo guardar el cambio.",
        });
      }
    },
    [seleccionados, pedido, estadosContenedor, actions],
  );

  if (!pedido) {
    return (
      <Flex direction="column" gap="medium">
        <SelectorEmpresaPedido
          companyId={companyId}
          onCargarPedido={handleCargarPedido}
          pedidoNumero={selectorPedidoNumero}
          onPedidoNumeroChange={setSelectorPedidoNumero}
          pedidosCache={selectorPedidosCache}
          onPedidosLoaded={handlePedidosLoaded}
        />
      </Flex>
    );
  }

  // La selección por checkbox ES la gestión. El 1º seleccionado es la referencia
  // que conduce las etapas de documentos compartidas (BL, certificados, embarque);
  // el bloque de datos se repite por cada contenedor seleccionado.
  const refId = seleccionados[0] ?? null;

  const contenedorRef =
    refId !== null ? pedido.contenedores.find((c) => c.id === refId) ?? null : null;

  const contenedorRefDetalle =
    refId !== null ? pedido.contenedoresDetalle.find((c) => c.id === refId) ?? null : null;

  const estadoContenedor =
    refId !== null ? estadosContenedor[refId] ?? initialEstadoContenedor() : null;

  const contenedoresSeleccionadosDetalle = seleccionados
    .map((id) => pedido.contenedoresDetalle.find((c) => c.id === id))
    .filter((c): c is PedidoDetalleContenedor => !!c);

  // ¿Difieren los contenedores seleccionados en su estado de envío/recepción? Los
  // controles muestran el de referencia y el cambio se aplica a todos, así que si
  // divergen hay que avisar de que el bulk puede sobrescribir valores no vistos.
  const entregaDivergente = (() => {
    if (seleccionados.length < 2) return false;
    const claveEntrega = (id: string): string => {
      const e = (estadosContenedor[id] ?? initialEstadoContenedor()).entrega;
      return [
        e.enviarPorMensajeria,
        e.permitirEnviar,
        e.documentacionRecibida,
        e.mercanciaRetirada,
        e.datosEnvioMensajeria,
        baseDateToIso(e.fechaLlegadaContenedor),
        baseDateToIso(e.fechaRetirada),
      ].join("|");
    };
    const k0 = claveEntrega(seleccionados[0]);
    return seleccionados.slice(1).some((id) => claveEntrega(id) !== k0);
  })();

  // Requisitos de documentos = unión de los contenedores seleccionados (embarque).
  const documentosAGenerarContenedor = Array.from(
    new Set(contenedoresSeleccionadosDetalle.flatMap((c) => c.documentos_a_generar ?? [])),
  );

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
        tipoPedido={pedido.tipo_pedido}
        cargaPorPalets={pedido.carga_por_palets}
        seleccionados={seleccionados}
        onToggleSeleccion={handleToggleSeleccion}
        onSeleccionarTodos={handleSeleccionarTodos}
        onLimpiarSeleccion={handleLimpiarSeleccion}
        onAgruparPorBooking={handleAgruparPorBooking}
      />

      {contenedorRef && estadoContenedor && contenedorRefDetalle && (
        <Box>
          <DetalleContenedorPanel
            contenedor={contenedorRef}
            contenedorDetalle={contenedorRefDetalle}
            contenedoresSeleccionados={contenedoresSeleccionadosDetalle}
            numContenedoresPedido={pedido.contenedores.length}
            documentosAGenerar={documentosAGenerarContenedor}
            requiereBL={requiereBL}
            requiereOrigen={requiereOrigen}
            requiereSanitario={requiereSanitario}
            tipoPedido={pedido.tipo_pedido}
            fotosDeCarga={pedido.fotos_de_carga}
            estadoBL={estadoContenedor.bl}
            estadoOrigen={estadoOrigen}
            estadoSanitario={estadoSanitario}
            estadoContenedor={estadoContenedor}
            numeroPedido={pedido.numero}
            companyId={pedido.companyId}
            pedidoInfo={pedido.pedidoInfo}
            selectOptions={pedido.select_options}
            contenedorIdsDestino={seleccionados}
            entregaDivergente={entregaDivergente}
            onChangeBL={handleChangeBL}
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
