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
import DatosUnidadEditable from "./DatosUnidadEditable";
import CertificadoStepper from "./CertificadoStepper";
import OtrosDocumentosSection from "./OtrosDocumentosSection";
import EmbarqueDocSection from "./EmbarqueDocSection";
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
import {
  esAparienciaCamion,
  EMBARQUE_DOC_TIPO_DUA,
  EMBARQUE_DOC_TIPOS_EXPORT,
  OTROS_DOC_LABELS,
  type TipoPedido,
} from "../constants/documentos.constants";

interface DetalleContenedorPanelProps {
  /** Contenedor de referencia (1º seleccionado): conduce las etapas de documentos. */
  contenedor: ContenedorGestionItem;
  /** Contenedores seleccionados (detalle): el bloque de datos se repite por cada uno. */
  contenedoresSeleccionados: PedidoDetalleContenedor[];
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
  /** Subconjunto del embarque seleccionado en la tabla; vacío = todo el pedido. */
  contenedorIdsDestino?: string[];
  /** Los seleccionados difieren en su estado de envío/recepción (para avisar del bulk). */
  entregaDivergente?: boolean;
  actions: any;
  onChangeBL: (next: EstadoBL) => void;
  onUpdated: () => void | Promise<void>;
  onChangeOrigen: (next: EstadoCertificado) => void;
  onChangeSanitario: (next: EstadoCertificado) => void;
  onChangeEntrega: (next: EstadoEntrega) => void;
}

const DetalleContenedorPanel: React.FC<DetalleContenedorPanelProps> = ({
  contenedor,
  contenedoresSeleccionados,
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
  contenedorIdsDestino,
  entregaDivergente,
  actions,
  onChangeBL,
  onUpdated,
  onChangeOrigen,
  onChangeSanitario,
  onChangeEntrega,
}) => {
  const esCamion = esAparienciaCamion(tipoPedido);
  const numSeleccionados = contenedoresSeleccionados.length;
  const tituloUnidadSingular = esCamion ? "camión" : "contenedor";
  const tituloUnidadPlural = esCamion ? "camiones" : "contenedores";
  const tituloUnidadCap = esCamion ? "Camión" : "Contenedor";
  const tituloPanel =
    numSeleccionados <= 1
      ? `Documentación del ${tituloUnidadSingular} ${contenedoresSeleccionados[0]?.nombre ?? contenedor.nombre ?? ""}`.trim()
      : `Documentación de ${numSeleccionados} ${tituloUnidadPlural}`;

  const origenSellado    = !!estadoOrigen.sellado;
  const sanitarioSellado = !!estadoSanitario.sellado;
  // El estado/badge de certificados cuenta SOLO los que el pedido requiere
  // (origen y/o sanitario): si solo se pide uno, el total es 1.
  const totalCertsReq    = (requiereOrigen ? 1 : 0) + (requiereSanitario ? 1 : 0);
  const certsSellados    =
    (requiereOrigen && origenSellado ? 1 : 0) +
    (requiereSanitario && sanitarioSellado ? 1 : 0);
  const algunCertInicio  =
    (requiereOrigen && !!estadoOrigen.borrador) ||
    (requiereSanitario && !!estadoSanitario.borrador);
  const todosCertsSellados = totalCertsReq > 0 && certsSellados === totalCertsReq;

  const estadoCertificados: EstadoEtapa = todosCertsSellados
    ? "pasada"
    : algunCertInicio
      ? "actual"
      : "futura";

  const certBadge =
    todosCertsSellados ? (
      <Tag variant="success">{`${certsSellados}/${totalCertsReq} sellados`}</Tag>
    ) : certsSellados >= 1 ? (
      <Tag variant="info">{`${certsSellados}/${totalCertsReq} sellados`}</Tag>
    ) : algunCertInicio ? (
      <Tag variant="default">En progreso</Tag>
    ) : (
      <Tag variant="default">Sin iniciar</Tag>
    );

  const idOtros      = esCamion ? "1" : "3";
  const idCobro      = esCamion ? "2" : "4";
  const idEnvio      = esCamion ? "3" : "5";
  const idRecepcion  = esCamion ? "4" : "6";

  const requiereDua = documentosAGenerar.includes(EMBARQUE_DOC_TIPO_DUA);

  // Hasta que administración apruebe el envío (etapa de Envío) ninguna etapa de
  // documentos debe enviarse al cliente: lo señalizamos en cada cabecera.
  const envioNoPermitido = !estadoContenedor.entrega.permitirEnviar;

  return (
    <Tile>
      <Flex direction="column" gap="medium">
        <Flex direction="column" gap="extra-small">
          <Heading>{tituloPanel}</Heading>
          {numSeleccionados > 1 && (
            <Text variant="microcopy">
              Editas los datos de cada {tituloUnidadSingular} por separado; los documentos
              que subas se aplican a los {numSeleccionados} {tituloUnidadPlural} seleccionados.
            </Text>
          )}
        </Flex>

        <Flex direction="column" gap="medium">
          {contenedoresSeleccionados.map((det) => (
            <Flex key={det.id} direction="column" gap="extra-small">
              {numSeleccionados > 1 && (
                <Text format={{ fontWeight: "demibold" }}>
                  {tituloUnidadCap} {det.nombre ?? det.id}
                </Text>
              )}
              <DatosUnidadEditable
                esCamion={esCamion}
                contenedor={det}
                numeroBooking={det.numero_de_booking ?? null}
                numeroPedido={numeroPedido}
                companyId={companyId}
                actions={actions}
                onUpdated={onUpdated}
              />
            </Flex>
          ))}
        </Flex>

        {!esCamion && (
          <>
            {requiereDua && (
              <EmbarqueDocSection
                identificador="0"
                titulo={OTROS_DOC_LABELS[EMBARQUE_DOC_TIPO_DUA]}
                tipoDocumento="doc_dua"
                archivo={estadoContenedor.otrosDocs.dua}
                requerido={requiereDua}
                numeroPedido={numeroPedido}
                companyId={companyId}
                contenedorId={contenedor.id}
                contenedorIdsDestino={contenedorIdsDestino}
                numContenedoresPedido={numContenedoresPedido}
                envioNoPermitido={envioNoPermitido}
                actions={actions}
                onUpdated={onUpdated}
              />
            )}

            {requiereBL && (
              <BLAccordion
                estado={estadoBL}
                numContenedores={numContenedoresPedido}
                numeroPedido={numeroPedido}
                companyId={companyId}
                selectOptions={selectOptions}
                contenedorIdsDestino={contenedorIdsDestino}
                envioNoPermitido={envioNoPermitido}
                actions={actions}
                onChange={onChangeBL}
                onUpdated={onUpdated}
                requerido={requiereBL}
              />
            )}

            {(requiereOrigen || requiereSanitario) && (
              <SeccionBloque
                identificador="2"
                titulo="Certificados (origen y sanitario)"
                estado={estadoCertificados}
                defaultAbierta={estadoCertificados !== "pasada"}
                envioNoPermitido={envioNoPermitido}
                badge={certBadge}
              >
                <Flex direction="column" gap="small">
                  <Alert title="Información compartida con el pedido" variant="info">
                    Los certificados se gestionan a nivel de pedido. Los cambios aquí se aplican a los {numContenedoresPedido} contenedores.
                  </Alert>

                  {requiereOrigen && (
                    <CertificadoStepper
                      titulo="Certificado de Origen"
                      tipoCertificado="origen"
                      estado={estadoOrigen}
                      numeroPedido={numeroPedido}
                      companyId={companyId}
                      contenedorIdsDestino={contenedorIdsDestino}
                      actions={actions}
                      onChange={onChangeOrigen}
                      onUpdated={onUpdated}
                    />
                  )}

                  {requiereSanitario && (
                    <CertificadoStepper
                      titulo="Certificado Sanitario"
                      tipoCertificado="sanitario"
                      estado={estadoSanitario}
                      numeroPedido={numeroPedido}
                      companyId={companyId}
                      contenedorIdsDestino={contenedorIdsDestino}
                      actions={actions}
                      onChange={onChangeSanitario}
                      onUpdated={onUpdated}
                    />
                  )}
                </Flex>
              </SeccionBloque>
            )}
          </>
        )}

        <OtrosDocumentosSection
          identificador={idOtros}
          titulo={esCamion ? "Documentos" : "Otros documentos"}
          numeroPedido={numeroPedido}
          companyId={companyId}
          contenedorId={contenedor.id}
          contenedorIdsDestino={contenedorIdsDestino}
          contenedorNombre={contenedor.nombre}
          contenedoresSeleccionados={contenedoresSeleccionados}
          documentosAGenerar={documentosAGenerar}
          pedidoInfo={pedidoInfo}
          fotosDeCarga={fotosDeCarga}
          estado={estadoContenedor.otrosDocs}
          tiposExcluidos={esCamion ? undefined : [...EMBARQUE_DOC_TIPOS_EXPORT]}
          envioNoPermitido={envioNoPermitido}
          actions={actions}
          onUpdated={onUpdated}
        />

        <CobroAccordion
          identificador={idCobro}
          contenedores={contenedoresSeleccionados}
          pedidoInfo={pedidoInfo}
          envioNoPermitido={envioNoPermitido}
        />

        <EnvioDocumentacionSection
          estado={estadoContenedor.entrega}
          onChange={onChangeEntrega}
          pedidoInfo={pedidoInfo}
          contenedor={contenedorDetalle}
          contenedoresSeleccionados={contenedoresSeleccionados}
          entregaDivergente={entregaDivergente}
          fotosDeCarga={fotosDeCarga}
          tipoPedido={tipoPedido}
          numeroPedido={numeroPedido}
          companyId={companyId}
          contenedorIdsDestino={contenedorIdsDestino}
          onUpdated={onUpdated}
          identificadorEnvio={idEnvio}
          identificadorRecepcion={idRecepcion}
          actions={actions}
        />
      </Flex>
    </Tile>
  );
};

export default DetalleContenedorPanel;
