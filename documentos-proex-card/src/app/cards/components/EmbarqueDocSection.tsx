import React, { useState } from "react";
import {
  Flex,
  Text,
  Button,
  StatusTag,
  Tag,
  Link,
  Alert,
  LoadingSpinner,
} from "@hubspot/ui-extensions";

import { SeccionBloque, type EstadoEtapa } from "./ui/SeccionBloque";
import { formatDateES, type OtroDocArchivo } from "../utils/documentos.utils";
import { buildUploadModalUri, deletePedidoFile } from "../utils/gestion.api";

interface EmbarqueDocSectionProps {
  identificador: string;
  titulo: string;
  /** tipo_documento del backend; actualmente solo "doc_dua" (etapa previa al BL en exportación) */
  tipoDocumento: string;
  archivo: OtroDocArchivo | null;
  requerido: boolean;
  numeroPedido: string;
  companyId: string;
  /** contenedor activo: destino por defecto y referencia para el borrado */
  contenedorId: string;
  /** subconjunto del embarque; si tiene >1 elemento la subida se replica a todos */
  contenedorIdsDestino?: string[];
  numContenedoresPedido: number;
  actions: any;
  onUpdated: () => void | Promise<void>;
  /** Aún no se ha aprobado el envío de documentación al cliente. */
  envioNoPermitido?: boolean;
}

const EmbarqueDocSection: React.FC<EmbarqueDocSectionProps> = ({
  identificador,
  titulo,
  tipoDocumento,
  archivo,
  requerido,
  numeroPedido,
  companyId,
  contenedorId,
  contenedorIdsDestino,
  numContenedoresPedido,
  actions,
  onUpdated,
  envioNoPermitido,
}) => {
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState(false);

  if (!requerido) {
    return (
      <SeccionBloque
        identificador={identificador}
        titulo={titulo}
        estado="pasada"
        defaultAbierta={false}
        badge={<Tag variant="success">No requerido</Tag>}
      >
        <Text variant="microcopy">
          Ningún contenedor del pedido requiere {titulo.toLowerCase()}.
        </Text>
      </SeccionBloque>
    );
  }

  const tieneSeleccion = !!contenedorIdsDestino && contenedorIdsDestino.length > 0;
  const destinos = tieneSeleccion ? contenedorIdsDestino! : [contenedorId];
  const esEmbarque = destinos.length > 1;

  const estado: EstadoEtapa = archivo ? "pasada" : "actual";
  const badge = archivo ? (
    <Tag variant="success">Subido</Tag>
  ) : (
    <Tag variant="default">Pendiente</Tag>
  );

  const handleSubir = () => {
    if (!actions?.openIframeModal) {
      console.warn("[EmbarqueDoc] actions.openIframeModal no disponible");
      return;
    }
    setUploading(true);
    actions.openIframeModal(
      {
        uri: buildUploadModalUri(
          numeroPedido,
          companyId,
          tipoDocumento,
          contenedorId,
          tieneSeleccion ? destinos : undefined,
        ),
        title: `Subir ${titulo}`,
        width: 640,
        height: 520,
        flush: true,
      },
      async () => {
        try {
          await onUpdated();
        } finally {
          setUploading(false);
        }
      },
    );
  };

  const handleBorrar = async () => {
    if (!archivo) return;
    setDeleting(true);
    try {
      await deletePedidoFile(
        numeroPedido,
        companyId,
        archivo.file_id,
        tipoDocumento,
        contenedorId,
        tieneSeleccion ? destinos : undefined,
      );
      await onUpdated();
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      actions?.addAlert?.({
        type: "danger",
        title: `${titulo} — error al borrar`,
        message: msg,
      });
    } finally {
      setDeleting(false);
    }
  };

  return (
    <SeccionBloque
      identificador={identificador}
      titulo={titulo}
      estado={estado}
      defaultAbierta={!archivo}
      envioNoPermitido={envioNoPermitido}
      badge={badge}
    >
      <Flex direction="column" gap="small">
        {esEmbarque ? (
          <Alert title="Documento del embarque" variant="info">
            Se subirá a los {destinos.length} contenedores seleccionados del embarque.
          </Alert>
        ) : (
          <Text variant="microcopy">
            Se aplicará solo a este contenedor. Marca varios contenedores en la
            tabla para subirlo a un embarque ({numContenedoresPedido} en el pedido).
          </Text>
        )}

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
              {deleting ? (
                <LoadingSpinner size="sm" label="Quitando..." />
              ) : (
                <Button variant="secondary" size="xs" onClick={handleBorrar}>
                  Quitar
                </Button>
              )}
            </>
          ) : uploading ? (
            <LoadingSpinner size="sm" label="Subiendo..." />
          ) : (
            <>
              <Button variant="secondary" size="sm" onClick={handleSubir}>
                Subir archivo
              </Button>
              <Text variant="microcopy">Sin archivo</Text>
            </>
          )}
        </Flex>

        {archivo?.created_at && (
          <Text variant="microcopy">Subido el {formatDateES(archivo.created_at)}</Text>
        )}
      </Flex>
    </SeccionBloque>
  );
};

export default EmbarqueDocSection;
