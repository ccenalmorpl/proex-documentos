import React from "react";
import {
  Modal,
  ModalBody,
  ModalFooter,
  Flex,
  Text,
  Button,
  Alert,
} from "@hubspot/ui-extensions";

import { getDocTypeLabel } from "../utils/documentos.utils";

interface ConfirmRollbackModalProps {
  modalId: string;
  contenedorName: string;
  docType: string;
  affectedCount: number;
  onConfirm: () => void;
  actions: any;
}

const ConfirmRollbackModal: React.FC<ConfirmRollbackModalProps> = ({
  modalId,
  contenedorName,
  docType,
  affectedCount,
  onConfirm,
  actions,
}) => {
  const docLabel = getDocTypeLabel(docType);

  return (
    <Modal id={modalId} title="Confirmar borrado" variant="danger" width="sm">
      <ModalBody>
        <Flex direction="column" gap="small">
          <Flex direction="row" gap="extra-small">
            <Text>Documento:</Text>
            <Text format={{ fontWeight: "bold" }}>{docLabel}</Text>
          </Flex>
          <Flex direction="row" gap="extra-small">
            <Text>Contenedor:</Text>
            <Text format={{ fontWeight: "bold" }}>{contenedorName}</Text>
          </Flex>
          {affectedCount > 1 && (
            <Alert title={`Este rollback afectará a ${affectedCount} contenedores`} variant="warning">
              Todos los contenedores generados en el mismo lote perderán este documento.
            </Alert>
          )}
          <Text>Esta acción no se puede deshacer.</Text>
        </Flex>
      </ModalBody>
      <ModalFooter>
        <Flex direction="row" gap="small" justify="end">
          <Button
            variant="secondary"
            onClick={() => actions.closeOverlay(modalId)}
          >
            Cancelar
          </Button>
          <Button
            variant="destructive"
            onClick={() => {
              onConfirm();
              actions.closeOverlay(modalId);
            }}
          >
            Borrar
          </Button>
        </Flex>
      </ModalFooter>
    </Modal>
  );
};

export default ConfirmRollbackModal;
