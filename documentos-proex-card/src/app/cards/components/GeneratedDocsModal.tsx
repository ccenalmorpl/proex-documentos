import React from "react";
import {
  Modal,
  ModalBody,
  ModalFooter,
  Flex,
  Text,
  Button,
  Link,
} from "@hubspot/ui-extensions";

import { getDocTypeLabel, type GeneratedDoc } from "../utils/documentos.utils";

interface GeneratedDocsModalProps {
  modalId: string;
  generatedDocs: GeneratedDoc[];
  onClose: () => void;
  actions: any;
}

const GeneratedDocsModal: React.FC<GeneratedDocsModalProps> = ({
  modalId,
  generatedDocs,
  onClose,
  actions,
}) => {
  const handleClose = () => {
    onClose();
    actions.closeOverlay(modalId);
  };

  return (
    <Modal id={modalId} title="Documentos generados" width="md">
      <ModalBody>
        <Flex direction="column" gap="small">
          <Text>
            {generatedDocs.length === 1
              ? "Se ha generado el siguiente documento:"
              : `Se han generado ${generatedDocs.length} documentos:`}
          </Text>
          {generatedDocs.map((doc) => (
            <Flex key={doc.doc_type} direction="row" gap="extra-small" alignItems="center">
              <Text format={{ fontWeight: "bold" }}>
                {getDocTypeLabel(doc.doc_type)}:
              </Text>
              <Link href={doc.file_url}>
                Abrir PDF
              </Link>
            </Flex>
          ))}
        </Flex>
      </ModalBody>
      <ModalFooter>
        <Flex direction="row" justify="end">
          <Button variant="primary" onClick={handleClose}>
            Cerrar
          </Button>
        </Flex>
      </ModalFooter>
    </Modal>
  );
};

export default GeneratedDocsModal;
