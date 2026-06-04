import React, { useEffect, useState } from "react";
import {
  Flex,
  Text,
  Button,
  Checkbox,
  StatusTag,
  Tag,
  Link,
  Divider,
  LoadingSpinner,
} from "@hubspot/ui-extensions";

import { SeccionBloque, type EstadoEtapa } from "./ui/SeccionBloque";
import type {
  ArchivoSimple,
  EstadoOtrosDocs,
  OtroDocArchivo,
  OtroDocTipoDiscriminado,
  PedidoDetalleInfo,
} from "../utils/documentos.utils";
import { formatDateES } from "../utils/documentos.utils";
import {
  buildUploadModalUri,
  deletePedidoFile,
  updateContenedorEntrega,
} from "../utils/gestion.api";
import {
  FOTOS_CARGA_MAX_FILES,
  FOTO_CARGA_FILE_TYPE,
  OTROS_DOC_GESTIONADOS_EN_OTRAS_ETAPAS,
  OTROS_DOC_LABELS,
  OTROS_DOC_MAX_FILES,
  OTROS_DOC_SUBIBLES_DISCRIMINADOS,
  OTROS_DOC_SUBIBLES_VALIDOS,
  OTROS_DOC_TYPE_OTROS,
  OTROS_DOC_TYPE_TO_FILE_TYPE,
  OTROS_DOC_TYPE_WAIVER,
} from "../constants/documentos.constants";

interface OtrosDocumentosSectionProps {
  identificador?: string;
  titulo?: string;
  numeroPedido: string;
  companyId: string;
  contenedorId: string;
  contenedorNombre: string | null;
  documentosAGenerar: string[];
  pedidoInfo: PedidoDetalleInfo;
  fotosDeCarga: boolean;
  estado: EstadoOtrosDocs;
  actions: any;
  onUpdated: () => void | Promise<void>;
}

const FileRow: React.FC<{
  label: string;
  archivo: OtroDocArchivo | null;
  onSubir: () => void;
  onBorrar: () => void;
  deleting?: boolean;
  uploading?: boolean;
  disabled?: boolean;
  disabledReason?: string;
}> = ({ label, archivo, onSubir, onBorrar, deleting, uploading, disabled, disabledReason }) => (
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

const MultiFileSlot: React.FC<{
  label: string;
  archivos: ArchivoSimple[];
  max: number;
  deletingFileIds: Set<string>;
  uploading: boolean;
  onSubir: () => void;
  onBorrar: (file_id: string) => void;
}> = ({ label, archivos, max, deletingFileIds, uploading, onSubir, onBorrar }) => {
  const lleno = archivos.length >= max;
  return (
    <Flex direction="column" gap="extra-small">
      <Flex direction="row" gap="extra-small" align="center">
        <Text format={{ fontWeight: "demibold" }}>{label}</Text>
        <Tag variant={lleno ? "success" : "default"}>
          {archivos.length}/{max}
        </Tag>
      </Flex>
      {archivos.length > 0 && (
        <Flex direction="column" gap="extra-small">
          {archivos.map((a) => (
            <Flex key={a.file_id} direction="row" gap="sm" align="center">
              <StatusTag variant="success">
                {a.url ? (
                  <Link href={{ url: a.url, external: true }}>{a.name}</Link>
                ) : (
                  a.name
                )}
              </StatusTag>
              {deletingFileIds.has(a.file_id) ? (
                <LoadingSpinner size="sm" label="Quitando..." />
              ) : (
                <Button variant="secondary" size="xs" onClick={() => onBorrar(a.file_id)}>
                  Quitar
                </Button>
              )}
            </Flex>
          ))}
        </Flex>
      )}
      <Flex direction="row" gap="sm" align="center">
        {uploading ? (
          <LoadingSpinner size="sm" label="Subiendo..." />
        ) : (
          <>
            <Button variant="secondary" size="sm" onClick={onSubir} disabled={lleno}>
              {archivos.length === 0 ? "Subir archivo" : "Añadir archivo"}
            </Button>
            <Text variant="microcopy">
              {lleno ? `Máximo ${max} archivos` : `Hasta ${max} archivos`}
            </Text>
          </>
        )}
      </Flex>
    </Flex>
  );
};

const ReadonlyDocLink: React.FC<{
  label: string;
  url: string | null;
  fallbackWarning: string;
}> = ({ label, url, fallbackWarning }) => (
  <Flex direction="column" gap="extra-small" align="start">
    <Text format={{ fontWeight: "demibold" }}>{label}</Text>
    {url ? (
      <Link href={{ url, external: true }}>Ver documento</Link>
    ) : (
      <Tag variant="warning">{fallbackWarning}</Tag>
    )}
  </Flex>
);

const OtrosDocumentosSection: React.FC<OtrosDocumentosSectionProps> = ({
  identificador = "3",
  titulo = "Otros documentos",
  numeroPedido,
  companyId,
  contenedorId,
  contenedorNombre,
  documentosAGenerar,
  pedidoInfo,
  fotosDeCarga,
  estado,
  actions,
  onUpdated,
}) => {
  const [deletingFileIds, setDeletingFileIds] = useState<Set<string>>(new Set());
  const [uploadingKeys,   setUploadingKeys]   = useState<Set<string>>(new Set());
  const [waiverValidadoOptim, setWaiverValidadoOptim] = useState(estado.waiverValidado);

  useEffect(() => {
    setWaiverValidadoOptim(estado.waiverValidado);
  }, [estado.waiverValidado]);

  const subibles = documentosAGenerar.filter(
    (k) =>
      !OTROS_DOC_GESTIONADOS_EN_OTRAS_ETAPAS.has(k) &&
      OTROS_DOC_SUBIBLES_VALIDOS.has(k),
  );

  const discriminadosSeleccionados = subibles.filter((k) =>
    OTROS_DOC_SUBIBLES_DISCRIMINADOS.includes(k as (typeof OTROS_DOC_SUBIBLES_DISCRIMINADOS)[number]),
  );
  const incluyeWaiver = subibles.includes(OTROS_DOC_TYPE_WAIVER);
  const incluyeOtros  = subibles.includes(OTROS_DOC_TYPE_OTROS);

  const waiverCompleto =
    !!estado.waiverBorrador && waiverValidadoOptim && !!estado.waiverFinal;

  const totalRequeridos =
    discriminadosSeleccionados.length +
    (incluyeWaiver ? 1 : 0) +
    (incluyeOtros ? 1 : 0) +
    (fotosDeCarga ? 1 : 0);
  const subidos =
    discriminadosSeleccionados.filter((k) => !!estado[k as OtroDocTipoDiscriminado]).length +
    (incluyeWaiver && waiverCompleto ? 1 : 0) +
    (incluyeOtros && estado.otros.length > 0 ? 1 : 0) +
    (fotosDeCarga && estado.fotos.length > 0 ? 1 : 0);

  const seccionEstado: EstadoEtapa =
    totalRequeridos === 0
      ? "futura"
      : subidos === totalRequeridos
        ? "pasada"
        : subidos > 0
          ? "actual"
          : "futura";

  const badge =
    totalRequeridos > 0 ? (
      <Tag variant={subidos === totalRequeridos ? "success" : "default"}>
        {subidos}/{totalRequeridos}
      </Tag>
    ) : (
      <Tag variant="default">Sin requisitos</Tag>
    );

  const abrirModalUpload = (tipoDocumento: string, titulo: string) => {
    if (!actions?.openIframeModal) {
      console.warn("[OtrosDocs] actions.openIframeModal no disponible");
      return;
    }
    setUploadingKeys((prev) => {
      const next = new Set(prev);
      next.add(tipoDocumento);
      return next;
    });
    actions.openIframeModal(
      {
        uri: buildUploadModalUri(numeroPedido, companyId, tipoDocumento, contenedorId),
        title: titulo,
        width: 720,
        height: 560,
        flush: true,
      },
      async () => {
        try {
          await onUpdated();
        } finally {
          setUploadingKeys((prev) => {
            const next = new Set(prev);
            next.delete(tipoDocumento);
            return next;
          });
        }
      },
    );
  };

  const handleSubirDiscriminado = (tipo: OtroDocTipoDiscriminado) => {
    const fileType = OTROS_DOC_TYPE_TO_FILE_TYPE[tipo];
    if (!fileType) return;
    const titulo = `Subir ${OTROS_DOC_LABELS[tipo] ?? tipo}`;
    abrirModalUpload(fileType, titulo);
  };

  const handleToggleWaiverValidado = async (checked: boolean) => {
    const snapshot = waiverValidadoOptim;
    setWaiverValidadoOptim(checked);
    try {
      const resp = await updateContenedorEntrega(
        numeroPedido, companyId, contenedorId, { waiver_validado: checked },
      );
      if (resp && resp.success === false) {
        throw new Error(resp.error ?? "PATCH respondió sin éxito");
      }
      actions?.addAlert?.({
        type: "success",
        title: "Waiver actualizado",
        message: checked ? "Validado por cliente" : "Quitada validación por cliente",
      });
      await onUpdated();
    } catch (e) {
      setWaiverValidadoOptim(snapshot);
      const msg = e instanceof Error ? e.message : String(e);
      actions?.addAlert?.({
        type: "danger",
        title: "Waiver — error",
        message: msg,
      });
    }
  };

  const handleBorrarArchivo = async (
    fileId: string,
    fileType: string,
    labelHumano: string,
  ) => {
    setDeletingFileIds((prev) => {
      const next = new Set(prev);
      next.add(fileId);
      return next;
    });
    try {
      await deletePedidoFile(numeroPedido, companyId, fileId, fileType, contenedorId);
      await onUpdated();
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      actions?.addAlert?.({
        type: "danger",
        title: `${labelHumano} — error al borrar`,
        message: msg,
      });
    } finally {
      setDeletingFileIds((prev) => {
        const next = new Set(prev);
        next.delete(fileId);
        return next;
      });
    }
  };

  const hayAlgoSubible = subibles.length > 0;

  return (
    <SeccionBloque
      identificador={identificador}
      titulo={titulo}
      estado={seccionEstado}
      defaultAbierta={seccionEstado !== "pasada"}
      badge={badge}
    >
      <Flex direction="column" gap="medium">
        <Flex direction="column" gap="small">
          <Text format={{ fontWeight: "demibold" }}>Documentos del pedido</Text>
          <Text variant="microcopy">
            Documentos generados en el pipeline del pedido (compartidos por todos los contenedores).
          </Text>
          <Flex direction="row" gap="large" align="start">
            <Flex direction="column" gap="extra-small" align="start">
              <ReadonlyDocLink
                label="Factura"
                url={pedidoInfo.factura_pedido?.url ?? null}
                fallbackWarning="Generar en pedido"
              />
              {pedidoInfo.fecha_de_facturacion_pedido && (
                <Text variant="microcopy">
                  Facturado: {formatDateES(pedidoInfo.fecha_de_facturacion_pedido)}
                </Text>
              )}
              {pedidoInfo.fecha_de_vencimiento_factura && (
                <Text variant="microcopy">
                  Vencimiento: {formatDateES(pedidoInfo.fecha_de_vencimiento_factura)}
                </Text>
              )}
            </Flex>
            <ReadonlyDocLink
              label="Packing list"
              url={pedidoInfo.packing_list_pedido?.url ?? null}
              fallbackWarning="Generar en pedido"
            />
            {pedidoInfo.carta_porte_pedido?.url && (
              <Flex direction="column" gap="extra-small" align="start">
                <Text format={{ fontWeight: "demibold" }}>Carta de porte</Text>
                <Link
                  href={{ url: pedidoInfo.carta_porte_pedido.url, external: true }}
                >
                  Ver documento
                </Link>
              </Flex>
            )}
          </Flex>
        </Flex>

        <Divider />

        <Flex direction="column" gap="small">
          <Text format={{ fontWeight: "demibold" }}>
            Documentos a aportar{contenedorNombre ? ` — ${contenedorNombre}` : ""}
          </Text>
          {!hayAlgoSubible ? (
            <Text variant="microcopy">
              Este pedido no tiene documentos extra marcados en "documentación a generar".
            </Text>
          ) : (
            <Flex direction="row" gap="medium" wrap="wrap">
              {discriminadosSeleccionados.map((k) => {
                const tipo  = k as OtroDocTipoDiscriminado;
                const label = OTROS_DOC_LABELS[k] ?? k;
                const archivo = estado[tipo] as OtroDocArchivo | null;
                return (
                  <FileRow
                    key={k}
                    label={label}
                    archivo={archivo}
                    deleting={!!archivo && deletingFileIds.has(archivo.file_id)}
                    uploading={uploadingKeys.has(OTROS_DOC_TYPE_TO_FILE_TYPE[k])}
                    onSubir={() => handleSubirDiscriminado(tipo)}
                    onBorrar={() =>
                      archivo &&
                      handleBorrarArchivo(
                        archivo.file_id,
                        OTROS_DOC_TYPE_TO_FILE_TYPE[k],
                        label,
                      )
                    }
                  />
                );
              })}
              {incluyeWaiver && (
                <Flex direction="column" gap="extra-small">
                  <Text format={{ fontWeight: "bold" }}>Waiver</Text>
                  <FileRow
                    label="Waiver borrador"
                    archivo={estado.waiverBorrador}
                    deleting={!!estado.waiverBorrador && deletingFileIds.has(estado.waiverBorrador.file_id)}
                    uploading={uploadingKeys.has("doc_waiver_borrador")}
                    onSubir={() => handleSubirDiscriminado("waiver_borrador")}
                    onBorrar={() =>
                      estado.waiverBorrador &&
                      handleBorrarArchivo(estado.waiverBorrador.file_id, "doc_waiver_borrador", "Waiver borrador")
                    }
                  />
                  <Checkbox
                    checked={waiverValidadoOptim}
                    onChange={handleToggleWaiverValidado}
                    name="waiver_validado"
                    readOnly={!estado.waiverBorrador}
                  >
                    Validado por cliente
                  </Checkbox>
                  <FileRow
                    label="Waiver final"
                    archivo={estado.waiverFinal}
                    deleting={!!estado.waiverFinal && deletingFileIds.has(estado.waiverFinal.file_id)}
                    uploading={uploadingKeys.has("doc_waiver_final")}
                    onSubir={() => handleSubirDiscriminado("waiver_final")}
                    onBorrar={() =>
                      estado.waiverFinal &&
                      handleBorrarArchivo(estado.waiverFinal.file_id, "doc_waiver_final", "Waiver final")
                    }
                    disabled={!waiverValidadoOptim}
                    disabledReason="Marca antes 'Validado por cliente'"
                  />
                </Flex>
              )}
              {incluyeOtros && (
                <MultiFileSlot
                  label={OTROS_DOC_LABELS[OTROS_DOC_TYPE_OTROS]}
                  archivos={estado.otros}
                  max={OTROS_DOC_MAX_FILES}
                  deletingFileIds={deletingFileIds}
                  uploading={uploadingKeys.has(
                    OTROS_DOC_TYPE_TO_FILE_TYPE[OTROS_DOC_TYPE_OTROS],
                  )}
                  onSubir={() =>
                    abrirModalUpload(
                      OTROS_DOC_TYPE_TO_FILE_TYPE[OTROS_DOC_TYPE_OTROS],
                      "Subir otros documentos",
                    )
                  }
                  onBorrar={(fileId) =>
                    handleBorrarArchivo(
                      fileId,
                      OTROS_DOC_TYPE_TO_FILE_TYPE[OTROS_DOC_TYPE_OTROS],
                      "Otros",
                    )
                  }
                />
              )}
            </Flex>
          )}
        </Flex>

        {fotosDeCarga && (
          <>
            <Divider />
            <Flex direction="column" gap="small">
              <Text format={{ fontWeight: "demibold" }}>Fotos de carga</Text>
              <Text variant="microcopy">
                Adjunta hasta {FOTOS_CARGA_MAX_FILES} fotos de la carga de este contenedor.
              </Text>
              <MultiFileSlot
                label="Fotos"
                archivos={estado.fotos}
                max={FOTOS_CARGA_MAX_FILES}
                deletingFileIds={deletingFileIds}
                uploading={uploadingKeys.has(FOTO_CARGA_FILE_TYPE)}
                onSubir={() => abrirModalUpload(FOTO_CARGA_FILE_TYPE, "Subir fotos de carga")}
                onBorrar={(fileId) =>
                  handleBorrarArchivo(fileId, FOTO_CARGA_FILE_TYPE, "Fotos de carga")
                }
              />
            </Flex>
          </>
        )}
      </Flex>
    </SeccionBloque>
  );
};

export default OtrosDocumentosSection;
