import asyncio
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple

from app.shared.hubspot_batch import batch_read_associations

from hubspot.crm.deals import (
    Filter as DealFilter,
    FilterGroup as DealFilterGroup,
    PublicObjectSearchRequest as DealSearchRequest,
    SimplePublicObjectInput as DealSimplePublicObjectInput,
)
from hubspot.crm.objects import (
    BatchInputSimplePublicObjectBatchInput,
    BatchReadInputSimplePublicObjectId,
    SimplePublicObjectBatchInput,
    SimplePublicObjectId,
)

from app.core.constants import (
    BL_FILE_PREFIX_BORRADOR,
    BL_FILE_PREFIX_FINAL,
    COMPANY_PROP_NAME,
    CONTENEDOR_PROP_CERT_ORIGEN,
    CONTENEDOR_PROP_CERT_ORIGEN_BORRADOR,
    CONTENEDOR_PROP_CERT_ORIGEN_VALIDADO,
    CONTENEDOR_PROP_CERT_ORIGEN_ENVIAR_FIRMAR,
    CONTENEDOR_PROP_CERT_SANITARIO_ENVIAR_FIRMAR,
    CONTENEDOR_PROP_CERT_SANITARIO,
    CONTENEDOR_PROP_CERT_SANITARIO_VALIDADO,
    CONTENEDOR_PROP_DOCUMENTACION_RECIBIDA,
    CONTENEDOR_PROP_DOCUMENTOS,
    CONTENEDOR_PROP_ENVIAR_POR_MENSAJERIA,
    CONTENEDOR_PROP_FECHA_LLEGADA_CONTENEDOR,
    CONTENEDOR_PROP_FECHA_RETIRADA_MERCANCIA,
    CONTENEDOR_PROP_DATOS_ENVIO_MENSAJERIA,
    CONTENEDOR_PROP_ALBARAN_MENSAJERIA,
    CONTENEDOR_PROP_FOTOS_DE_CARGA,
    CONTENEDOR_PROP_MERCANCIA_RETIRADA,
    CONTENEDOR_PROP_OTROS_DOCUMENTOS,
    CONTENEDOR_PROP_PERMITIR_ENVIAR_DOCUMENTACION,
    CONTENEDOR_PROP_TIPO_CONTENEDOR,
    CONTENEDOR_PROP_WAIVER_VALIDADO,
    DOC_TIPO_TO_PREFIX,
    FILE_TYPE_CONFIG,
    COMPANY_PROP_TIPO_CLIENTE,
    CONTENEDOR_DETALLE_PROPERTIES,
    COTIZACION_ALMACEN_PROEX_SAN_ROQUE,
    COTIZACION_PROP_ALMACEN,
    COTIZACION_PROP_COMENTARIOS_LOGISTICA,
    COTIZACION_PROP_TIPO_DE_VENTA,
    COTIZACION_PROP_CONSIGNEE,
    COTIZACION_PROP_LOCALIDAD_DESTINO,
    COTIZACION_PROP_LUGAR_CARGA,
    COTIZACION_PROP_NOTIFY,
    COTIZACION_PROP_PUERTO_DESTINO,
    COTIZACION_PROP_PUERTO_SALIDA,
    DEAL_PROP_DATOS_DEL_CHOFER,
    DEAL_PROP_DIRECCION_DE_ENTREGA,
    DEAL_PROP_FECHA_DE_ENTREGA,
    DEAL_PROP_TRANSITARIO_DEL_PEDIDO,
    DEAL_PROP_TRANSITARIO_TERRESTRE_DEL_PEDIDO,
    DEAL_DETALLE_PROPERTIES,
    DEAL_PROP_BL_VALIDADO_ADMINISTRACION,
    DEAL_PROP_BL_VALIDADO_LOGISTICA,
    DEAL_PROP_BL_ENVIADO_CLIENTE,
    DEAL_PROP_BORRADOR_BL,
    DEAL_PROP_NUMERO_DE_BOOKING,
    DEAL_PROP_CAMBIOS_EN_BL,
    DEAL_PROP_CARTA_DE_PORTE_PROEX,
    DEAL_PROP_DESCRIPCION_MERCANCIA,
    DEAL_PROP_ETA,
    DEAL_PROP_ETD,
    DEAL_PROP_FACTURA_DEL_PEDIDO,
    DEAL_PROP_FECHA_FACTURACION_PEDIDO,
    DEAL_PROP_FECHA_VENCIMIENTO_FACTURA,
    DEAL_PROP_NUMERO_DE_FACTURA,
    DEAL_PROP_FOTOS_DE_CARGA,
    DEAL_PROP_NUMERO_DE_PEDIDO,
    DEAL_PROP_OBSERVACIONES,
    DEAL_PROP_PACKING_LIST_PROEX,
    DEAL_PROP_PIPELINE,
    DEAL_PROP_TIPO_DE_BL,
    DEAL_SELECT_PROPERTIES,
    OBJECT_TYPE_COMPANY,
    OBJECT_TYPE_CONTENEDOR,
    OBJECT_TYPE_DEAL,
    OBJECT_TYPE_PROVEEDOR,
    PEDIDO_PIPELINE_ID,
    DOCUMENTO_PIPELINE_ID,
    CAMION_TIPO_CONTENEDOR,
    TIPO_FLUJO_CAMION,
    TIPO_FLUJO_CAMION_SAN_ROQUE,
    TIPO_FLUJO_CONTENEDOR,
    TIPO_FLUJO_CONTENEDOR_SAN_ROQUE,
)
from app.pedidos.schemas import (
    ArchivoSimple,
    BLArchivo,
    CertificadoArchivo,
    ContenedorDetalleItem,
    DealFile,
    DeleteFileResponse,
    EmpresaResumen,
    OtroDocArchivo,
    PedidoCompanyResumen,
    PedidoDetalle,
    PedidoDetalleResponse,
    PedidoInfo,
    PedidosListaResponse,
    SelectOption,
    UpdateContenedorBookingRequest,
    UpdateContenedorDatosRequest,
    UpdateContenedorEntregaRequest,
    UpdateContenedorFechasRequest,
    UpdateContenedoresCertificadosRequest,
    UpdatePedidoBLRequest,
    UpdatePedidoResponse,
    UploadFileResponse,
)
from app.shared.files import (
    delete_file,
    fetch_file_metadata,
    parse_file_ids,
    serialize_file_ids,
    upload_file,
)
from app.shared.hubspot_client import hubspot_client
from app.shared.properties import fetch_select_options, resolve_enum_label
from app.shared.elementos import (
    get_elementos_fabricante_por_contenedor,
    calcular_descripcion_mercancia_agregada,
)

logger = logging.getLogger(__name__)

FILE_METADATA_WORKERS = 8


class PedidoNoEncontradoError(Exception):
    """Pedido no existe en el pipeline o no pertenece a la empresa indicada."""

    def __init__(self, numero_de_pedido: str):
        self.numero_de_pedido = numero_de_pedido
        super().__init__(f"numero_de_pedido={numero_de_pedido!r} no encontrado")


def _get_contenedores_for_company(client, company_id: str) -> List[str]:
    contenedor_ids: List[str] = []
    seen: set = set()
    after: Optional[str] = None
    page = 0

    while True:
        page += 1
        kwargs = {
            "object_type": OBJECT_TYPE_COMPANY,
            "object_id": company_id,
            "to_object_type": OBJECT_TYPE_CONTENEDOR,
            "limit": 100,
        }
        if after:
            kwargs["after"] = after

        try:
            resp = client.crm.associations.v4.basic_api.get_page(**kwargs)
        except Exception as e:
            logger.warning(
                f"  [assoc] error company={company_id} página={page}: {e}"
            )
            break

        for assoc in (resp.results or []):
            cid = str(assoc.to_object_id)
            if cid not in seen:
                seen.add(cid)
                contenedor_ids.append(cid)

        if resp.paging and resp.paging.next:
            after = resp.paging.next.after
        else:
            break

    return contenedor_ids


def _get_deal_ids_for_contenedores(
    client, contenedor_ids: List[str],
) -> Dict[str, List[str]]:
    if not contenedor_ids:
        return {}
    t = time.monotonic()
    mapping = batch_read_associations(
        client, OBJECT_TYPE_CONTENEDOR, OBJECT_TYPE_DEAL, contenedor_ids,
    )
    logger.info(
        f"[TIMER] _get_deal_ids_for_contenedores: {time.monotonic() - t:.2f}s "
        f"contenedores={len(contenedor_ids)}"
    )
    return mapping


def _get_contenedor_ids_for_deals(
    client, deal_ids: List[str],
) -> Dict[str, List[str]]:
    if not deal_ids:
        return {}
    t = time.monotonic()
    mapping = batch_read_associations(
        client, OBJECT_TYPE_DEAL, OBJECT_TYPE_CONTENEDOR, deal_ids,
    )
    logger.info(
        f"[TIMER] _get_contenedor_ids_for_deals: {time.monotonic() - t:.2f}s "
        f"deals={len(deal_ids)}"
    )
    return mapping


def _get_company_ids_for_contenedor(client, contenedor_id: str) -> Set[str]:
    company_ids: Set[str] = set()
    try:
        resp = client.crm.associations.v4.basic_api.get_page(
            object_type=OBJECT_TYPE_CONTENEDOR,
            object_id=contenedor_id,
            to_object_type=OBJECT_TYPE_COMPANY,
            limit=10,
        )
        for assoc in (resp.results or []):
            company_ids.add(str(assoc.to_object_id))
    except Exception as e:
        logger.warning(f"  [assoc] error contenedor->company {contenedor_id}: {e}")
    return company_ids


def _batch_read_deals_min(client, deal_ids: List[str]) -> Dict[str, dict]:
    result: Dict[str, dict] = {}
    if not deal_ids:
        return result

    minimal_props = [DEAL_PROP_NUMERO_DE_PEDIDO, DEAL_PROP_PIPELINE, "dealname"]
    chunk_size = 100

    for i in range(0, len(deal_ids), chunk_size):
        chunk = deal_ids[i:i + chunk_size]
        batch_input = BatchReadInputSimplePublicObjectId(
            properties=minimal_props,
            inputs=[SimplePublicObjectId(id=did) for did in chunk],
        )
        resp = client.crm.objects.batch_api.read(
            object_type=OBJECT_TYPE_DEAL,
            batch_read_input_simple_public_object_id=batch_input,
        )
        for obj in (resp.results or []):
            result[obj.id] = obj.properties or {}

    return result


def _batch_read_deals_detalle(client, deal_ids: List[str]) -> Dict[str, dict]:
    result: Dict[str, dict] = {}
    if not deal_ids:
        return result

    chunk_size = 100
    for i in range(0, len(deal_ids), chunk_size):
        chunk = deal_ids[i:i + chunk_size]
        batch_input = BatchReadInputSimplePublicObjectId(
            properties=DEAL_DETALLE_PROPERTIES,
            inputs=[SimplePublicObjectId(id=did) for did in chunk],
        )
        resp = client.crm.objects.batch_api.read(
            object_type=OBJECT_TYPE_DEAL,
            batch_read_input_simple_public_object_id=batch_input,
        )
        for obj in (resp.results or []):
            result[obj.id] = obj.properties or {}

    return result


def _batch_read_contenedores_detalle(
    client, contenedor_ids: List[str],
) -> Dict[str, dict]:
    result: Dict[str, dict] = {}
    if not contenedor_ids:
        return result

    chunk_size = 100
    for i in range(0, len(contenedor_ids), chunk_size):
        chunk = contenedor_ids[i:i + chunk_size]
        batch_input = BatchReadInputSimplePublicObjectId(
            properties=CONTENEDOR_DETALLE_PROPERTIES,
            inputs=[SimplePublicObjectId(id=cid) for cid in chunk],
        )
        resp = client.crm.objects.batch_api.read(
            object_type=OBJECT_TYPE_CONTENEDOR,
            batch_read_input_simple_public_object_id=batch_input,
        )
        for obj in (resp.results or []):
            result[obj.id] = obj.properties or {}

    return result


def _resolve_numero_pedido(
    deal_ids: List[str], deal_props_by_id: Dict[str, dict]
) -> Optional[str]:
    for did in deal_ids:
        props = deal_props_by_id.get(did) or {}
        if props.get(DEAL_PROP_PIPELINE) != PEDIDO_PIPELINE_ID:
            continue
        numero = (props.get(DEAL_PROP_NUMERO_DE_PEDIDO) or "").strip()
        if numero:
            return numero
    return None


def _resolve_cotizacion_dealname(
    deal_ids: List[str], deal_props_by_id: Dict[str, dict]
) -> Optional[str]:
    for did in deal_ids:
        props = deal_props_by_id.get(did) or {}
        if props.get(DEAL_PROP_PIPELINE) == PEDIDO_PIPELINE_ID:
            continue
        dealname = (props.get("dealname") or "").strip()
        if dealname:
            return dealname
    return None


def _list_pedidos_sync(company_id: str) -> PedidosListaResponse:
    client = hubspot_client.get_client()

    contenedor_ids = _get_contenedores_for_company(client, company_id)
    logger.info(
        f"[list_pedidos] company={company_id} contenedores={len(contenedor_ids)}"
    )
    if not contenedor_ids:
        return PedidosListaResponse()

    contenedor_to_deals = _get_deal_ids_for_contenedores(client, contenedor_ids)
    unique_deal_ids: List[str] = list({
        did for dids in contenedor_to_deals.values() for did in dids
    })
    deal_props_by_id = _batch_read_deals_min(client, unique_deal_ids)

    counts: Dict[str, int] = {}
    nombres_cotizacion: Dict[str, str] = {}
    sin_pedido = 0

    # TODO: filtrar pedidos sin facturas cuando el endpoint de facturación esté listo
    for cid in contenedor_ids:
        deals_del_contenedor = contenedor_to_deals.get(cid, [])
        numero = _resolve_numero_pedido(deals_del_contenedor, deal_props_by_id)
        if not numero:
            sin_pedido += 1
            continue
        counts[numero] = counts.get(numero, 0) + 1
        if numero not in nombres_cotizacion:
            dealname_cot = _resolve_cotizacion_dealname(
                deals_del_contenedor, deal_props_by_id
            )
            if dealname_cot:
                nombres_cotizacion[numero] = dealname_cot

    logger.info(
        f"[list_pedidos] company={company_id} pedidos_distintos={len(counts)} "
        f"contenedores_sin_pedido={sin_pedido} con_cotizacion={len(nombres_cotizacion)}"
    )

    pedidos_company = [
        PedidoCompanyResumen(
            numero_de_pedido=numero,
            numero_contenedores_pedido=count,
            nombre_cotizacion=nombres_cotizacion.get(numero),
        )
        for numero, count in counts.items()
    ]
    return PedidosListaResponse(success=True, pedidos_company=pedidos_company)


async def list_pedidos_for_company(company_id: str) -> PedidosListaResponse:
    logger.info(f"[list_pedidos] inicio company_id={company_id!r}")
    try:
        return await asyncio.to_thread(_list_pedidos_sync, company_id)
    except Exception as e:
        logger.error(f"[list_pedidos] ERROR company={company_id}: {e}", exc_info=True)
        return PedidosListaResponse(success=False, error=str(e))


def _search_pedidos_by_numero(client, numero: str, pipeline_id: str) -> List[str]:
    # Un expediente tiene un deal por contenedor y los hay de 20 o más: sin
    # paginar, la card solo veía los 10 primeros (P-65571985983, 28/10/2026).
    filters = [
        DealFilter(property_name=DEAL_PROP_NUMERO_DE_PEDIDO, operator="EQ", value=numero),
        DealFilter(property_name=DEAL_PROP_PIPELINE, operator="EQ", value=pipeline_id),
    ]
    deal_ids: List[str] = []
    after: Optional[str] = None
    while True:
        search_request = DealSearchRequest(
            filter_groups=[DealFilterGroup(filters=filters)],
            properties=[DEAL_PROP_NUMERO_DE_PEDIDO, DEAL_PROP_PIPELINE],
            limit=100,
            after=after,
        )
        resp = client.crm.deals.search_api.do_search(
            public_object_search_request=search_request,
        )
        deal_ids.extend(d.id for d in (resp.results or []))
        if resp.paging and resp.paging.next:
            after = resp.paging.next.after
        else:
            return deal_ids


def _verify_pedido_belongs_to_company(
    client, numero: str, company_id: str,
) -> List[str]:
    pedido_deal_ids = _search_pedidos_by_numero(client, numero, PEDIDO_PIPELINE_ID)
    if not pedido_deal_ids:
        raise PedidoNoEncontradoError(numero)

    deal_to_contenedores = _get_contenedor_ids_for_deals(client, pedido_deal_ids)
    contenedor_ids = list({
        cid for cids in deal_to_contenedores.values() for cid in cids
    })

    if not contenedor_ids:
        raise PedidoNoEncontradoError(numero)

    t = time.monotonic()
    contenedor_to_companies = batch_read_associations(
        client, OBJECT_TYPE_CONTENEDOR, OBJECT_TYPE_COMPANY, contenedor_ids,
    )
    logger.info(
        f"[TIMER] verify_pedido.batch_companies: {time.monotonic() - t:.2f}s "
        f"contenedores={len(contenedor_ids)}"
    )

    if any(company_id in (companies or []) for companies in contenedor_to_companies.values()):
        return pedido_deal_ids

    raise PedidoNoEncontradoError(numero)


def _classify_deals(
    deal_ids: List[str], deal_props_by_id: Dict[str, dict],
) -> Tuple[
    Optional[Tuple[str, dict]],
    Optional[Tuple[str, dict]],
    Optional[Tuple[str, dict]],
]:
    """Separa los deals del contenedor en (cotización, pedido, documento) por
    pipeline. El Negocio Documento (905179456) es el tercer tipo; sin esta rama
    se colaría como cotización y contaminaría sus props."""
    cotizacion: Optional[Tuple[str, dict]] = None
    pedido: Optional[Tuple[str, dict]] = None
    documento: Optional[Tuple[str, dict]] = None

    for did in deal_ids:
        props = deal_props_by_id.get(did) or {}
        numero = (props.get(DEAL_PROP_NUMERO_DE_PEDIDO) or "").strip()
        pipeline = props.get(DEAL_PROP_PIPELINE)

        if pipeline == DOCUMENTO_PIPELINE_ID:
            if documento is None:
                documento = (did, props)
        elif pipeline == PEDIDO_PIPELINE_ID and numero:
            if pedido is None:
                pedido = (did, props)
        else:
            if cotizacion is None:
                cotizacion = (did, props)

    return cotizacion, pedido, documento


def _doc_first(documento_props: dict, pedido_props: dict, key: str) -> str:
    """Lee una prop de deal con el Negocio Documento como fuente de verdad y
    fallback al Negocio Pedido (para pedidos legados sin valor en el Documento)."""
    val = (documento_props.get(key) or "").strip()
    if val:
        return val
    return (pedido_props.get(key) or "").strip()


def _read_company_props(client, company_id: str) -> dict:
    try:
        obj = client.crm.companies.basic_api.get_by_id(
            company_id=company_id,
            properties=[COMPANY_PROP_NAME, COMPANY_PROP_TIPO_CLIENTE],
        )
        return obj.properties or {}
    except Exception as e:
        logger.warning(f"  [company] no se pudieron leer props company={company_id}: {e}")
        return {}


FLUJOS_CONTENEDOR = {TIPO_FLUJO_CONTENEDOR, TIPO_FLUJO_CONTENEDOR_SAN_ROQUE}
FLUJOS_SAN_ROQUE = {TIPO_FLUJO_CONTENEDOR_SAN_ROQUE, TIPO_FLUJO_CAMION_SAN_ROQUE}


def _normalize_tipo_contenedor(raw: Optional[str]) -> str:
    # Quita todo lo no alfanumérico (espacios, guiones bajos, guiones) para que
    # "trailer_80", "TRAILER 80" y "TRAILER80" matcheen la allowlist por igual.
    return re.sub(r"[^A-Z0-9]", "", (raw or "").strip().upper())


def _es_camion(tipo_contenedor_raw: Optional[str]) -> bool:
    return _normalize_tipo_contenedor(tipo_contenedor_raw) in CAMION_TIPO_CONTENEDOR


def _compute_tipo_flujo(
    tipo_contenedor_raw: Optional[str], almacen: Optional[str],
) -> str:
    """Cruza transporte (tipo_contenedor) con origen (almacen). El tipo de
    cliente ya no interviene en la apariencia."""
    san_roque = (almacen or "").strip() == COTIZACION_ALMACEN_PROEX_SAN_ROQUE
    if _es_camion(tipo_contenedor_raw):
        return TIPO_FLUJO_CAMION_SAN_ROQUE if san_roque else TIPO_FLUJO_CAMION
    return TIPO_FLUJO_CONTENEDOR_SAN_ROQUE if san_roque else TIPO_FLUJO_CONTENEDOR


def _tipo_contenedor_representativo(
    contenedores_props: Dict[str, dict],
    contenedor_ids,
    contexto: str = "",
) -> Optional[str]:
    """tipo_contenedor crudo representativo del expediente (transporte uniforme).
    Si los contenedores divergen en camión/contenedor, logea warning y toma el
    primero — "todo camión o todo contenedor" es regla de negocio (de momento)."""
    raws = [
        ((contenedores_props.get(cid, {}) or {}).get(CONTENEDOR_PROP_TIPO_CONTENEDOR) or "").strip()
        for cid in contenedor_ids
    ]
    raws = [r for r in raws if r]
    if not raws:
        return None
    if len({_es_camion(r) for r in raws}) > 1:
        logger.warning(
            f"[transporte]{contexto} contenedores con transporte mixto "
            f"(camión y contenedor en el mismo pedido): {raws!r}; se toma el primero"
        )
    return raws[0]


def _to_float(raw) -> Optional[float]:
    if raw is None or raw == "":
        return None
    try:
        return float(str(raw).strip())
    except (ValueError, TypeError):
        return None


def _compute_vgm(peso_bruto: Optional[str], tara: Optional[str]) -> Optional[str]:
    bruto = _to_float(peso_bruto)
    t = _to_float(tara)
    if bruto is None and t is None:
        return None
    total = (bruto or 0.0) + (t or 0.0)
    if total == int(total):
        return str(int(total))
    return f"{total:.2f}"


def _parse_documentos_a_generar(raw) -> List[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        return [t.strip() for t in raw if t and t.strip()]
    return [t.strip() for t in str(raw).split(";") if t.strip()]


def _parse_bool(raw) -> bool:
    if isinstance(raw, bool):
        return raw
    return str(raw or "").strip().lower() == "true"


def _iso_from_hubspot_date(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    s = str(raw).strip()
    if not s:
        return None
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    try:
        ms = int(s)
    except ValueError:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


def _hubspot_date_from_iso(iso: Optional[str]) -> str:
    if not iso:
        return ""
    try:
        dt = datetime.strptime(iso, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return ""
    return str(int(dt.timestamp() * 1000))


def _build_contenedor_item(
    cid: str,
    props: dict,
    tipo_contenedor_labels: Dict[str, str],
    descripcion_mercancia_agregada: Optional[str] = None,
    numero_de_factura: Optional[str] = None,
    fecha_de_vencimiento_factura: Optional[str] = None,
    numero_de_booking: Optional[str] = None,
    etd: Optional[str] = None,
    eta: Optional[str] = None,
    transitario: Optional[str] = None,
    transitario_terrestre: Optional[str] = None,
    factura_pedido: Optional[DealFile] = None,
    packing_list_pedido: Optional[DealFile] = None,
    carta_porte_pedido: Optional[DealFile] = None,
    bl_validado_logistica: bool = False,
    bl_validado_administracion: bool = False,
    bl_enviado_cliente: bool = False,
    tipo_de_bl: Optional[str] = None,
    cambios_en_bl: Optional[str] = None,
    bl_archivos: Optional[List[BLArchivo]] = None,
    tiene_negocio_documento: bool = False,
    documento_dealstage: Optional[str] = None,
    meta_cache: Optional[dict] = None,
) -> ContenedorDetalleItem:
    peso_bruto = props.get("peso_bruto")
    tara = props.get("tara")
    tipo_value = (props.get(CONTENEDOR_PROP_TIPO_CONTENEDOR) or "").strip()
    tipo_label = tipo_contenedor_labels.get(tipo_value) or (tipo_value or None)
    fecha_llegada = (props.get(CONTENEDOR_PROP_FECHA_LLEGADA_CONTENEDOR) or "").strip() or None
    fecha_retirada = (props.get(CONTENEDOR_PROP_FECHA_RETIRADA_MERCANCIA) or "").strip() or None
    return ContenedorDetalleItem(
        id=cid,
        nombre=props.get("nombre"),
        numero_contenedor=props.get("numero_contenedor"),
        numero_precinto=props.get("numero_precinto"),
        peso_bruto=peso_bruto,
        peso_neto=props.get("peso_neto"),
        tara=tara,
        vgm=_compute_vgm(peso_bruto, tara),
        # ETD/ETA del pedido-deal del contenedor (fuente autoritativa que gestiona
        # Pedidos, per-contenedor), no del objeto Contenedor. Normalizadas a ISO
        # "YYYY-MM-DD" para que el DateInput de la card las precargue.
        etd=_iso_from_hubspot_date(etd),
        eta=_iso_from_hubspot_date(eta),
        tipo_contenedor=tipo_label,
        total_cajas=props.get("total_cajas"),
        transitario=(transitario or None),
        transitario_terrestre=(transitario_terrestre or None),
        descripcion_mercancia_agregada=descripcion_mercancia_agregada,
        documentos_a_generar=_parse_documentos_a_generar(props.get("documentos_a_generar")),
        importe_pendiente_cobro=props.get("importe_pendiente_cobro"),
        price=props.get("price"),
        documentos_archivos=_build_documentos_archivos(props.get(CONTENEDOR_PROP_DOCUMENTOS), meta_cache),
        otros_documentos=_build_archivos_simples(props.get(CONTENEDOR_PROP_OTROS_DOCUMENTOS), meta_cache),
        fotos_de_carga_archivos=_build_archivos_simples(props.get(CONTENEDOR_PROP_FOTOS_DE_CARGA), meta_cache),
        enviar_por_mensajeria=_parse_bool(props.get(CONTENEDOR_PROP_ENVIAR_POR_MENSAJERIA)),
        permitir_enviar_documentacion=_parse_bool(props.get(CONTENEDOR_PROP_PERMITIR_ENVIAR_DOCUMENTACION)),
        documentacion_recibida=_parse_bool(props.get(CONTENEDOR_PROP_DOCUMENTACION_RECIBIDA)),
        mercancia_retirada=_parse_bool(props.get(CONTENEDOR_PROP_MERCANCIA_RETIRADA)),
        waiver_validado=_parse_bool(props.get(CONTENEDOR_PROP_WAIVER_VALIDADO)),
        fecha_llegada_contenedor=_iso_from_hubspot_date(fecha_llegada),
        fecha_retirada_mercancia=_iso_from_hubspot_date(fecha_retirada),
        datos_envio_mensajeria=(props.get(CONTENEDOR_PROP_DATOS_ENVIO_MENSAJERIA) or None),
        albaran_mensajeria=next(
            iter(_build_archivos_simples(props.get(CONTENEDOR_PROP_ALBARAN_MENSAJERIA), meta_cache)), None
        ),
        numero_de_factura=(numero_de_factura or None),
        fecha_de_vencimiento_factura=(fecha_de_vencimiento_factura or None),
        numero_de_booking=(numero_de_booking or None),
        factura_pedido=factura_pedido,
        packing_list_pedido=packing_list_pedido,
        carta_porte_pedido=carta_porte_pedido,
        bl_validado_logistica=bl_validado_logistica,
        bl_validado_administracion=bl_validado_administracion,
        bl_enviado_cliente=bl_enviado_cliente,
        tipo_de_bl=(tipo_de_bl or None),
        cambios_en_bl=(cambios_en_bl or None),
        bl_archivos=(bl_archivos or []),
        tiene_negocio_documento=tiene_negocio_documento,
        documento_dealstage=documento_dealstage,
    )


def _classify_bl_file_by_name(name: str) -> str:
    if name.startswith(BL_FILE_PREFIX_BORRADOR):
        return "borrador"
    if name.startswith(BL_FILE_PREFIX_FINAL):
        return "final"
    return "desconocido"


def _file_metadata(file_id: str, meta_cache: Optional[dict]):
    if meta_cache is not None and file_id in meta_cache:
        return meta_cache[file_id]
    meta = fetch_file_metadata(file_id)
    if meta_cache is not None:
        meta_cache[file_id] = meta
    return meta


def _prefetch_file_metadata(file_ids: List[str], meta_cache: dict) -> None:
    pendientes = [fid for fid in dict.fromkeys(file_ids) if fid not in meta_cache]
    if not pendientes:
        return
    with ThreadPoolExecutor(max_workers=FILE_METADATA_WORKERS) as pool:
        meta_cache.update(zip(pendientes, pool.map(fetch_file_metadata, pendientes)))


def _build_bl_archivos(borrador_bl_raw: Optional[str], meta_cache: Optional[dict] = None) -> List[BLArchivo]:
    archivos: List[BLArchivo] = []
    for file_id in parse_file_ids(borrador_bl_raw):
        meta = _file_metadata(file_id, meta_cache)
        if meta is None:
            archivos.append(BLArchivo(file_id=file_id, name="", url=None, tipo="desconocido"))
            continue
        archivos.append(BLArchivo(
            file_id=meta.file_id,
            name=meta.name,
            url=meta.url,
            tipo=_classify_bl_file_by_name(meta.name),
            created_at=_iso_from_hubspot_date(meta.created_at),
        ))
    return archivos


def _classify_cert_file_by_name(name: str, family: str) -> str:
    if name.startswith(f"{family}_borrador_"):
        return "borrador"
    if name.startswith(f"{family}_validado_"):
        return "validado"
    if name.startswith(f"{family}_sellado_"):
        return "sellado"
    return "desconocido"


def _build_cert_archivos(
    raw: Optional[str], family: str, meta_cache: Optional[dict] = None,
) -> List[CertificadoArchivo]:
    archivos: List[CertificadoArchivo] = []
    for file_id in parse_file_ids(raw):
        meta = _file_metadata(file_id, meta_cache)
        if meta is None:
            archivos.append(CertificadoArchivo(file_id=file_id, name="", url=None, tipo="desconocido"))
            continue
        archivos.append(CertificadoArchivo(
            file_id=meta.file_id,
            name=meta.name,
            url=meta.url,
            tipo=_classify_cert_file_by_name(meta.name, family),
            created_at=_iso_from_hubspot_date(meta.created_at),
        ))
    return archivos


def _build_origen_archivos(
    cert_origen_borrador_raw: Optional[str],
    cert_origen_raw: Optional[str],
    meta_cache: Optional[dict] = None,
) -> List[CertificadoArchivo]:
    return [
        *_build_cert_archivos(cert_origen_borrador_raw, "origen", meta_cache),
        *_build_cert_archivos(cert_origen_raw, "origen", meta_cache),
    ]


def _build_sanitario_archivos(
    cert_sanitario_raw: Optional[str], meta_cache: Optional[dict] = None,
) -> List[CertificadoArchivo]:
    return _build_cert_archivos(cert_sanitario_raw, "sanitario", meta_cache)


def _classify_documentos_file_by_name(name: str) -> str:
    for tipo, prefix in DOC_TIPO_TO_PREFIX.items():
        if name.startswith(prefix):
            return tipo
    return "desconocido"


def _build_documentos_archivos(raw: Optional[str], meta_cache: Optional[dict] = None) -> List[OtroDocArchivo]:
    archivos: List[OtroDocArchivo] = []
    for file_id in parse_file_ids(raw):
        meta = _file_metadata(file_id, meta_cache)
        if meta is None:
            archivos.append(OtroDocArchivo(file_id=file_id, name="", url=None, tipo="desconocido"))
            continue
        archivos.append(OtroDocArchivo(
            file_id=meta.file_id,
            name=meta.name,
            url=meta.url,
            tipo=_classify_documentos_file_by_name(meta.name),
            created_at=_iso_from_hubspot_date(meta.created_at),
        ))
    return archivos


def _build_archivos_simples(raw: Optional[str], meta_cache: Optional[dict] = None) -> List[ArchivoSimple]:
    archivos: List[ArchivoSimple] = []
    for file_id in parse_file_ids(raw):
        meta = _file_metadata(file_id, meta_cache)
        if meta is None:
            archivos.append(ArchivoSimple(file_id=file_id, name="", url=None))
            continue
        archivos.append(ArchivoSimple(
            file_id=meta.file_id,
            name=meta.name,
            url=meta.url,
            created_at=_iso_from_hubspot_date(meta.created_at),
        ))
    return archivos


def _build_deal_file(raw: Optional[str], meta_cache: Optional[dict] = None) -> Optional[DealFile]:
    ids = parse_file_ids(raw)
    if not ids:
        return None
    file_id = ids[0]
    meta = _file_metadata(file_id, meta_cache)
    if meta is None:
        return DealFile(file_id=file_id, name=None, url=None)
    return DealFile(file_id=meta.file_id, name=meta.name, url=meta.url)


def _merge_cert_props(
    contenedores_props: Dict[str, dict], contenedor_ids: List[str],
) -> dict:
    """Certificados a nivel de pedido: la cabecera agrega los ficheros de TODOS los
    contenedores (dedup por file_id), no de un contenedor 'muestra' arbitrario. Así,
    un certificado subido a un subconjunto del embarque (validado/sellado) aparece
    igual aunque el contenedor muestra no lo tenga. Los flags 'validado' se OR-ean."""
    file_props = [
        CONTENEDOR_PROP_CERT_ORIGEN_BORRADOR,
        CONTENEDOR_PROP_CERT_ORIGEN,
        CONTENEDOR_PROP_CERT_SANITARIO,
    ]
    merged: dict = {}
    for prop in file_props:
        seen: List[str] = []
        for cid in contenedor_ids:
            for fid in parse_file_ids((contenedores_props.get(cid, {}) or {}).get(prop)):
                if fid not in seen:
                    seen.append(fid)
        merged[prop] = serialize_file_ids(seen)
    for prop in (
        CONTENEDOR_PROP_CERT_ORIGEN_VALIDADO,
        CONTENEDOR_PROP_CERT_SANITARIO_VALIDADO,
        CONTENEDOR_PROP_CERT_ORIGEN_ENVIAR_FIRMAR,
        CONTENEDOR_PROP_CERT_SANITARIO_ENVIAR_FIRMAR,
    ):
        merged[prop] = "true" if any(
            _parse_bool((contenedores_props.get(cid, {}) or {}).get(prop))
            for cid in contenedor_ids
        ) else "false"
    return merged


def _build_pedido_info(
    pedido_props: dict,
    cotizacion_props: dict,
    contenedor_sample_props: dict,
    meta_cache: Optional[dict] = None,
) -> PedidoInfo:
    cert_origen_borrador_raw = contenedor_sample_props.get(CONTENEDOR_PROP_CERT_ORIGEN_BORRADOR)
    cert_origen_raw          = contenedor_sample_props.get(CONTENEDOR_PROP_CERT_ORIGEN)
    cert_sanitario_raw       = contenedor_sample_props.get(CONTENEDOR_PROP_CERT_SANITARIO)

    return PedidoInfo(
        etd=pedido_props.get(DEAL_PROP_ETD),
        eta=pedido_props.get(DEAL_PROP_ETA),
        consignee=cotizacion_props.get(COTIZACION_PROP_CONSIGNEE),
        notify=cotizacion_props.get(COTIZACION_PROP_NOTIFY),
        puerto_destino=cotizacion_props.get(COTIZACION_PROP_PUERTO_DESTINO),
        puerto_salida=cotizacion_props.get(COTIZACION_PROP_PUERTO_SALIDA),
        tipo_de_venta=(cotizacion_props.get(COTIZACION_PROP_TIPO_DE_VENTA) or None),
        descripcion_mercancia=cotizacion_props.get(DEAL_PROP_DESCRIPCION_MERCANCIA),
        observaciones=pedido_props.get(DEAL_PROP_OBSERVACIONES),
        fecha_de_entrega=(pedido_props.get(DEAL_PROP_FECHA_DE_ENTREGA) or None),
        lugar_carga=(cotizacion_props.get(COTIZACION_PROP_LUGAR_CARGA) or None),
        localidad_destino=(cotizacion_props.get(COTIZACION_PROP_LOCALIDAD_DESTINO) or None),
        direccion_de_entrega=(
            pedido_props.get(DEAL_PROP_DIRECCION_DE_ENTREGA)
            or cotizacion_props.get(DEAL_PROP_DIRECCION_DE_ENTREGA)
            or None
        ),
        datos_del_chofer=(pedido_props.get(DEAL_PROP_DATOS_DEL_CHOFER) or None),
        comentarios_logistica=(cotizacion_props.get(COTIZACION_PROP_COMENTARIOS_LOGISTICA) or None),
        bl_validado_logistica=_parse_bool(pedido_props.get(DEAL_PROP_BL_VALIDADO_LOGISTICA)),
        bl_validado_administracion=_parse_bool(pedido_props.get(DEAL_PROP_BL_VALIDADO_ADMINISTRACION)),
        bl_enviado_cliente=_parse_bool(pedido_props.get(DEAL_PROP_BL_ENVIADO_CLIENTE)),
        tipo_de_bl=(pedido_props.get(DEAL_PROP_TIPO_DE_BL) or None),
        numero_de_booking=(pedido_props.get(DEAL_PROP_NUMERO_DE_BOOKING) or None),
        bl_archivos=_build_bl_archivos(pedido_props.get(DEAL_PROP_BORRADOR_BL), meta_cache),
        certificado_origen_validado=_parse_bool(contenedor_sample_props.get(CONTENEDOR_PROP_CERT_ORIGEN_VALIDADO)),
        certificado_sanitario_validado=_parse_bool(contenedor_sample_props.get(CONTENEDOR_PROP_CERT_SANITARIO_VALIDADO)),
        certificado_origen_enviar_a_firmar=_parse_bool(contenedor_sample_props.get(CONTENEDOR_PROP_CERT_ORIGEN_ENVIAR_FIRMAR)),
        certificado_sanitario_enviar_a_firmar=_parse_bool(contenedor_sample_props.get(CONTENEDOR_PROP_CERT_SANITARIO_ENVIAR_FIRMAR)),
        origen_archivos=_build_origen_archivos(cert_origen_borrador_raw, cert_origen_raw, meta_cache),
        sanitario_archivos=_build_sanitario_archivos(cert_sanitario_raw, meta_cache),
        factura_pedido=_build_deal_file(pedido_props.get(DEAL_PROP_FACTURA_DEL_PEDIDO), meta_cache),
        packing_list_pedido=_build_deal_file(pedido_props.get(DEAL_PROP_PACKING_LIST_PROEX), meta_cache),
        carta_porte_pedido=_build_deal_file(pedido_props.get(DEAL_PROP_CARTA_DE_PORTE_PROEX), meta_cache),
        fecha_de_facturacion_pedido=(pedido_props.get(DEAL_PROP_FECHA_FACTURACION_PEDIDO) or None),
        fecha_de_vencimiento_factura=(pedido_props.get(DEAL_PROP_FECHA_VENCIMIENTO_FACTURA) or None),
    )


def _detalle_file_ids(
    pedido_props: dict,
    cert_props: dict,
    contenedores_props: Dict[str, dict],
    filas: List[Tuple[str, dict, Optional[Tuple[str, dict]]]],
) -> List[str]:
    """Los ficheros que pinta el detalle. Si alguno se queda fuera no pasa nada:
    se pide en serie al construir la fila."""
    file_ids: List[str] = []
    for prop in (
        CONTENEDOR_PROP_CERT_ORIGEN_BORRADOR,
        CONTENEDOR_PROP_CERT_ORIGEN,
        CONTENEDOR_PROP_CERT_SANITARIO,
    ):
        file_ids += parse_file_ids(cert_props.get(prop))
    file_ids += parse_file_ids(pedido_props.get(DEAL_PROP_BORRADOR_BL))
    for deal_props in [pedido_props, *(pd for _, pd, _ in filas)]:
        for prop in (
            DEAL_PROP_FACTURA_DEL_PEDIDO,
            DEAL_PROP_PACKING_LIST_PROEX,
            DEAL_PROP_CARTA_DE_PORTE_PROEX,
        ):
            file_ids += parse_file_ids(deal_props.get(prop))[:1]
    for cid, pd, documento_c in filas:
        doc = documento_c[1] if documento_c else {}
        file_ids += parse_file_ids(_doc_first(doc, pd, DEAL_PROP_BORRADOR_BL))
        props = contenedores_props.get(cid) or {}
        for prop in (
            CONTENEDOR_PROP_DOCUMENTOS,
            CONTENEDOR_PROP_OTROS_DOCUMENTOS,
            CONTENEDOR_PROP_FOTOS_DE_CARGA,
            CONTENEDOR_PROP_ALBARAN_MENSAJERIA,
        ):
            file_ids += parse_file_ids(props.get(prop))
    return file_ids


def _get_pedido_detalle_sync(numero_de_pedido: str, company_id: str) -> PedidoDetalleResponse:
    client = hubspot_client.get_client()

    pedido_deal_ids = _verify_pedido_belongs_to_company(
        client, numero_de_pedido, company_id,
    )
    logger.info(
        f"[get_pedido_detalle] numero={numero_de_pedido!r} company={company_id} "
        f"pedido_deal_ids={pedido_deal_ids}"
    )

    deal_to_contenedores = _get_contenedor_ids_for_deals(client, pedido_deal_ids)
    contenedor_ids = list({
        cid for cids in deal_to_contenedores.values() for cid in cids
    })

    contenedor_to_deals = (
        _get_deal_ids_for_contenedores(client, contenedor_ids) if contenedor_ids else {}
    )

    all_deal_ids: Set[str] = set(pedido_deal_ids)
    for dids in contenedor_to_deals.values():
        all_deal_ids.update(dids)

    deal_props_by_id = _batch_read_deals_detalle(client, list(all_deal_ids))
    contenedores_props = _batch_read_contenedores_detalle(client, contenedor_ids)
    # La card pinta las filas en este orden: 001, 002…
    contenedor_ids.sort(key=lambda cid: (contenedores_props.get(cid) or {}).get("nombre") or "")

    pedido_props = deal_props_by_id.get(pedido_deal_ids[0], {}) if pedido_deal_ids else {}

    cotizacion_props: dict = {}
    for cid in contenedor_ids:
        cot, _, _ = _classify_deals(contenedor_to_deals.get(cid, []), deal_props_by_id)
        if cot is not None:
            cotizacion_props = cot[1]
            break

    company_props = _read_company_props(client, company_id)

    cotizacion_props = dict(cotizacion_props)
    cotizacion_props[COTIZACION_PROP_PUERTO_SALIDA] = resolve_enum_label(
        client, "deals", COTIZACION_PROP_PUERTO_SALIDA,
        cotizacion_props.get(COTIZACION_PROP_PUERTO_SALIDA, ""),
    )
    cotizacion_props[COTIZACION_PROP_PUERTO_DESTINO] = resolve_enum_label(
        client, "deals", COTIZACION_PROP_PUERTO_DESTINO,
        cotizacion_props.get(COTIZACION_PROP_PUERTO_DESTINO, ""),
    )
    cotizacion_props[COTIZACION_PROP_LUGAR_CARGA] = resolve_enum_label(
        client, OBJECT_TYPE_DEAL, "selector_lugar_carga",
        cotizacion_props.get(COTIZACION_PROP_LUGAR_CARGA, ""),
    )
    cotizacion_props[COTIZACION_PROP_LOCALIDAD_DESTINO] = resolve_enum_label(
        client, OBJECT_TYPE_PROVEEDOR, "lugar_de_la_carga_envio",
        cotizacion_props.get(COTIZACION_PROP_LOCALIDAD_DESTINO, ""),
    )
    cotizacion_props[COTIZACION_PROP_TIPO_DE_VENTA] = resolve_enum_label(
        client, OBJECT_TYPE_DEAL, COTIZACION_PROP_TIPO_DE_VENTA,
        cotizacion_props.get(COTIZACION_PROP_TIPO_DE_VENTA, ""),
    )

    tipo_contenedor_raw = _tipo_contenedor_representativo(
        contenedores_props, contenedor_ids, contexto=f" pedido={numero_de_pedido}",
    )
    tipo_flujo = _compute_tipo_flujo(
        tipo_contenedor_raw,
        cotizacion_props.get(COTIZACION_PROP_ALMACEN),
    )

    tipo_contenedor_values: Set[str] = {
        ((contenedores_props.get(cid, {}) or {}).get(CONTENEDOR_PROP_TIPO_CONTENEDOR) or "").strip()
        for cid in contenedor_ids
    }
    tipo_contenedor_labels: Dict[str, str] = {}
    for v in tipo_contenedor_values:
        if not v:
            continue
        tipo_contenedor_labels[v] = resolve_enum_label(
            client, OBJECT_TYPE_CONTENEDOR, CONTENEDOR_PROP_TIPO_CONTENEDOR, v,
        )

    elementos_por_contenedor = get_elementos_fabricante_por_contenedor(
        client, contenedor_ids
    )
    descripcion_por_contenedor = {
        cid: calcular_descripcion_mercancia_agregada(
            elementos_por_contenedor.get(cid, [])
        )
        for cid in contenedor_ids
    }

    # Cambio 2 — booking, factura/packing/carta viven en el PEDIDO-deal del
    # contenedor (1:1). El Negocio Documento (si existe) habilita la gestión.
    filas: List[Tuple[str, dict, Optional[Tuple[str, dict]]]] = []
    for cid in contenedor_ids:
        _, pedido_c, documento_c = _classify_deals(
            contenedor_to_deals.get(cid, []), deal_props_by_id,
        )
        filas.append((cid, pedido_c[1] if pedido_c else {}, documento_c))

    cert_props = _merge_cert_props(contenedores_props, contenedor_ids) if contenedor_ids else {}

    # Caché de metadata por request, precargada en paralelo: factura/packing/carta
    # se repiten entre los N pedido-deals y el resto son ~0,3 s por fichero en serie.
    meta_cache: Dict[str, object] = {}
    _prefetch_file_metadata(
        _detalle_file_ids(pedido_props, cert_props, contenedores_props, filas),
        meta_cache,
    )

    contenedores = []
    for cid, pd, documento_c in filas:
        doc = documento_c[1] if documento_c else {}
        documento_dealstage = (doc.get("dealstage") or None) if documento_c else None
        contenedores.append(
            _build_contenedor_item(
                cid,
                contenedores_props.get(cid, {}),
                tipo_contenedor_labels,
                descripcion_por_contenedor.get(cid),
                numero_de_factura=pd.get(DEAL_PROP_NUMERO_DE_FACTURA),
                fecha_de_vencimiento_factura=pd.get(DEAL_PROP_FECHA_VENCIMIENTO_FACTURA),
                # BL, booking y ETD/ETA: Documento manda (fallback al Pedido del contenedor).
                numero_de_booking=(_doc_first(doc, pd, DEAL_PROP_NUMERO_DE_BOOKING) or None),
                etd=(_doc_first(doc, pd, DEAL_PROP_ETD) or None),
                eta=(_doc_first(doc, pd, DEAL_PROP_ETA) or None),
                transitario=(pd.get(DEAL_PROP_TRANSITARIO_DEL_PEDIDO) or None),
                transitario_terrestre=(pd.get(DEAL_PROP_TRANSITARIO_TERRESTRE_DEL_PEDIDO) or None),
                factura_pedido=_build_deal_file(pd.get(DEAL_PROP_FACTURA_DEL_PEDIDO), meta_cache),
                packing_list_pedido=_build_deal_file(pd.get(DEAL_PROP_PACKING_LIST_PROEX), meta_cache),
                carta_porte_pedido=_build_deal_file(pd.get(DEAL_PROP_CARTA_DE_PORTE_PROEX), meta_cache),
                bl_validado_logistica=_parse_bool(_doc_first(doc, pd, DEAL_PROP_BL_VALIDADO_LOGISTICA)),
                bl_validado_administracion=_parse_bool(_doc_first(doc, pd, DEAL_PROP_BL_VALIDADO_ADMINISTRACION)),
                bl_enviado_cliente=_parse_bool(_doc_first(doc, pd, DEAL_PROP_BL_ENVIADO_CLIENTE)),
                tipo_de_bl=(_doc_first(doc, pd, DEAL_PROP_TIPO_DE_BL) or None),
                cambios_en_bl=(_doc_first(doc, pd, DEAL_PROP_CAMBIOS_EN_BL) or None),
                bl_archivos=_build_bl_archivos(_doc_first(doc, pd, DEAL_PROP_BORRADOR_BL), meta_cache),
                tiene_negocio_documento=documento_c is not None,
                documento_dealstage=documento_dealstage,
                meta_cache=meta_cache,
            )
        )

    detalle = PedidoDetalle(
        numero_de_pedido=numero_de_pedido,
        empresa=EmpresaResumen(
            id=company_id,
            name=company_props.get(COMPANY_PROP_NAME),
            tipo_cliente=(company_props.get(COMPANY_PROP_TIPO_CLIENTE) or None),
        ),
        info=_build_pedido_info(
            pedido_props,
            cotizacion_props,
            cert_props,
            meta_cache=meta_cache,
        ),
        tipo_flujo=tipo_flujo,
        es_contenedor=tipo_flujo in FLUJOS_CONTENEDOR,
        es_san_roque=tipo_flujo in FLUJOS_SAN_ROQUE,
        carga_por_palets=(
            _parse_bool(cotizacion_props.get("carga_por_palets"))
            if cotizacion_props.get("carga_por_palets") is not None
            else None
        ),
        fotos_de_carga=_parse_bool(pedido_props.get(DEAL_PROP_FOTOS_DE_CARGA)),
        contenedores=contenedores,
    )

    select_options_raw = fetch_select_options(client, DEAL_SELECT_PROPERTIES)
    select_options = {
        prop: [SelectOption(**opt) for opt in opts]
        for prop, opts in select_options_raw.items()
    }

    logger.info(
        f"[get_pedido_detalle] numero={numero_de_pedido!r} "
        f"contenedores={len(contenedores)} tipo_flujo={tipo_flujo!r} "
        f"fotos_de_carga={detalle.fotos_de_carga} "
        f"bl_archivos={len(detalle.info.bl_archivos)}"
    )
    return PedidoDetalleResponse(success=True, pedido=detalle, select_options=select_options)


async def get_pedido_detalle(
    numero_de_pedido: str, company_id: str,
) -> PedidoDetalleResponse:
    logger.info(
        f"[get_pedido_detalle] inicio numero={numero_de_pedido!r} company={company_id!r}"
    )
    try:
        return await asyncio.to_thread(
            _get_pedido_detalle_sync, numero_de_pedido, company_id,
        )
    except PedidoNoEncontradoError:
        raise
    except Exception as e:
        logger.error(
            f"[get_pedido_detalle] ERROR numero={numero_de_pedido!r}: {e}",
            exc_info=True,
        )
        return PedidoDetalleResponse(success=False, error=str(e))


def _patch_pedido_deals(client, pedido_deal_ids: List[str], properties: dict) -> int:
    updated = 0
    for did in pedido_deal_ids:
        try:
            client.crm.deals.basic_api.update(
                deal_id=did,
                simple_public_object_input=DealSimplePublicObjectInput(properties=properties),
            )
            updated += 1
        except Exception as e:
            logger.warning(f"[PATCH_DEAL] fallo deal_id={did!r}: {e}")
    return updated


def _recalcular_documentos_best_effort(client, numero_de_pedido: str) -> None:
    """Recalcula la etapa de los Negocios Documento del pedido tras mutar un
    documento. Best-effort: nunca rompe la operación de archivo si falla."""
    try:
        from app.documento_deal.service import _recalcular_dealstage_documento
        _recalcular_dealstage_documento(client, numero_de_pedido)
    except Exception as e:
        logger.warning(
            f"[recalcular_documentos] numero={numero_de_pedido!r} fallo (no bloqueante): {e}"
        )


def _update_pedido_bl_sync(
    numero_de_pedido: str, company_id: str, payload: UpdatePedidoBLRequest,
) -> UpdatePedidoResponse:
    client = hubspot_client.get_client()
    pedido_deal_ids = _verify_pedido_belongs_to_company(client, numero_de_pedido, company_id)

    properties: dict = {}
    if payload.bl_validado_logistica is not None:
        properties[DEAL_PROP_BL_VALIDADO_LOGISTICA] = "true" if payload.bl_validado_logistica else "false"
    if payload.bl_validado_administracion is not None:
        properties[DEAL_PROP_BL_VALIDADO_ADMINISTRACION] = "true" if payload.bl_validado_administracion else "false"
    if payload.bl_enviado_cliente is not None:
        properties[DEAL_PROP_BL_ENVIADO_CLIENTE] = "true" if payload.bl_enviado_cliente else "false"
    if payload.tipo_de_bl is not None:
        properties[DEAL_PROP_TIPO_DE_BL] = payload.tipo_de_bl or ""
    if payload.cambios_en_bl is not None:
        properties[DEAL_PROP_CAMBIOS_EN_BL] = payload.cambios_en_bl or ""

    if not properties:
        return UpdatePedidoResponse(success=False, error="Al menos un campo es obligatorio.")

    # BL del embarque seleccionado: se escribe en el Negocio Documento (autoritativo)
    # y en el Negocio Pedido de los contenedores objetivo. Sin selección → todos.
    # Con selección explícita NO se ensancha a todo el pedido (igual que el borrado).
    tiene_seleccion = bool(payload.contenedor_ids)
    target_cids = _resolve_target_contenedor_ids(client, pedido_deal_ids, payload.contenedor_ids)
    if tiene_seleccion and not target_cids:
        return UpdatePedidoResponse(
            success=False, error="Los contenedores seleccionados no pertenecen al pedido.",
        )
    target_pedido = _resolve_target_pedido_deal_ids(
        client, pedido_deal_ids, target_cids, allow_fallback=not tiene_seleccion,
    )
    if tiene_seleccion and not target_pedido:
        return UpdatePedidoResponse(
            success=False, error="Los contenedores seleccionados no tienen pedido-deal asociado.",
        )
    target_documento = _resolve_target_documento_deal_ids(client, target_cids)

    logger.info(
        f"[update_pedido_bl] numero={numero_de_pedido!r} props={list(properties.keys())} "
        f"pedido_deals={target_pedido} documento_deals={target_documento}"
    )
    updated = _patch_pedido_deals(client, target_pedido, properties)
    updated += _patch_pedido_deals(client, target_documento, properties)
    if updated == 0:
        return UpdatePedidoResponse(success=False, error="No se pudo actualizar ningún deal.")
    _recalcular_documentos_best_effort(client, numero_de_pedido)
    return UpdatePedidoResponse(success=True)


async def update_pedido_bl(
    numero_de_pedido: str, company_id: str, payload: UpdatePedidoBLRequest,
) -> UpdatePedidoResponse:
    try:
        return await asyncio.to_thread(
            _update_pedido_bl_sync, numero_de_pedido, company_id, payload,
        )
    except PedidoNoEncontradoError:
        raise
    except Exception as e:
        logger.error(
            f"[update_pedido_bl] ERROR numero={numero_de_pedido!r}: {e}", exc_info=True,
        )
        return UpdatePedidoResponse(success=False, error=str(e))


def _update_contenedores_certificados_sync(
    numero_de_pedido: str, company_id: str,
    payload: UpdateContenedoresCertificadosRequest,
) -> UpdatePedidoResponse:
    client = hubspot_client.get_client()
    pedido_deal_ids = _verify_pedido_belongs_to_company(client, numero_de_pedido, company_id)

    properties: dict = {}
    if payload.certificado_origen_validado is not None:
        properties[CONTENEDOR_PROP_CERT_ORIGEN_VALIDADO] = (
            "true" if payload.certificado_origen_validado else "false"
        )
    if payload.certificado_sanitario_validado is not None:
        properties[CONTENEDOR_PROP_CERT_SANITARIO_VALIDADO] = (
            "true" if payload.certificado_sanitario_validado else "false"
        )
    if payload.certificado_origen_enviar_a_firmar is not None:
        properties[CONTENEDOR_PROP_CERT_ORIGEN_ENVIAR_FIRMAR] = (
            "true" if payload.certificado_origen_enviar_a_firmar else "false"
        )
    if payload.certificado_sanitario_enviar_a_firmar is not None:
        properties[CONTENEDOR_PROP_CERT_SANITARIO_ENVIAR_FIRMAR] = (
            "true" if payload.certificado_sanitario_enviar_a_firmar else "false"
        )

    if not properties:
        return UpdatePedidoResponse(success=False, error="Al menos un campo es obligatorio.")

    contenedor_ids = _get_contenedores_of_pedido(client, pedido_deal_ids)
    if not contenedor_ids:
        return UpdatePedidoResponse(
            success=False, error="El pedido no tiene contenedores asociados.",
        )

    logger.info(
        f"[update_contenedores_certificados] numero={numero_de_pedido!r} "
        f"contenedores={len(contenedor_ids)} props={list(properties.keys())}"
    )
    updated = _patch_contenedores_batch(client, contenedor_ids, properties)
    if updated == 0:
        return UpdatePedidoResponse(success=False, error="No se pudo actualizar ningún contenedor.")
    _recalcular_documentos_best_effort(client, numero_de_pedido)
    return UpdatePedidoResponse(success=True)


async def update_contenedores_certificados(
    numero_de_pedido: str, company_id: str,
    payload: UpdateContenedoresCertificadosRequest,
) -> UpdatePedidoResponse:
    try:
        return await asyncio.to_thread(
            _update_contenedores_certificados_sync,
            numero_de_pedido, company_id, payload,
        )
    except PedidoNoEncontradoError:
        raise
    except Exception as e:
        logger.error(
            f"[update_contenedores_certificados] ERROR numero={numero_de_pedido!r}: {e}",
            exc_info=True,
        )
        return UpdatePedidoResponse(success=False, error=str(e))


def _update_contenedor_entrega_sync(
    numero_de_pedido: str, company_id: str, contenedor_id: str,
    payload: UpdateContenedorEntregaRequest,
) -> UpdatePedidoResponse:
    client = hubspot_client.get_client()
    pedido_deal_ids = _verify_pedido_belongs_to_company(client, numero_de_pedido, company_id)

    contenedor_ids = _get_contenedores_of_pedido(client, pedido_deal_ids)
    if contenedor_id not in contenedor_ids:
        return UpdatePedidoResponse(
            success=False, error="El contenedor no pertenece al pedido indicado.",
        )

    properties: dict = {}
    bool_fields = (
        (payload.enviar_por_mensajeria, CONTENEDOR_PROP_ENVIAR_POR_MENSAJERIA),
        (payload.permitir_enviar_documentacion, CONTENEDOR_PROP_PERMITIR_ENVIAR_DOCUMENTACION),
        (payload.documentacion_recibida, CONTENEDOR_PROP_DOCUMENTACION_RECIBIDA),
        (payload.mercancia_retirada, CONTENEDOR_PROP_MERCANCIA_RETIRADA),
        (payload.waiver_validado, CONTENEDOR_PROP_WAIVER_VALIDADO),
    )
    for value, prop in bool_fields:
        if value is not None:
            properties[prop] = "true" if value else "false"

    if "datos_envio_mensajeria" in payload.model_fields_set:
        properties[CONTENEDOR_PROP_DATOS_ENVIO_MENSAJERIA] = payload.datos_envio_mensajeria or ""

    if "fecha_llegada_contenedor" in payload.model_fields_set:
        properties[CONTENEDOR_PROP_FECHA_LLEGADA_CONTENEDOR] = _hubspot_date_from_iso(
            payload.fecha_llegada_contenedor
        )
    if "fecha_retirada_mercancia" in payload.model_fields_set:
        properties[CONTENEDOR_PROP_FECHA_RETIRADA_MERCANCIA] = _hubspot_date_from_iso(
            payload.fecha_retirada_mercancia
        )

    if not properties:
        return UpdatePedidoResponse(success=False, error="Al menos un campo es obligatorio.")

    logger.info(
        f"[update_contenedor_entrega] numero={numero_de_pedido!r} "
        f"contenedor={contenedor_id} props={list(properties.keys())}"
    )
    updated = _patch_contenedores_batch(client, [contenedor_id], properties)
    if updated == 0:
        return UpdatePedidoResponse(success=False, error="No se pudo actualizar el contenedor.")
    _recalcular_documentos_best_effort(client, numero_de_pedido)
    return UpdatePedidoResponse(success=True)


async def update_contenedor_entrega(
    numero_de_pedido: str, company_id: str, contenedor_id: str,
    payload: UpdateContenedorEntregaRequest,
) -> UpdatePedidoResponse:
    try:
        return await asyncio.to_thread(
            _update_contenedor_entrega_sync,
            numero_de_pedido, company_id, contenedor_id, payload,
        )
    except PedidoNoEncontradoError:
        raise
    except Exception as e:
        logger.error(
            f"[update_contenedor_entrega] ERROR numero={numero_de_pedido!r} "
            f"contenedor={contenedor_id}: {e}",
            exc_info=True,
        )
        return UpdatePedidoResponse(success=False, error=str(e))


# Datos físicos del contenedor editables desde Documentos. Viven en el propio
# Contenedor (los PDFs los leen de ahí), así que basta con un PATCH al contenedor.
_CONTENEDOR_DATOS_FIELDS = (
    "numero_contenedor",
    "numero_precinto",
    "peso_bruto",
    "peso_neto",
    "tara",
)


def _update_contenedor_datos_sync(
    numero_de_pedido: str, company_id: str, contenedor_id: str,
    payload: UpdateContenedorDatosRequest,
) -> UpdatePedidoResponse:
    client = hubspot_client.get_client()
    pedido_deal_ids = _verify_pedido_belongs_to_company(client, numero_de_pedido, company_id)

    contenedor_ids = _get_contenedores_of_pedido(client, pedido_deal_ids)
    if contenedor_id not in contenedor_ids:
        return UpdatePedidoResponse(
            success=False, error="El contenedor no pertenece al pedido indicado.",
        )

    properties: dict = {}
    for field in _CONTENEDOR_DATOS_FIELDS:
        if field in payload.model_fields_set:
            value = getattr(payload, field)
            properties[field] = value if value is not None else ""

    if not properties:
        return UpdatePedidoResponse(success=False, error="Al menos un campo es obligatorio.")

    logger.info(
        f"[update_contenedor_datos] numero={numero_de_pedido!r} "
        f"contenedor={contenedor_id} props={list(properties.keys())}"
    )
    updated = _patch_contenedores_batch(client, [contenedor_id], properties)
    if updated == 0:
        return UpdatePedidoResponse(success=False, error="No se pudo actualizar el contenedor.")
    return UpdatePedidoResponse(success=True)


async def update_contenedor_datos(
    numero_de_pedido: str, company_id: str, contenedor_id: str,
    payload: UpdateContenedorDatosRequest,
) -> UpdatePedidoResponse:
    try:
        return await asyncio.to_thread(
            _update_contenedor_datos_sync,
            numero_de_pedido, company_id, contenedor_id, payload,
        )
    except PedidoNoEncontradoError:
        raise
    except Exception as e:
        logger.error(
            f"[update_contenedor_datos] ERROR numero={numero_de_pedido!r} "
            f"contenedor={contenedor_id}: {e}",
            exc_info=True,
        )
        return UpdatePedidoResponse(success=False, error=str(e))


def _update_contenedor_booking_sync(
    numero_de_pedido: str, company_id: str, contenedor_id: str,
    payload: UpdateContenedorBookingRequest,
) -> UpdatePedidoResponse:
    # Cambio 2 — booking INDIVIDUAL: se escribe solo en el pedido-deal (1:1) de
    # este contenedor; un pedido puede tener bookings distintos por embarque.
    if payload.numero_de_booking is None:
        return UpdatePedidoResponse(success=False, error="numero_de_booking es obligatorio.")

    client = hubspot_client.get_client()
    pedido_deal_ids = _verify_pedido_belongs_to_company(client, numero_de_pedido, company_id)

    if contenedor_id not in _get_contenedores_of_pedido(client, pedido_deal_ids):
        return UpdatePedidoResponse(
            success=False, error="El contenedor no pertenece al pedido indicado.",
        )

    container_deals = _get_deal_ids_for_contenedores(client, [contenedor_id]).get(contenedor_id, [])
    pedido_set = set(pedido_deal_ids)
    target = [d for d in container_deals if d in pedido_set]
    if not target:
        return UpdatePedidoResponse(
            success=False, error="El contenedor no tiene pedido-deal asociado.",
        )
    if len(target) > 1:
        # Invariante Cambio 2: 1 pedido-deal por Contenedor. Si hay >1, la lectura
        # solo refleja el primero; se escriben todos con el mismo valor (consistentes).
        logger.warning(
            f"[update_contenedor_booking] contenedor={contenedor_id} con {len(target)} "
            f"pedido-deals (esperado 1): {target}"
        )

    # Documento manda: el booking se escribe también en el Negocio Documento del
    # contenedor, además de su Pedido-deal.
    target_documento = _resolve_target_documento_deal_ids(client, [contenedor_id])
    booking_props = {DEAL_PROP_NUMERO_DE_BOOKING: payload.numero_de_booking or ""}

    logger.info(
        f"[update_contenedor_booking] numero={numero_de_pedido!r} "
        f"contenedor={contenedor_id} pedido_deal(s)={target} documento_deal(s)={target_documento}"
    )
    updated = _patch_pedido_deals(client, target, booking_props)
    updated += _patch_pedido_deals(client, target_documento, booking_props)
    if updated == 0:
        return UpdatePedidoResponse(success=False, error="No se pudo actualizar el booking.")
    return UpdatePedidoResponse(success=True)


async def update_contenedor_booking(
    numero_de_pedido: str, company_id: str, contenedor_id: str,
    payload: UpdateContenedorBookingRequest,
) -> UpdatePedidoResponse:
    try:
        return await asyncio.to_thread(
            _update_contenedor_booking_sync,
            numero_de_pedido, company_id, contenedor_id, payload,
        )
    except PedidoNoEncontradoError:
        raise
    except Exception as e:
        logger.error(
            f"[update_contenedor_booking] ERROR numero={numero_de_pedido!r} "
            f"contenedor={contenedor_id}: {e}",
            exc_info=True,
        )
        return UpdatePedidoResponse(success=False, error=str(e))


def _update_contenedor_fechas_sync(
    numero_de_pedido: str, company_id: str, contenedor_id: str,
    payload: UpdateContenedorFechasRequest,
) -> UpdatePedidoResponse:
    # ETD/ETA por contenedor: la lectura usa el Documento (fallback Pedido), así que
    # se escriben en AMBOS deals del contenedor para mantener la consistencia.
    client = hubspot_client.get_client()
    pedido_deal_ids = _verify_pedido_belongs_to_company(client, numero_de_pedido, company_id)

    if contenedor_id not in _get_contenedores_of_pedido(client, pedido_deal_ids):
        return UpdatePedidoResponse(
            success=False, error="El contenedor no pertenece al pedido indicado.",
        )

    props: dict = {}
    if "etd" in payload.model_fields_set:
        props[DEAL_PROP_ETD] = _hubspot_date_from_iso(payload.etd)
    if "eta" in payload.model_fields_set:
        props[DEAL_PROP_ETA] = _hubspot_date_from_iso(payload.eta)
    if not props:
        return UpdatePedidoResponse(success=True)

    container_deals = _get_deal_ids_for_contenedores(client, [contenedor_id]).get(contenedor_id, [])
    pedido_set = set(pedido_deal_ids)
    target = [d for d in container_deals if d in pedido_set]
    if not target:
        return UpdatePedidoResponse(
            success=False, error="El contenedor no tiene pedido-deal asociado.",
        )

    target_documento = _resolve_target_documento_deal_ids(client, [contenedor_id])

    logger.info(
        f"[update_contenedor_fechas] numero={numero_de_pedido!r} "
        f"contenedor={contenedor_id} props={list(props.keys())} "
        f"pedido_deal(s)={target} documento_deal(s)={target_documento}"
    )
    updated = _patch_pedido_deals(client, target, props)
    updated += _patch_pedido_deals(client, target_documento, props)
    if updated == 0:
        return UpdatePedidoResponse(success=False, error="No se pudieron actualizar las fechas.")
    return UpdatePedidoResponse(success=True)


async def update_contenedor_fechas(
    numero_de_pedido: str, company_id: str, contenedor_id: str,
    payload: UpdateContenedorFechasRequest,
) -> UpdatePedidoResponse:
    try:
        return await asyncio.to_thread(
            _update_contenedor_fechas_sync,
            numero_de_pedido, company_id, contenedor_id, payload,
        )
    except PedidoNoEncontradoError:
        raise
    except Exception as e:
        logger.error(
            f"[update_contenedor_fechas] ERROR numero={numero_de_pedido!r} "
            f"contenedor={contenedor_id}: {e}",
            exc_info=True,
        )
        return UpdatePedidoResponse(success=False, error=str(e))


def _extract_extension(original_filename: Optional[str], mime_type: Optional[str]) -> str:
    if original_filename and "." in original_filename:
        ext = original_filename.rsplit(".", 1)[-1].strip().lower()
        if ext:
            return ext
    mapping = {
        "application/pdf": "pdf",
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/heic": "heic",
        "image/heif": "heif",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
        "application/vnd.ms-excel": "xls",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "application/msword": "doc",
    }
    return mapping.get((mime_type or "").lower(), "bin")


def _build_filename(
    numero_de_pedido: str,
    tipo_documento: str,
    original_filename: Optional[str] = None,
    mime_type: Optional[str] = None,
) -> str:
    from uuid import uuid4
    config = FILE_TYPE_CONFIG[tipo_documento]
    prefix = config["filename_prefix"]
    safe_numero = numero_de_pedido.replace("/", "-").replace(" ", "_")
    short = uuid4().hex[:6]
    extension = _extract_extension(original_filename, mime_type)
    return f"{prefix}{safe_numero}_{short}.{extension}"


def _build_filename_preserve_original(
    original_filename: Optional[str],
    mime_type: Optional[str],
) -> str:
    from uuid import uuid4
    short = uuid4().hex[:6]
    safe = (original_filename or "").replace("/", "-").replace("\\", "-").strip()
    if not safe:
        ext = _extract_extension(None, mime_type)
        return f"documento_{short}.{ext}"
    if "." in safe:
        base, ext = safe.rsplit(".", 1)
        return f"{base}_{short}.{ext}"
    ext = _extract_extension(None, mime_type)
    return f"{safe}_{short}.{ext}"


def _get_contenedores_of_pedido(client, pedido_deal_ids: List[str]) -> List[str]:
    deal_to_contenedores = _get_contenedor_ids_for_deals(client, pedido_deal_ids)
    return list({cid for cids in deal_to_contenedores.values() for cid in cids})


def _patch_contenedores_batch(client, container_ids: List[str], properties: dict) -> int:
    updated = 0
    chunk_size = 100
    for i in range(0, len(container_ids), chunk_size):
        chunk = container_ids[i : i + chunk_size]
        batch_input = BatchInputSimplePublicObjectBatchInput(
            inputs=[
                SimplePublicObjectBatchInput(id=cid, properties=properties)
                for cid in chunk
            ]
        )
        try:
            resp = client.crm.objects.batch_api.update(
                object_type=OBJECT_TYPE_CONTENEDOR,
                batch_input_simple_public_object_batch_input=batch_input,
            )
            updated += len(resp.results or [])
        except Exception as e:
            logger.error(
                f"[PATCH_CONTENEDORES] ERROR chunk {i // chunk_size + 1}: {e}",
                exc_info=True,
            )
    return updated


def _read_contenedor_prop_value(client, container_id: str, prop: str) -> str:
    try:
        obj = client.crm.objects.basic_api.get_by_id(
            object_type=OBJECT_TYPE_CONTENEDOR,
            object_id=container_id,
            properties=[prop],
        )
        return (obj.properties or {}).get(prop) or ""
    except Exception as e:
        logger.warning(f"[READ_CONTENEDOR_PROP] fallo cid={container_id!r} prop={prop!r}: {e}")
        return ""


def _read_deal_prop_value(client, deal_id: str, prop: str) -> str:
    try:
        deal = client.crm.deals.basic_api.get_by_id(deal_id=deal_id, properties=[prop])
        return (deal.properties or {}).get(prop) or ""
    except Exception as e:
        logger.warning(f"[READ_DEAL_PROP] fallo deal_id={deal_id!r} prop={prop!r}: {e}")
        return ""


def _resolve_target_contenedor_ids(
    client, pedido_deal_ids: List[str], contenedor_ids: Optional[List[str]],
) -> List[str]:
    """Cambio 2 — docs por EMBARQUE: el destino es el SUBCONJUNTO de contenedores
    seleccionado. Sin selección → todos los del pedido (subir una vez y replicar
    a todos). La selección se INTERSECA siempre con los contenedores reales del
    pedido (no se confía en el cliente: evita leer/escribir props de contenedores
    ajenos al pedido verificado)."""
    todos = _get_contenedores_of_pedido(client, pedido_deal_ids)
    if contenedor_ids:
        permitidos = set(todos)
        return [c for c in dict.fromkeys([c for c in contenedor_ids if c]) if c in permitidos]
    return todos


def _resolve_target_pedido_deal_ids(
    client, pedido_deal_ids: List[str], target_cids: List[str],
    allow_fallback: bool = True,
) -> List[str]:
    """Pedido-deals (1:1) de los contenedores objetivo, para los docs de scope
    'deal' (p. ej. BL): replicar el file_id solo a los deals del subconjunto.
    `allow_fallback`: en SUBIDA, si no se resuelve ninguno se cae a todos (no
    romper). En BORRADO con selección explícita se pasa False para NO ensanchar
    un borrado acotado a todo el pedido (devuelve [] y el caller lo trata como error)."""
    if not target_cids:
        return pedido_deal_ids
    cid_to_deals = _get_deal_ids_for_contenedores(client, target_cids)
    pedido_set = set(pedido_deal_ids)
    out: List[str] = []
    for cid in target_cids:
        for did in cid_to_deals.get(cid, []):
            if did in pedido_set and did not in out:
                out.append(did)
    if out:
        return out
    return pedido_deal_ids if allow_fallback else []


def _resolve_target_documento_deal_ids(client, target_cids: List[str]) -> List[str]:
    """Negocio Documento (pipeline DOCUMENTO_PIPELINE_ID) de los contenedores
    objetivo. El BL y el booking se escriben aquí además del Pedido-deal: el
    Documento es la fuente de verdad. Invariante 1 Documento : 1 Contenedor; si
    hubiera >1 se escriben todos con el mismo valor."""
    if not target_cids:
        return []
    cid_to_deals = _get_deal_ids_for_contenedores(client, target_cids)
    all_dids = list(dict.fromkeys(
        did for cid in target_cids for did in cid_to_deals.get(cid, [])
    ))
    if not all_dids:
        return []
    props_by_id = _batch_read_deals_min(client, all_dids)
    return [
        did for did in all_dids
        if (props_by_id.get(did) or {}).get(DEAL_PROP_PIPELINE) == DOCUMENTO_PIPELINE_ID
    ]


def _upload_pedido_file_sync(
    numero_de_pedido: str,
    company_id: str,
    file_bytes: bytes,
    tipo_documento: str,
    original_filename: Optional[str],
    mime_type: Optional[str],
    contenedor_ids: Optional[List[str]],
) -> UploadFileResponse:
    config = FILE_TYPE_CONFIG.get(tipo_documento)
    if config is None:
        return UploadFileResponse(
            success=False,
            error=f"tipo_documento desconocido: {tipo_documento!r}",
        )

    scope             = config.get("scope", "deal")
    prop              = config["prop"]
    prefix            = config["filename_prefix"]
    folder            = config["folder"]
    replace_by_prefix = config.get("replace_by_prefix", True)
    max_files         = config.get("max_files")

    client = hubspot_client.get_client()
    pedido_deal_ids = _verify_pedido_belongs_to_company(client, numero_de_pedido, company_id)

    # Cambio 2 — destino = subconjunto de contenedores seleccionado (embarque).
    target_cids = _resolve_target_contenedor_ids(client, pedido_deal_ids, contenedor_ids)
    if not target_cids:
        return UploadFileResponse(
            success=False, error="El pedido no tiene contenedores asociados.",
        )
    if scope == "deal":
        # BL y otros de scope 'deal': replicar a los pedido-deals del subconjunto.
        # Con selección explícita no se ensancha a todo el pedido (igual que el borrado).
        target_deal_ids = _resolve_target_pedido_deal_ids(
            client, pedido_deal_ids, target_cids, allow_fallback=not contenedor_ids,
        )
        if not target_deal_ids:
            return UploadFileResponse(
                success=False,
                error="Los contenedores seleccionados no tienen pedido-deal asociado.",
            )
        current_raw = _read_deal_prop_value(client, target_deal_ids[0], prop)
    else:
        current_raw = _read_contenedor_prop_value(client, target_cids[0], prop)

    current_ids = parse_file_ids(current_raw)
    kept_ids: List[str] = []
    if replace_by_prefix:
        for fid in current_ids:
            meta = fetch_file_metadata(fid)
            if meta and meta.name.startswith(prefix):
                try:
                    delete_file(fid)
                except Exception as e:
                    logger.warning(f"[upload_pedido_file] delete_file falló para {fid!r}: {e}")
            else:
                kept_ids.append(fid)
    else:
        kept_ids = list(current_ids)
        if max_files is not None and len(kept_ids) >= max_files:
            return UploadFileResponse(
                success=False,
                error=f"Has alcanzado el máximo de {max_files} archivos.",
                error_code="limite_archivos_excedido",
            )

    if config.get("preserve_original_filename"):
        new_filename = _build_filename_preserve_original(original_filename, mime_type)
    else:
        new_filename = _build_filename(
            numero_de_pedido, tipo_documento, original_filename, mime_type,
        )
    upload_result = upload_file(
        file_bytes, new_filename, mime_type or "application/octet-stream", folder_path=folder,
    )
    logger.info(
        f"[upload_pedido_file] scope={scope!r} tipo={tipo_documento!r} prop={prop!r} "
        f"file_id={upload_result.file_id!r} name={new_filename!r}"
    )

    kept_ids.append(upload_result.file_id)
    new_value = serialize_file_ids(kept_ids)

    if scope == "deal":
        # Documento manda: el fichero (BL) se replica al Negocio Documento además
        # del Negocio Pedido de los contenedores objetivo.
        _patch_pedido_deals(client, target_deal_ids, {prop: new_value})
        _patch_pedido_deals(
            client, _resolve_target_documento_deal_ids(client, target_cids), {prop: new_value},
        )
    else:
        _patch_contenedores_batch(client, target_cids, {prop: new_value})

    _recalcular_documentos_best_effort(client, numero_de_pedido)

    return UploadFileResponse(
        success=True,
        file_id=upload_result.file_id,
        file_name=new_filename,
        file_url=upload_result.file_url,
        tipo_documento=tipo_documento,
    )


async def upload_pedido_file(
    numero_de_pedido: str,
    company_id: str,
    file_bytes: bytes,
    tipo_documento: str,
    original_filename: Optional[str] = None,
    mime_type: Optional[str] = None,
    contenedor_ids: Optional[List[str]] = None,
) -> UploadFileResponse:
    try:
        return await asyncio.to_thread(
            _upload_pedido_file_sync,
            numero_de_pedido,
            company_id,
            file_bytes,
            tipo_documento,
            original_filename,
            mime_type,
            contenedor_ids,
        )
    except PedidoNoEncontradoError:
        raise
    except Exception as e:
        logger.error(
            f"[upload_pedido_file] ERROR numero={numero_de_pedido!r}: {e}", exc_info=True,
        )
        return UploadFileResponse(success=False, error=str(e))


def _delete_pedido_file_sync(
    numero_de_pedido: str,
    company_id: str,
    file_id: str,
    tipo_documento: str,
    contenedor_ids: Optional[List[str]],
) -> DeleteFileResponse:
    config = FILE_TYPE_CONFIG.get(tipo_documento)
    if config is None:
        return DeleteFileResponse(
            success=False,
            error=f"tipo_documento desconocido: {tipo_documento!r}",
        )
    scope = config.get("scope", "deal")
    prop  = config["prop"]

    client = hubspot_client.get_client()
    pedido_deal_ids = _verify_pedido_belongs_to_company(client, numero_de_pedido, company_id)

    # Cambio 2 — el borrado es simétrico a la subida: si un doc se replicó a un
    # subconjunto (embarque), se quita de TODOS ellos. Se recalcula POR objeto
    # porque las props pueden divergir (subidas a subconjuntos distintos).
    if scope == "deal":
        if contenedor_ids:
            tcids = _resolve_target_contenedor_ids(client, pedido_deal_ids, contenedor_ids)
            if not tcids:
                return DeleteFileResponse(
                    success=False,
                    error="Los contenedores seleccionados no pertenecen al pedido.",
                )
            target_deal_ids = _resolve_target_pedido_deal_ids(
                client, pedido_deal_ids, tcids, allow_fallback=False,
            )
            if not target_deal_ids:
                return DeleteFileResponse(
                    success=False,
                    error="Los contenedores seleccionados no tienen pedido-deal asociado.",
                )
        else:
            tcids = _get_contenedores_of_pedido(client, pedido_deal_ids)
            target_deal_ids = pedido_deal_ids
        # Documento manda: el fichero también se quita del Negocio Documento.
        target_documento = _resolve_target_documento_deal_ids(client, tcids)
        removed = False
        for did in [*target_deal_ids, *target_documento]:
            current_ids = parse_file_ids(_read_deal_prop_value(client, did, prop))
            if file_id not in current_ids:
                continue
            new_value = serialize_file_ids([fid for fid in current_ids if fid != file_id])
            _patch_pedido_deals(client, [did], {prop: new_value})
            removed = True
        if not removed:
            return DeleteFileResponse(success=False, error="file_id no presente en la propiedad")
    else:
        target_cids = _resolve_target_contenedor_ids(client, pedido_deal_ids, contenedor_ids)
        if not target_cids:
            return DeleteFileResponse(
                success=False, error="El pedido no tiene contenedores asociados.",
            )
        # Se quita el file_id de cada contenedor del subconjunto que lo tenga
        # (sus props pueden divergir, así que se recalcula por contenedor).
        removed = False
        for cid in target_cids:
            current_ids = parse_file_ids(_read_contenedor_prop_value(client, cid, prop))
            if file_id not in current_ids:
                continue
            new_value = serialize_file_ids([fid for fid in current_ids if fid != file_id])
            _patch_contenedores_batch(client, [cid], {prop: new_value})
            removed = True
        if not removed:
            return DeleteFileResponse(
                success=False,
                error="file_id no presente en los contenedores seleccionados",
            )

    try:
        delete_file(file_id)
    except Exception as e:
        logger.warning(f"[delete_pedido_file] delete_file falló para {file_id!r}: {e}")

    _recalcular_documentos_best_effort(client, numero_de_pedido)

    return DeleteFileResponse(success=True)


async def delete_pedido_file(
    numero_de_pedido: str,
    company_id: str,
    file_id: str,
    tipo_documento: str,
    contenedor_ids: Optional[List[str]] = None,
) -> DeleteFileResponse:
    try:
        return await asyncio.to_thread(
            _delete_pedido_file_sync,
            numero_de_pedido,
            company_id,
            file_id,
            tipo_documento,
            contenedor_ids,
        )
    except PedidoNoEncontradoError:
        raise
    except Exception as e:
        logger.error(
            f"[delete_pedido_file] ERROR numero={numero_de_pedido!r}: {e}", exc_info=True,
        )
        return DeleteFileResponse(success=False, error=str(e))


def _render_invalid_tipo_html(tipo_documento: str) -> str:
    safe = (tipo_documento or "").replace("<", "&lt;").replace(">", "&gt;")
    return (
        "<!doctype html><html lang=\"es\"><head><meta charset=\"utf-8\">"
        "<title>Tipo no soportado</title></head>"
        f"<body style=\"font-family:sans-serif;padding:24px;color:#d94a4a\">"
        f"<h1>Tipo de documento no soportado</h1>"
        f"<p><code>{safe}</code></p></body></html>"
    )


def _mime_to_accept(mime_types: tuple) -> str:
    ext_map = {
        "application/pdf": ".pdf",
        "image/jpeg": ".jpg,.jpeg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/heic": ".heic",
        "image/heif": ".heif",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
        "application/vnd.ms-excel": ".xls",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "application/msword": ".doc",
    }
    parts: list = []
    for m in mime_types:
        parts.append(m)
        if m in ext_map:
            parts.append(ext_map[m])
    seen = set()
    out = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return ",".join(out)


def _mime_user_friendly(mime_types: tuple) -> str:
    friendly = {
        "application/pdf": "PDF",
        "image/jpeg": "JPG",
        "image/png": "PNG",
        "image/webp": "WebP",
        "image/heic": "HEIC",
        "image/heif": "HEIF",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "XLSX",
        "application/vnd.ms-excel": "XLS",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "DOCX",
        "application/msword": "DOC",
    }
    seen = set()
    out = []
    for m in mime_types:
        label = friendly.get(m, m)
        if label not in seen:
            seen.add(label)
            out.append(label)
    return ", ".join(out)


def render_upload_iframe_html(
    numero_de_pedido: str,
    company_id: str,
    tipo_documento: str,
    contenedor_id: Optional[str] = None,
    n_destinos: int = 0,
) -> str:
    import json as _json

    config = FILE_TYPE_CONFIG.get(tipo_documento)
    if config is None:
        return _render_invalid_tipo_html(tipo_documento)

    destinos_hint = (
        f" Se aplicará a {n_destinos} contenedores seleccionados." if n_destinos > 1 else ""
    )

    label = config["label"]
    allowed_mimes: tuple = config.get("allowed_mime_types") or ("application/pdf",)
    max_files: int = int(config.get("max_files") or 1)
    accept_attr = _mime_to_accept(allowed_mimes)
    mimes_json = _json.dumps(list(allowed_mimes))
    friendly = _mime_user_friendly(allowed_mimes)
    multiple_attr = "multiple" if max_files > 1 else ""
    limit_hint = f"Máximo {max_files} archivos." if max_files > 1 else ""

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8" />
<title>Subir {label}</title>
<style>
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    padding: 20px; color: #33475b;
    background: #fff;
  }}
  h1 {{ font-size: 16px; font-weight: 600; margin: 0 0 4px; }}
  p.lead {{ font-size: 13px; margin: 0 0 16px; color: #506e91; }}

  .visually-hidden {{
    position: absolute !important;
    width: 1px; height: 1px;
    padding: 0; margin: -1px;
    overflow: hidden; clip: rect(0, 0, 0, 0);
    white-space: nowrap; border: 0;
  }}

  .drop {{
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    border: 2px dashed #cbd6e2; border-radius: 8px;
    padding: 36px 16px; text-align: center; cursor: pointer;
    transition: border-color .15s, background .15s;
    user-select: none;
  }}
  .drop:hover, .drop.dragover {{ border-color: #ff7a59; background: #fff7f3; }}
  .drop p {{ margin: 0; font-size: 14px; }}
  .drop p.hint {{ font-size: 12px; color: #7c98b6; margin-top: 6px; }}

  ul.files {{ margin: 16px 0 0; padding: 0; list-style: none; font-size: 13px; }}
  ul.files li {{
    display: flex; align-items: center; gap: 8px; padding: 6px 0;
    border-bottom: 1px solid #eaf0f6;
  }}
  ul.files li.ok {{ color: #00a4bd; }}
  ul.files li.err {{ color: #d94a4a; }}
  ul.files li .name {{
    flex: 1; min-width: 0; overflow: hidden;
    text-overflow: ellipsis; white-space: nowrap;
  }}
  ul.files li .size {{ color: #7c98b6; font-size: 12px; }}
  ul.files li .remove {{ color: #d94a4a; cursor: pointer; padding: 0 8px; font-weight: 700; }}

  .actions {{ margin-top: 16px; display: flex; gap: 8px; }}
  button {{
    border: 0; border-radius: 4px; padding: 8px 16px; font-size: 13px;
    cursor: pointer; font-weight: 600;
  }}
  button.primary {{ background: #ff7a59; color: white; }}
  button.primary:disabled {{ background: #cbd6e2; cursor: not-allowed; }}

  .status {{ margin-top: 16px; font-size: 13px; min-height: 20px; }}
  .status.ok {{ color: #00a4bd; }}
  .status.err {{ color: #d94a4a; }}

  .progress {{
    width: 100%; height: 4px; background: #eaf0f6; border-radius: 2px;
    overflow: hidden; margin-top: 12px; display: none;
  }}
  .progress .bar {{ height: 100%; background: #ff7a59; width: 0%; transition: width .2s; }}
</style>
</head>
<body>
<h1>Subir {label}</h1>
<p class="lead">El archivo se guardará en HubSpot y se asociará al pedido <strong>{numero_de_pedido}</strong>.{destinos_hint}</p>

<label class="drop" for="file" id="drop">
  <p>Arrastra archivos aquí o haz click para seleccionar</p>
  <p class="hint">{friendly}. Máximo 50 MB por archivo. {limit_hint}</p>
</label>
<input type="file" id="file" class="visually-hidden" accept="{accept_attr}" {multiple_attr} />

<ul class="files" id="files"></ul>
<div class="progress" id="progress"><div class="bar" id="bar"></div></div>
<div class="actions">
  <button class="primary" id="upload" disabled>Subir</button>
</div>
<div class="status" id="status"></div>

<script>
  const ALLOWED_MIMES = {mimes_json};
  const MAX_FILES = {max_files};
  const drop = document.getElementById('drop');
  const fileInput = document.getElementById('file');
  const filesEl = document.getElementById('files');
  const uploadBtn = document.getElementById('upload');
  const statusEl = document.getElementById('status');
  const progressEl = document.getElementById('progress');
  const barEl = document.getElementById('bar');
  let queue = [];

  function renderQueue() {{
    filesEl.innerHTML = '';
    queue.forEach((item, idx) => {{
      const li = document.createElement('li');
      li.dataset.idx = String(idx);
      if (item.status === 'ok') li.classList.add('ok');
      if (item.status === 'err') li.classList.add('err');
      const name = document.createElement('span');
      name.className = 'name';
      name.textContent = item.file.name;
      const size = document.createElement('span');
      size.className = 'size';
      size.textContent = (item.file.size / 1024 / 1024).toFixed(2) + ' MB';
      const rm = document.createElement('span');
      rm.className = 'remove';
      rm.textContent = '×';
      rm.title = 'Quitar';
      rm.addEventListener('click', () => {{
        queue.splice(idx, 1);
        renderQueue();
        uploadBtn.disabled = queue.length === 0;
      }});
      li.appendChild(name);
      li.appendChild(size);
      li.appendChild(rm);
      filesEl.appendChild(li);
    }});
  }}

  function addFiles(list) {{
    let added = 0;
    for (const f of list) {{
      if (queue.length >= MAX_FILES) {{
        statusEl.textContent = '✗ Has alcanzado el máximo de ' + MAX_FILES + ' archivos en esta tanda.';
        statusEl.className = 'status err';
        break;
      }}
      if (f.size > 50 * 1024 * 1024) {{
        statusEl.textContent = '✗ ' + f.name + ' supera 50 MB.';
        statusEl.className = 'status err';
        continue;
      }}
      if (f.type && ALLOWED_MIMES.length && !ALLOWED_MIMES.includes(f.type)) {{
        statusEl.textContent = '✗ Tipo no admitido: ' + f.name;
        statusEl.className = 'status err';
        continue;
      }}
      queue.push({{ file: f, status: 'pending' }});
      added++;
    }}
    if (added > 0) {{
      statusEl.textContent = '';
      statusEl.className = 'status';
    }}
    renderQueue();
    uploadBtn.disabled = queue.length === 0;
  }}

  drop.addEventListener('dragover', e => {{
    e.preventDefault();
    drop.classList.add('dragover');
  }});
  drop.addEventListener('dragleave', () => drop.classList.remove('dragover'));
  drop.addEventListener('drop', e => {{
    e.preventDefault();
    drop.classList.remove('dragover');
    if (e.dataTransfer.files.length) addFiles(e.dataTransfer.files);
  }});

  fileInput.addEventListener('change', () => {{
    if (fileInput.files.length) addFiles(fileInput.files);
    fileInput.value = '';
  }});

  function uploadOne(item) {{
    return new Promise(resolve => {{
      const fd = new FormData();
      fd.append('file', item.file, item.file.name);
      const xhr = new XMLHttpRequest();
      const uploadPath = window.location.pathname.replace('/upload-modal', '/upload');
      xhr.open('POST', uploadPath + window.location.search, true);
      xhr.upload.onprogress = e => {{
        if (e.lengthComputable) barEl.style.width = ((e.loaded / e.total) * 100) + '%';
      }};
      xhr.onload = () => {{
        let data = {{}};
        try {{ data = JSON.parse(xhr.responseText); }} catch (_) {{}}
        if (xhr.status >= 200 && xhr.status < 300 && data && data.success) {{
          item.status = 'ok';
          resolve({{ ok: true, data }});
        }} else {{
          item.status = 'err';
          const code = data && data.error_code;
          const msg = (data && data.error) || ('Error ' + xhr.status);
          resolve({{ ok: false, error: msg, error_code: code }});
        }}
      }};
      xhr.onerror = () => {{
        item.status = 'err';
        resolve({{ ok: false, error: 'Error de red' }});
      }};
      xhr.send(fd);
    }});
  }}

  uploadBtn.addEventListener('click', async () => {{
    if (queue.length === 0) return;
    uploadBtn.disabled = true;
    progressEl.style.display = 'block';
    let lastError = null;
    let lastErrorCode = null;
    for (let i = 0; i < queue.length; i++) {{
      const item = queue[i];
      if (item.status === 'ok') continue;
      barEl.style.width = '0%';
      statusEl.textContent = 'Subiendo ' + item.file.name + '… (' + (i + 1) + '/' + queue.length + ')';
      statusEl.className = 'status';
      const res = await uploadOne(item);
      renderQueue();
      if (!res.ok) {{
        lastError = res.error;
        lastErrorCode = res.error_code;
        if (res.error_code === 'limite_archivos_excedido') break;
      }}
    }}
    barEl.style.width = '100%';
    const pendientes = queue.filter(q => q.status !== 'ok').length;
    if (pendientes === 0) {{
      statusEl.textContent = '✓ Todos los archivos subidos. Puedes cerrar esta ventana.';
      statusEl.className = 'status ok';
    }} else if (lastError) {{
      statusEl.textContent = '✗ ' + lastError;
      statusEl.className = 'status err';
      uploadBtn.disabled = false;
    }}
  }});
</script>
</body>
</html>"""
