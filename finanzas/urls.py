from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

# Rutas de la aplicacion finanzas
urlpatterns = [
    # Paginas publicas
    path('', views.landing_view, name='landing'),
    path('login/', views.login_view, name='login'),
    path('registro-usuario/', views.registro_usuario_view, name='registro_usuario'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Secciones internas del panel
    path('app/', views.dashboard_view, name='dashboard'),
    path('app/movimiento/', views.movimiento_view, name='movimiento'),
    path('app/historial/', views.historial_view, name='historial'),
    path('app/metas/', views.metas_view, name='metas'),
]
