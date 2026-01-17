"""Test settings for Trait d'Union Studio.

Used by pytest and GitHub Actions CI/CD pipeline.
"""
from .base import *  # noqa: F401,F403

import os

# ==============================================================================
# CORE SETTINGS
# ==============================================================================
DEBUG = False
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'test-secret-key-for-testing')

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

# ==============================================================================
# DATABASE (PostgreSQL for CI, SQLite for local tests)
# ==============================================================================
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    import dj_database_url
    DATABASES['default'] = dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=0,  # Pas de pool en tests
    )
else:
    # SQLite pour tests locaux rapides
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }

# ==============================================================================
# CACHE (Local memory pour les tests)
# ==============================================================================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# ==============================================================================
# EMAIL (Console backend pour les tests)
# ==============================================================================
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ==============================================================================
# STATIC FILES
# ==============================================================================
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# ==============================================================================
# PASSWORD HASHERS (Plus rapide pour les tests)
# ==============================================================================
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# ==============================================================================
# MEDIA FILES (Temporary pour les tests)
# ==============================================================================
import tempfile
MEDIA_ROOT = tempfile.mkdtemp()

# ==============================================================================
# LOGGING (Minimal pour les tests)
# ==============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
        'level': 'CRITICAL',
    },
}

# ==============================================================================
# BREVO (Disabled pour les tests)
# ==============================================================================
BREVO_API_KEY = None

# ==============================================================================
# STRIPE (Test mode)
# ==============================================================================
STRIPE_PUBLIC_KEY = 'pk_test_fake'
STRIPE_SECRET_KEY = 'sk_test_fake'
STRIPE_WEBHOOK_SECRET = 'whsec_test_fake'

# ==============================================================================
# SECURITY (Relaxed pour les tests)
# ==============================================================================
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False

# ==============================================================================
# PERFORMANCE (Faster templates)
# ==============================================================================
# Disable cached template loader for tests
TEMPLATES[0]['APP_DIRS'] = True
if 'loaders' in TEMPLATES[0].get('OPTIONS', {}):
    del TEMPLATES[0]['OPTIONS']['loaders']
