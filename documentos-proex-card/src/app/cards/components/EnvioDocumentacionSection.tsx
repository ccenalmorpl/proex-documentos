import React from "react";
import {
  Box,
  Flex,
  Text,
  Checkbox,
  Button,
  StatusTag,
  Alert,
  DateInput,
  Divider,
  Tag,
  Link,
  Icon,
} from "@hubspot/ui-extensions";

import { SeccionBloque, type EstadoEtapa } from "./ui/SeccionBloque";
import ConfirmPermitirEnvioModal from "./ConfirmPermitirEnvioModal";
import ConfirmRevocarEnvioModal from "./ConfirmRevocarEnvioModal";
import {
  buildDocumentosContenedorResumen,
  type ArchivoSimple,
  type BaseDate,
  type DocStatus,
  type EstadoEntrega,
  type FileSlot,
  type PedidoDetalleContenedor,
  type PedidoDetalleInfo,
} from "../utils/documentos.utils";
import { type TipoPedido } from "../constants/documentos.constants";

interface EnvioDocumentacionSectionProps {
  estado: EstadoEntrega;
  onChange: (next: EstadoEntrega) => void;
  pedidoInfo: PedidoDetalleInfo;
  contenedor: PedidoDetalleContenedor;
  fotosDeCarga: boolean;
  tipoPedido: TipoPedido;
  identificadorEnvio?: string;
  identificadorRecepcion?: string;
  actions: any;
}

const FAKE_ALBARAN = "albaran_mensajeria.pdf";

const MAX_POR_FILA = 4;

const chunk = <T,>(arr: T[], size: number): T[][] => {
  const out: T[][] = [];
  for (let i = 0; i < arr.length; i += size) {
    out.push(arr.slice(i, i + size));
  }
  return out;
};

const ResumenDocumentos: React.FC<{
  docs: DocStatus[];
  otrosArchivos: ArchivoSimple[];
}> = ({ docs, otrosArchivos }) => {
  const subidos  = docs.filter((d) => d.generado).length;
  const total    = docs.length;
  const completo = total > 0 && subidos === total;
  const filas    = chunk(docs, MAX_POR_FILA);

  const renderValor = (d: DocStatus) => {
    if (!d.generado) return <Tag variant="warning">Pendiente</Tag>;
    if (d.key === "otros") {
      return (
        <Flex direction="column" gap="extra-small" align="center">
          {otrosArchivos.map((a) =>
            a.url ? (
              <Link key={a.file_id} href={{ url: a.url, external: true }}>
                {a.name}
              </Link>
            ) : (
              <Text key={a.file_id} variant="microcopy">{a.name}</Text>
            ),
          )}
        </Flex>
      );
    }
    return d.url ? (
      <Link href={{ url: d.url, external: true }}>Ver documento</Link>
    ) : (
      <Text variant="microcopy">Ver documento</Text>
    );
  };

  return (
    <Box>
      <Flex direction="column" gap="extra-small">
        <Flex direction="row" gap="sm" align="center">
          <Text format={{ fontWeight: "demibold" }}>Documentos a enviar al cliente</Text>
          <Tag variant={completo ? "success" : "warning"}>
            {subidos}/{total}
          </Tag>
        </Flex>
        <Text variant="microcopy">
          Resumen de los documentos que se enviarán. Todos deben estar subidos para validar el envío.
        </Text>

        <Flex direction="column" gap="small">
          {filas.map((fila, i) => (
            <Flex key={i} direction="row" gap="medium" align="start">
              {fila.map((d) => (
                <Box key={d.key} flex={1}>
                  <Flex direction="column" gap="sm" align="center">
                    <Text format={{ fontWeight: "demibold" }}>{d.label}:</Text>
                    {renderValor(d)}
                  </Flex>
                </Box>
              ))}
              {Array.from({ length: MAX_POR_FILA - fila.length }).map((_, j) => (
                <Box key={`empty-${j}`} flex={1}>
                  <Text> </Text>
                </Box>
              ))}
            </Flex>
          ))}
        </Flex>
      </Flex>
    </Box>
  );
};

const FileMockRow: React.FC<{
  slot: FileSlot;
  fakeName: string;
  onChange: (slot: FileSlot) => void;
}> = ({ slot, fakeName, onChange }) => (
  <Flex direction="row" gap="sm" align="center">
    {slot.filename ? (
      <>
        <StatusTag variant="success">{slot.filename}</StatusTag>
        <Button variant="secondary" size="xs" onClick={() => onChange({ filename: null })}>
          Quitar
        </Button>
      </>
    ) : (
      <>
        <Button variant="secondary" size="sm" onClick={() => onChange({ filename: fakeName })}>
          Subir archivo
        </Button>
        <Text variant="microcopy">Sin archivo</Text>
      </>
    )}
  </Flex>
);

const EnvioDocumentacionSection: React.FC<EnvioDocumentacionSectionProps> = ({
  estado,
  onChange,
  pedidoInfo,
  contenedor,
  fotosDeCarga,
  tipoPedido,
  identificadorEnvio = "5",
  identificadorRecepcion = "6",
  actions,
}) => {
  const set = (patch: Partial<EstadoEntrega>) => onChange({ ...estado, ...patch });

  const docsAEnviar: DocStatus[] = buildDocumentosContenedorResumen({
    contenedor,
    pedidoInfo,
    tipoPedido,
    fotosDeCarga,
  });

  const todosSubidos = docsAEnviar.every((d) => d.generado);

  const importePendiente = parseFloat(contenedor.importe_pendiente_cobro ?? "0") || 0;
  const pagoCompletado = importePendiente <= 0;

  const motivosEtapasPendientes: string[] = [];
  if (!pagoCompletado) motivosEtapasPendientes.push("El pago del contenedor no está completado.");
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
          <ResumenDocumentos docs={docsAEnviar} otrosArchivos={contenedor.otros_documentos} />

          {!todosSubidos && !estado.permitirEnviar && (
            <Alert title="Faltan documentos" variant="warning">
              Hay documentos pendientes de subir. Aun así, administración puede aprobar el envío manualmente.
            </Alert>
          )}

          <Divider />

          <Flex direction="column" gap="small">
            <Text format={{ fontWeight: "demibold" }}>Envío por mensajería</Text>
            <Flex direction="row" gap="medium">
              <Box>
                <Checkbox
                  checked={estado.enviarPorMensajeria}
                  onChange={(checked: boolean) =>
                    set({
                      enviarPorMensajeria: checked,
                      ...(checked ? {} : { albaranMensajeria: { filename: null } }),
                    })
                  }
                  name="enviar_mensajeria"
                  description="Admin marca esta casilla para que logística prepare la mensajería."
                >
                  Enviar documentación por mensajería
                </Checkbox>
              </Box>

              {estado.enviarPorMensajeria && (
                <Box flex={1}>
                  <Flex direction="column" gap="extra-small">
                    <Text format={{ fontWeight: "demibold" }}>Albarán de envío de documentación</Text>
                    <FileMockRow
                      slot={estado.albaranMensajeria}
                      fakeName={FAKE_ALBARAN}
                      onChange={(s) => set({ albaranMensajeria: s })}
                    />
                  </Flex>
                </Box>
              )}
            </Flex>
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
              </Text>
            </Flex>
          </Flex>
        </Flex>
      </SeccionBloque>

      <SeccionBloque
        identificador={identificadorRecepcion}
        titulo="Recepción y retirada"
        estado={estadoRecepcion}
        bloqueada={recepcionBloqueada}
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
