import React, { useState } from "react";
import { Box, Flex, Text, Divider, Button, Tag } from "@hubspot/ui-extensions";

export type EstadoEtapa = "actual" | "pasada" | "futura";

export type TagVariant =
  | "default"
  | "info"
  | "success"
  | "warning"
  | "error";

interface SeccionBloqueProps {
  identificador: string;
  titulo: string;
  children: React.ReactNode;
  estado?: EstadoEtapa;
  defaultAbierta?: boolean;
  bloqueada?: boolean;
  destacada?: boolean;
  badge?: React.ReactNode;
  tagVariantOverride?: TagVariant;
}

export const SeccionBloque: React.FC<SeccionBloqueProps> = ({
  identificador,
  titulo,
  children,
  estado,
  defaultAbierta,
  bloqueada = false,
  destacada = false,
  badge,
  tagVariantOverride,
}) => {
  const computedDefaultAbierta = defaultAbierta ?? false;
  const [abierta, setAbierta] = useState(computedDefaultAbierta);

  const tagVariantBase: TagVariant =
    estado === "actual"
      ? destacada
        ? "warning"
        : "info"
      : estado === "pasada"
        ? "success"
        : destacada
          ? "warning"
          : "default";
  const tagVariant = tagVariantOverride ?? tagVariantBase;

  return (
    <Box>
      <Flex direction="row" gap="small" justify={"end"} align={"end"}>
        <Box alignSelf="start">
          <Tag variant={tagVariant}>{identificador}</Tag>
        </Box>
        <Box alignSelf="start">
          <Text format={{ fontWeight: "bold" }} inline={true}>{titulo}</Text>
        </Box>
        <Box alignSelf="start" flex={1}>
          {badge && badge}
          {bloqueada && <Tag variant="error">Bloqueado</Tag>}
          {destacada && !bloqueada && estado !== "pasada" && <Tag variant="warning">Requiere atención</Tag>}
        </Box>
        <Box alignSelf="start">
          <Button
            variant="transparent"
            size="xs"
            onClick={() => setAbierta(!abierta)}
          >
            {abierta ? "Cerrar" : "Ver más"}
          </Button>
        </Box>
      </Flex>

      {abierta && (
        <Box>
          {children}
        </Box>
      )}
    <Divider />
    </Box>
  );
};

interface SubSeccionProps {
  titulo: string;
  children: React.ReactNode;
}

export const SubSeccion: React.FC<SubSeccionProps> = ({ titulo, children }) => (
  <Flex direction="column" gap="extra-small">
    <Text variant="microcopy">{titulo}</Text>
    {children}
  </Flex>
);
