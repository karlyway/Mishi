from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('registro/', views.registro_view, name='registro'),
    path('historial/', views.historial_view, name='historial'),
    path('metas/', views.metas_view, name='metas'),
]
