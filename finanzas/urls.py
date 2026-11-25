from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

# Rutas de la aplicacion finanzas
urlpatterns = [
    # Paginas publicas
    path('', views.landing_view, name='landing'),
    path('login/', views.login_view, name='login'),
    path('registro-usuario/', views.registro_usuario_view, name='registro_usuario'),
    path('privacidad/', views.privacidad_view, name='privacidad'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Secciones internas del panel (experiencia tipo app)
    path('app/', views.dashboard_view, name='dashboard'),
    path('app/movimiento/', views.movimiento_view, name='movimiento'),
    path('app/historial/', views.historial_view, name='historial'),
    path('app/historial/<int:movimiento_id>/', views.detalle_movimiento_view, name='detalle_movimiento'),
    path('app/historial/editar/<int:movimiento_id>/', views.editar_movimiento_view, name='editar_movimiento'),
    path('app/historial/eliminar/<int:movimiento_id>/', views.eliminar_movimiento_view, name='eliminar_movimiento'),
    path('app/metas/', views.metas_view, name='metas'),
    path('app/metas/crear/', views.crear_meta_view, name='crear_meta'),
    path('app/categorias/', views.categorias_view, name='categorias'),
    path('app/insights/', views.insights_view, name='insights'),
    path('app/perfil/', views.perfil_view, name='perfil'),
    path('app/perfil/preferencias/', views.perfil_preferencias_view, name='perfil_preferencias'),
    path('app/perfil/contrasena/', views.cambiar_contrasena_view, name='cambiar_contrasena'),
    path('app/privacidad/aceptar/', views.aceptar_privacidad_view, name='aceptar_privacidad'),
    path('app/notificaciones/', views.notificaciones_view, name='notificaciones'),
    path('app/notificaciones/leer/', views.notificaciones_leer_view, name='notificaciones_leer'),
    path('app/notificaciones/eliminar/<int:notificacion_id>/', views.notificacion_eliminar_view, name='notificacion_eliminar'),
    path('app/presupuestos/', views.presupuestos_view, name='presupuestos'),
    path('app/animo/', views.animo_view, name='animo'),
]
