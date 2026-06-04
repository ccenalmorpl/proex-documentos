import React, { useState, useCallback } from "react";
import {
  Box,
  Flex,
  Heading,
  Text,
  Alert,
  Divider,
} from "@hubspot/ui-extensions";

import FiltrosDocumentos from "../components/FiltrosDocumentos";
import ContenedoresTable from "../components/ContenedoresTable";
import { fetchFromAPI } from "../utils/api.utils";
import { API_CONFIG } from "../config";
import {
  buildGeneratedPayload,
  buildRollbackPayload,
  type FiltrosState,
  type ContenedorItem,
  type BaseDate,
} from "../utils/documentos.utils";
import {
  DEFAULT_FILTROS,
  DOCUMENTOS_ERRORS,
  DOCUMENTOS_SUCCESS,
} from "../constants/documentos.constants";

interface DocumentosHistoricoTabProps {
  context: any;
  actions: any;
}

const DocumentosHistoricoTab: React.FC<DocumentosHistoricoTabProps> = ({
  context,
  actions,
}) => {
  const dealId: string = context?.crm?.objectId ?? "";

  const [filtros, setFiltros] = useState<FiltrosState>({ ...DEFAULT_FILTROS });
  const [contenedores, setContenedores] = useState<ContenedorItem[]>([]);

  const [loadingList, setLoadingList] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const handleFiltroChange = useCallback(
    (field: keyof FiltrosState, value: string | string[] | BaseDate | null) => {
      setFiltros((prev) => ({ ...prev, [field]: value }));
    },
    []
  );

  const handleApplyFiltros = useCallback(async () => {
    if (!dealId) {
      setError("No se encontró el ID del Deal en el contexto.");
      return;
    }
    setError(null);
    setSuccessMsg(null);
    setLoadingList(true);
    setHasSearched(true);
    try {
      const payload = buildGeneratedPayload(dealId, filtros);
      const response = await fetchFromAPI(API_CONFIG.endpoints.documentosGenerated, {
        method: "POST",
        body: payload,
      });
      setContenedores(response.contenedores ?? []);
    } catch (err: any) {
      setError(err.message ?? DOCUMENTOS_ERRORS.LOAD_GENERATED_ERROR);
    } finally {
      setLoadingList(false);
    }
  }, [dealId, filtros]);

  const handleRollback = useCallback(
    async (contenedor: ContenedorItem, docType: string) => {
      setError(null);
      setSuccessMsg(null);
      try {
        const docInfo = contenedor.docs.find((d) => d.doc_type === docType);
        const payload = buildRollbackPayload(
          contenedor.name,
          docType,
          docInfo?.group_id
        );
        await fetchFromAPI(API_CONFIG.endpoints.documentosRollback, {
          method: "POST",
          body: payload,
        });
        setSuccessMsg(DOCUMENTOS_SUCCESS.ROLLBACK);
        await handleApplyFiltros();
      } catch (err: any) {
        setError(err.message ?? DOCUMENTOS_ERRORS.ROLLBACK_ERROR);
      }
    },
    [handleApplyFiltros]
  );

  return (
    <Flex direction="column" gap="medium">

      <FiltrosDocumentos
        filtros={filtros}
        onChange={handleFiltroChange}
        onApply={handleApplyFiltros}
        loading={loadingList}
        docTypeTooltip="Selecciona los tipos de documento ya generados que deseas consultar o revertir."
        docTypeMicrocopy="Selecciona al menos un tipo. Se filtrarán contenedores que ya tengan ese documento generado."
      />

      <Divider />

      {error && (
        <Alert title="Error" variant="error">
          {error}
        </Alert>
      )}
      {successMsg && (
        <Alert title="Éxito" variant="success">
          {successMsg}
        </Alert>
      )}

      {hasSearched && (
        <Box>
          <Flex direction="column" gap="sm">
            <Heading>Documentos generados</Heading>
            <Text variant="microcopy">
              Contenedores con documentos ya generados. Haz clic en "Ver" para abrir el fichero o usa "Acciones" para revertir un documento.
            </Text>
            <ContenedoresTable
              contenedores={contenedores}
              loading={loadingList}
              mode="historico"
              onRollback={handleRollback}
              actions={actions}
              context={context}
            />
          </Flex>
        </Box>
      )}

    </Flex>
  );
};

export default DocumentosHistoricoTab;
