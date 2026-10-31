from django.contrib import admin
from django.urls import path, include

# Rutas principales del proyecto
urlpatterns = [
    path('admin/', admin.site.urls),
    # Incluye las rutas de la app finanzas
    path('', include('finanzas.urls')),
]
