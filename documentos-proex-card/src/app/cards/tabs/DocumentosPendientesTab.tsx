/**
 * DocumentosPendientesTab — Tab 1
 *
 * Flujo:
 * 1. Usuario aplica filtros → POST /api/v1/documentos/pending
 * 2. Tabla muestra contenedores pendientes con multi-select
 * 3. Usuario selecciona contenedores + tipos → CTA "Generar documentos pendientes"
 * 4. POST /api/v1/documentos/generate → refresca lista
 */

import React, { useState, useCallback } from "react";
import {
  Box,
  Flex,
  Heading,
  Text,
  Button,
  Alert,
  Divider,
  ToggleGroup,
} from "@hubspot/ui-extensions";

import FiltrosDocumentos from "../components/FiltrosDocumentos";
import ContenedoresTable from "../components/ContenedoresTable";
import { fetchFromAPI } from "../utils/api.utils";
import { API_CONFIG } from "../config";
import {
  buildPendingPayload,
  buildGeneratePayload,
  type FiltrosState,
  type ContenedorItem,
} from "../utils/documentos.utils";
import {
  DEFAULT_FILTROS,
  DOC_TYPE_LABELS,
  ALL_DOC_TYPES,
  DOCUMENTOS_ERRORS,
  DOCUMENTOS_SUCCESS,
  DOCUMENTOS_LOADING,
} from "../constants/documentos.constants";

interface DocumentosPendientesTabProps {
  context: any;
  actions: any;
}

const DOC_TYPE_OPTIONS = ALL_DOC_TYPES.map((t) => ({
  label: DOC_TYPE_LABELS[t],
  value: t,
}));

const DocumentosPendientesTab: React.FC<DocumentosPendientesTabProps> = ({
  context,
}) => {
  const dealId: string = context?.crm?.objectId ?? "";

  // ── Estado ───────────────────────────────────────────────────────────────
  const [filtros, setFiltros] = useState<FiltrosState>({ ...DEFAULT_FILTROS });
  const [contenedores, setContenedores] = useState<ContenedorItem[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [selectedDocTypes, setSelectedDocTypes] = useState<string[]>([]);

  const [loadingList, setLoadingList] = useState(false);
  const [loadingGenerate, setLoadingGenerate] = useState(false);
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
    setSelectedIds([]);
    setLoadingList(true);
    setHasSearched(true);
    try {
      const payload = buildPendingPayload(dealId, filtros);
      const response = await fetchFromAPI(API_CONFIG.endpoints.documentosPending, {
        method: "POST",
        body: payload,
      });
      setContenedores(response.contenedores ?? []);
    } catch (err: any) {
      setError(err.message ?? DOCUMENTOS_ERRORS.LOAD_PENDING_ERROR);
    } finally {
      setLoadingList(false);
    }
  }, [dealId, filtros]);

  const handleToggleSelect = useCallback((id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  }, []);

  const handleGenerate = useCallback(async () => {
    if (selectedIds.length === 0) {
      setError(DOCUMENTOS_ERRORS.NO_CONTAINERS_SELECTED);
      return;
    }
    if (selectedDocTypes.length === 0) {
      setError(DOCUMENTOS_ERRORS.NO_DOC_TYPES_SELECTED);
      return;
    }
    setError(null);
    setSuccessMsg(null);
    setLoadingGenerate(true);
    try {
      const payload = buildGeneratePayload(dealId, selectedIds, selectedDocTypes);
      await fetchFromAPI(API_CONFIG.endpoints.documentosGenerate, {
        method: "POST",
        body: payload,
      });
      setSuccessMsg(DOCUMENTOS_SUCCESS.GENERATED);
      setSelectedIds([]);
      // Refrescar la lista automáticamente
      await handleApplyFiltros();
    } catch (err: any) {
      setError(err.message ?? DOCUMENTOS_ERRORS.GENERATE_ERROR);
    } finally {
      setLoadingGenerate(false);
    }
  }, [dealId, selectedIds, selectedDocTypes, handleApplyFiltros]);

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

      {/* Tabla de contenedores pendientes */}
      {hasSearched && (
        <Box>
          <Heading>Contenedores pendientes</Heading>
          <ContenedoresTable
            contenedores={contenedores}
            loading={loadingList}
            mode="pending"
            selectedIds={selectedIds}
            onToggleSelect={handleToggleSelect}
          />
        </Box>
      )}

      {/* Selección de tipos + CTA Generar */}
      {contenedores.length > 0 && (
        <Box>
          <Divider />
          <Flex direction="column" gap="small">
            <Heading>Tipos de documento a generar</Heading>
            <ToggleGroup
              name="doc-types-to-generate"
              toggleType="checkboxList"
              label="Selecciona los tipos"
              options={DOC_TYPE_OPTIONS}
              value={selectedDocTypes}
              onChange={(values: string[]) => setSelectedDocTypes(values)}
            />
            <Button
              variant="primary"
              onClick={handleGenerate}
              disabled={loadingGenerate || selectedIds.length === 0 || selectedDocTypes.length === 0}
            >
              {loadingGenerate
                ? DOCUMENTOS_LOADING.GENERATING
                : `Generar documentos pendientes (${selectedIds.length} contenedor${selectedIds.length !== 1 ? "es" : ""})`}
            </Button>
          </Flex>
        </Box>
      )}

    </Flex>
  );
};

export default DocumentosPendientesTab;
