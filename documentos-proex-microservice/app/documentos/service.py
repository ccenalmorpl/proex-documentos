"""Lógica de negocio del módulo documentos.

Cada función implementa uno de los 4 endpoints.
Los TODO marcan los pasos que requieren implementación de HubSpot/PDF.
"""

import logging
from typing import List

from app.documentos.schemas import (
    PendingRequest, PendingResponse, ContenedorListItem, DocInfo,
    GenerateRequest, GenerateResponse, GeneratedDocResult,
    GeneratedRequest, GeneratedResponse,
    RollbackRequest, RollbackResponse,
)
from app.core.constants import (
    OBJECT_TYPE_CONTENEDOR,
    CONTENEDOR_DOC_PROPERTIES,
    CONTENEDOR_ALL_PROPERTIES,
    ALL_DOC_TYPES,
)
from app.shared.hubspot_client import hubspot_client
from app.shared.utils import generate_group_id, utcnow_iso

logger = logging.getLogger(__name__)


# ── Helpers internos ────────────────────────────────────────────────────────

def _build_doc_info_for_container(properties: dict, doc_type: str) -> DocInfo:
    """Extrae el DocInfo de un tipo de documento desde las propiedades de un Contenedor."""
    props = CONTENEDOR_DOC_PROPERTIES[doc_type]
    return DocInfo(
        doc_type=doc_type,
        file_id=properties.get(props["file_id"]),
        file_url=properties.get(props["file_url"]),
        generated_at=properties.get(props["generated_at"]),
        group_generation_id=properties.get(props["group_generation_id"]),
    )


def _is_pending(properties: dict, doc_type: str) -> bool:
    """Devuelve True si el doc_type NO está generado en este contenedor."""
    props = CONTENEDOR_DOC_PROPERTIES[doc_type]
    return not properties.get(props["file_url"])


def _is_generated(properties: dict, doc_type: str) -> bool:
    """Devuelve True si el doc_type SÍ está generado en este contenedor."""
    return not _is_pending(properties, doc_type)


def _map_to_list_item(obj_id: str, properties: dict, doc_types: list) -> ContenedorListItem:
    """Convierte un objeto Contenedor de HubSpot en ContenedorListItem."""
    return ContenedorListItem(
        id=obj_id,
        name=properties.get("name", ""),
        nombre_cliente=properties.get("nombre_cliente"),
        fecha_carga=properties.get("fecha_carga"),
        fecha_cotizacion=properties.get("fecha_cotizacion"),
        docs=[_build_doc_info_for_container(properties, dt) for dt in doc_types],
    )


def _clear_doc_properties(doc_type: str) -> dict:
    """Devuelve un dict de propiedades con valores vacíos para limpiar un tipo de doc."""
    props = CONTENEDOR_DOC_PROPERTIES[doc_type]
    return {v: "" for v in props.values()}


# ── Endpoints ───────────────────────────────────────────────────────────────

async def get_pending_containers(request: PendingRequest) -> PendingResponse:
    """Devuelve contenedores asociados al Deal que tienen docs pendientes según filtros.

    Pasos:
    1. Obtener IDs de contenedores asociados al deal_id.
    2. Leer propiedades de cada contenedor (CONTENEDOR_ALL_PROPERTIES).
    3. Aplicar filtros (empresa, fechas).
    4. Para cada contenedor, determinar qué tipos están pendientes
       (según request.filtros.tipos_documento o todos si no se especifica).
    5. Devolver solo los que tienen al menos 1 tipo pendiente.
    """
    client = hubspot_client.get_client()
    filtros = request.filtros
    tipos = filtros.tipos_documento or ALL_DOC_TYPES

    try:
        # TODO: Paso 1 — obtener contenedores asociados al deal
        # Usar Associations API v4:
        # client.crm.associations.v4.basic_api.get_page(
        #     object_type="deals",
        #     object_id=request.deal_id,
        #     to_object_type=OBJECT_TYPE_CONTENEDOR,
        # )
        # container_ids = [r.to_object_id for r in response.results]

        # TODO: Paso 2 — leer propiedades de los contenedores
        # client.crm.objects.batch_api.read(
        #     batch_read_input_simple_public_object_id={
        #         "inputs": [{"id": cid} for cid in container_ids],
        #         "properties": CONTENEDOR_ALL_PROPERTIES,
        #     },
        #     object_type=OBJECT_TYPE_CONTENEDOR,
        # )

        # TODO: Paso 3 y 4 — filtrar y mapear
        # Aplicar filtros de empresa y fechas sobre las propiedades.
        # Conservar solo contenedores donde _is_pending(props, tipo) == True para ≥1 tipo.

        # TODO: Paso 5 — devolver lista
        contenedores: List[ContenedorListItem] = []
        return PendingResponse(success=True, contenedores=contenedores, total=len(contenedores))

    except Exception as e:
        logger.error(f"get_pending_containers error: {e}", exc_info=True)
        return PendingResponse(success=False, error=str(e))


async def generate_documents(request: GenerateRequest) -> GenerateResponse:
    """Genera PDFs para los tipos solicitados y los persiste en los contenedores.

    Pasos:
    1. Validar que los container_ids existen y están asociados al deal.
    2. Crear group_generation_id único.
    3. Para cada doc_type en request.doc_types:
       a. Recopilar datos necesarios (artículos, empresa, consignee, puertos, etc.).
       b. Generar PDF con la plantilla correspondiente.
       c. Subir PDF a HubSpot File Manager (shared/files.py).
       d. Persistir file_id, file_url, group_generation_id, generated_at
          en TODOS los contenedores del grupo.
    4. Devolver resumen de generación.
    """
    client = hubspot_client.get_client()
    group_id = generate_group_id()
    generated_docs: List[GeneratedDocResult] = []

    try:
        # TODO: Paso 1 — validar contenedores
        # Leer batch de contenedores y verificar asociación con deal_id.

        for doc_type in request.doc_types:
            # TODO: Paso 3a — recopilar datos para la plantilla
            # Los datos varían por tipo:
            # - origen_borrador / origen_final: artículos, sumatorios, totales
            # - sanitario: artículos únicos, cajas globales, peso neto global,
            #              país destino (HubDB), consignee, numero_contenedor,
            #              fecha primera factura, empresa+dirección (config)

            # TODO: Paso 3b — generar PDF
            # from app.documentos.templates import render_origen, render_sanitario
            # pdf_bytes = render_origen(data, draft=(doc_type == "origen_borrador"))
            # o pdf_bytes = render_sanitario(data)

            # TODO: Paso 3c — subir a File Manager
            # from app.shared.files import upload_pdf
            # filename = f"{doc_type}_{group_id[:8]}.pdf"
            # upload_result = upload_pdf(pdf_bytes, filename)

            # TODO: Paso 3d — persistir en cada contenedor del grupo
            # props_to_update = {
            #     CONTENEDOR_DOC_PROPERTIES[doc_type]["group_generation_id"]: group_id,
            #     CONTENEDOR_DOC_PROPERTIES[doc_type]["file_id"]: upload_result.file_id,
            #     CONTENEDOR_DOC_PROPERTIES[doc_type]["file_url"]: upload_result.file_url,
            #     CONTENEDOR_DOC_PROPERTIES[doc_type]["generated_at"]: utcnow_iso(),
            # }
            # client.crm.objects.batch_api.update(
            #     batch_input_simple_public_object_batch_input={
            #         "inputs": [{"id": cid, "properties": props_to_update}
            #                    for cid in request.container_ids]
            #     },
            #     object_type=OBJECT_TYPE_CONTENEDOR,
            # )

            pass  # Eliminar cuando esté implementado

        return GenerateResponse(
            success=True,
            group_generation_id=group_id,
            generated_docs=generated_docs,
            affected_containers=request.container_ids,
        )

    except Exception as e:
        logger.error(f"generate_documents error: {e}", exc_info=True)
        return GenerateResponse(success=False, error=str(e))


async def get_generated_containers(request: GeneratedRequest) -> GeneratedResponse:
    """Devuelve contenedores que tienen al menos un tipo de doc generado (Tab 2).

    Mismo flujo que get_pending_containers pero con _is_generated en lugar de _is_pending.
    """
    client = hubspot_client.get_client()
    filtros = request.filtros
    tipos = filtros.tipos_documento or ALL_DOC_TYPES

    try:
        # TODO: Mismo patrón que get_pending_containers pero filtrando _is_generated.
        # Ver comentarios en get_pending_containers para los pasos.

        contenedores: List[ContenedorListItem] = []
        return GeneratedResponse(success=True, contenedores=contenedores, total=len(contenedores))

    except Exception as e:
        logger.error(f"get_generated_containers error: {e}", exc_info=True)
        return GeneratedResponse(success=False, error=str(e))


async def rollback_document(request: RollbackRequest) -> RollbackResponse:
    """Borra el documento de un grupo y limpia propiedades en todos los contenedores.

    Pasos:
    1. Leer propiedades del contenedor ancla (container_id) para obtener group_generation_id.
    2. Si request.group_generation_id ya viene en el body, usarlo directamente (optimización).
    3. Buscar TODOS los contenedores con ese group_generation_id y ese doc_type.
    4. Para cada contenedor afectado:
       a. Obtener file_id del tipo de doc.
       b. Borrar archivo en File Manager (shared/files.py).
       c. Limpiar propiedades del tipo de doc en el contenedor.
    5. Responder con affected_containers_count.

    IMPORTANTE: Validación defensiva — si falta file_id en algún contenedor,
    responder con error claro y NO realizar borrados parciales.
    """
    client = hubspot_client.get_client()
    doc_type = request.doc_type
    props_map = CONTENEDOR_DOC_PROPERTIES.get(doc_type)

    if not props_map:
        return RollbackResponse(
            success=False,
            error=f"doc_type no válido: {doc_type}. Válidos: {list(CONTENEDOR_DOC_PROPERTIES.keys())}"
        )

    try:
        # TODO: Paso 1 — obtener group_generation_id del contenedor ancla
        # anchor = client.crm.objects.basic_api.get_by_id(
        #     object_id=request.container_id,
        #     object_type=OBJECT_TYPE_CONTENEDOR,
        #     properties=[props_map["group_generation_id"], props_map["file_id"]],
        # )
        # group_id = request.group_generation_id or anchor.properties.get(props_map["group_generation_id"])

        # TODO: Paso 3 — buscar todos los contenedores con ese group_generation_id
        # Usar Search API filtrando por la propiedad group_generation_id.

        # TODO: Paso 4 — validación defensiva
        # Verificar que TODOS tienen file_id antes de borrar ninguno.
        # Si alguno falta, retornar error sin tocar nada.

        # TODO: Paso 4a/4b/4c — borrar archivo y limpiar propiedades
        # from app.shared.files import delete_file
        # for cid, file_id in containers_to_rollback.items():
        #     delete_file(file_id)
        #     client.crm.objects.basic_api.update(
        #         object_id=cid,
        #         object_type=OBJECT_TYPE_CONTENEDOR,
        #         simple_public_object_input={"properties": _clear_doc_properties(doc_type)},
        #     )

        affected_ids: List[str] = []
        return RollbackResponse(
            success=True,
            affected_containers_count=len(affected_ids),
            affected_container_ids=affected_ids,
        )

    except Exception as e:
        logger.error(f"rollback_document error: {e}", exc_info=True)
        return RollbackResponse(success=False, error=str(e))
