import logging
import time
import uuid
from typing import List, Optional, Tuple

from app.shared.hubspot_batch import batch_read_associations, batch_read_objects

from hubspot.crm.objects import (
    PublicObjectSearchRequest,
    Filter,
    FilterGroup,
    BatchInputSimplePublicObjectBatchInput,
    SimplePublicObjectBatchInput,
    BatchReadInputSimplePublicObjectId,
    SimplePublicObjectId,
)

from app.documentos.schemas import (
    PendingRequest, PendingResponse, ContenedorListItem, DocInfo,
    GenerateRequest, GenerateResponse, GeneratedDocResult,
    GeneratedRequest, GeneratedResponse,
    RollbackRequest, RollbackResponse,
    DealContextResponse,
)
from app.core.constants import (
    OBJECT_TYPE_CONTENEDOR,
    OBJECT_TYPE_DEAL,
    OBJECT_TYPE_COMPANY,
    ASSOCIATION_TYPE_CONTENEDOR_TO_ELEMENTO,
    CONTENEDOR_DOC_PROPERTIES,
    CONTENEDOR_ALL_PROPERTIES,
    CONTENEDOR_GENERATE_PROPERTIES,
    CONTENEDOR_PROP_DOCUMENTOS_A_GENERAR,
    CONTENEDOR_PROP_ETD,
    CONTENEDOR_PROP_ETA,
    ALL_DOC_TYPES,
    DOC_TYPE_ORIGEN_BORRADOR,
    DOC_TYPE_ORIGEN_FINAL,
    DOC_TYPE_SANITARIO,
    DOC_TYPE_TO_HUBSPOT_FILTER,
    DOC_TYPE_TO_FILE_PROPERTY,
    ALL_CONTENEDOR_FILE_PROPERTY_NAMES,
    ROLLBACK_API_TO_INTERNAL_DOC_TYPE,
    DEAL_GENERATE_PROPERTIES,
    DOC_TYPE_LABELS_ES,
    DEAL_PROP_PIPELINE,
    PEDIDO_PIPELINE_ID,
    DOCUMENTO_PIPELINE_ID,
)
from app.shared.hubspot_client import hubspot_client
from app.shared.files import (
    delete_file,
    fetch_file_metadata,
    parse_file_ids,
    serialize_file_ids,
    upload_pdf,
)
from app.shared.properties import resolve_enum_label
from app.shared.hubdb import get_formato_label_map
from app.shared.elementos import get_elementos_fabricante_por_contenedor

from app.core.config import settings
from app.documentos.domain.origen import build_origen_payload
from app.documentos.domain.sanitario import build_sanitario_payload
from app.documentos.pdf_renderer import render_origen_borrador_v2, render_origen_final_v2, render_sanitario_v2

logger = logging.getLogger(__name__)

def _build_doc_info_for_container(properties: dict, doc_type: str, required: bool) -> DocInfo:
    """Construye DocInfo para un doc_type leyendo el estado desde las propiedades del contenedor."""
    generated = _is_doc_generated(doc_type, properties)
    file_prop = DOC_TYPE_TO_FILE_PROPERTY.get(doc_type)
    raw_file = properties.get(file_prop) if file_prop else None
    file_url = raw_file if raw_file else None

    group_prop = CONTENEDOR_DOC_PROPERTIES.get(doc_type, {}).get("group_generation_id")
    raw_group = properties.get(group_prop) if group_prop else None
    group_id = raw_group if raw_group else None

    doc_info = DocInfo(
        doc_type=doc_type,
        generated=generated,
        required=required,
        group_id=group_id,
        file_url=file_url,
    )
    logger.debug(
        f"  [DocInfo] doc_type={doc_type} file_prop={file_prop!r} "
        f"required={required} generated={generated} "
        f"group_id={group_id!r} file_url={file_url!r}"
    )
    return doc_info

def _map_to_list_item(
    obj_id: str,
    properties: dict,
    deal_id: Optional[str] = None,
    deal_name: Optional[str] = None,
    deal_properties: Optional[dict] = None,
    parsed_documentos_a_generar: Optional[List[str]] = None,
) -> ContenedorListItem:
    """Convierte un objeto Contenedor de HubSpot en ContenedorListItem."""
    if parsed_documentos_a_generar is None:
        parsed_documentos_a_generar = _parse_documentos_a_generar(obj_id, properties)

    docs = [
        _build_doc_info_for_container(
            properties, dt,
            required=_is_doc_type_required(dt, parsed_documentos_a_generar),
        )
        for dt in ALL_DOC_TYPES
    ]
    item = ContenedorListItem(
        id=obj_id,
        name=properties.get("nombre", ""),
        etd=properties.get(CONTENEDOR_PROP_ETD),
        eta=properties.get(CONTENEDOR_PROP_ETA),
        deal_id=deal_id or None,
        deal_name=deal_name or None,
        deal_properties=deal_properties or None,
        docs=docs,
    )
    logger.debug(
        f"  [MapItem] id={obj_id} name={item.name!r} "
        f"deal_id={item.deal_id!r} deal_name={item.deal_name!r} "
        f"etd={item.etd!r} eta={item.eta!r} "
        f"docs={[{'doc_type': d.doc_type, 'required': d.required, 'generated': d.generated} for d in item.docs]}"
    )
    return item

def _pick_cotizacion_deal(deal_ids: List[str], deal_data_by_id: dict) -> Tuple[str, dict]:
    """Elige el Negocio Cotización padre entre los deals asociados al contenedor:
    el deal cuyo pipeline NO es el de Pedidos ni el de Documentación. Si ninguno lo
    es, devuelve vacío: nunca se muestra el pedido ni la documentación como 'Negocio'."""
    for did in deal_ids:
        props = deal_data_by_id.get(did) or {}
        pipeline = props.get(DEAL_PROP_PIPELINE)
        if pipeline not in (PEDIDO_PIPELINE_ID, DOCUMENTO_PIPELINE_ID):
            return did, props
    return "", {}


def _get_deal_info_for_containers(
    client,
    container_ids: List[str],
) -> dict:
    """Obtiene (deal_id, deal_name, deal_properties) del Negocio Cotización padre de
    cada contenedor. Un contenedor puede estar asociado a cotización + pedido +
    documentación; la columna 'Negocio' y las props de cabecera se toman SIEMPRE de
    la cotización. Fallo silencioso: si no tiene Deal asociado devuelve ("", "", {})."""
    if not container_ids:
        return {}

    t = time.monotonic()
    contenedor_to_deals = batch_read_associations(
        client, OBJECT_TYPE_CONTENEDOR, OBJECT_TYPE_DEAL, container_ids,
    )
    logger.info(f"[TIMER] _get_deal_info.batch_assoc: {time.monotonic() - t:.2f}s")

    # Leemos TODOS los deals asociados (no solo el primero) para poder distinguir la
    # cotización de pedido/documentación por pipeline.
    all_deal_ids = list({did for deals in contenedor_to_deals.values() for did in deals})
    t = time.monotonic()
    deal_data_by_id = batch_read_objects(
        client,
        OBJECT_TYPE_DEAL,
        all_deal_ids,
        ["dealname", DEAL_PROP_PIPELINE, "certificado_origen_mercancia", "observaciones", "preprints_language"],
    )
    logger.info(f"[TIMER] _get_deal_info.batch_deals: {time.monotonic() - t:.2f}s")

    result: dict = {}
    for cid in container_ids:
        cot_id, cot_props = _pick_cotizacion_deal(contenedor_to_deals.get(cid, []), deal_data_by_id)
        result[cid] = (
            cot_id or "",
            (cot_props.get("dealname") or ""),
            {
                "certificado_origen_mercancia": (cot_props.get("certificado_origen_mercancia") or ""),
                "observaciones": (cot_props.get("observaciones") or ""),
                "preprints_language": (cot_props.get("preprints_language") or ""),
            },
        )
    return result

def _clear_doc_properties(doc_type: str) -> dict:
    """Devuelve un dict de propiedades con valores vacíos para limpiar un tipo de doc."""
    props = CONTENEDOR_DOC_PROPERTIES[doc_type]
    return {v: "" for v in props.values()}

def _search_contenedor_by_nombre(client, nombre: str, props: List[str]) -> dict:
    """Busca Contenedor(es) por la propiedad 'nombre' (EQ). Limit=5 para detectar duplicados."""
    filters = [Filter(property_name="nombre", operator="EQ", value=nombre)]
    search_request = PublicObjectSearchRequest(
        filter_groups=[FilterGroup(filters=filters)],
        properties=props,
        limit=5,
    )
    resp = client.crm.objects.search_api.do_search(
        object_type=OBJECT_TYPE_CONTENEDOR,
        public_object_search_request=search_request,
    )
    return {obj.id: obj.properties for obj in (resp.results or [])}

def _search_contenedores_by_group_prop(
    client, group_prop_name: str, group_id_value: str, props: List[str]
) -> dict:
    """Busca todos los Contenedores cuyo group_prop == group_id_value (paginado)."""
    result: dict = {}
    after: Optional[str] = None
    page_num = 0

    while True:
        page_num += 1
        filters = [Filter(property_name=group_prop_name, operator="EQ", value=group_id_value)]
        search_request = PublicObjectSearchRequest(
            filter_groups=[FilterGroup(filters=filters)],
            properties=props,
            limit=100,
            after=after,
        )
        logger.info(
            f"  [ROLLBACK][search_group] página={page_num} "
            f"group_prop={group_prop_name!r} group_id={group_id_value!r}"
        )
        resp = client.crm.objects.search_api.do_search(
            object_type=OBJECT_TYPE_CONTENEDOR,
            public_object_search_request=search_request,
        )
        for obj in (resp.results or []):
            result[obj.id] = obj.properties
        logger.info(
            f"  [ROLLBACK][search_group] página={page_num} → "
            f"{len(resp.results or [])} resultados (acumulado={len(result)})"
        )
        if resp.paging and resp.paging.next:
            after = resp.paging.next.after
        else:
            break

    return result

def _read_contenedor_file_prop(client, container_id: str, prop: str) -> str:
    try:
        obj = client.crm.objects.basic_api.get_by_id(
            object_type=OBJECT_TYPE_CONTENEDOR,
            object_id=container_id,
            properties=[prop],
        )
        return (obj.properties or {}).get(prop) or ""
    except Exception as e:
        logger.warning(f"[READ_FILE_PROP] cid={container_id!r} prop={prop!r} fallo: {e}")
        return ""


def _merge_file_in_prop(client, sample_container_id: str, prop: str, prefix: str, new_file_id: str) -> str:
    """Lee la prop del contenedor sample, elimina archivos del mismo prefix (y los borra del File Manager), añade el nuevo, devuelve el valor serializado para escribir."""
    current_raw = _read_contenedor_file_prop(client, sample_container_id, prop)
    current_ids = parse_file_ids(current_raw)
    kept_ids: List[str] = []
    for fid in current_ids:
        if fid == new_file_id:
            continue
        meta = fetch_file_metadata(fid)
        if meta and meta.name.startswith(prefix):
            try:
                delete_file(fid)
            except Exception as e:
                logger.warning(f"[MERGE_FILE_PROP] delete_file falló para {fid!r}: {e}")
        else:
            kept_ids.append(fid)
    kept_ids.append(new_file_id)
    return serialize_file_ids(kept_ids)


def _batch_update_contenedores(client, container_ids: List[str], properties: dict) -> dict:
    """Actualiza propiedades en batch sobre Contenedores (chunks de 100). Un fallo en un chunk no aborta los demás."""
    updated = 0
    failed: List[str] = []
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
            chunk_updated = len(resp.results or [])
            updated += chunk_updated
            logger.debug(
                f"  [ROLLBACK][batch_update] chunk {i // chunk_size + 1}: "
                f"solicitados={len(chunk)} actualizados={chunk_updated}"
            )
        except Exception as e:
            logger.error(
                f"  [ROLLBACK][batch_update] ERROR chunk {i // chunk_size + 1}: {e}",
                exc_info=True,
            )
            failed.extend(chunk)

    return {"updated": updated, "failed": failed, "total_requested": len(container_ids)}

def _search_companies_by_name(client, empresa: str) -> List[tuple]:
    """Busca empresas cuyo nombre contenga 'empresa'. Devuelve lista de (company_id, company_name)."""
    from app.empresas.service import _search_companies_by_name as _search

    results = _search(client, empresa)
    logger.info(
        f"  [search_companies] empresa={empresa!r} → "
        f"{len(results)} encontradas | sample={results[:3]}"
    )
    return results

def _resolve_company_ids(client, company_id: str, empresa: str) -> List[str]:
    """IDs de las empresas objetivo. Prioriza el company_id exacto del contexto (una
    sola empresa); si no viene, cae a la búsqueda difusa por nombre (legacy)."""
    if company_id:
        return [company_id]
    return [cid for cid, _ in _search_companies_by_name(client, empresa)]

def _get_contenedores_for_companies(client, company_ids: List[str]) -> dict:
    """Devuelve {contenedor_id: company_id} para todas las empresas dadas. Si un contenedor está asociado a varias empresas, prevalece la última vista."""
    contenedor_to_company: dict = {}

    for company_id in company_ids:
        after = None
        page = 0
        while True:
            page += 1
            kwargs: dict = {
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
                    f"  [assoc] error empresa={company_id} "
                    f"página={page}: {e}"
                )
                break

            page_ids = {assoc.to_object_id for assoc in (resp.results or [])}
            for cid in page_ids:
                contenedor_to_company[cid] = company_id
            logger.debug(
                f"  [assoc] empresa={company_id} página={page} "
                f"+{len(page_ids)} contenedores (acumulado={len(contenedor_to_company)})"
            )

            if resp.paging and resp.paging.next:
                after = resp.paging.next.after
            else:
                break

    return contenedor_to_company

def _batch_read_contenedores(client, contenedor_ids: List[str]) -> dict:
    """Lee propiedades de contenedores en batch (máx 100 por llamada)."""
    props_to_read = CONTENEDOR_ALL_PROPERTIES + [CONTENEDOR_PROP_DOCUMENTOS_A_GENERAR] + ALL_CONTENEDOR_FILE_PROPERTY_NAMES
    result: dict = {}
    chunk_size = 100

    for i in range(0, len(contenedor_ids), chunk_size):
        chunk = contenedor_ids[i:i + chunk_size]
        batch_input = BatchReadInputSimplePublicObjectId(
            properties=props_to_read,
            inputs=[SimplePublicObjectId(id=cid) for cid in chunk],
        )
        resp = client.crm.objects.batch_api.read(
            object_type=OBJECT_TYPE_CONTENEDOR,
            batch_read_input_simple_public_object_id=batch_input,
        )
        for obj in (resp.results or []):
            result[obj.id] = obj.properties

        logger.debug(
            f"  [batch_read] chunk {i // chunk_size + 1}: "
            f"solicitados={len(chunk)} devueltos={len(resp.results or [])}"
        )

    logger.info(
        f"  [batch_read] total leídos con propiedades: {len(result)}"
    )
    return result

def _parse_documentos_a_generar(cid: str, properties: dict) -> Optional[List[str]]:
    """Parsea la propiedad multi-select documentos_a_generar. HubSpot puede devolverla como string ';' o como lista."""
    raw = properties.get(CONTENEDOR_PROP_DOCUMENTOS_A_GENERAR)
    if not raw:
        logger.warning(
            f"  [parse] id={cid} NO tiene '{CONTENEDOR_PROP_DOCUMENTOS_A_GENERAR}' "
            f"o está vacío → descartado"
        )
        return None

    if isinstance(raw, list):
        parsed = [t.strip() for t in raw if t.strip()]
    else:
        parsed = [t.strip() for t in str(raw).split(";") if t.strip()]

    if not parsed:
        logger.warning(
            f"  [parse] id={cid} raw={raw!r} → vacío tras parse → descartado"
        )
        return None

    logger.debug(f"  [parse] id={cid} raw={raw!r} → {parsed}")
    return parsed

def _is_doc_type_required(doc_type: str, parsed_documentos: Optional[List[str]]) -> bool:
    """Determina si un doc_type es requerido según documentos_a_generar parseado."""
    if not parsed_documentos:
        return False
    hs_value = DOC_TYPE_TO_HUBSPOT_FILTER.get(doc_type)
    return hs_value is not None and hs_value in parsed_documentos

def _is_doc_generated(doc_type: str, properties: dict) -> bool:
    """True si la propiedad archivo del doc_type tiene valor. No usa group_generation_id."""
    file_prop = DOC_TYPE_TO_FILE_PROPERTY.get(doc_type)
    if not file_prop:
        return False
    return bool(properties.get(file_prop))

def _filter_by_generated_docs(contenedores: dict, tipos: List[str]) -> tuple:
    """Mantiene solo contenedores que tienen al menos un doc generado en los tipos dados."""
    filtered: dict = {}
    discarded = 0

    for cid, props in contenedores.items():
        tiene_alguno = False
        for tipo in tipos:
            file_prop = DOC_TYPE_TO_FILE_PROPERTY.get(tipo)
            if not file_prop:
                continue
            if props.get(file_prop):
                tiene_alguno = True
                break

        if tiene_alguno:
            filtered[cid] = props
            logger.debug(
                f"  [generated] id={cid} → INCLUIDO (al menos un doc generado)"
            )
        else:
            discarded += 1
            logger.debug(
                f"  [generated] id={cid} → DESCARTADO (ningún doc generado)"
            )

    return filtered, discarded

async def get_pending_containers(request: PendingRequest) -> PendingResponse:
    """Devuelve contenedores con documentos pendientes según los filtros del request."""
    filtros = request.filtros
    company_id = (filtros.company_id or "").strip()
    empresa = (filtros.empresa or "").strip()
    tipos = filtros.tipos_documento or []

    if not company_id and not empresa:
        logger.warning("[pending_containers] company_id/empresa requerido pero vacío")
        return PendingResponse(
            success=False,
            error="Falta la empresa del contexto (company_id).",
        )

    if not tipos:
        logger.warning("[pending_containers] tipos_documento requerido pero vacío")
        return PendingResponse(
            success=False,
            error="El filtro 'tipos_documento' es obligatorio.",
        )

    logger.info(
        f"[pending_containers] filtros normalizados: "
        f"company_id={company_id!r} empresa={empresa!r} tipos={tipos}"
    )

    try:
        client = hubspot_client.get_client()

        company_ids = _resolve_company_ids(client, company_id, empresa)

        logger.info(
            f"[pending_containers]{len(company_ids)} empresa(s) "
            f"→ sample={company_ids[:3]}"
        )

        if not company_ids:
            logger.info(
                f"[pending_containers] sin empresas (company_id={company_id!r} "
                f"empresa={empresa!r}) → respuesta vacía"
            )
            return PendingResponse(success=True, contenedores=[], total=0)

        contenedor_to_company = _get_contenedores_for_companies(client, company_ids)
        contenedor_ids_set = set(contenedor_to_company.keys())

        logger.info(
            f"[pending_containers]{len(contenedor_ids_set)} contenedor(es) "
            f"pre-filtros → sample={list(contenedor_ids_set)[:3]}"
        )

        if not contenedor_ids_set:
            logger.info(
                "[pending_containers] ninguna empresa tiene contenedores "
                "asociados → respuesta vacía"
            )
            return PendingResponse(success=True, contenedores=[], total=0)

        contenedores_data = _batch_read_contenedores(
            client, list(contenedor_ids_set)
        )
        logger.info(
            f"[pending_containers]{len(contenedores_data)} contenedores "
            f"leídos con propiedades"
        )

        for cid, props in contenedores_data.items():
            file_vals = " ".join(
                f"{p}={props.get(p)!r}" for p in sorted(ALL_CONTENEDOR_FILE_PROPERTY_NAMES)
            )
            logger.info(
                f"[pending_containers][prefiltro] "
                f"id={cid} "
                f"name={props.get('nombre')!r} "
                f"etd={props.get(CONTENEDOR_PROP_ETD)!r} "
                f"eta={props.get(CONTENEDOR_PROP_ETA)!r} "
                f"documentos_a_generar={props.get(CONTENEDOR_PROP_DOCUMENTOS_A_GENERAR)!r} "
                f"{file_vals}"
            )

        mapped_tipos = list({DOC_TYPE_TO_HUBSPOT_FILTER.get(t, t) for t in tipos})
        logger.info(
            f"[pending_containers] tipos_solicitados={tipos} "
            f"→ hubspot_filter_values={mapped_tipos}"
        )

        filtered: dict = {}
        parsed_docs_by_cid: dict = {}
        discarded_step4 = 0
        sample_logged = 0

        for cid, props in contenedores_data.items():
            parsed_tipos = _parse_documentos_a_generar(cid, props)

            has_required_pending = False
            for t in tipos:
                if _is_doc_type_required(t, parsed_tipos) and not _is_doc_generated(t, props):
                    has_required_pending = True
                    break

            if sample_logged < 3:
                logger.info(
                    f"[pending_containers][sample] id={cid} "
                    f"documentos_a_generar_parsed={parsed_tipos} "
                    f"has_required_pending={has_required_pending}"
                )
                sample_logged += 1

            if has_required_pending:
                filtered[cid] = props
                parsed_docs_by_cid[cid] = parsed_tipos
            else:
                discarded_step4 += 1

        logger.info(
            f"[pending_containers] post-filtro: {len(filtered)} "
            f"({discarded_step4} descartados)"
        )

        if not filtered:
            return PendingResponse(success=True, contenedores=[], total=0)

        deal_info = _get_deal_info_for_containers(client, list(filtered.keys()))
        contenedores: List[ContenedorListItem] = [
            _map_to_list_item(
                cid, props,
                deal_id=deal_info.get(cid, ("", "", {}))[0] or None,
                deal_name=deal_info.get(cid, ("", "", {}))[1] or None,
                deal_properties=deal_info.get(cid, ("", "", {}))[2] or None,
                parsed_documentos_a_generar=parsed_docs_by_cid.get(cid),
            )
            for cid, props in filtered.items()
        ]

        logger.info(
            f"[pending_containers] total_final={len(contenedores)}"
        )
        return PendingResponse(
            success=True,
            contenedores=contenedores,
            total=len(contenedores),
        )

    except Exception as e:
        logger.error(f"[pending_containers] ERROR inesperado: {e}", exc_info=True)
        return PendingResponse(success=False, error=str(e))

def _get_contenedores_for_generate(client, container_ids: List[str]) -> dict:
    """Batch read de contenedores para generación de PDFs, preservando el orden de container_ids. Lanza ValueError si algún ID no existe."""
    logger.info(
        f"solicitados={len(container_ids)} ids={container_ids}"
    )

    raw: dict = {}
    chunk_size = 100
    for i in range(0, len(container_ids), chunk_size):
        chunk = container_ids[i : i + chunk_size]
        batch_input = BatchReadInputSimplePublicObjectId(
            properties=CONTENEDOR_GENERATE_PROPERTIES,
            inputs=[SimplePublicObjectId(id=cid) for cid in chunk],
        )
        resp = client.crm.objects.batch_api.read(
            object_type=OBJECT_TYPE_CONTENEDOR,
            batch_read_input_simple_public_object_id=batch_input,
        )
        for obj in (resp.results or []):
            raw[obj.id] = obj.properties

    missing = [cid for cid in container_ids if cid not in raw]
    if missing:
        raise ValueError(
            f"contenedores no encontrados en HubSpot: {missing}"
        )

    ordered = {cid: raw[cid] for cid in container_ids}
    logger.info(f"OK → {len(ordered)} contenedores leídos")
    return ordered

def _get_deal_for_contenedores(client, container_ids: List[str]) -> tuple:
    """Obtiene el Deal asociado a los contenedores. Lanza ValueError si algún contenedor no tiene Deal."""
    logger.info(f"resolviendo deal para {len(container_ids)} contenedores")

    t = time.monotonic()
    contenedor_to_deals = batch_read_associations(
        client, OBJECT_TYPE_CONTENEDOR, OBJECT_TYPE_DEAL, container_ids,
    )
    logger.info(f"[TIMER] _get_deal_for_contenedores.batch_assoc: {time.monotonic() - t:.2f}s")

    sin_deal: List[str] = [cid for cid in container_ids if not contenedor_to_deals.get(cid)]
    if sin_deal:
        raise ValueError(f"contenedores sin Deal asociado: {sin_deal}")

    deal_id_per_container = {
        cid: contenedor_to_deals[cid][0] for cid in container_ids
    }
    unique_deals = set(deal_id_per_container.values())
    if len(unique_deals) != 1:
        logger.warning(
            f"contenedores pertenecen a {len(unique_deals)} "
            f"deals distintos: {unique_deals}. Usando el primero para consignee/puerto_destino."
        )

    deal_id = next(iter(unique_deals))
    logger.info(f"deal_id={deal_id!r} — leyendo propiedades")

    t = time.monotonic()
    deals_by_id = batch_read_objects(
        client, OBJECT_TYPE_DEAL, [deal_id], list(DEAL_GENERATE_PROPERTIES),
    )
    deal_props = deals_by_id.get(deal_id) or {}
    logger.info(
        f"[TIMER] _get_deal_for_contenedores.batch_read_deal: {time.monotonic() - t:.2f}s "
        f"consignee={'presente' if deal_props.get('consignee') else 'ausente'}"
    )
    return deal_id, deal_props

async def generate_documents(request: GenerateRequest) -> GenerateResponse:
    """Genera 1–3 documentos para un grupo de contenedores. Todos los contenedores deben pertenecer al mismo Deal."""
    logger.info(
        f"container_ids={request.container_ids} doc_types={request.doc_types}"
    )

    client = hubspot_client.get_client()

    try:
        containers = _get_contenedores_for_generate(client, request.container_ids)

        for cid, props in containers.items():
            parsed_docs = _parse_documentos_a_generar(cid, props)
            nombre = props.get("nombre", cid)
            for dt in request.doc_types:
                if not _is_doc_type_required(dt, parsed_docs):
                    label = DOC_TYPE_LABELS_ES.get(dt, dt)
                    return GenerateResponse(
                        success=False,
                        error=f"El contenedor '{nombre}' no requiere el documento "
                              f"'{label}'. "
                              f"Revisa la selección de contenedores y tipos de documento.",
                    )
                if _is_doc_generated(dt, props):
                    label = DOC_TYPE_LABELS_ES.get(dt, dt)
                    return GenerateResponse(
                        success=False,
                        error=f"El contenedor '{nombre}' ya tiene generado el documento "
                              f"'{label}'. "
                              f"Realiza rollback antes de regenerar.",
                    )

        _, deal_props = _get_deal_for_contenedores(client, request.container_ids)

        formato_labels: dict = {}
        if DOC_TYPE_SANITARIO in set(request.doc_types):
            deal_props = dict(deal_props)
            deal_props["puerto_destino"] = resolve_enum_label(
                client, "deals", "puerto_destino", deal_props.get("puerto_destino", "")
            )
            formato_labels = get_formato_label_map(request.idioma)

        elementos_by_container = get_elementos_fabricante_por_contenedor(
            client, request.container_ids
        )

        origen_types = {DOC_TYPE_ORIGEN_BORRADOR, DOC_TYPE_ORIGEN_FINAL}
        if origen_types & set(request.doc_types):
            if not request.descripcion_mercancia or not request.descripcion_mercancia.strip():
                raise ValueError(
                    "El campo descripcion_mercancia es obligatorio para certificados de origen."
                )

        documents_data: dict = {}
        group_generation_ids: dict = {}
        generated_docs: list = []
        affected_containers_set: set = set()

        for doc_type in request.doc_types:
            group_id = str(uuid.uuid4())
            group_generation_ids[doc_type] = group_id

            if doc_type in (DOC_TYPE_ORIGEN_BORRADOR, DOC_TYPE_ORIGEN_FINAL):
                logger.info(f"doc_type={doc_type!r}")
                payload = build_origen_payload(
                    request.container_ids,
                    containers,
                    deal_props,
                    elementos_by_container,
                    descripcion_mercancia=request.descripcion_mercancia,
                    observaciones=request.observaciones or "",
                    idioma=request.idioma,
                )
            elif doc_type == DOC_TYPE_SANITARIO:
                logger.info("")
                payload = build_sanitario_payload(
                    request.container_ids,
                    containers,
                    deal_props,
                    elementos_by_container,
                    settings,
                    idioma=request.idioma,
                    formato_labels=formato_labels,
                )
            else:
                logger.warning(f"doc_type desconocido ignorado: {doc_type!r}")
                continue

            documents_data[doc_type] = payload

            if doc_type == DOC_TYPE_ORIGEN_BORRADOR:
                logger.info(f"doc_type={doc_type!r} group_id={group_id}")

                pdf_bytes = render_origen_borrador_v2(payload, debug=settings.pdf_debug_layout)
                logger.info(f"[PDF_READY] size={len(pdf_bytes)} bytes")

                filename = f"origen_borrador_{group_id[:8]}.pdf"
                upload_result = upload_pdf(pdf_bytes, filename)
                logger.info(
                    f"[FILE_UPLOADED] file_id={upload_result.file_id} "
                    f"url={upload_result.file_url!r}"
                )

                update_props = {
                    "certificado_origen_borrador": upload_result.file_id,
                    "doc_group_id_origen_borrador": group_id,
                }
                update_result = _batch_update_contenedores(
                    client, request.container_ids, update_props
                )
                logger.info(
                    f"[CONTAINERS_PATCHED] updated={update_result['updated']} "
                    f"failed={update_result['failed']} "
                    f"sample={request.container_ids[:3]}"
                )

                generated_docs.append(GeneratedDocResult(
                    doc_type=doc_type,
                    file_id=upload_result.file_id,
                    file_url=upload_result.file_url,
                    group_generation_id=group_id,
                ))
                affected_containers_set.update(request.container_ids)

            elif doc_type == DOC_TYPE_ORIGEN_FINAL:
                logger.info(f"doc_type={doc_type!r} group_id={group_id}")
                logger.info(
                    f"[PDF_RENDER_MODE] debug={settings.pdf_debug_layout}"
                )
                pdf_bytes = render_origen_final_v2(payload, debug=settings.pdf_debug_layout)
                logger.info(f"[PDF_READY] size={len(pdf_bytes)} bytes")

                filename = f"origen_validado_{group_id[:8]}.pdf"
                upload_result = upload_pdf(pdf_bytes, filename)
                logger.info(
                    f"[FILE_UPLOADED] file_id={upload_result.file_id} "
                    f"url={upload_result.file_url!r}"
                )

                merged_value = _merge_file_in_prop(
                    client, request.container_ids[0],
                    "certificado_origen", "origen_validado_", upload_result.file_id,
                )
                update_props = {
                    "certificado_origen": merged_value,
                    "doc_group_id_origen_final": group_id,
                }
                update_result = _batch_update_contenedores(
                    client, request.container_ids, update_props
                )
                logger.info(
                    f"[CONTAINERS_PATCHED] updated={update_result['updated']} "
                    f"failed={update_result['failed']} "
                    f"sample={request.container_ids[:3]}"
                )

                generated_docs.append(GeneratedDocResult(
                    doc_type=doc_type,
                    file_id=upload_result.file_id,
                    file_url=upload_result.file_url,
                    group_generation_id=group_id,
                ))
                affected_containers_set.update(request.container_ids)

            elif doc_type == DOC_TYPE_SANITARIO:
                logger.info(f"doc_type={doc_type!r} group_id={group_id}")
                logger.info(f"[PDF_RENDER_MODE] debug={settings.pdf_debug_layout}")
                pdf_bytes = render_sanitario_v2(payload, debug=settings.pdf_debug_layout)
                logger.info(f"[PDF_READY] size={len(pdf_bytes)} bytes")

                filename = f"sanitario_borrador_{group_id[:8]}.pdf"
                upload_result = upload_pdf(pdf_bytes, filename)
                logger.info(
                    f"[FILE_UPLOADED] file_id={upload_result.file_id} "
                    f"url={upload_result.file_url!r}"
                )

                merged_value = _merge_file_in_prop(
                    client, request.container_ids[0],
                    "certificado_sanitario", "sanitario_borrador_", upload_result.file_id,
                )
                update_props = {
                    "certificado_sanitario":  merged_value,
                    "doc_group_id_sanitario": group_id,
                }
                update_result = _batch_update_contenedores(
                    client, request.container_ids, update_props
                )
                logger.info(
                    f"[CONTAINERS_PATCHED] updated={update_result['updated']} "
                    f"failed={update_result['failed']} "
                    f"sample={request.container_ids[:3]}"
                )

                generated_docs.append(GeneratedDocResult(
                    doc_type=doc_type,
                    file_id=upload_result.file_id,
                    file_url=upload_result.file_url,
                    group_generation_id=group_id,
                ))
                affected_containers_set.update(request.container_ids)

            else:
                logger.info(
                    f"doc_type={doc_type!r} → "
                    "PDF generation not yet implemented; skipping upload/persist"
                )

        logger.info(
            f"doc_types_built={list(documents_data.keys())} "
            f"generated_pdfs={[d.doc_type for d in generated_docs]} "
            f"group_ids={group_generation_ids}"
        )
        return GenerateResponse(
            success=True,
            documents_data=documents_data,
            group_generation_ids=group_generation_ids,
            generated_docs=generated_docs,
            affected_containers=list(affected_containers_set),
        )

    except ValueError as e:
        logger.warning(f"[generate_documents] error de validación: {e}")
        return GenerateResponse(success=False, error=str(e))
    except Exception as e:
        logger.error(f"[generate_documents] ERROR inesperado: {e}", exc_info=True)
        return GenerateResponse(success=False, error=str(e))

async def get_generated_containers(request: GeneratedRequest) -> GeneratedResponse:
    """Devuelve contenedores con al menos un tipo de doc generado (Tab 2)."""
    filtros = request.filtros
    company_id = (filtros.company_id or "").strip()
    empresa = (filtros.empresa or "").strip()
    tipos = filtros.tipos_documento or ALL_DOC_TYPES

    logger.info(
        f"[get_generated_containers] START "
        f"deal_id={request.deal_id!r} "
        f"company_id={company_id!r} "
        f"empresa={empresa!r} "
        f"tipos_documento={tipos}"
    )

    if not company_id and not empresa:
        logger.warning("[get_generated_containers] company_id/empresa requerido pero vacío")
        return GeneratedResponse(
            success=False,
            error="Falta la empresa del contexto (company_id).",
        )

    try:
        client = hubspot_client.get_client()

        company_ids = _resolve_company_ids(client, company_id, empresa)

        if not company_ids:
            return GeneratedResponse(success=True, contenedores=[], total=0)

        contenedor_to_company = _get_contenedores_for_companies(client, company_ids)
        contenedor_ids_set = set(contenedor_to_company.keys())

        if not contenedor_ids_set:
            return GeneratedResponse(success=True, contenedores=[], total=0)

        contenedores_data = _batch_read_contenedores(
            client, list(contenedor_ids_set)
        )

        filtered, discarded = _filter_by_generated_docs(contenedores_data, tipos)
        logger.info(
            f"[get_generated_containers] post-generated: {len(filtered)} "
            f"({discarded} descartados por no tener ninguno generado)"
        )

        if not filtered:
            return GeneratedResponse(success=True, contenedores=[], total=0)

        deal_info = _get_deal_info_for_containers(client, list(filtered.keys()))
        contenedores = [
            _map_to_list_item(
                cid, props,
                deal_id=deal_info.get(cid, ("", "", {}))[0] or None,
                deal_name=deal_info.get(cid, ("", "", {}))[1] or None,
                deal_properties=deal_info.get(cid, ("", "", {}))[2] or None,
            )
            for cid, props in filtered.items()
        ]

        logger.info(f"[get_generated_containers] END → {len(contenedores)} con docs generados")
        return GeneratedResponse(
            success=True,
            contenedores=contenedores,
            total=len(contenedores),
        )

    except Exception as e:
        logger.error(f"[get_generated_containers] ERROR: {e}", exc_info=True)
        return GeneratedResponse(success=False, error=str(e))

ROLLBACK_INTERNAL_DOC_TYPE_TO_PREFIX = {
    DOC_TYPE_ORIGEN_BORRADOR: "origen_borrador_",
    DOC_TYPE_ORIGEN_FINAL:    "origen_validado_",
    DOC_TYPE_SANITARIO:       "sanitario_borrador_",
}

ROLLBACK_MULTI_FILE_PROPS = {"certificado_origen", "certificado_sanitario"}


def _compute_rollback_file_value(current_raw: str, internal_doc_type: str) -> Tuple[str, List[str]]:
    """Devuelve (new_serialized, file_ids_to_delete) para rollback. Multi-file conserva archivos sin el prefix del doc_type; single-file limpia todo."""
    file_prop_name = DOC_TYPE_TO_FILE_PROPERTY[internal_doc_type]
    if file_prop_name not in ROLLBACK_MULTI_FILE_PROPS:
        return "", parse_file_ids(current_raw) if current_raw else []
    prefix = ROLLBACK_INTERNAL_DOC_TYPE_TO_PREFIX[internal_doc_type]
    current_ids = parse_file_ids(current_raw)
    kept_ids: List[str] = []
    to_delete: List[str] = []
    for fid in current_ids:
        meta = fetch_file_metadata(fid)
        if meta and meta.name.startswith(prefix):
            to_delete.append(fid)
        else:
            kept_ids.append(fid)
    return serialize_file_ids(kept_ids), to_delete


async def rollback_document(request: RollbackRequest) -> RollbackResponse:
    """Borra el archivo del File Manager y limpia/preserva propiedades del tipo de documento en todos los contenedores del grupo. En props multi-file solo se borran los archivos cuyo nombre empieza con el prefix del doc_type."""
    contenedor_nombre = request.contenedor_nombre
    doc_type_api = request.doc_type
    internal_doc_type = ROLLBACK_API_TO_INTERNAL_DOC_TYPE[doc_type_api]
    group_prop_name = CONTENEDOR_DOC_PROPERTIES[internal_doc_type]["group_generation_id"]
    file_prop_name = DOC_TYPE_TO_FILE_PROPERTY[internal_doc_type]
    is_multi_file = file_prop_name in ROLLBACK_MULTI_FILE_PROPS

    logger.info(
        f"[ROLLBACK] input: contenedor_nombre={contenedor_nombre!r} "
        f"doc_type={doc_type_api!r} internal={internal_doc_type!r} "
        f"group_prop={group_prop_name!r} file_prop={file_prop_name!r}"
    )

    client = hubspot_client.get_client()

    props_to_clear = _clear_doc_properties(internal_doc_type)
    props_to_clear[file_prop_name] = ""

    try:
        frontend_group_id = (request.group_id or "").strip() or None
        if frontend_group_id:
            logger.info(
                f"[ROLLBACK] group_id desde frontend: {frontend_group_id!r} "
                f"— saltando búsqueda por nombre"
            )
            group_id_value: Optional[str] = frontend_group_id
        else:
            search_props = ["nombre", group_prop_name, file_prop_name]
            found = _search_contenedor_by_nombre(client, contenedor_nombre, search_props)
            found_count = len(found)

            logger.info(
                f"[ROLLBACK] contenedor resuelto: "
                f"found_count={found_count} "
                f"container_id={repr(list(found.keys())[0]) if found_count == 1 else 'N/A'} "
                f"nombre={contenedor_nombre!r}"
            )

            if found_count == 0:
                return RollbackResponse(
                    success=True,
                    affected_containers_count=0,
                    message="Contenedor no encontrado",
                )

            if found_count > 1:
                return RollbackResponse(
                    success=False,
                    error=f"Nombre de contenedor no es único: {found_count} coincidencias",
                    message="Nombre de contenedor no es único",
                )

            anchor_id, anchor_props = next(iter(found.items()))

            raw_group = anchor_props.get(group_prop_name)
            raw_file = anchor_props.get(file_prop_name)
            group_id_value = raw_group if raw_group else None
            has_file = bool(raw_file)

            logger.info(
                f"[ROLLBACK] props resueltas: container_id={anchor_id!r} "
                f"group_prop={group_prop_name!r} group_id_value={group_id_value!r} "
                f"file_prop={file_prop_name!r} has_file={has_file}"
            )

            if not group_id_value:
                if has_file:
                    logger.info(
                        f"[ROLLBACK] group_id_empty=True has_file=True "
                        f"action=single_container_rollback container_id={anchor_id!r}"
                    )
                    new_value, to_delete = _compute_rollback_file_value(raw_file, internal_doc_type)
                    for fid in to_delete:
                        try:
                            delete_file(fid)
                        except Exception as e:
                            logger.warning(
                                f"[ROLLBACK] delete_file falló para file_id={fid!r}: {e}. "
                                f"Continuando con clear de propiedades."
                            )
                    props_single = dict(props_to_clear)
                    if is_multi_file:
                        props_single[file_prop_name] = new_value
                    result = _batch_update_contenedores(client, [anchor_id], props_single)
                    logger.info(
                        f"[ROLLBACK] batch update: requested_count=1 "
                        f"updated_count={result['updated']} failed_count={len(result['failed'])} "
                        f"sample_failed_ids={result['failed'][:3]}"
                    )
                    logger.info(
                        f"[ROLLBACK] end summary: doc_type={doc_type_api!r} "
                        f"affected_containers_count={result['updated']}"
                    )
                    return RollbackResponse(
                        success=True,
                        affected_containers_count=result["updated"],
                        affected_container_names=[anchor_props.get("nombre", anchor_id)],
                        message=f"Rollback aplicado a 1 contenedor para doc_type={doc_type_api}",
                    )
                else:
                    logger.info(
                        f"[ROLLBACK] group_id_empty=True has_file=False "
                        f"action=noop container_id={anchor_id!r}"
                    )
                    return RollbackResponse(
                        success=True,
                        affected_containers_count=0,
                        message="No hay documento generado para rollback",
                    )

        group_containers = _search_contenedores_by_group_prop(
            client, group_prop_name, group_id_value, props=["nombre", file_prop_name]
        )
        group_count = len(group_containers)
        sample_ids = list(group_containers.keys())[:3]

        logger.info(
            f"[ROLLBACK] contenedores del grupo: "
            f"group_prop={group_prop_name!r} group_id_value={group_id_value!r} "
            f"count={group_count} sample_container_ids={sample_ids}"
        )

        if group_count == 0:
            logger.warning(
                f"[ROLLBACK] búsqueda por group_id devolvió 0 resultados "
                f"(posible race condition o ya limpiados) group_id={group_id_value!r}"
            )
            return RollbackResponse(
                success=True,
                affected_containers_count=0,
                message=(
                    f"No se encontraron contenedores con group_id={group_id_value!r} "
                    f"(ya limpiados o inconsistencia)"
                ),
            )

        all_ids = list(group_containers.keys())

        sample_raw = ""
        for props in group_containers.values():
            sample_raw = props.get(file_prop_name) or ""
            if sample_raw:
                break
        new_value, to_delete = _compute_rollback_file_value(sample_raw, internal_doc_type)
        logger.info(
            f"[ROLLBACK] file_ids a borrar: count={len(to_delete)} "
            f"sample={to_delete[:3]} multi_file={is_multi_file}"
        )
        for fid in to_delete:
            try:
                delete_file(fid)
            except Exception as e:
                logger.warning(
                    f"[ROLLBACK] delete_file falló para file_id={fid!r}: {e}. "
                    f"Continuando con clear de propiedades."
                )

        props_to_apply = dict(props_to_clear)
        if is_multi_file:
            props_to_apply[file_prop_name] = new_value

        result = _batch_update_contenedores(client, all_ids, props_to_apply)
        sample_failed = result["failed"][:3]

        logger.info(
            f"[ROLLBACK] batch update: requested_count={group_count} "
            f"updated_count={result['updated']} failed_count={len(result['failed'])} "
            f"sample_failed_ids={sample_failed}"
        )

        sample_names = [
            group_containers[cid].get("nombre", cid) for cid in all_ids[:3]
        ]
        message = (
            f"Rollback aplicado a {result['updated']} contenedores para doc_type={doc_type_api}"
        )
        if result["failed"]:
            message += f" ({len(result['failed'])} fallidos)"

        logger.info(
            f"[ROLLBACK] end summary: doc_type={doc_type_api!r} "
            f"affected_containers_count={result['updated']}"
        )

        return RollbackResponse(
            success=True,
            affected_containers_count=result["updated"],
            affected_container_names=sample_names,
            message=message,
        )

    except Exception as e:
        logger.error(f"[ROLLBACK] ERROR inesperado: {e}", exc_info=True)
        return RollbackResponse(success=False, error=str(e))


async def get_deal_context(deal_id: str) -> DealContextResponse:
    """Devuelve el contexto del deal (cotización padre) necesario para precarga
    en la card de Documentos. Hoy solo `preprints_language`; se puede ampliar
    sin romper compatibilidad."""
    client = hubspot_client.get_client()
    try:
        deal = client.crm.deals.basic_api.get_by_id(
            deal_id=deal_id,
            properties=["preprints_language"],
        )
    except Exception as e:
        logger.warning(f"[deal-context] deal={deal_id!r} no encontrado: {e}")
        return DealContextResponse(preprints_language=None)

    raw = ((deal.properties or {}).get("preprints_language") or "").strip().upper()
    if raw not in {"ES", "EN", "FR"}:
        return DealContextResponse(preprints_language=None)
    return DealContextResponse(preprints_language=raw)
