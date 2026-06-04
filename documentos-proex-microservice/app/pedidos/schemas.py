from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class PedidoCompanyResumen(BaseModel):
    numero_de_pedido: str
    numero_contenedores_pedido: int = 0
    nombre_cotizacion: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class PedidosListaResponse(BaseModel):
    success: bool = True
    error: Optional[str] = None
    pedidos_company: List[PedidoCompanyResumen] = Field(
        default_factory=list, alias="pedidosCompany"
    )

    model_config = ConfigDict(populate_by_name=True)


class SelectOption(BaseModel):
    label: str
    value: str


class BLArchivo(BaseModel):
    file_id: str
    name: str
    url: Optional[str] = None
    tipo: Literal["borrador", "final", "desconocido"]


class CertificadoArchivo(BaseModel):
    file_id: str
    name: str
    url: Optional[str] = None
    tipo: Literal["borrador", "validado", "sellado", "desconocido"]


class OtroDocArchivo(BaseModel):
    file_id: str
    name: str
    url: Optional[str] = None
    tipo: Literal[
        "dua", "arc", "eur1", "anexo_i", "inspeccion",
        "waiver_borrador", "waiver_final", "desconocido"
    ]


class ArchivoSimple(BaseModel):
    file_id: str
    name: str
    url: Optional[str] = None


class DealFile(BaseModel):
    file_id: Optional[str] = None
    name: Optional[str] = None
    url: Optional[str] = None


class PedidoInfo(BaseModel):
    etd: Optional[str] = None
    eta: Optional[str] = None
    consignee: Optional[str] = None
    notify: Optional[str] = None
    puerto_destino: Optional[str] = None
    puerto_salida: Optional[str] = None
    descripcion_mercancia: Optional[str] = None
    observaciones: Optional[str] = None
    fecha_de_entrega: Optional[str] = None
    lugar_carga: Optional[str] = None
    localidad_destino: Optional[str] = None
    direccion_de_entrega: Optional[str] = None
    datos_del_chofer: Optional[str] = None
    comentarios_logistica: Optional[str] = None
    bl_validado_logistica: bool = False
    bl_validado_administracion: bool = False
    bl_enviado_cliente: bool = False
    tipo_de_bl: Optional[str] = None
    bl_archivos: List[BLArchivo] = Field(default_factory=list)
    certificado_origen_validado: bool = False
    certificado_sanitario_validado: bool = False
    origen_archivos: List[CertificadoArchivo] = Field(default_factory=list)
    sanitario_archivos: List[CertificadoArchivo] = Field(default_factory=list)
    factura_pedido: Optional[DealFile] = None
    packing_list_pedido: Optional[DealFile] = None
    carta_porte_pedido: Optional[DealFile] = None
    fecha_de_facturacion_pedido: Optional[str] = None
    fecha_de_vencimiento_factura: Optional[str] = None


class ContenedorDetalleItem(BaseModel):
    id: str
    nombre: Optional[str] = None
    numero_contenedor: Optional[str] = None
    numero_precinto: Optional[str] = None
    peso_bruto: Optional[str] = None
    peso_neto: Optional[str] = None
    tara: Optional[str] = None
    vgm: Optional[str] = None
    etd: Optional[str] = None
    eta: Optional[str] = None
    tipo_contenedor: Optional[str] = None
    total_cajas: Optional[str] = None
    descripcion_mercancia_agregada: Optional[str] = None
    documentos_a_generar: List[str] = Field(default_factory=list)
    importe_pendiente_cobro: Optional[str] = None
    price: Optional[str] = None
    documentos_archivos: List[OtroDocArchivo] = Field(default_factory=list)
    otros_documentos: List[ArchivoSimple] = Field(default_factory=list)
    fotos_de_carga_archivos: List[ArchivoSimple] = Field(default_factory=list)
    enviar_por_mensajeria: bool = False
    permitir_enviar_documentacion: bool = False
    documentacion_recibida: bool = False
    mercancia_retirada: bool = False
    waiver_validado: bool = False
    fecha_llegada_contenedor: Optional[str] = None
    fecha_retirada_mercancia: Optional[str] = None


class EmpresaResumen(BaseModel):
    id: str
    name: Optional[str] = None
    tipo_cliente: Optional[str] = None


class PedidoDetalle(BaseModel):
    numero_de_pedido: str
    empresa: EmpresaResumen
    info: PedidoInfo = Field(default_factory=PedidoInfo)
    tipo_flujo: Optional[str] = None
    carga_por_palets: Optional[bool] = None
    fotos_de_carga: bool = False
    contenedores: List[ContenedorDetalleItem] = Field(default_factory=list)


class PedidoDetalleResponse(BaseModel):
    success: bool = True
    error: Optional[str] = None
    pedido: Optional[PedidoDetalle] = None
    select_options: Dict[str, List[SelectOption]] = Field(
        default_factory=dict, alias="selectOptions"
    )

    model_config = ConfigDict(populate_by_name=True)


class UpdatePedidoBLRequest(BaseModel):
    bl_validado_logistica: Optional[bool] = None
    bl_validado_administracion: Optional[bool] = None
    bl_enviado_cliente: Optional[bool] = None
    tipo_de_bl: Optional[str] = None


class UpdateContenedoresCertificadosRequest(BaseModel):
    certificado_origen_validado: Optional[bool] = None
    certificado_sanitario_validado: Optional[bool] = None


class UpdateContenedorEntregaRequest(BaseModel):
    enviar_por_mensajeria: Optional[bool] = None
    permitir_enviar_documentacion: Optional[bool] = None
    documentacion_recibida: Optional[bool] = None
    mercancia_retirada: Optional[bool] = None
    waiver_validado: Optional[bool] = None
    fecha_llegada_contenedor: Optional[str] = None
    fecha_retirada_mercancia: Optional[str] = None


class UpdatePedidoResponse(BaseModel):
    success: bool = True
    error: Optional[str] = None


class UploadFileResponse(BaseModel):
    success: bool = True
    error: Optional[str] = None
    error_code: Optional[str] = None
    file_id: Optional[str] = None
    file_name: Optional[str] = None
    file_url: Optional[str] = None
    tipo_documento: Optional[str] = None


class DeleteFileResponse(BaseModel):
    success: bool = True
    error: Optional[str] = None
