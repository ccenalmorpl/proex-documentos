import React from "react";
import { Tag } from "@hubspot/ui-extensions";

import {
  FLUJO_LABELS,
  TIPO_PEDIDO_CONTENEDOR,
  TIPO_PEDIDO_CONTENEDOR_SAN_ROQUE,
  TIPO_PEDIDO_CAMION,
  TIPO_PEDIDO_CAMION_SAN_ROQUE,
  type TipoPedido,
} from "../../constants/documentos.constants";

interface FlujoBadgeProps {
  tipoPedido: TipoPedido;
}

const VARIANTS: Record<TipoPedido, "info" | "success"> = {
  [TIPO_PEDIDO_CONTENEDOR]:             "info",
  [TIPO_PEDIDO_CONTENEDOR_SAN_ROQUE]:  "info",
  [TIPO_PEDIDO_CAMION]:                "success",
  [TIPO_PEDIDO_CAMION_SAN_ROQUE]:      "success",
};

export const FlujoBadge: React.FC<FlujoBadgeProps> = ({ tipoPedido }) => (
  <Tag variant={VARIANTS[tipoPedido]}>{FLUJO_LABELS[tipoPedido]}</Tag>
);

export default FlujoBadge;
