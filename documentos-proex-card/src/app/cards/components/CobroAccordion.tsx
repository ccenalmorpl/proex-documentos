import React from "react";
import {
  Flex,
  Text,
  Alert,
  Tag,
  Statistics,
  StatisticsItem,
  StatisticsTrend,
  DescriptionList,
  DescriptionListItem,
} from "@hubspot/ui-extensions";

import { SeccionBloque, type EstadoEtapa } from "./ui/SeccionBloque";
import {
  calcularPorcentajePendiente,
  daysSince,
  daysUntil,
  formatDateES,
  formatImporte,
  formatPorcentaje,
} from "../utils/documentos.utils";

interface CobroAccordionProps {
  identificador?: string;
  price: string | null;
  importePendienteCobro: string | null;
  numeroFactura: string | null;
  fechaFacturacion: string | null;
  fechaVencimiento: string | null;
}

const CobroAccordion: React.FC<CobroAccordionProps> = ({
  identificador = "4",
  price,
  importePendienteCobro,
  numeroFactura,
  fechaFacturacion,
  fechaVencimiento,
}) => {
  const { precio, pendiente, porcentajePendiente, cobradoCompleto, precioDisponible } =
    calcularPorcentajePendiente(importePendienteCobro, price);

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
      titulo="Cobro del contenedor"
      estado={seccionEstado}
      destacada={precioDisponible && !cobradoCompleto}
      defaultAbierta={!cobradoCompleto}
      badge={badge}
    >
      <Flex direction="column" gap="md">
        {!precioDisponible && (
          <Alert title="Falta el precio del contenedor" variant="warning">
            <Text>
              No se puede calcular el porcentaje pendiente porque el contenedor no
              tiene el campo <Text inline format={{ fontWeight: "bold" }}>price</Text> informado
              en HubSpot.
            </Text>
          </Alert>
        )}

        <Statistics>
          <StatisticsItem label="Precio total" number={formatImporte(precio)} />
          <StatisticsItem label="Pendiente de cobro" number={formatImporte(pendiente)} />
          <StatisticsItem label="% pendiente" number={porcentajeNumber}>
            {porcentajeTrend}
          </StatisticsItem>
        </Statistics>

        {(numeroFactura || fechaFacturacion || fechaVencimiento) && (() => {
          const diasFacturado = daysSince(fechaFacturacion);
          const diasVencimiento = daysUntil(fechaVencimiento);
          return (
            <DescriptionList direction="row">
              {numeroFactura && (
                <DescriptionListItem label="Nº factura">
                  <Text>{numeroFactura}</Text>
                </DescriptionListItem>
              )}
              {fechaFacturacion && (
                <DescriptionListItem label="Fecha de facturación">
                  <Flex direction="column" gap="extra-small" align="start">
                    <Text>{formatDateES(fechaFacturacion) || "—"}</Text>
                    {diasFacturado !== null && (
                      <Tag variant={diasFacturado >= 0 ? "default" : "warning"}>
                        {diasFacturado >= 0
                          ? `Facturado hace ${diasFacturado} d`
                          : `Factura en ${Math.abs(diasFacturado)} d`}
                      </Tag>
                    )}
                  </Flex>
                </DescriptionListItem>
              )}
              {fechaVencimiento && (
                <DescriptionListItem label="Vencimiento de factura">
                  <Flex direction="column" gap="extra-small" align="start">
                    <Text>{formatDateES(fechaVencimiento) || "—"}</Text>
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
                </DescriptionListItem>
              )}
            </DescriptionList>
          );
        })()}

        <Alert title="Recordatorio sobre el cobro" variant="info">
          <Text>
            Para terminar de asignar dinero a este contenedor, usa el{" "}
            <Text inline format={{ fontWeight: "bold" }}>asistente de cobros</Text>.
            Hasta que no se cobre el 100% no debería enviarse la documentación al cliente.
          </Text>
        </Alert>
      </Flex>
    </SeccionBloque>
  );
};

export default CobroAccordion;
