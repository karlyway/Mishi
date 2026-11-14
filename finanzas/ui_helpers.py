from datetime import timedelta
from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone

from .models import Transaccion


CATEGORIA_ESTILOS = (
    (('aliment', 'comida', 'almuerz', 'cena', 'desayun', 'caf'), {
        'slug': 'comida',
        'tone': 'green',
        'color': '#36A65B',
        'soft': '#DCF4DF',
        'icon': 'utensils',
    }),
    (('transport', 'bus', 'uber', 'taxi', 'pasaje'), {
        'slug': 'transporte',
        'tone': 'yellow',
        'color': '#F5B82E',
        'soft': '#FDF2CE',
        'icon': 'car',
    }),
    (('ocio', 'entreten', 'cine', 'juego', 'spotify', 'musica'), {
        'slug': 'ocio',
        'tone': 'indigo',
        'color': '#6466E9',
        'soft': '#E7E7FB',
        'icon': 'gamepad',
    }),
    (('universidad', 'educac', 'estud', 'libro', 'copia', 'curso'), {
        'slug': 'educacion',
        'tone': 'slate',
        'color': '#525866',
        'soft': '#ECEEF2',
        'icon': 'graduation',
    }),
    (('hogar', 'compra', 'ropa', 'mercado', 'casa'), {
        'slug': 'compras',
        'tone': 'orange',
        'color': '#F97A22',
        'soft': '#FCE8D5',
        'icon': 'bag',
    }),
    (('salud', 'medic', 'farmac', 'eps'), {
        'slug': 'salud',
        'tone': 'rose',
        'color': '#E25563',
        'soft': '#FDE5E7',
        'icon': 'heart',
    }),
    (('mesada', 'ingreso', 'servic', 'beca', 'sueldo'), {
        'slug': 'servicios',
        'tone': 'teal',
        'color': '#189A88',
        'soft': '#DDF5F0',
        'icon': 'wallet',
    }),
)

ESTILO_POR_DEFECTO = {
    'slug': 'otros',
    'tone': 'amber',
    'color': '#E69D18',
    'soft': '#FBF0D6',
    'icon': 'tag',
}

DIAS_SEMANA_INICIAL = ('L', 'M', 'M', 'J', 'V', 'S', 'D')


def estilo_categoria(nombre):
    """Retorna tono, color hex e icono SVG lógico para una categoría."""
    texto = (nombre or '').strip().lower()
    texto = (
        texto.replace('á', 'a')
        .replace('é', 'e')
        .replace('í', 'i')
        .replace('ó', 'o')
        .replace('ú', 'u')
    )
    for claves, estilo in CATEGORIA_ESTILOS:
        if any(clave in texto for clave in claves):
            return dict(estilo)
    return dict(ESTILO_POR_DEFECTO)


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
    dias_por_frecuencia = {
        'diario': 1,
        'semanal': 7,
        'quincenal': 15,
        'mensual': 30,
    }
    return dias_por_frecuencia.get(frecuencia, 15)


def calcular_resumen_usuario(perfil, hoy=None):
    """Calcula saldo disponible, límites y alertas diarias del estudiante."""
    hoy = hoy or timezone.localdate()
    movimientos = Transaccion.objects.filter(
        idUsuario=perfil
    ).select_related('idCategoria').order_by('-fecha', '-idTransaccion')

    ingresos = movimientos.filter(
        tipo__iexact='ingreso'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    gastos = movimientos.filter(
        tipo__iexact='gasto'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    saldo = perfil.mesada + ingresos - gastos
    dias = calcular_dias_frecuencia(perfil.frecuencia)
    limite_diario = round(saldo / dias) if saldo > 0 else 0

    gasto_hoy = movimientos.filter(
        tipo__iexact='gasto',
        fecha=hoy
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    if limite_diario > 0:
        porcentaje_gasto_hoy = round(float(gasto_hoy / limite_diario) * 100, 2)
    elif gasto_hoy > 0:
        porcentaje_gasto_hoy = 100
    else:
        porcentaje_gasto_hoy = 0

    limite_superado = (
        (gasto_hoy >= limite_diario and limite_diario > 0)
        or (limite_diario <= 0 and gasto_hoy > 0)
    )
    alerta_activa = porcentaje_gasto_hoy >= 75 or limite_superado

    total_hormiga = movimientos.filter(
        tipo__iexact='gasto',
        fecha=hoy,
        monto__lte=Decimal('15000.00')
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    inicio_mes = hoy.replace(day=1)
    gastos_mes = movimientos.filter(
        tipo__iexact='gasto',
        fecha__gte=inicio_mes,
        fecha__lte=hoy
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    referencia_mensual = perfil.mesada + ingresos
    if referencia_mensual > 0:
        porcentaje_mes = min(100, round(float(gastos_mes / referencia_mensual) * 100))
    elif gastos_mes > 0:
        porcentaje_mes = 100
    else:
        porcentaje_mes = 0

    return {
        'movimientos': movimientos,
        'hoy': hoy,
        'ingresos': ingresos,
        'gastos': gastos,
        'saldo': saldo,
        'saldo_fmt': formatear_cop(saldo),
        'dias_restantes': dias,
        'limite_diario': limite_diario,
        'limite_diario_fmt': formatear_cop(limite_diario),
        'gasto_hoy': gasto_hoy,
        'gasto_hoy_fmt': formatear_cop(gasto_hoy),
        'porcentaje_gasto_hoy': porcentaje_gasto_hoy,
        'limite_superado': limite_superado,
        'alerta_activa': alerta_activa,
        'total_hormiga': total_hormiga,
        'total_hormiga_fmt': formatear_cop(total_hormiga),
        'gastos_mes': gastos_mes,
        'gastos_mes_fmt': formatear_cop(gastos_mes),
        'porcentaje_mes': porcentaje_mes,
    }


def agrupar_categorias_gasto(gastos_qs):
    """Agrupa un queryset de gastos por categoría con porcentaje y metadata visual."""
    filas = list(
        gastos_qs.values('idCategoria', 'idCategoria__nombre')
        .annotate(total=Sum('monto'))
        .order_by('-total')
    )
    total_general = sum((item['total'] for item in filas), Decimal('0.00'))
    resultado = []
    for item in filas:
        nombre = item['idCategoria__nombre']
        total = item['total'] or Decimal('0.00')
        porcentaje = round(float(total / total_general) * 100) if total_general > 0 else 0
        resultado.append({
            'id': item['idCategoria'],
            'nombre': nombre,
            'total': total,
            'total_fmt': formatear_cop(total),
            'porcentaje': porcentaje,
            'ui': estilo_categoria(nombre),
        })
    return resultado, total_general


def serie_semanal_gastos(movimientos_qs, hoy):
    """Genera serie de 7 barras (L a D) de gastos de la semana actual."""
    lunes = hoy - timedelta(days=hoy.weekday())
    totales_por_dia = []
    for offset in range(7):
        dia = lunes + timedelta(days=offset)
        total = movimientos_qs.filter(
            tipo__iexact='gasto',
            fecha=dia
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        totales_por_dia.append((offset, dia, total))

    maximo = max((t for _, _, t in totales_por_dia), default=Decimal('0.00'))
    barras = []
    for offset, dia, total in totales_por_dia:
        altura = round(float(total / maximo) * 100) if maximo > 0 else 12
        barras.append({
            'letra': DIAS_SEMANA_INICIAL[offset],
            'fecha': dia,
            'total': total,
            'total_fmt': formatear_cop(total),
            'altura': max(14, altura) if total > 0 else 10,
            'vacia': total == 0,
            'destacada': dia == hoy or (maximo > 0 and total == maximo),
        })
    return barras


def enriquecer_metas(metas_qs):
    """Añade faltante, porcentaje acotado e icono visual a cada MetaAhorro."""
    lista = []
    for meta in metas_qs:
        objetivo = meta.objetivo or Decimal('0.00')
        acumulado = meta.acumulado or Decimal('0.00')
        faltante = max(objetivo - acumulado, Decimal('0.00'))
        if objetivo > 0:
            porcentaje = min(100, round(float(acumulado / objetivo) * 100))
        else:
            porcentaje = 0
        lista.append({
            'obj': meta,
            'idMeta': meta.idMeta,
            'nombre': meta.nombre,
            'categoria': meta.categoria,
            'objetivo': objetivo,
            'objetivo_fmt': formatear_cop(objetivo),
            'acumulado': acumulado,
            'acumulado_fmt': formatear_cop(acumulado),
            'faltante_fmt': formatear_cop(faltante),
            'porcentaje': porcentaje,
            'completada': faltante == 0 and objetivo > 0,
            'ui': estilo_categoria(meta.categoria or meta.nombre),
        })
    return lista
