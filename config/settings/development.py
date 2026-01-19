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
# DATABASE - SQLite local (fallback si PostgreSQL non disponible)
# ==============================================================================
import socket

def _is_postgres_available(port=5432):
    """Vérifie si PostgreSQL est accessible."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0
    except:
        return False

# Essayer d'abord le port Docker (5432), puis le port local (5433)
if _is_postgres_available(5432):
    # Docker PostgreSQL
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'tus_db',
            'USER': 'tus_user',
            'PASSWORD': 'tus_password',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }
elif _is_postgres_available(5433):
    # PostgreSQL local
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
else:
    # Fallback SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ==============================================================================
# MEDIA FILES (Cloudinary) - Pour tester le stockage prod en dev
# ==============================================================================
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')

if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY:
    # Configuration Cloudinary
    INSTALLED_APPS += ['cloudinary', 'cloudinary_storage']
    
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': CLOUDINARY_CLOUD_NAME,
        'API_KEY': CLOUDINARY_API_KEY,
        'API_SECRET': CLOUDINARY_API_SECRET,
    }
    
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    MEDIA_URL = f'https://res.cloudinary.com/{CLOUDINARY_CLOUD_NAME}/'

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