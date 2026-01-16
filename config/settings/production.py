"""
Production settings for TUS website - Optimisé pour Render.com

Configuration optimale pour :
- Hébergement sur Render (Web Service)
- Base de données PostgreSQL managée
- Stockage S3 compatible (Cloudflare R2 / AWS S3)
- Emails transactionnels via Brevo API
- WhiteNoise pour les fichiers statiques
"""
from .base import *  # noqa: F401,F403

import dj_database_url

DEBUG = False

# ==============================================================================
# HOSTS & SECURITY
# ==============================================================================
ALLOWED_HOSTS = os.environ.get(
    'DJANGO_ALLOWED_HOSTS', 
    'traitdunion.it,www.traitdunion.it,.onrender.com'
).split(',')

# CSRF trusted origins pour Render
CSRF_TRUSTED_ORIGINS = os.environ.get(
    'CSRF_TRUSTED_ORIGINS',
    'https://traitdunion.it,https://www.traitdunion.it,https://*.onrender.com'
).split(',')

# Sécurité HTTPS
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ==============================================================================
# DATABASE (PostgreSQL via Render)
# ==============================================================================
# Render fournit DATABASE_URL automatiquement
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    DATABASES['default'] = dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=True,
    )
else:
    # Fallback PostgreSQL manuel
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', ''),
        'USER': os.environ.get('DB_USER', ''),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }

# ==============================================================================
# STATIC FILES (WhiteNoise)
# ==============================================================================
# WhiteNoise doit être après SecurityMiddleware
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Compression et cache long terme
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ==============================================================================
# MEDIA FILES (S3 Compatible - Cloudflare R2 recommandé pour Render)
# ==============================================================================
# Activer S3 uniquement si configuré
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = os.environ.get('AWS_S3_ENDPOINT_URL')  # Pour Cloudflare R2
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'auto')

if AWS_ACCESS_KEY_ID and AWS_STORAGE_BUCKET_NAME:
    # Configuration S3/R2
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = True
    AWS_S3_FILE_OVERWRITE = False
    
    # URL personnalisée pour accès public (optionnel)
    AWS_S3_CUSTOM_DOMAIN = os.environ.get('AWS_S3_CUSTOM_DOMAIN')
    
    if AWS_S3_CUSTOM_DOMAIN:
        MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
    else:
        MEDIA_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/'

# ==============================================================================
# EMAIL (Brevo API - recommandé pour Render)
# ==============================================================================
# Brevo est préféré sur Render car :
# - L'API REST évite les problèmes de firewall SMTP
# - Meilleur tracking et délivrabilité
# - Offre gratuite généreuse (300 emails/jour)

# La clé API Brevo est déjà configurée dans base.py via BREVO_API_KEY

# Fallback SMTP si besoin (non recommandé sur Render)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp-relay.brevo.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# ==============================================================================
# CACHING (Redis via Render)
# ==============================================================================
REDIS_URL = os.environ.get('REDIS_URL')

if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'ssl_cert_reqs': None,  # Pour Render Redis managé
            }
        }
    }
    
    # Sessions via Redis (plus rapide)
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'

# ==============================================================================
# LOGGING (Production)
# ==============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'core.services.email_backends': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ==============================================================================
# PERFORMANCE
# ==============================================================================
# Cache templates en production
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]
# Supprimer APP_DIRS car on utilise un loader explicite
TEMPLATES[0]['APP_DIRS'] = False
