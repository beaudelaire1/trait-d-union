#!/usr/bin/env bash
# ==============================================================================
# build.sh - Script pre-deploy pour Render.com (Docker runtime)
# ==============================================================================
# Exécuté APRÈS le build Docker, AVANT le démarrage du service.
# Les dépendances pip et collectstatic sont gérés dans le Dockerfile.
# Ce script ne gère que les opérations nécessitant la BDD de production.
# ==============================================================================

set -o errexit  # Exit immédiatement si une commande échoue

export DJANGO_SETTINGS_MODULE=config.settings.production

echo "=========================================="
echo "🚀 TRAIT D'UNION STUDIO - Pre-deploy"
echo "=========================================="

# 1. Appliquer les migrations
echo ""
echo "🗄️  Application des migrations..."
python manage.py migrate --noinput

# 2. Créer le superuser si nécessaire (première installation)
echo ""
echo "👤 Vérification du superuser..."
python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()
import os

email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@traitdunion.it')
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if password and not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"✅ Superuser '{username}' créé!")
else:
    print(f"ℹ️  Superuser '{username}' existe déjà ou DJANGO_SUPERUSER_PASSWORD non défini")
EOF

echo ""
echo "=========================================="
echo "✅ Pre-deploy terminé avec succès!"
echo "=========================================="
