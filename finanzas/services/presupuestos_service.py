"""Presupuestos mensuales reales por categoría (RF-11)."""

from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from finanzas.models import Categoria, PresupuestoCategoria, Transaccion
from finanzas.services.categorias_service import (
    obtener_categoria_accesible,
    obtener_estilo_categoria,
)
from finanzas.services.finanzas_service import CERO, formatear_cop


def calcular_presupuestos_categoria(perfil, hoy=None):
    """Calcula consumo real del mes actual frente a los límites configurados por categoría."""
    hoy = hoy or timezone.localdate()
    inicio_mes = hoy.replace(day=1)

    gastos_por_cat = {
        row['idCategoria']: row['total'] or CERO
        for row in Transaccion.objects.filter(
            idUsuario=perfil,
            tipo__iexact='gasto',
            fecha__gte=inicio_mes,
            fecha__lte=hoy,
        )
        .values('idCategoria')
        .annotate(total=Sum('monto'))
    }

    presupuestos_qs = (
        PresupuestoCategoria.objects.filter(idUsuario=perfil)
        .select_related('idCategoria')
        .order_by('idCategoria__nombre')
    )

    configurados = []
    ids_configurados = set()
    total_asignado = CERO
    excedidas_count = 0
    preventivas_count = 0

    for pc in presupuestos_qs:
        cat = pc.idCategoria
        ids_configurados.add(cat.idCategoria)
        gastado = gastos_por_cat.get(cat.idCategoria, CERO)
        tope = pc.limiteMensual or CERO
        total_asignado += tope

        disponible = max(tope - gastado, CERO)
        excedente = max(gastado - tope, CERO)
        pct_real = round(float((gastado / tope) * Decimal('100'))) if tope > CERO else 0
        pct_barra = min(100, pct_real)
        excedido = tope > CERO and gastado > tope
        cerca = (not excedido) and pct_real >= 80

        if excedido:
            estado = 'excedido'
            excedidas_count += 1
        elif cerca:
            estado = 'preventivo'
            preventivas_count += 1
        else:
            estado = 'ok'

        configurados.append({
            'idPresupuestoCat': pc.idPresupuestoCat,
            'idCategoria': cat.idCategoria,
            'nombre': cat.nombre,
            'gastado': gastado,
            'gastado_fmt': formatear_cop(gastado),
            'tope': tope,
            'tope_val': int(tope),
            'tope_fmt': formatear_cop(tope),
            'disponible': disponible,
            'disponible_fmt': formatear_cop(disponible),
            'excedente': excedente,
            'excedente_fmt': formatear_cop(excedente),
            'porcentaje': pct_barra,
            'porcentaje_real': pct_real,
            'excedido': excedido,
            'cerca': cerca,
            'estado': estado,
            'ui': obtener_estilo_categoria(cat),
        })

    # Ordenar primero los críticos/más consumidos
    configurados.sort(key=lambda item: (-item['porcentaje_real'], -item['gastado']))

    # Categorías con gastos reales del mes pero sin tope asignado (sin inventar límites)
    sin_tope_ids = [cid for cid, total in gastos_por_cat.items() if total > CERO and cid not in ids_configurados]
    sin_presupuesto = []
    if sin_tope_ids:
        cats_map = {
            c.idCategoria: c
            for c in Categoria.objects.filter(idCategoria__in=sin_tope_ids)
        }
        for cid in sorted(sin_tope_ids, key=lambda x: -gastos_por_cat[x]):
            cat = cats_map.get(cid)
            if cat is None:
                continue
            gastado = gastos_por_cat[cid]
            sin_presupuesto.append({
                'idCategoria': cat.idCategoria,
                'nombre': cat.nombre,
                'gastado': gastado,
                'gastado_fmt': formatear_cop(gastado),
                'ui': obtener_estilo_categoria(cat),
            })

    return {
        'presupuestos_configurados': configurados,
        'categorias_sin_presupuesto': sin_presupuesto,
        'total_asignado': total_asignado,
        'total_asignado_fmt': formatear_cop(total_asignado),
        'excedidas_count': excedidas_count,
        'preventivas_count': preventivas_count,
    }


def guardar_presupuesto_categoria(perfil, categoria_id, limite_mensual):
    """Crea o actualiza el tope mensual real para una categoría accesible del usuario."""
    categoria = obtener_categoria_accesible(perfil, categoria_id)
    if categoria is None:
        raise ValueError('La categoría seleccionada no es válida.')
    if limite_mensual < Decimal('1000.00') or limite_mensual > Decimal('99999999.99'):
        raise ValueError('El presupuesto por categoría debe ser al menos $1.000 COP.')

    obj, _ = PresupuestoCategoria.objects.update_or_create(
        idUsuario=perfil,
        idCategoria=categoria,
        defaults={'limiteMensual': limite_mensual},
    )
    return obj


def eliminar_presupuesto_categoria(perfil, presupuesto_cat_id):
    """Elimina un presupuesto por categoría perteneciente al usuario."""
    eliminados, _ = PresupuestoCategoria.objects.filter(
        idPresupuestoCat=presupuesto_cat_id,
        idUsuario=perfil,
    ).delete()
    return eliminados > 0
