"""Motor de recomendaciones financieras personalizadas basadas en datos reales (RF-13)."""

from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from finanzas.services.finanzas_service import (
    CERO,
    formatear_cop,
    obtener_umbral_hormiga,
)


def generar_recomendaciones_personalizadas(
    perfil,
    resumen,
    comparacion=None,
    presupuestos_cat=None,
    metas_plan=None,
    compartidos_resumen=None,
    hoy=None,
):
    """Genera recomendaciones accionables y cuantificadas únicamente con datos reales del usuario."""
    hoy = hoy or resumen.get('hoy') or timezone.localdate()
    umbral_hormiga = obtener_umbral_hormiga(perfil)
    recomendaciones = []

    # 1. Liquidez crítica o límite diario excedido
    if resumen['saldo_cero_o_negativo']:
        recomendaciones.append({
            'nivel': 'danger',
            'titulo': 'Prioriza gastos esenciales hasta tu próximo ingreso',
            'detalle': (
                f"Tu saldo disponible está en ${resumen['saldo_fmt']} para "
                f"{resumen['dias_restantes']} día{'s' if resumen['dias_restantes'] != 1 else ''}. "
                'Pausa gastos opcionales y revisa si tienes reembolsos por cobrar.'
            ),
            'accion_lbl': 'Revisar presupuesto',
            'url_destino': '/app/presupuestos/',
        })
    elif resumen['limite_superado']:
        recomendaciones.append({
            'nivel': 'danger',
            'titulo': 'Compensa el excedente de hoy mañana',
            'detalle': (
                f"Hoy superaste tu límite diario por ${resumen['excedente_hoy_fmt']}. "
                f"Tu límite sugerido actual para los próximos días es ${resumen['limite_diario_recomendado_fmt']}/día."
            ),
            'accion_lbl': 'Ver movimientos',
            'url_destino': '/app/historial/?tipo=gasto',
        })

    # 2. Presupuestos por categoría excedidos o cerca del tope (RF-11)
    if presupuestos_cat:
        for pc in presupuestos_cat.get('presupuestos_configurados', []):
            if pc['excedido']:
                recomendaciones.append({
                    'nivel': 'danger',
                    'titulo': f"Recorta gastos en {pc['nombre']}",
                    'detalle': (
                        f"Has gastado ${pc['gastado_fmt']} en {pc['nombre']}, superando tu tope de "
                        f"${pc['tope_fmt']} en ${pc['excedente_fmt']} ({pc['porcentaje_real']}%)."
                    ),
                    'accion_lbl': 'Ajustar tope',
                    'url_destino': '/app/presupuestos/',
                })
                break
        else:
            for pc in presupuestos_cat.get('presupuestos_configurados', []):
                if pc['cerca']:
                    recomendaciones.append({
                        'nivel': 'warn',
                        'titulo': f"Cuida tu presupuesto de {pc['nombre']}",
                        'detalle': (
                            f"Ya usaste el {pc['porcentaje_real']}% en {pc['nombre']}. "
                            f"Te quedan ${pc['disponible_fmt']} disponibles este mes."
                        ),
                        'accion_lbl': 'Ver presupuestos',
                        'url_destino': '/app/presupuestos/',
                    })
                    break

    # 3. Gastos hormiga usando el umbral configurable del usuario (RF-09)
    inicio_mes = hoy.replace(day=1)
    hormiga_qs = resumen['movimientos'].filter(
        tipo__iexact='gasto',
        fecha__gte=inicio_mes,
        fecha__lte=hoy,
        monto__lte=umbral_hormiga,
    )
    hormiga_mes = hormiga_qs.aggregate(t=Sum('monto'))['t'] or CERO
    hormiga_cant = hormiga_qs.count()
    gastos_mes = resumen['gastos_mes']

    if hormiga_mes > CERO and (
        (gastos_mes > CERO and (hormiga_mes / gastos_mes) >= Decimal('0.20'))
        or hormiga_cant >= 4
    ):
        ahorro_potencial = (hormiga_mes * Decimal('0.30')).quantize(Decimal('1'))
        pct_h = round(float((hormiga_mes / gastos_mes) * Decimal('100'))) if gastos_mes > CERO else 0
        extra_meta = ''
        if metas_plan:
            meta_activa = next((m for m in metas_plan if not m['completada']), None)
            if meta_activa:
                extra_meta = f" para acercarte a tu meta «{meta_activa['nombre']}»"
        recomendaciones.append({
            'nivel': 'warn',
            'titulo': f'Reduce tus gastos hormiga (≤ ${formatear_cop(umbral_hormiga)})',
            'detalle': (
                f'Este mes registras {hormiga_cant} compras pequeñas por ${formatear_cop(hormiga_mes)} '
                f'({pct_h}% de tus gastos). Reducir un 30% liberaría ${formatear_cop(ahorro_potencial)}{extra_meta}.'
            ),
            'accion_lbl': 'Ajustar umbral',
            'url_destino': '/app/insights/?tab=control',
        })

    # 4. Comparación entre períodos (RF-08)
    if comparacion and comparacion.get('tiene_datos_anteriores'):
        var_gas = comparacion['var_gastos_pct']
        if var_gas >= 15 and comparacion['delta_gastos'] > CERO:
            top_subida = next(
                (c for c in comparacion.get('variacion_categorias', []) if c['subio']),
                None,
            )
            foco = (
                f" El mayor aumento está en {top_subida['nombre']} (+${top_subida['delta_abs_fmt']})."
                if top_subida
                else ''
            )
            recomendaciones.append({
                'nivel': 'warn',
                'titulo': f'Tus gastos subieron {var_gas}% frente a {comparacion["etiqueta_anterior"].lower()}',
                'detalle': (
                    f"Llevas ${comparacion['gastos_actual_fmt']} frente a ${comparacion['gastos_anterior_fmt']} "
                    f"en el período previo.{foco}"
                ),
                'accion_lbl': 'Ver historial',
                'url_destino': '/app/historial/?tipo=gasto',
            })
        elif var_gas <= -10 and comparacion['delta_gastos'] < CERO:
            recomendaciones.append({
                'nivel': 'success',
                'titulo': f'Ahorraste ${comparacion["delta_gastos_fmt"]} frente a {comparacion["etiqueta_anterior"].lower()}',
                'detalle': (
                    f'Bajaste tus gastos un {abs(var_gas)}%. Es un buen momento para '
                    'abonar parte de ese ahorro a una meta.'
                ),
                'accion_lbl': 'Ir a metas',
                'url_destino': '/app/metas/',
            })

    # 5. Metas con fecha objetivo vencida o exigente (RF-10)
    if metas_plan:
        meta_vencida = next((m for m in metas_plan if m['vencida']), None)
        if meta_vencida:
            recomendaciones.append({
                'nivel': 'warn',
                'titulo': f"Reprograma tu meta «{meta_vencida['nombre']}»",
                'detalle': (
                    f"La fecha objetivo ya pasó y faltan ${meta_vencida['faltante_fmt']}. "
                    'Actualiza la fecha para recalcular cuotas alcanzables.'
                ),
                'accion_lbl': 'Editar meta',
                'url_destino': '/app/metas/',
            })
        else:
            meta_exigente = next((m for m in metas_plan if not m['completada'] and m['exigente']), None)
            if meta_exigente:
                recomendaciones.append({
                    'nivel': 'info',
                    'titulo': f"Plan exigente en «{meta_exigente['nombre']}»",
                    'detalle': (
                        f"Necesitas ahorrar ${meta_exigente['cuota_diaria_fmt']}/día "
                        f"(${meta_exigente['cuota_ciclo_fmt']} {meta_exigente['etiqueta_ciclo']}) "
                        'para cumplirla a tiempo. Evalúa ampliar el plazo si te ajusta el límite diario.'
                    ),
                    'accion_lbl': 'Ver metas',
                    'url_destino': '/app/metas/',
                })

    # 6. Dinero pendiente por recuperar en préstamos y gastos compartidos (RF-12)
    if compartidos_resumen:
        por_recuperar = (
            compartidos_resumen.get('total_por_cobrar', CERO)
            + compartidos_resumen.get('total_por_recuperar', CERO)
        )
        if por_recuperar > CERO:
            recomendaciones.append({
                'nivel': 'info',
                'titulo': f'Tienes ${formatear_cop(por_recuperar)} pendientes por recuperar',
                'detalle': (
                    'Entre préstamos por cobrar y gastos compartidos con compañeros tienes '
                    f'${formatear_cop(por_recuperar)} pendientes. Cuando los recibas, márcalos como pagados.'
                ),
                'accion_lbl': 'Gestionar cobros',
                'url_destino': '/app/metas/?tab=compartidos',
            })

    # 7. Estado saludable cuando no hay alertas críticas
    if not recomendaciones:
        recomendaciones.append({
            'nivel': 'success',
            'titulo': 'Tu ritmo financiero va equilibrado',
            'detalle': (
                f"Tienes ${resumen['saldo_fmt']} disponibles y un límite sugerido de "
                f"${resumen['limite_diario_recomendado_fmt']}/día para los próximos "
                f"{resumen['dias_restantes']} día{'s' if resumen['dias_restantes'] != 1 else ''}. "
                'Configura presupuestos por categoría o una meta con fecha objetivo para potenciar tu ahorro.'
            ),
            'accion_lbl': 'Explorar metas',
            'url_destino': '/app/metas/',
        })

    return recomendaciones[:5]
