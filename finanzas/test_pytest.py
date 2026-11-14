from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from finanzas.models import (
    Categoria,
    MetaAhorro,
    Presupuesto,
    Prestamo,
    Transaccion,
    Usuario,
)


@pytest.fixture
def crear_estudiante(db):
    User = get_user_model()

    def _crear(correo, nombre='Estudiante Prueba', mesada='300000.00', frecuencia='quincenal'):
        cuenta = User.objects.create_user(
            username=correo,
            email=correo,
            password='Password123!'
        )
        perfil = Usuario.objects.create(
            cuenta=cuenta,
            nombre=nombre,
            universidad='Corporación Universitaria Rafael Núñez',
            frecuencia=frecuencia,
            mesada=Decimal(mesada)
        )
        return cuenta, perfil

    return _crear


@pytest.fixture
def categoria_base(db):
    cat, _ = Categoria.objects.get_or_create(nombre='Alimentación')
    return cat


@pytest.fixture
def categoria_transporte(db):
    cat, _ = Categoria.objects.get_or_create(nombre='Transporte')
    return cat


# ==============================================================================
# 1. PRUEBAS DE MODELOS
# ==============================================================================

@pytest.mark.django_db
def test_modelo_usuario_y_valores_por_defecto(crear_estudiante):
    cuenta, perfil = crear_estudiante('karla@curn.edu.co', nombre='Karla')
    assert perfil.cuenta == cuenta
    assert perfil.frecuencia == 'quincenal'
    assert perfil.mesada == Decimal('300000.00')
    assert cuenta.perfil_mishi == perfil


@pytest.mark.django_db
def test_modelo_transaccion_meta_y_prestamo(crear_estudiante, categoria_base):
    _, perfil = crear_estudiante('modelo@curn.edu.co')

    mov = Transaccion.objects.create(
        idUsuario=perfil,
        idCategoria=categoria_base,
        descripcion='Almuerzo',
        monto=Decimal('12000.00'),
        fecha=date.today(),
        tipo='gasto'
    )
    meta = MetaAhorro.objects.create(
        idUsuario=perfil,
        nombre='Portátil',
        categoria='Estudios',
        objetivo=Decimal('1500000.00')
    )
    prestamo = Prestamo.objects.create(
        idUsuario=perfil,
        deudor='Carlos',
        concepto='Copias',
        monto=Decimal('5000.00')
    )

    assert mov.idTransaccion is not None
    assert meta.acumulado == Decimal('0.00')
    assert prestamo.estado == 'Pendiente'
    assert prestamo.tipo == 'Por cobrar'


@pytest.mark.django_db
def test_modelo_borrado_en_cascada_usuario(crear_estudiante, categoria_base):
    _, perfil = crear_estudiante('cascada@curn.edu.co')
    Transaccion.objects.create(
        idUsuario=perfil,
        idCategoria=categoria_base,
        descripcion='Café',
        monto=Decimal('4000.00'),
        fecha=date.today(),
        tipo='gasto'
    )
    MetaAhorro.objects.create(
        idUsuario=perfil,
        nombre='Viaje',
        objetivo=Decimal('200000.00')
    )
    Prestamo.objects.create(
        idUsuario=perfil,
        deudor='Ana',
        concepto='Pasaje',
        monto=Decimal('3000.00')
    )

    perfil.delete()

    assert Transaccion.objects.count() == 0
    assert MetaAhorro.objects.count() == 0
    assert Prestamo.objects.count() == 0


# ==============================================================================
# 2. PRUEBAS DE FORMULARIOS Y VALIDACIONES
# ==============================================================================

@pytest.mark.django_db
def test_formulario_registro_rechaza_correo_duplicado_y_frecuencia_invalida(client, crear_estudiante):
    crear_estudiante('repetido@curn.edu.co')

    resp_dup = client.post(reverse('registro_usuario'), {
        'nombre': 'Otro',
        'universidad': 'CURN',
        'frecuencia': 'quincenal',
        'mesada': '200000',
        'correo': 'repetido@curn.edu.co',
        'pass': 'Clave1234',
    })
    assert resp_dup.status_code == 200
    assert 'Este correo ya está registrado.' in resp_dup.content.decode('utf-8')

    resp_frec = client.post(reverse('registro_usuario'), {
        'nombre': 'Nuevo',
        'universidad': 'CURN',
        'frecuencia': 'anual',
        'mesada': '200000',
        'correo': 'nuevo@curn.edu.co',
        'pass': 'Clave1234',
    })
    assert resp_frec.status_code == 200
    assert 'Selecciona una frecuencia válida.' in resp_frec.content.decode('utf-8')
    assert not Usuario.objects.filter(cuenta__username='nuevo@curn.edu.co').exists()


@pytest.mark.django_db
def test_formulario_movimiento_rechaza_monto_minimo_decimales_y_fecha_futura(client, crear_estudiante, categoria_base):
    cuenta, perfil = crear_estudiante('form@curn.edu.co')
    client.force_login(cuenta)
    manana = (date.today() + timedelta(days=1)).isoformat()

    casos_invalidos = [
        {'tipo': 'gasto', 'monto': '50', 'categoria': categoria_base.idCategoria, 'descripcion': 'Muy bajo', 'fecha': date.today().isoformat()},
        {'tipo': 'gasto', 'monto': '1500.123', 'categoria': categoria_base.idCategoria, 'descripcion': 'Decimales', 'fecha': date.today().isoformat()},
        {'tipo': 'gasto', 'monto': '5000', 'categoria': categoria_base.idCategoria, 'descripcion': 'Futura', 'fecha': manana},
    ]

    for payload in casos_invalidos:
        resp = client.post(reverse('movimiento'), payload)
        assert resp.status_code == 200

    assert Transaccion.objects.filter(idUsuario=perfil).count() == 0


@pytest.mark.django_db
def test_formulario_editar_movimiento_rechaza_mas_de_dos_decimales(client, crear_estudiante, categoria_base):
    cuenta, perfil = crear_estudiante('editform@curn.edu.co')
    client.force_login(cuenta)
    mov = Transaccion.objects.create(
        idUsuario=perfil,
        idCategoria=categoria_base,
        descripcion='Desayuno',
        monto=Decimal('8000.00'),
        fecha=date.today(),
        tipo='gasto'
    )

    resp = client.post(reverse('editar_movimiento', args=[mov.idTransaccion]), {
        'tipo': 'gasto',
        'monto': '8500.555',
        'categoria': categoria_base.idCategoria,
        'descripcion': 'Desayuno editado',
        'fecha': date.today().isoformat(),
    })

    assert resp.status_code == 200
    mov.refresh_from_db()
    assert mov.monto == Decimal('8000.00')


@pytest.mark.django_db
def test_formulario_historial_categoria_no_numerica_no_genera_error_500(client, crear_estudiante):
    cuenta, _ = crear_estudiante('histform@curn.edu.co')
    client.force_login(cuenta)

    resp = client.get(reverse('historial'), {'categoria': 'abc'})
    assert resp.status_code == 200
    assert resp.context['error_filtros'] == 'La categoría seleccionada no es válida.'


# ==============================================================================
# 3. PRUEBAS DE PERMISOS Y AISLAMIENTO ENTRE USUARIOS
# ==============================================================================

@pytest.mark.django_db
@pytest.mark.parametrize('url_name', ['dashboard', 'movimiento', 'historial', 'metas'])
def test_permisos_vistas_protegidas_redirigen_a_login(client, url_name):
    resp = client.get(reverse(url_name))
    assert resp.status_code == 302
    assert reverse('login') in resp.url


@pytest.mark.django_db
def test_permisos_usuario_no_puede_editar_ni_eliminar_movimiento_ajeno(client, crear_estudiante, categoria_base):
    _, perfil_a = crear_estudiante('dueno@curn.edu.co')
    cuenta_b, _ = crear_estudiante('intruso@curn.edu.co')

    mov_a = Transaccion.objects.create(
        idUsuario=perfil_a,
        idCategoria=categoria_base,
        descripcion='Secreto A',
        monto=Decimal('20000.00'),
        fecha=date.today(),
        tipo='gasto'
    )

    client.force_login(cuenta_b)

    resp_edit = client.post(reverse('editar_movimiento', args=[mov_a.idTransaccion]), {
        'tipo': 'gasto',
        'monto': '99999',
        'categoria': categoria_base.idCategoria,
        'descripcion': 'Hackeado',
        'fecha': date.today().isoformat(),
    })
    assert resp_edit.status_code == 302

    resp_del = client.post(reverse('eliminar_movimiento', args=[mov_a.idTransaccion]))
    assert resp_del.status_code == 302

    mov_a.refresh_from_db()
    assert mov_a.monto == Decimal('20000.00')
    assert mov_a.descripcion == 'Secreto A'


@pytest.mark.django_db
def test_permisos_usuario_no_puede_modificar_meta_ni_prestamo_ajeno(client, crear_estudiante):
    _, perfil_a = crear_estudiante('dueno_metas@curn.edu.co')
    cuenta_b, _ = crear_estudiante('otro_metas@curn.edu.co')

    meta_a = MetaAhorro.objects.create(
        idUsuario=perfil_a,
        nombre='Meta A',
        objetivo=Decimal('100000.00')
    )
    prestamo_a = Prestamo.objects.create(
        idUsuario=perfil_a,
        deudor='Luis',
        concepto='Libro',
        monto=Decimal('25000.00')
    )

    client.force_login(cuenta_b)

    client.post(reverse('metas'), {
        'accion': 'actualizar_meta',
        'meta_id': meta_a.idMeta,
        'ahorro': '50000',
    })
    client.post(reverse('metas'), {
        'accion': 'pagar_prestamo',
        'prestamo_id': prestamo_a.idPrestamo,
    })

    meta_a.refresh_from_db()
    prestamo_a.refresh_from_db()
    assert meta_a.acumulado == Decimal('0.00')
    assert prestamo_a.estado == 'Pendiente'


# ==============================================================================
# 4. PRUEBAS DE FLUJOS CRÍTICOS
# ==============================================================================

@pytest.mark.django_db
def test_flujo_critico_registro_usuario_y_categorias_por_defecto(client):
    resp = client.post(reverse('registro_usuario'), {
        'nombre': 'Camila Pérez',
        'universidad': 'CURN',
        'frecuencia': 'quincenal',
        'mesada': '300000',
        'correo': 'camila@curn.edu.co',
        'pass': 'Segura123!',
    })
    assert resp.status_code == 302
    assert resp.url == reverse('dashboard')

    resp_mov = client.get(reverse('movimiento'))
    assert resp_mov.status_code == 200
    assert Categoria.objects.exists()


@pytest.mark.django_db
def test_flujo_critico_calculo_saldo_gasto_hoy_hormiga_y_alerta_rf05(client, crear_estudiante, categoria_base):
    # Mesada 150.000 / 15 días = límite diario de $10.000
    cuenta, perfil = crear_estudiante('rf05@curn.edu.co', mesada='150000.00', frecuencia='quincenal')
    client.force_login(cuenta)

    # Gasto de hace 3 días (NO debe sumarse como gasto_hoy)
    Transaccion.objects.create(
        idUsuario=perfil,
        idCategoria=categoria_base,
        descripcion='Compra pasada',
        monto=Decimal('30000.00'),
        fecha=date.today() - timedelta(days=3),
        tipo='gasto'
    )
    # Saldo ahora = 120.000; límite diario = 120.000 / 15 = 8.000
    # Registramos un gasto hormiga hoy de $6.500 (81.25% del límite diario -> alerta preventiva)
    client.post(reverse('movimiento'), {
        'tipo': 'gasto',
        'monto': '6500',
        'categoria': categoria_base.idCategoria,
        'descripcion': 'Café y empanada',
        'fecha': date.today().isoformat(),
    })

    resp = client.get(reverse('dashboard'))
    assert resp.status_code == 200
    assert resp.context['saldo'] == Decimal('113500.00')
    assert resp.context['gasto_hoy'] == Decimal('6500.00')
    assert resp.context['total_hormiga'] == Decimal('6500.00')
    assert resp.context['alerta_activa'] is True
    assert resp.context['limite_superado'] is False

    # Agregamos otro gasto hoy de $5.000 -> gasto_hoy = $11.500 -> supera límite diario
    client.post(reverse('movimiento'), {
        'tipo': 'gasto',
        'monto': '5000',
        'categoria': categoria_base.idCategoria,
        'descripcion': 'Jugo',
        'fecha': date.today().isoformat(),
    })

    resp2 = client.get(reverse('dashboard'))
    assert resp2.context['gasto_hoy'] == Decimal('11500.00')
    assert resp2.context['total_hormiga'] == Decimal('11500.00')
    assert resp2.context['alerta_activa'] is True
    assert resp2.context['limite_superado'] is True


@pytest.mark.django_db
def test_flujo_critico_historial_filtros_edicion_y_eliminacion(client, crear_estudiante, categoria_base, categoria_transporte):
    cuenta, perfil = crear_estudiante('crud@curn.edu.co')
    client.force_login(cuenta)

    client.post(reverse('movimiento'), {
        'tipo': 'gasto',
        'monto': '10000',
        'categoria': categoria_base.idCategoria,
        'descripcion': 'Almuerzo',
        'fecha': date.today().isoformat(),
    })
    client.post(reverse('movimiento'), {
        'tipo': 'ingreso',
        'monto': '50000',
        'categoria': categoria_transporte.idCategoria,
        'descripcion': 'Reembolso',
        'fecha': date.today().isoformat(),
    })

    resp_filtro = client.get(reverse('historial'), {'categoria': str(categoria_base.idCategoria)})
    assert resp_filtro.status_code == 200
    assert len(resp_filtro.context['movimientos']) == 1
    assert resp_filtro.context['total_gastos'] == Decimal('10000.00')

    mov_id = resp_filtro.context['movimientos'][0]['id']

    resp_edit = client.post(reverse('editar_movimiento', args=[mov_id]), {
        'tipo': 'gasto',
        'monto': '15000',
        'categoria': categoria_base.idCategoria,
        'descripcion': 'Almuerzo especial',
        'fecha': date.today().isoformat(),
    })
    assert resp_edit.status_code == 302

    mov = Transaccion.objects.get(idTransaccion=mov_id)
    assert mov.monto == Decimal('15000.00')
    assert mov.descripcion == 'Almuerzo especial'

    resp_del = client.post(reverse('eliminar_movimiento', args=[mov_id]))
    assert resp_del.status_code == 302
    assert not Transaccion.objects.filter(idTransaccion=mov_id).exists()


@pytest.mark.django_db
def test_flujo_critico_metas_ahorro_y_prestamos(client, crear_estudiante):
    cuenta, perfil = crear_estudiante('metas@curn.edu.co')
    client.force_login(cuenta)

    client.post(reverse('metas'), {
        'accion': 'crear_meta',
        'nombre': 'Tablet',
        'categoria': 'Estudio',
        'objetivo': '500000',
    })
    meta = MetaAhorro.objects.get(idUsuario=perfil)

    client.post(reverse('metas'), {
        'accion': 'actualizar_meta',
        'meta_id': meta.idMeta,
        'ahorro': '125000',
    })
    meta.refresh_from_db()
    assert meta.acumulado == Decimal('125000.00')

    client.post(reverse('metas'), {
        'accion': 'crear_prestamo',
        'deudor': 'Sofía',
        'concepto': 'Materiales',
        'tipo': 'Por cobrar',
        'monto': '20000',
    })
    prestamo = Prestamo.objects.get(idUsuario=perfil)
    assert prestamo.estado == 'Pendiente'

    client.post(reverse('metas'), {
        'accion': 'pagar_prestamo',
        'prestamo_id': prestamo.idPrestamo,
    })
    prestamo.refresh_from_db()
    assert prestamo.estado == 'Pagado'


@pytest.mark.django_db
@pytest.mark.parametrize(
    'url_name',
    ['crear_meta', 'categorias', 'insights', 'perfil', 'presupuestos', 'animo'],
)
def test_permisos_nuevas_vistas_app_redirigen_a_login(client, url_name):
    resp = client.get(reverse(url_name))
    assert resp.status_code == 302
    assert reverse('login') in resp.url


@pytest.mark.django_db
def test_detalle_movimiento_aisla_usuarios_y_muestra_propio(client, crear_estudiante, categoria_base):
    cuenta_duena, perfil_dueno = crear_estudiante('duena_det@unal.edu.co')
    cuenta_otra, _ = crear_estudiante('otra_det@unal.edu.co')

    mov = Transaccion.objects.create(
        idUsuario=perfil_dueno,
        idCategoria=categoria_base,
        tipo='Gasto',
        monto=Decimal('22000.00'),
        fecha=date.today(),
        descripcion='Almuerzo facultad',
    )
    url = reverse('detalle_movimiento', args=[mov.idTransaccion])

    # Usuario distinto no puede ver el detalle del movimiento ajeno
    client.force_login(cuenta_otra)
    resp_otra = client.get(url)
    assert resp_otra.status_code == 302
    assert resp_otra.url == reverse('historial')

    # Propietaria accede con 200 y ve la descripción
    client.force_login(cuenta_duena)
    resp_duena = client.get(url)
    assert resp_duena.status_code == 200
    assert 'Almuerzo facultad' in resp_duena.content.decode('utf-8')


@pytest.mark.django_db
def test_flujo_crear_meta_perfil_presupuestos_y_vistas_secundarias(client, crear_estudiante, categoria_base):
    cuenta, perfil = crear_estudiante('app_full@unal.edu.co', nombre='Valen', mesada='500000.00')
    client.force_login(cuenta)

    Transaccion.objects.create(
        idUsuario=perfil,
        idCategoria=categoria_base,
        tipo='Gasto',
        monto=Decimal('12000.00'),
        fecha=date.today(),
        descripcion='Café campus',
    )

    # Crear meta desde la pantalla dedicada
    resp_meta = client.post(
        reverse('crear_meta'),
        {'nombre': 'Portátil', 'objetivo': '1500000', 'categoria': 'Educación'},
    )
    assert resp_meta.status_code == 302
    assert resp_meta.url == reverse('metas')
    assert MetaAhorro.objects.filter(idUsuario=perfil, nombre='Portátil', objetivo=Decimal('1500000.00')).exists()

    # Guardar límites personalizados en Presupuestos
    resp_pres = client.post(
        reverse('presupuestos'),
        {'limite_diario': '50000', 'limite_mensual': '600000'},
    )
    assert resp_pres.status_code == 302
    assert resp_pres.url == reverse('presupuestos')
    presupuesto = Presupuesto.objects.get(idUsuario=perfil)
    assert presupuesto.limiteDiario == Decimal('50000.00')
    assert presupuesto.limiteMensual == Decimal('600000.00')

    # Actualizar información en Perfil
    resp_perfil = client.post(
        reverse('perfil'),
        {
            'nombre': 'Valentina García',
            'universidad': 'Universidad Nacional',
            'frecuencia': 'mensual',
            'mesada': '800000',
        },
    )
    assert resp_perfil.status_code == 302
    assert resp_perfil.url == reverse('perfil')
    perfil.refresh_from_db()
    assert perfil.nombre == 'Valentina García'
    assert perfil.frecuencia == 'mensual'
    assert perfil.mesada == Decimal('800000.00')

    # Vistas analíticas y de descanso responden 200 sin errores
    assert client.get(reverse('categorias') + '?rango=3m').status_code == 200
    assert client.get(reverse('insights')).status_code == 200
    assert client.get(reverse('animo')).status_code == 200
