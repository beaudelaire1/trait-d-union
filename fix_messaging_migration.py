#!/usr/bin/env python
"""Script pour corriger les migrations messaging sur production."""
import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'

import django
django.setup()

from django.db import connection

print("=" * 50)
print("🔧 Correction des migrations messaging sur PRODUCTION")
print("=" * 50)

with connection.cursor() as cursor:
    # Supprimer les tables messaging car elles sont nouvelles
    print("Suppression des tables messaging...")
    cursor.execute("DROP TABLE IF EXISTS messaging_prospectmessage CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS messaging_prospectactivity CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS messaging_campaignrecipient CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS messaging_emailcampaign CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS messaging_prospect CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS messaging_emailtemplate CASCADE;")
    print("✅ Tables messaging supprimées")
    
    # Supprimer les entrées de migration pour messaging
    print("Nettoyage des migrations messaging...")
    cursor.execute("DELETE FROM django_migrations WHERE app = 'messaging';")
    print("✅ Entrées migrations messaging supprimées")

print("\n🔄 Relance des migrations...")
from django.core.management import call_command
call_command('migrate', 'messaging', '--noinput', verbosity=1)

print("\n✅ Migrations messaging appliquées avec succès!")
