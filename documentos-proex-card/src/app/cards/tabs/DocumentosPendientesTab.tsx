import React, { useState, useCallback, useEffect } from "react";
import {
  Box,
  Flex,
  Heading,
  Text,
  Button,
  Alert,
  Divider,
  ToggleGroup,
  Link,
  Tile,
  TextArea,
} from "@hubspot/ui-extensions";
import { CrmDataHighlight } from "@hubspot/ui-extensions/crm";

import FiltrosDocumentos from "../components/FiltrosDocumentos";
import ContenedoresTable from "../components/ContenedoresTable";
import { fetchFromAPI } from "../utils/api.utils";
import { API_CONFIG } from "../config";
import {
  buildPendingPayload,
  buildGeneratePayload,
  getDocTypeLabel,
  type FiltrosState,
  type ContenedorItem,
  type GeneratedDoc,
} from "../utils/documentos.utils";
import {
  DEFAULT_FILTROS,
  COMPANY_HIGHLIGHT_PROPS,
  DOC_TYPE_LABELS,
  ALL_DOC_TYPES,
  DOCUMENTOS_ERRORS,
  DOCUMENTOS_LOADING,
  IDIOMA_OPTIONS,
  DEFAULT_IDIOMA,
  type Idioma,
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
  const companyId: string = context?.crm?.objectId ?? "";

  const [filtros, setFiltros] = useState<FiltrosState>({ ...DEFAULT_FILTROS });
  const [contenedores, setContenedores] = useState<ContenedorItem[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [selectedDocTypes, setSelectedDocTypes] = useState<string[]>([]);

  const [loadingList, setLoadingList] = useState(false);
  const [loadingGenerate, setLoadingGenerate] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const [descripcionMercancia, setDescripcionMercancia] = useState<string>("");
  const [observaciones, setObservaciones] = useState<string>("");

  const [idiomaDeal, setIdiomaDeal] = useState<Idioma>(DEFAULT_IDIOMA);
  const [idioma, setIdioma] = useState<Idioma>(DEFAULT_IDIOMA);

  useEffect(() => {
    if (!companyId) return;
    let cancelled = false;
    (async () => {
      try {
        const resp = (await fetchFromAPI(
          API_CONFIG.endpoints.documentosDealContext(companyId),
        )) as { preprints_language?: Idioma | null };
        if (cancelled) return;
        const lang = resp?.preprints_language;
        if (lang === "ES" || lang === "EN" || lang === "FR") {
          setIdiomaDeal(lang);
          setIdioma(lang);
        }
      } catch {
        // Si falla, mantenemos DEFAULT_IDIOMA. La precarga es best-effort.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [companyId]);

  useEffect(() => {
    if (selectedIds.length === 0) {
      setDescripcionMercancia("");
      setObservaciones("");
      return;
    }
    const selected = contenedores.filter((c) => selectedIds.includes(c.id));
    const descripciones = [
      ...new Set(
        selected
          .map((c) => (c.deal_properties?.certificado_origen_mercancia ?? "").trim())
          .filter(Boolean)
      ),
    ].join("\n");
    const obs = [
      ...new Set(
        selected
          .map((c) => (c.deal_properties?.observaciones ?? "").trim())
          .filter(Boolean)
      ),
    ].join("\n");
    setDescripcionMercancia(descripciones);
    setObservaciones(obs);
  }, [selectedIds, contenedores]);

  const [generatedDocs, setGeneratedDocs] = useState<GeneratedDoc[]>([]);

  const conflictLines: string[] = selectedIds.flatMap((id) => {
    const c = contenedores.find((x) => x.id === id);
    if (!c) return [];
    return c.docs
      .filter((d) => selectedDocTypes.includes(d.doc_type) && d.generated)
      .map((d) => `${c.name} — ${getDocTypeLabel(d.doc_type)}`);
  });
  const hasConflict = conflictLines.length > 0;

  const notRequiredLines: string[] = selectedIds.flatMap((id) => {
    const c = contenedores.find((x) => x.id === id);
    if (!c) return [];
    return c.docs
      .filter((d) => selectedDocTypes.includes(d.doc_type) && d.required === false)
      .map((d) => `${c.name} — ${getDocTypeLabel(d.doc_type)}`);
  });
  const hasNotRequired = notRequiredLines.length > 0;

  const handleFiltroChange = useCallback(
    (field: keyof FiltrosState, value: string[]) => {
      setFiltros((prev) => ({ ...prev, [field]: value }));
    },
    []
  );

  const handleApplyFiltros = useCallback(async () => {
    if (!companyId) {
      setError("No se encontró la empresa en el contexto de la card.");
      return;
    }
    setError(null);
    setSelectedIds([]);
    setGeneratedDocs([]);
    setLoadingList(true);
    setHasSearched(true);
    try {
      const payload = buildPendingPayload(companyId, filtros);
      const response = await fetchFromAPI(API_CONFIG.endpoints.documentosPending, {
        method: "POST",
        body: payload,
      });
      const items = (response as any).contenedores ?? [];
      setContenedores(items);

      const rawLang = (items[0]?.deal_properties?.preprints_language ?? "").toUpperCase();
      if (rawLang === "ES" || rawLang === "EN" || rawLang === "FR") {
        setIdiomaDeal(rawLang as Idioma);
        setIdioma(rawLang as Idioma);
      }
    } catch (err: any) {
      setError(err.message ?? DOCUMENTOS_ERRORS.LOAD_PENDING_ERROR);
    } finally {
      setLoadingList(false);
    }
  }, [companyId, filtros]);

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
    setLoadingGenerate(true);
    try {
      const payload = buildGeneratePayload(companyId, selectedIds, selectedDocTypes, descripcionMercancia || undefined, observaciones || undefined, idioma);
      const response = await fetchFromAPI(API_CONFIG.endpoints.documentosGenerate, {
        method: "POST",
        body: payload,
      });
      setGeneratedDocs((response as any).generated_docs ?? []);
    } catch (err: any) {
      setError(err.message ?? DOCUMENTOS_ERRORS.GENERATE_ERROR);
    } finally {
      setLoadingGenerate(false);
    }
  }, [companyId, selectedIds, selectedDocTypes, descripcionMercancia, observaciones, idioma]);

  const handleNuevaGeneracion = useCallback(() => {
    setFiltros({ ...DEFAULT_FILTROS });
    setContenedores([]);
    setSelectedIds([]);
    setSelectedDocTypes([]);
    setIdioma(idiomaDeal);
    setHasSearched(false);
    setGeneratedDocs([]);
    setDescripcionMercancia("");
    setObservaciones("");
    setError(null);
  }, [idiomaDeal]);

  if (generatedDocs.length > 0) {
    return (
      <Flex direction="column" gap="medium">
        <Tile>
          <Flex direction="column" gap="small">
            <Heading>Documentos generados</Heading>
            {generatedDocs.map((doc) => (
              <Flex key={doc.doc_type} direction="row" gap="extra-small">
                <Text format={{ fontWeight: "bold" }}>
                  {getDocTypeLabel(doc.doc_type)}:
                </Text>
                <Link href={doc.file_url}>Abrir PDF</Link>
              </Flex>
            ))}
          </Flex>
        </Tile>
        <Button variant="secondary" onClick={handleNuevaGeneracion}>
          Nueva generación
        </Button>
      </Flex>
    );
  }

  return (
    <Flex direction="column" gap="medium">

      {companyId && (
        <CrmDataHighlight properties={COMPANY_HIGHLIGHT_PROPS} />
      )}

      <FiltrosDocumentos
        filtros={filtros}
        onChange={handleFiltroChange}
        onApply={handleApplyFiltros}
        loading={loadingList}
        docTypeTooltip="Selecciona los tipos de documento que deseas generar. Solo se mostrarán contenedores que aún no los tengan generados."
        docTypeMicrocopy="Se mostrarán contenedores que requieran y tengan pendiente al menos uno de los tipos seleccionados."
      />

      <Divider />

      {error && (
        <Alert title="Error" variant="error">
          {error}
        </Alert>
      )}

      {hasSearched && (
        <Box>
          <Flex direction="column" gap="sm">
            <Heading>Contenedores pendientes</Heading>
            <ContenedoresTable
              contenedores={contenedores}
              loading={loadingList}
              mode="pending"
              selectedIds={selectedIds}
              onToggleSelect={handleToggleSelect}
              context={context}
            />
          </Flex>
        </Box>
      )}

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
            {selectedDocTypes.length > 0 && (
              <ToggleGroup
                name="idioma-selector"
                toggleType="radioButtonList"
                label="Idioma del certificado"
                options={IDIOMA_OPTIONS}
                value={idioma}
                onChange={(value: string) => setIdioma(value as Idioma)}
              />
            )}
            {(selectedDocTypes.includes("origen_borrador") ||
              selectedDocTypes.includes("origen_final")) && (
              <TextArea
                label="Descripción de Mercancía"
                name="descripcion_mercancia"
                description="Pre-relleno desde la cotización. Editable antes de generar."
                rows={4}
                value={descripcionMercancia}
                onChange={(value: string) => setDescripcionMercancia(value)}
              />
            )}
            {(selectedDocTypes.includes("origen_borrador") || selectedDocTypes.includes("origen_final")) && (
              <TextArea
                label="Certificado de Origen - Observaciones"
                name="observaciones"
                description="Pre-relleno desde la cotización. Editable antes de generar."
                rows={3}
                value={observaciones}
                onChange={(value: string) => setObservaciones(value)}
              />
            )}
            {hasConflict && (
              <Alert title="Documentos ya generados" variant="warning">
                <Flex direction="column" gap="extra-small">
                  <Text>Los siguientes contenedores ya tienen ese documento:</Text>
                  {conflictLines.map((line) => (
                    <Text key={line} format={{ fontWeight: "bold" }}>{line}</Text>
                  ))}
                </Flex>
              </Alert>
            )}
            {hasNotRequired && (
              <Alert title="Documentos no requeridos" variant="warning">
                <Flex direction="column" gap="extra-small">
                  <Text>Los siguientes contenedores no requieren los documentos seleccionados:</Text>
                  {notRequiredLines.map((line) => (
                    <Text key={line} format={{ fontWeight: "bold" }}>{line}</Text>
                  ))}
                </Flex>
              </Alert>
            )}

            <Button
              variant="primary"
              onClick={handleGenerate}
              disabled={
                loadingGenerate ||
                selectedIds.length === 0 ||
                selectedDocTypes.length === 0 ||
                hasConflict ||
                hasNotRequired ||
                ((selectedDocTypes.includes("origen_borrador") ||
                  selectedDocTypes.includes("origen_final")) &&
                  !descripcionMercancia.trim())
              }
            >
              {loadingGenerate
                ? DOCUMENTOS_LOADING.GENERATING
                : `Generar documentos (${selectedIds.length} contenedor${selectedIds.length !== 1 ? "es" : ""})`}
            </Button>
          </Flex>
        </Box>
      )}

    </Flex>
  );
};

export default DocumentosPendientesTab;
