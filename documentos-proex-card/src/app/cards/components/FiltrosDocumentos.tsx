import React from "react";
import {
  Box,
  Flex,
  Form,
  ToggleGroup,
  Button,
  Heading,
  Text,
} from "@hubspot/ui-extensions";

import type { FiltrosState } from "../utils/documentos.utils";
import { DOC_TYPE_LABELS, ALL_DOC_TYPES } from "../constants/documentos.constants";

interface DocTypeOption {
  label: string;
  value: string;
}

interface FiltrosDocumentosProps {
  filtros: FiltrosState;
  onChange: (field: keyof FiltrosState, value: string[]) => void;
  docTypeOptions?: DocTypeOption[];
  onApply: () => void;
  loading?: boolean;
  docTypeTooltip?: string;
  docTypeMicrocopy?: string;
}

const DEFAULT_DOC_OPTIONS: DocTypeOption[] = ALL_DOC_TYPES.map((t) => ({
  label: DOC_TYPE_LABELS[t],
  value: t,
}));

const FiltrosDocumentos: React.FC<FiltrosDocumentosProps> = ({
  filtros,
  onChange,
  docTypeOptions = DEFAULT_DOC_OPTIONS,
  onApply,
  loading = false,
  docTypeTooltip = "",
  docTypeMicrocopy = "Selecciona al menos un tipo.",
}) => {
  const canApply = filtros.tipos_documento.length > 0;

  return (
    <Box>
      <Heading>Filtros</Heading>
      <Text variant="microcopy">
        Selecciona el tipo de documento para buscar contenedores de esta empresa.
      </Text>
      <Form>
        <Flex direction="column" gap="small">

          <ToggleGroup
            label="Tipo de documento *"
            name="tipos_documento"
            toggleType="checkboxList"
            options={docTypeOptions}
            value={filtros.tipos_documento}
            onChange={(values: string[]) => onChange("tipos_documento", values)}
            tooltip={docTypeTooltip}
          />
          <Text variant="microcopy">{docTypeMicrocopy}</Text>

          <Button
            variant="primary"
            onClick={onApply}
            disabled={loading || !canApply}
          >
            {loading ? "Cargando..." : "Aplicar filtros"}
          </Button>

        </Flex>
      </Form>
    </Box>
  );
};

export default FiltrosDocumentos;
