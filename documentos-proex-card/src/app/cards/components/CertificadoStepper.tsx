import React, { useState } from "react";
import {
  Box,
  Flex,
  Heading,
  Text,
  Button,
  Checkbox,
  StepIndicator,
  StatusTag,
  Tile,
  Divider,
  Tag,
  Link,
  LoadingSpinner,
} from "@hubspot/ui-extensions";

import type {
  CertificadoArchivo,
  EstadoCertificado,
} from "../utils/documentos.utils";
import {
  buildUploadModalUri,
  deletePedidoFile,
  updateContenedoresCertificados,
  type UpdateContenedoresCertificadosPayload,
} from "../utils/gestion.api";

type TipoCertificado = "origen" | "sanitario";

interface CertificadoStepperProps {
  titulo: string;
  tipoCertificado: TipoCertificado;
  estado: EstadoCertificado;
  numeroPedido: string;
  companyId: string;
  actions: any;
  onChange: (next: EstadoCertificado) => void;
  onUpdated: () => void | Promise<void>;
}

const tipoDocumentoFor = (
  tipoCert: TipoCertificado,
  etapa: "borrador" | "validado" | "sellado",
): string => `${tipoCert}_${etapa}`;

const FileRowReadonly: React.FC<{
  label: string;
  archivo: CertificadoArchivo | null;
  warningText: string;
}> = ({ label, archivo, warningText }) => (
  <Flex direction="column" gap="extra-small">
    <Text format={{ fontWeight: "demibold" }}>{label}</Text>
    {archivo ? (
      <StatusTag variant="success">
        {archivo.url ? (
          <Link href={{ url: archivo.url, external: true }}>{archivo.name}</Link>
        ) : (
          archivo.name
        )}
      </StatusTag>
    ) : (
      <Tag variant="warning">{warningText}</Tag>
    )}
  </Flex>
);

const FileRowEditable: React.FC<{
  label: string;
  archivo: CertificadoArchivo | null;
  onSubir: () => void;
  onBorrar: () => void;
  disabled?: boolean;
  disabledReason?: string;
  deleting?: boolean;
  uploading?: boolean;
}> = ({ label, archivo, onSubir, onBorrar, disabled, disabledReason, deleting, uploading }) => (
  <Flex direction="column" gap="extra-small">
    <Text format={{ fontWeight: "demibold" }}>{label}</Text>
    <Flex direction="row" gap="sm" align="center">
      {archivo ? (
        <>
          <StatusTag variant="success">
            {archivo.url ? (
              <Link href={{ url: archivo.url, external: true }}>{archivo.name}</Link>
            ) : (
              archivo.name
            )}
          </StatusTag>
          {uploading ? (
            <LoadingSpinner size="sm" label="Subiendo..." />
          ) : deleting ? (
            <LoadingSpinner size="sm" label="Quitando..." />
          ) : (
            <Button variant="secondary" size="xs" onClick={onBorrar}>
              Quitar
            </Button>
          )}
        </>
      ) : uploading ? (
        <LoadingSpinner size="sm" label="Subiendo..." />
      ) : (
        <>
          <Button variant="secondary" size="sm" onClick={onSubir} disabled={disabled}>
            Subir archivo
          </Button>
          <Text variant="microcopy">
            {disabled ? (disabledReason ?? "Bloqueado") : "Sin archivo"}
          </Text>
        </>
      )}
    </Flex>
  </Flex>
);

const CertificadoStepper: React.FC<CertificadoStepperProps> = ({
  titulo,
  tipoCertificado,
  estado,
  numeroPedido,
  companyId,
  actions,
  onChange,
  onUpdated,
}) => {
  const [deletingFileIds, setDeletingFileIds] = useState<Set<string>>(new Set());
  const [uploadingDocs,   setUploadingDocs]   = useState<Set<string>>(new Set());

  const tieneBorrador = !!estado.borrador;
  const tieneValidado = !!estado.validado;
  const tieneSellado  = !!estado.sellado;

  let currentStep = 0;
  if (tieneSellado)                 currentStep = 3;
  else if (tieneValidado)           currentStep = 2;
  else if (estado.validadoCliente)  currentStep = 1;
  else                              currentStep = 0;

  const warningBorrador = `Genera el certificado ${tipoCertificado} en la pestaña "Generar documentos"`;
  const warningValidado = tipoCertificado === "origen"
    ? `Genera el certificado de origen final en la pestaña "Generar documentos"`
    : "Sin archivo";

  const patchCheckbox = async (
    payload: UpdateContenedoresCertificadosPayload,
    optimistic: EstadoCertificado,
    description: string,
  ) => {
    const snapshot = estado;
    onChange(optimistic);
    try {
      const resp = await updateContenedoresCertificados(numeroPedido, companyId, payload);
      if (resp && resp.success === false) {
        throw new Error(resp.error ?? "PATCH respondió sin éxito");
      }
      actions?.addAlert?.({
        type: "success",
        title: `${titulo} actualizado`,
        message: description,
      });
    } catch (e) {
      onChange(snapshot);
      const msg = e instanceof Error ? e.message : String(e);
      actions?.addAlert?.({
        type: "danger",
        title: `${titulo} — error`,
        message: `${description}: ${msg}`,
      });
    }
  };

  const handleToggleValidado = (checked: boolean) => {
    const description = checked ? "Validado por cliente" : "Quitada validación por cliente";
    if (tipoCertificado === "origen") {
      return patchCheckbox(
        { certificado_origen_validado: checked },
        { ...estado, validadoCliente: checked },
        description,
      );
    }
    return patchCheckbox(
      { certificado_sanitario_validado: checked },
      { ...estado, validadoCliente: checked },
      description,
    );
  };

  const openUploadModal = (etapa: "validado" | "sellado") => {
    if (!actions?.openIframeModal) {
      console.warn("[Cert] actions.openIframeModal no disponible");
      return;
    }
    const tipoDocumento = tipoDocumentoFor(tipoCertificado, etapa);
    setUploadingDocs((prev) => {
      const next = new Set(prev);
      next.add(tipoDocumento);
      return next;
    });
    actions.openIframeModal(
      {
        uri: buildUploadModalUri(numeroPedido, companyId, tipoDocumento),
        title: `Subir ${titulo} — ${etapa}`,
        width: 640,
        height: 520,
        flush: true,
      },
      async () => {
        try {
          await onUpdated();
        } finally {
          setUploadingDocs((prev) => {
            const next = new Set(prev);
            next.delete(tipoDocumento);
            return next;
          });
        }
      },
    );
  };

  const handleBorrar = async (
    archivo: CertificadoArchivo | null,
    etapa: "validado" | "sellado",
  ) => {
    if (!archivo) return;
    const tipoDocumento = tipoDocumentoFor(tipoCertificado, etapa);
    setDeletingFileIds((prev) => {
      const next = new Set(prev);
      next.add(archivo.file_id);
      return next;
    });
    try {
      await deletePedidoFile(numeroPedido, companyId, archivo.file_id, tipoDocumento);
      await onUpdated();
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      actions?.addAlert?.({
        type: "danger",
        title: `${titulo} — error al borrar archivo`,
        message: msg,
      });
    } finally {
      setDeletingFileIds((prev) => {
        const next = new Set(prev);
        next.delete(archivo.file_id);
        return next;
      });
    }
  };

  const etapa2EsAuto = tipoCertificado === "origen";

  return (
    <Tile>
      <Flex direction="column" gap="small">
        <Heading>{titulo}</Heading>

        <StepIndicator
          stepNames={["Borrador a validar", "Validado por cliente", "Sellado y firmado"]}
          currentStep={currentStep}
          variant="default"
        />

        <Divider />

        <Flex direction="row" gap="medium" align="start">
          <Box flex={1}>
            <Flex direction="column" gap="small">
              <FileRowReadonly
                label="1. Borrador a validar (administración)"
                archivo={estado.borrador}
                warningText={warningBorrador}
              />
              <Checkbox
                checked={estado.validadoCliente}
                onChange={handleToggleValidado}
                name={`${tipoCertificado}_validado_cliente`}
                description="Marcar cuando el cliente haya confirmado el borrador."
                readOnly={!tieneBorrador}
              >
                Validado por cliente
              </Checkbox>
            </Flex>
          </Box>

          <Box flex={1}>
            {etapa2EsAuto ? (
              <FileRowReadonly
                label="2. Validado por cliente (administración)"
                archivo={estado.validado}
                warningText={warningValidado}
              />
            ) : (
              <FileRowEditable
                label="2. Validado por cliente (administración)"
                archivo={estado.validado}
                deleting={!!estado.validado && deletingFileIds.has(estado.validado.file_id)}
                uploading={uploadingDocs.has(tipoDocumentoFor(tipoCertificado, "validado"))}
                onSubir={() => openUploadModal("validado")}
                onBorrar={() => handleBorrar(estado.validado, "validado")}
                disabled={!estado.validadoCliente}
                disabledReason="Marca antes 'Validado por cliente'"
              />
            )}
          </Box>

          <Box flex={1}>
            <FileRowEditable
              label="3. Sellado y firmado (logística)"
              archivo={estado.sellado}
              deleting={!!estado.sellado && deletingFileIds.has(estado.sellado.file_id)}
              uploading={uploadingDocs.has(tipoDocumentoFor(tipoCertificado, "sellado"))}
              onSubir={() => openUploadModal("sellado")}
              onBorrar={() => handleBorrar(estado.sellado, "sellado")}
              disabled={!tieneValidado}
              disabledReason="Sube antes el archivo validado por cliente"
            />
          </Box>
        </Flex>
      </Flex>
    </Tile>
  );
};

export default CertificadoStepper;
