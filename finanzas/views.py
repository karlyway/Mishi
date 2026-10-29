from django.shortcuts import render

# Datos iniciales simulados para que las pantallas sean totalmente navegables y ricas en datos
DATOS_DEMO = {
    'usuario': {
        'nombre': 'Karla Amaranto',
        'universidad': 'Corporación Universitaria Rafael Núñez',
        'mesada_base': 350000,
        'saldo_disponible': 135000,
        'dias_restantes': 9,
    },
    'movimientos': [
        {
            'id': 1,
            'titulo': 'Almuerzo en cafetería',
            'categoria': 'Alimentación',
            'icono': 'utensils',
            'tipo': 'gasto',
            'monto': 12000,
            'fecha': 'Hoy, 1:15 p.m.',
            'es_hormiga': False,
            'es_compartido': False,
        },
        {
            'id': 2,
            'titulo': 'Café y galletas (Snack)',
            'categoria': 'Refrigerios y Dulces',
            'icono': 'coffee',
            'tipo': 'gasto',
            'monto': 4500,
            'fecha': 'Hoy, 10:30 a.m.',
            'es_hormiga': True,
            'es_compartido': False,
        },
        {
            'id': 3,
            'titulo': 'Recarga de pasajes / Transcaribe',
            'categoria': 'Transporte',
            'icono': 'bus',
            'tipo': 'gasto',
            'monto': 15000,
            'fecha': 'Ayer',
            'es_hormiga': False,
            'es_compartido': False,
        },
        {
            'id': 4,
            'titulo': 'Apoyo familiar (Mesada parcial)',
            'categoria': 'Mesada / Ingreso',
            'icono': 'wallet',
            'tipo': 'ingreso',
            'monto': 150000,
            'fecha': '25 Oct 2026',
            'es_hormiga': False,
            'es_compartido': False,
        },
        {
            'id': 5,
            'titulo': 'Salida a cine con amigos',
            'categoria': 'Ocio y Salidas',
            'icono': 'film',
            'tipo': 'gasto',
            'monto': 22000,
            'fecha': '24 Oct 2026',
            'es_hormiga': False,
            'es_compartido': True,
            'amigo': 'Melvis M.',
        },
        {
            'id': 6,
            'titulo': 'Fotocopias de Guías de Estudio',
            'categoria': 'Gastos Universitarios',
            'icono': 'book-open',
            'tipo': 'gasto',
            'monto': 3500,
            'fecha': '23 Oct 2026',
            'es_hormiga': True,
            'es_compartido': False,
        },
    ],
    'metas': [
        {
            'id': 1,
            'nombre': 'Fondo para parciales y fotocopias',
            'objetivo': 60000,
            'acumulado': 45000,
            'porcentaje': 75,
            'categoria': 'Universidad',
            'icono': 'graduation-cap',
        },
        {
            'id': 2,
            'nombre': 'Colchón de imprevistos',
            'objetivo': 100000,
            'acumulado': 60000,
            'porcentaje': 60,
            'categoria': 'Ahorro',
            'icono': 'piggy-bank',
        },
        {
            'id': 3,
            'nombre': 'Salida de fin de semestre',
            'objetivo': 80000,
            'acumulado': 25000,
            'porcentaje': 31,
            'categoria': 'Ocio',
            'icono': 'sparkles',
        },
    ],
    'prestamos': [
        {
            'id': 1,
            'persona': 'Harrison B.',
            'concepto': 'Parte de la pizza compartida',
            'monto': 11000,
            'tipo': 'por_cobrar', # Me debe
            'estado': 'Pendiente',
            'fecha': '26 Oct 2026'
        },
        {
            'id': 2,
            'persona': 'Isabel A.',
            'concepto': 'Impresiones trabajo en grupo',
            'monto': 4000,
            'tipo': 'por_pagar', # Yo le debo
            'estado': 'Pendiente',
            'fecha': '27 Oct 2026'
        },
        {
            'id': 3,
            'persona': 'Melvis M.',
            'concepto': 'Almuerzo en la U',
            'monto': 12000,
            'tipo': 'por_cobrar',
            'estado': 'Pagado',
            'fecha': '22 Oct 2026'
        }
    ]
}


def dashboard_view(request):
    """Pantalla principal de Mishi con resumen financiero y cálculo de límite diario."""
    saldo = DATOS_DEMO['usuario']['saldo_disponible']
    dias = max(DATOS_DEMO['usuario']['dias_restantes'], 1)
    limite_diario = round(saldo / dias)
    
    # Gasto de hoy (acumulado)
    gasto_hoy = 16500
    porcentaje_gasto_hoy = min(round((gasto_hoy / limite_diario) * 100), 100) if limite_diario > 0 else 100
    
    # Alerta preventiva según RF-05
    alerta_activa = porcentaje_gasto_hoy >= 80
    
    # Suma de gastos hormiga
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
        'metas_destacadas': DATOS_DEMO['metas'][:2],
        'pestana_activa': 'dashboard'
    }
    return render(request, 'dashboard.html', context)


def registro_view(request):
    """Pantalla para registrar rápidamente ingresos o gastos."""
    saldo = DATOS_DEMO['usuario']['saldo_disponible']
    dias = max(DATOS_DEMO['usuario']['dias_restantes'], 1)
    limite_diario = round(saldo / dias)
    
    categorias = [
        {'id': 'alimentacion', 'nombre': 'Alimentación', 'icono': 'utensils'},
        {'id': 'ocio', 'nombre': 'Ocio y Salidas', 'icono': 'film'},
        {'id': 'transporte', 'nombre': 'Transporte', 'icono': 'bus'},
        {'id': 'refrigerios', 'nombre': 'Refrigerios, Dulces y Bebidas', 'icono': 'coffee'},
        {'id': 'universidad', 'nombre': 'Gastos Universitarios', 'icono': 'book-open'},
        {'id': 'servicios', 'nombre': 'Servicios y Recargas', 'icono': 'wifi'},
    ]
    
    context = {
        'saldo': saldo,
        'dias_restantes': dias,
        'limite_diario': limite_diario,
        'categorias': categorias,
        'pestana_activa': 'registro'
    }
    return render(request, 'registro.html', context)


def historial_view(request):
    """Pantalla con el historial completo de movimientos, filtros y gastos hormiga."""
    movimientos = DATOS_DEMO['movimientos']
    
    total_ingresos = sum(m['monto'] for m in movimientos if m['tipo'] == 'ingreso')
    total_gastos = sum(m['monto'] for m in movimientos if m['tipo'] == 'gasto')
    total_hormiga = sum(m['monto'] for m in movimientos if m.get('es_hormiga') and m['tipo'] == 'gasto')
    conteo_hormiga = len([m for m in movimientos if m.get('es_hormiga')])
    
    context = {
        'movimientos': movimientos,
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'total_hormiga': total_hormiga,
        'conteo_hormiga': conteo_hormiga,
        'pestana_activa': 'historial'
    }
    return render(request, 'historial.html', context)


def metas_view(request):
    """Pantalla de metas de ahorro y módulo social de préstamos."""
    context = {
        'metas': DATOS_DEMO['metas'],
        'prestamos': DATOS_DEMO['prestamos'],
        'pestana_activa': 'metas'
    }
    return render(request, 'metas.html', context)
