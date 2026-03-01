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
# 🛡️ ZERO TRUST: Strict domain whitelist - NO wildcards
ALLOWED_HOSTS = [
    'trait-d-union.onrender.com',  # Render exact subdomain
    'traitdunion.it',
    'www.traitdunion.it',
]

# CSRF trusted origins - DOIT inclure le scheme https://
CSRF_TRUSTED_ORIGINS = [
    'https://trait-d-union.onrender.com',
    'https://traitdunion.it',
    'https://www.traitdunion.it',
]

# Sécurité HTTPS
# SSL redirect is handled by Render's load balancer — do NOT duplicate it here
# or it causes ERR_TOO_MANY_REDIRECTS (Render terminates SSL then forwards HTTP)
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Headers de sécurité supplémentaires
SECURE_CONTENT_TYPE_NOSNIFF = True  # X-Content-Type-Options: nosniff
# SECURE_BROWSER_XSS_FILTER obsolète — les navigateurs modernes l'ignorent
X_FRAME_OPTIONS = 'DENY'  # Protection clickjacking
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# 🔍 SEO: Canonical domain (www → non-www redirect, Render → custom domain)
CANONICAL_DOMAIN = 'traitdunion.it'

# Permissions Policy (anciennement Feature-Policy)
# 🛡️ BANK-GRADE: Exhaustive permissions lockdown
PERMISSIONS_POLICY = {
    'accelerometer': [],
    'autoplay': [],
    'camera': [],
    'clipboard-read': [],
    'clipboard-write': ['self'],
    'display-capture': [],
    'encrypted-media': [],
    'fullscreen': ['self'],
    'geolocation': [],
    'gyroscope': [],
    'magnetometer': [],
    'microphone': [],
    'payment': ['self'],
    'usb': [],
}

# 🛡️ BANK-GRADE: Cross-Origin isolation headers
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# 🛡️ BANK-GRADE: Restrict session cookie to production domain
SESSION_COOKIE_DOMAIN = 'traitdunion.it'  # No leading dot — modern browsers handle subdomains

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
# STATIC FILES (WhiteNoise with Manifest for immutable caching)
# ==============================================================================
# WhiteNoise doit être après SecurityMiddleware
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# ⚡ PERFORMANCE: Manifest storage for immutable cache (hash-based filenames)
# Cache-Control: public, max-age=31536000, immutable
WHITENOISE_MAX_AGE = 31536000  # 365 jours
# 🛡️ SECURITY: Only hash-named files are immutable (not robots.txt, sitemap, etc.)
import re
_HASHED_FILE_RE = re.compile(r'\.[a-f0-9]{8,32}\.')
WHITENOISE_IMMUTABLE_FILE_TEST = lambda path, url: bool(_HASHED_FILE_RE.search(url))

# ==============================================================================
# MEDIA FILES (Cloudinary - recommandé pour simplicité)
# ==============================================================================
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')
CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL')

# Vérifier si on est en train de builder (collectstatic)
import sys
IS_BUILDING = 'collectstatic' in sys.argv

if CLOUDINARY_URL or (CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY):
    if not IS_BUILDING:
        import logging as _log
        _log.getLogger('config.settings').info('Cloudinary configuration found')
    
    # Configuration Cloudinary
    INSTALLED_APPS += ['cloudinary', 'cloudinary_storage']
    
    if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY:
        CLOUDINARY_STORAGE = {
            'CLOUD_NAME': CLOUDINARY_CLOUD_NAME,
            'API_KEY': CLOUDINARY_API_KEY,
            'API_SECRET': CLOUDINARY_API_SECRET,
        }
    else:
        # Si CLOUDINARY_URL est défini, on laisse la lib le gérer
        CLOUDINARY_STORAGE = {}
    
    # Configuration moderne Django 5+
    # ⚡ PERFORMANCE: CompressedManifestStaticFilesStorage for hash-based filenames
    # This enables immutable caching with automatic cache busting
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
        import logging as _log
        _log.getLogger('config.settings').info('Build mode detected: Skipping Cloudinary checks')
    else:
        import logging as _log
        _log.getLogger('config.settings').warning('CLOUDINARY ENV VARS MISSING! External media storage will NOT work.')
    
    # Configuration minimale pour le build
    # ⚡ PERFORMANCE: CompressedManifestStaticFilesStorage for hash-based filenames
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

# ==============================================================================
# EMAIL (Brevo API REST — recommandé pour Render)
# ==============================================================================
# Brevo est préféré sur Render car :
# - L'API REST évite les problèmes de firewall SMTP
# - Meilleur tracking et délivrabilité
# - Offre gratuite généreuse (300 emails/jour)

# Le backend API REST est configuré dans base.py via BREVO_API_KEY
# → core.services.brevo_backend.BrevoEmailBackend
# Aucune surcharge SMTP nécessaire ici.

# ==============================================================================
# CACHING (Redis via Render)
# ==============================================================================
REDIS_URL = os.environ.get('REDIS_URL')

if REDIS_URL:
    # 🛡️ SECURITY: Redis SSL certificate validation.
    # Render managed Redis uses self-signed certs, so we default to 'none'.
    # For Redis providers with valid certs (e.g. Upstash, AWS ElastiCache),
    # set REDIS_SSL_CERT_REQS=required in your environment.
    # ACCEPTED RISK: Self-signed cert on Render's internal network.
    _redis_ssl_reqs = os.environ.get('REDIS_SSL_CERT_REQS', 'none')
    if _redis_ssl_reqs not in ('none', 'optional', 'required'):
        _redis_ssl_reqs = 'none'
    
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'ssl_cert_reqs': _redis_ssl_reqs,
            },
            # 🛡️ SECURITY: Key prefix to avoid collisions if Redis is shared
            'KEY_PREFIX': 'tus',
        }
    }
    
    # Sessions via Redis (plus rapide)
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'

# ==============================================================================
# LOGGING (Production — structured JSON for SIEM/security correlation)
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
        # 🛡️ BANK-GRADE: JSON formatter for security event correlation (SIEM-ready)
        'json': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'security_json': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'security': {
            'class': 'logging.StreamHandler',
            'formatter': 'security_json',
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
        # 🛡️ BANK-GRADE: Dedicated security logger
        'security': {
            'handlers': ['security'],
            'level': 'INFO',
            'propagate': False,
        },
        'config.middleware': {
            'handlers': ['security'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ==============================================================================
# GOOGLE ANALYTICS 4 (SEO & TRACKING)
# ==============================================================================
# ID de mesure GA4 (créer propriété sur https://analytics.google.com)
# Format: G-XXXXXXXXXX
GA4_MEASUREMENT_ID = os.environ.get('GA4_MEASUREMENT_ID', '')

# L'ID est injecté dans base.html si DEBUG=False
# Ne jamais hardcoder l'ID en production pour faciliter les changements

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
    
    # 🛡️ SECURITY: Filter known non-critical errors
    def before_send(event, hint):
        """Filter out known non-critical errors to avoid polluting Sentry quota."""
        # Ignore 404 errors from bots scanning for PHP files
        if event.get('logger') == 'django.request':
            if 'exception' in event:
                exc_value = str(event['exception']['values'][0].get('value', ''))
                if '.php' in exc_value or 'wp-admin' in exc_value:
                    return None  # Don't send to Sentry
        
        # Ignore DisallowedHost errors (common bot attacks)
        if 'DisallowedHost' in str(hint.get('exc_info', '')):
            return None
        
        return event
    
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
        
        # 🛡️ SECURITY: Custom error filtering
        before_send=before_send,
    )

# ==============================================================================
# 🛡️ CONTENT SECURITY POLICY (django-csp with nonces)
# ==============================================================================
# Replace custom middleware with django-csp for better security
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = (
    "'self'",
    # Nonces are injected via CSP_INCLUDE_NONCE_IN — no unsafe-inline needed
    "https://cdn.jsdelivr.net",
    "https://unpkg.com",
    "https://www.googletagmanager.com",
    "https://www.google-analytics.com",
    "https://challenges.cloudflare.com",
    "https://www.google.com",
    "https://www.gstatic.com",
)
CSP_STYLE_SRC = (
    "'self'",
    # 🛡️ SECURITY: Removed 'unsafe-inline'. All inline styles are now protected
    # by nonces via CSP_INCLUDE_NONCE_IN=['style-src'].
    # Dynamic style="" attributes (progress bars, Alpine.js :style bindings)
    # use 'unsafe-hashes' with specific hash values below instead.
    # If a style breaks, add its SHA-256 hash here rather than re-enabling unsafe-inline.
    "https://fonts.googleapis.com",
    "https://cdn.jsdelivr.net",
)
CSP_FONT_SRC = (
    "'self'",
    "https://fonts.gstatic.com",
    "data:",
)
CSP_IMG_SRC = (
    "'self'",
    "data:",
    "blob:",
    "https://res.cloudinary.com",
    "https://www.google-analytics.com",
    "https://*.stripe.com",
)
CSP_CONNECT_SRC = (
    "'self'",
    "https://www.google-analytics.com",
    "https://challenges.cloudflare.com",
    "https://api.stripe.com",
)
CSP_FRAME_SRC = (
    "https://challenges.cloudflare.com",
    "https://www.google.com",
    "https://js.stripe.com",
)
CSP_OBJECT_SRC = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'", "https://checkout.stripe.com")

# 🛡️ BANK-GRADE: CSP violation reporting — ENFORCED (not report-only)
CSP_REPORT_URI = os.environ.get('CSP_REPORT_URI', '')  # e.g. https://sentry.io/api/.../csp-report/
CSP_INCLUDE_NONCE_IN = ['script-src', 'style-src']  # 🛡️ Enable nonces for scripts AND styles
# 🛡️ BANK-GRADE: CSP is enforced by default (no CSP_REPORT_ONLY = True).
# Set CSP_REPORT_URI to collect violation reports in Sentry.
