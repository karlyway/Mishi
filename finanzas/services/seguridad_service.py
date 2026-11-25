"""Utilidades de seguridad y consentimiento de privacidad (Fase 2)."""

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone


POLITICA_PRIVACIDAD_VERSION = '1.0-2026'
POLITICA_PRIVACIDAD_FECHA = '25 de noviembre de 2026'


def requiere_consentimiento_vigente(perfil):
    """Indica si el usuario aún no ha aceptado la versión vigente de la política de datos."""
    if perfil is None:
        return False
    return (
        not bool(getattr(perfil, 'acepto_politica_datos', False))
        or (getattr(perfil, 'version_politica_datos', '') or '') != POLITICA_PRIVACIDAD_VERSION
    )


def registrar_consentimiento_datos(perfil, guardar=True):
    """Registra la aceptación explícita con fecha/hora y versión exacta de política."""
    perfil.acepto_politica_datos = True
    perfil.fecha_aceptacion_datos = timezone.now()
    perfil.version_politica_datos = POLITICA_PRIVACIDAD_VERSION
    if guardar:
        perfil.save(update_fields=[
            'acepto_politica_datos',
            'fecha_aceptacion_datos',
            'version_politica_datos',
        ])
    return perfil


def validar_contrasena_servidor(password, user=None):
    """Ejecuta AUTH_PASSWORD_VALIDATORS de Django y devuelve lista de mensajes en español."""
    try:
        validate_password(password, user=user)
        return []
    except ValidationError as exc:
        return list(exc.messages)
