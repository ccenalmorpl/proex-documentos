import React, { useEffect, useState } from "react";
import { DateInput, Flex, Input, NumberInput, Text } from "@hubspot/ui-extensions";

import {
  updateContenedorBooking,
  updateContenedorDatos,
  updateContenedorFechas,
  type UpdateContenedorDatosPayload,
} from "../utils/gestion.api";
import {
  baseDateToIso,
  isoToBaseDate,
  type BaseDate,
  type PedidoDetalleContenedor,
} from "../utils/documentos.utils";

interface DatosUnidadEditableProps {
  esCamion: boolean;
  contenedor: PedidoDetalleContenedor;
  /** Booking propio del contenedor (Cambio 2: individual por contenedor). */
  numeroBooking: string | null;
  numeroPedido: string;
  companyId: string;
  actions: any;
  onUpdated: () => void | Promise<void>;
}

const toNum = (v: string | null): number | undefined => {
  if (v === null || v.trim() === "") return undefined;
  const n = Number(v);
  return Number.isFinite(n) ? n : undefined;
};

const numToStr = (n: number | undefined): string => (n === undefined ? "" : String(n));

const computeVgm = (bruto: number | undefined, tara: number | undefined): string => {
  if (bruto === undefined && tara === undefined) return "—";
  return String((bruto ?? 0) + (tara ?? 0));
};

const DatosUnidadEditable: React.FC<DatosUnidadEditableProps> = ({
  esCamion,
  contenedor,
  numeroBooking,
  numeroPedido,
  companyId,
  actions,
  onUpdated,
}) => {
  const [numero, setNumero] = useState<string>(contenedor.numero_contenedor ?? "");
  const [precinto, setPrecinto] = useState<string>(contenedor.numero_precinto ?? "");
  const [pesoBruto, setPesoBruto] = useState<number | undefined>(toNum(contenedor.peso_bruto));
  const [pesoNeto, setPesoNeto] = useState<number | undefined>(toNum(contenedor.peso_neto));
  const [tara, setTara] = useState<number | undefined>(toNum(contenedor.tara));
  const [etd, setEtd] = useState<BaseDate | null>(isoToBaseDate(contenedor.etd));
  const [eta, setEta] = useState<BaseDate | null>(isoToBaseDate(contenedor.eta));
  const [booking, setBooking] = useState<string>(numeroBooking ?? "");
  const [savingFields, setSavingFields] = useState<Set<string>>(new Set());

  // Resync solo al cambiar de unidad: el estado local es la fuente de verdad
  // mientras editas este contenedor, para que el refetch de un campo no pise lo
  // tecleado en otro.
  useEffect(() => {
    setNumero(contenedor.numero_contenedor ?? "");
    setPrecinto(contenedor.numero_precinto ?? "");
    setPesoBruto(toNum(contenedor.peso_bruto));
    setPesoNeto(toNum(contenedor.peso_neto));
    setTara(toNum(contenedor.tara));
    setEtd(isoToBaseDate(contenedor.etd));
    setEta(isoToBaseDate(contenedor.eta));
  }, [contenedor.id]);

  useEffect(() => {
    setBooking(numeroBooking ?? "");
  }, [numeroBooking]);

  const labelNumero = esCamion ? "Nº camión" : "Nº contenedor";
  const labelPrecinto = esCamion ? "Matrícula" : "Precinto";
  const tituloAlerta = `${esCamion ? "Camión" : "Contenedor"} ${contenedor.nombre ?? ""}`.trim();

  const isSaving = (campo: string) => savingFields.has(campo);

  // Guarda al perder el foco; solo el campo en curso queda readOnly mientras
  // el PATCH + refetch están en vuelo.
  const ejecutarGuardado = async (
    campo: string,
    accion: () => Promise<{ success: boolean; error?: string | null }>,
    mensajeOk: string,
  ) => {
    setSavingFields((prev) => new Set(prev).add(campo));
    try {
      const res = await accion();
      if (!res.success) throw new Error(res.error ?? "No se pudo guardar");
      await onUpdated();
      actions?.addAlert?.({ type: "success", title: tituloAlerta, message: mensajeOk });
    } catch (e: any) {
      actions?.addAlert?.({
        type: "danger",
        title: `${tituloAlerta} — error`,
        message: String(e?.message ?? e),
      });
    } finally {
      setSavingFields((prev) => {
        const next = new Set(prev);
        next.delete(campo);
        return next;
      });
    }
  };

  const guardarContenedor = (
    campo: string,
    payload: UpdateContenedorDatosPayload,
    mensajeOk: string,
  ) =>
    ejecutarGuardado(
      campo,
      () => updateContenedorDatos(numeroPedido, companyId, contenedor.id, payload),
      mensajeOk,
    );

  // ETD/ETA viven en el deal del contenedor (no en el objeto Contenedor): endpoint propio.
  const guardarFecha = (campo: "etd" | "eta", nextIso: string | null, mensajeOk: string) =>
    ejecutarGuardado(
      campo,
      () => updateContenedorFechas(numeroPedido, companyId, contenedor.id, { [campo]: nextIso }),
      mensajeOk,
    );

  return (
    <Flex direction="row" wrap="wrap" gap="medium">
      <Input
        label={labelNumero}
        name="numero_contenedor"
        value={numero}
        readOnly={isSaving("numero_contenedor")}
        onChange={(v) => setNumero(v ?? "")}
        onBlur={(v) => {
          if (isSaving("numero_contenedor")) return;
          const next = v ?? "";
          if (next !== (contenedor.numero_contenedor ?? "")) {
            guardarContenedor("numero_contenedor", { numero_contenedor: next }, `${labelNumero} actualizado`);
          }
        }}
      />
      <Input
        label={labelPrecinto}
        name="numero_precinto"
        value={precinto}
        readOnly={isSaving("numero_precinto")}
        onChange={(v) => setPrecinto(v ?? "")}
        onBlur={(v) => {
          if (isSaving("numero_precinto")) return;
          const next = v ?? "";
          if (next !== (contenedor.numero_precinto ?? "")) {
            guardarContenedor("numero_precinto", { numero_precinto: next }, `${labelPrecinto} actualizado`);
          }
        }}
      />
      <NumberInput
        label="Peso bruto (kg)"
        name="peso_bruto"
        value={pesoBruto}
        precision={2}
        readOnly={isSaving("peso_bruto")}
        onChange={setPesoBruto}
        onBlur={(v) => {
          if (isSaving("peso_bruto")) return;
          if (numToStr(v) !== (contenedor.peso_bruto ?? "")) {
            guardarContenedor("peso_bruto", { peso_bruto: numToStr(v) }, "Peso bruto actualizado");
          }
        }}
      />
      <NumberInput
        label="Peso neto (kg)"
        name="peso_neto"
        value={pesoNeto}
        precision={2}
        readOnly={isSaving("peso_neto")}
        onChange={setPesoNeto}
        onBlur={(v) => {
          if (isSaving("peso_neto")) return;
          if (numToStr(v) !== (contenedor.peso_neto ?? "")) {
            guardarContenedor("peso_neto", { peso_neto: numToStr(v) }, "Peso neto actualizado");
          }
        }}
      />

      {!esCamion && (
        <>
          <NumberInput
            label="Tara (kg)"
            name="tara"
            value={tara}
            precision={2}
            readOnly={isSaving("tara")}
            onChange={setTara}
            onBlur={(v) => {
              if (isSaving("tara")) return;
              if (numToStr(v) !== (contenedor.tara ?? "")) {
                guardarContenedor("tara", { tara: numToStr(v) }, "Tara actualizada");
              }
            }}
          />
          <DateInput
            label="ETD"
            name="etd"
            value={etd ?? undefined}
            readOnly={isSaving("etd")}
            format="L"
            onChange={(v) => {
              const next: BaseDate | null = v
                ? { year: v.year, month: v.month, date: v.date }
                : null;
              setEtd(next);
              const nextIso = baseDateToIso(next);
              if (nextIso !== (contenedor.etd ?? null)) {
                guardarFecha("etd", nextIso, "ETD actualizada");
              }
            }}
          />
          <DateInput
            label="ETA"
            name="eta"
            value={eta ?? undefined}
            readOnly={isSaving("eta")}
            format="L"
            onChange={(v) => {
              const next: BaseDate | null = v
                ? { year: v.year, month: v.month, date: v.date }
                : null;
              setEta(next);
              const nextIso = baseDateToIso(next);
              if (nextIso !== (contenedor.eta ?? null)) {
                guardarFecha("eta", nextIso, "ETA actualizada");
              }
            }}
          />
          <Flex direction="column" gap="extra-small">
            <Text variant="microcopy">VGM (kg)</Text>
            <Text>{computeVgm(pesoBruto, tara)}</Text>
          </Flex>
          <Input
            label="Nº de booking"
            name="numero_de_booking"
            value={booking}
            readOnly={isSaving("numero_de_booking")}
            onChange={(v) => setBooking(v ?? "")}
            onBlur={(v) => {
              if (isSaving("numero_de_booking")) return;
              const next = v ?? "";
              if (next !== (numeroBooking ?? "")) {
                ejecutarGuardado(
                  "numero_de_booking",
                  () => updateContenedorBooking(numeroPedido, companyId, contenedor.id, next),
                  "Nº de booking actualizado",
                );
              }
            }}
          />
        </>
      )}
    </Flex>
  );
};

export default DatosUnidadEditable;
