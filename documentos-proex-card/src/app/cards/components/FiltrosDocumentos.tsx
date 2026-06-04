import React from "react";
import {
  Box,
  Flex,
  Form,
  SearchInput,
  DateInput,
  ToggleGroup,
  Button,
  Heading,
  Text,
} from "@hubspot/ui-extensions";

import type { FiltrosState, BaseDate } from "../utils/documentos.utils";
import { DOC_TYPE_LABELS, ALL_DOC_TYPES } from "../constants/documentos.constants";

interface DocTypeOption {
  label: string;
  value: string;
}

interface FiltrosDocumentosProps {
  filtros: FiltrosState;
  onChange: (field: keyof FiltrosState, value: string | string[] | BaseDate | null) => void;
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
  const canApply =
    filtros.empresa.trim() !== "" && filtros.tipos_documento.length > 0;

  return (
    <Box>
      <Heading>Filtros</Heading>
      <Text variant="microcopy">
        Selecciona empresa y tipo de documento para buscar. Los campos marcados con * son obligatorios.
      </Text>
      <Form>
        <Flex direction="column" gap="small">

          <SearchInput
            label="Empresa (cliente)"
            name="empresa"
            value={filtros.empresa}
            onInput={(v: string) => onChange("empresa", v)}
            placeholder=""
            required
            description="Nombre (parcial o completo) de la empresa cliente asociada al contenedor."
            tooltip="Filtra por el nombre de la empresa. Admite búsqueda parcial (p. ej. 'Agro' encuentra 'Agroexport S.L.')."
          />

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

          <Flex direction="row" gap="small">
            <DateInput
              label="ETD — desde"
              name="etd_desde"
              value={filtros.etd_desde ?? undefined}
              onChange={(v) => onChange("etd_desde", v)}
              description="Opcional. Límite inicial del rango."
              tooltip="Estimated Time of Departure del contenedor. Filtra desde este día inclusive."
            />
            <DateInput
              label="ETD — hasta"
              name="etd_hasta"
              value={filtros.etd_hasta ?? undefined}
              onChange={(v) => onChange("etd_hasta", v)}
              description="Opcional. Límite final del rango."
              tooltip="Estimated Time of Departure del contenedor. Filtra hasta este día inclusive."
            />
          </Flex>

          <Flex direction="row" gap="small">
            <DateInput
              label="ETA — desde"
              name="eta_desde"
              value={filtros.eta_desde ?? undefined}
              onChange={(v) => onChange("eta_desde", v)}
              description="Opcional. Límite inicial del rango."
              tooltip="Estimated Time of Arrival del contenedor. Filtra desde este día inclusive."
            />
            <DateInput
              label="ETA — hasta"
              name="eta_hasta"
              value={filtros.eta_hasta ?? undefined}
              onChange={(v) => onChange("eta_hasta", v)}
              description="Opcional. Límite final del rango."
              tooltip="Estimated Time of Arrival del contenedor. Filtra hasta este día inclusive."
            />
          </Flex>

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
