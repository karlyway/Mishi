from pathlib import Path

from mishi_project.settings import *  # noqa: F401, F403

# Configuración local lista para ejecutar Mishi con SQLite sin instalar MySQL.
# Copia este archivo como `local_settings.py` en la raíz del proyecto.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
