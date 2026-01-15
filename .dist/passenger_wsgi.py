"""Passenger WSGI configuration for Hostinger."""
import os
import sys

# Chemin vers le projet Django
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_DIR, '.env'))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
