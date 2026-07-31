from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime


class FiltrosDocumentos(BaseModel):
    company_id: Optional[str] = Field(
        None,
        description="ID de la empresa (Company) del contexto de la card. Cuando viene, "
                    "se filtra por esta empresa exacta y se ignora 'empresa'.",
    )
    empresa: Optional[str] = Field(None, description="Nombre o ID de la empresa (cliente). Legacy: búsqueda difusa por nombre.")
    tipos_documento: Optional[List[str]] = Field(
        None,
        description="Tipos de documento a filtrar: origen_borrador, origen_final, sanitario"
    )


class DocInfo(BaseModel):
    doc_type: str
    generated: bool = False
    required: bool = True
    group_id: Optional[str] = None
    file_url: Optional[str] = None


class ContenedorListItem(BaseModel):
    id: str
    name: str
    etd: Optional[str] = None
    eta: Optional[str] = None
    deal_id: Optional[str] = None
    deal_name: Optional[str] = None
    docs: List[DocInfo] = Field(default_factory=list, description="Estado de docs por tipo")
    deal_properties: Optional[dict] = Field(
        default=None,
        description="Propiedades del deal asociado al contenedor (certificado_origen_mercancia, observaciones)"
    )


class PendingRequest(BaseModel):
    deal_id: str = Field(..., description="ID del Deal en HubSpot")
    filtros: FiltrosDocumentos = Field(default_factory=FiltrosDocumentos)


class PendingResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    contenedores: List[ContenedorListItem] = Field(default_factory=list)
    total: int = 0


class GenerateRequest(BaseModel):
    """Genera 1–3 tipos de documento para un grupo de contenedores. Todos los contenedores deben pertenecer al mismo Deal."""
    container_ids: List[str] = Field(..., min_length=1, description="IDs de los contenedores del grupo")
    doc_types: List[str] = Field(
        ...,
        min_length=1,
        max_length=3,
        description="Tipos a generar: origen_borrador, origen_final, sanitario"
    )
    descripcion_mercancia: Optional[str] = Field(
        default=None,
        description="Override de descripción de mercancía para el certificado de origen (editable pre-generación)"
    )
    observaciones: Optional[str] = Field(
        default=None,
        description="Observaciones concatenadas de los deals de los contenedores seleccionados"
    )
    idioma: Literal["ES", "EN", "FR"] = Field(
        default="ES",
        description="Idioma para el certificado de origen: ES, EN, FR."
    )


class GeneratedDocResult(BaseModel):
    doc_type: str
    file_id: str
    file_url: str
    group_generation_id: str


class GenerateResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    documents_data: Optional[dict] = Field(
        default=None,
        description="Datos agregados por doc_type para rellenar los PDFs"
    )
    group_generation_ids: dict = Field(
        default_factory=dict,
        description="group_generation_id por doc_type: {doc_type: uuid}"
    )
    generated_docs: List[GeneratedDocResult] = Field(default_factory=list)
    affected_containers: List[str] = Field(default_factory=list)


class GeneratedRequest(BaseModel):
    deal_id: str = Field(..., description="ID del Deal en HubSpot")
    filtros: FiltrosDocumentos = Field(default_factory=FiltrosDocumentos)


class GeneratedResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    contenedores: List[ContenedorListItem] = Field(default_factory=list)
    total: int = 0


class RollbackRequest(BaseModel):
    contenedor_nombre: str = Field(
        ...,
        min_length=1,
        description="Nombre del contenedor seleccionado en la UI",
    )
    doc_type: Literal["origen_borrador", "origen", "sanitario"] = Field(
        ...,
        description="Tipo de documento a revertir",
    )
    group_id: Optional[str] = Field(
        None,
        description="group_id del doc_type ya conocido por la UI",
    )


class RollbackResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    affected_containers_count: int = 0
    affected_container_names: List[str] = Field(
        default_factory=list,
        description="Muestra de nombres de contenedores afectados (máx 3)",
    )
    message: str = ""


class DealContextResponse(BaseModel):
    preprints_language: Optional[Literal["ES", "EN", "FR"]] = Field(
        default=None,
        description="Idioma configurado en el deal cotización padre (ES | EN | FR). null si el deal no tiene valor.",
    )
