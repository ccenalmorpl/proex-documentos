/**
 * FiltrosDocumentos — Filtros SAP-like compartidos por Tab 1 y Tab 2.
 *
 * Props:
 *   filtros         Estado actual de los filtros
 *   onChange        Callback para actualizar un campo del filtro
 *   docTypeOptions  Opciones de checkboxes (pendientes o creados según el tab)
 *   onApply         Callback para ejecutar la búsqueda con los filtros actuales
 *   loading         Deshabilita el botón mientras hay una petición en curso
 */

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
  Divider,
} from "@hubspot/ui-extensions";

import type { FiltrosState } from "../utils/documentos.utils";
import { DOC_TYPE_LABELS, ALL_DOC_TYPES } from "../constants/documentos.constants";

interface DocTypeOption {
  label: string;
  value: string;
}

interface FiltrosDocumentosProps {
  filtros: FiltrosState;
  onChange: (field: keyof FiltrosState, value: string | string[]) => void;
  docTypeOptions?: DocTypeOption[];
  onApply: () => void;
  loading?: boolean;
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
}) => {
  return (
    <Box>
      <Heading>Filtros</Heading>
      <Divider />
      <Form>
        <Flex direction="column" gap="small">

          {/* Empresa / Cliente */}
          <SearchInput
            label="Empresa (cliente)"
            name="empresa"
            value={filtros.empresa}
            onInput={(v: string) => onChange("empresa", v)}
            placeholder="Buscar por nombre de empresa..."
          />

          {/* Rango fecha de carga */}
          <Flex direction="row" gap="small">
            <DateInput
              label="Fecha carga — desde"
              name="fecha_carga_desde"
              value={filtros.fecha_carga_desde}
              onChange={(v: string) => onChange("fecha_carga_desde", v)}
            />
            <DateInput
              label="Fecha carga — hasta"
              name="fecha_carga_hasta"
              value={filtros.fecha_carga_hasta}
              onChange={(v: string) => onChange("fecha_carga_hasta", v)}
            />
          </Flex>

          {/* Rango fecha creación cotización */}
          <Flex direction="row" gap="small">
            <DateInput
              label="Fecha cotización — desde"
              name="fecha_cotizacion_desde"
              value={filtros.fecha_cotizacion_desde}
              onChange={(v: string) => onChange("fecha_cotizacion_desde", v)}
            />
            <DateInput
              label="Fecha cotización — hasta"
              name="fecha_cotizacion_hasta"
              value={filtros.fecha_cotizacion_hasta}
              onChange={(v: string) => onChange("fecha_cotizacion_hasta", v)}
            />
          </Flex>

          {/* Tipos de documento */}
          <ToggleGroup
            label="Tipo de documento"
            name="tipos_documento"
            toggleType="checkboxList"
            options={docTypeOptions}
            value={filtros.tipos_documento}
            onChange={(values: string[]) => onChange("tipos_documento", values)}
          />

          {/* Aplicar filtros */}
          <Button
            variant="primary"
            onClick={onApply}
            disabled={loading}
          >
            {loading ? "Cargando..." : "Aplicar filtros"}
          </Button>

        </Flex>
      </Form>
    </Box>
  );
};

export default FiltrosDocumentos;
