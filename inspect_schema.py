import os
import sqlite3
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
import django
django.setup()

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(devis_quote)")
columns = cursor.fetchall()
print("Colonnes de la table devis_quote:")
for col in columns:
    print(f"{col[1]:30} - {col[2]}")
