/**
 * ConfirmRollbackModal — Bloque de confirmación inline para el rollback.
 *
 * HubSpot UI Extensions no tiene modal nativo; se usa renderizado condicional
 * dentro del tab. Este componente muestra el mensaje de advertencia y los
 * botones Confirmar / Cancelar.
 */

import React from "react";
import {
  Box,
  Flex,
  Text,
  Button,
  Heading,
  Alert,
} from "@hubspot/ui-extensions";

import { getDocTypeLabel } from "../utils/documentos.utils";

interface ConfirmRollbackModalProps {
  contenedorName: string;
  docType: string;
  affectedCount?: number;
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

const ConfirmRollbackModal: React.FC<ConfirmRollbackModalProps> = ({
  contenedorName,
  docType,
  affectedCount,
  onConfirm,
  onCancel,
  loading = false,
}) => {
  const docLabel = getDocTypeLabel(docType);

  return (
    <Box>
      <Alert title="Confirmar borrado" variant="warning">
        <Flex direction="column" gap="small">
          <Text>
            Vas a borrar el documento <Text format={{ fontWeight: "bold" }}>{docLabel}</Text>{" "}
            generado desde el contenedor <Text format={{ fontWeight: "bold" }}>{contenedorName}</Text>.
          </Text>
          {affectedCount !== undefined && affectedCount > 1 && (
            <Text>
              Este documento fue generado para un grupo de{" "}
              <Text format={{ fontWeight: "bold" }}>{affectedCount} contenedores</Text>.
              Se borrará en todos ellos.
            </Text>
          )}
          <Text>Esta acción no se puede deshacer.</Text>
          <Flex direction="row" gap="small">
            <Button
              variant="destructive"
              onClick={onConfirm}
              disabled={loading}
            >
              {loading ? "Borrando..." : "Confirmar borrado"}
            </Button>
            <Button
              variant="secondary"
              onClick={onCancel}
              disabled={loading}
            >
              Cancelar
            </Button>
          </Flex>
        </Flex>
      </Alert>
    </Box>
  );
};

export default ConfirmRollbackModal;
