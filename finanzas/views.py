from django.shortcuts import render, redirect


from decimal import Decimal, InvalidOperation
from django.contrib.auth import get_user_model, login, authenticate
from django.db import transaction
from django.contrib import messages
from .models import Usuario, Transaccion, Categoria, MetaAhorro, Prestamo
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone

# Pagina de presentacion publica
def landing_view(request):
    return render(request, 'landing.html')


# Formulario de acceso de usuarios
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


# Formulario para registro de nuevos estudiantes
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
            if mesada < 0:
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


# Panel principal: calculo del limite diario segun saldo y dias restantes
@login_required
def dashboard_view(request):
    perfil = Usuario.objects.filter(cuenta=request.user).first()

    if perfil is None:
        return redirect('login')

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

    dias = 15 if perfil.frecuencia == 'quincenal' else 30
    limite_diario = round(saldo / dias) if saldo > 0 else 0

    hoy = timezone.localdate()

    gasto_hoy = movimientos.filter(
        tipo__iexact='gasto',
        fecha=hoy
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    porcentaje_gasto_hoy = min(
        round((gasto_hoy / limite_diario) * 100), 100
    ) if limite_diario > 0 else 100

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

    context = {
        'usuario': perfil,
        'saldo': saldo,
        'dias_restantes': dias,
        'limite_diario': limite_diario,
        'gasto_hoy': gasto_hoy,
        'porcentaje_gasto_hoy': porcentaje_gasto_hoy,
        'alerta_activa': porcentaje_gasto_hoy >= 80,
        'total_hormiga': 0,
        'ultimos_movimientos': ultimos_movimientos,
        'pestana_activa': 'dashboard',
    }

    return render(request, 'dashboard.html', context)


# Vista para agregar un movimiento (ingreso o gasto)
@login_required
def movimiento_view(request):
    perfil = Usuario.objects.filter(cuenta=request.user).first()

    if perfil is None:
        return redirect('login')

    movimientos = Transaccion.objects.filter(idUsuario=perfil)

    ingresos = movimientos.filter(tipo__iexact='ingreso').aggregate(
        total=Sum('monto')
    )['total'] or Decimal('0.00')

    gastos = movimientos.filter(tipo__iexact='gasto').aggregate(
        total=Sum('monto')
    )['total'] or Decimal('0.00')

    saldo = perfil.mesada + ingresos - gastos
    dias = 15 if perfil.frecuencia == 'quincenal' else 30
    limite_diario = round(saldo / dias) if saldo > 0 else 0

    categorias = Categoria.objects.all()

    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        monto_texto = request.POST.get('monto', '').strip()
        categoria_id = request.POST.get('categoria')
        descripcion = request.POST.get('descripcion', '').strip()
        fecha = request.POST.get('fecha')

        try:
            monto = Decimal(monto_texto)

            if monto <= 0:
                raise InvalidOperation

            categoria = Categoria.objects.get(idCategoria=categoria_id)

            Transaccion.objects.create(
                idUsuario=perfil,
                idCategoria=categoria,
                monto=monto,
                fecha=fecha,
                tipo=tipo,
                descripcion=descripcion
            )

            return redirect('dashboard')

        except (InvalidOperation, ValueError, TypeError, Categoria.DoesNotExist):
            return render(request, 'registro.html', {
                'saldo': saldo,
                'dias_restantes': dias,
                'limite_diario': limite_diario,
                'categorias': categorias,
                'error': 'Verifica los datos del movimiento.'
            })

    return render(request, 'registro.html', {
        'saldo': saldo,
        'dias_restantes': dias,
        'limite_diario': limite_diario,
        'categorias': categorias,
        'pestana_activa': 'movimiento'
    })

# Historial de gastos e ingresos registrados
@login_required
def historial_view(request):
    perfil = Usuario.objects.filter(cuenta=request.user).first()

    if perfil is None:
        return redirect('login')

    movimientos_db = Transaccion.objects.filter(
        idUsuario=perfil
    ).select_related('idCategoria').order_by('-fecha', '-idTransaccion')

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
        'pestana_activa': 'historial'
    }

    return render(request, 'historial.html', context)


# Visualizacion de metas de ahorro y deudas pendientes
@login_required
@login_required

@login_required

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

                if not nombre or objetivo <= 0:
                    raise ValueError

                MetaAhorro.objects.create(
                    idUsuario=perfil,
                    nombre=nombre,
                    categoria=categoria or 'General',
                    objetivo=objetivo
                )

            elif accion == 'actualizar_meta':
                meta_id = request.POST.get('meta_id')
                ahorro = Decimal(request.POST.get('ahorro', '0'))

                if ahorro <= 0:
                    raise ValueError

                meta = MetaAhorro.objects.get(
                    idMeta=meta_id,
                    idUsuario=perfil
                )
                meta.acumulado += ahorro
                meta.save()

            elif accion == 'crear_prestamo':
                deudor = request.POST.get('deudor', '').strip()
                concepto = request.POST.get('concepto', '').strip()
                tipo = request.POST.get('tipo', 'Por cobrar')
                monto = Decimal(request.POST.get('monto', '0'))

                if not deudor or not concepto or monto <= 0:
                    raise ValueError

                Prestamo.objects.create(
                    idUsuario=perfil,
                    deudor=deudor,
                    concepto=concepto,
                    tipo=tipo,
                    monto=monto,
                    estado='Pendiente'
                )

            elif accion == 'pagar_prestamo':
                prestamo_id = request.POST.get('prestamo_id')

                prestamo = Prestamo.objects.get(
                    idPrestamo=prestamo_id,
                    idUsuario=perfil
                )
                prestamo.estado = 'Pagado'
                prestamo.save()

            return redirect('metas')

        except (
            ValueError,
            InvalidOperation,
            MetaAhorro.DoesNotExist,
            Prestamo.DoesNotExist
        ):
            messages.error(request, 'Verifica los datos ingresados.')

    metas = MetaAhorro.objects.filter(idUsuario=perfil)
    prestamos = Prestamo.objects.filter(idUsuario=perfil)

    context = {
        'metas': metas,
        'prestamos': prestamos,
        'pestana_activa': 'metas'
    }

    return render(request, 'metas.html', context)
