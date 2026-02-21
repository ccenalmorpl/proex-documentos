/**
 * ContenedoresTable — Tabla de contenedores reutilizable para Tab 1 y Tab 2.
 *
 * mode="pending"   → columna checkbox multi-select (Tab 1)
 * mode="historico" → columna acción BORRAR (Tab 2)
 */

import React from "react";
import {
  Box,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableHeader,
  TableCell,
  Button,
  Link,
  Text,
  LoadingSpinner,
  Flex,
  ToggleGroup,
} from "@hubspot/ui-extensions";

import type { ContenedorItem } from "../utils/documentos.utils";
import { formatDate, getDocTypeLabel } from "../utils/documentos.utils";

interface ContenedoresTableProps {
  contenedores: ContenedorItem[];
  loading?: boolean;
  mode: "pending" | "historico";
  // mode="pending"
  selectedIds?: string[];
  onToggleSelect?: (id: string) => void;
  // mode="historico"
  onRollback?: (contenedor: ContenedorItem, docType: string) => void;
}

const ContenedoresTable: React.FC<ContenedoresTableProps> = ({
  contenedores,
  loading = false,
  mode,
  selectedIds = [],
  onToggleSelect,
  onRollback,
}) => {
  if (loading) {
    return (
      <Flex direction="column" align="center" gap="medium">
        <LoadingSpinner size="md" />
        <Text>Cargando contenedores...</Text>
      </Flex>
    );
  }

  if (contenedores.length === 0) {
    return (
      <Box>
        <Text>No se encontraron contenedores con los filtros aplicados.</Text>
      </Box>
    );
  }

  return (
    <Table>
      <TableHead>
        <TableRow>
          {mode === "pending" && <TableHeader>Sel.</TableHeader>}
          <TableHeader>Contenedor</TableHeader>
          <TableHeader>Cliente</TableHeader>
          <TableHeader>F. Cotización</TableHeader>
          <TableHeader>F. Carga</TableHeader>
          <TableHeader>Documentos</TableHeader>
          {mode === "historico" && <TableHeader>Acción</TableHeader>}
        </TableRow>
      </TableHead>
      <TableBody>
        {contenedores.map((c) => (
          <TableRow key={c.id}>

            {/* Checkbox (solo Tab 1) */}
            {mode === "pending" && (
              <TableCell>
                <ToggleGroup
                  name={`select-${c.id}`}
                  toggleType="checkboxList"
                  options={[{ label: "", value: c.id }]}
                  value={selectedIds.includes(c.id) ? [c.id] : []}
                  onChange={() => onToggleSelect?.(c.id)}
                />
              </TableCell>
            )}

            <TableCell>{c.name}</TableCell>
            <TableCell>{c.nombre_cliente ?? "—"}</TableCell>
            <TableCell>{formatDate(c.fecha_cotizacion)}</TableCell>
            <TableCell>{formatDate(c.fecha_carga)}</TableCell>

            {/* Links a documentos */}
            <TableCell>
              <Flex direction="column" gap="extra-small">
                {c.docs.map((doc) =>
                  doc.file_url ? (
                    <Link key={doc.doc_type} href={doc.file_url} external>
                      {getDocTypeLabel(doc.doc_type)}
                    </Link>
                  ) : (
                    <Text key={doc.doc_type} format={{ color: "medium" }}>
                      {getDocTypeLabel(doc.doc_type)}: pendiente
                    </Text>
                  )
                )}
              </Flex>
            </TableCell>

            {/* Botón BORRAR por tipo de doc (solo Tab 2) */}
            {mode === "historico" && (
              <TableCell>
                <Flex direction="column" gap="extra-small">
                  {c.docs
                    .filter((d) => !!d.file_url)
                    .map((doc) => (
                      <Button
                        key={doc.doc_type}
                        variant="destructive"
                        size="xs"
                        onClick={() => onRollback?.(c, doc.doc_type)}
                      >
                        Borrar {getDocTypeLabel(doc.doc_type)}
                      </Button>
                    ))}
                </Flex>
              </TableCell>
            )}

          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};

export default ContenedoresTable;
