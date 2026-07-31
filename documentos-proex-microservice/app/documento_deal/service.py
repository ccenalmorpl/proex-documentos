import asyncio
import logging
from typing import Dict, List, Optional, Tuple

from hubspot.crm.associations.v4 import (
    AssociationSpec,
    BatchInputPublicAssociationMultiPost,
    BatchInputPublicDefaultAssociationMultiPost,
    PublicAssociationMultiPost,
    PublicDefaultAssociationMultiPost,
    PublicObjectId,
)
from hubspot.crm.deals import (
    SimplePublicObjectInput,
    SimplePublicObjectInputForCreate,
)

from app.core.constants import (
    ASSOC_CATEGORY_USER_DEFINED,
    ASSOC_TYPE_ID_COTIZACION_TO_DOCUMENTO,
    ASSOC_TYPE_ID_DOCUMENTO_TO_CONTENEDOR,
    ASSOC_TYPE_ID_PEDIDO_TO_DOCUMENTO,
    CONTENEDOR_PROP_CERT_ORIGEN,
    CONTENEDOR_PROP_CERT_ORIGEN_BORRADOR,
    CONTENEDOR_PROP_CERT_ORIGEN_VALIDADO,
    CONTENEDOR_PROP_CERT_SANITARIO,
    CONTENEDOR_PROP_CERT_SANITARIO_VALIDADO,
    CONTENEDOR_PROP_DOCUMENTACION_RECIBIDA,
    CONTENEDOR_PROP_MERCANCIA_RETIRADA,
    CONTENEDOR_PROP_DOCUMENTOS,
    CONTENEDOR_PROP_DOCUMENTOS_A_GENERAR,
    CONTENEDOR_PROP_OTROS_DOCUMENTOS,
    DEAL_PROP_BORRADOR_BL,
    DEAL_PROP_NUMERO_DE_PEDIDO,
    DEAL_PROP_PIPELINE,
    DOC_DEALSTAGE_EN_PROCESO,
    DOC_GENERAR_OTROS_TO_PREFIXES,
    DOC_GENERAR_VALUE_BL,
    DOC_GENERAR_VALUE_ORIGEN,
    DOC_GENERAR_VALUE_OTROS,
    DOC_GENERAR_VALUE_SANITARIO,
    DOCUMENTO_PIPELINE_ID,
    OBJECT_TYPE_COBRO,
    OBJECT_TYPE_COMPANY,
    OBJECT_TYPE_CONTENEDOR,
    OBJECT_TYPE_DEAL,
    OBJECT_TYPE_ELEMENTO,
    OBJECT_TYPE_PROVEEDOR,
    OBJECT_TYPE_RUTA,
    PEDIDO_DEALSTAGE_PREPARAR_DOC,
    PEDIDO_PIPELINE_ID,
    PEDIDO_PROPS_A_REPLICAR_EN_DOCUMENTO,
)
from app.documento_deal.dealstage_calculator import calcular_dealstage_documento
from app.documento_deal.schemas import WebhookDocumentoResponse
from app.pedidos.service import (
    _batch_read_contenedores_detalle,
    _batch_read_deals_detalle,
    _batch_read_deals_min,
    _build_bl_archivos,
    _build_documentos_archivos,
    _build_origen_archivos,
    _build_sanitario_archivos,
    _classify_deals,
    _es_camion,
    _get_contenedor_ids_for_deals,
    _get_deal_ids_for_contenedores,
    _parse_bool,
    _parse_documentos_a_generar,
    _search_pedidos_by_numero,
)
from app.shared.files import parse_file_ids
from app.shared.hubspot_batch import batch_read_associations, batch_read_objects
from app.shared.hubspot_client import hubspot_client

logger = logging.getLogger(__name__)

_BATCH_SIZE = 100


def _chunked(items: List, size: int = _BATCH_SIZE):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def _get_proveedor_assocs_for_deal(client, deal_id: str) -> List[Tuple[str, str, int]]:
    """(proveedor_id, category, type_id) de todas las asociaciones del deal a
    Proveedores, sin filtrar por label, para replicarlas tal cual."""
    out: List[Tuple[str, str, int]] = []
    try:
        resp = client.crm.associations.v4.basic_api.get_page(
            object_type=OBJECT_TYPE_DEAL,
            object_id=deal_id,
            to_object_type=OBJECT_TYPE_PROVEEDOR,
            limit=100,
        )
    except Exception as e:
        logger.warning(f"  [proveedor_assocs] error leyendo deal={deal_id}: {e}")
        return out

    for assoc in (resp.results or []):
        pid = str(assoc.to_object_id)
        for at in (assoc.association_types or []):
            cat = getattr(at, "category", None)
            tid = getattr(at, "type_id", None)
            if cat and tid is not None:
                out.append((pid, cat, int(tid)))
    return out


def _get_ruta_assocs_for_deal(client, deal_id: str) -> List[Tuple[str, str, int]]:
    """(ruta_id, category, type_id) de todas las asociaciones del deal a Rutas
    (custom object), sin filtrar por label, para replicarlas tal cual."""
    out: List[Tuple[str, str, int]] = []
    try:
        resp = client.crm.associations.v4.basic_api.get_page(
            object_type=OBJECT_TYPE_DEAL,
            object_id=deal_id,
            to_object_type=OBJECT_TYPE_RUTA,
            limit=100,
        )
    except Exception as e:
        logger.warning(f"  [ruta_assocs] error leyendo deal={deal_id}: {e}")
        return out

    for assoc in (resp.results or []):
        rid = str(assoc.to_object_id)
        for at in (assoc.association_types or []):
            cat = getattr(at, "category", None)
            tid = getattr(at, "type_id", None)
            if cat and tid is not None:
                out.append((rid, cat, int(tid)))
    return out


def _build_documento_ruta_batches(
    ruta_assocs: List[Tuple[str, str, int]],
    documento_deal_id: str,
) -> Tuple[Dict[int, List[Tuple[str, str, int]]], List[Tuple[str, str]]]:
    """Fan-out de (ruta_id, category, type_id) → (user_by_type, default_pairs) para
    asociar el Negocio Documento a las rutas heredadas preservando el type_id de la
    etiqueta (714 terrestre / 716 marítima)."""
    user_by_type: Dict[int, List[Tuple[str, str, int]]] = {}
    default_pairs: List[Tuple[str, str]] = []
    for ruta_id, category, type_id in ruta_assocs:
        if category == ASSOC_CATEGORY_USER_DEFINED:
            user_by_type.setdefault(type_id, []).append((documento_deal_id, ruta_id, type_id))
        else:
            default_pairs.append((documento_deal_id, ruta_id))
    return user_by_type, default_pairs


def _batch_create_user_defined_assocs(
    client, from_object_type: str, to_object_type: str,
    triples: List[Tuple[str, str, int]],
) -> int:
    if not triples:
        return 0
    n_errors = 0
    for chunk in _chunked(triples):
        inputs = [
            PublicAssociationMultiPost(
                _from=PublicObjectId(id=fid),
                to=PublicObjectId(id=tid),
                types=[AssociationSpec(
                    association_category=ASSOC_CATEGORY_USER_DEFINED,
                    association_type_id=type_id,
                )],
            )
            for fid, tid, type_id in chunk
        ]
        batch_input = BatchInputPublicAssociationMultiPost(inputs=inputs)
        try:
            resp = client.crm.associations.v4.batch_api.create(
                from_object_type=from_object_type,
                to_object_type=to_object_type,
                batch_input_public_association_multi_post=batch_input,
            )
            errors = getattr(resp, "errors", None) or []
            n_errors += len(errors)
            for err in errors:
                logger.warning(
                    f"  [assoc_user_defined] from={from_object_type} "
                    f"to={to_object_type} parcial: {err}"
                )
        except Exception as e:
            n_errors += len(chunk)
            logger.warning(
                f"  [assoc_user_defined] error from={from_object_type} "
                f"to={to_object_type} chunk_size={len(chunk)}: {e}"
            )
    return n_errors


def _batch_create_default_assocs(
    client, from_object_type: str, to_object_type: str,
    pairs: List[Tuple[str, str]],
) -> int:
    if not pairs:
        return 0
    n_errors = 0
    for chunk in _chunked(pairs):
        inputs = [
            PublicDefaultAssociationMultiPost(
                _from=PublicObjectId(id=fid),
                to=PublicObjectId(id=tid),
            )
            for fid, tid in chunk
        ]
        batch_input = BatchInputPublicDefaultAssociationMultiPost(inputs=inputs)
        try:
            resp = client.crm.associations.v4.batch_api.create_default(
                from_object_type=from_object_type,
                to_object_type=to_object_type,
                batch_input_public_default_association_multi_post=batch_input,
            )
            errors = getattr(resp, "errors", None) or []
            n_errors += len(errors)
            for err in errors:
                logger.warning(
                    f"  [assoc_default] from={from_object_type} "
                    f"to={to_object_type} parcial: {err}"
                )
        except Exception as e:
            n_errors += len(chunk)
            logger.warning(
                f"  [assoc_default] error from={from_object_type} "
                f"to={to_object_type} chunk_size={len(chunk)}: {e}"
            )
    return n_errors


def _read_documento_replica_props(client, pedido_deal_id: str) -> Dict[str, str]:
    try:
        pd = client.crm.deals.basic_api.get_by_id(
            deal_id=pedido_deal_id,
            properties=PEDIDO_PROPS_A_REPLICAR_EN_DOCUMENTO,
        )
    except Exception as e:
        logger.warning(
            f"[documento_create] no se pudieron leer props de cabecera de "
            f"pedido={pedido_deal_id}: {e}; documento creado sin réplica."
        )
        return {}
    props = pd.properties or {}
    return {p: props[p] for p in PEDIDO_PROPS_A_REPLICAR_EN_DOCUMENTO if props.get(p) not in (None, "")}


def _create_documento_deal(
    client, replica_props: Dict[str, str], dealname: str,
) -> Optional[str]:
    props = {
        **replica_props,
        "dealname": dealname,
        "pipeline": DOCUMENTO_PIPELINE_ID,
        "dealstage": DOC_DEALSTAGE_EN_PROCESO,
    }
    try:
        created = client.crm.deals.basic_api.create(
            simple_public_object_input_for_create=SimplePublicObjectInputForCreate(properties=props),
        )
        return str(created.id)
    except Exception as e:
        logger.error(f"[documento_create] create de documento-deal fallido: {e}", exc_info=True)
        return None


def _crear_asociaciones_documento(
    client, documento_deal_id: str, contenedor_id: str,
    pedido_deal_id: str, cotizacion_deal_id: Optional[str],
) -> None:
    # Dedicadas: cada una se crea desde el lado en que se definió en HubSpot.
    err_cn = _batch_create_user_defined_assocs(
        client, OBJECT_TYPE_DEAL, OBJECT_TYPE_CONTENEDOR,
        [(documento_deal_id, contenedor_id, ASSOC_TYPE_ID_DOCUMENTO_TO_CONTENEDOR)],
    )
    err_ped = _batch_create_user_defined_assocs(
        client, OBJECT_TYPE_DEAL, OBJECT_TYPE_DEAL,
        [(pedido_deal_id, documento_deal_id, ASSOC_TYPE_ID_PEDIDO_TO_DOCUMENTO)],
    )
    err_cot = 0
    if cotizacion_deal_id:
        err_cot = _batch_create_user_defined_assocs(
            client, OBJECT_TYPE_DEAL, OBJECT_TYPE_DEAL,
            [(cotizacion_deal_id, documento_deal_id, ASSOC_TYPE_ID_COTIZACION_TO_DOCUMENTO)],
        )

    # Resto: se replican las del pedido-deal con sus mismos typeIds/category.
    company_ids = batch_read_associations(
        client, OBJECT_TYPE_DEAL, OBJECT_TYPE_COMPANY, [pedido_deal_id],
    ).get(pedido_deal_id, [])
    err_comp = _batch_create_default_assocs(
        client, OBJECT_TYPE_DEAL, OBJECT_TYPE_COMPANY,
        [(documento_deal_id, c) for c in company_ids],
    )

    elemento_ids = batch_read_associations(
        client, OBJECT_TYPE_DEAL, OBJECT_TYPE_ELEMENTO, [pedido_deal_id],
    ).get(pedido_deal_id, [])
    err_elem = _batch_create_default_assocs(
        client, OBJECT_TYPE_DEAL, OBJECT_TYPE_ELEMENTO,
        [(documento_deal_id, e) for e in elemento_ids],
    )

    cobro_ids = batch_read_associations(
        client, OBJECT_TYPE_DEAL, OBJECT_TYPE_COBRO, [pedido_deal_id],
    ).get(pedido_deal_id, [])
    err_cobro = _batch_create_default_assocs(
        client, OBJECT_TYPE_DEAL, OBJECT_TYPE_COBRO,
        [(documento_deal_id, c) for c in cobro_ids],
    )

    prov_user_by_type: Dict[int, List[Tuple[str, str, int]]] = {}
    prov_default: List[Tuple[str, str]] = []
    for pid, category, type_id in _get_proveedor_assocs_for_deal(client, pedido_deal_id):
        if category == ASSOC_CATEGORY_USER_DEFINED:
            prov_user_by_type.setdefault(type_id, []).append((documento_deal_id, pid, type_id))
        else:
            prov_default.append((documento_deal_id, pid))
    err_prov = 0
    for type_id, triples in prov_user_by_type.items():
        err_prov += _batch_create_user_defined_assocs(
            client, OBJECT_TYPE_DEAL, OBJECT_TYPE_PROVEEDOR, triples,
        )
    if prov_default:
        err_prov += _batch_create_default_assocs(
            client, OBJECT_TYPE_DEAL, OBJECT_TYPE_PROVEEDOR, prov_default,
        )

    # Rutas: heredar las rutas terrestre/marítima de la cotización (fallback al
    # pedido si la cotización no se resolvió) preservando category+type_id (714/716).
    ruta_source_deal = cotizacion_deal_id or pedido_deal_id
    ruta_user_by_type, ruta_default = _build_documento_ruta_batches(
        _get_ruta_assocs_for_deal(client, ruta_source_deal), documento_deal_id,
    )
    err_ruta = 0
    for type_id, triples in ruta_user_by_type.items():
        err_ruta += _batch_create_user_defined_assocs(
            client, OBJECT_TYPE_DEAL, OBJECT_TYPE_RUTA, triples,
        )
    if ruta_default:
        err_ruta += _batch_create_default_assocs(
            client, OBJECT_TYPE_DEAL, OBJECT_TYPE_RUTA, ruta_default,
        )

    logger.info(
        f"[documento_create] asociaciones documento={documento_deal_id}: "
        f"contenedor errors={err_cn}, pedido errors={err_ped}, cotizacion errors={err_cot}, "
        f"company errors={err_comp}, elementos errors={err_elem}, cobros errors={err_cobro}, "
        f"proveedores errors={err_prov}, rutas errors={err_ruta}"
    )


def _crear_documento_desde_pedido_sync(pedido_deal_id: str) -> WebhookDocumentoResponse:
    from hubspot.crm.deals.exceptions import NotFoundException

    client = hubspot_client.get_client()

    try:
        deal = client.crm.deals.basic_api.get_by_id(
            deal_id=pedido_deal_id,
            properties=[DEAL_PROP_PIPELINE, "dealstage", DEAL_PROP_NUMERO_DE_PEDIDO],
        )
    except NotFoundException:
        return WebhookDocumentoResponse(
            success=False, estado="fallido", pedido_deal_id=pedido_deal_id,
            error="pedido_deal_no_encontrado",
        )

    props = deal.properties or {}
    pipeline = (props.get(DEAL_PROP_PIPELINE) or "").strip()
    dealstage = (props.get("dealstage") or "").strip()
    numero_de_pedido = (props.get(DEAL_PROP_NUMERO_DE_PEDIDO) or "").strip()

    if pipeline != PEDIDO_PIPELINE_ID:
        return WebhookDocumentoResponse(
            success=False, estado="fallido", pedido_deal_id=pedido_deal_id,
            error="deal_no_es_pedido",
        )

    if dealstage != PEDIDO_DEALSTAGE_PREPARAR_DOC:
        logger.warning(
            f"[documento_create] pedido={pedido_deal_id} dealstage={dealstage!r} "
            f"!= preparar_documentacion; no se crea (guard estricto)."
        )
        return WebhookDocumentoResponse(
            success=False, estado="fallido", pedido_deal_id=pedido_deal_id,
            error="pedido_no_en_preparar_documentacion",
        )

    contenedor_ids = batch_read_associations(
        client, OBJECT_TYPE_DEAL, OBJECT_TYPE_CONTENEDOR, [pedido_deal_id],
    ).get(pedido_deal_id, [])
    if not contenedor_ids:
        return WebhookDocumentoResponse(
            success=False, estado="fallido", pedido_deal_id=pedido_deal_id,
            error="pedido_sin_contenedor",
        )
    if len(contenedor_ids) > 1:
        logger.warning(
            f"[documento_create] pedido={pedido_deal_id} con {len(contenedor_ids)} "
            f"contenedores (esperado 1): {contenedor_ids}; se toma el primero."
        )
    contenedor_id = contenedor_ids[0]

    # Los pedidos de tipo camión no pasan por el pipeline de Documentos: se
    # gestionan hasta la entrega en el propio asistente de Pedidos (bloque
    # "Pedido entregado"). "Preparar documentación" es un movimiento manual, así
    # que este guard es el único punto que evita crear el Negocio Documento.
    tipo_contenedor = (
        batch_read_objects(client, OBJECT_TYPE_CONTENEDOR, [contenedor_id], ["tipo_contenedor"])
        .get(contenedor_id, {})
        .get("tipo_contenedor")
    )
    if _es_camion(tipo_contenedor):
        logger.info(
            f"[documento_create] contenedor={contenedor_id} es camión "
            f"(tipo_contenedor={tipo_contenedor!r}); no se crea Negocio Documento."
        )
        return WebhookDocumentoResponse(
            success=True, estado="saltado_camion", pedido_deal_id=pedido_deal_id,
            contenedor_id=contenedor_id,
        )

    contenedor_deals = _get_deal_ids_for_contenedores(
        client, [contenedor_id],
    ).get(contenedor_id, [])
    deal_props_min = _batch_read_deals_min(client, contenedor_deals) if contenedor_deals else {}
    cotizacion, _pedido, documento = _classify_deals(contenedor_deals, deal_props_min)

    if documento is not None:
        logger.info(
            f"[documento_create] contenedor={contenedor_id} ya tiene documento-deal "
            f"{documento[0]}; idempotente, se salta."
        )
        return WebhookDocumentoResponse(
            success=True, estado="saltado", pedido_deal_id=pedido_deal_id,
            contenedor_id=contenedor_id, documento_deal_id=documento[0],
        )

    cotizacion_deal_id = cotizacion[0] if cotizacion else None

    replica_props = _read_documento_replica_props(client, pedido_deal_id)
    nombre_cn = (
        batch_read_objects(client, OBJECT_TYPE_CONTENEDOR, [contenedor_id], ["nombre"])
        .get(contenedor_id, {})
        .get("nombre")
        or f"CN-{contenedor_id}"
    )
    base_nombre = numero_de_pedido or f"pedido {pedido_deal_id}"
    dealname = f"DOC {base_nombre} ({nombre_cn})"

    documento_deal_id = _create_documento_deal(client, replica_props, dealname)
    if not documento_deal_id:
        return WebhookDocumentoResponse(
            success=False, estado="fallido", pedido_deal_id=pedido_deal_id,
            contenedor_id=contenedor_id, error="create_deal_failed",
        )

    _crear_asociaciones_documento(
        client, documento_deal_id, contenedor_id, pedido_deal_id, cotizacion_deal_id,
    )

    try:
        _recalcular_dealstage_para_documento(client, documento_deal_id)
    except Exception as e:
        logger.warning(
            f"[documento_create] recálculo inicial documento={documento_deal_id} "
            f"falló (no bloqueante): {e}"
        )

    logger.info(
        f"[documento_create] creado documento={documento_deal_id} "
        f"pedido={pedido_deal_id} contenedor={contenedor_id} numero={numero_de_pedido!r}"
    )
    return WebhookDocumentoResponse(
        success=True, estado="creado", pedido_deal_id=pedido_deal_id,
        contenedor_id=contenedor_id, documento_deal_id=documento_deal_id,
    )


async def crear_documento_desde_pedido(pedido_deal_id: str) -> WebhookDocumentoResponse:
    try:
        return await asyncio.to_thread(_crear_documento_desde_pedido_sync, pedido_deal_id)
    except Exception as e:
        logger.error(
            f"[documento_create] ERROR pedido_deal_id={pedido_deal_id!r}: {e}", exc_info=True,
        )
        return WebhookDocumentoResponse(
            success=False, estado="fallido", pedido_deal_id=pedido_deal_id, error=str(e),
        )


def _otros_obligatorios_ok(generar: set, contenedor_props: dict) -> bool:
    requeridos = generar & (set(DOC_GENERAR_OTROS_TO_PREFIXES) | {DOC_GENERAR_VALUE_OTROS})
    if not requeridos:
        return True
    nombres = [
        (a.name or "")
        for a in _build_documentos_archivos(contenedor_props.get(CONTENEDOR_PROP_DOCUMENTOS))
    ]
    for clave in requeridos:
        if clave == DOC_GENERAR_VALUE_OTROS:
            if not parse_file_ids(contenedor_props.get(CONTENEDOR_PROP_OTROS_DOCUMENTOS)):
                return False
            continue
        prefijos = DOC_GENERAR_OTROS_TO_PREFIXES.get(clave, ())
        if not any(n.startswith(p) for n in nombres for p in prefijos):
            return False
    return True


def _derivar_flags_documento(
    pedido_props: dict, contenedor_props: dict, documento_props: Optional[dict] = None,
) -> dict:
    generar = set(_parse_documentos_a_generar(
        contenedor_props.get(CONTENEDOR_PROP_DOCUMENTOS_A_GENERAR)
    ))

    bl_required = DOC_GENERAR_VALUE_BL in generar
    origen_required = DOC_GENERAR_VALUE_ORIGEN in generar
    sanitario_required = DOC_GENERAR_VALUE_SANITARIO in generar

    # Documento manda: el fichero BL se lee del propio Documento, fallback al Pedido.
    bl_borrador_raw = (
        (documento_props or {}).get(DEAL_PROP_BORRADOR_BL)
        or pedido_props.get(DEAL_PROP_BORRADOR_BL)
    )
    bl_archivos = _build_bl_archivos(bl_borrador_raw)
    bl_borrador_present = any(a.tipo == "borrador" for a in bl_archivos)
    bl_final_present = any(a.tipo == "final" for a in bl_archivos)

    origen_archivos = _build_origen_archivos(
        contenedor_props.get(CONTENEDOR_PROP_CERT_ORIGEN_BORRADOR),
        contenedor_props.get(CONTENEDOR_PROP_CERT_ORIGEN),
    )
    sanitario_archivos = _build_sanitario_archivos(
        contenedor_props.get(CONTENEDOR_PROP_CERT_SANITARIO)
    )

    origen_borrador_present = any(a.tipo == "borrador" for a in origen_archivos)
    sanitario_borrador_present = any(a.tipo == "borrador" for a in sanitario_archivos)
    origen_validado_present = (
        any(a.tipo in ("validado", "sellado") for a in origen_archivos)
        or _parse_bool(contenedor_props.get(CONTENEDOR_PROP_CERT_ORIGEN_VALIDADO))
    )
    sanitario_validado_present = (
        any(a.tipo in ("validado", "sellado") for a in sanitario_archivos)
        or _parse_bool(contenedor_props.get(CONTENEDOR_PROP_CERT_SANITARIO_VALIDADO))
    )

    return {
        "bl_borrador_ok": (not bl_required) or bl_borrador_present,
        "bl_final_ok": (not bl_required) or bl_final_present,
        "certs_borrador_ok": (
            ((not origen_required) or origen_borrador_present)
            and ((not sanitario_required) or sanitario_borrador_present)
        ),
        "certs_validado_ok": (
            ((not origen_required) or origen_validado_present)
            and ((not sanitario_required) or sanitario_validado_present)
        ),
        "otros_obligatorios_ok": _otros_obligatorios_ok(generar, contenedor_props),
        "documentacion_recibida": _parse_bool(
            contenedor_props.get(CONTENEDOR_PROP_DOCUMENTACION_RECIBIDA)
        ),
        "mercancia_retirada": _parse_bool(
            contenedor_props.get(CONTENEDOR_PROP_MERCANCIA_RETIRADA)
        ),
    }


def _read_dealstage(client, deal_id: str) -> str:
    try:
        d = client.crm.deals.basic_api.get_by_id(deal_id=deal_id, properties=["dealstage"])
        return ((d.properties or {}).get("dealstage") or "").strip()
    except Exception as e:
        logger.warning(f"[recalcular_dealstage_documento] no se pudo leer dealstage deal={deal_id}: {e}")
        return ""


def _recalcular_dealstage_para_documento(client, documento_deal_id: str) -> bool:
    cids = _get_contenedor_ids_for_deals(client, [documento_deal_id]).get(documento_deal_id, [])
    if not cids:
        logger.warning(
            f"[recalcular_dealstage_documento] documento={documento_deal_id} sin contenedor asociado."
        )
        return False
    contenedor_id = cids[0]

    contenedor_deals = _get_deal_ids_for_contenedores(client, [contenedor_id]).get(contenedor_id, [])
    _cot, pedido, _doc = _classify_deals(
        contenedor_deals, _batch_read_deals_min(client, contenedor_deals),
    )
    pedido_deal_id = pedido[0] if pedido else None

    deal_ids_to_read = [d for d in {pedido_deal_id, documento_deal_id} if d]
    deal_props = _batch_read_deals_detalle(client, deal_ids_to_read) if deal_ids_to_read else {}
    pedido_props = deal_props.get(pedido_deal_id, {}) if pedido_deal_id else {}
    documento_props = deal_props.get(documento_deal_id, {})
    contenedor_props = _batch_read_contenedores_detalle(client, [contenedor_id]).get(contenedor_id, {})

    flags = _derivar_flags_documento(pedido_props, contenedor_props, documento_props)
    dealstage_actual = _read_dealstage(client, documento_deal_id)
    nuevo = calcular_dealstage_documento(**flags, dealstage_actual=dealstage_actual)
    if nuevo == dealstage_actual:
        return False

    client.crm.deals.basic_api.update(
        deal_id=documento_deal_id,
        simple_public_object_input=SimplePublicObjectInput(properties={"dealstage": nuevo}),
    )
    logger.info(
        f"[recalcular_dealstage_documento] deal={documento_deal_id} "
        f"{dealstage_actual!r}->{nuevo!r}"
    )
    return True


def _recalcular_dealstage_documento(client, numero_de_pedido: str) -> int:
    documento_deal_ids = _search_pedidos_by_numero(client, numero_de_pedido, DOCUMENTO_PIPELINE_ID)
    if not documento_deal_ids:
        return 0
    cambios = 0
    for did in documento_deal_ids:
        try:
            if _recalcular_dealstage_para_documento(client, did):
                cambios += 1
        except Exception as e:
            logger.warning(
                f"[recalcular_dealstage_documento] fallo deal={did}: {e}"
            )
    return cambios
