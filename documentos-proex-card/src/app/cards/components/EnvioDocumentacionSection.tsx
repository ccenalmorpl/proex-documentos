import React, { useState } from "react";
import {
  Box,
  Flex,
  Text,
  TextArea,
  Checkbox,
  Button,
  StatusTag,
  Alert,
  DateInput,
  Divider,
  Tag,
  Link,
  Icon,
  LoadingSpinner,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableHeader,
  TableCell,
} from "@hubspot/ui-extensions";

import { SeccionBloque, type EstadoEtapa } from "./ui/SeccionBloque";
import ConfirmPermitirEnvioModal from "./ConfirmPermitirEnvioModal";
import ConfirmRevocarEnvioModal from "./ConfirmRevocarEnvioModal";
import {
  buildDocumentosContenedorResumen,
  formatDateES,
  type ArchivoSimple,
  type BaseDate,
  type DocStatus,
  type EstadoEntrega,
  type PedidoDetalleContenedor,
  type PedidoDetalleInfo,
} from "../utils/documentos.utils";
import { buildUploadModalUri, deletePedidoFile } from "../utils/gestion.api";
import { type TipoPedido } from "../constants/documentos.constants";

const ALBARAN_MENSAJERIA_TIPO = "albaran_mensajeria";

interface EnvioDocumentacionSectionProps {
  estado: EstadoEntrega;
  onChange: (next: EstadoEntrega) => void;
  pedidoInfo: PedidoDetalleInfo;
  contenedor: PedidoDetalleContenedor;
  contenedoresSeleccionados: PedidoDetalleContenedor[];
  /** Los seleccionados difieren en estado de envío/recepción: avisar antes del bulk. */
  entregaDivergente?: boolean;
  fotosDeCarga: boolean;
  tipoPedido: TipoPedido;
  numeroPedido: string;
  companyId: string;
  /** IDs de los contenedores seleccionados (destino de la subida del albarán). */
  contenedorIdsDestino?: string[];
  onUpdated: () => void | Promise<void>;
  identificadorEnvio?: string;
  identificadorRecepcion?: string;
  actions: any;
}

const CeldaDocEnvio: React.FC<{ doc: DocStatus | undefined }> = ({ doc }) => {
  if (!doc) return <Text variant="microcopy">—</Text>;
  if (!doc.generado) return <Tag variant="warning">Pendiente</Tag>;
  return doc.url ? (
    <Link href={{ url: doc.url, external: true }}>Ver</Link>
  ) : (
    <Tag variant="success">Subido</Tag>
  );
};

/** Tabla de documentos a enviar: una fila por contenedor, una columna por documento. */
const TablaDocsAEnviar: React.FC<{
  contenedores: PedidoDetalleContenedor[];
  pedidoInfo: PedidoDetalleInfo;
  tipoPedido: TipoPedido;
  fotosDeCarga: boolean;
}> = ({ contenedores, pedidoInfo, tipoPedido, fotosDeCarga }) => {
  const resumenPorContenedor = contenedores.map((c) => ({
    contenedor: c,
    docs: buildDocumentosContenedorResumen({ contenedor: c, pedidoInfo, tipoPedido, fotosDeCarga }),
  }));

  // Columnas = unión de tipos de documento de todos los contenedores (orden estable).
  const columnas: { key: string; label: string }[] = [];
  const vistos = new Set<string>();
  for (const { docs } of resumenPorContenedor) {
    for (const d of docs) {
      if (!vistos.has(d.key)) {
        vistos.add(d.key);
        columnas.push({ key: d.key, label: d.label });
      }
    }
  }

  const totalGlobal = resumenPorContenedor.reduce((acc, r) => acc + r.docs.length, 0);
  const subidosGlobal = resumenPorContenedor.reduce(
    (acc, r) => acc + r.docs.filter((d) => d.generado).length,
    0,
  );
  const completo = totalGlobal > 0 && subidosGlobal === totalGlobal;

  return (
    <Flex direction="column" gap="extra-small">
      <Flex direction="row" gap="sm" align="center">
        <Text format={{ fontWeight: "demibold" }}>Documentos a enviar al cliente</Text>
        <Tag variant={completo ? "success" : "warning"}>
          {subidosGlobal}/{totalGlobal}
        </Tag>
      </Flex>
      <Text variant="microcopy">
        Documentos por contenedor (factura, packing… son propios de cada uno). Todos deben
        estar subidos para validar el envío.
      </Text>
      <Table>
        <TableHead>
          <TableRow>
            <TableHeader width={140}>Contenedor</TableHeader>
            {columnas.map((col) => (
              <TableHeader key={col.key}>{col.label}</TableHeader>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {resumenPorContenedor.map(({ contenedor, docs }) => {
            const porKey = new Map(docs.map((d) => [d.key, d]));
            return (
              <TableRow key={contenedor.id}>
                <TableCell>
                  <Text format={{ fontWeight: "demibold" }}>
                    {contenedor.nombre ?? contenedor.id}
                  </Text>
                </TableCell>
                {columnas.map((col) => (
                  <TableCell key={col.key}>
                    <CeldaDocEnvio doc={porKey.get(col.key)} />
                  </TableCell>
                ))}
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </Flex>
  );
};

/** Subida real (iframe) del albarán de recogida al Contenedor de referencia; si hay
 *  varios seleccionados, se replica a todos. Refetch al cerrar el modal. */
const AlbaranMensajeriaUpload: React.FC<{
  archivo: ArchivoSimple | null;
  numeroPedido: string;
  companyId: string;
  contenedorId: string;
  destinos: string[];
  actions: any;
  onUpdated: () => void | Promise<void>;
}> = ({ archivo, numeroPedido, companyId, contenedorId, destinos, actions, onUpdated }) => {
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const esEmbarque = destinos.length > 1;

  const handleSubir = () => {
    if (!actions?.openIframeModal) return;
    setUploading(true);
    actions.openIframeModal(
      {
        uri: buildUploadModalUri(
          numeroPedido,
          companyId,
          ALBARAN_MENSAJERIA_TIPO,
          contenedorId,
          esEmbarque ? destinos : undefined,
        ),
        title: "Subir albarán de recogida",
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
        ALBARAN_MENSAJERIA_TIPO,
        contenedorId,
        esEmbarque ? destinos : undefined,
      );
      await onUpdated();
    } catch (e) {
      actions?.addAlert?.({
        type: "danger",
        title: "Albarán de recogida — error al borrar",
        message: e instanceof Error ? e.message : String(e),
      });
    } finally {
      setDeleting(false);
    }
  };

  return (
    <Flex direction="row" gap="sm" align="center">
      {archivo ? (
        <>
          <StatusTag variant="success">
            {archivo.url ? (
              <Link href={{ url: archivo.url, external: true }}>{archivo.name || "albarán"}</Link>
            ) : (
              archivo.name || "albarán"
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
  );
};

const EnvioDocumentacionSection: React.FC<EnvioDocumentacionSectionProps> = ({
  estado,
  onChange,
  pedidoInfo,
  contenedor,
  contenedoresSeleccionados,
  entregaDivergente,
  fotosDeCarga,
  tipoPedido,
  numeroPedido,
  companyId,
  contenedorIdsDestino,
  onUpdated,
  identificadorEnvio = "5",
  identificadorRecepcion = "6",
  actions,
}) => {
  const set = (patch: Partial<EstadoEntrega>) => onChange({ ...estado, ...patch });

  const esMulti = contenedoresSeleccionados.length > 1;
  const destinosAlbaran =
    contenedorIdsDestino && contenedorIdsDestino.length > 0
      ? contenedorIdsDestino
      : [contenedor.id];

  // Todos los documentos de TODOS los contenedores seleccionados deben estar subidos.
  const todosSubidos = contenedoresSeleccionados.every((c) =>
    buildDocumentosContenedorResumen({ contenedor: c, pedidoInfo, tipoPedido, fotosDeCarga }).every(
      (d) => d.generado,
    ),
  );

  const pagoCompletado = contenedoresSeleccionados.every(
    (c) => (parseFloat(c.importe_pendiente_cobro ?? "0") || 0) <= 0,
  );

  const motivosEtapasPendientes: string[] = [];
  if (!pagoCompletado)
    motivosEtapasPendientes.push(
      esMulti
        ? "El pago de algún contenedor no está completado."
        : "El pago del contenedor no está completado.",
    );
  if (!todosSubidos)   motivosEtapasPendientes.push("Faltan documentos por subir o generar.");

  const valoresEtapa6 = {
    documentacionRecibida:  estado.documentacionRecibida,
    fechaLlegadaContenedor: estado.fechaLlegadaContenedor,
    mercanciaRetirada:      estado.mercanciaRetirada,
    fechaRetirada:          estado.fechaRetirada,
  };
  const hayDatosEtapa6 =
    valoresEtapa6.documentacionRecibida ||
    valoresEtapa6.mercanciaRetirada ||
    valoresEtapa6.fechaLlegadaContenedor !== null ||
    valoresEtapa6.fechaRetirada !== null;

  const aplicarPermitir = () => set({ permitirEnviar: true });
  const aplicarRevocar = () =>
    set({
      permitirEnviar:         false,
      documentacionRecibida:  false,
      fechaLlegadaContenedor: null,
      mercanciaRetirada:      false,
      fechaRetirada:          null,
    });

  const estadoEnvio: EstadoEtapa = estado.permitirEnviar
    ? "pasada"
    : (todosSubidos || estado.enviarPorMensajeria)
      ? "actual"
      : "futura";

  const recepcionBloqueada = !estado.permitirEnviar;

  const estadoRecepcion: EstadoEtapa = recepcionBloqueada
    ? "futura"
    : estado.mercanciaRetirada
      ? "pasada"
      : "actual";

  return (
    <Flex direction="column" gap="small">
      <SeccionBloque
        identificador={identificadorEnvio}
        titulo="Envío de documentación"
        estado={estadoEnvio}
        defaultAbierta={!estado.permitirEnviar}
        badge={
          <Flex direction="row" gap="extra-small">
            {estado.permitirEnviar ? (
              <Tag variant="success">Aprobado</Tag>
            ) : (
              <Tag variant="default">Pendiente</Tag>
            )}
            {estado.enviarPorMensajeria && (
              <Tag variant="warning">📦 Enviar por mensajería</Tag>
            )}
          </Flex>
        }
      >
        <Flex direction="column" gap="medium">
          <TablaDocsAEnviar
            contenedores={contenedoresSeleccionados}
            pedidoInfo={pedidoInfo}
            tipoPedido={tipoPedido}
            fotosDeCarga={fotosDeCarga}
          />

          {esMulti && entregaDivergente && (
            <Alert title="Estados de envío/recepción distintos" variant="warning">
              Los contenedores seleccionados no están en el mismo punto de envío/recepción.
              Los controles muestran el primero ({contenedor.nombre ?? contenedor.id}); lo que
              cambies se aplicará a todos y puede sobrescribir el estado de los demás.
            </Alert>
          )}

          {!todosSubidos && !estado.permitirEnviar && (
            <Alert title="Faltan documentos" variant="warning">
              Hay documentos pendientes de subir. Aun así, administración puede aprobar el envío manualmente.
            </Alert>
          )}

          <Divider />

          <Flex direction="column" gap="small">
            <Text format={{ fontWeight: "demibold" }}>Envío por mensajería</Text>
            {esMulti && (
              <Text variant="microcopy">
                Se aplica a los {contenedoresSeleccionados.length} contenedores seleccionados.
              </Text>
            )}
            <Box>
              <Checkbox
                checked={estado.enviarPorMensajeria}
                onChange={(checked: boolean) =>
                  set({
                    enviarPorMensajeria: checked,
                    ...(checked ? {} : { datosEnvioMensajeria: "" }),
                  })
                }
                name="enviar_mensajeria"
                description="Admin marca esta casilla para que logística prepare la mensajería."
              >
                Enviar documentación por mensajería
              </Checkbox>
            </Box>

            {estado.enviarPorMensajeria && (
              <Flex direction="column" gap="small">
                <TextArea
                  label="Datos para administración (nº de copias, dirección de envío, contacto)"
                  name="datos_envio_mensajeria"
                  value={estado.datosEnvioMensajeria}
                  rows={4}
                  onChange={(v: string) => set({ datosEnvioMensajeria: v ?? "" })}
                  description="Información para gestionar el envío por mensajería. Se aplica a los contenedores seleccionados."
                />

                <Flex direction="column" gap="extra-small">
                  <Text format={{ fontWeight: "demibold" }}>Albarán de recogida</Text>
                  {esMulti && (
                    <Text variant="microcopy">
                      Se subirá a los {contenedoresSeleccionados.length} contenedores seleccionados.
                    </Text>
                  )}
                  <AlbaranMensajeriaUpload
                    archivo={contenedor.albaran_mensajeria ?? null}
                    numeroPedido={numeroPedido}
                    companyId={companyId}
                    contenedorId={contenedor.id}
                    destinos={destinosAlbaran}
                    actions={actions}
                    onUpdated={onUpdated}
                  />
                  {contenedor.albaran_mensajeria?.created_at && (
                    <Text variant="microcopy">
                      Subido el {formatDateES(contenedor.albaran_mensajeria.created_at)}
                    </Text>
                  )}
                </Flex>
              </Flex>
            )}
          </Flex>

          <Divider />
          <Flex direction="row" gap="small" align="center">
            <Icon color="alert" name="warning" size="large" />
            <Flex direction="column" gap="extra-small">
              {!estado.permitirEnviar ? (
                <Button
                  variant="primary"
                  overlay={
                    motivosEtapasPendientes.length > 0 ? (
                      <ConfirmPermitirEnvioModal
                        modalId={`permitir-envio-${contenedor.id}`}
                        motivos={motivosEtapasPendientes}
                        onConfirm={aplicarPermitir}
                        actions={actions}
                      />
                    ) : undefined
                  }
                  onClick={
                    motivosEtapasPendientes.length > 0 ? undefined : aplicarPermitir
                  }
                >
                  Permitir envío de documentación al cliente
                </Button>
              ) : (
                <Button
                  variant="destructive"
                  overlay={
                    hayDatosEtapa6 ? (
                      <ConfirmRevocarEnvioModal
                        modalId={`revocar-envio-${contenedor.id}`}
                        valoresAPerder={valoresEtapa6}
                        onConfirm={aplicarRevocar}
                        actions={actions}
                      />
                    ) : undefined
                  }
                  onClick={hayDatosEtapa6 ? undefined : aplicarRevocar}
                >
                  Revocar permiso de envío
                </Button>
              )}
              <Text variant="microcopy">
                Confirmación manual de administración: toda la documentación está lista para enviarse al cliente.
                {esMulti ? " Se aplica a los contenedores seleccionados." : ""}
              </Text>
            </Flex>
          </Flex>
        </Flex>
      </SeccionBloque>

      <SeccionBloque
        identificador={identificadorRecepcion}
        titulo="Recepción y retirada"
        estado={estadoRecepcion}
        envioNoPermitido={recepcionBloqueada}
        defaultAbierta={!recepcionBloqueada && !estado.mercanciaRetirada}
        badge={
          recepcionBloqueada ? (
            <Tag variant="default">Esperando aprobación de envío</Tag>
          ) : estado.mercanciaRetirada ? (
            <Tag variant="success">Retirada</Tag>
          ) : estado.documentacionRecibida ? (
            <Tag variant="info">Documentación recibida</Tag>
          ) : (
            <Tag variant="default">Pendiente</Tag>
          )
        }
      >
        <Flex direction="column" gap="medium">
          {recepcionBloqueada ? (
            <Alert title="Etapa bloqueada" variant="warning">
              Marca antes "Permitir enviar documentación al cliente" en la etapa anterior para poder rellenar la recepción y retirada.
            </Alert>
          ) : (
            <Alert title="Tras enviar al cliente" variant="info">
              Marca la recepción y retirada cuando el cliente confirme.
              {esMulti ? " Se aplica a los contenedores seleccionados." : ""}
            </Alert>
          )}

          <Flex direction="row" gap="medium">
            <Box>
              <Checkbox
                checked={estado.documentacionRecibida}
                onChange={(checked: boolean) => set({ documentacionRecibida: checked })}
                name="doc_recibida"
                readOnly={recepcionBloqueada}
              >
                Documentación recibida por el cliente
              </Checkbox>
            </Box>
            <Box>
              <DateInput
                label="Fecha de envío de originales al cliente"
                name="fecha_llegada"
                value={estado.fechaLlegadaContenedor ?? undefined}
                onChange={(v: BaseDate | null) => set({ fechaLlegadaContenedor: v ?? null })}
                readOnly={recepcionBloqueada || !estado.documentacionRecibida}
                description={
                  recepcionBloqueada
                    ? "Etapa bloqueada hasta aprobar el envío."
                    : estado.documentacionRecibida
                      ? "Fecha real de envío de originales al cliente."
                      : "Marca antes 'Documentación recibida'."
                }
              />
            </Box>
          </Flex>

          <Divider />

          <Flex direction="row" gap="medium">
            <Box>
              <Checkbox
                checked={estado.mercanciaRetirada}
                onChange={(checked: boolean) => set({ mercanciaRetirada: checked })}
                name="mercancia_retirada"
                readOnly={recepcionBloqueada}
              >
                Mercancía retirada por el cliente
              </Checkbox>
            </Box>
            <Box>
              <DateInput
                label="Fecha de retirada"
                name="fecha_retirada"
                value={estado.fechaRetirada ?? undefined}
                onChange={(v: BaseDate | null) => set({ fechaRetirada: v ?? null })}
                readOnly={recepcionBloqueada || !estado.mercanciaRetirada}
                description={
                  recepcionBloqueada
                    ? "Etapa bloqueada hasta aprobar el envío."
                    : estado.mercanciaRetirada
                      ? "Fecha en la que el cliente retiró la mercancía."
                      : "Marca antes 'Mercancía retirada'."
                }
              />
            </Box>
          </Flex>
        </Flex>
      </SeccionBloque>
    </Flex>
  );
};

export default EnvioDocumentacionSection;
