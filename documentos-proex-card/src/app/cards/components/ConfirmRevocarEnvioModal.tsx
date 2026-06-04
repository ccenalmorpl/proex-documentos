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

import { type BaseDate } from "../utils/documentos.utils";

const formatBaseDateES = (d: BaseDate): string => {
  const day = String(d.date).padStart(2, "0");
  const month = String(d.month + 1).padStart(2, "0");
  return `${day}/${month}/${d.year}`;
};

interface ValoresAPerder {
  documentacionRecibida: boolean;
  fechaLlegadaContenedor: BaseDate | null;
  mercanciaRetirada: boolean;
  fechaRetirada: BaseDate | null;
}

interface ConfirmRevocarEnvioModalProps {
  modalId: string;
  valoresAPerder: ValoresAPerder;
  onConfirm: () => void;
  actions: any;
}

const ConfirmRevocarEnvioModal: React.FC<ConfirmRevocarEnvioModalProps> = ({
  modalId,
  valoresAPerder,
  onConfirm,
  actions,
}) => {
  const filas: string[] = [];
  if (valoresAPerder.documentacionRecibida) {
    filas.push("Documentación recibida por el cliente");
  }
  if (valoresAPerder.fechaLlegadaContenedor) {
    filas.push(
      `Fecha de envío de originales al cliente: ${formatBaseDateES(valoresAPerder.fechaLlegadaContenedor)}`,
    );
  }
  if (valoresAPerder.mercanciaRetirada) {
    filas.push("Mercancía retirada por el cliente");
  }
  if (valoresAPerder.fechaRetirada) {
    filas.push(`Fecha de retirada: ${formatBaseDateES(valoresAPerder.fechaRetirada)}`);
  }

  return (
    <Modal id={modalId} title="Revocar permiso de envío" variant="danger" width="md">
      <ModalBody>
        <Flex direction="column" gap="small">
          <Alert title="Se borrarán los siguientes datos de la etapa 6" variant="warning">
            Revocar el permiso de envío limpiará los campos guardados:
          </Alert>
          <Flex direction="column" gap="extra-small">
            {filas.map((f, i) => (
              <Text key={i}>• {f}</Text>
            ))}
          </Flex>
          <Text>Esta acción no se puede deshacer.</Text>
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
            Revocar y borrar
          </Button>
        </Flex>
      </ModalFooter>
    </Modal>
  );
};

export default ConfirmRevocarEnvioModal;
