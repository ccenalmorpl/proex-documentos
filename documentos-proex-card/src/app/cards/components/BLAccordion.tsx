import React, { useEffect, useState } from "react";
import {
  Box,
  Flex,
  Text,
  Button,
  Checkbox,
  Select,
  TextArea,
  Alert,
  StatusTag,
  Divider,
  Tag,
  StepIndicator,
  Link,
  LoadingSpinner,
} from "@hubspot/ui-extensions";

import { SeccionBloque, type EstadoEtapa } from "./ui/SeccionBloque";
import { formatDateES } from "../utils/documentos.utils";
import type { BLArchivo, EstadoBL, SelectOption } from "../utils/documentos.utils";
import {
  buildUploadModalUri,
  deletePedidoFile,
  updatePedidoBL,
} from "../utils/gestion.api";

interface BLAccordionProps {
  estado: EstadoBL;
  numContenedores: number;
  numeroPedido: string;
  companyId: string;
  selectOptions: Record<string, SelectOption[]>;
  actions: any;
  onChange: (next: EstadoBL) => void;
  onUpdated: () => void | Promise<void>;
  requerido: boolean;
  /** Subconjunto del embarque al que replicar el BL; vacío = todos los del pedido. */
  contenedorIdsDestino?: string[];
  /** Aún no se ha aprobado el envío de documentación al cliente. */
  envioNoPermitido?: boolean;
}

const FileRow: React.FC<{
  label: string;
  archivo: BLArchivo | null;
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
    {archivo?.created_at && (
      <Text variant="microcopy">Subido el {formatDateES(archivo.created_at)}</Text>
    )}
  </Flex>
);

const BLAccordion: React.FC<BLAccordionProps> = ({
  estado,
  numContenedores,
  numeroPedido,
  companyId,
  selectOptions,
  actions,
  onChange,
  onUpdated,
  requerido,
  contenedorIdsDestino,
  envioNoPermitido,
}) => {
  const [deletingFileIds, setDeletingFileIds] = useState<Set<string>>(new Set());
  const [uploadingTipos,  setUploadingTipos]  = useState<Set<string>>(new Set());
  // Texto libre: se edita en local y se persiste al perder el foco (no por tecla).
  const [cambios, setCambios] = useState<string>(estado.cambiosEnBL ?? "");
  useEffect(() => {
    setCambios(estado.cambiosEnBL ?? "");
  }, [estado.cambiosEnBL]);

  // Subir SIEMPRE al conjunto seleccionado (consistente con cert/otros/embarque).
  const tieneSeleccion = !!contenedorIdsDestino && contenedorIdsDestino.length > 0;
  const esSubconjuntoParcial =
    tieneSeleccion && contenedorIdsDestino!.length < numContenedores;

  if (!requerido) {
    return (
      <SeccionBloque
        identificador="1"
        titulo="Bill of Lading (BL)"
        estado="pasada"
        defaultAbierta={false}
        badge={<Tag variant="success">No requerido</Tag>}
      >
        <Text variant="microcopy">
          Ningún contenedor del pedido requiere BL.
        </Text>
      </SeccionBloque>
    );
  }

  const tieneBorrador     = !!estado.borrador;
  // El tipo de emisión lo abre administración: basta con el envío a cliente y su
  // validación. La validación de logística es informativa y ya no bloquea esta etapa.
  const puedeElegirTipo   = estado.enviadoCliente && estado.validadoAdministracion;
  const tipoSeleccionado  = !!estado.tipo;
  const tieneFinal        = !!estado.final;

  const tipoOptions = selectOptions["tipo_de_bl"] ?? [];
  const tipoLbl = estado.tipo
    ? tipoOptions.find((o) => o.value === estado.tipo)?.label ?? estado.tipo
    : null;

  let currentStep = 0;
  if (tieneFinal)              currentStep = 3;
  else if (tipoSeleccionado)   currentStep = 2;
  else if (puedeElegirTipo)    currentStep = 1;
  else                         currentStep = 0;

  const seccionEstado: EstadoEtapa = tieneFinal
    ? "pasada"
    : tieneBorrador
      ? "actual"
      : "futura";

  const patchProp = async (
    payload: Parameters<typeof updatePedidoBL>[2],
    optimistic: EstadoBL,
    description: string,
  ) => {
    const snapshot = estado;
    onChange(optimistic);
    try {
      const resp = await updatePedidoBL(
        numeroPedido, companyId, payload,
        tieneSeleccion ? contenedorIdsDestino : undefined,
      );
      if (resp && resp.success === false) {
        throw new Error(resp.error ?? "PATCH respondió sin éxito");
      }
      actions?.addAlert?.({
        type: "success",
        title: "BL actualizado",
        message: description,
      });
    } catch (e) {
      onChange(snapshot);
      const msg = e instanceof Error ? e.message : String(e);
      actions?.addAlert?.({
        type: "danger",
        title: "BL — error",
        message: `${description}: ${msg}`,
      });
    }
  };

  const handleToggleEnviadoCliente = (checked: boolean) =>
    patchProp(
      { bl_enviado_cliente: checked },
      { ...estado, enviadoCliente: checked },
      checked ? "BL enviado a cliente" : "Quitado 'enviado a cliente'",
    );

  const handleToggleAdmin = (checked: boolean) =>
    patchProp(
      { bl_validado_administracion: checked },
      { ...estado, validadoAdministracion: checked },
      checked ? "Validado por administración" : "Quitada validación administración",
    );

  const handleToggleLogistica = (checked: boolean) =>
    patchProp(
      { bl_validado_logistica: checked },
      { ...estado, validadoLogistica: checked },
      checked ? "Validado por logística" : "Quitada validación logística",
    );

  const handleChangeTipo = (v: any) => {
    const tipo = v ? String(v) : null;
    const label = tipoOptions.find((o) => o.value === tipo)?.label ?? tipo ?? "(sin tipo)";
    return patchProp(
      { tipo_de_bl: tipo },
      { ...estado, tipo },
      `Tipo de BL: ${label}`,
    );
  };

  const handleBlurCambios = (v: string) => {
    const next = v ?? "";
    if (next === (estado.cambiosEnBL ?? "")) return;
    patchProp(
      { cambios_en_bl: next },
      { ...estado, cambiosEnBL: next },
      next ? "Cambios solicitados en el BL guardados" : "Cambios solicitados en el BL borrados",
    );
  };

  const tipoToTipoDocumento = (tipo: "borrador" | "final"): string =>
    tipo === "borrador" ? "bl_borrador" : "bl_final";

  const archivoToTipoDocumento = (archivo: BLArchivo): string | null => {
    if (archivo.tipo === "borrador") return "bl_borrador";
    if (archivo.tipo === "final") return "bl_final";
    return null;
  };

  const handleSubir = (tipo: "borrador" | "final") => {
    if (!actions?.openIframeModal) {
      console.warn("[BL] actions.openIframeModal no disponible");
      return;
    }
    const tipoDocumento = tipoToTipoDocumento(tipo);
    setUploadingTipos((prev) => {
      const next = new Set(prev);
      next.add(tipoDocumento);
      return next;
    });
    actions.openIframeModal(
      {
        uri: buildUploadModalUri(
          numeroPedido,
          companyId,
          tipoDocumento,
          undefined,
          tieneSeleccion ? contenedorIdsDestino : undefined,
        ),
        title: tipo === "borrador" ? "Subir borrador BL" : "Subir BL final",
        width: 640,
        height: 520,
        flush: true,
      },
      async () => {
        try {
          await onUpdated();
        } finally {
          setUploadingTipos((prev) => {
            const next = new Set(prev);
            next.delete(tipoDocumento);
            return next;
          });
        }
      },
    );
  };

  const handleBorrar = async (archivo: BLArchivo | null) => {
    if (!archivo) return;
    const tipoDocumento = archivoToTipoDocumento(archivo);
    if (!tipoDocumento) {
      console.warn("[BL] archivo con tipo desconocido, no se puede borrar:", archivo);
      return;
    }
    setDeletingFileIds((prev) => {
      const next = new Set(prev);
      next.add(archivo.file_id);
      return next;
    });
    try {
      await deletePedidoFile(
        numeroPedido,
        companyId,
        archivo.file_id,
        tipoDocumento,
        undefined,
        tieneSeleccion ? contenedorIdsDestino : undefined,
      );
      await onUpdated();
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      actions?.addAlert?.({
        type: "danger",
        title: "BL — error al borrar archivo",
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

  return (
    <SeccionBloque
      identificador="1"
      titulo="Bill of Lading (BL)"
      estado={seccionEstado}
      defaultAbierta={seccionEstado !== "pasada"}
      envioNoPermitido={envioNoPermitido}
      badge={tipoLbl ? <Tag variant="info">{tipoLbl}</Tag> : undefined}
    >
      <Flex direction="column" gap="small">
        <Alert title="BL del embarque seleccionado" variant="info">
          {esSubconjuntoParcial
            ? `El BL (validaciones, tipo, borrador y cambios solicitados) se guarda en los ${contenedorIdsDestino!.length} contenedores seleccionados (de ${numContenedores}), en su Negocio Documento y su Negocio Pedido.`
            : `El BL (validaciones, tipo, borrador y cambios solicitados) se guarda en los ${tieneSeleccion ? contenedorIdsDestino!.length : numContenedores} contenedores seleccionados, en su Negocio Documento y su Negocio Pedido.`}
        </Alert>

        <StepIndicator
          stepNames={["Borrador BL", "Tipo de emisión", "BL final"]}
          currentStep={currentStep}
          variant="default"
        />

        <Divider />

        <Flex direction="row" gap="medium" align="start">
          <Box flex={1}>
            <Flex direction="column" gap="small">
              <FileRow
                label="1. Borrador BL"
                archivo={estado.borrador}
                deleting={!!estado.borrador && deletingFileIds.has(estado.borrador.file_id)}
                uploading={uploadingTipos.has("bl_borrador")}
                onSubir={() => handleSubir("borrador")}
                onBorrar={() => handleBorrar(estado.borrador)}
              />
              <Checkbox
                checked={estado.enviadoCliente}
                onChange={handleToggleEnviadoCliente}
                name="bl_enviado_cliente"
                readOnly={!tieneBorrador}
              >
                Enviado a cliente
              </Checkbox>
              <Checkbox
                checked={estado.validadoAdministracion}
                onChange={handleToggleAdmin}
                name="bl_validado_administracion"
                readOnly={!tieneBorrador}
              >
                Validado por administración
              </Checkbox>
              <Checkbox
                checked={estado.validadoLogistica}
                onChange={handleToggleLogistica}
                name="bl_validado_logistica"
                readOnly={!tieneBorrador}
              >
                Validado por logística
              </Checkbox>
            </Flex>
          </Box>

          <Box flex={1}>
            <Flex direction="column" gap="extra-small">
              <Text format={{ fontWeight: "demibold" }}>2. Tipo de emisión (administración)</Text>
              <Select
                label=""
                name="bl_tipo"
                value={estado.tipo ?? ""}
                options={tipoOptions}
                onChange={handleChangeTipo}
                placeholder="Seleccionar..."
                readOnly={!puedeElegirTipo}
              />
              <Text variant="microcopy">
                {puedeElegirTipo
                  ? "Admin elige el tipo tras confirmar el borrador con el cliente."
                  : "Marca antes 'Enviado a cliente' y 'Validado por administración'."}
              </Text>
            </Flex>
          </Box>

          <Box flex={1}>
            <FileRow
              label="3. BL final"
              archivo={estado.final}
              deleting={!!estado.final && deletingFileIds.has(estado.final.file_id)}
              uploading={uploadingTipos.has("bl_final")}
              onSubir={() => handleSubir("final")}
              onBorrar={() => handleBorrar(estado.final)}
              disabled={!tipoSeleccionado}
              disabledReason="Selecciona antes el tipo de BL"
            />
          </Box>
        </Flex>

        <Divider />

        <Flex direction="column" gap="extra-small">
          <Text format={{ fontWeight: "demibold" }}>Cambios solicitados en el BL</Text>
          <TextArea
            label=""
            name="cambios_en_bl"
            value={cambios}
            onChange={setCambios}
            onBlur={handleBlurCambios}
            rows={3}
            placeholder="Anota los cambios que el cliente o la naviera solicitan sobre el BL…"
            readOnly={!tieneBorrador}
          />
          <Text variant="microcopy">
            {tieneBorrador
              ? "Texto libre. Se guarda al salir del campo, en los contenedores seleccionados."
              : "Disponible cuando haya un borrador de BL."}
          </Text>
        </Flex>
      </Flex>
    </SeccionBloque>
  );
};

export default BLAccordion;
