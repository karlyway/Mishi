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
        'acepto_politica_datos': '1',
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


# ==============================================================================
# 5. PRUEBAS DEL MOTOR FINANCIERO (FASE 1)
# ==============================================================================

@pytest.mark.django_db
def test_fase1_sin_doble_contabilizacion_al_editar_ingreso_esperado_ni_al_avanzar_ciclo(
    client, crear_estudiante, categoria_base
):
    from finanzas.services.finanzas_service import calcular_resumen_financiero

    cuenta, perfil = crear_estudiante('contable@curn.edu.co', mesada='300000.00', frecuencia='quincenal')
    perfil.fecha_proximo_ingreso = date(2026, 3, 1)
    perfil.save()

    # Saldo inicial queda fijado en $300.000
    assert perfil.saldo_inicial == Decimal('300000.00')

    # Cambiar ingreso esperado (mesada) en Perfil NO altera retroactivamente saldo_inicial ni saldo disponible
    client.force_login(cuenta)
    resp = client.post(reverse('perfil'), {
        'nombre': perfil.nombre,
        'universidad': perfil.universidad,
        'frecuencia': 'mensual',
        'mesada': '800000',
        'fecha_proximo_ingreso': '2026-03-01',
    })
    assert resp.status_code == 302
    perfil.refresh_from_db()
    assert perfil.mesada == Decimal('800000.00')
    assert perfil.saldo_inicial == Decimal('300000.00')

    # Avanzar el reloj 2 meses despues de la fecha estimada NO agrega dinero automaticamente al saldo
    resumen_futuro = calcular_resumen_financiero(perfil, hoy=date(2026, 5, 10))
    assert resumen_futuro['saldo_disponible'] == Decimal('300000.00')
    assert resumen_futuro['ciclo']['ciclos_avanzados'] == 3
    assert resumen_futuro['ciclo']['fecha_proximo_ingreso'] == date(2026, 6, 1)


@pytest.mark.django_db
def test_fase1_dos_ingresos_legitimos_mismo_monto_y_fecha_se_contabilizan_ambos(
    client, crear_estudiante, categoria_base
):
    from finanzas.services.finanzas_service import calcular_resumen_financiero

    cuenta, perfil = crear_estudiante('ingresos_iguales@curn.edu.co', mesada='100000.00')
    client.force_login(cuenta)
    hoy = date.today()

    for desc in ('Monitoría mañana', 'Monitoría tarde'):
        resp = client.post(reverse('movimiento'), {
            'tipo': 'ingreso',
            'monto': '50000',
            'categoria': categoria_base.idCategoria,
            'descripcion': desc,
            'fecha': hoy.isoformat(),
        })
        assert resp.status_code == 302

    assert Transaccion.objects.filter(idUsuario=perfil, tipo='ingreso').count() == 2
    resumen = calcular_resumen_financiero(perfil, hoy=hoy)
    assert resumen['ingresos_recibidos'] == Decimal('100000.00')
    assert resumen['ingresos_hoy'] == Decimal('100000.00')
    assert resumen['saldo_disponible'] == Decimal('200000.00')


@pytest.mark.django_db
def test_fase1_gastos_consecutivos_hoy_no_reducen_limite_diario_y_calculan_restante_exacto(
    crear_estudiante, categoria_base
):
    from finanzas.services.finanzas_service import calcular_resumen_financiero

    hoy = date(2026, 11, 25)
    _, perfil = crear_estudiante('gastos_dia@curn.edu.co', mesada='150000.00', frecuencia='quincenal')
    perfil.fecha_proximo_ingreso = hoy + timedelta(days=15)
    perfil.save()

    # Inicio del dia: saldo 150.000 / 15 dias = limite diario $10.000
    r0 = calcular_resumen_financiero(perfil, hoy=hoy)
    assert r0['saldo_inicio_dia'] == Decimal('150000.00')
    assert r0['limite_diario_recomendado'] == Decimal('10000.00')
    assert r0['dinero_restante_hoy'] == Decimal('10000.00')

    # Primer gasto hoy de $4.000 -> limite sigue en $10.000, restante = $6.000
    Transaccion.objects.create(
        idUsuario=perfil, idCategoria=categoria_base, descripcion='Desayuno',
        monto=Decimal('4000.00'), fecha=hoy, tipo='gasto'
    )
    r1 = calcular_resumen_financiero(perfil, hoy=hoy)
    assert r1['saldo_disponible'] == Decimal('146000.00')
    assert r1['limite_diario_recomendado'] == Decimal('10000.00')
    assert r1['gasto_hoy'] == Decimal('4000.00')
    assert r1['dinero_restante_hoy'] == Decimal('6000.00')
    assert r1['estado_alerta_diaria'] == 'normal'

    # Segundo gasto hoy de $4.000 (total $8.000 = 80% exacto) -> alerta preventiva, limite sigue en $10.000
    Transaccion.objects.create(
        idUsuario=perfil, idCategoria=categoria_base, descripcion='Almuerzo',
        monto=Decimal('4000.00'), fecha=hoy, tipo='gasto'
    )
    r2 = calcular_resumen_financiero(perfil, hoy=hoy)
    assert r2['limite_diario_recomendado'] == Decimal('10000.00')
    assert r2['gasto_hoy'] == Decimal('8000.00')
    assert r2['dinero_restante_hoy'] == Decimal('2000.00')
    assert r2['estado_alerta_diaria'] == 'preventiva'
    assert r2['alerta_preventiva'] is True
    assert r2['limite_superado'] is False

    # Tercer gasto hoy de $2.000 (total $10.000 = 100% exacto) -> sigue en advertencia preventiva, NO superado
    Transaccion.objects.create(
        idUsuario=perfil, idCategoria=categoria_base, descripcion='Jugo',
        monto=Decimal('2000.00'), fecha=hoy, tipo='gasto'
    )
    r3 = calcular_resumen_financiero(perfil, hoy=hoy)
    assert r3['porcentaje_gasto_hoy'] == 100.0
    assert r3['estado_alerta_diaria'] == 'preventiva'
    assert r3['limite_superado'] is False
    assert r3['dinero_restante_hoy'] == Decimal('0.00')

    # Cuarto gasto hoy de $1.000 (total $11.000 = 110% > 100%) -> limite superado
    Transaccion.objects.create(
        idUsuario=perfil, idCategoria=categoria_base, descripcion='Menta',
        monto=Decimal('1000.00'), fecha=hoy, tipo='gasto'
    )
    r4 = calcular_resumen_financiero(perfil, hoy=hoy)
    assert r4['limite_diario_recomendado'] == Decimal('10000.00')
    assert r4['estado_alerta_diaria'] == 'superado'
    assert r4['limite_superado'] is True
    assert r4['excedente_hoy'] == Decimal('1000.00')


@pytest.mark.django_db
def test_fase1_ingreso_hoy_edicion_cambio_fecha_y_eliminacion_recalculan_correctamente(
    crear_estudiante, categoria_base
):
    from finanzas.services.finanzas_service import calcular_resumen_financiero

    hoy = date(2026, 11, 25)
    ayer = hoy - timedelta(days=1)
    _, perfil = crear_estudiante('recalculo@curn.edu.co', mesada='100000.00', frecuencia='semanal')
    perfil.fecha_proximo_ingreso = hoy + timedelta(days=10)
    perfil.save()

    # Ingreso recibido HOY de $50.000 -> base_disponible_hoy = $150.000 -> limite = $15.000/dia
    Transaccion.objects.create(
        idUsuario=perfil, idCategoria=categoria_base, descripcion='Trabajo hoy',
        monto=Decimal('50000.00'), fecha=hoy, tipo='ingreso'
    )
    gasto = Transaccion.objects.create(
        idUsuario=perfil, idCategoria=categoria_base, descripcion='Almuerzo',
        monto=Decimal('10000.00'), fecha=hoy, tipo='gasto'
    )
    r_hoy = calcular_resumen_financiero(perfil, hoy=hoy)
    assert r_hoy['base_disponible_hoy'] == Decimal('150000.00')
    assert r_hoy['limite_diario_recomendado'] == Decimal('15000.00')
    assert r_hoy['dinero_restante_hoy'] == Decimal('5000.00')

    # Cambiar fecha del gasto de hoy -> ayer reduce saldo_inicio_dia a $90.000 y gasto_hoy a $0
    gasto.fecha = ayer
    gasto.save()
    r_movido = calcular_resumen_financiero(perfil, hoy=hoy)
    assert r_movido['saldo_inicio_dia'] == Decimal('90000.00')
    assert r_movido['base_disponible_hoy'] == Decimal('140000.00')
    assert r_movido['limite_diario_recomendado'] == Decimal('14000.00')
    assert r_movido['gasto_hoy'] == Decimal('0.00')

    # Editar monto del gasto a $20.000 y luego eliminarlo
    gasto.monto = Decimal('20000.00')
    gasto.save()
    r_editado = calcular_resumen_financiero(perfil, hoy=hoy)
    assert r_editado['saldo_disponible'] == Decimal('130000.00')

    gasto.delete()
    r_borrado = calcular_resumen_financiero(perfil, hoy=hoy)
    assert r_borrado['saldo_disponible'] == Decimal('150000.00')
    assert r_borrado['limite_diario_recomendado'] == Decimal('15000.00')


@pytest.mark.django_db
def test_fase1_saldo_cero_negativo_y_reconciliacion_metas(crear_estudiante, categoria_base):
    from finanzas.services.finanzas_service import calcular_resumen_financiero

    hoy = date(2026, 11, 25)
    _, perfil = crear_estudiante('saldo_cero@curn.edu.co', mesada='50000.00', frecuencia='semanal')

    # Reservar $20.000 en meta -> saldo_total $50.000, disponible $30.000
    MetaAhorro.objects.create(
        idUsuario=perfil, nombre='Libros', objetivo=Decimal('100000.00'), acumulado=Decimal('20000.00')
    )
    r_meta = calcular_resumen_financiero(perfil, hoy=hoy)
    assert r_meta['saldo_total'] == Decimal('50000.00')
    assert r_meta['dinero_reservado_metas'] == Decimal('20000.00')
    assert r_meta['saldo_disponible'] == Decimal('30000.00')
    assert r_meta['saldo_disponible'] + r_meta['dinero_reservado_metas'] == r_meta['saldo_total']

    # Gasto ayer por $30.000 -> saldo disponible = $0 sin gasto hoy -> alerta independiente de saldo insuficiente
    g_ayer = Transaccion.objects.create(
        idUsuario=perfil, idCategoria=categoria_base, descripcion='Mercado',
        monto=Decimal('30000.00'), fecha=hoy - timedelta(days=1), tipo='gasto'
    )
    r_cero = calcular_resumen_financiero(perfil, hoy=hoy)
    assert r_cero['saldo_disponible'] == Decimal('0.00')
    assert r_cero['limite_diario_activo'] == Decimal('0.00')
    assert r_cero['alerta_saldo_insuficiente'] is True
    assert r_cero['alerta_activa'] is True
    assert r_cero['alerta_principal']['tipo'] == 'saldo_insuficiente'

    # Gasto mayor -> saldo negativo (-$10.000)
    g_ayer.monto = Decimal('40000.00')
    g_ayer.save()
    r_neg = calcular_resumen_financiero(perfil, hoy=hoy)
    assert r_neg['saldo_disponible'] == Decimal('-10000.00')
    assert r_neg['limite_diario_activo'] == Decimal('0.00')
    assert r_neg['dinero_restante_hoy'] == Decimal('0.00')
    assert r_neg['alerta_saldo_insuficiente'] is True


@pytest.mark.django_db
def test_fase1_ciclo_fin_de_mes_anio_bisiesto_irregular_y_sin_division_por_cero(crear_estudiante):
    from finanzas.services.finanzas_service import avanzar_fecha_ciclo, calcular_ciclo_financiero, sumar_un_mes

    # Meses de distinta duracion y preservacion del dia ancla 31
    assert sumar_un_mes(date(2026, 1, 31), dia_ancla=31) == date(2026, 2, 28)
    assert sumar_un_mes(date(2026, 2, 28), dia_ancla=31) == date(2026, 3, 31)
    assert sumar_un_mes(date(2026, 3, 31), dia_ancla=31) == date(2026, 4, 30)

    # Anio bisiesto 2028
    assert sumar_un_mes(date(2028, 1, 31), dia_ancla=31) == date(2028, 2, 29)
    assert sumar_un_mes(date(2028, 2, 29), dia_ancla=31) == date(2028, 3, 31)

    # Proyeccion vencida multi-mes en anio bisiesto
    proy, saltos, vencido = avanzar_fecha_ciclo(date(2028, 1, 31), 'mensual', date(2028, 2, 15), dia_ancla=31)
    assert proy == date(2028, 2, 29)
    assert saltos == 1
    assert vencido is True

    # Fecha de proximo ingreso igual a HOY -> dias_restantes = 1 (nunca divide por cero)
    _, perfil = crear_estudiante('ciclos@curn.edu.co', mesada='100000.00', frecuencia='mensual')
    perfil.fecha_proximo_ingreso = date(2026, 11, 25)
    perfil.save()
    ciclo_hoy = calcular_ciclo_financiero(perfil, hoy=date(2026, 11, 25))
    assert ciclo_hoy['dias_restantes'] == 1

    # Usuario con ingresos irregulares y fecha vencida: no inventa nueva fecha ni suma dinero
    perfil.frecuencia = 'irregular'
    perfil.fecha_proximo_ingreso = date(2026, 11, 10)
    perfil.save()
    ciclo_irr = calcular_ciclo_financiero(perfil, hoy=date(2026, 11, 25))
    assert ciclo_irr['ciclo_vencido'] is True
    assert ciclo_irr['requiere_fecha_ciclo'] is True
    assert ciclo_irr['dias_restantes'] == 1
    assert ciclo_irr['fecha_proximo_ingreso'] == date(2026, 11, 10)


@pytest.mark.django_db
def test_fase1_consistencia_alertas_entre_dashboard_insights_y_presupuestos_y_aislamiento(
    client, crear_estudiante, categoria_base
):
    cuenta_a, perfil_a = crear_estudiante('cons_a@curn.edu.co', mesada='300000.00', frecuencia='quincenal')
    _, perfil_b = crear_estudiante('cons_b@curn.edu.co', mesada='10000.00', frecuencia='diario')

    # Datos de usuario B no deben afectar a usuario A
    Presupuesto.objects.create(idUsuario=perfil_b, limiteDiario=Decimal('1000.00'), limiteMensual=Decimal('30000.00'))
    MetaAhorro.objects.create(idUsuario=perfil_b, nombre='Ajena', objetivo=Decimal('10000.00'), acumulado=Decimal('9000.00'))

    # Usuario A configura limite diario personalizado $50.000 y gasta $15.000 hoy (30% -> normal)
    Presupuesto.objects.create(idUsuario=perfil_a, limiteDiario=Decimal('50000.00'), limiteMensual=Decimal('600000.00'))
    Transaccion.objects.create(
        idUsuario=perfil_a, idCategoria=categoria_base, descripcion='Almuerzo',
        monto=Decimal('15000.00'), fecha=date.today(), tipo='gasto'
    )

    client.force_login(cuenta_a)
    r_dash = client.get(reverse('dashboard'))
    r_pres = client.get(reverse('presupuestos'))
    r_ins = client.get(reverse('insights'))

    # Mismo limite diario activo ($50.000) y cero contradiccion de limite_superado en las 3 pantallas
    assert r_dash.context['limite_diario'] == Decimal('50000.00')
    assert r_ins.context['resumen']['limite_diario_activo'] == Decimal('50000.00')
    assert r_pres.context['limite_diario_fmt'] == '50.000'
    assert r_dash.context['limite_superado'] is False
    assert r_pres.context['limite_superado_hoy'] is False
    # Pero saldo $285.000 no alcanza para $50.000 x 15 dias ($750.000) -> alerta de saldo ajustado consistente
    assert r_dash.context['alerta_saldo_insuficiente'] is True
    assert r_pres.context['alerta_saldo_insuficiente'] is True
    assert r_dash.context['saldo'] == Decimal('285000.00')


# ==============================================================================
# 6. PRUEBAS DE AVATARES PERSONALIZADOS Y PREFERENCIAS PERSISTENTES
# ==============================================================================

@pytest.mark.django_db
def test_avatares_registro_seleccion_y_persistencia_en_bd(client):
    resp = client.post(reverse('registro_usuario'), {
        'nombre': 'Luna Gato',
        'universidad': 'CURN',
        'frecuencia': 'quincenal',
        'mesada': '250000',
        'correo': 'luna@curn.edu.co',
        'pass': 'ClaveSegura1!',
        'avatar': 'mishi-negro-capucha',
        'acepto_politica_datos': '1',
    })
    assert resp.status_code == 302
    perfil = Usuario.objects.get(cuenta__username='luna@curn.edu.co')
    assert perfil.avatar == 'mishi-negro-capucha'

    # Se visualiza el avatar seleccionado en Dashboard (navbar) y en Perfil
    resp_dash = client.get(reverse('dashboard'))
    assert 'img/mishi-avatars/avatars/mishi-negro-capucha.png' in resp_dash.content.decode('utf-8')
    resp_perf = client.get(reverse('perfil'))
    assert 'img/mishi-avatars/avatars/mishi-negro-capucha.png' in resp_perf.content.decode('utf-8')


@pytest.mark.django_db
def test_avatares_cambio_preferencias_validacion_y_aislamiento(client, crear_estudiante):
    cuenta_a, perfil_a = crear_estudiante('av_a@curn.edu.co', nombre='Ana')
    _, perfil_b = crear_estudiante('av_b@curn.edu.co', nombre='Beto')
    client.force_login(cuenta_a)

    # Cambiar avatar a uno valido de la coleccion de 15 PNGs y preferencias persistentes
    resp_ok = client.post(reverse('perfil_preferencias'), {
        'avatar': 'mishi-blanco-gafas',
        'ocultar_saldo': '1',
        'alertas_activas': '0',
        'tema_visual': 'pure',
    })
    assert resp_ok.status_code == 302
    perfil_a.refresh_from_db()
    perfil_b.refresh_from_db()
    assert perfil_a.avatar == 'mishi-blanco-gafas'
    assert perfil_a.ocultar_saldo is True
    assert perfil_a.alertas_activas is False
    assert perfil_a.tema_visual == 'pure'
    # Aislamiento: usuario B mantiene valores por defecto intactos
    assert perfil_b.avatar == 'mishi-naranja-feliz'
    assert perfil_b.ocultar_saldo is False

    # Rechaza avatar invalido o intento de path traversal
    resp_bad = client.post(
        reverse('perfil_preferencias'),
        {'avatar': '../../etc/passwd'},
        HTTP_X_REQUESTED_WITH='XMLHttpRequest',
    )
    assert resp_bad.status_code == 400
    perfil_a.refresh_from_db()
    assert perfil_a.avatar == 'mishi-blanco-gafas'


# ==============================================================================
# 7. PRUEBAS DE NOTIFICACIONES REALES IN-APP
# ==============================================================================

@pytest.mark.django_db
def test_notificaciones_generacion_real_deduplicacion_y_lectura(client, crear_estudiante, categoria_base):
    from finanzas.models import Notificacion

    cuenta, perfil = crear_estudiante('notif@curn.edu.co', mesada='150000.00', frecuencia='quincenal')
    # Limite diario = $10.000; gasto hoy de $8.500 (85% -> alerta preventiva) + meta lograda + prestamo pendiente
    Transaccion.objects.create(
        idUsuario=perfil, idCategoria=categoria_base, descripcion='Almuerzo',
        monto=Decimal('8500.00'), fecha=date.today(), tipo='gasto'
    )
    MetaAhorro.objects.create(
        idUsuario=perfil, nombre='Audífonos', objetivo=Decimal('20000.00'), acumulado=Decimal('20000.00')
    )
    Prestamo.objects.create(
        idUsuario=perfil, deudor='Mateo', concepto='Copias', monto=Decimal('5000.00'), estado='Pendiente'
    )

    client.force_login(cuenta)
    resp1 = client.get(reverse('notificaciones'))
    assert resp1.status_code == 200
    tipos = set(Notificacion.objects.filter(idUsuario=perfil).values_list('tipo', flat=True))
    assert {'alerta_80', 'meta_lograda', 'prestamo_pendiente'}.issubset(tipos)
    conteo_inicial = Notificacion.objects.filter(idUsuario=perfil).count()

    # Recargar varias veces NO duplica notificaciones del mismo dia/evento
    client.get(reverse('notificaciones'))
    client.get(reverse('dashboard'))
    assert Notificacion.objects.filter(idUsuario=perfil).count() == conteo_inicial

    # Marcar una notificacion como leida redirige a su destino
    una = Notificacion.objects.filter(idUsuario=perfil, tipo='meta_lograda').first()
    resp_leer = client.post(reverse('notificaciones_leer'), {'notificacion_id': str(una.idNotificacion)})
    assert resp_leer.status_code == 302
    assert resp_leer.url == '/app/metas/'
    una.refresh_from_db()
    assert una.leida is True

    # Marcar todas como leidas deja no_leidas en 0
    resp_all = client.post(reverse('notificaciones_leer'), {'todas': '1'})
    assert resp_all.status_code == 302
    assert Notificacion.objects.filter(idUsuario=perfil, leida=False).count() == 0


@pytest.mark.django_db
def test_notificaciones_aislamiento_entre_usuarios_y_eliminacion(client, crear_estudiante, categoria_base):
    from finanzas.models import Notificacion

    cuenta_a, perfil_a = crear_estudiante('notif_a@curn.edu.co', mesada='50000.00')
    cuenta_b, _ = crear_estudiante('notif_b@curn.edu.co', mesada='50000.00')
    notif_a = Notificacion.objects.create(
        idUsuario=perfil_a, clave='manual_a', tipo='info', nivel='info',
        titulo='Privada A', mensaje='Solo para A', url_destino='/app/', leida=False
    )

    # Usuario B no puede leer ni eliminar la notificacion de A
    client.force_login(cuenta_b)
    client.post(reverse('notificaciones_leer'), {'notificacion_id': str(notif_a.idNotificacion)})
    client.post(reverse('notificacion_eliminar', args=[notif_a.idNotificacion]))
    notif_a.refresh_from_db()
    assert notif_a.leida is False

    # Usuario A si puede eliminar su propia notificacion (descarte logico para evitar reaparicion)
    client.force_login(cuenta_a)
    resp_del = client.post(reverse('notificacion_eliminar', args=[notif_a.idNotificacion]))
    assert resp_del.status_code == 302
    notif_a.refresh_from_db()
    assert notif_a.descartada is True
    assert notif_a.leida is True
    assert not Notificacion.objects.filter(idNotificacion=notif_a.idNotificacion, descartada=False).exists()


# ==============================================================================
# 8. VERIFICACION DE NOTIFICACIONES (NO REAPARICION, PREFERENCIAS, RENDIMIENTO)
#    Y SEGURIDAD / PRIVACIDAD (FASE 2)
# ==============================================================================

@pytest.mark.django_db
def test_notificaciones_eliminada_no_reaparece_por_el_mismo_evento(client, crear_estudiante, categoria_base):
    from finanzas.models import Notificacion
    from finanzas.services.notificaciones_service import sincronizar_notificaciones_usuario

    cuenta, perfil = crear_estudiante('no_reaparece@curn.edu.co', mesada='150000.00', frecuencia='quincenal')
    # Limite diario = $10.000 -> gasto hoy $8.500 (85%, alerta_80) + meta lograda
    Transaccion.objects.create(
        idUsuario=perfil, idCategoria=categoria_base, descripcion='Almuerzo',
        monto=Decimal('8500.00'), fecha=date.today(), tipo='gasto'
    )
    MetaAhorro.objects.create(
        idUsuario=perfil, nombre='Libros', objetivo=Decimal('10000.00'), acumulado=Decimal('10000.00')
    )

    client.force_login(cuenta)
    resp = client.get(reverse('notificaciones'))
    assert resp.status_code == 200
    alerta_80 = Notificacion.objects.get(idUsuario=perfil, tipo='alerta_80', descartada=False)
    meta_ok = Notificacion.objects.get(idUsuario=perfil, tipo='meta_lograda', descartada=False)

    # El usuario elimina ambas notificaciones
    client.post(reverse('notificacion_eliminar', args=[alerta_80.idNotificacion]))
    client.post(reverse('notificacion_eliminar', args=[meta_ok.idNotificacion]))

    # Re-sincronizar y navegar varias veces NO vuelve a mostrar ni recrear esos eventos
    sincronizar_notificaciones_usuario(perfil)
    resp_after = client.get(reverse('notificaciones'))
    client.get(reverse('dashboard'))
    assert resp_after.status_code == 200
    assert Notificacion.objects.filter(idUsuario=perfil, tipo='alerta_80', descartada=False).count() == 0
    assert Notificacion.objects.filter(idUsuario=perfil, tipo='meta_lograda', descartada=False).count() == 0
    assert resp_after.context['total_notificaciones'] == 0


@pytest.mark.django_db
def test_preferencias_usuario_funcionan_de_extremo_a_extremo(client, crear_estudiante, categoria_base):
    from finanzas.models import Notificacion

    cuenta, perfil = crear_estudiante('prefs_e2e@curn.edu.co', mesada='150000.00', frecuencia='quincenal')
    Transaccion.objects.create(
        idUsuario=perfil, idCategoria=categoria_base, descripcion='Almuerzo',
        monto=Decimal('8500.00'), fecha=date.today(), tipo='gasto'
    )
    client.force_login(cuenta)

    # Desactivar alertas, ocultar saldo y elegir tema blanco
    resp_pref = client.post(reverse('perfil_preferencias'), {
        'alertas_activas': '0',
        'ocultar_saldo': '1',
        'tema_visual': 'pure',
    })
    assert resp_pref.status_code == 302

    # En Dashboard se reflejan las 3 preferencias desde el servidor
    resp_dash = client.get(reverse('dashboard'))
    html_dash = resp_dash.content.decode('utf-8')
    assert 'data-mishi-theme="pure"' in html_dash
    assert '$••••••' in html_dash
    assert 'id="mishi-home-alert"' not in html_dash

    # Con alertas_activas=False no se generan avisos de limite/presupuesto/hormiga
    resp_notif = client.get(reverse('notificaciones'))
    assert 'Alertas de límite pausadas.' in resp_notif.content.decode('utf-8')
    assert Notificacion.objects.filter(
        idUsuario=perfil,
        tipo__in=('alerta_80', 'limite_superado', 'saldo_insuficiente', 'presupuesto_mensual', 'hormiga'),
        descartada=False,
    ).count() == 0

    # Al reactivar alertas_activas=1, el aviso se genera y vuelve a aparecer en Inicio
    client.post(reverse('perfil_preferencias'), {'alertas_activas': '1'})
    assert Notificacion.objects.filter(idUsuario=perfil, tipo='alerta_80', descartada=False).count() == 1
    resp_dash2 = client.get(reverse('dashboard'))
    assert 'id="mishi-home-alert"' in resp_dash2.content.decode('utf-8')


@pytest.mark.django_db
def test_notificaciones_navegacion_normal_usa_conteo_liviano_sin_resincronizar(
    client, crear_estudiante, monkeypatch
):
    import finanzas.context_processors as cp

    cuenta, _ = crear_estudiante('perf_notif@curn.edu.co', mesada='200000.00')
    client.force_login(cuenta)

    # Primera carga del dia sincroniza y marca la sesion
    assert client.get(reverse('dashboard')).status_code == 200

    llamadas = {'sync': 0}
    real_sync = cp.sincronizar_notificaciones_usuario

    def spy_sync(*args, **kwargs):
        llamadas['sync'] += 1
        return real_sync(*args, **kwargs)

    monkeypatch.setattr(cp, 'sincronizar_notificaciones_usuario', spy_sync)

    # Navegacion normal por multiples pantallas NO re-ejecuta sincronizacion completa
    for ruta in ('dashboard', 'historial', 'perfil', 'presupuestos'):
        assert client.get(reverse(ruta)).status_code == 200
    assert llamadas['sync'] == 0


def test_fase2_validacion_configuracion_produccion_rechaza_insegura_y_sin_hsts_prematuro():
    from django.conf import settings as dj_settings
    from django.core.exceptions import ImproperlyConfigured
    from mishi_project.settings import validar_configuracion_produccion

    clave_valida = 'MishiProdKey_9f8e7d6c5b4a3210_segura_2026!'

    # Rechaza SECRET_KEY ausente, django-insecure o corta en produccion
    for bad_key in ('', 'django-insecure-123456789012345678901234567890', 'corta123'):
        with pytest.raises(ImproperlyConfigured):
            validar_configuracion_produccion(False, bad_key, 'mishi.app')

    # Rechaza ALLOWED_HOSTS vacio o comodin '*' en produccion
    for bad_hosts in ('', '*', 'mishi.app,*'):
        with pytest.raises(ImproperlyConfigured):
            validar_configuracion_produccion(False, clave_valida, bad_hosts)

    # Acepta configuracion productiva valida
    key_ok, hosts_ok = validar_configuracion_produccion(False, clave_valida, 'mishi.app, www.mishi.app')
    assert key_ok == clave_valida
    assert hosts_ok == ['mishi.app', 'www.mishi.app']

    # Endurecimiento de cookies y headers activos; HSTS no forzado prematuramente
    assert dj_settings.SESSION_COOKIE_HTTPONLY is True
    assert dj_settings.SESSION_COOKIE_SAMESITE == 'Lax'
    assert dj_settings.CSRF_COOKIE_SAMESITE == 'Lax'
    assert dj_settings.SECURE_CONTENT_TYPE_NOSNIFF is True
    assert dj_settings.X_FRAME_OPTIONS == 'DENY'
    assert getattr(dj_settings, 'SECURE_HSTS_SECONDS', 0) == 0


@pytest.mark.django_db
def test_fase2_registro_exige_consentimiento_y_contrasena_fuerte_en_servidor(client):
    from finanzas.services.seguridad_service import POLITICA_PRIVACIDAD_VERSION

    base_payload = {
        'nombre': 'Mateo Torres',
        'universidad': 'CURN',
        'frecuencia': 'quincenal',
        'mesada': '250000',
        'correo': 'mateo_sec@curn.edu.co',
        'pass': 'ClaveSegura2026!',
    }

    # Sin aceptar politica de datos -> rechazado
    resp_no_consent = client.post(reverse('registro_usuario'), base_payload)
    assert resp_no_consent.status_code == 200
    assert 'política de tratamiento de datos' in resp_no_consent.content.decode('utf-8').lower()
    assert not Usuario.objects.filter(cuenta__username='mateo_sec@curn.edu.co').exists()

    # Contrasenas debiles rechazadas por AUTH_PASSWORD_VALIDATORS del servidor
    for weak_pw in ('123456', '12345678', 'password'):
        resp_weak = client.post(reverse('registro_usuario'), {
            **base_payload,
            'pass': weak_pw,
            'acepto_politica_datos': '1',
        })
        assert resp_weak.status_code == 200
        assert not Usuario.objects.filter(cuenta__username='mateo_sec@curn.edu.co').exists()

    # Registro completo valido persiste consentimiento, fecha y version
    resp_ok = client.post(reverse('registro_usuario'), {
        **base_payload,
        'acepto_politica_datos': '1',
    })
    assert resp_ok.status_code == 302
    perfil = Usuario.objects.get(cuenta__username='mateo_sec@curn.edu.co')
    assert perfil.acepto_politica_datos is True
    assert perfil.fecha_aceptacion_datos is not None
    assert perfil.version_politica_datos == POLITICA_PRIVACIDAD_VERSION


@pytest.mark.django_db
def test_fase2_usuario_existente_puede_leer_y_aceptar_politica_privacidad(client, crear_estudiante):
    from finanzas.services.seguridad_service import POLITICA_PRIVACIDAD_VERSION

    # Pagina publica accesible sin autenticacion
    assert client.get(reverse('privacidad')).status_code == 200

    # Usuario existente sin consentimiento previo ve el aviso discreto
    cuenta, perfil = crear_estudiante('legacy_priv@curn.edu.co', nombre='Laura')
    assert perfil.acepto_politica_datos is False
    client.force_login(cuenta)

    resp_before = client.get(reverse('dashboard'))
    assert 'm-consent-bar' in resp_before.content.decode('utf-8')

    # Aceptar protege contra open-redirect y registra fecha + version
    resp_accept = client.post(reverse('aceptar_privacidad'), {'next': 'https://evil.example/phish'})
    assert resp_accept.status_code == 302
    assert resp_accept.url == reverse('dashboard')

    perfil.refresh_from_db()
    assert perfil.acepto_politica_datos is True
    assert perfil.fecha_aceptacion_datos is not None
    assert perfil.version_politica_datos == POLITICA_PRIVACIDAD_VERSION

    # Al recargar, el aviso ya no aparece
    resp_after = client.get(reverse('dashboard'))
    assert 'm-consent-bar' not in resp_after.content.decode('utf-8')


@pytest.mark.django_db
def test_fase2_cambio_contrasena_en_perfil_valida_y_mantiene_sesion(client, crear_estudiante):
    from django.contrib.auth import authenticate

    cuenta, _ = crear_estudiante('pw_change@curn.edu.co', nombre='Sofía')
    client.force_login(cuenta)

    # Rechaza contrasena actual incorrecta
    client.post(reverse('cambiar_contrasena'), {
        'password_actual': 'Incorrecta999!',
        'password_nueva': 'NuevaClave2026!',
        'password_confirmar': 'NuevaClave2026!',
    })
    cuenta.refresh_from_db()
    assert cuenta.check_password('Password123!') is True

    # Rechaza contrasena nueva debil
    client.post(reverse('cambiar_contrasena'), {
        'password_actual': 'Password123!',
        'password_nueva': '12345678',
        'password_confirmar': '12345678',
    })
    cuenta.refresh_from_db()
    assert cuenta.check_password('Password123!') is True

    # Cambio valido actualiza hash y conserva sesion activa
    resp_ok = client.post(reverse('cambiar_contrasena'), {
        'password_actual': 'Password123!',
        'password_nueva': 'NuevaClaveSegura9!',
        'password_confirmar': 'NuevaClaveSegura9!',
    })
    assert resp_ok.status_code == 302
    assert resp_ok.url == reverse('perfil')
    assert client.get(reverse('perfil')).status_code == 200
    assert authenticate(username='pw_change@curn.edu.co', password='NuevaClaveSegura9!') is not None


@pytest.mark.django_db
def test_fase2_aislamiento_post_y_csrf_en_endpoints_mutantes(crear_estudiante):
    from django.test import Client as DjangoClient
    from finanzas.models import Notificacion

    cuenta, perfil = crear_estudiante('csrf_check@curn.edu.co')
    notif = Notificacion.objects.create(
        idUsuario=perfil, clave='csrf_test', tipo='info', nivel='info',
        titulo='Aviso', mensaje='Prueba CSRF', url_destino='/app/', leida=False
    )

    # Sin autenticacion redirigen a login
    anon = DjangoClient()
    for url in (
        reverse('perfil_preferencias'),
        reverse('cambiar_contrasena'),
        reverse('aceptar_privacidad'),
        reverse('notificaciones'),
        reverse('notificaciones_leer'),
        reverse('notificacion_eliminar', args=[notif.idNotificacion]),
    ):
        resp = anon.get(url)
        assert resp.status_code == 302
        assert reverse('login') in resp.url

    # Con CSRF enforced, POST sin token devuelve 403 Forbidden
    csrf_client = DjangoClient(enforce_csrf_checks=True)
    csrf_client.force_login(cuenta)
    for url, data in (
        (reverse('perfil_preferencias'), {'ocultar_saldo': '1'}),
        (reverse('cambiar_contrasena'), {'password_actual': 'Password123!', 'password_nueva': 'OtraClave99!', 'password_confirmar': 'OtraClave99!'}),
        (reverse('aceptar_privacidad'), {}),
        (reverse('notificaciones_leer'), {'todas': '1'}),
        (reverse('notificacion_eliminar', args=[notif.idNotificacion]), {}),
    ):
        assert csrf_client.post(url, data).status_code == 403

    # GET a endpoints mutantes nunca modifica datos
    csrf_client.get(reverse('perfil_preferencias') + '?ocultar_saldo=1')
    csrf_client.get(reverse('aceptar_privacidad'))
    csrf_client.get(reverse('notificacion_eliminar', args=[notif.idNotificacion]))
    perfil.refresh_from_db()
    notif.refresh_from_db()
    assert perfil.ocultar_saldo is False
    assert perfil.acepto_politica_datos is False
    assert notif.descartada is False


# ==============================================================================
# 9. PRUEBAS DE FASE 3 (RF-02, RF-08, RF-09, RF-10, RF-11, RF-12, RF-13)
# ==============================================================================

@pytest.mark.django_db
def test_rf02_categorias_personalizadas_crud_uso_y_aislamiento(client, crear_estudiante):
    cuenta_a, perfil_a = crear_estudiante('cat_a@curn.edu.co', nombre='Ana')
    cuenta_b, perfil_b = crear_estudiante('cat_b@curn.edu.co', nombre='Beto')
    client.force_login(cuenta_a)

    # Crear 4 categorías personalizadas (supera el mínimo de 3 de RF-02)
    for nombre, tono in (
        ('Gimnasio', 'green'),
        ('Fotocopias', 'indigo'),
        ('Mascota', 'orange'),
        ('Suscripciones', 'rose'),
    ):
        resp = client.post(reverse('categoria_crear'), {
            'nombre': nombre,
            'tipo_aplicable': 'gasto',
            'tono': tono,
        })
        assert resp.status_code == 302

    cats_a = Categoria.objects.filter(idUsuario=perfil_a, es_personalizada=True)
    assert cats_a.count() == 4
    cat_gym = cats_a.get(nombre='Gimnasio')
    cat_mascota = cats_a.get(nombre='Mascota')

    # Usar categoría personalizada en una transacción real
    resp_mov = client.post(reverse('movimiento'), {
        'tipo': 'gasto',
        'monto': '45000',
        'categoria': cat_gym.idCategoria,
        'descripcion': 'Mensualidad gym',
        'fecha': date.today().isoformat(),
    })
    assert resp_mov.status_code == 302
    assert Transaccion.objects.filter(idUsuario=perfil_a, idCategoria=cat_gym).count() == 1

    # No permite eliminar categoría en uso, pero sí renombrarla y eliminar una sin uso
    client.post(reverse('categoria_eliminar', args=[cat_gym.idCategoria]))
    assert Categoria.objects.filter(idCategoria=cat_gym.idCategoria).exists()

    client.post(reverse('categoria_editar', args=[cat_gym.idCategoria]), {
        'nombre': 'Gimnasio U',
        'tipo_aplicable': 'gasto',
        'tono': 'teal',
    })
    cat_gym.refresh_from_db()
    assert cat_gym.nombre == 'Gimnasio U'

    client.post(reverse('categoria_eliminar', args=[cat_mascota.idCategoria]))
    assert not Categoria.objects.filter(idCategoria=cat_mascota.idCategoria).exists()

    # Aislamiento: usuario B (sesión independiente) no ve, no usa, no edita ni elimina categorías de usuario A
    from django.test import Client as DjangoClient
    client_b = DjangoClient()
    client_b.force_login(cuenta_b)
    resp_cats_b = client_b.get(reverse('categorias'))
    assert resp_cats_b.context['categorias_personalizadas'] == []
    assert 'Gimnasio U' not in [c['nombre'] for c in resp_cats_b.context['sheet_categorias_ui']]
    assert 'Gimnasio U' not in resp_cats_b.content.decode('utf-8')

    client_b.post(reverse('movimiento'), {
        'tipo': 'gasto',
        'monto': '10000',
        'categoria': cat_gym.idCategoria,
        'descripcion': 'Intento ajeno',
        'fecha': date.today().isoformat(),
    })
    assert Transaccion.objects.filter(idUsuario=perfil_b).count() == 0

    client_b.post(reverse('categoria_editar', args=[cat_gym.idCategoria]), {'nombre': 'Hack'})
    client_b.post(reverse('categoria_eliminar', args=[cat_gym.idCategoria]))
    cat_gym.refresh_from_db()
    assert cat_gym.nombre == 'Gimnasio U'


@pytest.mark.django_db
def test_rf08_comparacion_entre_periodos_y_evolucion_del_ahorro_real(
    client, crear_estudiante, categoria_base
):
    from finanzas.models import AporteMeta
    from finanzas.services.analitica_service import (
        calcular_comparacion_periodos,
        calcular_evolucion_ahorro,
    )

    hoy = date(2026, 11, 25)
    mes_pasado = date(2026, 10, 15)
    cuenta, perfil = crear_estudiante('rf08@curn.edu.co', mesada='400000.00')

    # Mes anterior: gasto $100.000, ingreso $200.000
    Transaccion.objects.create(
        idUsuario=perfil, idCategoria=categoria_base, descripcion='Ingreso oct',
        monto=Decimal('200000.00'), fecha=mes_pasado, tipo='ingreso'
    )
    Transaccion.objects.create(
        idUsuario=perfil, idCategoria=categoria_base, descripcion='Gasto oct',
        monto=Decimal('100000.00'), fecha=mes_pasado, tipo='gasto'
    )
    # Mes actual: gasto $60.000 (-40%), ingreso $250.000, aporte meta $50.000
    Transaccion.objects.create(
        idUsuario=perfil, idCategoria=categoria_base, descripcion='Ingreso nov',
        monto=Decimal('250000.00'), fecha=hoy, tipo='ingreso'
    )
    Transaccion.objects.create(
        idUsuario=perfil, idCategoria=categoria_base, descripcion='Gasto nov',
        monto=Decimal('60000.00'), fecha=hoy, tipo='gasto'
    )
    meta = MetaAhorro.objects.create(
        idUsuario=perfil, nombre='Portátil', objetivo=Decimal('500000.00'), acumulado=Decimal('50000.00')
    )
    AporteMeta.objects.create(idMeta=meta, idUsuario=perfil, monto=Decimal('50000.00'), fecha=hoy)

    comp = calcular_comparacion_periodos(perfil, periodo='mensual', hoy=hoy)
    assert comp['gastos_anterior'] == Decimal('100000.00')
    assert comp['gastos_actual'] == Decimal('60000.00')
    assert comp['var_gastos_pct'] == -40
    assert comp['ahorro_neto_actual'] == Decimal('190000.00')
    assert comp['aportes_metas_actual'] == Decimal('50000.00')

    evol = calcular_evolucion_ahorro(perfil, hoy=hoy, meses=6)
    assert len(evol['serie']) == 6
    assert evol['serie'][-1]['aportes_metas'] == Decimal('50000.00')
    assert evol['serie'][-1]['acumulado_metas'] == Decimal('50000.00')
    assert evol['serie'][-2]['ahorro_neto'] == Decimal('100000.00')

    client.force_login(cuenta)
    resp = client.get(reverse('insights') + '?periodo=mensual')
    assert resp.status_code == 200
    assert 'Evolución del ahorro (6 meses)' in resp.content.decode('utf-8')


@pytest.mark.django_db
def test_rf09_umbral_hormiga_configurable_consistente_en_motor_estadisticas_recomendaciones_y_notificaciones(
    client, crear_estudiante, categoria_base
):
    from finanzas.models import Notificacion
    from finanzas.services.finanzas_service import calcular_resumen_financiero

    cuenta, perfil = crear_estudiante('rf09@curn.edu.co', mesada='300000.00')
    # Gasto de $25.000 hoy: NO es hormiga con $15.000 por defecto
    Transaccion.objects.create(
        idUsuario=perfil, idCategoria=categoria_base, descripcion='Combo almuerzo',
        monto=Decimal('25000.00'), fecha=date.today(), tipo='gasto'
    )
    r_def = calcular_resumen_financiero(perfil)
    assert r_def['umbral_hormiga'] == Decimal('15000.00')
    assert r_def['total_hormiga'] == Decimal('0.00')

    # Configurar umbral a $30.000 vía POST + CSRF
    client.force_login(cuenta)
    resp_upd = client.post(reverse('umbral_hormiga'), {
        'umbral_hormiga': '30000',
        'next': '/app/insights/?tab=control',
    })
    assert resp_upd.status_code == 302
    perfil.refresh_from_db()
    assert perfil.umbral_hormiga == Decimal('30000.00')

    # Motor financiero, Estadísticas, Recomendaciones y Notificaciones usan $30.000 consistentemente
    r_new = calcular_resumen_financiero(perfil)
    assert r_new['total_hormiga'] == Decimal('25000.00')

    resp_ins = client.get(reverse('insights') + '?tab=control')
    html_ins = resp_ins.content.decode('utf-8')
    assert resp_ins.context['hormiga_count'] == 1
    assert '30.000' in html_ins
    assert any('30.000' in rec['titulo'] for rec in resp_ins.context['recomendaciones'])

    notif_hormiga = Notificacion.objects.filter(idUsuario=perfil, tipo='hormiga', descartada=False).first()
    assert notif_hormiga is not None
    assert '30.000' in notif_hormiga.mensaje

    # Rechaza umbral fuera de rango
    client.post(reverse('umbral_hormiga'), {'umbral_hormiga': '100'})
    perfil.refresh_from_db()
    assert perfil.umbral_hormiga == Decimal('30000.00')


@pytest.mark.django_db
def test_rf10_metas_fecha_objetivo_cuotas_reales_y_sin_doble_contabilizacion(
    client, crear_estudiante
):
    from finanzas.models import AporteMeta, Notificacion
    from finanzas.services.finanzas_service import calcular_resumen_financiero
    from finanzas.services.metas_service import calcular_plan_meta
    from finanzas.services.notificaciones_service import sincronizar_notificaciones_usuario

    hoy = date.today()
    cuenta, perfil = crear_estudiante('rf10@curn.edu.co', mesada='500000.00', frecuencia='quincenal')
    client.force_login(cuenta)

    # Crear meta con fecha objetivo a 30 días ($300.000 -> $10.000/día, $150.000/quincena)
    fecha_obj = hoy + timedelta(days=30)
    resp_crear = client.post(reverse('crear_meta'), {
        'nombre': 'Bicicleta',
        'categoria': 'Transporte',
        'objetivo': '300000',
        'fecha_objetivo': fecha_obj.isoformat(),
    })
    assert resp_crear.status_code == 302
    meta = MetaAhorro.objects.get(idUsuario=perfil, nombre='Bicicleta')
    assert meta.fecha_objetivo == fecha_obj

    plan0 = calcular_plan_meta(meta, perfil=perfil, hoy=hoy)
    assert plan0['dias_restantes'] == 30
    assert plan0['cuota_diaria'] == Decimal('10000.00')
    assert plan0['cuota_quincenal'] == Decimal('150000.00')
    assert plan0['cuota_mensual'] == Decimal('300000.00')

    # Abonar $50.000 crea AporteMeta SIN crear Transaccion gasto duplicada
    client.post(reverse('metas'), {
        'accion': 'actualizar_meta',
        'meta_id': meta.idMeta,
        'ahorro': '50000',
    })
    meta.refresh_from_db()
    assert meta.acumulado == Decimal('50000.00')
    assert AporteMeta.objects.filter(idMeta=meta, idUsuario=perfil, monto=Decimal('50000.00')).count() == 1
    assert Transaccion.objects.filter(idUsuario=perfil).count() == 0

    resumen = calcular_resumen_financiero(perfil, hoy=hoy)
    assert resumen['dinero_reservado_metas'] == Decimal('50000.00')
    assert resumen['saldo_disponible'] == Decimal('450000.00')

    # Meta vencida dispara notificación real
    meta.fecha_objetivo = hoy - timedelta(days=2)
    meta.save(update_fields=['fecha_objetivo'])
    sincronizar_notificaciones_usuario(perfil, hoy=hoy)
    assert Notificacion.objects.filter(
        idUsuario=perfil, clave=f'meta_vencida_{meta.idMeta}', descartada=False
    ).exists()


@pytest.mark.django_db
def test_rf11_presupuestos_reales_por_categoria_alertas_y_aislamiento(
    client, crear_estudiante, categoria_base, categoria_transporte
):
    from finanzas.models import Notificacion, PresupuestoCategoria

    cuenta_a, perfil_a = crear_estudiante('rf11_a@curn.edu.co', mesada='500000.00')
    cuenta_b, _ = crear_estudiante('rf11_b@curn.edu.co', mesada='500000.00')
    client.force_login(cuenta_a)

    # Configurar presupuesto real de $100.000 para Alimentación
    resp_save = client.post(reverse('presupuesto_categoria_guardar'), {
        'categoria_id': str(categoria_base.idCategoria),
        'limite_mensual': '100000',
    })
    assert resp_save.status_code == 302
    pc = PresupuestoCategoria.objects.get(idUsuario=perfil_a, idCategoria=categoria_base)
    assert pc.limiteMensual == Decimal('100000.00')

    # Gastar $85.000 en Alimentación (85% -> alerta preventiva) y $12.000 en Transporte (sin tope)
    client.post(reverse('movimiento'), {
        'tipo': 'gasto',
        'monto': '85000',
        'categoria': categoria_base.idCategoria,
        'descripcion': 'Mercado',
        'fecha': date.today().isoformat(),
    })
    Transaccion.objects.create(
        idUsuario=perfil_a, idCategoria=categoria_transporte, descripcion='Bus',
        monto=Decimal('12000.00'), fecha=date.today(), tipo='gasto'
    )

    resp_p1 = client.get(reverse('presupuestos'))
    barras = resp_p1.context['barras_presupuesto']
    assert len(barras) == 1
    assert barras[0]['porcentaje_real'] == 85
    assert barras[0]['cerca'] is True
    assert barras[0]['excedido'] is False
    assert len(resp_p1.context['categorias_sin_presupuesto']) == 1
    assert Notificacion.objects.filter(idUsuario=perfil_a, tipo='presupuesto_categoria', nivel='warn').exists()

    # Superar tope (+$25.000 -> $110.000 = 110% -> alerta danger)
    client.post(reverse('movimiento'), {
        'tipo': 'gasto',
        'monto': '25000',
        'categoria': categoria_base.idCategoria,
        'descripcion': 'Cena',
        'fecha': date.today().isoformat(),
    })
    resp_p2 = client.get(reverse('presupuestos'))
    assert resp_p2.context['barras_presupuesto'][0]['excedido'] is True
    assert resp_p2.context['barras_presupuesto'][0]['excedente'] == Decimal('10000.00')
    assert Notificacion.objects.filter(idUsuario=perfil_a, tipo='presupuesto_categoria', nivel='danger').exists()

    # Aislamiento: usuario B no puede eliminar presupuesto de usuario A
    client.force_login(cuenta_b)
    client.post(reverse('presupuesto_categoria_eliminar', args=[pc.idPresupuestoCat]))
    assert PresupuestoCategoria.objects.filter(idPresupuestoCat=pc.idPresupuestoCat).exists()


@pytest.mark.django_db
def test_rf12_prestamos_y_gastos_compartidos_sin_doble_contabilizacion_e_idempotencia(
    client, crear_estudiante, categoria_base
):
    from finanzas.models import GastoCompartido, Notificacion, Participante
    from finanzas.services.finanzas_service import calcular_resumen_financiero

    cuenta_a, perfil_a = crear_estudiante('rf12_a@curn.edu.co', mesada='200000.00')
    cuenta_b, _ = crear_estudiante('rf12_b@curn.edu.co', mesada='200000.00')
    client.force_login(cuenta_a)
    hoy = date.today()

    # Escenario A: usuario paga cuenta completa de $60.000 (mi parte $20.000, Ana $20.000, Mateo $20.000)
    resp_gc = client.post(reverse('gasto_compartido_crear'), {
        'descripcion': 'Pizza estudio',
        'categoria': str(categoria_base.idCategoria),
        'fecha': hoy.isoformat(),
        'monto_total': '60000',
        'mi_parte': '20000',
        'yo_pague_total': '1',
        'participante_nombre': ['Ana', 'Mateo'],
        'participante_monto': ['20000', '20000'],
    })
    assert resp_gc.status_code == 302
    gc = GastoCompartido.objects.get(idUsuario=perfil_a)
    assert gc.estado == 'Pendiente'
    # Exactamente 1 gasto de $60.000 -> saldo $140.000 (cero doble descuento)
    assert Transaccion.objects.filter(idUsuario=perfil_a, tipo='gasto').count() == 1
    assert calcular_resumen_financiero(perfil_a, hoy=hoy)['saldo_disponible'] == Decimal('140000.00')
    assert Notificacion.objects.filter(idUsuario=perfil_a, tipo='gasto_compartido').exists()

    p_ana = Participante.objects.get(idGastoComp=gc, nombreAmigo='Ana')
    p_mateo = Participante.objects.get(idGastoComp=gc, nombreAmigo='Mateo')

    # Aislamiento: usuario B no puede marcar pagado al participante de A
    client.force_login(cuenta_b)
    client.post(reverse('participante_pagar', args=[p_ana.idParticipante]))
    p_ana.refresh_from_db()
    assert p_ana.pagado is False

    # Usuario A marca a Ana pagada DOS veces -> solo 1 reembolso de $20.000 (idempotente)
    client.force_login(cuenta_a)
    client.post(reverse('participante_pagar', args=[p_ana.idParticipante]))
    client.post(reverse('participante_pagar', args=[p_ana.idParticipante]))
    assert Transaccion.objects.filter(idUsuario=perfil_a, tipo='ingreso').count() == 1
    assert calcular_resumen_financiero(perfil_a, hoy=hoy)['saldo_disponible'] == Decimal('160000.00')

    # Usuario A marca a Mateo pagado -> gasto pasa a Liquidado y saldo neto final = $180.000 (-$20.000 reales)
    client.post(reverse('participante_pagar', args=[p_mateo.idParticipante]))
    gc.refresh_from_db()
    assert gc.estado == 'Liquidado'
    assert calcular_resumen_financiero(perfil_a, hoy=hoy)['saldo_disponible'] == Decimal('180000.00')

    # Préstamo con fecha límite vencida + liquidación opcional en saldo (idempotente)
    client.post(reverse('metas'), {
        'accion': 'crear_prestamo',
        'deudor': 'Carlos',
        'concepto': 'Fotocopias',
        'tipo': 'Por cobrar',
        'monto': '10000',
        'fecha_limite': (hoy - timedelta(days=1)).isoformat(),
    })
    prestamo = Prestamo.objects.get(idUsuario=perfil_a, deudor='Carlos')
    assert Notificacion.objects.filter(
        idUsuario=perfil_a, clave=f'prestamo_vencido_{prestamo.idPrestamo}'
    ).exists()

    client.post(reverse('metas'), {
        'accion': 'pagar_prestamo',
        'prestamo_id': prestamo.idPrestamo,
        'registrar_movimiento': '1',
    })
    client.post(reverse('metas'), {
        'accion': 'pagar_prestamo',
        'prestamo_id': prestamo.idPrestamo,
        'registrar_movimiento': '1',
    })
    assert calcular_resumen_financiero(perfil_a, hoy=hoy)['saldo_disponible'] == Decimal('190000.00')


@pytest.mark.django_db
def test_rf13_recomendaciones_personalizadas_con_datos_reales(
    client, crear_estudiante, categoria_base
):
    from finanzas.models import PresupuestoCategoria

    cuenta, perfil = crear_estudiante('rf13@curn.edu.co', mesada='300000.00')
    PresupuestoCategoria.objects.create(
        idUsuario=perfil, idCategoria=categoria_base, limiteMensual=Decimal('40000.00')
    )
    Transaccion.objects.create(
        idUsuario=perfil, idCategoria=categoria_base, descripcion='Comida',
        monto=Decimal('50000.00'), fecha=date.today(), tipo='gasto'
    )
    Prestamo.objects.create(
        idUsuario=perfil, deudor='Laura', concepto='Pasaje', tipo='Por cobrar',
        monto=Decimal('15000.00'), estado='Pendiente'
    )

    client.force_login(cuenta)
    resp = client.get(reverse('insights'))
    assert resp.status_code == 200
    recs = resp.context['recomendaciones']
    assert len(recs) >= 2
    titulos = ' '.join(r['titulo'] for r in recs)
    assert 'Alimentación' in titulos
    assert '15.000' in titulos





