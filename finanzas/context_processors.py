from django.utils import timezone

from .models import Categoria, Usuario
from .ui_helpers import calcular_resumen_usuario, estilo_categoria


CATEGORIAS_BASE = (
    'Alimentación',
    'Transporte',
    'Universidad',
    'Ocio',
    'Hogar',
    'Salud',
    'Mesada / Ingreso',
    'Otros',
)


def mishi_app_chrome(request):
    """Expone categorías reales y resumen ligero para el bottom sheet global de movimientos."""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}

    perfil = Usuario.objects.filter(cuenta=user).first()
    if perfil is None:
        return {}

    if not Categoria.objects.exists():
        for nombre in CATEGORIAS_BASE:
            Categoria.objects.get_or_create(nombre=nombre)

    categorias = Categoria.objects.all().order_by('idCategoria')
    sheet_categorias_ui = [
        {
            'idCategoria': c.idCategoria,
            'nombre': c.nombre,
            'ui': estilo_categoria(c.nombre),
        }
        for c in categorias
    ]

    resumen = calcular_resumen_usuario(perfil)
    return {
        'sheet_categorias_ui': sheet_categorias_ui,
        'sheet_hoy_iso': timezone.localdate().isoformat(),
        'sheet_saldo_fmt': resumen['saldo_fmt'],
        'sheet_limite_diario_fmt': resumen['limite_diario_fmt'],
        'sheet_alerta_activa': resumen['alerta_activa'],
    }
