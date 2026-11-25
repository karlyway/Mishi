"""Servicio de metas de ahorro con fecha objetivo y cálculo real de cuotas (RF-10)."""

import math
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from finanzas.models import AporteMeta, MetaAhorro
from finanzas.services.finanzas_service import CERO, CENTAVO, formatear_cop
from finanzas.ui_helpers import MESES_CORTOS_ES, estilo_categoria


def _redondear_cop(valor):
    return Decimal(valor).quantize(CENTAVO, rounding=ROUND_HALF_UP)


def calcular_plan_meta(meta, perfil=None, hoy=None, limite_diario_ref=None):
    """Calcula faltante, avance y cuotas reales (diaria, semanal, quincenal, mensual) según fecha objetivo."""
    hoy = hoy or timezone.localdate()
    objetivo = meta.objetivo or CERO
    acumulado = meta.acumulado or CERO
    faltante = max(objetivo - acumulado, CERO)

    if objetivo > CERO:
        porcentaje = min(100, round(float((acumulado / objetivo) * Decimal('100'))))
    else:
        porcentaje = 0

    completada = faltante == CERO and objetivo > CERO
    fecha_obj = getattr(meta, 'fecha_objetivo', None)
    frec = (getattr(perfil, 'frecuencia', 'quincenal') or 'quincenal').lower()

    dias_restantes = None
    vencida = False
    proxima_vencer = False
    cuota_diaria = CERO
    cuota_semanal = CERO
    cuota_quincenal = CERO
    cuota_mensual = CERO
    cuota_ciclo = CERO
    etiqueta_ciclo = 'por quincena'
    resumen_cuota_lbl = ''
    exigente = False

    if completada:
        estado = 'completada'
        fecha_estimada_lbl = 'Meta completada'
    elif fecha_obj is not None:
        delta = (fecha_obj - hoy).days
        mes_txt = MESES_CORTOS_ES[fecha_obj.month - 1]
        fecha_corta = f'{fecha_obj.day} {mes_txt} {fecha_obj.year}'

        if delta <= 0:
            vencida = True
            dias_restantes = 0
            estado = 'vencida'
            cuota_diaria = faltante
            cuota_semanal = faltante
            cuota_quincenal = faltante
            cuota_mensual = faltante
            cuota_ciclo = faltante
            etiqueta_ciclo = 'pendiente'
            fecha_estimada_lbl = f'Vencida · {fecha_corta}'
            resumen_cuota_lbl = f'Faltan ${formatear_cop(faltante)} · Actualiza la fecha objetivo'
        else:
            dias_restantes = delta
            proxima_vencer = delta <= 7
            estado = 'proxima' if proxima_vencer else 'activa'
            cuota_diaria = _redondear_cop(faltante / Decimal(delta))
            semanas = max(1, math.ceil(delta / 7))
            quincenas = max(1, math.ceil(delta / 15))
            meses = max(1, math.ceil(delta / 30))
            cuota_semanal = _redondear_cop(faltante / Decimal(semanas))
            cuota_quincenal = _redondear_cop(faltante / Decimal(quincenas))
            cuota_mensual = _redondear_cop(faltante / Decimal(meses))

            mapa_ciclo = {
                'diario': (cuota_diaria, 'al día'),
                'semanal': (cuota_semanal, 'a la semana'),
                'quincenal': (cuota_quincenal, 'por quincena'),
                'mensual': (cuota_mensual, 'al mes'),
                'irregular': (cuota_diaria, 'al día'),
            }
            cuota_ciclo, etiqueta_ciclo = mapa_ciclo.get(frec, (cuota_quincenal, 'por quincena'))
            if limite_diario_ref is not None and limite_diario_ref > CERO:
                exigente = cuota_diaria > (limite_diario_ref * Decimal('0.50'))

            fecha_estimada_lbl = f'Objetivo: {fecha_corta} ({delta} d)'
            resumen_cuota_lbl = (
                f'Cuota: ${formatear_cop(cuota_diaria)}/día · '
                f'${formatear_cop(cuota_ciclo)} {etiqueta_ciclo}'
            )
    else:
        estado = 'sin_fecha'
        fecha_estimada_lbl = 'Sin fecha objetivo'
        resumen_cuota_lbl = 'Define una fecha objetivo para calcular tu cuota real.'

    return {
        'obj': meta,
        'idMeta': meta.idMeta,
        'nombre': meta.nombre,
        'categoria': meta.categoria,
        'objetivo': objetivo,
        'objetivo_fmt': formatear_cop(objetivo),
        'acumulado': acumulado,
        'acumulado_fmt': formatear_cop(acumulado),
        'faltante': faltante,
        'faltante_fmt': formatear_cop(faltante),
        'porcentaje': porcentaje,
        'completada': completada,
        'estado': estado,
        'fecha_objetivo': fecha_obj,
        'fecha_objetivo_iso': fecha_obj.isoformat() if fecha_obj else '',
        'dias_restantes': dias_restantes,
        'vencida': vencida,
        'proxima_vencer': proxima_vencer,
        'exigente': exigente,
        'cuota_diaria': cuota_diaria,
        'cuota_diaria_fmt': formatear_cop(cuota_diaria),
        'cuota_semanal': cuota_semanal,
        'cuota_semanal_fmt': formatear_cop(cuota_semanal),
        'cuota_quincenal': cuota_quincenal,
        'cuota_quincenal_fmt': formatear_cop(cuota_quincenal),
        'cuota_mensual': cuota_mensual,
        'cuota_mensual_fmt': formatear_cop(cuota_mensual),
        'cuota_ciclo': cuota_ciclo,
        'cuota_ciclo_fmt': formatear_cop(cuota_ciclo),
        'etiqueta_ciclo': etiqueta_ciclo,
        'fecha_estimada_lbl': fecha_estimada_lbl,
        'resumen_cuota_lbl': resumen_cuota_lbl,
        'ui': estilo_categoria(meta.categoria or meta.nombre),
    }


def enriquecer_metas_reales(metas_qs, perfil=None, hoy=None, limite_diario_ref=None):
    """Enriquece un queryset de MetaAhorro con fechas objetivo y cuotas reales."""
    hoy = hoy or timezone.localdate()
    return [
        calcular_plan_meta(m, perfil=perfil, hoy=hoy, limite_diario_ref=limite_diario_ref)
        for m in metas_qs
    ]


def crear_meta_usuario(perfil, nombre, categoria, objetivo, fecha_objetivo=None, hoy=None):
    """Crea una meta de ahorro con fecha objetivo opcional."""
    hoy = hoy or timezone.localdate()
    limpio = (nombre or '').strip()
    if not limpio:
        raise ValueError('Ingresa un nombre para la meta.')
    if fecha_objetivo is not None and fecha_objetivo < hoy:
        raise ValueError('La fecha objetivo debe ser hoy o una fecha futura.')

    return MetaAhorro.objects.create(
        idUsuario=perfil,
        nombre=limpio[:100],
        categoria=(categoria or 'General').strip()[:100] or 'General',
        objetivo=objetivo,
        fecha_objetivo=fecha_objetivo,
        creada_en=hoy,
    )


def registrar_aporte_meta(perfil, meta_id, monto, fecha=None, nota=''):
    """Registra un abono a una meta reservando dinero SIN duplicar un gasto en Transaccion."""
    hoy = fecha or timezone.localdate()
    if monto <= CERO:
        raise ValueError('El monto del abono debe ser mayor a cero.')

    with transaction.atomic():
        meta = MetaAhorro.objects.get(idMeta=meta_id, idUsuario=perfil)
        meta.acumulado = (meta.acumulado or CERO) + monto
        meta.save(update_fields=['acumulado'])
        aporte = AporteMeta.objects.create(
            idMeta=meta,
            idUsuario=perfil,
            monto=monto,
            fecha=hoy,
            nota=(nota or '').strip()[:120],
        )
    return meta, aporte


def actualizar_fecha_objetivo_meta(perfil, meta_id, fecha_objetivo):
    """Actualiza o limpia la fecha objetivo de una meta perteneciente al usuario."""
    meta = MetaAhorro.objects.get(idMeta=meta_id, idUsuario=perfil)
    meta.fecha_objetivo = fecha_objetivo
    meta.save(update_fields=['fecha_objetivo'])
    return meta
