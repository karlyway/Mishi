"""Motor de notificaciones reales in-app de Mishi.

Genera y sincroniza notificaciones persistentes en BD a partir del estado
financiero real del usuario (sin datos ficticios ni alertas duplicadas).
"""

from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from finanzas.models import MetaAhorro, Notificacion, Prestamo
from finanzas.services.finanzas_service import (
    CERO,
    UMBRAL_HORMIGA_DEFECTO,
    calcular_resumen_financiero,
    formatear_cop,
)


def _registrar_o_actualizar(perfil, clave, tipo, nivel, titulo, mensaje, url_destino):
    """Crea la notificación si no existe para esa clave; si ya existe sin leer, actualiza su texto."""
    existente = Notificacion.objects.filter(idUsuario=perfil, clave=clave).first()
    if existente is None:
        return Notificacion.objects.create(
            idUsuario=perfil,
            clave=clave,
            tipo=tipo,
            nivel=nivel,
            titulo=titulo[:120],
            mensaje=mensaje[:280],
            url_destino=url_destino[:120],
            leida=False,
        )

    if not existente.leida and (existente.titulo != titulo[:120] or existente.mensaje != mensaje[:280]):
        existente.titulo = titulo[:120]
        existente.mensaje = mensaje[:280]
        existente.nivel = nivel
        existente.url_destino = url_destino[:120]
        existente.save(update_fields=['titulo', 'mensaje', 'nivel', 'url_destino'])
    return existente


def sincronizar_notificaciones_usuario(perfil, resumen=None, hoy=None):
    """Evalúa reglas financieras reales y persiste notificaciones deduplicadas en BD."""
    hoy = hoy or timezone.localdate()
    resumen = resumen or calcular_resumen_financiero(perfil, hoy=hoy)
    hoy_iso = hoy.isoformat()
    mes_tag = f'{hoy.year}_{hoy.month:02d}'

    # 1. Alertas de límite diario y saldo (respetan la preferencia alertas_activas del estudiante)
    if getattr(perfil, 'alertas_activas', True):
        dias = resumen['dias_restantes']
        dias_txt = f'{dias} día{"s" if dias != 1 else ""}'

        if resumen['saldo_cero_o_negativo']:
            _registrar_o_actualizar(
                perfil,
                clave=f'saldo_cero_{hoy_iso}',
                tipo='saldo_insuficiente',
                nivel='danger',
                titulo='Saldo insuficiente',
                mensaje=(
                    f"Tu saldo disponible está en ${resumen['saldo_fmt']} para los "
                    f'{dias_txt} restantes del ciclo.'
                ),
                url_destino='/app/insights/?tab=control',
            )
        elif resumen['alerta_saldo_insuficiente']:
            _registrar_o_actualizar(
                perfil,
                clave=f'saldo_ciclo_{hoy_iso}',
                tipo='saldo_insuficiente',
                nivel='warn',
                titulo='Saldo ajustado para tu ciclo',
                mensaje=(
                    f"Con tu límite diario de ${resumen['limite_diario_fmt']}, tu saldo "
                    f"(${resumen['saldo_fmt']}) no alcanza para los {dias_txt} restantes."
                ),
                url_destino='/app/presupuestos/',
            )

        if resumen['limite_superado']:
            _registrar_o_actualizar(
                perfil,
                clave=f'limite_superado_{hoy_iso}',
                tipo='limite_superado',
                nivel='danger',
                titulo='Límite diario superado',
                mensaje=(
                    f"Hoy registras ${resumen['gasto_hoy_fmt']} sobre tu límite diario de "
                    f"${resumen['limite_diario_fmt']} ({resumen['porcentaje_gasto_hoy']}%)."
                ),
                url_destino='/app/insights/?tab=control',
            )
        elif resumen['alerta_preventiva']:
            _registrar_o_actualizar(
                perfil,
                clave=f'limite_80_{hoy_iso}',
                tipo='alerta_80',
                nivel='warn',
                titulo=f"Límite diario al {resumen['porcentaje_gasto_hoy']}%",
                mensaje=(
                    f"Llevas ${resumen['gasto_hoy_fmt']} hoy. Te quedan "
                    f"${resumen['dinero_restante_hoy_fmt']} disponibles para el resto del día."
                ),
                url_destino='/app/insights/?tab=control',
            )

        # 2. Presupuesto mensual (80% preventivo o >100% superado)
        presupuesto = resumen.get('presupuesto')
        if presupuesto and presupuesto.limiteMensual > CERO:
            gastos_mes = resumen['gastos_mes']
            pct_mes = round(float((gastos_mes / presupuesto.limiteMensual) * Decimal('100')))
            if gastos_mes > presupuesto.limiteMensual:
                _registrar_o_actualizar(
                    perfil,
                    clave=f'presupuesto_mes_superado_{mes_tag}',
                    tipo='presupuesto_mensual',
                    nivel='danger',
                    titulo='Presupuesto mensual superado',
                    mensaje=(
                        f"Llevas ${resumen['gastos_mes_fmt']} gastados frente a tu tope mensual "
                        f"de ${formatear_cop(presupuesto.limiteMensual)} ({pct_mes}%)."
                    ),
                    url_destino='/app/presupuestos/',
                )
            elif pct_mes >= 80:
                _registrar_o_actualizar(
                    perfil,
                    clave=f'presupuesto_mes_80_{mes_tag}',
                    tipo='presupuesto_mensual',
                    nivel='warn',
                    titulo=f'Presupuesto mensual al {pct_mes}%',
                    mensaje=(
                        f"Has usado ${resumen['gastos_mes_fmt']} de tu límite mensual de "
                        f"${formatear_cop(presupuesto.limiteMensual)}."
                    ),
                    url_destino='/app/presupuestos/',
                )

    # 3. Gastos hormiga relevantes del mes (>= $20.000 y >= 30% del gasto mensual)
    gastos_mes_total = resumen['gastos_mes']
    if gastos_mes_total > CERO:
        inicio_mes = hoy.replace(day=1)
        hormiga_mes = (
            resumen['movimientos']
            .filter(
                tipo__iexact='gasto',
                fecha__gte=inicio_mes,
                fecha__lte=hoy,
                monto__lte=UMBRAL_HORMIGA_DEFECTO,
            )
            .aggregate(total=Sum('monto'))['total']
            or CERO
        )
        if hormiga_mes >= Decimal('20000.00') and (hormiga_mes / gastos_mes_total) >= Decimal('0.30'):
            pct_h = round(float((hormiga_mes / gastos_mes_total) * Decimal('100')))
            _registrar_o_actualizar(
                perfil,
                clave=f'hormiga_mes_{mes_tag}',
                tipo='hormiga',
                nivel='info',
                titulo='Ojo con tus gastos hormiga',
                mensaje=(
                    f'Este mes sumas ${formatear_cop(hormiga_mes)} ({pct_h}% de tus gastos) '
                    'en compras pequeñas de $15.000 o menos.'
                ),
                url_destino='/app/insights/?tab=control',
            )

    # 4. Metas de ahorro cumplidas al 100%
    for meta in MetaAhorro.objects.filter(idUsuario=perfil):
        if meta.objetivo > CERO and meta.acumulado >= meta.objetivo:
            _registrar_o_actualizar(
                perfil,
                clave=f'meta_lograda_{meta.idMeta}',
                tipo='meta_lograda',
                nivel='success',
                titulo=f'¡Meta lograda: {meta.nombre}!',
                mensaje=(
                    f'Completaste el 100% de tu meta (${formatear_cop(meta.objetivo)}). '
                    'Gran hábito de ahorro.'
                ),
                url_destino='/app/metas/',
            )

    # 5. Recordatorio de préstamos pendientes
    prestamos_pend = Prestamo.objects.filter(idUsuario=perfil, estado='Pendiente')
    cant_prest = prestamos_pend.count()
    if cant_prest > 0:
        total_prest = prestamos_pend.aggregate(total=Sum('monto'))['total'] or CERO
        _registrar_o_actualizar(
            perfil,
            clave=f'prestamos_pend_{mes_tag}',
            tipo='prestamo_pendiente',
            nivel='info',
            titulo=f'Tienes {cant_prest} préstamo{"s" if cant_prest != 1 else ""} pendiente{"s" if cant_prest != 1 else ""}',
            mensaje=(
                f'Suman ${formatear_cop(total_prest)} por gestionar entre compañeros. '
                'Márcalos como pagados cuando se salden.'
            ),
            url_destino='/app/metas/?tab=prestamos',
        )

    # 6. Aviso de fecha vencida para usuarios con ingresos irregulares
    ciclo = resumen['ciclo']
    if ciclo.get('requiere_fecha_ciclo') and ciclo.get('ciclo_vencido'):
        _registrar_o_actualizar(
            perfil,
            clave=f'ciclo_irregular_vencido_{hoy_iso}',
            tipo='ciclo',
            nivel='info',
            titulo='Actualiza tu próximo ingreso',
            mensaje='La fecha estimada de tu ciclo irregular ya pasó. Actualízala en Perfil para recalcular tu límite.',
            url_destino='/app/perfil/',
        )

    return Notificacion.objects.filter(idUsuario=perfil, leida=False).count()
