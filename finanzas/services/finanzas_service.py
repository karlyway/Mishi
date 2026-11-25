"""Motor financiero centralizado de Mishi (Fase 1).

Fuente única de verdad para:
- Reconciliación de saldo inicial, ingresos efectivos, gastos, dinero reservado para metas y saldo disponible.
- Ciclo financiero (diario, semanal, quincenal, mensual con fin de mes/bisiestos, e irregular).
- Límite diario basado en saldo al inicio del día + ingresos del día (sin descontar dos veces el gasto del día).
- Reglas de alertas sin contradicciones (<80% normal, 80-100% preventiva, >100% superado, saldo insuficiente).
"""

import calendar
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Sum
from django.utils import timezone

from finanzas.models import MetaAhorro, Presupuesto, Transaccion


FRECUENCIAS_VALIDAS = ('diario', 'semanal', 'quincenal', 'mensual', 'irregular')

DIAS_POR_FRECUENCIA = {
    'diario': 1,
    'semanal': 7,
    'quincenal': 15,
    'mensual': 30,
    'irregular': 1,
}

UMBRAL_ALERTA_PREVENTIVA = Decimal('0.80')
UMBRAL_HORMIGA_DEFECTO = Decimal('15000.00')
CERO = Decimal('0.00')
CENTAVO = Decimal('0.01')


def formatear_cop(valor):
    """Formatea un valor numérico con separador de miles en punto estilo COP."""
    if valor is None:
        return '0'
    numero = Decimal(valor)
    negativo = numero < 0
    numero = abs(numero)
    entero = int(numero)
    fraccion = numero - entero
    entero_fmt = f'{entero:,}'.replace(',', '.')
    if fraccion > 0:
        dec = f'{fraccion:.2f}'[2:].rstrip('0')
        resultado = f'{entero_fmt},{dec}' if dec else entero_fmt
    else:
        resultado = entero_fmt
    return f'-{resultado}' if negativo else resultado


def calcular_dias_frecuencia(frecuencia):
    """Retorna la duración estándar en días (>= 1) para cada frecuencia."""
    return max(1, DIAS_POR_FRECUENCIA.get((frecuencia or 'quincenal').lower(), 15))


def sumar_un_mes(fecha_actual, dia_ancla=None):
    """Avanza exactamente un mes calendario preservando el día ancla en meses cortos y años bisiestos."""
    ancla = dia_ancla or fecha_actual.day
    if fecha_actual.month == 12:
        nuevo_anio = fecha_actual.year + 1
        nuevo_mes = 1
    else:
        nuevo_anio = fecha_actual.year
        nuevo_mes = fecha_actual.month + 1
    ultimo_dia = calendar.monthrange(nuevo_anio, nuevo_mes)[1]
    return date(nuevo_anio, nuevo_mes, min(ancla, ultimo_dia))


def avanzar_fecha_ciclo(fecha_estimada, frecuencia, hoy, dia_ancla=None):
    """Proyecta la próxima fecha estimada de ingreso sin añadir dinero automáticamente al saldo.

    Retorna tupla: (fecha_proyectada, ciclos_avanzados, ciclo_vencido).
    Para frecuencia 'irregular' nunca inventa una fecha nueva si venció.
    """
    if fecha_estimada is None:
        return None, 0, False

    frec = (frecuencia or 'quincenal').lower()
    if fecha_estimada >= hoy:
        return fecha_estimada, 0, False

    if frec == 'irregular':
        return fecha_estimada, 0, True

    proyectada = fecha_estimada
    ancla = dia_ancla or fecha_estimada.day
    avanzados = 0

    while proyectada < hoy:
        if frec == 'diario':
            proyectada += timedelta(days=1)
        elif frec == 'semanal':
            proyectada += timedelta(days=7)
        elif frec == 'quincenal':
            proyectada += timedelta(days=15)
        elif frec == 'mensual':
            proyectada = sumar_un_mes(proyectada, ancla)
        else:
            proyectada += timedelta(days=15)
        avanzados += 1

    return proyectada, avanzados, True


def calcular_ciclo_financiero(perfil, hoy=None):
    """Calcula días restantes (>= 1) hasta el próximo ingreso estimado sin alterar saldo."""
    hoy = hoy or timezone.localdate()
    frec = (perfil.frecuencia or 'quincenal').lower()
    fecha_config = getattr(perfil, 'fecha_proximo_ingreso', None)
    dia_ancla = getattr(perfil, 'dia_pago_mensual', None)

    if fecha_config is None:
        return {
            'frecuencia': frec,
            'fecha_configurada': None,
            'fecha_proximo_ingreso': None,
            'dias_restantes': calcular_dias_frecuencia(frec),
            'ciclos_avanzados': 0,
            'ciclo_vencido': False,
            'ciclo_estimado': True,
            'requiere_fecha_ciclo': frec == 'irregular',
        }

    fecha_proyectada, avanzados, vencido = avanzar_fecha_ciclo(
        fecha_config,
        frec,
        hoy,
        dia_ancla=dia_ancla,
    )

    if frec == 'irregular' and vencido:
        dias_restantes = 1
        requiere_fecha = True
    else:
        dias_restantes = max(1, (fecha_proyectada - hoy).days)
        requiere_fecha = False

    return {
        'frecuencia': frec,
        'fecha_configurada': fecha_config,
        'fecha_proximo_ingreso': fecha_proyectada,
        'dias_restantes': dias_restantes,
        'ciclos_avanzados': avanzados,
        'ciclo_vencido': vencido,
        'ciclo_estimado': False,
        'requiere_fecha_ciclo': requiere_fecha,
    }


def _redondear_moneda(valor):
    return Decimal(valor).quantize(CENTAVO, rounding=ROUND_HALF_UP)


def calcular_resumen_financiero(perfil, hoy=None):
    """Fuente única de verdad financiera para todas las vistas de Mishi.

    Invariante contable verificable:
      saldo_total = saldo_inicial + ingresos_recibidos - gastos_totales
      saldo_disponible = saldo_total - dinero_reservado_metas
      base_disponible_hoy = saldo_inicio_dia + ingresos_hoy == saldo_disponible + gasto_hoy
    """
    hoy = hoy or timezone.localdate()
    ciclo = calcular_ciclo_financiero(perfil, hoy=hoy)
    dias_restantes = ciclo['dias_restantes']

    movimientos = (
        Transaccion.objects.filter(idUsuario=perfil)
        .select_related('idCategoria')
        .order_by('-fecha', '-idTransaccion')
    )
    movimientos_hasta_hoy = movimientos.filter(fecha__lte=hoy)

    # 1. Desglose contable por fecha (< hoy vs == hoy) para no castigar el límite diario al gastar hoy
    ingresos_anteriores = (
        movimientos_hasta_hoy.filter(tipo__iexact='ingreso', fecha__lt=hoy)
        .aggregate(total=Sum('monto'))['total']
        or CERO
    )
    gastos_anteriores = (
        movimientos_hasta_hoy.filter(tipo__iexact='gasto', fecha__lt=hoy)
        .aggregate(total=Sum('monto'))['total']
        or CERO
    )
    ingresos_hoy = (
        movimientos_hasta_hoy.filter(tipo__iexact='ingreso', fecha=hoy)
        .aggregate(total=Sum('monto'))['total']
        or CERO
    )
    gasto_hoy = (
        movimientos_hasta_hoy.filter(tipo__iexact='gasto', fecha=hoy)
        .aggregate(total=Sum('monto'))['total']
        or CERO
    )

    ingresos_recibidos = ingresos_anteriores + ingresos_hoy
    gastos_totales = gastos_anteriores + gasto_hoy

    # 2. Separación estricta: saldo inicial vs ingreso esperado vs dinero reservado en metas
    saldo_inicial = (
        perfil.saldo_inicial
        if getattr(perfil, 'saldo_inicial', None) is not None
        else (perfil.mesada or CERO)
    )
    ingreso_esperado = perfil.mesada or CERO

    dinero_reservado_metas = (
        MetaAhorro.objects.filter(idUsuario=perfil).aggregate(total=Sum('acumulado'))['total']
        or CERO
    )

    saldo_total = saldo_inicial + ingresos_recibidos - gastos_totales
    saldo_disponible = saldo_total - dinero_reservado_metas

    # 3. Base de cálculo del límite diario (invariante ante gastos registrados HOY, reactiva a ingresos HOY)
    saldo_inicio_dia = saldo_inicial + ingresos_anteriores - gastos_anteriores - dinero_reservado_metas
    base_disponible_hoy = saldo_inicio_dia + ingresos_hoy  # == saldo_disponible + gasto_hoy

    if base_disponible_hoy > CERO:
        limite_diario_recomendado = _redondear_moneda(base_disponible_hoy / Decimal(dias_restantes))
    else:
        limite_diario_recomendado = CERO

    presupuesto = Presupuesto.objects.filter(idUsuario=perfil).first()
    limite_diario_personalizado = presupuesto.limiteDiario if presupuesto else None
    limite_mensual_personalizado = presupuesto.limiteMensual if presupuesto else None

    if base_disponible_hoy <= CERO:
        limite_diario_activo = CERO
        usa_limite_personalizado = False
    elif limite_diario_personalizado is not None:
        limite_diario_activo = limite_diario_personalizado
        usa_limite_personalizado = True
    else:
        limite_diario_activo = limite_diario_recomendado
        usa_limite_personalizado = False

    margen_limite_hoy = limite_diario_activo - gasto_hoy
    dinero_restante_hoy = max(CERO, min(margen_limite_hoy, saldo_disponible))
    excedente_hoy = max(CERO, gasto_hoy - limite_diario_activo)

    # 4. Porcentaje y reglas exactas de alertas RF-05 (<80 normal, 80-100 preventiva, >100 superado, saldo insuficiente)
    if limite_diario_activo > CERO:
        porcentaje_gasto_hoy = round(float((gasto_hoy / limite_diario_activo) * Decimal('100')), 2)
    elif gasto_hoy > CERO:
        porcentaje_gasto_hoy = 100.0
    else:
        porcentaje_gasto_hoy = 0.0

    limite_superado = (
        (limite_diario_activo > CERO and gasto_hoy > limite_diario_activo)
        or (limite_diario_activo <= CERO and gasto_hoy > CERO)
    )
    alerta_preventiva = (
        not limite_superado
        and limite_diario_activo > CERO
        and gasto_hoy >= (limite_diario_activo * UMBRAL_ALERTA_PREVENTIVA)
    )

    if limite_superado:
        estado_alerta_diaria = 'superado'
    elif alerta_preventiva:
        estado_alerta_diaria = 'preventiva'
    else:
        estado_alerta_diaria = 'normal'

    saldo_cero_o_negativo = saldo_disponible <= CERO
    saldo_insuficiente_ciclo = (
        limite_diario_personalizado is not None
        and saldo_disponible > CERO
        and base_disponible_hoy < (limite_diario_personalizado * Decimal(dias_restantes))
    )
    alerta_saldo_insuficiente = saldo_cero_o_negativo or saldo_insuficiente_ciclo
    alerta_activa = limite_superado or alerta_preventiva or alerta_saldo_insuficiente

    # Alerta priorizada única (evita contradicciones o avisos duplicados entre pantallas)
    if saldo_cero_o_negativo:
        alerta_principal = {
            'tipo': 'saldo_insuficiente',
            'nivel': 'danger',
            'titulo': 'Saldo insuficiente',
            'detalle': (
                f'Tu saldo disponible es ${formatear_cop(saldo_disponible)} para los '
                f'{dias_restantes} día{"s" if dias_restantes != 1 else ""} restantes.'
            ),
        }
    elif limite_superado:
        alerta_principal = {
            'tipo': 'limite_superado',
            'nivel': 'danger',
            'titulo': 'Límite diario superado',
            'detalle': (
                f'Hoy llevas ${formatear_cop(gasto_hoy)} de ${formatear_cop(limite_diario_activo)} '
                f'({porcentaje_gasto_hoy}%).'
            ),
        }
    elif alerta_preventiva:
        alerta_principal = {
            'tipo': 'preventiva',
            'nivel': 'warn',
            'titulo': f'Límite diario al {porcentaje_gasto_hoy}%',
            'detalle': (
                f'Hoy llevas ${formatear_cop(gasto_hoy)} · Te quedan ${formatear_cop(dinero_restante_hoy)}.'
            ),
        }
    elif saldo_insuficiente_ciclo:
        alerta_principal = {
            'tipo': 'saldo_insuficiente',
            'nivel': 'warn',
            'titulo': 'Saldo ajustado para tu ciclo',
            'detalle': (
                f'Con tu límite de ${formatear_cop(limite_diario_activo)}/día, '
                f'tu saldo no alcanza para los {dias_restantes} días restantes.'
            ),
        }
    else:
        alerta_principal = None

    # 5. Gastos hormiga de hoy y acumulados del mes
    umbral_hormiga = UMBRAL_HORMIGA_DEFECTO
    total_hormiga = (
        movimientos_hasta_hoy.filter(
            tipo__iexact='gasto',
            fecha=hoy,
            monto__lte=umbral_hormiga,
        ).aggregate(total=Sum('monto'))['total']
        or CERO
    )

    inicio_mes = hoy.replace(day=1)
    gastos_mes = (
        movimientos_hasta_hoy.filter(
            tipo__iexact='gasto',
            fecha__gte=inicio_mes,
            fecha__lte=hoy,
        ).aggregate(total=Sum('monto'))['total']
        or CERO
    )

    referencia_mensual = (
        limite_mensual_personalizado
        if limite_mensual_personalizado and limite_mensual_personalizado > CERO
        else (saldo_inicial + ingresos_recibidos)
    )
    if referencia_mensual > CERO:
        porcentaje_mes = min(100, round(float((gastos_mes / referencia_mensual) * Decimal('100'))))
    elif gastos_mes > CERO:
        porcentaje_mes = 100
    else:
        porcentaje_mes = 0

    return {
        'movimientos': movimientos,
        'hoy': hoy,
        'ciclo': ciclo,
        'presupuesto': presupuesto,
        # Contabilidad desglosada
        'saldo_inicial': saldo_inicial,
        'saldo_inicial_fmt': formatear_cop(saldo_inicial),
        'ingreso_esperado': ingreso_esperado,
        'ingreso_esperado_fmt': formatear_cop(ingreso_esperado),
        'ingresos': ingresos_recibidos,
        'ingresos_recibidos': ingresos_recibidos,
        'ingresos_recibidos_fmt': formatear_cop(ingresos_recibidos),
        'ingresos_hoy': ingresos_hoy,
        'ingresos_hoy_fmt': formatear_cop(ingresos_hoy),
        'gastos': gastos_totales,
        'gastos_totales': gastos_totales,
        'gastos_totales_fmt': formatear_cop(gastos_totales),
        'dinero_reservado_metas': dinero_reservado_metas,
        'dinero_reservado_metas_fmt': formatear_cop(dinero_reservado_metas),
        'saldo_total': saldo_total,
        'saldo_total_fmt': formatear_cop(saldo_total),
        'saldo': saldo_disponible,
        'saldo_disponible': saldo_disponible,
        'saldo_fmt': formatear_cop(saldo_disponible),
        # Límite diario y día actual
        'dias_restantes': dias_restantes,
        'saldo_inicio_dia': saldo_inicio_dia,
        'saldo_inicio_dia_fmt': formatear_cop(saldo_inicio_dia),
        'base_disponible_hoy': base_disponible_hoy,
        'base_disponible_hoy_fmt': formatear_cop(base_disponible_hoy),
        'limite_diario_recomendado': limite_diario_recomendado,
        'limite_diario_recomendado_fmt': formatear_cop(limite_diario_recomendado),
        'limite_diario_personalizado': limite_diario_personalizado,
        'limite_diario_personalizado_fmt': (
            formatear_cop(limite_diario_personalizado)
            if limite_diario_personalizado is not None
            else None
        ),
        'usa_limite_personalizado': usa_limite_personalizado,
        'limite_diario': limite_diario_activo,
        'limite_diario_activo': limite_diario_activo,
        'limite_diario_fmt': formatear_cop(limite_diario_activo),
        'gasto_hoy': gasto_hoy,
        'gasto_hoy_fmt': formatear_cop(gasto_hoy),
        'dinero_restante_hoy': dinero_restante_hoy,
        'dinero_restante_hoy_fmt': formatear_cop(dinero_restante_hoy),
        'excedente_hoy': excedente_hoy,
        'excedente_hoy_fmt': formatear_cop(excedente_hoy),
        'porcentaje_gasto_hoy': porcentaje_gasto_hoy,
        # Alertas RF-05
        'estado_alerta_diaria': estado_alerta_diaria,
        'alerta_preventiva': alerta_preventiva,
        'limite_superado': limite_superado,
        'saldo_cero_o_negativo': saldo_cero_o_negativo,
        'alerta_saldo_insuficiente': alerta_saldo_insuficiente,
        'alerta_activa': alerta_activa,
        'alerta_principal': alerta_principal,
        # Hormiga y mes
        'total_hormiga': total_hormiga,
        'total_hormiga_fmt': formatear_cop(total_hormiga),
        'gastos_mes': gastos_mes,
        'gastos_mes_fmt': formatear_cop(gastos_mes),
        'porcentaje_mes': porcentaje_mes,
    }
