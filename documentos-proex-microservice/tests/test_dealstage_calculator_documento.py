"""Calculador puro de etapa del Negocio Documento. Cadena monótona; "En proceso"
es el suelo; "Cierre perdido" intocable; documentacion_recibida no es override.
"""

from app.core.constants import (
    DOC_DEALSTAGE_CIERRE_PERDIDO,
    DOC_DEALSTAGE_CONFIRMADO,
    DOC_DEALSTAGE_EN_PROCESO,
    DOC_DEALSTAGE_ENVIADA,
    DOC_DEALSTAGE_PTE_CONFIRMAR,
    DOC_DEALSTAGE_RETIRADO,
)
from app.documento_deal.dealstage_calculator import calcular_dealstage_documento


def _calc(**kwargs):
    base = dict(
        bl_borrador_ok=False,
        certs_borrador_ok=False,
        otros_obligatorios_ok=False,
        certs_validado_ok=False,
        bl_final_ok=False,
        documentacion_recibida=False,
        mercancia_retirada=False,
    )
    base.update(kwargs)
    return calcular_dealstage_documento(**base)


def _cadena_completa(**kwargs):
    base = dict(
        bl_borrador_ok=True, certs_borrador_ok=True, otros_obligatorios_ok=True,
        certs_validado_ok=True, bl_final_ok=True, documentacion_recibida=True,
    )
    base.update(kwargs)
    return _calc(**base)


def test_en_proceso_por_defecto_sin_condicion_extra():
    # Nada subido y sin nada obligatorio cumplido → suelo de la cadena.
    assert _calc() == DOC_DEALSTAGE_EN_PROCESO
    # Aunque otros sub-pasos estén, si no se cumple Pte. confirmar se queda en proceso.
    assert _calc(certs_validado_ok=True, bl_final_ok=True) == DOC_DEALSTAGE_EN_PROCESO


def test_pte_confirmar():
    assert _calc(
        bl_borrador_ok=True, certs_borrador_ok=True, otros_obligatorios_ok=True,
    ) == DOC_DEALSTAGE_PTE_CONFIRMAR


def test_confirmado_requiere_pte_confirmar_y_validados_y_bl_final():
    assert _calc(
        bl_borrador_ok=True, certs_borrador_ok=True, otros_obligatorios_ok=True,
        certs_validado_ok=True, bl_final_ok=True,
    ) == DOC_DEALSTAGE_CONFIRMADO


def test_enviada_con_documentacion_recibida_y_pasos_previos():
    assert _calc(
        bl_borrador_ok=True, certs_borrador_ok=True, otros_obligatorios_ok=True,
        certs_validado_ok=True, bl_final_ok=True, documentacion_recibida=True,
    ) == DOC_DEALSTAGE_ENVIADA


def test_retirado_es_la_etapa_ganada():
    # Cadena completa + mercancía retirada por el cliente → Retirado (ganada).
    assert _cadena_completa(mercancia_retirada=True) == DOC_DEALSTAGE_RETIRADO


def test_retirado_no_es_override():
    # Retirada=True pero sin Enviada → no salta a Retirado (monótona estricta).
    assert _calc(mercancia_retirada=True) == DOC_DEALSTAGE_EN_PROCESO
    assert _calc(
        bl_borrador_ok=True, certs_borrador_ok=True, otros_obligatorios_ok=True,
        certs_validado_ok=True, bl_final_ok=True, mercancia_retirada=True,
    ) == DOC_DEALSTAGE_CONFIRMADO  # falta documentacion_recibida (Enviada)


def test_retroceso_al_desmarcar_mercancia_retirada():
    # En Retirado; al desmarcar el check de mercancía retirada retrocede a Enviada.
    assert _cadena_completa(mercancia_retirada=False) == DOC_DEALSTAGE_ENVIADA


def test_documentacion_recibida_no_es_override():
    # Recibida=True pero falta Pte. confirmar → se queda atrás (monótona estricta).
    assert _calc(documentacion_recibida=True) == DOC_DEALSTAGE_EN_PROCESO
    # Recibida=True con Pte. confirmar pero sin Confirmado → no salta a Enviada.
    assert _calc(
        bl_borrador_ok=True, certs_borrador_ok=True, otros_obligatorios_ok=True,
        documentacion_recibida=True,
    ) == DOC_DEALSTAGE_PTE_CONFIRMAR


def test_retroceso_al_borrar_bl_final():
    # En Enviada con todo cumplido; al "borrar" el BL final, bl_final_ok=False
    # retrocede a Pte. confirmar aunque documentacion_recibida siga true.
    nuevo = _calc(
        bl_borrador_ok=True, certs_borrador_ok=True, otros_obligatorios_ok=True,
        certs_validado_ok=True, bl_final_ok=False, documentacion_recibida=True,
    )
    assert nuevo == DOC_DEALSTAGE_PTE_CONFIRMAR


def test_cierre_perdido_intocable():
    # Sea cual sea la señal, si ya está en Cierre perdido se respeta.
    assert _calc(dealstage_actual=DOC_DEALSTAGE_CIERRE_PERDIDO) == DOC_DEALSTAGE_CIERRE_PERDIDO
    assert calcular_dealstage_documento(
        bl_borrador_ok=True, certs_borrador_ok=True, otros_obligatorios_ok=True,
        certs_validado_ok=True, bl_final_ok=True, documentacion_recibida=True,
        mercancia_retirada=True, dealstage_actual=DOC_DEALSTAGE_CIERRE_PERDIDO,
    ) == DOC_DEALSTAGE_CIERRE_PERDIDO


def test_flujo_camion_sin_bl_ni_certs_no_se_atasca():
    # En camión no hay BL ni certificados: sus *_ok llegan True (no obligatorios).
    # Si los otros obligatorios están subidos, avanza sin atascarse en En proceso.
    assert _calc(
        bl_borrador_ok=True, certs_borrador_ok=True, otros_obligatorios_ok=True,
    ) == DOC_DEALSTAGE_PTE_CONFIRMAR
