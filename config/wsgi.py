"""WSGI config for TUS website.

This exposes the WSGI callable as a module-level variable named ``application``.

En local, le .env définit DJANGO_SETTINGS_MODULE=config.settings.development.
En production (Render), la variable d'environnement est définie dans le dashboard
et pointe vers config.settings.production — le setdefault ci-dessous est un filet
de sécurité uniquement.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Charger .env si présent (dev local) — ne surcharge PAS les vars déjà définies (prod)
_env_path = Path(__file__).resolve().parent.parent / '.env'
if _env_path.exists():
    load_dotenv(_env_path, override=False)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()