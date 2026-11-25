"""Analítica real de comparación entre períodos y evolución del ahorro (RF-08)."""

from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from finanzas.models import AporteMeta, MetaAhorro, Transaccion
from finanzas.services.finanzas_service import CERO, formatear_cop
from finanzas.ui_helpers import MESES_CORTOS_ES


def _pct_variacion(actual, anterior):
    """Calcula variación porcentual entera sin divisiones por cero."""
    if anterior > CERO:
        return round(float(((actual - anterior) / anterior) * Decimal('100')))
    if actual > CERO:
        return 100
    return 0


def _ventanas_periodo(periodo, hoy):
    """Retorna (inicio_actual, fin_actual, inicio_prev, fin_prev, etiqueta_actual, etiqueta_prev)."""
    p = (periodo or 'mensual').lower()
    if p == 'semanal':
        inicio_act = hoy - timedelta(days=hoy.weekday())
        fin_act = hoy
        inicio_prev = inicio_act - timedelta(days=7)
        fin_prev = inicio_act - timedelta(days=1)
        return inicio_act, fin_act, inicio_prev, fin_prev, 'Esta semana', 'Semana anterior'

    if p == 'anual':
        inicio_act = hoy.replace(month=1, day=1)
        fin_act = hoy
        anio_prev = hoy.year - 1
        inicio_prev = hoy.replace(year=anio_prev, month=1, day=1)
        fin_prev = hoy.replace(year=anio_prev, month=12, day=31)
        return inicio_act, fin_act, inicio_prev, fin_prev, f'Año {hoy.year}', f'Año {anio_prev}'

    # Mensual por defecto
    inicio_act = hoy.replace(day=1)
    fin_act = hoy
    fin_prev = inicio_act - timedelta(days=1)
    inicio_prev = fin_prev.replace(day=1)
    mes_prev_lbl = MESES_CORTOS_ES[inicio_prev.month - 1].capitalize()
    return inicio_act, fin_act, inicio_prev, fin_prev, 'Este mes', f'{mes_prev_lbl} {inicio_prev.year}'


def calcular_comparacion_periodos(perfil, periodo='mensual', hoy=None):
    """Compara ingresos, gastos, ahorro neto, aportes a metas y categorías entre el período actual y el anterior."""
    hoy = hoy or timezone.localdate()
    ini_act, fin_act, ini_prev, fin_prev, lbl_act, lbl_prev = _ventanas_periodo(periodo, hoy)

    tx_usr = Transaccion.objects.filter(idUsuario=perfil)
    ap_usr = AporteMeta.objects.filter(idUsuario=perfil)

    def _totales_ventana(desde, hasta):
        qs = tx_usr.filter(fecha__gte=desde, fecha__lte=hasta)
        ing = qs.filter(tipo__iexact='ingreso').aggregate(t=Sum('monto'))['t'] or CERO
        gas = qs.filter(tipo__iexact='gasto').aggregate(t=Sum('monto'))['t'] or CERO
        apo = ap_usr.filter(fecha__gte=desde, fecha__lte=hasta).aggregate(t=Sum('monto'))['t'] or CERO
        return ing, gas, ing - gas, apo

    ing_act, gas_act, neto_act, apo_act = _totales_ventana(ini_act, fin_act)
    ing_prev, gas_prev, neto_prev, apo_prev = _totales_ventana(ini_prev, fin_prev)

    # Variación de gastos por categoría entre ambos períodos
    cats_act = {
        r['idCategoria__nombre']: r['total'] or CERO
        for r in tx_usr.filter(tipo__iexact='gasto', fecha__gte=ini_act, fecha__lte=fin_act)
        .values('idCategoria__nombre')
        .annotate(total=Sum('monto'))
    }
    cats_prev = {
        r['idCategoria__nombre']: r['total'] or CERO
        for r in tx_usr.filter(tipo__iexact='gasto', fecha__gte=ini_prev, fecha__lte=fin_prev)
        .values('idCategoria__nombre')
        .annotate(total=Sum('monto'))
    }
    todas_cats = sorted(set(cats_act.keys()) | set(cats_prev.keys()))
    variacion_categorias = []
    for nombre in todas_cats:
        val_act = cats_act.get(nombre, CERO)
        val_prev = cats_prev.get(nombre, CERO)
        delta = val_act - val_prev
        variacion_categorias.append({
            'nombre': nombre,
            'actual': val_act,
            'actual_fmt': formatear_cop(val_act),
            'anterior': val_prev,
            'anterior_fmt': formatear_cop(val_prev),
            'delta': delta,
            'delta_abs_fmt': formatear_cop(abs(delta)),
            'subio': delta > CERO,
            'bajo': delta < CERO,
            'pct': _pct_variacion(val_act, val_prev),
        })
    variacion_categorias.sort(key=lambda item: -abs(item['delta']))

    delta_ing = ing_act - ing_prev
    delta_gas = gas_act - gas_prev
    delta_neto = neto_act - neto_prev
    delta_apo = apo_act - apo_prev

    var_gas_pct = _pct_variacion(gas_act, gas_prev)
    var_ing_pct = _pct_variacion(ing_act, ing_prev)

    return {
        'periodo': periodo,
        'etiqueta_actual': lbl_act,
        'etiqueta_anterior': lbl_prev,
        'ingresos_actual': ing_act,
        'ingresos_actual_fmt': formatear_cop(ing_act),
        'ingresos_anterior': ing_prev,
        'ingresos_anterior_fmt': formatear_cop(ing_prev),
        'delta_ingresos': delta_ing,
        'delta_ingresos_fmt': formatear_cop(abs(delta_ing)),
        'var_ingresos_pct': var_ing_pct,
        'gastos_actual': gas_act,
        'gastos_actual_fmt': formatear_cop(gas_act),
        'gastos_anterior': gas_prev,
        'gastos_anterior_fmt': formatear_cop(gas_prev),
        'delta_gastos': delta_gas,
        'delta_gastos_fmt': formatear_cop(abs(delta_gas)),
        'var_gastos_pct': var_gas_pct,
        'var_gastos_abs': abs(var_gas_pct),
        'ahorro_neto_actual': neto_act,
        'ahorro_neto_actual_fmt': formatear_cop(abs(neto_act)),
        'ahorro_neto_actual_positivo': neto_act >= CERO,
        'ahorro_neto_anterior': neto_prev,
        'ahorro_neto_anterior_fmt': formatear_cop(abs(neto_prev)),
        'ahorro_neto_anterior_positivo': neto_prev >= CERO,
        'delta_ahorro_neto': delta_neto,
        'delta_ahorro_neto_fmt': formatear_cop(abs(delta_neto)),
        'ahorro_mejoro': delta_neto > CERO,
        'aportes_metas_actual': apo_act,
        'aportes_metas_actual_fmt': formatear_cop(apo_act),
        'aportes_metas_anterior': apo_prev,
        'aportes_metas_anterior_fmt': formatear_cop(apo_prev),
        'delta_aportes_metas': delta_apo,
        'delta_aportes_metas_fmt': formatear_cop(abs(delta_apo)),
        'tiene_datos_anteriores': (ing_prev > CERO or gas_prev > CERO or apo_prev > CERO),
        'variacion_categorias': variacion_categorias[:4],
    }


def calcular_evolucion_ahorro(perfil, hoy=None, meses=6):
    """Genera serie real mensual (últimos N meses) de ahorro neto (ingresos - gastos) y aportes a metas."""
    hoy = hoy or timezone.localdate()
    meses = max(3, min(12, int(meses)))

    anio = hoy.year
    mes = hoy.month
    lista_meses = []
    for _ in range(meses):
        lista_meses.append((anio, mes))
        mes -= 1
        if mes == 0:
            mes = 12
            anio -= 1
    lista_meses.reverse()

    tx_usr = Transaccion.objects.filter(idUsuario=perfil)
    ap_usr = AporteMeta.objects.filter(idUsuario=perfil)

    total_metas_actual = (
        MetaAhorro.objects.filter(idUsuario=perfil).aggregate(t=Sum('acumulado'))['t']
        or CERO
    )
    total_aportes_registrados = ap_usr.aggregate(t=Sum('monto'))['t'] or CERO
    base_previa_metas = max(total_metas_actual - total_aportes_registrados, CERO)

    primer_anio, primer_mes = lista_meses[0]
    inicio_ventana = hoy.replace(year=primer_anio, month=primer_mes, day=1)
    aportes_antes_ventana = (
        ap_usr.filter(fecha__lt=inicio_ventana).aggregate(t=Sum('monto'))['t']
        or CERO
    )
    acumulado_metas_corriente = base_previa_metas + aportes_antes_ventana

    serie = []
    for a, m in lista_meses:
        inicio = hoy.replace(year=a, month=m, day=1)
        if m == 12:
            siguiente = inicio.replace(year=a + 1, month=1, day=1)
        else:
            siguiente = inicio.replace(month=m + 1, day=1)
        fin = min(siguiente - timedelta(days=1), hoy)

        ing = (
            tx_usr.filter(tipo__iexact='ingreso', fecha__gte=inicio, fecha__lte=fin)
            .aggregate(t=Sum('monto'))['t']
            or CERO
        )
        gas = (
            tx_usr.filter(tipo__iexact='gasto', fecha__gte=inicio, fecha__lte=fin)
            .aggregate(t=Sum('monto'))['t']
            or CERO
        )
        apo = (
            ap_usr.filter(fecha__gte=inicio, fecha__lte=fin)
            .aggregate(t=Sum('monto'))['t']
            or CERO
        )
        acumulado_metas_corriente += apo
        ahorro_neto = ing - gas
        serie.append({
            'etiqueta': MESES_CORTOS_ES[m - 1].capitalize(),
            'anio': a,
            'mes': m,
            'ingresos': ing,
            'gastos': gas,
            'ahorro_neto': ahorro_neto,
            'ahorro_neto_fmt': formatear_cop(ahorro_neto),
            'aportes_metas': apo,
            'aportes_metas_fmt': formatear_cop(apo),
            'acumulado_metas': acumulado_metas_corriente,
            'acumulado_metas_fmt': formatear_cop(acumulado_metas_corriente),
        })

    return {
        'serie': serie,
        'etiquetas_json': [s['etiqueta'] for s in serie],
        'ahorro_neto_json': [float(s['ahorro_neto']) for s in serie],
        'aportes_metas_json': [float(s['aportes_metas']) for s in serie],
        'acumulado_metas_json': [float(s['acumulado_metas']) for s in serie],
        'total_ahorro_metas': total_metas_actual,
        'total_ahorro_metas_fmt': formatear_cop(total_metas_actual),
    }
