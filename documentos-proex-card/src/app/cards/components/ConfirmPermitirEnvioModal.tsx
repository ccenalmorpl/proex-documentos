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

interface ConfirmPermitirEnvioModalProps {
  modalId: string;
  motivos: string[];
  onConfirm: () => void;
  actions: any;
}

const ConfirmPermitirEnvioModal: React.FC<ConfirmPermitirEnvioModalProps> = ({
  modalId,
  motivos,
  onConfirm,
  actions,
}) => (
  <Modal id={modalId} title="Permitir envío con etapas pendientes" variant="danger" width="md">
    <ModalBody>
      <Flex direction="column" gap="small">
        <Alert title="Hay etapas previas sin completar" variant="warning">
          Estás a punto de permitir el envío de documentación al cliente, pero:
        </Alert>
        <Flex direction="column" gap="extra-small">
          {motivos.map((m, i) => (
            <Text key={i}>• {m}</Text>
          ))}
        </Flex>
        <Text>¿Confirmas que quieres permitir el envío de todos modos?</Text>
      </Flex>
    </ModalBody>
    <ModalFooter>
      <Flex direction="row" gap="small" justify="end">
        <Button variant="secondary" onClick={() => actions.closeOverlay(modalId)}>
          Cancelar
        </Button>
        <Button
          variant="destructive"
          onClick={() => {
            onConfirm();
            actions.closeOverlay(modalId);
          }}
        >
          Permitir de todos modos
        </Button>
      </Flex>
    </ModalFooter>
  </Modal>
);

export default ConfirmPermitirEnvioModal;
