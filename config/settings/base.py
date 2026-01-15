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