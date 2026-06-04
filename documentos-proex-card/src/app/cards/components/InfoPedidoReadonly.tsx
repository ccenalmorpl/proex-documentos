import React from "react";
import {
  Tile,
  Flex,
  Heading,
  DescriptionList,
  DescriptionListItem,
  Box,
} from "@hubspot/ui-extensions";
import { CrmDataHighlight } from "@hubspot/ui-extensions/crm";

import { formatDateES, type PedidoInfo } from "../utils/documentos.utils";
import { isFlujoNacional, type TipoPedido } from "../constants/documentos.constants";
import FlujoBadge from "./ui/FlujoBadge";
import CargaPaletsBadge from "./ui/CargaPaletsBadge";

const COMPANY_HIGHLIGHT_PROPS = [
  "name",
  "cif",
  "tipo_cliente",
  "residennum",
  "phone",
  "credito_concedido",
];

interface InfoPedidoReadonlyProps {
  numeroPedido: string;
  companyId: string;
  info: PedidoInfo;
  tipoPedido: TipoPedido;
  cargaPorPalets: boolean;
}

const placeholder = (v: string | number | null | undefined): string => {
  if (v === null || v === undefined) return "—";
  const s = String(v).trim();
  return s === "" ? "—" : s;
};

const InfoPedidoReadonly: React.FC<InfoPedidoReadonlyProps> = ({
  numeroPedido,
  companyId,
  info,
  tipoPedido,
  cargaPorPalets,
}) => {
  const flujoNacional = isFlujoNacional(tipoPedido);
  const companyIdNum = Number(companyId);

  return (
    <Tile>
      <Flex direction="column" gap="small">
        <Flex direction="row" justify="between" align="center" gap="md" wrap="wrap">
          <Heading>Información del pedido {placeholder(numeroPedido).replace(/-/g, "‑")}</Heading>
          <Flex direction="row" gap="extra-small" align="center" wrap="wrap">
            <FlujoBadge tipoPedido={tipoPedido} />
            {cargaPorPalets && <CargaPaletsBadge />}
          </Flex>
        </Flex>

        {Number.isFinite(companyIdNum) && companyIdNum > 0 && (
          <CrmDataHighlight
            objectTypeId="0-2"
            objectId={companyIdNum}
            properties={COMPANY_HIGHLIGHT_PROPS}
          />
        )}

        {flujoNacional ? (
          <>
            <DescriptionList direction="row">
              <DescriptionListItem label="Fecha de entrega">
                {placeholder(formatDateES(info.fecha_de_entrega))}
              </DescriptionListItem>
              {cargaPorPalets ? (
                <DescriptionListItem label="Total cajas pedido">
                  {placeholder(info.total_cajas_pedido)}
                </DescriptionListItem>
              ) : (
                <DescriptionListItem label="Nº camiones">
                  {placeholder(info.numero_contenedores)}
                </DescriptionListItem>
              )}
              <DescriptionListItem label="Lugar de carga">
                {placeholder(info.lugar_carga)}
              </DescriptionListItem>
              <DescriptionListItem label="Localidad destino">
                {placeholder(info.localidad_destino)}
              </DescriptionListItem>
            </DescriptionList>

            <DescriptionList direction="row">
              <DescriptionListItem label="Dirección de entrega">
                {placeholder(info.direccion_de_entrega)}
              </DescriptionListItem>
              <DescriptionListItem label="Datos del chofer">
                {placeholder(info.datos_del_chofer)}
              </DescriptionListItem>
            </DescriptionList>

            <DescriptionList direction="row">
              <DescriptionListItem label="Comentarios de logística">
                {placeholder(info.comentarios_logistica)}
              </DescriptionListItem>
              <DescriptionListItem label="Descripción mercancía">
                {placeholder(info.descripcion_mercancia)}
              </DescriptionListItem>
            </DescriptionList>
          </>
        ) : (
          <>
            <DescriptionList direction="row">
              <DescriptionListItem label="ETD (salida)">
                {placeholder(formatDateES(info.etd))}
              </DescriptionListItem>
              <DescriptionListItem label="ETA (llegada)">
                {placeholder(formatDateES(info.eta))}
              </DescriptionListItem>
              <DescriptionListItem label="Nº contenedores">
                {placeholder(info.numero_contenedores)}
              </DescriptionListItem>
              <DescriptionListItem label="Puerto salida">
                {placeholder(info.puerto_salida)}
              </DescriptionListItem>
              <DescriptionListItem label="Puerto destino">
                {placeholder(info.puerto_destino)}
              </DescriptionListItem>
            </DescriptionList>

            <DescriptionList direction="row">
              <DescriptionListItem label="Consignee">
                {placeholder(info.consignee)}
              </DescriptionListItem>
              <DescriptionListItem label="Notify">
                {placeholder(info.notify)}
              </DescriptionListItem>
              <DescriptionListItem label="Descripción mercancía">
                {placeholder(info.descripcion_mercancia)}
              </DescriptionListItem>
            </DescriptionList>
          </>
        )}
      </Flex>
    </Tile>
  );
};

export default InfoPedidoReadonly;
