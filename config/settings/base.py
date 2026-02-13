"""Base Django settings for Trait d'Union Studio website.

This file contains settings common to all environments. Environment-specific
settings (development, production) extend and override values defined here.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


# Base directory of the project
#
# ``__file__`` points to ``tus_website/config/settings/base.py``.  The
# directory structure is as follows:
#
# tus_website/
# ├── config/
# │   └── settings/
# │       └── base.py  ← this file
# ├── static/
# ├── templates/
# └── apps/
#
# We want ``BASE_DIR`` to resolve to the top‑level ``tus_website`` directory
# rather than the repository root.  Using ``parents[2]`` ascends
# from ``base.py`` → ``settings`` (0), ``config`` (1), ``tus_website`` (2).
BASE_DIR = Path(__file__).resolve().parents[2]

# Load environment variables from .env file (only in development, don't override existing)
load_dotenv(BASE_DIR / '.env', override=False)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'changeme-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS: list[str] = []

# Application definition
INSTALLED_APPS = [
    'jazzmin',  # Admin premium personnalisé
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.sites',
    'django_htmx',
    # allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # local apps
    'apps.pages',
    'apps.portfolio',
    'apps.leads',
    'apps.resources',
    'apps.devis',
    'apps.factures',
    'apps.chroniques',
    'apps.clients',
    'apps.messaging',
    'services',
]

# Django Sites framework
SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # HTMX must come before CommonMiddleware to set the proper flags
    'django_htmx.middleware.HtmxMiddleware',
    # allauth
    'allauth.account.middleware.AccountMiddleware',
    # custom middlewares
    'config.middleware.RateLimitMiddleware',
    'config.middleware.SecurityHeadersMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # The base template directory.  Because the Django project is
        # organised under ``tus_website/``, templates live in
        # ``tus_website/templates`` rather than the repository root.
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# https://docs.djangoproject.com/en/stable/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
# https://docs.djangoproject.com/en/stable/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files uploaded by users.  Ensure the ``media`` directory exists in
# the project root.  In development this folder is served by the
# ``django.views.static.serve`` view when ``DEBUG = True``.
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# EMAIL CONFIGURATION
# ==============================================================================
# Backend par défaut (console en dev)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Brevo (ex-Sendinblue) API pour les emails transactionnels
# En production, utiliser l'API Brevo plutôt que SMTP (plus fiable sur Render)
BREVO_API_KEY = os.environ.get('BREVO_API_KEY', '')

# Configuration expéditeur
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'contact@traitdunion.it')
DEFAULT_FROM_NAME = os.environ.get('DEFAULT_FROM_NAME', "Trait d'Union Studio")

# Email admin pour les notifications internes
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'contact@traitdunion.it')

# Email pour les notifications de tâches async (Celery) et alertes critiques
# Si non défini, utilise ADMIN_EMAIL comme fallback
TASK_NOTIFICATION_EMAIL = os.environ.get('TASK_NOTIFICATION_EMAIL', os.environ.get('ADMIN_EMAIL', 'contact@traitdunion.it'))

# reCAPTCHA v2 checkbox settings
# Obtenez vos clés sur https://www.google.com/recaptcha/admin
# Choisissez reCAPTCHA v2 "Je ne suis pas un robot" (checkbox)
RECAPTCHA_SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY', '')
RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY', '')

# ==============================================================================
# PHASE 3 : STRIPE PAYMENT CONFIGURATION
# ==============================================================================
# Configuration Stripe pour les paiements en ligne
# Obtenez vos clés sur https://dashboard.stripe.com/apikeys
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

# Taux d'acompte par défaut (30%)
QUOTE_DEPOSIT_RATE = 0.30

# ==============================================================================
# CRM INTEGRATION (Airtable / HubSpot)
# ==============================================================================
AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY', '')
AIRTABLE_BASE_ID = os.environ.get('AIRTABLE_BASE_ID', '')
AIRTABLE_TABLE_NAME = os.environ.get('AIRTABLE_TABLE_NAME', 'Leads')
HUBSPOT_API_KEY = os.environ.get('HUBSPOT_API_KEY', '')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

# Branding pour les devis et factures
INVOICE_BRANDING = {
    'name': 'Trait d\'Union Studio',
    'tagline': "Quand l'élégance se conçoit, la performance se déploie",
    'address': '258 Av Justin Catayée Rte de la Madeleine',
    'city': 'Cayenne',
    'zip_code': '97300',
    'region': 'Guyane',
    'country': 'Guyane française',
    'phone': '+594 695 35 80 41',
    'email': 'contact@traitdunion.it',
    'website': 'https://traitdunion.it',
    'siret': '908 264 112 00016',
    'tva_intra': '',
    'iban': 'FR76 1980 6001 8940 2584 2883 094',
    'bic': 'AGRIMQMX',
    'logo_url': '/static/img/tus-logo.svg',
}

QUOTE_BRANDING = INVOICE_BRANDING  # Alias pour les devis

# Site URL (pour les emails)
SITE_URL = os.environ.get('SITE_URL', 'https://traitdunion.it')

# Jazzmin Admin Theme Configuration
JAZZMIN_SETTINGS = {
    # Branding
    "site_title": "TUS · Admin",
    "site_header": "TUS",
    "site_brand": "Trait d'Union",
    "site_logo": "img/tus-logo.svg",
    "login_logo": "img/tus-logo.svg",
    "site_logo_classes": "",
    "site_icon": "img/tus-icon.svg",
    "welcome_sign": "",
    "copyright": "Trait d'Union Studio · Guyane",
    "user_avatar": None,

    # Top menu — accès rapide
    "topmenu_links": [
        {"name": "Dashboard", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Leads", "url": "admin:leads_lead_changelist", "permissions": ["leads.view_lead"]},
        {"name": "Devis", "url": "admin:devis_quote_changelist", "permissions": ["devis.view_quote"]},
        {"name": "Factures", "url": "admin:factures_invoice_changelist", "permissions": ["factures.view_invoice"]},
        {"name": "↗ Site", "url": "/", "new_window": True},
    ],

    # Sidebar
    "show_sidebar": True,
    "navigation_expanded": False,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": [
        "leads", "devis", "factures", "clients",
        "portfolio", "chroniques", "pages", "resources",
        "auth",
    ],

    # Icônes premium
    "icons": {
        "auth": "fas fa-shield-alt",
        "auth.user": "fas fa-user-astronaut",
        "auth.Group": "fas fa-layer-group",
        "leads.Lead": "fas fa-bolt",
        "leads.Client": "fas fa-handshake",
        "leads.EmailComposition": "fas fa-paper-plane",
        "portfolio.Project": "fas fa-gem",
        "portfolio.ProjectImage": "fas fa-camera-retro",
        "devis.Quote": "fas fa-file-signature",
        "devis.QuoteItem": "fas fa-stream",
        "factures.Invoice": "fas fa-file-invoice-dollar",
        "factures.InvoiceItem": "fas fa-receipt",
        "clients.ClientProfile": "fas fa-id-badge",
        "chroniques.Article": "fas fa-pen-nib",
        "chroniques.Category": "fas fa-tags",
        "pages.Page": "fas fa-pager",
        "resources.Resource": "fas fa-cubes",
        "services.Service": "fas fa-concierge-bell",
    },
    "default_icon_parents": "fas fa-chevron-right",
    "default_icon_children": "fas fa-angle-right",

    # UX
    "related_modal_active": True,
    "custom_css": "css/admin_custom.css",
    "custom_js": "js/admin_custom.js",
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs",
    },
}

# Jazzmin UI Tweaks
JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": True,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": True,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": True,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "darkly",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-outline-light",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
    "actions_sticky_top": True,
}

# ============================================================================
# Django Allauth Configuration (Client Portal)
# ============================================================================
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Allauth settings
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_EMAIL_SUBJECT_PREFIX = ''  # Pas de préfixe [Site]

# Redirections
LOGIN_REDIRECT_URL = '/espace-client/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/accounts/login/'