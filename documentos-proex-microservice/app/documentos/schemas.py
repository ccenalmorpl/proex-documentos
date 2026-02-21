"""Schemas Pydantic para el módulo documentos."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ── Health ─────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime


# ── Filtros (compartidos Tab 1 y Tab 2) ───────────────────────────────────

class FiltrosDocumentos(BaseModel):
    """Filtros SAP-like disponibles en ambos tabs."""
    empresa: Optional[str] = Field(None, description="Nombre o ID de la empresa (cliente)")
    fecha_carga_desde: Optional[str] = Field(None, description="Fecha carga contenedor - desde (YYYY-MM-DD)")
    fecha_carga_hasta: Optional[str] = Field(None, description="Fecha carga contenedor - hasta (YYYY-MM-DD)")
    fecha_cotizacion_desde: Optional[str] = Field(None, description="Fecha creación cotización - desde (YYYY-MM-DD)")
    fecha_cotizacion_hasta: Optional[str] = Field(None, description="Fecha creación cotización - hasta (YYYY-MM-DD)")
    tipos_documento: Optional[List[str]] = Field(
        None,
        description="Tipos de documento a filtrar: origen_borrador, origen_final, sanitario"
    )


# ── Contenedor en listados ─────────────────────────────────────────────────

class DocInfo(BaseModel):
    """Información de un documento generado para un tipo de cert."""
    doc_type: str
    file_id: Optional[str] = None
    file_url: Optional[str] = None
    generated_at: Optional[str] = None
    group_generation_id: Optional[str] = None


class ContenedorListItem(BaseModel):
    """Representación de un contenedor en los listados de Tab 1 y Tab 2."""
    id: str
    name: str
    nombre_cliente: Optional[str] = None
    fecha_carga: Optional[str] = None
    fecha_cotizacion: Optional[str] = None
    docs: List[DocInfo] = Field(default_factory=list, description="Estado de docs por tipo")


# ── POST /api/v1/documentos/pending ───────────────────────────────────────

class PendingRequest(BaseModel):
    """Solicitud para obtener contenedores con documentos pendientes."""
    deal_id: str = Field(..., description="ID del Deal en HubSpot")
    filtros: FiltrosDocumentos = Field(default_factory=FiltrosDocumentos)


class PendingResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    contenedores: List[ContenedorListItem] = Field(default_factory=list)
    total: int = 0


# ── POST /api/v1/documentos/generate ──────────────────────────────────────

class GenerateRequest(BaseModel):
    """Solicitud para generar 1–3 tipos de documento para un grupo de contenedores."""
    deal_id: str = Field(..., description="ID del Deal en HubSpot")
    container_ids: List[str] = Field(..., min_length=1, description="IDs de los contenedores del grupo")
    doc_types: List[str] = Field(
        ...,
        min_length=1,
        max_length=3,
        description="Tipos a generar: origen_borrador, origen_final, sanitario"
    )


class GeneratedDocResult(BaseModel):
    doc_type: str
    file_id: str
    file_url: str
    group_generation_id: str


class GenerateResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    group_generation_id: Optional[str] = None
    generated_docs: List[GeneratedDocResult] = Field(default_factory=list)
    affected_containers: List[str] = Field(default_factory=list)


# ── POST /api/v1/documentos/generated ─────────────────────────────────────

class GeneratedRequest(BaseModel):
    """Solicitud para obtener contenedores con documentos ya generados."""
    deal_id: str = Field(..., description="ID del Deal en HubSpot")
    filtros: FiltrosDocumentos = Field(default_factory=FiltrosDocumentos)


class GeneratedResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    contenedores: List[ContenedorListItem] = Field(default_factory=list)
    total: int = 0


# ── POST /api/v1/documentos/rollback ──────────────────────────────────────

class RollbackRequest(BaseModel):
    """Solicitud de rollback para un tipo de documento desde un contenedor ancla."""
    container_id: str = Field(..., description="ID del contenedor seleccionado en la tabla")
    doc_type: str = Field(..., description="Tipo de documento a borrar")
    group_generation_id: Optional[str] = Field(
        None,
        description="ID de grupo si la UI ya lo dispone (optimización)"
    )


class RollbackResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    affected_containers_count: int = 0
    affected_container_ids: List[str] = Field(default_factory=list)
