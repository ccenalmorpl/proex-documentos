from app.core.constants import (
    DOC_DEALSTAGE_CIERRE_PERDIDO,
    DOC_DEALSTAGE_CONFIRMADO,
    DOC_DEALSTAGE_EN_PROCESO,
    DOC_DEALSTAGE_ENVIADA,
    DOC_DEALSTAGE_PTE_CONFIRMAR,
    DOC_DEALSTAGE_RETIRADO,
)


def calcular_dealstage_documento(
    *,
    bl_borrador_ok: bool,
    certs_borrador_ok: bool,
    otros_obligatorios_ok: bool,
    certs_validado_ok: bool,
    bl_final_ok: bool,
    documentacion_recibida: bool,
    mercancia_retirada: bool,
    dealstage_actual: str = "",
) -> str:
    """Etapa del Negocio Documento a partir del estado de sus documentos.

    Recibe booleanos ya derivados (cada `_ok` incorpora que un documento no
    obligatorio no bloquea). La cadena es monótona: el resultado es el último
    escalón cuyas condiciones —y las de los anteriores— se cumplen; "En proceso"
    es el suelo y "Retirado" la etapa ganada. "Cierre perdido" es manual: si el
    deal ya está ahí, se respeta.
    """
    if dealstage_actual == DOC_DEALSTAGE_CIERRE_PERDIDO:
        return DOC_DEALSTAGE_CIERRE_PERDIDO

    cadena = [
        (DOC_DEALSTAGE_PTE_CONFIRMAR, bl_borrador_ok and certs_borrador_ok and otros_obligatorios_ok),
        (DOC_DEALSTAGE_CONFIRMADO, certs_validado_ok and bl_final_ok),
        (DOC_DEALSTAGE_ENVIADA, documentacion_recibida),
        (DOC_DEALSTAGE_RETIRADO, mercancia_retirada),
    ]

    etapa = DOC_DEALSTAGE_EN_PROCESO
    for stage_id, cumple in cadena:
        if not cumple:
            break
        etapa = stage_id
    return etapa
