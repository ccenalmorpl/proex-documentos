import React from "react";
import {
  Box,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableHeader,
  TableCell,
  Text,
  Button,
  Checkbox,
  Heading,
  Flex,
  Tag,
} from "@hubspot/ui-extensions";

import {
  buildDocumentosContenedorResumen,
  bookingDeContenedor,
  calcularPorcentajePendiente,
  daysSince,
  daysUntil,
  formatDateES,
  formatPorcentaje,
  resumenEstadoDocFila,
  type ContenedorGestionItem,
  type PedidoDetalleContenedor,
  type PedidoDetalleInfo,
} from "../utils/documentos.utils";
import { esAparienciaCamion, type TipoPedido } from "../constants/documentos.constants";

interface ContenedoresGestionTableProps {
  contenedores: ContenedorGestionItem[];
  contenedoresDetalle: PedidoDetalleContenedor[];
  pedidoInfo: PedidoDetalleInfo;
  fotosDeCarga: boolean;
  tipoPedido: TipoPedido;
  cargaPorPalets: boolean;
  seleccionados: string[];
  onToggleSeleccion: (id: string) => void;
  onSeleccionarTodos: () => void;
  onLimpiarSeleccion: () => void;
  onAgruparPorBooking: () => void;
}

const isValor = (v: string | null | undefined): boolean =>
  !!v && String(v).trim() !== "" && String(v).trim() !== "—";

const Pendiente: React.FC = () => (
  <Text variant="microcopy">— pendiente —</Text>
);

const EstadoCobroTag: React.FC<{ detalle: PedidoDetalleContenedor | undefined }> = ({
  detalle,
}) => {
  if (!detalle) return <Tag>—</Tag>;
  const { porcentajePendiente, cobradoCompleto, precioDisponible } =
    calcularPorcentajePendiente(detalle.importe_pendiente_cobro, detalle.price);

  if (!precioDisponible) return <Tag>—</Tag>;
  if (cobradoCompleto) return <Tag variant="success">Cobrado 100%</Tag>;
  return <Tag variant="warning">{formatPorcentaje(porcentajePendiente)} pendiente</Tag>;
};

const EstadoSeguimientoTag: React.FC<{ detalle: PedidoDetalleContenedor | undefined }> = ({
  detalle,
}) => {
  if (!detalle) return <Tag>—</Tag>;
  if (detalle.mercancia_retirada) return <Tag variant="success">Retirado</Tag>;
  if (detalle.permitir_enviar_documentacion) return <Tag variant="info">Aprobado</Tag>;
  return <Tag variant="default">En proceso</Tag>;
};

const ContenedoresGestionTable: React.FC<ContenedoresGestionTableProps> = ({
  contenedores,
  contenedoresDetalle,
  pedidoInfo,
  fotosDeCarga,
  tipoPedido,
  cargaPorPalets,
  seleccionados,
  onToggleSeleccion,
  onSeleccionarTodos,
  onLimpiarSeleccion,
  onAgruparPorBooking,
}) => {
  if (contenedores.length === 0) {
    return (
      <Box>
        <Text>El pedido no tiene contenedores cargados.</Text>
      </Box>
    );
  }

  const esCamion = esAparienciaCamion(tipoPedido);
  const mostrarTaraVgm = !esCamion;
  const headerUnidad = esCamion ? "Camión" : "Contenedor";
  const labelNumero = esCamion ? "Nº camión" : "Nº contenedor";
  const labelIdentificador = esCamion ? "Matrícula" : "Precinto";
  const labelUnidadSing = esCamion ? "camión" : "contenedor";
  const detalleById = new Map(contenedoresDetalle.map((c) => [c.id, c]));
  const seleccionadosSet = new Set(seleccionados);
  const nSeleccionados = seleccionadosSet.size;
  const nGestionables = contenedores.filter(
    (c) => detalleById.get(c.id)?.tiene_negocio_documento,
  ).length;
  const todosSeleccionados = nGestionables > 0 && nSeleccionados >= nGestionables;

  const diasFacturado = daysSince(pedidoInfo.fecha_de_facturacion_pedido);
  const diasVencimiento = daysUntil(pedidoInfo.fecha_de_vencimiento_factura);

  return (
    <Flex direction="column" gap="sm">
      <Heading>{esCamion ? "Camiones del pedido" : "Contenedores del pedido"}</Heading>

      <Flex direction="row" gap="small" align="center" wrap="wrap">
        <Tag variant={nSeleccionados > 0 ? "info" : "default"}>
          {nSeleccionados} seleccionado{nSeleccionados === 1 ? "" : "s"}
        </Tag>
        <Button
          variant="secondary"
          size="xs"
          onClick={todosSeleccionados ? onLimpiarSeleccion : onSeleccionarTodos}
          disabled={nGestionables === 0}
        >
          {todosSeleccionados ? "Quitar selección" : "Seleccionar todos"}
        </Button>
        <Button
          variant="secondary"
          size="xs"
          onClick={onAgruparPorBooking}
          disabled={nSeleccionados === 0}
        >
          Agrupar por booking
        </Button>
        {nSeleccionados > 0 && !todosSeleccionados && (
          <Button variant="transparent" size="xs" onClick={onLimpiarSeleccion}>
            Limpiar
          </Button>
        )}
        <Text variant="microcopy">
          Marca los {labelUnidadSing}es que quieras gestionar: se abren juntos abajo y
          cada documento que subas se aplica a todos los marcados.
        </Text>
      </Flex>

      <Table>
        <TableHead>
          <TableRow>
            <TableHeader width={48}>Gestionar</TableHeader>
            <TableHeader width={120}>{headerUnidad}</TableHeader>
            <TableHeader width={200}>Identificación</TableHeader>
            <TableHeader width={160}>Pesos (kg)</TableHeader>
            <TableHeader width={180}>Estado</TableHeader>
            <TableHeader width={220}>Descripción mercancía</TableHeader>
            <TableHeader>Documentos</TableHeader>
          </TableRow>
        </TableHead>

        <TableBody>
          {contenedores.map((c) => {
            const detalle = detalleById.get(c.id);
            const gestionable = detalle?.tiene_negocio_documento ?? false;
            const isChecked = gestionable && seleccionadosSet.has(c.id);
            const docs = detalle
              ? buildDocumentosContenedorResumen({
                  contenedor: detalle,
                  pedidoInfo,
                  tipoPedido,
                  fotosDeCarga,
                })
              : [];
            const resumenFila = resumenEstadoDocFila(docs);
            const booking = detalle ? bookingDeContenedor(detalle) : null;
            return (
              <TableRow key={c.id}>
                <TableCell>
                  <Flex direction="column" gap="extra-small" align="start">
                    <Checkbox
                      checked={isChecked}
                      onChange={() => onToggleSeleccion(c.id)}
                      name={`sel_${c.id}`}
                      readOnly={!gestionable}
                    >
                      {""}
                    </Checkbox>
                    {gestionable ? (
                      isChecked && <Tag variant="info">En gestión</Tag>
                    ) : (
                      <Flex direction="column" gap="extra-small" align="start">
                        <Tag variant="default">En pedido</Tag>
                        <Text variant="microcopy">
                          Aún no ha completado el pedido
                        </Text>
                      </Flex>
                    )}
                  </Flex>
                </TableCell>

                <TableCell>
                  <Flex direction="column" gap="extra-small">
                    <Text format={{ fontWeight: "demibold" }}>
                      {c.nombre ?? c.id}
                    </Text>
                    {!cargaPorPalets && detalle?.tipo_contenedor && (
                      <Text variant="microcopy">{detalle.tipo_contenedor}</Text>
                    )}
                    <Tag variant={resumenFila.variant}>{resumenFila.label}</Tag>
                    {booking && (
                      <Text variant="microcopy">Booking: {booking}</Text>
                    )}
                    {detalle?.etd && (
                      <Text variant="microcopy">ETD: {formatDateES(detalle.etd)}</Text>
                    )}
                    {detalle?.eta && (
                      <Text variant="microcopy">ETA: {formatDateES(detalle.eta)}</Text>
                    )}
                  </Flex>
                </TableCell>

                <TableCell>
                  <Flex direction="column" gap="small">
                    <Flex direction="column" gap="extra-small">
                      <Text variant="microcopy" format={{ fontWeight: "demibold" }}>
                        {labelNumero}
                      </Text>
                      {isValor(c.numero) ? <Text>{c.numero}</Text> : <Pendiente />}
                    </Flex>
                    <Flex direction="column" gap="extra-small">
                      <Text variant="microcopy" format={{ fontWeight: "demibold" }}>
                        {labelIdentificador}
                      </Text>
                      {isValor(c.precinto) ? <Text>{c.precinto}</Text> : <Pendiente />}
                    </Flex>
                    {esCamion && isValor(detalle?.transitario_terrestre) ? (
                      <>
                        <Flex direction="column" gap="extra-small">
                          <Text variant="microcopy" format={{ fontWeight: "demibold" }}>
                            Transitario marítimo
                          </Text>
                          {isValor(detalle?.transitario) ? (
                            <Text>{detalle?.transitario}</Text>
                          ) : (
                            <Pendiente />
                          )}
                        </Flex>
                        <Flex direction="column" gap="extra-small">
                          <Text variant="microcopy" format={{ fontWeight: "demibold" }}>
                            Transitario terrestre
                          </Text>
                          <Text>{detalle?.transitario_terrestre}</Text>
                        </Flex>
                      </>
                    ) : isValor(detalle?.transitario) ? (
                      <Flex direction="column" gap="extra-small">
                        <Text variant="microcopy" format={{ fontWeight: "demibold" }}>
                          Transitario
                        </Text>
                        <Text>{detalle?.transitario}</Text>
                      </Flex>
                    ) : null}
                  </Flex>
                </TableCell>

                <TableCell>
                  <Flex direction="column" gap="small">
                    <Flex direction="column" gap="extra-small">
                      <Text variant="microcopy" format={{ fontWeight: "demibold" }}>
                        Bruto
                      </Text>
                      {isValor(c.peso_bruto) ? <Text>{c.peso_bruto}</Text> : <Pendiente />}
                    </Flex>
                    <Flex direction="column" gap="extra-small">
                      <Text variant="microcopy" format={{ fontWeight: "demibold" }}>
                        Neto
                      </Text>
                      {isValor(c.peso_neto) ? <Text>{c.peso_neto}</Text> : <Pendiente />}
                    </Flex>
                    {mostrarTaraVgm && (
                      <Flex direction="column" gap="extra-small">
                        <Text variant="microcopy" format={{ fontWeight: "demibold" }}>
                          Tara
                        </Text>
                        {isValor(c.tara) ? <Text>{c.tara}</Text> : <Pendiente />}
                        <Text variant="microcopy">
                          Peso VGM: {isValor(c.vgm) ? `${c.vgm} kg` : "—"}
                        </Text>
                      </Flex>
                    )}
                  </Flex>
                </TableCell>

                <TableCell>
                  <Flex direction="column" gap="small">
                    <Flex direction="column" gap="extra-small">
                      <Text variant="microcopy" format={{ fontWeight: "demibold" }}>
                        Pago
                      </Text>
                      <EstadoCobroTag detalle={detalle} />
                      {detalle?.numero_de_factura && (
                        <Text variant="microcopy">
                          Nº factura: {detalle.numero_de_factura}
                        </Text>
                      )}
                      {diasFacturado !== null && (
                        <Flex direction="column" gap="extra-small" align="start">
                          <Tag variant={diasFacturado >= 0 ? "default" : "warning"}>
                            {diasFacturado >= 0 ? "FACTURADO" : "Factura prevista"}
                          </Tag>
                          <Text variant="microcopy">
                            {formatDateES(pedidoInfo.fecha_de_facturacion_pedido)}
                          </Text>
                        </Flex>
                      )}
                      {diasVencimiento !== null && (
                        <Tag
                          variant={
                            diasVencimiento < 0
                              ? "error"
                              : diasVencimiento <= 7
                                ? "warning"
                                : "default"
                          }
                        >
                          {diasVencimiento < 0
                            ? `Vencida hace ${Math.abs(diasVencimiento)} d`
                            : `Vence en ${diasVencimiento} d`}
                        </Tag>
                      )}
                    </Flex>
                    <Flex direction="column" gap="extra-small">
                      <Text variant="microcopy" format={{ fontWeight: "demibold" }}>
                        Seguimiento
                      </Text>
                      <EstadoSeguimientoTag detalle={detalle} />
                    </Flex>
                  </Flex>
                </TableCell>

                <TableCell>
                  {isValor(c.descripcion_mercancia) ? (
                    <Flex direction="column" gap="extra-small">
                      {c.descripcion_mercancia.split("\n").map((linea, i) => (
                        <Text key={i}>{linea}</Text>
                      ))}
                    </Flex>
                  ) : (
                    <Pendiente />
                  )}
                </TableCell>

                <TableCell>
                  {docs.length === 0 ? (
                    <Text variant="microcopy">—</Text>
                  ) : (
                    <Flex direction="row" wrap="wrap" gap="extra-small">
                      {docs.map((d) => (
                        <Tag
                          key={d.key}
                          variant={d.generado ? "success" : "warning"}
                        >
                          {d.label}
                        </Tag>
                      ))}
                    </Flex>
                  )}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </Flex>
  );
};

export default ContenedoresGestionTable;
