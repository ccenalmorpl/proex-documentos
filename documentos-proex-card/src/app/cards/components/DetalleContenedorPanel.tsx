import React from "react";
import {
  Tile,
  Flex,
  Heading,
  Text,
  Alert,
  Tag,
} from "@hubspot/ui-extensions";

import { SeccionBloque, type EstadoEtapa } from "./ui/SeccionBloque";
import BLAccordion from "./BLAccordion";
import CertificadoStepper from "./CertificadoStepper";
import OtrosDocumentosSection from "./OtrosDocumentosSection";
import CobroAccordion from "./CobroAccordion";
import EnvioDocumentacionSection from "./EnvioDocumentacionSection";

import type {
  ContenedorGestionItem,
  EstadoBL,
  EstadoCertificado,
  EstadoContenedor,
  EstadoEntrega,
  PedidoDetalleContenedor,
  PedidoDetalleInfo,
  SelectOption,
} from "../utils/documentos.utils";
import { isFlujoNacional, type TipoPedido } from "../constants/documentos.constants";

interface DetalleContenedorPanelProps {
  contenedor: ContenedorGestionItem;
  numContenedoresPedido: number;
  documentosAGenerar: string[];
  requiereBL: boolean;
  requiereOrigen: boolean;
  requiereSanitario: boolean;
  tipoPedido: TipoPedido;
  fotosDeCarga: boolean;
  estadoBL: EstadoBL;
  estadoOrigen: EstadoCertificado;
  estadoSanitario: EstadoCertificado;
  estadoContenedor: EstadoContenedor;
  numeroPedido: string;
  companyId: string;
  pedidoInfo: PedidoDetalleInfo;
  contenedorDetalle: PedidoDetalleContenedor;
  selectOptions: Record<string, SelectOption[]>;
  actions: any;
  onChangeBL: (next: EstadoBL) => void;
  onUpdated: () => void | Promise<void>;
  onChangeOrigen: (next: EstadoCertificado) => void;
  onChangeSanitario: (next: EstadoCertificado) => void;
  onChangeEntrega: (next: EstadoEntrega) => void;
}

const DetalleContenedorPanel: React.FC<DetalleContenedorPanelProps> = ({
  contenedor,
  numContenedoresPedido,
  documentosAGenerar,
  requiereBL,
  requiereOrigen,
  requiereSanitario,
  tipoPedido,
  fotosDeCarga,
  estadoBL,
  estadoOrigen,
  estadoSanitario,
  estadoContenedor,
  numeroPedido,
  companyId,
  pedidoInfo,
  contenedorDetalle,
  selectOptions,
  actions,
  onChangeBL,
  onUpdated,
  onChangeOrigen,
  onChangeSanitario,
  onChangeEntrega,
}) => {
  const flujoNacional = isFlujoNacional(tipoPedido);

  const origenSellado    = !!estadoOrigen.sellado;
  const sanitarioSellado = !!estadoSanitario.sellado;
  const algunCertInicio  = !!estadoOrigen.borrador || !!estadoSanitario.borrador;
  const ambosSellados    = origenSellado && sanitarioSellado;

  const estadoCertificados: EstadoEtapa = ambosSellados
    ? "pasada"
    : algunCertInicio
      ? "actual"
      : "futura";

  const completados = (origenSellado ? 1 : 0) + (sanitarioSellado ? 1 : 0);
  const certBadge =
    completados === 2 ? (
      <Tag variant="success">2/2 sellados</Tag>
    ) : completados === 1 ? (
      <Tag variant="info">1/2 sellados</Tag>
    ) : algunCertInicio ? (
      <Tag variant="default">En progreso</Tag>
    ) : (
      <Tag variant="default">Sin iniciar</Tag>
    );

  const idOtros      = flujoNacional ? "1" : "3";
  const idCobro      = flujoNacional ? "2" : "4";
  const idEnvio      = flujoNacional ? "3" : "5";
  const idRecepcion  = flujoNacional ? "4" : "6";

  const cabecera = flujoNacional
    ? `Nº camión ${contenedor.numero} · Matrícula ${contenedor.precinto} · Bruto ${contenedor.peso_bruto} · Neto ${contenedor.peso_neto}`
    : `Nº contenedor ${contenedor.numero} · Precinto ${contenedor.precinto} · Bruto ${contenedor.peso_bruto} · Neto ${contenedor.peso_neto} · Tara ${contenedor.tara} · VGM ${contenedor.vgm}`;

  const tituloUnidad = flujoNacional ? "camión" : "contenedor";

  return (
    <Tile>
      <Flex direction="column" gap="medium">
        <Flex direction="column" gap="extra-small">
          <Heading>Documentación del {tituloUnidad} {contenedor.nombre}</Heading>
          <Text variant="microcopy">{cabecera}</Text>
        </Flex>

        {!flujoNacional && (
          <>
            <BLAccordion
              estado={estadoBL}
              numContenedores={numContenedoresPedido}
              numeroPedido={numeroPedido}
              companyId={companyId}
              selectOptions={selectOptions}
              actions={actions}
              onChange={onChangeBL}
              onUpdated={onUpdated}
              requerido={requiereBL}
            />

            {(() => {
              const requiereCertificados = requiereOrigen || requiereSanitario;
              return (
                <SeccionBloque
                  identificador="2"
                  titulo="Certificados (origen y sanitario)"
                  estado={requiereCertificados ? estadoCertificados : "pasada"}
                  defaultAbierta={requiereCertificados && estadoCertificados !== "pasada"}
                  badge={
                    requiereCertificados
                      ? certBadge
                      : <Tag variant="success">No requerido</Tag>
                  }
                >
                  {requiereCertificados ? (
                    <Flex direction="column" gap="small">
                      <Alert title="Información compartida con el pedido" variant="info">
                        Los certificados se gestionan a nivel de pedido. Los cambios aquí se aplican a los {numContenedoresPedido} contenedores.
                      </Alert>

                      <CertificadoStepper
                        titulo="Certificado de Origen"
                        tipoCertificado="origen"
                        estado={estadoOrigen}
                        numeroPedido={numeroPedido}
                        companyId={companyId}
                        actions={actions}
                        onChange={onChangeOrigen}
                        onUpdated={onUpdated}
                      />

                      <CertificadoStepper
                        titulo="Certificado Sanitario"
                        tipoCertificado="sanitario"
                        estado={estadoSanitario}
                        numeroPedido={numeroPedido}
                        companyId={companyId}
                        actions={actions}
                        onChange={onChangeSanitario}
                        onUpdated={onUpdated}
                      />
                    </Flex>
                  ) : (
                    <Text variant="microcopy">
                      Ningún contenedor del pedido requiere certificados de origen ni sanitario.
                    </Text>
                  )}
                </SeccionBloque>
              );
            })()}
          </>
        )}

        <OtrosDocumentosSection
          identificador={idOtros}
          titulo={flujoNacional ? "Documentos" : "Otros documentos"}
          numeroPedido={numeroPedido}
          companyId={companyId}
          contenedorId={contenedor.id}
          contenedorNombre={contenedor.nombre}
          documentosAGenerar={documentosAGenerar}
          pedidoInfo={pedidoInfo}
          fotosDeCarga={fotosDeCarga}
          estado={estadoContenedor.otrosDocs}
          actions={actions}
          onUpdated={onUpdated}
        />

        <CobroAccordion
          identificador={idCobro}
          price={contenedorDetalle.price}
          importePendienteCobro={contenedorDetalle.importe_pendiente_cobro}
          numeroFactura={pedidoInfo.numero_de_factura}
          fechaFacturacion={pedidoInfo.fecha_de_facturacion_pedido}
          fechaVencimiento={pedidoInfo.fecha_de_vencimiento_factura}
        />

        <EnvioDocumentacionSection
          estado={estadoContenedor.entrega}
          onChange={onChangeEntrega}
          pedidoInfo={pedidoInfo}
          contenedor={contenedorDetalle}
          fotosDeCarga={fotosDeCarga}
          tipoPedido={tipoPedido}
          identificadorEnvio={idEnvio}
          identificadorRecepcion={idRecepcion}
          actions={actions}
        />
      </Flex>
    </Tile>
  );
};

export default DetalleContenedorPanel;
