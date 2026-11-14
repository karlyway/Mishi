from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import Categoria, MetaAhorro, Presupuesto, Prestamo, Transaccion, Usuario
from .ui_helpers import (
    agrupar_categorias_gasto,
    calcular_dias_frecuencia,
    calcular_resumen_usuario,
    enriquecer_metas,
    estilo_categoria,
    formatear_cop,
    serie_semanal_gastos,
)


CATEGORIAS_POR_DEFECTO = [
    'Alimentación',
    'Transporte',
    'Universidad',
    'Ocio',
    'Hogar',
    'Salud',
    'Mesada / Ingreso',
    'Otros',
]


def _obtener_perfil_autenticado(request):
    return Usuario.objects.filter(cuenta=request.user).first()


def _validar_monto_positivo(texto, minimo=Decimal('100')):
    monto = Decimal(texto)
    if not monto.is_finite() or monto < minimo or monto.as_tuple().exponent < -2:
        raise ValueError
    return monto


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

        if frecuencia not in ['diario', 'semanal', 'quincenal', 'mensual']:
            return render(request, 'registro_usuario.html', {
                'error': 'Selecciona una frecuencia válida.'
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


def obtener_categorias():
    if not Categoria.objects.exists():
        for nombre in CATEGORIAS_POR_DEFECTO:
            Categoria.objects.get_or_create(nombre=nombre)
    return Categoria.objects.all().order_by('idCategoria')


def _categorias_con_ui(categorias):
    return [
        {
            'idCategoria': c.idCategoria,
            'nombre': c.nombre,
            'ui': estilo_categoria(c.nombre),
        }
        for c in categorias
    ]


# Pantalla Inicio (App Home)
@login_required
def dashboard_view(request):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')

    resumen = calcular_resumen_usuario(perfil)
    movimientos = resumen['movimientos']
    hoy = resumen['hoy']

    ultimos_movimientos = []
    for mov in movimientos[:4]:
        es_hormiga = (
            mov.tipo.lower() == 'gasto'
            and mov.monto <= Decimal('15000.00')
        )
        ultimos_movimientos.append({
            'id': mov.idTransaccion,
            'fecha': mov.fecha,
            'titulo': mov.descripcion or mov.idCategoria.nombre,
            'categoria': mov.idCategoria.nombre,
            'tipo': mov.tipo.lower(),
            'monto': mov.monto,
            'monto_fmt': formatear_cop(mov.monto),
            'es_hormiga': es_hormiga,
            'es_compartido': False,
            'ui': estilo_categoria(mov.idCategoria.nombre),
        })

    periodo = request.GET.get('periodo', 'semanal')
    if periodo not in ['semanal', 'mensual']:
        periodo = 'semanal'

    fecha_inicio = hoy - timedelta(days=hoy.weekday()) if periodo == 'semanal' else hoy.replace(day=1)
    movimientos_periodo = movimientos.filter(fecha__gte=fecha_inicio, fecha__lte=hoy)

    ingresos_periodo = movimientos_periodo.filter(
        tipo__iexact='ingreso'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    gastos_periodo = movimientos_periodo.filter(
        tipo__iexact='gasto'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    gastos_categorias = movimientos_periodo.filter(
        tipo__iexact='gasto'
    ).values('idCategoria__nombre').annotate(total=Sum('monto')).order_by('idCategoria__nombre')

    etiquetas_categorias = [item['idCategoria__nombre'] for item in gastos_categorias]
    valores_categorias = [float(item['total']) for item in gastos_categorias]

    gastos_mes_qs = movimientos.filter(
        tipo__iexact='gasto',
        fecha__gte=hoy.replace(day=1),
        fecha__lte=hoy
    )
    categorias_resumen, _ = agrupar_categorias_gasto(gastos_mes_qs)

    context = {
        'usuario': perfil,
        'saldo': resumen['saldo'],
        'saldo_fmt': resumen['saldo_fmt'],
        'dias_restantes': resumen['dias_restantes'],
        'limite_diario': resumen['limite_diario'],
        'limite_diario_fmt': resumen['limite_diario_fmt'],
        'gasto_hoy': resumen['gasto_hoy'],
        'gasto_hoy_fmt': resumen['gasto_hoy_fmt'],
        'porcentaje_gasto_hoy': resumen['porcentaje_gasto_hoy'],
        'alerta_activa': resumen['alerta_activa'],
        'limite_superado': resumen['limite_superado'],
        'total_hormiga': resumen['total_hormiga'],
        'total_hormiga_fmt': resumen['total_hormiga_fmt'],
        'gastos_mes': resumen['gastos_mes'],
        'gastos_mes_fmt': resumen['gastos_mes_fmt'],
        'porcentaje_mes': resumen['porcentaje_mes'],
        'categorias_resumen': categorias_resumen[:4],
        'ultimos_movimientos': ultimos_movimientos,
        'periodo': periodo,
        'ingresos_periodo': float(ingresos_periodo),
        'gastos_periodo': float(gastos_periodo),
        'etiquetas_categorias': etiquetas_categorias,
        'valores_categorias': valores_categorias,
        'pestana_activa': 'dashboard',
    }
    return render(request, 'dashboard.html', context)


# Pantalla Nuevo Gasto / Ingreso
@login_required
def movimiento_view(request):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')

    resumen = calcular_resumen_usuario(perfil)
    categorias = obtener_categorias()
    categorias_ui = _categorias_con_ui(categorias)

    if request.method == 'POST':
        tipo = request.POST.get('tipo', '').strip()
        monto_texto = request.POST.get('monto', '').strip()
        categoria_id = request.POST.get('categoria')
        descripcion = request.POST.get('descripcion', '').strip()
        fecha = request.POST.get('fecha', '').strip()

        try:
            if tipo not in ['gasto', 'ingreso']:
                raise ValueError

            monto = _validar_monto_positivo(monto_texto, Decimal('100'))
            categoria = Categoria.objects.get(idCategoria=categoria_id)
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

            messages.success(request, 'Movimiento registrado correctamente.')
            return redirect('dashboard')

        except (InvalidOperation, ValueError, TypeError, Categoria.DoesNotExist):
            messages.error(
                request,
                'Verifica los datos. El monto mínimo es $100 y la fecha no puede ser futura.'
            )

    return render(request, 'registro.html', {
        'usuario': perfil,
        'saldo': resumen['saldo'],
        'saldo_fmt': resumen['saldo_fmt'],
        'dias_restantes': resumen['dias_restantes'],
        'limite_diario': resumen['limite_diario'],
        'limite_diario_fmt': resumen['limite_diario_fmt'],
        'categorias': categorias,
        'categorias_ui': categorias_ui,
        'pestana_activa': 'movimiento',
    })


# Pantalla Gastos / Historial
@login_required
def historial_view(request):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')

    movimientos_base = Transaccion.objects.filter(
        idUsuario=perfil
    ).select_related('idCategoria').order_by('-fecha', '-idTransaccion')

    movimientos_db = movimientos_base
    hoy = timezone.localdate()

    rango = request.GET.get('rango', '').strip()
    if rango not in ['mes', '3m', 'todos']:
        rango = ''

    fecha_inicio = request.GET.get('fecha_inicio', '').strip()
    fecha_fin = request.GET.get('fecha_fin', '').strip()
    categoria_id = request.GET.get('categoria', '').strip()
    error_filtros = ''

    if not fecha_inicio and not fecha_fin:
        if rango == 'mes':
            movimientos_db = movimientos_db.filter(fecha__gte=hoy.replace(day=1))
        elif rango == '3m':
            movimientos_db = movimientos_db.filter(fecha__gte=hoy - timedelta(days=90))

    try:
        if fecha_inicio:
            inicio = date.fromisoformat(fecha_inicio)
            movimientos_db = movimientos_db.filter(fecha__gte=inicio)

        if fecha_fin:
            fin = date.fromisoformat(fecha_fin)
            movimientos_db = movimientos_db.filter(fecha__lte=fin)

        if fecha_inicio and fecha_fin and inicio > fin:
            raise ValueError

    except ValueError:
        error_filtros = 'Verifica las fechas seleccionadas.'
        movimientos_db = movimientos_base

    if categoria_id:
        if categoria_id.isdigit() and Categoria.objects.filter(idCategoria=int(categoria_id)).exists():
            movimientos_db = movimientos_db.filter(idCategoria_id=int(categoria_id))
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
        es_hormiga = (
            m.tipo.lower() == 'gasto'
            and m.monto <= Decimal('15000.00')
        )
        movimientos.append({
            'id': m.idTransaccion,
            'titulo': m.descripcion or m.idCategoria.nombre,
            'categoria': m.idCategoria.nombre,
            'tipo': m.tipo.lower(),
            'monto': m.monto,
            'monto_fmt': formatear_cop(m.monto),
            'fecha': m.fecha,
            'es_hormiga': es_hormiga,
            'es_compartido': False,
            'ui': estilo_categoria(m.idCategoria.nombre),
        })

    context = {
        'usuario': perfil,
        'movimientos': movimientos,
        'total_ingresos': total_ingresos,
        'total_ingresos_fmt': formatear_cop(total_ingresos),
        'total_gastos': total_gastos,
        'total_gastos_fmt': formatear_cop(total_gastos),
        'balance': total_ingresos - total_gastos,
        'balance_fmt': formatear_cop(total_ingresos - total_gastos),
        'barras_semana': serie_semanal_gastos(movimientos_base, hoy),
        'categorias': obtener_categorias(),
        'rango': rango or 'mes',
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'categoria_seleccionada': categoria_id,
        'filtros_activos': bool(fecha_inicio or fecha_fin or categoria_id or error_filtros),
        'error_filtros': error_filtros,
        'pestana_activa': 'historial',
    }
    return render(request, 'historial.html', context)


# Pantalla Detalle de Gasto / Movimiento
@login_required
def detalle_movimiento_view(request, movimiento_id):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')

    movimiento = Transaccion.objects.filter(
        idTransaccion=movimiento_id,
        idUsuario=perfil
    ).select_related('idCategoria').first()

    if movimiento is None:
        return redirect('historial')

    es_hormiga = (
        movimiento.tipo.lower() == 'gasto'
        and movimiento.monto <= Decimal('15000.00')
    )
    return render(request, 'detalle_movimiento.html', {
        'usuario': perfil,
        'movimiento': movimiento,
        'monto_fmt': formatear_cop(movimiento.monto),
        'ui': estilo_categoria(movimiento.idCategoria.nombre),
        'es_hormiga': es_hormiga,
        'pestana_activa': 'historial',
    })


# Editar movimiento
@login_required
def editar_movimiento_view(request, movimiento_id):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')

    movimiento = Transaccion.objects.filter(
        idTransaccion=movimiento_id,
        idUsuario=perfil
    ).first()

    if movimiento is None:
        return redirect('historial')

    categorias = obtener_categorias()

    if request.method == 'POST':
        try:
            tipo = request.POST.get('tipo')
            monto_texto = request.POST.get('monto', '0')
            categoria_id = request.POST.get('categoria')
            descripcion = request.POST.get('descripcion', '').strip()
            fecha = request.POST.get('fecha')

            if tipo not in ['gasto', 'ingreso'] or not fecha:
                raise ValueError

            monto = _validar_monto_positivo(monto_texto, Decimal('100'))
            fecha_movimiento = date.fromisoformat(fecha)

            if fecha_movimiento > timezone.localdate():
                raise ValueError

            categoria = Categoria.objects.get(idCategoria=categoria_id)

            movimiento.tipo = tipo
            movimiento.monto = monto
            movimiento.idCategoria = categoria
            movimiento.descripcion = descripcion
            movimiento.fecha = fecha_movimiento
            movimiento.save()

            messages.success(request, 'Movimiento actualizado correctamente.')
            return redirect('historial')

        except (InvalidOperation, ValueError, TypeError, Categoria.DoesNotExist):
            return render(request, 'editar_movimiento.html', {
                'usuario': perfil,
                'movimiento': movimiento,
                'categorias': categorias,
                'error': 'Verifica los datos ingresados.',
                'pestana_activa': 'historial',
            })

    return render(request, 'editar_movimiento.html', {
        'usuario': perfil,
        'movimiento': movimiento,
        'categorias': categorias,
        'pestana_activa': 'historial',
    })


# Eliminar movimiento
@login_required
def eliminar_movimiento_view(request, movimiento_id):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')

    if request.method == 'POST':
        movimiento = Transaccion.objects.filter(
            idTransaccion=movimiento_id,
            idUsuario=perfil
        )

        if movimiento.exists():
            movimiento.delete()
            messages.success(request, 'Movimiento eliminado correctamente.')
        else:
            messages.error(request, 'No se encontró el movimiento.')

    return redirect('historial')


# Metas de ahorro y préstamos
@login_required
def metas_view(request):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')

    if request.method == 'POST':
        accion = request.POST.get('accion')

        try:
            if accion == 'crear_meta':
                nombre = request.POST.get('nombre', '').strip()
                categoria = request.POST.get('categoria', '').strip()
                objetivo = _validar_monto_positivo(request.POST.get('objetivo', '0'), Decimal('0.01'))

                if not nombre:
                    raise ValueError

                MetaAhorro.objects.create(
                    idUsuario=perfil,
                    nombre=nombre,
                    categoria=categoria or 'General',
                    objetivo=objetivo
                )
                messages.success(request, 'Meta de ahorro creada correctamente.')

            elif accion == 'actualizar_meta':
                meta_id = request.POST.get('meta_id')
                ahorro = _validar_monto_positivo(request.POST.get('ahorro', '0'), Decimal('0.01'))
                meta = MetaAhorro.objects.get(idMeta=meta_id, idUsuario=perfil)
                meta.acumulado += ahorro
                meta.save()
                messages.success(request, 'Ahorro agregado correctamente.')

            elif accion == 'crear_prestamo':
                deudor = request.POST.get('deudor', '').strip()
                concepto = request.POST.get('concepto', '').strip()
                tipo = request.POST.get('tipo', 'Por cobrar')
                monto = _validar_monto_positivo(request.POST.get('monto', '0'), Decimal('0.01'))

                if not deudor or not concepto or tipo not in ['Por cobrar', 'Por pagar']:
                    raise ValueError

                Prestamo.objects.create(
                    idUsuario=perfil,
                    deudor=deudor,
                    concepto=concepto,
                    tipo=tipo,
                    monto=monto,
                    estado='Pendiente'
                )
                messages.success(request, 'Préstamo registrado correctamente.')

            elif accion == 'pagar_prestamo':
                prestamo_id = request.POST.get('prestamo_id')
                prestamo = Prestamo.objects.get(idPrestamo=prestamo_id, idUsuario=perfil)
                prestamo.estado = 'Pagado'
                prestamo.save()
                messages.success(request, 'Préstamo marcado como pagado.')

            else:
                messages.error(request, 'Acción no válida.')

            return redirect('metas')

        except (ValueError, InvalidOperation, MetaAhorro.DoesNotExist, Prestamo.DoesNotExist):
            messages.error(request, 'Verifica los datos ingresados.')

    metas = MetaAhorro.objects.filter(idUsuario=perfil).order_by('-idMeta')
    prestamos = Prestamo.objects.filter(idUsuario=perfil).order_by('estado', '-idPrestamo')

    context = {
        'usuario': perfil,
        'metas': metas,
        'metas_ui': enriquecer_metas(metas),
        'prestamos': prestamos,
        'pestana_activa': 'metas',
    }
    return render(request, 'metas.html', context)


# Pantalla Crear Meta (dedicada, conectada al botón + de Metas)
@login_required
def crear_meta_view(request):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')

    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre', '').strip()
            categoria = request.POST.get('categoria', '').strip()
            objetivo = _validar_monto_positivo(request.POST.get('objetivo', '0'), Decimal('0.01'))

            if not nombre:
                raise ValueError

            MetaAhorro.objects.create(
                idUsuario=perfil,
                nombre=nombre,
                categoria=categoria or 'General',
                objetivo=objetivo
            )
            messages.success(request, 'Meta de ahorro creada correctamente.')
            return redirect('metas')

        except (ValueError, InvalidOperation):
            messages.error(request, 'Completa el nombre y un monto objetivo válido.')

    return render(request, 'crear_meta.html', {
        'usuario': perfil,
        'pestana_activa': 'metas',
    })


# Pantalla Categorías (Donut + desglose por porcentaje)
@login_required
def categorias_view(request):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')

    hoy = timezone.localdate()
    rango = request.GET.get('rango', 'mes')
    if rango not in ['mes', '3m']:
        rango = 'mes'

    desde = hoy.replace(day=1) if rango == 'mes' else hoy - timedelta(days=90)
    gastos_qs = Transaccion.objects.filter(
        idUsuario=perfil,
        tipo__iexact='gasto',
        fecha__gte=desde,
        fecha__lte=hoy
    )
    categorias_gasto, total_gastado = agrupar_categorias_gasto(gastos_qs)

    return render(request, 'categorias.html', {
        'usuario': perfil,
        'rango': rango,
        'categorias_gasto': categorias_gasto,
        'total_gastado_fmt': formatear_cop(total_gastado),
        'etiquetas_json': [c['nombre'] for c in categorias_gasto],
        'valores_json': [float(c['total']) for c in categorias_gasto],
        'colores_json': [c['ui']['color'] for c in categorias_gasto],
        'pestana_activa': 'historial',
    })


# Pantalla Mis Insights (Alertas inteligentes, hormiga y comparativo mensual)
@login_required
def insights_view(request):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')

    resumen = calcular_resumen_usuario(perfil)
    hoy = resumen['hoy']
    inicio_mes = hoy.replace(day=1)
    fin_mes_pasado = inicio_mes - timedelta(days=1)
    inicio_mes_pasado = fin_mes_pasado.replace(day=1)

    gastos_mes_qs = resumen['movimientos'].filter(
        tipo__iexact='gasto',
        fecha__gte=inicio_mes,
        fecha__lte=hoy
    )
    gastos_mes_pasado = resumen['movimientos'].filter(
        tipo__iexact='gasto',
        fecha__gte=inicio_mes_pasado,
        fecha__lte=fin_mes_pasado
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    gastos_mes = resumen['gastos_mes']
    if gastos_mes_pasado > 0:
        variacion = round(float((gastos_mes - gastos_mes_pasado) / gastos_mes_pasado) * 100)
    else:
        variacion = 0

    hormiga_mes = gastos_mes_qs.filter(
        monto__lte=Decimal('15000.00')
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    categorias_top, _ = agrupar_categorias_gasto(gastos_mes_qs)

    return render(request, 'insights.html', {
        'usuario': perfil,
        'resumen': resumen,
        'variacion': variacion,
        'variacion_abs': abs(variacion),
        'hormiga_mes_fmt': formatear_cop(hormiga_mes),
        'categorias_top': categorias_top[:3],
        'pestana_activa': 'dashboard',
    })


# Pantalla Perfil y ajustes de cuenta estudiante
@login_required
def perfil_view(request):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        universidad = request.POST.get('universidad', '').strip()
        frecuencia = request.POST.get('frecuencia', perfil.frecuencia)
        mesada_texto = request.POST.get('mesada', str(perfil.mesada)).strip()

        try:
            mesada = Decimal(mesada_texto or '0')
            if (
                not nombre
                or not universidad
                or frecuencia not in ['diario', 'semanal', 'quincenal', 'mensual']
                or not mesada.is_finite()
                or mesada < 0
                or mesada.as_tuple().exponent < -2
            ):
                raise ValueError

            perfil.nombre = nombre
            perfil.universidad = universidad
            perfil.frecuencia = frecuencia
            perfil.mesada = mesada
            perfil.save()
            messages.success(request, 'Tu perfil fue actualizado correctamente.')
            return redirect('perfil')

        except (ValueError, InvalidOperation):
            messages.error(request, 'Verifica los datos de tu perfil antes de guardar.')

    resumen = calcular_resumen_usuario(perfil)
    return render(request, 'perfil.html', {
        'usuario': perfil,
        'correo': request.user.email or request.user.username,
        'saldo_fmt': resumen['saldo_fmt'],
        'limite_diario_fmt': resumen['limite_diario_fmt'],
        'pestana_activa': 'perfil',
    })


# Pantalla Presupuestos (conectada al modelo Presupuesto)
@login_required
def presupuestos_view(request):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')

    resumen = calcular_resumen_usuario(perfil)
    presupuesto = Presupuesto.objects.filter(idUsuario=perfil).first()

    if request.method == 'POST':
        try:
            limite_diario = _validar_monto_positivo(request.POST.get('limite_diario', '0'), Decimal('100'))
            limite_mensual = _validar_monto_positivo(request.POST.get('limite_mensual', '0'), Decimal('1000'))

            Presupuesto.objects.update_or_create(
                idUsuario=perfil,
                defaults={
                    'limiteDiario': limite_diario,
                    'limiteMensual': limite_mensual,
                }
            )
            messages.success(request, 'Presupuesto guardado correctamente.')
            return redirect('presupuestos')

        except (ValueError, InvalidOperation):
            messages.error(request, 'Ingresa límites válidos (mínimo diario $100 y mensual $1.000).')

    limite_diario_activo = (
        presupuesto.limiteDiario if presupuesto else Decimal(resumen['limite_diario'] or 0)
    )
    limite_mensual_activo = (
        presupuesto.limiteMensual
        if presupuesto
        else (perfil.mesada if perfil.mesada > 0 else Decimal('600000.00'))
    )

    hoy = resumen['hoy']
    gastos_mes_qs = resumen['movimientos'].filter(
        tipo__iexact='gasto',
        fecha__gte=hoy.replace(day=1),
        fecha__lte=hoy
    )
    categorias_gasto, _ = agrupar_categorias_gasto(gastos_mes_qs)

    # Distribución orientativa sobre el presupuesto mensual para mostrar avance por categoría
    if not categorias_gasto:
        categorias_gasto = [
            {'nombre': c.nombre, 'total': Decimal('0.00'), 'total_fmt': '0', 'ui': estilo_categoria(c.nombre)}
            for c in obtener_categorias()[:4]
        ]

    divisor = max(len(categorias_gasto), 1)
    tope_categoria = limite_mensual_activo / divisor
    barras_presupuesto = []
    for item in categorias_gasto:
        pct = min(100, round(float(item['total'] / tope_categoria) * 100)) if tope_categoria > 0 else 0
        barras_presupuesto.append({
            'nombre': item['nombre'],
            'gastado_fmt': item['total_fmt'],
            'tope_fmt': formatear_cop(round(tope_categoria)),
            'porcentaje': pct,
            'excedido': item['total'] > tope_categoria,
            'ui': item['ui'],
        })

    return render(request, 'presupuestos.html', {
        'usuario': perfil,
        'presupuesto': presupuesto,
        'limite_diario_val': int(limite_diario_activo),
        'limite_mensual_val': int(limite_mensual_activo),
        'limite_diario_fmt': formatear_cop(limite_diario_activo),
        'limite_mensual_fmt': formatear_cop(limite_mensual_activo),
        'gastos_mes_fmt': resumen['gastos_mes_fmt'],
        'barras_presupuesto': barras_presupuesto,
        'pestana_activa': 'perfil',
    })


# Pantalla motivacional / descanso Mishi (Screen 12 naranja)
@login_required
def animo_view(request):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')

    return render(request, 'animo.html', {
        'usuario': perfil,
        'ocultar_chrome': True,
    })
