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

# TOUJOURS False en production - ne jamais utiliser de variable d'env pour DEBUG
DEBUG = False

# ==============================================================================
# HOSTS & SECURITY
# ==============================================================================
# Hardcodé pour éviter les problèmes de variables d'environnement
ALLOWED_HOSTS = [
    'trait-d-union.onrender.com',
    'traitdunion.it',
    'www.traitdunion.it',
    '.onrender.com',
    'localhost',
    '127.0.0.1',
]

# CSRF trusted origins - DOIT inclure le scheme https://
CSRF_TRUSTED_ORIGINS = [
    'https://trait-d-union.onrender.com',
    'https://traitdunion.it',
    'https://www.traitdunion.it',
]

# Sécurité HTTPS
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Headers de sécurité supplémentaires
SECURE_CONTENT_TYPE_NOSNIFF = True  # X-Content-Type-Options: nosniff
SECURE_BROWSER_XSS_FILTER = True  # X-XSS-Protection (navigateurs anciens)
X_FRAME_OPTIONS = 'DENY'  # Protection clickjacking
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Permissions Policy (anciennement Feature-Policy)
PERMISSIONS_POLICY = {
    'geolocation': [],
    'microphone': [],
    'camera': [],
    'payment': ['self'],
}

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
# MEDIA FILES (Cloudinary - recommandé pour simplicité)
# ==============================================================================
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')

# Vérifier si on est en train de builder (collectstatic)
import sys
IS_BUILDING = 'collectstatic' in sys.argv

if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY:
    if not IS_BUILDING:
        print(f"✅ Cloudinary configuration found for cloud: {CLOUDINARY_CLOUD_NAME}")
    
    # Configuration Cloudinary
    INSTALLED_APPS += ['cloudinary', 'cloudinary_storage']
    
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': CLOUDINARY_CLOUD_NAME,
        'API_KEY': CLOUDINARY_API_KEY,
        'API_SECRET': CLOUDINARY_API_SECRET,
    }
    
    # Configuration moderne Django 5+
    STORAGES = {
        "default": {
            "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    
    # Fallback pour compatibilité
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    
    # IMPORTANT : Ne pas surcharger MEDIA_URL avec l'URL Cloudinary brute.
    # La librairie cloudinary_storage génère elle-même les URLs complètes (incluant /image/upload/...).
    # En laissant /media/, on évite de casser les liens.
    MEDIA_URL = '/media/'
else:
    # Mode Build ou Config manquante
    if IS_BUILDING:
        print("ℹ️  Build mode detected: Skipping detailed Cloudinary checks (expected).")
    else:
        print("❌ CLOUDINARY ENV VARS MISSING! External media storage will NOT work.")
    
    # Configuration minimale pour le build
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

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

# ==============================================================================
# SENTRY (Monitoring erreurs)
# ==============================================================================
SENTRY_DSN = os.environ.get('SENTRY_DSN')

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(
                transaction_style='url',
                middleware_spans=True,
            ),
            LoggingIntegration(
                level=None,  # Capture tous les logs
                event_level='ERROR',  # Envoyer les ERROR+ comme events
            ),
        ],
        # Performance monitoring
        traces_sample_rate=0.1,  # 10% des transactions
        profiles_sample_rate=0.1,  # 10% des profils
        
        # Environnement
        environment='production',
        release=os.environ.get('RENDER_GIT_COMMIT', 'unknown'),
        
        # Options
        send_default_pii=False,  # RGPD: pas de données personnelles
        attach_stacktrace=True,
    )
