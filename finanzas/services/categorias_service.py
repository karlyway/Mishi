"""Gestión de categorías base y categorías personalizadas por usuario (RF-02)."""

from django.db.models import Q

from finanzas.models import Categoria, Transaccion
from finanzas.ui_helpers import estilo_categoria


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

TIPOS_CATEGORIA_VALIDOS = ('gasto', 'ingreso', 'ambos')
MAX_CATEGORIAS_PERSONALIZADAS = 30

TONOS_CATEGORIA_PALETA = (
    ('orange', 'Naranja', '#F97A22', '#FCE8D5'),
    ('green', 'Verde', '#36A65B', '#DCF4DF'),
    ('yellow', 'Amarillo', '#F5B82E', '#FDF2CE'),
    ('indigo', 'Índigo', '#6466E9', '#E7E7FB'),
    ('teal', 'Turquesa', '#189A88', '#DDF5F0'),
    ('rose', 'Rosa', '#E25563', '#FDE5E7'),
    ('slate', 'Grafito', '#525866', '#ECEEF2'),
    ('amber', 'Ámbar', '#E69D18', '#FBF0D6'),
)

TONOS_MAP = {
    slug: {'slug': slug, 'tone': slug, 'nombre': nombre, 'color': color, 'soft': soft}
    for slug, nombre, color, soft in TONOS_CATEGORIA_PALETA
}


def asegurar_categorias_base():
    """Garantiza que existan categorías globales mínimas sin duplicar registros."""
    if not Categoria.objects.filter(idUsuario__isnull=True).exists():
        for nombre in CATEGORIAS_BASE:
            Categoria.objects.get_or_create(
                nombre=nombre,
                idUsuario=None,
                defaults={'es_personalizada': False, 'tipo_aplicable': 'ambos'},
            )


def obtener_categorias_usuario(perfil, tipo=None):
    """Retorna categorías globales + categorías personalizadas exclusivas del usuario."""
    asegurar_categorias_base()
    qs = Categoria.objects.filter(
        Q(idUsuario__isnull=True) | Q(idUsuario=perfil)
    )
    if tipo in ('gasto', 'ingreso'):
        qs = qs.filter(Q(tipo_aplicable='ambos') | Q(tipo_aplicable=tipo))
    return qs.order_by('es_personalizada', 'idCategoria')


def obtener_categorias_personalizadas(perfil):
    """Retorna únicamente las categorías creadas por el usuario autenticado."""
    return Categoria.objects.filter(
        idUsuario=perfil,
        es_personalizada=True,
    ).order_by('-idCategoria')


def obtener_categoria_accesible(perfil, categoria_id):
    """Resuelve una categoría verificando que sea global o propiedad del usuario."""
    if categoria_id in (None, ''):
        return None
    try:
        cid = int(categoria_id)
    except (TypeError, ValueError):
        return None
    return Categoria.objects.filter(
        Q(idUsuario__isnull=True) | Q(idUsuario=perfil),
        idCategoria=cid,
    ).first()


def obtener_estilo_categoria(categoria):
    """Calcula color, tono e ícono respetando el tono explícito de categorías personalizadas."""
    base = estilo_categoria(getattr(categoria, 'nombre', ''))
    tono = (getattr(categoria, 'tono', '') or '').strip().lower()
    if tono and tono in TONOS_MAP:
        t = TONOS_MAP[tono]
        return {
            'slug': base['slug'],
            'tone': t['tone'],
            'color': t['color'],
            'soft': t['soft'],
            'icon': base['icon'],
        }
    return base


def _normalizar_nombre(nombre):
    return ' '.join((nombre or '').strip().split())


def crear_categoria_personalizada(perfil, nombre, tipo_aplicable='ambos', tono=''):
    """Crea una categoría personalizada aislada por usuario."""
    limpio = _normalizar_nombre(nombre)
    if len(limpio) < 2 or len(limpio) > 50:
        raise ValueError('El nombre de la categoría debe tener entre 2 y 50 caracteres.')

    tipo = (tipo_aplicable or 'ambos').strip().lower()
    if tipo not in TIPOS_CATEGORIA_VALIDOS:
        tipo = 'ambos'

    tono_limpio = (tono or '').strip().lower()
    if tono_limpio not in TONOS_MAP:
        tono_limpio = ''

    actuales = Categoria.objects.filter(idUsuario=perfil, es_personalizada=True).count()
    if actuales >= MAX_CATEGORIAS_PERSONALIZADAS:
        raise ValueError(f'Alcanzaste el límite de {MAX_CATEGORIAS_PERSONALIZADAS} categorías personalizadas.')

    duplicada = Categoria.objects.filter(
        Q(idUsuario__isnull=True) | Q(idUsuario=perfil),
        nombre__iexact=limpio,
    ).exists()
    if duplicada:
        raise ValueError('Ya existe una categoría con ese nombre.')

    return Categoria.objects.create(
        nombre=limpio,
        idUsuario=perfil,
        es_personalizada=True,
        tipo_aplicable=tipo,
        tono=tono_limpio,
    )


def editar_categoria_personalizada(perfil, categoria_id, nombre, tipo_aplicable='ambos', tono=''):
    """Actualiza una categoría personalizada únicamente si pertenece al usuario."""
    cat = Categoria.objects.filter(
        idCategoria=categoria_id,
        idUsuario=perfil,
        es_personalizada=True,
    ).first()
    if cat is None:
        raise ValueError('No se encontró la categoría personalizada.')

    limpio = _normalizar_nombre(nombre)
    if len(limpio) < 2 or len(limpio) > 50:
        raise ValueError('El nombre de la categoría debe tener entre 2 y 50 caracteres.')

    tipo = (tipo_aplicable or 'ambos').strip().lower()
    if tipo not in TIPOS_CATEGORIA_VALIDOS:
        tipo = 'ambos'

    tono_limpio = (tono or '').strip().lower()
    if tono_limpio not in TONOS_MAP:
        tono_limpio = ''

    duplicada = (
        Categoria.objects.filter(
            Q(idUsuario__isnull=True) | Q(idUsuario=perfil),
            nombre__iexact=limpio,
        )
        .exclude(idCategoria=cat.idCategoria)
        .exists()
    )
    if duplicada:
        raise ValueError('Ya existe otra categoría con ese nombre.')

    cat.nombre = limpio
    cat.tipo_aplicable = tipo
    cat.tono = tono_limpio
    cat.save(update_fields=['nombre', 'tipo_aplicable', 'tono'])
    return cat


def eliminar_categoria_personalizada(perfil, categoria_id):
    """Elimina una categoría personalizada del usuario si no tiene movimientos asociados."""
    cat = Categoria.objects.filter(
        idCategoria=categoria_id,
        idUsuario=perfil,
        es_personalizada=True,
    ).first()
    if cat is None:
        raise ValueError('No se encontró la categoría personalizada.')

    usos = Transaccion.objects.filter(idCategoria=cat).count()
    if usos > 0:
        raise ValueError(
            f'No puedes eliminar "{cat.nombre}" porque tiene {usos} movimiento'
            f'{"s" if usos != 1 else ""} registrado{"s" if usos != 1 else ""}.'
        )

    nombre = cat.nombre
    cat.delete()
    return nombre
