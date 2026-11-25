"""Servicio de préstamos entre compañeros y gastos compartidos sin doble contabilización (RF-12)."""

from decimal import Decimal

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from finanzas.models import Categoria, GastoCompartido, Participante, Prestamo, Transaccion
from finanzas.services.categorias_service import (
    asegurar_categorias_base,
    obtener_categoria_accesible,
    obtener_estilo_categoria,
)
from finanzas.services.finanzas_service import CERO, formatear_cop


def _categoria_sistema(perfil, preferida_nombres):
    """Busca una categoría global adecuada para registrar reembolsos/liquidaciones."""
    asegurar_categorias_base()
    for nombre in preferida_nombres:
        cat = Categoria.objects.filter(
            Q(idUsuario__isnull=True) | Q(idUsuario=perfil),
            nombre__icontains=nombre,
        ).first()
        if cat is not None:
            return cat
    return Categoria.objects.filter(idUsuario__isnull=True).order_by('idCategoria').first()


def crear_prestamo_usuario(perfil, deudor, concepto, tipo, monto, fecha_limite=None):
    """Registra un préstamo informativo entre compañeros (sin alterar saldo automáticamente)."""
    deudor_c = (deudor or '').strip()
    concepto_c = (concepto or '').strip()
    if not deudor_c or not concepto_c or tipo not in ('Por cobrar', 'Por pagar'):
        raise ValueError('Completa los datos obligatorios del préstamo.')
    if monto <= CERO:
        raise ValueError('El monto del préstamo debe ser mayor a cero.')

    return Prestamo.objects.create(
        idUsuario=perfil,
        deudor=deudor_c[:100],
        concepto=concepto_c[:255],
        tipo=tipo,
        monto=monto,
        estado='Pendiente',
        fecha_limite=fecha_limite,
    )


def marcar_prestamo_pagado(perfil, prestamo_id, registrar_movimiento=False, hoy=None):
    """Marca un préstamo como pagado de forma idempotente; opcionalmente registra 1 movimiento único."""
    hoy = hoy or timezone.localdate()
    with transaction.atomic():
        prestamo = Prestamo.objects.get(idPrestamo=prestamo_id, idUsuario=perfil)
        if prestamo.estado == 'Pagado':
            return prestamo, False

        prestamo.estado = 'Pagado'
        prestamo.fecha_pago = hoy

        if registrar_movimiento and prestamo.transaccion_pago_id is None:
            es_cobro = prestamo.tipo == 'Por cobrar'
            cat = _categoria_sistema(
                perfil,
                ('Mesada', 'Ingreso', 'Otros') if es_cobro else ('Otros', 'Ocio'),
            )
            tx = Transaccion.objects.create(
                idUsuario=perfil,
                idCategoria=cat,
                monto=prestamo.monto,
                fecha=hoy,
                tipo='ingreso' if es_cobro else 'gasto',
                descripcion=(
                    f'{"Cobro" if es_cobro else "Pago"} préstamo ({prestamo.deudor}): '
                    f'{prestamo.concepto}'
                )[:255],
            )
            prestamo.transaccion_pago = tx

        prestamo.save(update_fields=['estado', 'fecha_pago', 'transaccion_pago'])
    return prestamo, True


def crear_gasto_compartido(
    perfil,
    categoria_id,
    descripcion,
    monto_total,
    mi_parte,
    fecha,
    participantes_lista,
    yo_pague_total=True,
    hoy=None,
):
    """Crea un gasto compartido ligado 1-a-1 a una sola Transaccion (sin doble contabilización).

    Contabilidad exacta:
    - Si yo_pague_total=True: se descuenta monto_total una sola vez ahora; cada reembolso de un
      participante crea exactamente un ingreso por su parteAportada.
    - Si yo_pague_total=False: solo se descuenta mi_parte una sola vez y los participantes
      quedan como referencia liquidada (sin reembolsos pendientes).
    """
    hoy = hoy or timezone.localdate()
    desc_c = (descripcion or '').strip()
    if not desc_c:
        raise ValueError('Ingresa una descripción para el gasto compartido.')
    if fecha is None or fecha > hoy:
        raise ValueError('La fecha del gasto compartido no puede ser futura.')

    categoria = obtener_categoria_accesible(perfil, categoria_id)
    if categoria is None:
        raise ValueError('Selecciona una categoría válida.')

    if monto_total < Decimal('100.00') or monto_total > Decimal('99999999.99'):
        raise ValueError('El monto total debe ser al menos $100 COP.')
    if mi_parte < CERO or mi_parte > monto_total:
        raise ValueError('Tu parte debe estar entre $0 y el monto total.')
    if not yo_pague_total and mi_parte < Decimal('100.00'):
        raise ValueError('Si otro amigo pagó el total, tu parte debe ser al menos $100 COP.')

    if not participantes_lista:
        raise ValueError('Agrega al menos un compañero participante.')

    participantes_limpios = []
    suma_amigos = CERO
    for nombre, aporte in participantes_lista:
        nm = (nombre or '').strip()
        if not nm:
            raise ValueError('Cada participante debe tener un nombre.')
        if aporte < Decimal('100.00') or aporte > monto_total:
            raise ValueError(f'El aporte de {nm} debe ser al menos $100 COP.')
        suma_amigos += aporte
        participantes_limpios.append((nm[:100], aporte))

    if (mi_parte + suma_amigos) != monto_total:
        raise ValueError(
            f'Tu parte (${formatear_cop(mi_parte)}) más los aportes de tus compañeros '
            f'(${formatear_cop(suma_amigos)}) deben sumar exactamente ${formatear_cop(monto_total)}.'
        )

    monto_transaccion = monto_total if yo_pague_total else mi_parte
    estado_inicial = 'Pendiente' if yo_pague_total else 'Liquidado'

    with transaction.atomic():
        tx = Transaccion.objects.create(
            idUsuario=perfil,
            idCategoria=categoria,
            monto=monto_transaccion,
            fecha=fecha,
            tipo='gasto',
            descripcion=f'{desc_c} (Compartido)'[:255],
        )
        gasto_comp = GastoCompartido.objects.create(
            idUsuario=perfil,
            idTransaccion=tx,
            descripcion=desc_c[:255],
            montoTotal=monto_total,
            mi_parte=mi_parte,
            yo_pague_total=bool(yo_pague_total),
            estado=estado_inicial,
            creado_en=fecha,
        )
        Participante.objects.bulk_create([
            Participante(
                idGastoComp=gasto_comp,
                nombreAmigo=nm,
                parteAportada=aporte,
                pagado=not yo_pague_total,
                fecha_pago=fecha if not yo_pague_total else None,
            )
            for nm, aporte in participantes_limpios
        ])
    return gasto_comp


def marcar_participante_pagado(perfil, participante_id, hoy=None):
    """Marca como pagada la parte de un participante y registra su reembolso 1 sola vez."""
    hoy = hoy or timezone.localdate()
    with transaction.atomic():
        part = (
            Participante.objects.select_related('idGastoComp', 'idGastoComp__idTransaccion')
            .get(idParticipante=participante_id, idGastoComp__idUsuario=perfil)
        )
        if part.pagado:
            return part, False

        gasto_comp = part.idGastoComp
        part.pagado = True
        part.fecha_pago = hoy

        if gasto_comp.yo_pague_total and part.transaccion_reembolso_id is None:
            cat_ingreso = _categoria_sistema(perfil, ('Mesada', 'Ingreso', 'Otros'))
            tx_reemb = Transaccion.objects.create(
                idUsuario=perfil,
                idCategoria=cat_ingreso,
                monto=part.parteAportada,
                fecha=hoy,
                tipo='ingreso',
                descripcion=f'Reembolso compartido: {gasto_comp.descripcion} ({part.nombreAmigo})'[:255],
            )
            part.transaccion_reembolso = tx_reemb

        part.save(update_fields=['pagado', 'fecha_pago', 'transaccion_reembolso'])

        pendientes = Participante.objects.filter(
            idGastoComp=gasto_comp,
            pagado=False,
        ).exists()
        if not pendientes and gasto_comp.estado != 'Liquidado':
            gasto_comp.estado = 'Liquidado'
            gasto_comp.save(update_fields=['estado'])

    return part, True


def obtener_resumen_compartidos_y_prestamos(perfil, hoy=None):
    """Resume préstamos y gastos compartidos del usuario sin duplicar totales."""
    hoy = hoy or timezone.localdate()

    prestamos_qs = Prestamo.objects.filter(idUsuario=perfil).order_by('estado', '-idPrestamo')
    total_por_cobrar = CERO
    total_por_pagar = CERO
    prestamos_vencidos = 0
    prestamos_ui = []
    for p in prestamos_qs:
        vencido = (
            p.estado == 'Pendiente'
            and p.fecha_limite is not None
            and p.fecha_limite < hoy
        )
        if p.estado == 'Pendiente':
            if p.tipo == 'Por cobrar':
                total_por_cobrar += p.monto
            else:
                total_por_pagar += p.monto
            if vencido:
                prestamos_vencidos += 1
        prestamos_ui.append({
            'obj': p,
            'idPrestamo': p.idPrestamo,
            'deudor': p.deudor,
            'concepto': p.concepto,
            'tipo': p.tipo,
            'monto': p.monto,
            'monto_fmt': formatear_cop(p.monto),
            'estado': p.estado,
            'fecha': p.fecha,
            'fecha_limite': p.fecha_limite,
            'fecha_pago': p.fecha_pago,
            'vencido': vencido,
            'con_movimiento': p.transaccion_pago_id is not None,
        })

    compartidos_qs = (
        GastoCompartido.objects.filter(
            Q(idUsuario=perfil) | Q(idTransaccion__idUsuario=perfil)
        )
        .select_related('idTransaccion', 'idTransaccion__idCategoria')
        .prefetch_related('participantes')
        .order_by('-creado_en', '-idGastoComp')
    )

    total_por_recuperar = CERO
    compartidos_pendientes_count = 0
    compartidos_ui = []

    for gc in compartidos_qs:
        parts = list(gc.participantes.all())
        pendiente = sum((pt.parteAportada for pt in parts if not pt.pagado), CERO)
        recuperado = sum((pt.parteAportada for pt in parts if pt.pagado), CERO)
        if gc.yo_pague_total and pendiente > CERO:
            total_por_recuperar += pendiente
            compartidos_pendientes_count += 1

        compartidos_ui.append({
            'obj': gc,
            'idGastoComp': gc.idGastoComp,
            'idTransaccion': gc.idTransaccion_id,
            'descripcion': gc.descripcion,
            'categoria': gc.idTransaccion.idCategoria.nombre,
            'ui': obtener_estilo_categoria(gc.idTransaccion.idCategoria),
            'fecha': gc.creado_en,
            'monto_total': gc.montoTotal,
            'monto_total_fmt': formatear_cop(gc.montoTotal),
            'mi_parte': gc.mi_parte,
            'mi_parte_fmt': formatear_cop(gc.mi_parte),
            'yo_pague_total': gc.yo_pague_total,
            'estado': gc.estado,
            'es_liquidado': gc.estado == 'Liquidado',
            'pendiente': pendiente,
            'pendiente_fmt': formatear_cop(pendiente),
            'recuperado': recuperado,
            'recuperado_fmt': formatear_cop(recuperado),
            'participantes': [
                {
                    'idParticipante': pt.idParticipante,
                    'nombreAmigo': pt.nombreAmigo,
                    'parte': pt.parteAportada,
                    'parte_fmt': formatear_cop(pt.parteAportada),
                    'pagado': pt.pagado,
                    'fecha_pago': pt.fecha_pago,
                    'con_reembolso': pt.transaccion_reembolso_id is not None,
                }
                for pt in parts
            ],
        })

    return {
        'prestamos': prestamos_qs,
        'prestamos_ui': prestamos_ui,
        'prestamos_pendientes_count': prestamos_qs.filter(estado='Pendiente').count(),
        'prestamos_vencidos_count': prestamos_vencidos,
        'total_por_cobrar': total_por_cobrar,
        'total_por_cobrar_fmt': formatear_cop(total_por_cobrar),
        'total_por_pagar': total_por_pagar,
        'total_por_pagar_fmt': formatear_cop(total_por_pagar),
        'gastos_compartidos': compartidos_ui,
        'compartidos_pendientes_count': compartidos_pendientes_count,
        'total_por_recuperar': total_por_recuperar,
        'total_por_recuperar_fmt': formatear_cop(total_por_recuperar),
    }
