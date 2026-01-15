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

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'changeme-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS: list[str] = []

# Application definition
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django_htmx',
    # local apps
    'apps.pages',
    'apps.portfolio',
    'apps.leads',
    'apps.resources',
    'apps.devis',
    'apps.factures',
    'services',
]

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

# Email backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Email configuration
# In production, override via environment variables
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'contact@traitdunion.it')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'contact@traitdunion.it')

# reCAPTCHA v3 settings
# Obtenez vos clés sur https://www.google.com/recaptcha/admin
RECAPTCHA_SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY', '')
RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY', '')
RECAPTCHA_SCORE_THRESHOLD = 0.5  # Score minimum (0.0 à 1.0)

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
    'address': '97300 Cayenne',
    'city': 'Cayenne',
    'zip_code': '97300',
    'region': 'Guyane',
    'country': 'France',
    'phone': '',
    'email': 'contact@traitdunion.it',
    'website': 'https://traitdunion.it',
    'siret': '',
    'tva_intra': '',
    'iban': '',
    'bic': '',
    'logo_url': '/static/img/tus-logo.svg',
}

QUOTE_BRANDING = INVOICE_BRANDING  # Alias pour les devis

# Site URL (pour les emails)
SITE_URL = os.environ.get('SITE_URL', 'https://traitdunion.it')

# Jazzmin Admin Theme Configuration
JAZZMIN_SETTINGS = {
    # title of the window (Will default to current_admin_site.site_title if absent or None)
    "site_title": "Trait d'Union Studio",

    # Title on the login screen (19 chars max) (defaults to current_admin_site.site_header if absent or None)
    "site_header": "TUS Admin",

    # Title on the brand (19 chars max) (defaults to current_admin_site.site_header if absent or None)
    "site_brand": "Trait d'Union Studio",

    # Logo to use for your site, must be present in static files, used for brand on top left
    "site_logo": None,

    # Logo to use for your site, must be present in static files, used for login form logo (defaults to site_logo)
    "login_logo": None,

    # CSS classes that are applied to the logo above
    "site_logo_classes": "img-circle",

    # Relative path to a favicon for your site, will default to site_logo if absent (ideally 32x32 px)
    "site_icon": None,

    # Welcome text on the login screen
    "welcome_sign": "Bienvenue sur l'administration TUS",

    # Copyright on the footer
    "copyright": "Trait d'Union Studio",

    # Field name on user model that contains avatar ImageField/URLField/Charfield or a callable that receives the user
    "user_avatar": None,

    # Links to put along the top menu
    "topmenu_links": [
        # Url that gets reversed (Permissions can be added)
        {"name": "Accueil", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Voir le site", "url": "/", "new_window": True},
    ],

    # Whether to display the side menu
    "show_sidebar": True,

    # Whether to aut expand the menu
    "navigation_expanded": True,

    # Hide these apps when generating side menu e.g (auth)
    "hide_apps": [],

    # Hide these models when generating side menu (e.g auth.user)
    "hide_models": [],

    # List of apps (and/or models) to base side menu ordering off of (does not need to contain all apps/models)
    "order_with_respect_to": ["auth", "apps.leads", "apps.portfolio", "apps.devis", "apps.factures"],

    # Custom icons for side menu apps/models
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "leads.Lead": "fas fa-envelope",
        "leads.Client": "fas fa-address-book",
        "portfolio.Project": "fas fa-briefcase",
        "portfolio.ProjectImage": "fas fa-images",
        "devis.Quote": "fas fa-file-alt",
        "devis.QuoteItem": "fas fa-list",
        "factures.Invoice": "fas fa-file-invoice",
        "factures.InvoiceItem": "fas fa-list-alt",
    },

    # Icons that are used when one is not manually specified
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",

    # Use modals instead of popups
    "related_modal_active": False,

    # Custom CSS/JS (must be present in static files)
    "custom_css": None,
    "custom_js": None,

    # Whether to show the UI customizer on the sidebar
    "show_ui_builder": False,

    # Theme overrides
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {"auth.user": "collapsible", "auth.group": "vertical_tabs"},
}

# Jazzmin UI Tweaks
JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "darkly",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    },
    "actions_sticky_top": True,
}