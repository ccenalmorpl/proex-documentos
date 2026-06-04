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
  Heading,
  Flex,
  Tag,
} from "@hubspot/ui-extensions";

import {
  buildDocumentosContenedorResumen,
  calcularPorcentajePendiente,
  daysSince,
  daysUntil,
  formatDateES,
  formatPorcentaje,
  type ContenedorGestionItem,
  type PedidoDetalleContenedor,
  type PedidoDetalleInfo,
} from "../utils/documentos.utils";
import { isFlujoNacional, type TipoPedido } from "../constants/documentos.constants";

interface ContenedoresGestionTableProps {
  contenedores: ContenedorGestionItem[];
  contenedoresDetalle: PedidoDetalleContenedor[];
  pedidoInfo: PedidoDetalleInfo;
  fotosDeCarga: boolean;
  contenedorActivoId: string | null;
  tipoPedido: TipoPedido;
  cargaPorPalets: boolean;
  onSeleccionar: (id: string) => void;
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
  contenedorActivoId,
  tipoPedido,
  cargaPorPalets,
  onSeleccionar,
}) => {
  if (contenedores.length === 0) {
    return (
      <Box>
        <Text>El pedido no tiene contenedores cargados.</Text>
      </Box>
    );
  }

  const flujoNacional = isFlujoNacional(tipoPedido);
  const mostrarTaraVgm = !flujoNacional;
  const headerUnidad = flujoNacional ? "Camión" : "Contenedor";
  const labelNumero = flujoNacional ? "Nº camión" : "Nº contenedor";
  const labelIdentificador = flujoNacional ? "Matrícula" : "Precinto";
  const detalleById = new Map(contenedoresDetalle.map((c) => [c.id, c]));

  const diasFacturado = daysSince(pedidoInfo.fecha_de_facturacion_pedido);
  const diasVencimiento = daysUntil(pedidoInfo.fecha_de_vencimiento_factura);

  return (
    <Flex direction="column" gap="sm">
      <Heading>{flujoNacional ? "Camiones del pedido" : "Contenedores del pedido"}</Heading>
      <Table>
        <TableHead>
          <TableRow>
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
            const isActive = c.id === contenedorActivoId;
            const detalle = detalleById.get(c.id);
            const docs = detalle
              ? buildDocumentosContenedorResumen({
                  contenedor: detalle,
                  pedidoInfo,
                  tipoPedido,
                  fotosDeCarga,
                })
              : [];
            return (
              <TableRow key={c.id}>
                <TableCell>
                  <Flex direction="column" gap="extra-small">
                    <Text format={{ fontWeight: "demibold" }}>
                      {c.nombre ?? c.id}
                    </Text>
                    {!cargaPorPalets && detalle?.tipo_contenedor && (
                      <Text variant="microcopy">{detalle.tipo_contenedor}</Text>
                    )}
                    <Button
                      variant={isActive ? "primary" : "secondary"}
                      size="sm"
                      onClick={() => onSeleccionar(c.id)}
                    >
                      {isActive ? "En gestión" : "Gestionar"}
                    </Button>
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
