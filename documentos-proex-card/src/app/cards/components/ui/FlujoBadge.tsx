import React from "react";
import { Tag } from "@hubspot/ui-extensions";

import {
  FLUJO_LABELS,
  TIPO_PEDIDO_EXPORTACION,
  TIPO_PEDIDO_NACIONAL,
  TIPO_PEDIDO_NACIONAL_SAN_ROQUE,
  type TipoPedido,
} from "../../constants/documentos.constants";

interface FlujoBadgeProps {
  tipoPedido: TipoPedido;
}

const VARIANTS: Record<TipoPedido, "info" | "success"> = {
  [TIPO_PEDIDO_EXPORTACION]:        "info",
  [TIPO_PEDIDO_NACIONAL]:           "success",
  [TIPO_PEDIDO_NACIONAL_SAN_ROQUE]: "success",
};

export const FlujoBadge: React.FC<FlujoBadgeProps> = ({ tipoPedido }) => (
  <Tag variant={VARIANTS[tipoPedido]}>{FLUJO_LABELS[tipoPedido]}</Tag>
);

export default FlujoBadge;
