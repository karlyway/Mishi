from django.shortcuts import render, redirect

# Datos de prueba para visualizar informacion en las pantallas
DATOS_DEMO = {
    'usuario': {
        'nombre': 'Camila Perez',
        'universidad': 'Universidad de Cartagena',
        'mesada_base': 350000,
        'saldo_disponible': 135000,
        'dias_restantes': 9,
    },
    'movimientos': [
        {
            'id': 1,
            'titulo': 'Almuerzo en cafeteria',
            'categoria': 'Alimentacion',
            'tipo': 'gasto',
            'monto': 12000,
            'fecha': '29/10/2026',
            'es_hormiga': False,
            'es_compartido': False,
        },
        {
            'id': 2,
            'titulo': 'Cafe y galletas',
            'categoria': 'Refrigerios',
            'tipo': 'gasto',
            'monto': 4500,
            'fecha': '29/10/2026',
            'es_hormiga': True,
            'es_compartido': False,
        },
        {
            'id': 3,
            'titulo': 'Pasajes de transporte',
            'categoria': 'Transporte',
            'tipo': 'gasto',
            'monto': 15000,
            'fecha': '28/10/2026',
            'es_hormiga': False,
            'es_compartido': False,
        },
        {
            'id': 4,
            'titulo': 'Mesada quincenal',
            'categoria': 'Mesada',
            'tipo': 'ingreso',
            'monto': 150000,
            'fecha': '25/10/2026',
            'es_hormiga': False,
            'es_compartido': False,
        },
        {
            'id': 5,
            'titulo': 'Salida a cine',
            'categoria': 'Ocio',
            'tipo': 'gasto',
            'monto': 22000,
            'fecha': '24/10/2026',
            'es_hormiga': False,
            'es_compartido': True,
            'amigo': 'Andres G.',
        },
        {
            'id': 6,
            'titulo': 'Fotocopias de estudio',
            'categoria': 'Universidad',
            'tipo': 'gasto',
            'monto': 3500,
            'fecha': '23/10/2026',
            'es_hormiga': True,
            'es_compartido': False,
        },
    ],
    'metas': [
        {
            'id': 1,
            'nombre': 'Fotocopias y parciales',
            'objetivo': 60000,
            'acumulado': 45000,
            'porcentaje': 75,
            'categoria': 'Universidad',
        },
        {
            'id': 2,
            'nombre': 'Fondo de emergencia',
            'objetivo': 100000,
            'acumulado': 60000,
            'porcentaje': 60,
            'categoria': 'Ahorro',
        },
        {
            'id': 3,
            'nombre': 'Salida de semestre',
            'objetivo': 80000,
            'acumulado': 25000,
            'porcentaje': 31,
            'categoria': 'Ocio',
        },
    ],
    'prestamos': [
        {
            'id': 1,
            'persona': 'Andres Gomez',
            'concepto': 'Parte de la pizza',
            'monto': 11000,
            'tipo': 'Por cobrar',
            'estado': 'Pendiente',
            'fecha': '26/10/2026'
        },
        {
            'id': 2,
            'persona': 'Laura Mendoza',
            'concepto': 'Impresiones en grupo',
            'monto': 4000,
            'tipo': 'Por pagar',
            'estado': 'Pendiente',
            'fecha': '27/10/2026'
        },
        {
            'id': 3,
            'persona': 'Santiago Ruiz',
            'concepto': 'Almuerzo',
            'monto': 12000,
            'tipo': 'Por cobrar',
            'estado': 'Pagado',
            'fecha': '22/10/2026'
        }
    ]
}


# Pagina de presentacion publica
def landing_view(request):
    return render(request, 'landing.html')


# Formulario de acceso de usuarios
def login_view(request):
    if request.method == 'POST':
        return redirect('dashboard')
    return render(request, 'login.html')


# Formulario para registro de nuevos estudiantes
def registro_usuario_view(request):
    if request.method == 'POST':
        return redirect('dashboard')
    return render(request, 'registro_usuario.html')


# Panel principal: calculo del limite diario segun saldo y dias restantes
def dashboard_view(request):
    saldo = DATOS_DEMO['usuario']['saldo_disponible']
    dias = max(DATOS_DEMO['usuario']['dias_restantes'], 1)
    # Formula: saldo dividido entre dias restantes
    limite_diario = round(saldo / dias)
    
    # Calculo para evaluar si se supera el 80% del presupuesto diario
    gasto_hoy = 16500
    porcentaje_gasto_hoy = min(round((gasto_hoy / limite_diario) * 100), 100) if limite_diario > 0 else 100
    alerta_activa = porcentaje_gasto_hoy >= 80
    total_hormiga = sum(m['monto'] for m in DATOS_DEMO['movimientos'] if m.get('es_hormiga') and m['tipo'] == 'gasto')
    
    context = {
        'usuario': DATOS_DEMO['usuario'],
        'saldo': saldo,
        'dias_restantes': dias,
        'limite_diario': limite_diario,
        'gasto_hoy': gasto_hoy,
        'porcentaje_gasto_hoy': porcentaje_gasto_hoy,
        'alerta_activa': alerta_activa,
        'total_hormiga': total_hormiga,
        'ultimos_movimientos': DATOS_DEMO['movimientos'][:4],
        'pestana_activa': 'dashboard'
    }
    return render(request, 'dashboard.html', context)


# Vista para agregar un movimiento (ingreso o gasto)
def movimiento_view(request):
    saldo = DATOS_DEMO['usuario']['saldo_disponible']
    dias = max(DATOS_DEMO['usuario']['dias_restantes'], 1)
    limite_diario = round(saldo / dias)
    
    # Opciones de categoria para el formulario
    categorias = [
        'Alimentacion',
        'Transporte',
        'Ocio y Salidas',
        'Refrigerios',
        'Gastos Universitarios',
        'Otros'
    ]
    
    context = {
        'saldo': saldo,
        'dias_restantes': dias,
        'limite_diario': limite_diario,
        'categorias': categorias,
        'pestana_activa': 'movimiento'
    }
    return render(request, 'registro.html', context)


# Historial de gastos e ingresos registrados
def historial_view(request):
    movimientos = DATOS_DEMO['movimientos']
    total_ingresos = sum(m['monto'] for m in movimientos if m['tipo'] == 'ingreso')
    total_gastos = sum(m['monto'] for m in movimientos if m['tipo'] == 'gasto')
    
    context = {
        'movimientos': movimientos,
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'balance': total_ingresos - total_gastos,
        'pestana_activa': 'historial'
    }
    return render(request, 'historial.html', context)


# Visualizacion de metas de ahorro y deudas pendientes
def metas_view(request):
    context = {
        'metas': DATOS_DEMO['metas'],
        'prestamos': DATOS_DEMO['prestamos'],
        'pestana_activa': 'metas'
    }
    return render(request, 'metas.html', context)
