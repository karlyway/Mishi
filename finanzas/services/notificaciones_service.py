"""Motor de notificaciones reales in-app de Mishi.

Optimizado para bajo impacto de consultas:
- Carga las claves existentes en una sola consulta en memoria.
- Respeta descartada=True (una notificación eliminada NUNCA reaparece para el mismo evento/clave).
- Respeta alertas_activas=False del usuario.
- Integrado con RF-09 (umbral hormiga configurable), RF-10 (metas y fechas objetivo),
  RF-11 (presupuestos por categoría) y RF-12 (préstamos y gastos compartidos).
"""

from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from finanzas.models import MetaAhorro, Notificacion, Participante, Prestamo
from finanzas.services.finanzas_service import (
    CERO,
    calcular_resumen_financiero,
    formatear_cop,
    obtener_umbral_hormiga,
)
from finanzas.services.presupuestos_service import calcular_presupuestos_categoria


def contar_notificaciones_no_leidas(perfil):
    """Consulta liviana indexada (1 sola query COUNT) para la campana en navegación normal."""
    return Notificacion.objects.filter(
        idUsuario=perfil,
        descartada=False,
        leida=False,
    ).count()


def sincronizar_notificaciones_usuario(perfil, resumen=None, hoy=None):
    """Evalúa eventos financieros reales y persiste avisos sin duplicar ni revivir descartados."""
    hoy = hoy or timezone.localdate()
    resumen = resumen or calcular_resumen_financiero(perfil, hoy=hoy)
    hoy_iso = hoy.isoformat()
    mes_tag = f'{hoy.year}_{hoy.month:02d}'
    alertas_on = bool(getattr(perfil, 'alertas_activas', True))
    umbral_hormiga = obtener_umbral_hormiga(perfil)

    candidatas = []

    # 1. Alertas de límite diario, saldo y presupuestos (respetan alertas_activas del usuario)
    if alertas_on:
        dias = resumen['dias_restantes']
        dias_txt = f'{dias} día{"s" if dias != 1 else ""}'

        if resumen['saldo_cero_o_negativo']:
            candidatas.append((
                f'saldo_cero_{hoy_iso}',
                'saldo_insuficiente',
                'danger',
                'Saldo insuficiente',
                (
                    f"Tu saldo disponible está en ${resumen['saldo_fmt']} para los "
                    f'{dias_txt} restantes del ciclo.'
                ),
                '/app/insights/?tab=control',
            ))
        elif resumen['alerta_saldo_insuficiente']:
            candidatas.append((
                f'saldo_ciclo_{hoy_iso}',
                'saldo_insuficiente',
                'warn',
                'Saldo ajustado para tu ciclo',
                (
                    f"Con tu límite diario de ${resumen['limite_diario_fmt']}, tu saldo "
                    f"(${resumen['saldo_fmt']}) no alcanza para los {dias_txt} restantes."
                ),
                '/app/presupuestos/',
            ))

        if resumen['limite_superado']:
            candidatas.append((
                f'limite_superado_{hoy_iso}',
                'limite_superado',
                'danger',
                'Límite diario superado',
                (
                    f"Hoy registras ${resumen['gasto_hoy_fmt']} sobre tu límite diario de "
                    f"${resumen['limite_diario_fmt']} ({resumen['porcentaje_gasto_hoy']}%)."
                ),
                '/app/insights/?tab=control',
            ))
        elif resumen['alerta_preventiva']:
            candidatas.append((
                f'limite_80_{hoy_iso}',
                'alerta_80',
                'warn',
                f"Límite diario al {resumen['porcentaje_gasto_hoy']}%",
                (
                    f"Llevas ${resumen['gasto_hoy_fmt']} hoy. Te quedan "
                    f"${resumen['dinero_restante_hoy_fmt']} disponibles para el resto del día."
                ),
                '/app/insights/?tab=control',
            ))

        presupuesto = resumen.get('presupuesto')
        if presupuesto and presupuesto.limiteMensual > CERO:
            gastos_mes = resumen['gastos_mes']
            pct_mes = round(float((gastos_mes / presupuesto.limiteMensual) * Decimal('100')))
            if gastos_mes > presupuesto.limiteMensual:
                candidatas.append((
                    f'presupuesto_mes_superado_{mes_tag}',
                    'presupuesto_mensual',
                    'danger',
                    'Presupuesto mensual superado',
                    (
                        f"Llevas ${resumen['gastos_mes_fmt']} gastados frente a tu tope mensual "
                        f"de ${formatear_cop(presupuesto.limiteMensual)} ({pct_mes}%)."
                    ),
                    '/app/presupuestos/',
                ))
            elif pct_mes >= 80:
                candidatas.append((
                    f'presupuesto_mes_80_{mes_tag}',
                    'presupuesto_mensual',
                    'warn',
                    f'Presupuesto mensual al {pct_mes}%',
                    (
                        f"Has usado ${resumen['gastos_mes_fmt']} de tu límite mensual de "
                        f"${formatear_cop(presupuesto.limiteMensual)}."
                    ),
                    '/app/presupuestos/',
                ))

        # 1b. Presupuestos reales por categoría (RF-11)
        pres_cats = calcular_presupuestos_categoria(perfil, hoy=hoy)['presupuestos_configurados']
        for pc in pres_cats:
            if pc['excedido']:
                candidatas.append((
                    f"presupuesto_cat_superado_{pc['idCategoria']}_{mes_tag}",
                    'presupuesto_categoria',
                    'danger',
                    f"Tope de {pc['nombre']} superado",
                    (
                        f"Llevas ${pc['gastado_fmt']} en {pc['nombre']} sobre tu presupuesto de "
                        f"${pc['tope_fmt']} ({pc['porcentaje_real']}%)."
                    ),
                    '/app/presupuestos/',
                ))
            elif pc['cerca']:
                candidatas.append((
                    f"presupuesto_cat_80_{pc['idCategoria']}_{mes_tag}",
                    'presupuesto_categoria',
                    'warn',
                    f"{pc['nombre']} al {pc['porcentaje_real']}% del tope",
                    (
                        f"Has usado ${pc['gastado_fmt']} de ${pc['tope_fmt']} en {pc['nombre']}. "
                        f"Te quedan ${pc['disponible_fmt']} este mes."
                    ),
                    '/app/presupuestos/',
                ))

    # 2. Gastos hormiga relevantes del mes usando el umbral configurable del usuario (RF-09)
    gastos_mes_total = resumen['gastos_mes']
    if alertas_on and gastos_mes_total > CERO:
        inicio_mes = hoy.replace(day=1)
        hormiga_mes = (
            resumen['movimientos']
            .filter(
                tipo__iexact='gasto',
                fecha__gte=inicio_mes,
                fecha__lte=hoy,
                monto__lte=umbral_hormiga,
            )
            .aggregate(total=Sum('monto'))['total']
            or CERO
        )
        if hormiga_mes >= Decimal('20000.00') and (hormiga_mes / gastos_mes_total) >= Decimal('0.30'):
            pct_h = round(float((hormiga_mes / gastos_mes_total) * Decimal('100')))
            candidatas.append((
                f'hormiga_mes_{mes_tag}',
                'hormiga',
                'info',
                'Ojo con tus gastos hormiga',
                (
                    f'Este mes sumas ${formatear_cop(hormiga_mes)} ({pct_h}% de tus gastos) '
                    f'en compras de ${formatear_cop(umbral_hormiga)} o menos.'
                ),
                '/app/insights/?tab=control',
            ))

    # 3. Metas de ahorro cumplidas al 100%, próximas a vencer o vencidas (RF-10)
    for meta in MetaAhorro.objects.filter(idUsuario=perfil).only(
        'idMeta', 'nombre', 'objetivo', 'acumulado', 'fecha_objetivo'
    ):
        if meta.objetivo > CERO and meta.acumulado >= meta.objetivo:
            candidatas.append((
                f'meta_lograda_{meta.idMeta}',
                'meta_lograda',
                'success',
                f'¡Meta lograda: {meta.nombre}!',
                (
                    f'Completaste el 100% de tu meta (${formatear_cop(meta.objetivo)}). '
                    'Gran hábito de ahorro.'
                ),
                '/app/metas/',
            ))
        elif meta.fecha_objetivo is not None and meta.objetivo > meta.acumulado:
            dias_meta = (meta.fecha_objetivo - hoy).days
            faltante = meta.objetivo - meta.acumulado
            if dias_meta <= 0:
                candidatas.append((
                    f'meta_vencida_{meta.idMeta}',
                    'meta_plazo',
                    'warn',
                    f'Fecha vencida: {meta.nombre}',
                    (
                        f'La fecha objetivo de «{meta.nombre}» pasó y faltan '
                        f'${formatear_cop(faltante)}. Actualiza el plazo en Metas.'
                    ),
                    '/app/metas/',
                ))
            elif dias_meta <= 7:
                candidatas.append((
                    f'meta_proxima_{meta.idMeta}_{mes_tag}',
                    'meta_plazo',
                    'info',
                    f'Tu meta «{meta.nombre}» vence en {dias_meta} día{"s" if dias_meta != 1 else ""}',
                    f'Te faltan ${formatear_cop(faltante)} para completarla a tiempo.',
                    '/app/metas/',
                ))

    # 4. Recordatorio de préstamos pendientes y vencidos (RF-12)
    prestamos_pend = Prestamo.objects.filter(idUsuario=perfil, estado='Pendiente')
    cant_prest = prestamos_pend.count()
    if cant_prest > 0:
        total_prest = prestamos_pend.aggregate(total=Sum('monto'))['total'] or CERO
        candidatas.append((
            f'prestamos_pend_{mes_tag}',
            'prestamo_pendiente',
            'info',
            f'Tienes {cant_prest} préstamo{"s" if cant_prest != 1 else ""} pendiente{"s" if cant_prest != 1 else ""}',
            (
                f'Suman ${formatear_cop(total_prest)} por gestionar entre compañeros. '
                'Márcalos como pagados cuando se salden.'
            ),
            '/app/metas/?tab=prestamos',
        ))
        for p_venc in prestamos_pend.filter(fecha_limite__lt=hoy):
            candidatas.append((
                f'prestamo_vencido_{p_venc.idPrestamo}',
                'prestamo_vencido',
                'warn',
                f'Préstamo vencido con {p_venc.deudor}',
                (
                    f'El préstamo de ${formatear_cop(p_venc.monto)} ({p_venc.concepto}) '
                    'superó su fecha límite.'
                ),
                '/app/metas/?tab=prestamos',
            ))

    # 4b. Reembolsos pendientes de gastos compartidos (RF-12)
    part_pend = Participante.objects.filter(
        idGastoComp__idUsuario=perfil,
        idGastoComp__yo_pague_total=True,
        pagado=False,
    )
    cant_comp_pend = part_pend.count()
    if cant_comp_pend > 0:
        total_comp_pend = part_pend.aggregate(total=Sum('parteAportada'))['total'] or CERO
        candidatas.append((
            f'compartidos_pend_{mes_tag}',
            'gasto_compartido',
            'info',
            f'Tienes ${formatear_cop(total_comp_pend)} por recuperar en compartidos',
            (
                f'{cant_comp_pend} aporte{"s" if cant_comp_pend != 1 else ""} de compañeros '
                'siguen pendientes de reembolso.'
            ),
            '/app/metas/?tab=compartidos',
        ))

    # 5. Fecha vencida en ciclo irregular
    ciclo = resumen['ciclo']
    if ciclo.get('requiere_fecha_ciclo') and ciclo.get('ciclo_vencido'):
        candidatas.append((
            f'ciclo_irregular_vencido_{hoy_iso}',
            'ciclo',
            'info',
            'Actualiza tu próximo ingreso',
            'La fecha estimada de tu ciclo irregular ya pasó. Actualízala en Perfil para recalcular tu límite.',
            '/app/perfil/',
        ))

    if candidatas:
        claves = [c[0] for c in candidatas]
        existentes = {
            n.clave: n
            for n in Notificacion.objects.filter(idUsuario=perfil, clave__in=claves)
        }
        por_crear = []
        for clave, tipo, nivel, titulo, mensaje, url_destino in candidatas:
            titulo_c = titulo[:120]
            mensaje_c = mensaje[:280]
            url_c = url_destino[:120]
            prev = existentes.get(clave)
            if prev is None:
                por_crear.append(Notificacion(
                    idUsuario=perfil,
                    clave=clave,
                    tipo=tipo,
                    nivel=nivel,
                    titulo=titulo_c,
                    mensaje=mensaje_c,
                    url_destino=url_c,
                    leida=False,
                    descartada=False,
                ))
            elif prev.descartada:
                # Respetar eliminación del usuario: jamás revive el mismo evento/clave
                continue
            elif not prev.leida and (prev.titulo != titulo_c or prev.mensaje != mensaje_c or prev.nivel != nivel):
                prev.titulo = titulo_c
                prev.mensaje = mensaje_c
                prev.nivel = nivel
                prev.url_destino = url_c
                prev.save(update_fields=['titulo', 'mensaje', 'nivel', 'url_destino'])

        if por_crear:
            Notificacion.objects.bulk_create(por_crear)

    return contar_notificaciones_no_leidas(perfil)
