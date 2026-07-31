import React from "react";
import {
  Flex,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableHeader,
  TableCell,
  Text,
  Alert,
  Tag,
  Statistics,
  StatisticsItem,
  StatisticsTrend,
} from "@hubspot/ui-extensions";

import { SeccionBloque, type EstadoEtapa } from "./ui/SeccionBloque";
import {
  acumularCobro,
  calcularPorcentajePendiente,
  daysUntil,
  formatDateES,
  formatImporte,
  formatPorcentaje,
  type PedidoDetalleContenedor,
  type PedidoDetalleInfo,
} from "../utils/documentos.utils";

interface CobroAccordionProps {
  identificador?: string;
  contenedores: PedidoDetalleContenedor[];
  pedidoInfo: PedidoDetalleInfo;
  /** Aún no se ha aprobado el envío de documentación al cliente. */
  envioNoPermitido?: boolean;
}

const VencimientoTag: React.FC<{ fecha: string | null }> = ({ fecha }) => {
  const dias = daysUntil(fecha);
  if (dias === null) return null;
  return (
    <Tag variant={dias < 0 ? "error" : dias <= 7 ? "warning" : "default"}>
      {dias < 0 ? `Vencida hace ${Math.abs(dias)} d` : `Vence en ${dias} d`}
    </Tag>
  );
};

const CobroAccordion: React.FC<CobroAccordionProps> = ({
  identificador = "4",
  contenedores,
  pedidoInfo,
  envioNoPermitido,
}) => {
  const {
    precioTotal,
    pendienteTotal,
    porcentajePendiente,
    cobradoCompleto,
    precioDisponible,
  } = acumularCobro(contenedores);

  const esMulti = contenedores.length > 1;
  const seccionEstado: EstadoEtapa = cobradoCompleto ? "pasada" : "actual";

  const badge = !precioDisponible ? (
    <Tag>Precio no informado</Tag>
  ) : cobradoCompleto ? (
    <Tag variant="success">Cobrado al 100%</Tag>
  ) : (
    <Tag variant="warning">Pendiente {formatPorcentaje(porcentajePendiente)}</Tag>
  );

  const porcentajeNumber = precioDisponible ? formatPorcentaje(porcentajePendiente) : "—";
  const porcentajeTrend = !precioDisponible ? null : cobradoCompleto ? (
    <StatisticsTrend direction="decrease" color="green" value="cobrado al 100%" />
  ) : (
    <StatisticsTrend direction="increase" color="red" value="por cobrar" />
  );

  return (
    <SeccionBloque
      identificador={identificador}
      titulo={esMulti ? "Cobro de los contenedores" : "Cobro del contenedor"}
      estado={seccionEstado}
      destacada={precioDisponible && !cobradoCompleto}
      defaultAbierta={!cobradoCompleto}
      envioNoPermitido={envioNoPermitido}
      badge={badge}
    >
      <Flex direction="column" gap="md">
        {!precioDisponible && (
          <Alert title="Falta el precio del contenedor" variant="warning">
            <Text>
              No se puede calcular el porcentaje pendiente porque{" "}
              {esMulti ? "los contenedores no tienen" : "el contenedor no tiene"} el campo{" "}
              <Text inline format={{ fontWeight: "bold" }}>price</Text> informado en HubSpot.
            </Text>
          </Alert>
        )}

        <Statistics>
          <StatisticsItem
            label={esMulti ? "Precio total (acumulado)" : "Precio total"}
            number={formatImporte(precioTotal)}
          />
          <StatisticsItem label="Pendiente de cobro" number={formatImporte(pendienteTotal)} />
          <StatisticsItem label="% pendiente" number={porcentajeNumber}>
            {porcentajeTrend}
          </StatisticsItem>
        </Statistics>

        <Table>
          <TableHead>
            <TableRow>
              <TableHeader width={140}>Contenedor</TableHeader>
              <TableHeader width={220}>Factura</TableHeader>
              <TableHeader>Importe</TableHeader>
            </TableRow>
          </TableHead>
          <TableBody>
            {contenedores.map((c) => {
              const { precio, pendiente, porcentajePendiente: pctFila, cobradoCompleto: cobradaFila, precioDisponible: precioFila } =
                calcularPorcentajePendiente(c.importe_pendiente_cobro, c.price);
              const numFactura = c.numero_de_factura ?? pedidoInfo.numero_de_factura;
              const fechaVto = c.fecha_de_vencimiento_factura ?? pedidoInfo.fecha_de_vencimiento_factura;
              return (
                <TableRow key={c.id}>
                  <TableCell>
                    <Text format={{ fontWeight: "demibold" }}>{c.nombre ?? c.id}</Text>
                  </TableCell>
                  <TableCell>
                    <Flex direction="column" gap="extra-small" align="start">
                      <Text variant="microcopy">
                        {numFactura ? `Nº ${numFactura}` : "Sin nº de factura"}
                      </Text>
                      {fechaVto && <Text variant="microcopy">Vto: {formatDateES(fechaVto)}</Text>}
                      <VencimientoTag fecha={fechaVto} />
                    </Flex>
                  </TableCell>
                  <TableCell>
                    <Flex direction="column" gap="extra-small" align="start">
                      <Text>{formatImporte(precio)}</Text>
                      <Text variant="microcopy">Pendiente: {formatImporte(pendiente)}</Text>
                      {precioFila ? (
                        <Tag variant={cobradaFila ? "success" : "warning"}>
                          {cobradaFila ? "Cobrado 100%" : `${formatPorcentaje(pctFila)} pendiente`}
                        </Tag>
                      ) : (
                        <Tag>Sin precio</Tag>
                      )}
                    </Flex>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>

        <Alert title="Recordatorio sobre el cobro" variant="info">
          <Text>
            Para terminar de asignar dinero a{" "}
            {esMulti ? "cada contenedor" : "este contenedor"}, usa el{" "}
            <Text inline format={{ fontWeight: "bold" }}>asistente de cobros</Text>.
            Hasta que no se cobre el 100% no debería enviarse la documentación al cliente.
          </Text>
        </Alert>
      </Flex>
    </SeccionBloque>
  );
};

export default CobroAccordion;
