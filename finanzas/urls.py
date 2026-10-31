from django.urls import path
from . import views

# Rutas de la aplicacion finanzas
urlpatterns = [
    # Paginas publicas
    path('', views.landing_view, name='landing'),
    path('login/', views.login_view, name='login'),
    path('registro-usuario/', views.registro_usuario_view, name='registro_usuario'),

    # Secciones internas del panel
    path('app/', views.dashboard_view, name='dashboard'),
    path('app/movimiento/', views.movimiento_view, name='movimiento'),
    path('app/historial/', views.historial_view, name='historial'),
    path('app/metas/', views.metas_view, name='metas'),
]
