"""Development settings for TUS website.

Active automatiquement l'envoi SMTP si des variables d'environnement
sont présentes, sinon utilise le backend console (pas d'envoi réel).
"""
from .base import *  # noqa: F401,F403
import os

DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS += [
    'django_extensions',
]

# ==============================================================================
# DATABASE - PostgreSQL local (via venv Python 3.11)
# ==============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'tus_db',
        'USER': 'postgres',
        'PASSWORD': 'Vilme1479*',
        'HOST': 'localhost',
        'PORT': '5433',
    }
}

# Email configuration (auto)
if os.environ.get('EMAIL_HOST'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in {'1', 'true', 'yes'}
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
else:
    # Fallback: print emails to console in dev
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'