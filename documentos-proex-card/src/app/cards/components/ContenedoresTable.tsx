import React, { useMemo } from "react";
import {
  Box,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableHeader,
  TableCell,
  Text,
  LoadingSpinner,
  Flex,
  ToggleGroup,
  Icon,
  Dropdown,
  Tooltip,
  Link,
} from "@hubspot/ui-extensions";

import type { ContenedorItem, DocInfo } from "../utils/documentos.utils";
import { formatDate } from "../utils/documentos.utils";
import ConfirmRollbackModal from "./ConfirmRollbackModal";

const DOC_COLUMNS: { docType: string; header: string }[] = [
  { docType: "origen_final",    header: "Cert. Origen" },
  { docType: "origen_borrador", header: "Cert. Origen Borrador" },
  { docType: "sanitario",       header: "Cert. Sanitario" },
];

interface ContenedoresTableProps {
  contenedores: ContenedorItem[];
  loading?: boolean;
  mode: "pending" | "historico";
  selectedIds?: string[];
  onToggleSelect?: (id: string) => void;
  onRollback?: (contenedor: ContenedorItem, docType: string) => void;
  actions?: any;
  context?: any;
}

const getDocInfo = (docs: DocInfo[], docType: string): DocInfo | undefined =>
  docs.find((d) => d.doc_type === docType);

const getAffectedCount = (
  all: ContenedorItem[],
  c: ContenedorItem,
  docType: string
): number => {
  const groupId = getDocInfo(c.docs, docType)?.group_id;
  if (!groupId) return 1;
  return all.filter(
    (other) => getDocInfo(other.docs, docType)?.group_id === groupId
  ).length;
};

const buildFileUrl = (fileValue: string, portalId: string | number): string =>
  fileValue.startsWith("http://") || fileValue.startsWith("https://")
    ? fileValue
    : `https://app.hubspot.com/file-preview/${portalId}/file/${fileValue}`;

const DOC_LABELS: Record<string, string> = {
  origen_borrador: "Origen Borrador",
  origen_final:    "Origen Final",
  sanitario:       "Sanitario",
};

const ContenedoresTable: React.FC<ContenedoresTableProps> = ({
  contenedores,
  loading = false,
  mode,
  selectedIds = [],
  onToggleSelect,
  onRollback,
  actions,
  context,
}) => {
  const sorted = useMemo(() => {
    return [...contenedores].sort((a, b) =>
      (a.name ?? "").localeCompare(b.name ?? "", undefined, { numeric: true, sensitivity: "base" })
    );
  }, [contenedores]);

  if (loading) {
    return (
      <Flex direction="column" align="center" gap="medium">
        <LoadingSpinner size="md" />
        <Text>Cargando contenedores...</Text>
      </Flex>
    );
  }

  if (sorted.length === 0) {
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
          {mode === "pending" && <TableHeader> </TableHeader>}
          <TableHeader>Contenedor</TableHeader>
          <TableHeader>Cliente</TableHeader>
          <TableHeader>Negocio</TableHeader>
          <TableHeader>ETD</TableHeader>
          <TableHeader>ETA</TableHeader>
          {DOC_COLUMNS.map((col) => (
            <TableHeader key={col.docType}>{col.header}</TableHeader>
          ))}
          {mode === "historico" && <TableHeader>Acciones</TableHeader>}
        </TableRow>
      </TableHead>

      <TableBody>
        {sorted.map((c) => (
          <TableRow key={c.id}>

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
            <TableCell>
              {c.deal_id ? (
                <Link
                  href={{
                    url: `https://app.hubspot.com/contacts/${context?.portal?.id ?? ""}/record/0-3/${c.deal_id}`,
                    external: true,
                  }}
                >
                  {c.deal_name || c.deal_id}
                </Link>
              ) : "—"}
            </TableCell>
            <TableCell>{formatDate(c.etd)}</TableCell>
            <TableCell>{formatDate(c.eta)}</TableCell>

            {DOC_COLUMNS.map((col) => {
              const info = getDocInfo(c.docs, col.docType);
              return (
                <TableCell key={col.docType}>
                  {info?.file_url ? (
                    <Link
                      href={{
                        url: buildFileUrl(info.file_url, context?.portal?.id ?? ""),
                        external: true,
                      }}
                    >
                      Ver
                    </Link>
                  ) : info?.required === false ? (
                    <Text>—</Text>
                  ) : (
                    <Icon name="remove" color="alert" size="sm" />
                  )}
                </TableCell>
              );
            })}

            {mode === "historico" && (
              <TableCell>
                <Dropdown
                  buttonText="Acciones"
                  variant="secondary"
                  buttonSize="sm"
                >
                  {DOC_COLUMNS.map((col) => {
                    const info = getDocInfo(c.docs, col.docType);
                    const generated = info?.generated ?? false;
                    const required = info?.required !== false;
                    const label = DOC_LABELS[col.docType] ?? col.docType;
                    const modalId = `rollback-${c.id}-${col.docType}`;

                    if (generated) {
                      return (
                        <Dropdown.ButtonItem
                          key={col.docType}
                          overlay={
                            <ConfirmRollbackModal
                              modalId={modalId}
                              contenedorName={c.name}
                              docType={col.docType}
                              affectedCount={getAffectedCount(contenedores, c, col.docType)}
                              onConfirm={() => onRollback?.(c, col.docType)}
                              actions={actions}
                            />
                          }
                        >
                          {`Borrar ${label}`}
                        </Dropdown.ButtonItem>
                      );
                    }

                    return (
                      <Dropdown.ButtonItem
                        key={col.docType}
                        overlay={
                          <Tooltip placement="right">
                            {required ? "No generado" : "No requerido"}
                          </Tooltip>
                        }
                      >
                        {required ? `${label} (no generado)` : `${label} (N/A)`}
                      </Dropdown.ButtonItem>
                    );
                  })}
                </Dropdown>
              </TableCell>
            )}

          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};

export default ContenedoresTable;
