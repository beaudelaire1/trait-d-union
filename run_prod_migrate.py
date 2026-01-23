#!/usr/bin/env python
"""Script pour appliquer les migrations sur la base de production."""
import os
import sys

# Forcer les settings de production
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'

# Installer les dépendances manquantes si nécessaire
try:
    import dj_database_url
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'dj-database-url', 'psycopg2-binary'])
    import dj_database_url

import django
django.setup()

from django.db import connection
from django.core.management import call_command

print("=" * 50)
print("🚀 Migration sur la base de PRODUCTION")
print("=" * 50)
print(f"Host: {connection.settings_dict['HOST']}")
print(f"Database: {connection.settings_dict['NAME']}")
print("=" * 50)

call_command('migrate', '--noinput', verbosity=2)
print("\n✅ Migrations appliquées avec succès!")
