from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import (
    Categoria,
    GastoCompartido,
    MetaAhorro,
    Notificacion,
    Participante,
    Presupuesto,
    Prestamo,
    Transaccion,
    Usuario,
)
from .services.analitica_service import (
    calcular_comparacion_periodos,
    calcular_evolucion_ahorro,
)
from .services.avatares import (
    AVATAR_DEFECTO,
    AVATARES_MISHI,
    TEMAS_VALIDOS,
    es_avatar_valido,
    obtener_avatar_info,
)
from .services.categorias_service import (
    TONOS_CATEGORIA_PALETA,
    crear_categoria_personalizada,
    editar_categoria_personalizada,
    eliminar_categoria_personalizada,
    obtener_categoria_accesible,
    obtener_categorias_personalizadas,
    obtener_categorias_usuario,
    obtener_estilo_categoria,
)
from .services.compartidos_service import (
    crear_gasto_compartido,
    crear_prestamo_usuario,
    marcar_participante_pagado,
    marcar_prestamo_pagado,
    obtener_resumen_compartidos_y_prestamos,
)
from .services.finanzas_service import (
    FRECUENCIAS_VALIDAS,
    UMBRAL_HORMIGA_MAX,
    UMBRAL_HORMIGA_MIN,
    es_gasto_hormiga,
    obtener_umbral_hormiga,
)
from .services.metas_service import (
    actualizar_fecha_objetivo_meta,
    crear_meta_usuario,
    enriquecer_metas_reales,
    registrar_aporte_meta,
)
from .services.notificaciones_service import (
    contar_notificaciones_no_leidas,
    sincronizar_notificaciones_usuario,
)
from .services.presupuestos_service import (
    calcular_presupuestos_categoria,
    eliminar_presupuesto_categoria,
    guardar_presupuesto_categoria,
)
from .services.recomendaciones_service import generar_recomendaciones_personalizadas
from .services.seguridad_service import (
    POLITICA_PRIVACIDAD_FECHA,
    POLITICA_PRIVACIDAD_VERSION,
    registrar_consentimiento_datos,
    requiere_consentimiento_vigente,
    validar_contrasena_servidor,
)
from .ui_helpers import (
    FRECUENCIA_ETIQUETAS,
    agrupar_categorias_gasto,
    agrupar_movimientos_por_fecha,
    calcular_dias_frecuencia,
    calcular_resumen_usuario,
    enriquecer_metas,
    estilo_categoria,
    etiqueta_fecha_movimiento,
    formatear_cop,
    serie_evolucion_periodo,
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


def _obtener_resumen(request, perfil):
    resumen = getattr(request, '_mishi_resumen', None)
    if resumen is None:
        resumen = calcular_resumen_usuario(perfil)
        request._mishi_resumen = resumen
    return resumen


def _validar_monto_positivo(texto, minimo=Decimal('100'), maximo=Decimal('99999999.99')):
    monto = Decimal(texto)
    if (
        not monto.is_finite()
        or monto < minimo
        or monto > maximo
        or monto.as_tuple().exponent < -2
    ):
        raise ValueError
    return monto


def _refrescar_notificaciones(request, perfil):
    """Sincroniza notificaciones tras una mutación financiera sin sobrecargar GETs."""
    hoy = timezone.localdate()
    resumen = calcular_resumen_usuario(perfil)
    request._mishi_resumen = resumen
    no_leidas = sincronizar_notificaciones_usuario(perfil, resumen=resumen, hoy=hoy)
    request._mishi_notif_count = no_leidas
    request.session['mishi_notif_sync_day'] = hoy.isoformat()
    return no_leidas


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
    context_base = {
        'avatares_mishi': AVATARES_MISHI,
        'avatar_seleccionado': obtener_avatar_info(AVATAR_DEFECTO),
        'politica_version': POLITICA_PRIVACIDAD_VERSION,
    }

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        universidad = request.POST.get('universidad', '').strip()
        frecuencia = request.POST.get('frecuencia', 'quincenal')
        correo = request.POST.get('correo', '').strip().lower()
        password = request.POST.get('pass', '')
        mesada_texto = request.POST.get('mesada', '0').strip()
        avatar_id = request.POST.get('avatar', AVATAR_DEFECTO).strip() or AVATAR_DEFECTO
        acepto_politica = request.POST.get('acepto_politica_datos') in ('1', 'on', 'true', 'True')
        if not es_avatar_valido(avatar_id):
            avatar_id = AVATAR_DEFECTO
        context_base['avatar_seleccionado'] = obtener_avatar_info(avatar_id)

        User = get_user_model()

        if not nombre or not universidad or not correo or not password:
            return render(request, 'registro_usuario.html', {
                **context_base,
                'error': 'Completa todos los campos obligatorios.'
            })

        if frecuencia not in FRECUENCIAS_VALIDAS:
            return render(request, 'registro_usuario.html', {
                **context_base,
                'error': 'Selecciona una frecuencia válida.'
            })

        try:
            mesada = Decimal(mesada_texto or '0')
            if (
                not mesada.is_finite()
                or mesada < 0
                or mesada > Decimal('99999999.99')
                or mesada.as_tuple().exponent < -2
            ):
                raise InvalidOperation
        except InvalidOperation:
            return render(request, 'registro_usuario.html', {
                **context_base,
                'error': 'Ingresa una mesada válida.'
            })

        if User.objects.filter(username=correo).exists():
            return render(request, 'registro_usuario.html', {
                **context_base,
                'error': 'Este correo ya está registrado.'
            })

        if not acepto_politica:
            return render(request, 'registro_usuario.html', {
                **context_base,
                'error': 'Debes aceptar la política de tratamiento de datos para crear tu cuenta.'
            })

        errores_pass = validar_contrasena_servidor(
            password,
            user=User(username=correo, email=correo, first_name=nombre),
        )
        if errores_pass:
            return render(request, 'registro_usuario.html', {
                **context_base,
                'error': errores_pass[0]
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
                    mesada=mesada,
                    saldo_inicial=mesada,
                    avatar=avatar_id,
                    acepto_politica_datos=True,
                    fecha_aceptacion_datos=timezone.now(),
                    version_politica_datos=POLITICA_PRIVACIDAD_VERSION,
                )

            login(request, cuenta)
            return redirect('dashboard')

        except Exception:
            return render(request, 'registro_usuario.html', {
                **context_base,
                'error': 'No se pudo crear la cuenta. Inténtalo nuevamente.'
            })

    return render(request, 'registro_usuario.html', context_base)


def obtener_categorias(perfil=None):
    if perfil is not None:
        return obtener_categorias_usuario(perfil)
    if not Categoria.objects.filter(idUsuario__isnull=True).exists():
        for nombre in CATEGORIAS_POR_DEFECTO:
            Categoria.objects.get_or_create(nombre=nombre, idUsuario=None)
    return Categoria.objects.filter(idUsuario__isnull=True).order_by('idCategoria')


def _categorias_con_ui(categorias):
    return [
        {
            'idCategoria': c.idCategoria,
            'nombre': c.nombre,
            'es_personalizada': getattr(c, 'es_personalizada', False),
            'ui': obtener_estilo_categoria(c),
        }
        for c in categorias
    ]


# Pantalla Inicio (App Home)
@login_required
def dashboard_view(request):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')

    resumen = _obtener_resumen(request, perfil)
    movimientos = resumen['movimientos']
    hoy = resumen['hoy']
    umbral_hormiga = resumen['umbral_hormiga']

    recientes = list(movimientos[:4])
    compartidos_ids = set(
        GastoCompartido.objects.filter(
            idTransaccion_id__in=[m.idTransaccion for m in recientes]
        ).values_list('idTransaccion_id', flat=True)
    )

    ultimos_movimientos = []
    for mov in recientes:
        es_hormiga = es_gasto_hormiga(mov.monto, mov.tipo, umbral_hormiga)
        ultimos_movimientos.append({
            'id': mov.idTransaccion,
            'fecha': mov.fecha,
            'fecha_label': etiqueta_fecha_movimiento(mov.fecha, hoy),
            'titulo': mov.descripcion or mov.idCategoria.nombre,
            'categoria': mov.idCategoria.nombre,
            'tipo': mov.tipo.lower(),
            'monto': mov.monto,
            'monto_fmt': formatear_cop(mov.monto),
            'es_hormiga': es_hormiga,
            'es_compartido': mov.idTransaccion in compartidos_ids,
            'ui': obtener_estilo_categoria(mov.idCategoria),
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
        'saldo_total_fmt': resumen['saldo_total_fmt'],
        'dinero_reservado_metas_fmt': resumen['dinero_reservado_metas_fmt'],
        'dias_restantes': resumen['dias_restantes'],
        'ciclo': resumen['ciclo'],
        'limite_diario': resumen['limite_diario'],
        'limite_diario_fmt': resumen['limite_diario_fmt'],
        'limite_diario_recomendado_fmt': resumen['limite_diario_recomendado_fmt'],
        'usa_limite_personalizado': resumen['usa_limite_personalizado'],
        'gasto_hoy': resumen['gasto_hoy'],
        'gasto_hoy_fmt': resumen['gasto_hoy_fmt'],
        'dinero_restante_hoy_fmt': resumen['dinero_restante_hoy_fmt'],
        'porcentaje_gasto_hoy': resumen['porcentaje_gasto_hoy'],
        'estado_alerta_diaria': resumen['estado_alerta_diaria'],
        'alerta_preventiva': resumen['alerta_preventiva'],
        'alerta_saldo_insuficiente': resumen['alerta_saldo_insuficiente'],
        'alerta_activa': resumen['alerta_activa'],
        'alerta_principal': resumen['alerta_principal'],
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

    resumen = _obtener_resumen(request, perfil)
    categorias = obtener_categorias(perfil)
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
            categoria = obtener_categoria_accesible(perfil, categoria_id)
            if categoria is None:
                raise Categoria.DoesNotExist
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
            _refrescar_notificaciones(request, perfil)

            messages.success(request, 'Movimiento registrado correctamente.')
            next_url = request.POST.get('next', '').strip()
            if next_url.startswith('/app/') and not next_url.startswith('//'):
                return redirect(next_url)
            return redirect('dashboard')

        except (InvalidOperation, ValueError, TypeError, Categoria.DoesNotExist):
            messages.error(
                request,
                'Verifica los datos. El monto mínimo es $100 y la fecha no puede ser futura.'
            )

    tipo_inicial = request.GET.get('tipo', 'gasto').strip().lower()
    if tipo_inicial not in ['gasto', 'ingreso']:
        tipo_inicial = 'gasto'

    return render(request, 'registro.html', {
        'usuario': perfil,
        'saldo': resumen['saldo'],
        'saldo_fmt': resumen['saldo_fmt'],
        'dias_restantes': resumen['dias_restantes'],
        'limite_diario': resumen['limite_diario'],
        'limite_diario_fmt': resumen['limite_diario_fmt'],
        'categorias': categorias,
        'categorias_ui': categorias_ui,
        'tipo_inicial': tipo_inicial,
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

    q = request.GET.get('q', '').strip()
    tipo_filtro = request.GET.get('tipo', 'todos').strip().lower()
    if tipo_filtro not in ['todos', 'gasto', 'ingreso']:
        tipo_filtro = 'todos'

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
        cat_filtrada = obtener_categoria_accesible(perfil, categoria_id) if categoria_id.isdigit() else None
        if cat_filtrada is not None:
            movimientos_db = movimientos_db.filter(idCategoria_id=cat_filtrada.idCategoria)
        else:
            error_filtros = 'La categoría seleccionada no es válida.'

    if tipo_filtro in ['gasto', 'ingreso']:
        movimientos_db = movimientos_db.filter(tipo__iexact=tipo_filtro)

    if q:
        movimientos_db = movimientos_db.filter(
            Q(descripcion__icontains=q) | Q(idCategoria__nombre__icontains=q)
        )

    total_ingresos = movimientos_db.filter(
        tipo__iexact='ingreso'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    total_gastos = movimientos_db.filter(
        tipo__iexact='gasto'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    umbral_hormiga = obtener_umbral_hormiga(perfil)
    movs_lista = list(movimientos_db)
    compartidos_ids = set(
        GastoCompartido.objects.filter(
            idTransaccion_id__in=[m.idTransaccion for m in movs_lista]
        ).values_list('idTransaccion_id', flat=True)
    )

    movimientos = []
    for m in movs_lista:
        es_hormiga = es_gasto_hormiga(m.monto, m.tipo, umbral_hormiga)
        movimientos.append({
            'id': m.idTransaccion,
            'titulo': m.descripcion or m.idCategoria.nombre,
            'categoria': m.idCategoria.nombre,
            'tipo': m.tipo.lower(),
            'monto': m.monto,
            'monto_fmt': formatear_cop(m.monto),
            'fecha': m.fecha,
            'fecha_label': etiqueta_fecha_movimiento(m.fecha, hoy),
            'es_hormiga': es_hormiga,
            'es_compartido': m.idTransaccion in compartidos_ids,
            'ui': obtener_estilo_categoria(m.idCategoria),
        })

    movimientos_agrupados = agrupar_movimientos_por_fecha(movimientos, hoy)
    balance = total_ingresos - total_gastos

    context = {
        'usuario': perfil,
        'movimientos': movimientos,
        'movimientos_agrupados': movimientos_agrupados,
        'total_cantidad': len(movimientos),
        'total_ingresos': total_ingresos,
        'total_ingresos_fmt': formatear_cop(total_ingresos),
        'total_gastos': total_gastos,
        'total_gastos_fmt': formatear_cop(total_gastos),
        'balance': balance,
        'balance_fmt': formatear_cop(abs(balance)),
        'balance_positivo': balance >= 0,
        'barras_semana': serie_semanal_gastos(movimientos_base, hoy),
        'categorias': obtener_categorias(perfil),
        'q': q,
        'tipo_filtro': tipo_filtro,
        'rango': rango or 'todos',
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'categoria_seleccionada': categoria_id,
        'filtros_activos': bool(fecha_inicio or fecha_fin or categoria_id or error_filtros),
        'hay_busqueda_o_filtro': bool(q or tipo_filtro != 'todos' or fecha_inicio or fecha_fin or categoria_id or rango in ['mes', '3m']),
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

    umbral_hormiga = obtener_umbral_hormiga(perfil)
    es_hormiga = es_gasto_hormiga(movimiento.monto, movimiento.tipo, umbral_hormiga)
    gasto_comp = (
        GastoCompartido.objects.filter(idTransaccion=movimiento)
        .prefetch_related('participantes')
        .first()
    )
    participantes_comp = []
    if gasto_comp is not None:
        participantes_comp = [
            {
                'idParticipante': pt.idParticipante,
                'nombreAmigo': pt.nombreAmigo,
                'parte_fmt': formatear_cop(pt.parteAportada),
                'pagado': pt.pagado,
            }
            for pt in gasto_comp.participantes.all()
        ]
    return render(request, 'detalle_movimiento.html', {
        'usuario': perfil,
        'movimiento': movimiento,
        'monto_fmt': formatear_cop(movimiento.monto),
        'ui': obtener_estilo_categoria(movimiento.idCategoria),
        'es_hormiga': es_hormiga,
        'umbral_hormiga_fmt': formatear_cop(umbral_hormiga),
        'gasto_compartido': gasto_comp,
        'gasto_comp_mi_parte_fmt': formatear_cop(gasto_comp.mi_parte) if gasto_comp else '',
        'gasto_comp_total_fmt': formatear_cop(gasto_comp.montoTotal) if gasto_comp else '',
        'participantes_comp': participantes_comp,
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

    categorias = obtener_categorias(perfil)

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

            categoria = obtener_categoria_accesible(perfil, categoria_id)
            if categoria is None:
                raise Categoria.DoesNotExist

            movimiento.tipo = tipo
            movimiento.monto = monto
            movimiento.idCategoria = categoria
            movimiento.descripcion = descripcion
            movimiento.fecha = fecha_movimiento
            movimiento.save()
            _refrescar_notificaciones(request, perfil)

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
            _refrescar_notificaciones(request, perfil)
            messages.success(request, 'Movimiento eliminado correctamente.')
        else:
            messages.error(request, 'No se encontró el movimiento.')

    return redirect('historial')


# Metas de ahorro, préstamos y gastos compartidos (RF-10, RF-12)
@login_required
def metas_view(request):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')

    hoy = timezone.localdate()

    if request.method == 'POST':
        accion = request.POST.get('accion')
        tab_destino = 'metas'

        try:
            if accion == 'crear_meta':
                nombre = request.POST.get('nombre', '').strip()
                categoria = request.POST.get('categoria', '').strip()
                objetivo = _validar_monto_positivo(request.POST.get('objetivo', '0'), Decimal('0.01'))
                fecha_obj_txt = request.POST.get('fecha_objetivo', '').strip()
                fecha_obj = date.fromisoformat(fecha_obj_txt) if fecha_obj_txt else None

                crear_meta_usuario(perfil, nombre, categoria, objetivo, fecha_objetivo=fecha_obj, hoy=hoy)
                messages.success(request, 'Meta de ahorro creada correctamente.')

            elif accion == 'actualizar_meta':
                meta_id = request.POST.get('meta_id')
                ahorro = _validar_monto_positivo(request.POST.get('ahorro', '0'), Decimal('0.01'))
                registrar_aporte_meta(perfil, meta_id, ahorro, fecha=hoy)
                messages.success(request, 'Ahorro agregado correctamente.')

            elif accion == 'actualizar_fecha_meta':
                meta_id = request.POST.get('meta_id')
                fecha_obj_txt = request.POST.get('fecha_objetivo', '').strip()
                fecha_obj = date.fromisoformat(fecha_obj_txt) if fecha_obj_txt else None
                if fecha_obj is not None and fecha_obj < hoy:
                    raise ValueError('La fecha objetivo debe ser hoy o futura.')
                actualizar_fecha_objetivo_meta(perfil, meta_id, fecha_obj)
                messages.success(request, 'Fecha objetivo actualizada correctamente.')

            elif accion == 'crear_prestamo':
                tab_destino = 'prestamos'
                deudor = request.POST.get('deudor', '').strip()
                concepto = request.POST.get('concepto', '').strip()
                tipo = request.POST.get('tipo', 'Por cobrar')
                monto = _validar_monto_positivo(request.POST.get('monto', '0'), Decimal('0.01'))
                fecha_lim_txt = request.POST.get('fecha_limite', '').strip()
                fecha_lim = date.fromisoformat(fecha_lim_txt) if fecha_lim_txt else None

                crear_prestamo_usuario(perfil, deudor, concepto, tipo, monto, fecha_limite=fecha_lim)
                messages.success(request, 'Préstamo registrado correctamente.')

            elif accion == 'pagar_prestamo':
                tab_destino = 'prestamos'
                prestamo_id = request.POST.get('prestamo_id')
                registrar_mov = request.POST.get('registrar_movimiento') in ('1', 'on', 'true', 'True')
                _, actualizado = marcar_prestamo_pagado(
                    perfil,
                    prestamo_id,
                    registrar_movimiento=registrar_mov,
                    hoy=hoy,
                )
                if actualizado:
                    messages.success(request, 'Préstamo marcado como pagado.')

            else:
                messages.error(request, 'Acción no válida.')
                return redirect('metas')

            _refrescar_notificaciones(request, perfil)
            if tab_destino != 'metas':
                return redirect(f'/app/metas/?tab={tab_destino}')
            return redirect('metas')

        except (ValueError, InvalidOperation, MetaAhorro.DoesNotExist, Prestamo.DoesNotExist) as exc:
            detalle = str(exc).strip()
            messages.error(
                request,
                detalle if detalle and 'does not exist' not in detalle.lower() else 'Verifica los datos ingresados.',
            )

    resumen = _obtener_resumen(request, perfil)
    metas = MetaAhorro.objects.filter(idUsuario=perfil).order_by('-idMeta')
    metas_ui = enriquecer_metas_reales(
        metas,
        perfil=perfil,
        hoy=hoy,
        limite_diario_ref=resumen['limite_diario_recomendado'],
    )
    comp_resumen = obtener_resumen_compartidos_y_prestamos(perfil, hoy=hoy)

    total_ahorrado = sum((m['acumulado'] for m in metas_ui), Decimal('0.00'))
    total_objetivo = sum((m['objetivo'] for m in metas_ui), Decimal('0.00'))
    porcentaje_global = (
        min(100, round(float(total_ahorrado / total_objetivo) * 100))
        if total_objetivo > 0
        else 0
    )
    metas_completadas_count = sum(1 for m in metas_ui if m['completada'])
    metas_activas_count = len(metas_ui) - metas_completadas_count

    tab_param = request.GET.get('tab', 'metas').strip().lower()
    tab_activo = tab_param if tab_param in ('metas', 'prestamos', 'compartidos') else 'metas'

    context = {
        'usuario': perfil,
        'metas': metas,
        'metas_ui': metas_ui,
        'prestamos': comp_resumen['prestamos'],
        'prestamos_ui': comp_resumen['prestamos_ui'],
        'gastos_compartidos': comp_resumen['gastos_compartidos'],
        'comp_resumen': comp_resumen,
        'categorias_gasto': obtener_categorias_usuario(perfil, tipo='gasto'),
        'hoy_iso': hoy.isoformat(),
        'total_ahorrado_fmt': formatear_cop(total_ahorrado),
        'total_objetivo_fmt': formatear_cop(total_objetivo),
        'porcentaje_global': porcentaje_global,
        'metas_activas_count': metas_activas_count,
        'metas_completadas_count': metas_completadas_count,
        'prestamos_pendientes_count': comp_resumen['prestamos_pendientes_count'],
        'compartidos_pendientes_count': comp_resumen['compartidos_pendientes_count'],
        'tab_activo': tab_activo,
        'pestana_activa': 'metas',
    }
    return render(request, 'metas.html', context)


# Pantalla Crear Meta (dedicada, conectada al botón + de Metas)
@login_required
def crear_meta_view(request):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')

    hoy = timezone.localdate()

    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre', '').strip()
            categoria = request.POST.get('categoria', '').strip()
            objetivo = _validar_monto_positivo(request.POST.get('objetivo', '0'), Decimal('0.01'))
            fecha_obj_txt = request.POST.get('fecha_objetivo', '').strip()
            fecha_obj = date.fromisoformat(fecha_obj_txt) if fecha_obj_txt else None

            crear_meta_usuario(perfil, nombre, categoria, objetivo, fecha_objetivo=fecha_obj, hoy=hoy)
            _refrescar_notificaciones(request, perfil)
            messages.success(request, 'Meta de ahorro creada correctamente.')
            return redirect('metas')

        except (ValueError, InvalidOperation) as exc:
            detalle = str(exc).strip()
            messages.error(request, detalle or 'Completa el nombre y un monto objetivo válido.')

    return render(request, 'crear_meta.html', {
        'usuario': perfil,
        'hoy_iso': hoy.isoformat(),
        'pestana_activa': 'metas',
    })


# Pantalla Categorías (Donut + gestión de categorías personalizadas RF-02)
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

    personalizadas_qs = obtener_categorias_personalizadas(perfil)
    conteo_por_cat = {
        r['idCategoria']: r['total']
        for r in Transaccion.objects.filter(
            idUsuario=perfil,
            idCategoria__in=personalizadas_qs,
        )
        .values('idCategoria')
        .annotate(total=Sum('monto'))
    }
    personalizadas_ui = []
    for cat in personalizadas_qs:
        personalizadas_ui.append({
            'idCategoria': cat.idCategoria,
            'nombre': cat.nombre,
            'tipo_aplicable': cat.tipo_aplicable,
            'tono': cat.tono,
            'ui': obtener_estilo_categoria(cat),
            'tiene_movimientos': cat.idCategoria in conteo_por_cat,
        })

    return render(request, 'categorias.html', {
        'usuario': perfil,
        'rango': rango,
        'categorias_gasto': categorias_gasto,
        'categorias_personalizadas': personalizadas_ui,
        'tonos_paleta': TONOS_CATEGORIA_PALETA,
        'total_gastado_fmt': formatear_cop(total_gastado),
        'etiquetas_json': [c['nombre'] for c in categorias_gasto],
        'valores_json': [float(c['total']) for c in categorias_gasto],
        'colores_json': [c['ui']['color'] for c in categorias_gasto],
        'pestana_activa': 'historial',
    })


# Pantalla Estadísticas e Insights (RF-08, RF-09, RF-13)
@login_required
def insights_view(request):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')

    resumen = _obtener_resumen(request, perfil)
    hoy = resumen['hoy']
    inicio_mes = hoy.replace(day=1)
    umbral_hormiga = resumen['umbral_hormiga']

    periodo = request.GET.get('periodo', 'mensual').strip().lower()
    if periodo not in ['semanal', 'mensual', 'anual']:
        periodo = 'mensual'

    if periodo == 'semanal':
        desde_periodo = hoy - timedelta(days=hoy.weekday())
        etiqueta_periodo = 'Esta semana'
    elif periodo == 'anual':
        desde_periodo = hoy.replace(month=1, day=1)
        etiqueta_periodo = f'Año {hoy.year}'
    else:
        desde_periodo = inicio_mes
        etiqueta_periodo = 'Este mes'

    movimientos_periodo = resumen['movimientos'].filter(
        fecha__gte=desde_periodo,
        fecha__lte=hoy,
    )
    ingresos_periodo = movimientos_periodo.filter(
        tipo__iexact='ingreso'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    gastos_periodo_qs = movimientos_periodo.filter(tipo__iexact='gasto')
    gastos_periodo = gastos_periodo_qs.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    balance_periodo = ingresos_periodo - gastos_periodo

    gastos_mes_qs = resumen['movimientos'].filter(
        tipo__iexact='gasto',
        fecha__gte=inicio_mes,
        fecha__lte=hoy,
    )

    comparacion = calcular_comparacion_periodos(perfil, periodo=periodo, hoy=hoy)
    evolucion_ahorro = calcular_evolucion_ahorro(perfil, hoy=hoy, meses=6)
    variacion = comparacion['var_gastos_pct']

    hormiga_mes = gastos_mes_qs.filter(
        monto__lte=umbral_hormiga
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    hormiga_periodo_qs = gastos_periodo_qs.filter(monto__lte=umbral_hormiga)
    hormiga_periodo = hormiga_periodo_qs.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    hormiga_count = hormiga_periodo_qs.count()

    categorias_periodo, _ = agrupar_categorias_gasto(gastos_periodo_qs)
    barras_evolucion = serie_evolucion_periodo(resumen['movimientos'], hoy, periodo)

    presupuestos_cat = calcular_presupuestos_categoria(perfil, hoy=hoy)
    metas_plan = enriquecer_metas_reales(
        MetaAhorro.objects.filter(idUsuario=perfil),
        perfil=perfil,
        hoy=hoy,
        limite_diario_ref=resumen['limite_diario_recomendado'],
    )
    compartidos_resumen = obtener_resumen_compartidos_y_prestamos(perfil, hoy=hoy)
    recomendaciones = generar_recomendaciones_personalizadas(
        perfil,
        resumen,
        comparacion=comparacion,
        presupuestos_cat=presupuestos_cat,
        metas_plan=metas_plan,
        compartidos_resumen=compartidos_resumen,
        hoy=hoy,
    )

    alerta_principal = resumen['alerta_principal']
    if alerta_principal is not None:
        mishi_mood = 'alert'
        mishi_titulo = alerta_principal['titulo']
        mishi_mensaje = alerta_principal['detalle']
    elif comparacion['tiene_datos_anteriores'] and variacion < 0:
        mishi_mood = 'celebrate'
        mishi_titulo = 'Ritmo de ahorro saludable'
        mishi_mensaje = (
            f"Llevas {abs(variacion)}% menos en gastos frente a {comparacion['etiqueta_anterior'].lower()}. "
            'Buen momento para abonar a una meta.'
        )
    elif comparacion['tiene_datos_anteriores'] and variacion > 0:
        mishi_mood = 'alert'
        mishi_titulo = f'Tus gastos subieron {variacion}%'
        mishi_mensaje = (
            f"Acumulas ${comparacion['gastos_actual_fmt']} frente a ${comparacion['gastos_anterior_fmt']} "
            f"en {comparacion['etiqueta_anterior'].lower()}."
        )
    else:
        mishi_mood = 'neutral'
        mishi_titulo = 'Tu dinero va en equilibrio'
        mishi_mensaje = (
            f"Llevas ${resumen['gasto_hoy_fmt']} hoy de tu límite diario de ${resumen['limite_diario_fmt']} "
            f"en tu ciclo {FRECUENCIA_ETIQUETAS.get(perfil.frecuencia, perfil.frecuencia).lower()}."
        )

    return render(request, 'insights.html', {
        'usuario': perfil,
        'resumen': resumen,
        'periodo': periodo,
        'etiqueta_periodo': etiqueta_periodo,
        'ingresos_periodo': float(ingresos_periodo),
        'gastos_periodo': float(gastos_periodo),
        'ingresos_periodo_fmt': formatear_cop(ingresos_periodo),
        'gastos_periodo_fmt': formatear_cop(gastos_periodo),
        'balance_periodo_fmt': formatear_cop(abs(balance_periodo)),
        'balance_periodo_positivo': balance_periodo >= 0,
        'etiquetas_categorias': [c['nombre'] for c in categorias_periodo],
        'valores_categorias': [float(c['total']) for c in categorias_periodo],
        'colores_categorias': [c['ui']['color'] for c in categorias_periodo],
        'categorias_periodo': categorias_periodo,
        'categorias_top': categorias_periodo[:4],
        'barras_evolucion': barras_evolucion,
        'comparacion': comparacion,
        'evolucion_ahorro': evolucion_ahorro,
        'recomendaciones': recomendaciones,
        'variacion': variacion,
        'variacion_abs': abs(variacion),
        'umbral_hormiga_val': int(umbral_hormiga),
        'umbral_hormiga_fmt': resumen['umbral_hormiga_fmt'],
        'hormiga_mes_fmt': formatear_cop(hormiga_mes),
        'hormiga_periodo_fmt': formatear_cop(hormiga_periodo),
        'hormiga_count': hormiga_count,
        'mesada_fmt': formatear_cop(perfil.mesada),
        'frecuencia_label': FRECUENCIA_ETIQUETAS.get(perfil.frecuencia, perfil.frecuencia),
        'mishi_mood': mishi_mood,
        'mishi_titulo': mishi_titulo,
        'mishi_mensaje': mishi_mensaje,
        'pestana_activa': 'insights',
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
        fecha_proximo_texto = request.POST.get('fecha_proximo_ingreso', '').strip()
        umbral_texto = request.POST.get('umbral_hormiga', '').strip()

        try:
            mesada = Decimal(mesada_texto or '0')
            if (
                not nombre
                or not universidad
                or frecuencia not in FRECUENCIAS_VALIDAS
                or not mesada.is_finite()
                or mesada < 0
                or mesada > Decimal('99999999.99')
                or mesada.as_tuple().exponent < -2
            ):
                raise ValueError

            fecha_proximo = None
            if fecha_proximo_texto:
                fecha_proximo = date.fromisoformat(fecha_proximo_texto)

            if umbral_texto:
                umbral = _validar_monto_positivo(umbral_texto, UMBRAL_HORMIGA_MIN, UMBRAL_HORMIGA_MAX)
                perfil.umbral_hormiga = umbral

            perfil.nombre = nombre
            perfil.universidad = universidad
            perfil.frecuencia = frecuencia
            perfil.mesada = mesada
            if 'fecha_proximo_ingreso' in request.POST:
                perfil.fecha_proximo_ingreso = fecha_proximo
                perfil.dia_pago_mensual = (
                    fecha_proximo.day
                    if (fecha_proximo and frecuencia == 'mensual')
                    else None
                )
            elif frecuencia != 'mensual':
                perfil.dia_pago_mensual = None
            perfil.save()
            _refrescar_notificaciones(request, perfil)
            messages.success(request, 'Tu perfil fue actualizado correctamente.')
            return redirect('perfil')

        except (ValueError, InvalidOperation):
            messages.error(request, 'Verifica los datos de tu perfil antes de guardar.')

    resumen = _obtener_resumen(request, perfil)
    return render(request, 'perfil.html', {
        'usuario': perfil,
        'correo': request.user.email or request.user.username,
        'saldo_fmt': resumen['saldo_fmt'],
        'saldo_inicial_fmt': resumen['saldo_inicial_fmt'],
        'dinero_reservado_metas_fmt': resumen['dinero_reservado_metas_fmt'],
        'limite_diario_fmt': resumen['limite_diario_fmt'],
        'umbral_hormiga_val': int(resumen['umbral_hormiga']),
        'umbral_hormiga_fmt': resumen['umbral_hormiga_fmt'],
        'mesada_fmt': formatear_cop(perfil.mesada),
        'dias_restantes': resumen['dias_restantes'],
        'ciclo': resumen['ciclo'],
        'fecha_proximo_ingreso_iso': (
            perfil.fecha_proximo_ingreso.isoformat()
            if perfil.fecha_proximo_ingreso
            else ''
        ),
        'frecuencia_label': FRECUENCIA_ETIQUETAS.get(perfil.frecuencia, perfil.frecuencia),
        'alerta_activa': resumen['alerta_activa'],
        'presupuesto_configurado': Presupuesto.objects.filter(idUsuario=perfil).exists(),
        'politica_version': POLITICA_PRIVACIDAD_VERSION,
        'pestana_activa': 'perfil',
    })


# Guardar avatar personalizado y preferencias persistentes en BD (POST + CSRF)
@login_required
def perfil_preferencias_view(request):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')

    if request.method != 'POST':
        return redirect('perfil')

    es_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    campos_actualizados = []

    if 'avatar' in request.POST:
        avatar_id = request.POST.get('avatar', '').strip()
        if not es_avatar_valido(avatar_id):
            if es_ajax:
                return JsonResponse({'ok': False, 'error': 'Avatar no válido.'}, status=400)
            messages.error(request, 'El avatar seleccionado no es válido.')
            return redirect('perfil')
        perfil.avatar = avatar_id
        campos_actualizados.append('avatar')

    if 'ocultar_saldo' in request.POST:
        perfil.ocultar_saldo = request.POST.get('ocultar_saldo') in ('1', 'true', 'True', 'on')
        campos_actualizados.append('ocultar_saldo')

    if 'alertas_activas' in request.POST:
        perfil.alertas_activas = request.POST.get('alertas_activas') in ('1', 'true', 'True', 'on')
        campos_actualizados.append('alertas_activas')

    if 'tema_visual' in request.POST:
        tema = request.POST.get('tema_visual', '').strip()
        if tema not in TEMAS_VALIDOS:
            if es_ajax:
                return JsonResponse({'ok': False, 'error': 'Tema no válido.'}, status=400)
            messages.error(request, 'Tema visual no válido.')
            return redirect('perfil')
        perfil.tema_visual = tema
        campos_actualizados.append('tema_visual')

    if campos_actualizados:
        perfil.save(update_fields=campos_actualizados)
        if 'alertas_activas' in campos_actualizados:
            _refrescar_notificaciones(request, perfil)

    avatar_info = obtener_avatar_info(perfil.avatar)
    if es_ajax:
        return JsonResponse({
            'ok': True,
            'avatar': avatar_info['id'],
            'avatar_nombre': avatar_info['nombre'],
            'ocultar_saldo': perfil.ocultar_saldo,
            'alertas_activas': perfil.alertas_activas,
            'tema_visual': perfil.tema_visual,
        })

    if 'avatar' in campos_actualizados:
        messages.success(request, f'Avatar actualizado a {avatar_info["nombre"]}.')
    else:
        messages.success(request, 'Preferencias guardadas correctamente.')
    return redirect('perfil')


# Pantalla Presupuestos (general + presupuestos reales por categoría RF-11)
@login_required
def presupuestos_view(request):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')

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
            _refrescar_notificaciones(request, perfil)
            messages.success(request, 'Presupuesto guardado correctamente.')
            return redirect('presupuestos')

        except (ValueError, InvalidOperation):
            messages.error(request, 'Ingresa límites válidos (mínimo diario $100 y mensual $1.000).')

    resumen = _obtener_resumen(request, perfil)
    limite_diario_activo = resumen['limite_diario_activo']
    limite_diario_form_val = (
        presupuesto.limiteDiario if presupuesto else resumen['limite_diario_recomendado']
    )
    referencia_base = perfil.mesada if perfil.mesada > 0 else (resumen['saldo_inicial'] + resumen['ingresos_recibidos'])
    limite_mensual_activo = presupuesto.limiteMensual if presupuesto else referencia_base

    hoy = resumen['hoy']
    gastos_mes = resumen['gastos_mes']
    disponible_mensual = max(limite_mensual_activo - gastos_mes, Decimal('0.00'))
    excedente_mensual = max(gastos_mes - limite_mensual_activo, Decimal('0.00'))
    porcentaje_mensual_real = (
        round(float(gastos_mes / limite_mensual_activo) * 100)
        if limite_mensual_activo > 0
        else 0
    )
    porcentaje_mensual = min(100, porcentaje_mensual_real)
    if limite_mensual_activo > 0 and gastos_mes > limite_mensual_activo:
        estado_mensual = 'excedido'
    elif limite_mensual_activo > 0 and porcentaje_mensual_real >= 80:
        estado_mensual = 'preventivo'
    else:
        estado_mensual = 'ok'

    pres_cat_data = calcular_presupuestos_categoria(perfil, hoy=hoy)

    return render(request, 'presupuestos.html', {
        'usuario': perfil,
        'presupuesto': presupuesto,
        'limite_diario_val': int(limite_diario_form_val),
        'limite_mensual_val': int(limite_mensual_activo),
        'limite_diario_fmt': formatear_cop(limite_diario_activo),
        'limite_diario_recomendado_fmt': resumen['limite_diario_recomendado_fmt'],
        'limite_mensual_fmt': formatear_cop(limite_mensual_activo),
        'gastos_mes_fmt': resumen['gastos_mes_fmt'],
        'disponible_mensual_fmt': formatear_cop(disponible_mensual),
        'excedente_mensual_fmt': formatear_cop(excedente_mensual),
        'porcentaje_mensual': porcentaje_mensual,
        'porcentaje_mensual_real': porcentaje_mensual_real,
        'estado_mensual': estado_mensual,
        'gasto_hoy_fmt': resumen['gasto_hoy_fmt'],
        'dinero_restante_hoy_fmt': resumen['dinero_restante_hoy_fmt'],
        'porcentaje_gasto_hoy': resumen['porcentaje_gasto_hoy'],
        'limite_superado_hoy': resumen['limite_superado'],
        'alerta_hoy': resumen['alerta_activa'],
        'alerta_principal': resumen['alerta_principal'],
        'alerta_saldo_insuficiente': resumen['alerta_saldo_insuficiente'],
        'barras_presupuesto': pres_cat_data['presupuestos_configurados'],
        'categorias_sin_presupuesto': pres_cat_data['categorias_sin_presupuesto'],
        'total_asignado_categorias_fmt': pres_cat_data['total_asignado_fmt'],
        'categorias_disponibles': obtener_categorias_usuario(perfil, tipo='gasto'),
        'pestana_activa': 'presupuestos',
    })


# Endpoints modulares de Fase 3 (POST + CSRF + aislamiento estricto)
@login_required
def categoria_crear_view(request):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')
    if request.method == 'POST':
        try:
            cat = crear_categoria_personalizada(
                perfil,
                nombre=request.POST.get('nombre', ''),
                tipo_aplicable=request.POST.get('tipo_aplicable', 'ambos'),
                tono=request.POST.get('tono', ''),
            )
            messages.success(request, f'Categoría "{cat.nombre}" creada correctamente.')
        except ValueError as exc:
            messages.error(request, str(exc))
    return redirect('categorias')


@login_required
def categoria_editar_view(request, categoria_id):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')
    if request.method == 'POST':
        try:
            cat = editar_categoria_personalizada(
                perfil,
                categoria_id=categoria_id,
                nombre=request.POST.get('nombre', ''),
                tipo_aplicable=request.POST.get('tipo_aplicable', 'ambos'),
                tono=request.POST.get('tono', ''),
            )
            messages.success(request, f'Categoría "{cat.nombre}" actualizada.')
        except ValueError as exc:
            messages.error(request, str(exc))
    return redirect('categorias')


@login_required
def categoria_eliminar_view(request, categoria_id):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')
    if request.method == 'POST':
        try:
            nombre = eliminar_categoria_personalizada(perfil, categoria_id)
            messages.success(request, f'Categoría "{nombre}" eliminada.')
        except ValueError as exc:
            messages.error(request, str(exc))
    return redirect('categorias')


@login_required
def presupuesto_categoria_guardar_view(request):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')
    if request.method == 'POST':
        try:
            cat_id = request.POST.get('categoria_id', '')
            limite = _validar_monto_positivo(request.POST.get('limite_mensual', '0'), Decimal('1000'))
            pc = guardar_presupuesto_categoria(perfil, cat_id, limite)
            _refrescar_notificaciones(request, perfil)
            messages.success(request, f'Tope mensual de "{pc.idCategoria.nombre}" guardado.')
        except (ValueError, InvalidOperation) as exc:
            messages.error(request, str(exc) or 'Ingresa un presupuesto válido por categoría.')
    return redirect('presupuestos')


@login_required
def presupuesto_categoria_eliminar_view(request, presupuesto_cat_id):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')
    if request.method == 'POST':
        if eliminar_presupuesto_categoria(perfil, presupuesto_cat_id):
            _refrescar_notificaciones(request, perfil)
            messages.success(request, 'Presupuesto de categoría eliminado.')
    return redirect('presupuestos')


@login_required
def gasto_compartido_crear_view(request):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')
    if request.method == 'POST':
        try:
            hoy = timezone.localdate()
            descripcion = request.POST.get('descripcion', '').strip()
            categoria_id = request.POST.get('categoria', '')
            monto_total = _validar_monto_positivo(request.POST.get('monto_total', '0'), Decimal('100'))
            mi_parte_txt = request.POST.get('mi_parte', '0').strip() or '0'
            mi_parte = _validar_monto_positivo(mi_parte_txt, Decimal('0.00'))
            fecha_txt = request.POST.get('fecha', '').strip() or hoy.isoformat()
            fecha_mov = date.fromisoformat(fecha_txt)
            yo_pague_total = request.POST.get('yo_pague_total', '1') in ('1', 'on', 'true', 'True')

            nombres = request.POST.getlist('participante_nombre')
            montos = request.POST.getlist('participante_monto')
            participantes = []
            for nm, m_txt in zip(nombres, montos):
                nm_c = nm.strip()
                m_c = m_txt.strip()
                if not nm_c and not m_c:
                    continue
                aporte = _validar_monto_positivo(m_c or '0', Decimal('100'))
                participantes.append((nm_c, aporte))

            crear_gasto_compartido(
                perfil=perfil,
                categoria_id=categoria_id,
                descripcion=descripcion,
                monto_total=monto_total,
                mi_parte=mi_parte,
                fecha=fecha_mov,
                participantes_lista=participantes,
                yo_pague_total=yo_pague_total,
                hoy=hoy,
            )
            _refrescar_notificaciones(request, perfil)
            messages.success(request, 'Gasto compartido registrado correctamente.')
        except (ValueError, InvalidOperation) as exc:
            messages.error(request, str(exc) or 'Verifica los datos del gasto compartido.')
    return redirect('/app/metas/?tab=compartidos')


@login_required
def participante_pagar_view(request, participante_id):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')
    if request.method == 'POST':
        try:
            part, marcado = marcar_participante_pagado(perfil, participante_id)
            if marcado:
                _refrescar_notificaciones(request, perfil)
                messages.success(request, f'Reembolso de {part.nombreAmigo} registrado correctamente.')
        except Participante.DoesNotExist:
            messages.error(request, 'No se encontró el participante indicado.')
    next_url = request.POST.get('next', '').strip()
    if next_url.startswith('/app/') and not next_url.startswith('//'):
        return redirect(next_url)
    return redirect('/app/metas/?tab=compartidos')


@login_required
def umbral_hormiga_view(request):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')
    if request.method == 'POST':
        try:
            nuevo = _validar_monto_positivo(
                request.POST.get('umbral_hormiga', '0').strip(),
                UMBRAL_HORMIGA_MIN,
                UMBRAL_HORMIGA_MAX,
            )
            perfil.umbral_hormiga = nuevo
            perfil.save(update_fields=['umbral_hormiga'])
            _refrescar_notificaciones(request, perfil)
            messages.success(
                request,
                f'Umbral de gastos hormiga actualizado a ${formatear_cop(nuevo)}.',
            )
        except (ValueError, InvalidOperation):
            messages.error(
                request,
                f'Ingresa un umbral válido entre ${formatear_cop(UMBRAL_HORMIGA_MIN)} y ${formatear_cop(UMBRAL_HORMIGA_MAX)}.',
            )
    next_url = request.POST.get('next', '').strip()
    if next_url.startswith('/app/') and not next_url.startswith('//'):
        return redirect(next_url)
    return redirect('perfil')


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


# Centro de Notificaciones reales in-app
@login_required
def notificaciones_view(request):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')

    resumen = _obtener_resumen(request, perfil)
    hoy = resumen['hoy']
    no_leidas = sincronizar_notificaciones_usuario(perfil, resumen=resumen, hoy=hoy)
    request._mishi_notif_count = no_leidas
    request.session['mishi_notif_sync_day'] = hoy.isoformat()

    filtro = request.GET.get('filtro', 'todas').strip().lower()
    if filtro not in ('todas', 'no_leidas'):
        filtro = 'todas'

    qs = Notificacion.objects.filter(idUsuario=perfil, descartada=False)
    total_notificaciones = qs.count()
    if filtro == 'no_leidas':
        qs = qs.filter(leida=False)

    notificaciones_ui = []
    for n in qs[:50]:
        fecha_local = timezone.localtime(n.creada_en)
        notificaciones_ui.append({
            'id': n.idNotificacion,
            'tipo': n.tipo,
            'nivel': n.nivel,
            'titulo': n.titulo,
            'mensaje': n.mensaje,
            'url_destino': n.url_destino,
            'leida': n.leida,
            'fecha_label': etiqueta_fecha_movimiento(fecha_local.date(), hoy),
            'hora_label': fecha_local.strftime('%I:%M %p').lstrip('0').lower(),
        })

    return render(request, 'notificaciones.html', {
        'usuario': perfil,
        'notificaciones': notificaciones_ui,
        'total_notificaciones': total_notificaciones,
        'no_leidas_count': no_leidas,
        'filtro': filtro,
        'pestana_activa': 'notificaciones',
    })


@login_required
def notificaciones_leer_view(request):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')

    if request.method != 'POST':
        return redirect('notificaciones')

    if request.POST.get('todas') == '1':
        Notificacion.objects.filter(
            idUsuario=perfil,
            descartada=False,
            leida=False,
        ).update(leida=True)
        messages.success(request, 'Todas las notificaciones fueron marcadas como leídas.')
        return redirect('notificaciones')

    notif_id = request.POST.get('notificacion_id', '').strip()
    destino = request.POST.get('next', '').strip()
    if notif_id.isdigit():
        notif = Notificacion.objects.filter(
            idNotificacion=int(notif_id),
            idUsuario=perfil,
            descartada=False,
        ).first()
        if notif:
            if not notif.leida:
                notif.leida = True
                notif.save(update_fields=['leida'])
            if not destino:
                destino = notif.url_destino

    if destino.startswith('/app/') and not destino.startswith('//'):
        return redirect(destino)
    return redirect('notificaciones')


@login_required
def notificacion_eliminar_view(request, notificacion_id):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')

    if request.method == 'POST':
        # Descarte lógico: evita que el motor vuelva a crear la misma alerta/evento.
        actualizadas = Notificacion.objects.filter(
            idNotificacion=notificacion_id,
            idUsuario=perfil,
            descartada=False,
        ).update(descartada=True, leida=True)
        if actualizadas:
            messages.success(request, 'Notificación eliminada.')

    return redirect('notificaciones')


# Política de privacidad y tratamiento de datos personales (Fase 2)
def privacidad_view(request):
    perfil = None
    pestana_activa = None
    if request.user.is_authenticated:
        perfil = _obtener_perfil_autenticado(request)
        if perfil is not None:
            pestana_activa = 'perfil'

    return render(request, 'privacidad.html', {
        'usuario': perfil,
        'pestana_activa': pestana_activa,
        'politica_version': POLITICA_PRIVACIDAD_VERSION,
        'politica_fecha': POLITICA_PRIVACIDAD_FECHA,
        'consentimiento_pendiente': requiere_consentimiento_vigente(perfil) if perfil else False,
    })


@login_required
def aceptar_privacidad_view(request):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')

    if request.method == 'POST':
        registrar_consentimiento_datos(perfil)
        messages.success(request, 'Consentimiento de tratamiento de datos registrado.')

    next_url = request.POST.get('next', '').strip()
    if next_url.startswith('/app/') and not next_url.startswith('//'):
        return redirect(next_url)
    return redirect('dashboard')


@login_required
def cambiar_contrasena_view(request):
    perfil = _obtener_perfil_autenticado(request)
    if perfil is None:
        return redirect('login')

    if request.method != 'POST':
        return redirect('perfil')

    actual = request.POST.get('password_actual', '')
    nueva = request.POST.get('password_nueva', '')
    confirmar = request.POST.get('password_confirmar', '')

    if not actual or not nueva or not confirmar:
        messages.error(request, 'Completa todos los campos para cambiar tu contraseña.')
        return redirect('perfil')

    if not request.user.check_password(actual):
        messages.error(request, 'Tu contraseña actual no coincide.')
        return redirect('perfil')

    if nueva != confirmar:
        messages.error(request, 'La nueva contraseña y su confirmación no coinciden.')
        return redirect('perfil')

    if actual == nueva:
        messages.error(request, 'La nueva contraseña debe ser diferente a la actual.')
        return redirect('perfil')

    errores = validar_contrasena_servidor(nueva, user=request.user)
    if errores:
        messages.error(request, errores[0])
        return redirect('perfil')

    request.user.set_password(nueva)
    request.user.save(update_fields=['password'])
    update_session_auth_hash(request, request.user)
    messages.success(request, 'Tu contraseña se actualizó correctamente.')
    return redirect('perfil')
