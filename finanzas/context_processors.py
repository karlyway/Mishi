from django.utils import timezone

from .models import Categoria, Usuario
from .services.avatares import AVATARES_MISHI, obtener_avatar_info
from .services.finanzas_service import calcular_resumen_financiero
from .services.notificaciones_service import (
    contar_notificaciones_no_leidas,
    sincronizar_notificaciones_usuario,
)
from .services.seguridad_service import (
    POLITICA_PRIVACIDAD_VERSION,
    requiere_consentimiento_vigente,
)
from .ui_helpers import estilo_categoria


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
    """Expone categorías reales y resumen financiero compartido para el bottom sheet global."""
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

    resumen = getattr(request, '_mishi_resumen', None)
    if resumen is None:
        resumen = calcular_resumen_financiero(perfil)
        request._mishi_resumen = resumen

    hoy_iso = timezone.localdate().isoformat()
    avatar_info = obtener_avatar_info(getattr(perfil, 'avatar', None))
    no_leidas = getattr(request, '_mishi_notif_count', None)
    if no_leidas is None:
        if request.session.get('mishi_notif_sync_day') != hoy_iso:
            no_leidas = sincronizar_notificaciones_usuario(perfil, resumen=resumen)
            request.session['mishi_notif_sync_day'] = hoy_iso
        else:
            no_leidas = contar_notificaciones_no_leidas(perfil)
        request._mishi_notif_count = no_leidas

    return {
        'sheet_categorias_ui': sheet_categorias_ui,
        'sheet_hoy_iso': hoy_iso,
        'sheet_saldo_fmt': resumen['saldo_fmt'],
        'sheet_limite_diario_fmt': resumen['limite_diario_fmt'],
        'sheet_restante_hoy_fmt': resumen['dinero_restante_hoy_fmt'],
        'sheet_alerta_activa': resumen['alerta_activa'],
        'notificaciones_no_leidas': no_leidas,
        'usuario_avatar': avatar_info,
        'usuario_avatar_path': avatar_info['archivo'],
        'usuario_avatar_nombre': avatar_info['nombre'],
        'avatares_mishi': AVATARES_MISHI,
        'pref_ocultar_saldo': bool(getattr(perfil, 'ocultar_saldo', False)),
        'pref_alertas_activas': bool(getattr(perfil, 'alertas_activas', True)),
        'pref_tema_visual': getattr(perfil, 'tema_visual', 'warm') or 'warm',
        'requiere_consentimiento_datos': requiere_consentimiento_vigente(perfil),
        'politica_privacidad_version': POLITICA_PRIVACIDAD_VERSION,
    }
