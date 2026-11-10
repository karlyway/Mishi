
from django.shortcuts import render, redirect
from decimal import Decimal, InvalidOperation
from datetime import date, timedelta
from django.contrib.auth import get_user_model, login, authenticate
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone

from .models import Usuario, Transaccion, Categoria, MetaAhorro, Prestamo


# Página de presentación pública
def landing_view(request):
    return render(request, 'landing.html')


# Acceso de usuarios
def login_view(request):
    if request.method == 'POST':
        correo = request.POST.get('usuario', '').strip().lower()
        password = request.POST.get('password', '')

        usuario = authenticate(
            request,
            username=correo,
            password=password
        )

        if usuario is not None:
            login(request, usuario)
            return redirect('dashboard')

        return render(request, 'login.html', {
            'error': 'Correo o contraseña incorrectos.'
        })

    return render(request, 'login.html')


# Registro de usuarios
def registro_usuario_view(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        universidad = request.POST.get('universidad', '').strip()
        frecuencia = request.POST.get('frecuencia', 'quincenal')
        correo = request.POST.get('correo', '').strip().lower()
        password = request.POST.get('pass', '')
        mesada_texto = request.POST.get('mesada', '0').strip()

        User = get_user_model()

        if not nombre or not universidad or not correo or not password:
            return render(request, 'registro_usuario.html', {
                'error': 'Completa todos los campos obligatorios.'
            })

        try:
            mesada = Decimal(mesada_texto or '0')

            if not mesada.is_finite() or mesada < 0:
                raise InvalidOperation

        except InvalidOperation:
            return render(request, 'registro_usuario.html', {
                'error': 'Ingresa una mesada válida.'
            })

        if User.objects.filter(username=correo).exists():
            return render(request, 'registro_usuario.html', {
                'error': 'Este correo ya está registrado.'
            })

        try:
            with transaction.atomic():
                cuenta = User.objects.create_user(
                    username=correo,
                    email=correo,
                    password=password
                )

                Usuario.objects.create(
                    cuenta=cuenta,
                    nombre=nombre,
                    universidad=universidad,
                    frecuencia=frecuencia,
                    mesada=mesada
                )

            login(request, cuenta)
            return redirect('dashboard')

        except Exception:
            return render(request, 'registro_usuario.html', {
                'error': 'No se pudo crear la cuenta. Inténtalo nuevamente.'
            })

    return render(request, 'registro_usuario.html')


# Calcular días según frecuencia de ingreso
def calcular_dias_frecuencia(frecuencia):
    dias_por_frecuencia = {
        'diario': 1,
        'semanal': 7,
        'quincenal': 15,
        'mensual': 30,
    }

    return dias_por_frecuencia.get(frecuencia, 15)


# Panel principal
@login_required
def dashboard_view(request):

    perfil = Usuario.objects.filter(cuenta=request.user).first()

    if perfil is None:
        return redirect('login')

    movimientos = Transaccion.objects.filter(
        idUsuario=perfil
    ).select_related('idCategoria').order_by(
        '-fecha', '-idTransaccion'
    )

    ingresos = movimientos.filter(
        tipo__iexact='ingreso'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    gastos = movimientos.filter(
        tipo__iexact='gasto'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    saldo = perfil.mesada + ingresos - gastos

    dias = calcular_dias_frecuencia(perfil.frecuencia)
    limite_diario = round(saldo / dias) if saldo > 0 else 0

    hoy = timezone.localdate()

    fecha_inicio_periodo = hoy - timedelta(days=dias - 1)

    gasto_hoy = movimientos.filter(
    tipo__iexact='gasto',
    fecha__gte=fecha_inicio_periodo,
    fecha__lte=hoy
).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    porcentaje_gasto_hoy = (
        round(float(gasto_hoy / limite_diario) * 100, 2)
        if limite_diario > 0 else 0
        )

    limite_superado = (
    gasto_hoy >= limite_diario and limite_diario > 0
)

    # Últimos movimientos
    ultimos_movimientos = []

    for movimiento in movimientos[:4]:
        ultimos_movimientos.append({
            'fecha': movimiento.fecha,
            'titulo': movimiento.idCategoria.nombre,
            'categoria': movimiento.idCategoria.nombre,
            'tipo': movimiento.tipo.lower(),
            'monto': movimiento.monto,
            'es_hormiga': False,
            'es_compartido': False,
        })

    # Seleccionar periodo de estadísticas
    periodo = request.GET.get('periodo', 'semanal')

    if periodo not in ['semanal', 'mensual']:
        periodo = 'semanal'

    if periodo == 'semanal':
        fecha_inicio = hoy - timedelta(days=hoy.weekday())
    else:
        fecha_inicio = hoy.replace(day=1)

    movimientos_periodo = movimientos.filter(
        fecha__gte=fecha_inicio,
        fecha__lte=hoy
    )

    ingresos_periodo = movimientos_periodo.filter(
        tipo__iexact='ingreso'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    gastos_periodo = movimientos_periodo.filter(
        tipo__iexact='gasto'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    # Gastos por categoría
    gastos_categorias = movimientos_periodo.filter(
        tipo__iexact='gasto'
    ).values(
        'idCategoria__nombre'
    ).annotate(
        total=Sum('monto')
    ).order_by('idCategoria__nombre')

    etiquetas_categorias = [
        item['idCategoria__nombre']
        for item in gastos_categorias
    ]

    valores_categorias = [
        float(item['total'])
        for item in gastos_categorias
    ]

    context = {
        'usuario': perfil,
        'saldo': saldo,
        'dias_restantes': dias,
        'limite_diario': limite_diario,
        'gasto_hoy': gasto_hoy,
        'porcentaje_gasto_hoy': porcentaje_gasto_hoy,
        'alerta_activa': True,
        'limite_superado': limite_superado,
        'total_hormiga': 0,
        'ultimos_movimientos': ultimos_movimientos,
        'periodo': periodo,
        'ingresos_periodo': float(ingresos_periodo),
        'gastos_periodo': float(gastos_periodo),
        'etiquetas_categorias': etiquetas_categorias,
        'valores_categorias': valores_categorias,
        'pestana_activa': 'dashboard',
    }

    return render(request, 'dashboard.html', context)


# Registrar ingresos y gastos
@login_required
def movimiento_view(request):

    perfil = Usuario.objects.filter(cuenta=request.user).first()

    if perfil is None:
        return redirect('login')

    movimientos = Transaccion.objects.filter(idUsuario=perfil)

    ingresos = movimientos.filter(
        tipo__iexact='ingreso'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    gastos = movimientos.filter(
        tipo__iexact='gasto'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    saldo = perfil.mesada + ingresos - gastos

    dias = calcular_dias_frecuencia(perfil.frecuencia)
    limite_diario = round(saldo / dias) if saldo > 0 else 0

    categorias = Categoria.objects.all()

    if request.method == 'POST':
        tipo = request.POST.get('tipo', '').strip()
        monto_texto = request.POST.get('monto', '').strip()
        categoria_id = request.POST.get('categoria')
        descripcion = request.POST.get('descripcion', '').strip()
        fecha = request.POST.get('fecha', '').strip()

        try:
            if tipo not in ['gasto', 'ingreso']:
                raise ValueError

            monto = Decimal(monto_texto)

            if not monto.is_finite() or monto < 100:
                raise ValueError

            if monto.as_tuple().exponent < -2:
                raise ValueError

            categoria = Categoria.objects.get(
                idCategoria=categoria_id
            )

            fecha_movimiento = date.fromisoformat(fecha)

            if fecha_movimiento > timezone.localdate():
                raise ValueError

            Transaccion.objects.create(
                idUsuario=perfil,
                idCategoria=categoria,
                monto=monto,
                fecha=fecha_movimiento,
                tipo=tipo,
                descripcion=descripcion
            )

            messages.success(
                request,
                'Movimiento registrado correctamente.'
            )

            return redirect('dashboard')

        except (
            InvalidOperation,
            ValueError,
            TypeError,
            Categoria.DoesNotExist
        ):
            messages.error(
                request,
                'Verifica los datos. El monto mínimo es $100 y la fecha no puede ser futura.'
            )

            return render(request, 'registro.html', {
                'saldo': saldo,
                'dias_restantes': dias,
                'limite_diario': limite_diario,
                'categorias': categorias,
                'pestana_activa': 'movimiento'
            })

    return render(request, 'registro.html', {
        'saldo': saldo,
        'dias_restantes': dias,
        'limite_diario': limite_diario,
        'categorias': categorias,
        'pestana_activa': 'movimiento'
    })


# Historial de ingresos y gastos
@login_required
def historial_view(request):

    perfil = Usuario.objects.filter(cuenta=request.user).first()

    if perfil is None:
        return redirect('login')

    movimientos_db = Transaccion.objects.filter(
        idUsuario=perfil
    ).select_related('idCategoria').order_by(
        '-fecha', '-idTransaccion'
    )

    fecha_inicio = request.GET.get('fecha_inicio', '').strip()
    fecha_fin = request.GET.get('fecha_fin', '').strip()
    categoria_id = request.GET.get('categoria', '').strip()

    error_filtros = ''

    try:
        if fecha_inicio:
            inicio = date.fromisoformat(fecha_inicio)
            movimientos_db = movimientos_db.filter(fecha__gte=inicio)

        if fecha_fin:
            fin = date.fromisoformat(fecha_fin)
            movimientos_db = movimientos_db.filter(fecha__lte=fin)

        if fecha_inicio and fecha_fin:
            if inicio > fin:
                raise ValueError

    except ValueError:
        error_filtros = 'Verifica las fechas seleccionadas.'

        movimientos_db = Transaccion.objects.filter(
            idUsuario=perfil
        ).select_related('idCategoria').order_by(
            '-fecha', '-idTransaccion'
        )

    if categoria_id:
        if Categoria.objects.filter(idCategoria=categoria_id).exists():
            movimientos_db = movimientos_db.filter(
                idCategoria_id=categoria_id
            )
        else:
            error_filtros = 'La categoría seleccionada no es válida.'

    total_ingresos = movimientos_db.filter(
        tipo__iexact='ingreso'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    total_gastos = movimientos_db.filter(
        tipo__iexact='gasto'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    movimientos = []

    for m in movimientos_db:
        movimientos.append({
            'id': m.idTransaccion,
            'titulo': m.descripcion or m.idCategoria.nombre,
            'categoria': m.idCategoria.nombre,
            'tipo': m.tipo.lower(),
            'monto': m.monto,
            'fecha': m.fecha,
            'es_hormiga': False,
            'es_compartido': False,
        })

    context = {
        'movimientos': movimientos,
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'balance': total_ingresos - total_gastos,
        'categorias': Categoria.objects.all().order_by('nombre'),
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'categoria_seleccionada': categoria_id,
        'error_filtros': error_filtros,
        'pestana_activa': 'historial'
    }

    return render(request, 'historial.html', context)


# Editar movimiento
@login_required
def editar_movimiento_view(request, movimiento_id):

    perfil = Usuario.objects.filter(cuenta=request.user).first()

    if perfil is None:
        return redirect('login')

    movimiento = Transaccion.objects.filter(
        idTransaccion=movimiento_id,
        idUsuario=perfil
    ).first()

    if movimiento is None:
        return redirect('historial')

    categorias = Categoria.objects.all()

    if request.method == 'POST':
        try:
            tipo = request.POST.get('tipo')
            monto = Decimal(request.POST.get('monto', '0'))
            categoria_id = request.POST.get('categoria')
            descripcion = request.POST.get('descripcion', '').strip()
            fecha = request.POST.get('fecha')

            if (
                tipo not in ['gasto', 'ingreso']
                or not monto.is_finite()
                or monto < 100
                or not fecha
            ):
                raise ValueError

            fecha_movimiento = date.fromisoformat(fecha)

            if fecha_movimiento > timezone.localdate():
                raise ValueError

            categoria = Categoria.objects.get(
                idCategoria=categoria_id
            )

            movimiento.tipo = tipo
            movimiento.monto = monto
            movimiento.idCategoria = categoria
            movimiento.descripcion = descripcion
            movimiento.fecha = fecha_movimiento
            movimiento.save()

            messages.success(
                request,
                'Movimiento actualizado correctamente.'
            )

            return redirect('historial')

        except (
            InvalidOperation,
            ValueError,
            TypeError,
            Categoria.DoesNotExist
        ):
            return render(request, 'editar_movimiento.html', {
                'movimiento': movimiento,
                'categorias': categorias,
                'error': 'Verifica los datos ingresados.',
                'pestana_activa': 'historial'
            })

    return render(request, 'editar_movimiento.html', {
        'movimiento': movimiento,
        'categorias': categorias,
        'pestana_activa': 'historial'
    })


# Eliminar movimiento
@login_required
def eliminar_movimiento_view(request, movimiento_id):

    perfil = Usuario.objects.filter(cuenta=request.user).first()

    if perfil is None:
        return redirect('login')

    if request.method == 'POST':
        movimiento = Transaccion.objects.filter(
            idTransaccion=movimiento_id,
            idUsuario=perfil
        )

        if movimiento.exists():
            movimiento.delete()
            messages.success(
                request,
                'Movimiento eliminado correctamente.'
            )
        else:
            messages.error(
                request,
                'No se encontró el movimiento.'
            )

    return redirect('historial')


# Metas de ahorro y préstamos
@login_required
def metas_view(request):

    perfil = Usuario.objects.filter(cuenta=request.user).first()

    if perfil is None:
        return redirect('login')

    if request.method == 'POST':
        accion = request.POST.get('accion')

        try:
            if accion == 'crear_meta':
                nombre = request.POST.get('nombre', '').strip()
                categoria = request.POST.get('categoria', '').strip()
                objetivo = Decimal(request.POST.get('objetivo', '0'))

                if not nombre or not objetivo.is_finite() or objetivo <= 0:
                    raise ValueError

                MetaAhorro.objects.create(
                    idUsuario=perfil,
                    nombre=nombre,
                    categoria=categoria or 'General',
                    objetivo=objetivo
                )

                messages.success(
                    request,
                    'Meta de ahorro creada correctamente.'
                )

            elif accion == 'actualizar_meta':
                meta_id = request.POST.get('meta_id')
                ahorro = Decimal(request.POST.get('ahorro', '0'))

                if not ahorro.is_finite() or ahorro <= 0:
                    raise ValueError

                meta = MetaAhorro.objects.get(
                    idMeta=meta_id,
                    idUsuario=perfil
                )

                meta.acumulado += ahorro
                meta.save()

                messages.success(
                    request,
                    'Ahorro agregado correctamente.'
                )

            elif accion == 'crear_prestamo':
                deudor = request.POST.get('deudor', '').strip()
                concepto = request.POST.get('concepto', '').strip()
                tipo = request.POST.get('tipo', 'Por cobrar')
                monto = Decimal(request.POST.get('monto', '0'))

                if (
                    not deudor
                    or not concepto
                    or not monto.is_finite()
                    or monto <= 0
                ):
                    raise ValueError

                Prestamo.objects.create(
                    idUsuario=perfil,
                    deudor=deudor,
                    concepto=concepto,
                    tipo=tipo,
                    monto=monto,
                    estado='Pendiente'
                )

                messages.success(
                    request,
                    'Préstamo registrado correctamente.'
                )

            elif accion == 'pagar_prestamo':
                prestamo_id = request.POST.get('prestamo_id')

                prestamo = Prestamo.objects.get(
                    idPrestamo=prestamo_id,
                    idUsuario=perfil
                )

                prestamo.estado = 'Pagado'
                prestamo.save()

                messages.success(
                    request,
                    'Préstamo marcado como pagado.'
                )

            else:
                messages.error(request, 'Acción no válida.')

            return redirect('metas')

        except (
            ValueError,
            InvalidOperation,
            MetaAhorro.DoesNotExist,
            Prestamo.DoesNotExist
        ):
            messages.error(
                request,
                'Verifica los datos ingresados.'
            )

    metas = MetaAhorro.objects.filter(idUsuario=perfil)
    prestamos = Prestamo.objects.filter(idUsuario=perfil)

    context = {
        'metas': metas,
        'prestamos': prestamos,
        'pestana_activa': 'metas'
    }

    return render(request, 'metas.html', context)
