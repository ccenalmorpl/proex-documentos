/**
 * DocumentosHistoricoTab — Tab 2
 *
 * Flujo:
 * 1. Usuario aplica filtros → POST /api/v1/documentos/generated
 * 2. Tabla muestra contenedores con docs generados
 * 3. Usuario pulsa BORRAR en un doc → se muestra ConfirmRollbackModal
 * 4. Confirma → POST /api/v1/documentos/rollback → refresca lista
 */

import React, { useState, useCallback } from "react";
import {
  Box,
  Flex,
  Heading,
  Alert,
  Divider,
} from "@hubspot/ui-extensions";

import FiltrosDocumentos from "../components/FiltrosDocumentos";
import ContenedoresTable from "../components/ContenedoresTable";
import ConfirmRollbackModal from "../components/ConfirmRollbackModal";
import { fetchFromAPI } from "../utils/api.utils";
import { API_CONFIG } from "../config";
import {
  buildGeneratedPayload,
  buildRollbackPayload,
  type FiltrosState,
  type ContenedorItem,
} from "../utils/documentos.utils";
import {
  DEFAULT_FILTROS,
  DOCUMENTOS_ERRORS,
  DOCUMENTOS_SUCCESS,
  DOCUMENTOS_LOADING,
} from "../constants/documentos.constants";

interface DocumentosHistoricoTabProps {
  context: any;
  actions: any;
}

interface RollbackTarget {
  contenedor: ContenedorItem;
  docType: string;
}

const DocumentosHistoricoTab: React.FC<DocumentosHistoricoTabProps> = ({
  context,
}) => {
  const dealId: string = context?.crm?.objectId ?? "";

  // ── Estado ───────────────────────────────────────────────────────────────
  const [filtros, setFiltros] = useState<FiltrosState>({ ...DEFAULT_FILTROS });
  const [contenedores, setContenedores] = useState<ContenedorItem[]>([]);
  const [rollbackTarget, setRollbackTarget] = useState<RollbackTarget | null>(null);

  const [loadingList, setLoadingList] = useState(false);
  const [loadingRollback, setLoadingRollback] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  // ── Handlers ─────────────────────────────────────────────────────────────

  const handleFiltroChange = useCallback(
    (field: keyof FiltrosState, value: string | string[]) => {
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
    setRollbackTarget(null);
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

  const handleRollbackRequest = useCallback(
    (contenedor: ContenedorItem, docType: string) => {
      setError(null);
      setSuccessMsg(null);
      setRollbackTarget({ contenedor, docType });
    },
    []
  );

  const handleRollbackConfirm = useCallback(async () => {
    if (!rollbackTarget) return;
    const { contenedor, docType } = rollbackTarget;

    // Obtener el group_generation_id si está disponible en el doc local
    const docInfo = contenedor.docs.find((d) => d.doc_type === docType);
    const groupId = docInfo?.group_generation_id;

    setLoadingRollback(true);
    try {
      const payload = buildRollbackPayload(contenedor.id, docType, groupId);
      await fetchFromAPI(API_CONFIG.endpoints.documentosRollback, {
        method: "POST",
        body: payload,
      });
      setSuccessMsg(DOCUMENTOS_SUCCESS.ROLLBACK);
      setRollbackTarget(null);
      // Refrescar lista
      await handleApplyFiltros();
    } catch (err: any) {
      setError(err.message ?? DOCUMENTOS_ERRORS.ROLLBACK_ERROR);
    } finally {
      setLoadingRollback(false);
    }
  }, [rollbackTarget, handleApplyFiltros]);

  const handleRollbackCancel = useCallback(() => {
    setRollbackTarget(null);
  }, []);

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <Flex direction="column" gap="medium">

      {/* Filtros */}
      <FiltrosDocumentos
        filtros={filtros}
        onChange={handleFiltroChange}
        onApply={handleApplyFiltros}
        loading={loadingList}
      />

      <Divider />

      {/* Alertas */}
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

      {/* Confirmación rollback (inline) */}
      {rollbackTarget && (
        <ConfirmRollbackModal
          contenedorName={rollbackTarget.contenedor.name}
          docType={rollbackTarget.docType}
          onConfirm={handleRollbackConfirm}
          onCancel={handleRollbackCancel}
          loading={loadingRollback}
        />
      )}

      {/* Tabla de histórico */}
      {hasSearched && (
        <Box>
          <Heading>Documentos generados</Heading>
          <ContenedoresTable
            contenedores={contenedores}
            loading={loadingList}
            mode="historico"
            onRollback={handleRollbackRequest}
          />
        </Box>
      )}

    </Flex>
  );
};

export default DocumentosHistoricoTab;
