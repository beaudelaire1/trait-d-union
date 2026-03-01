#!/usr/bin/env bash
# ==============================================================================
# build.sh - Script de build pour Render.com
# ==============================================================================
# Ce script est exécuté automatiquement par Render lors du déploiement
# ==============================================================================

set -o errexit  # Exit immédiatement si une commande échoue

# Forcer l'utilisation de la configuration production
export DJANGO_SETTINGS_MODULE=config.settings.production

echo "=========================================="
echo "🚀 TRAIT D'UNION STUDIO - Build Script"
echo "=========================================="

# 1. Installer les dépendances Python
echo ""
echo "📦 Installation des dépendances..."
pip install --upgrade pip
pip install -r requirements.txt

# 2. Collecter les fichiers statiques
echo ""
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput --clear

# 3. Appliquer les migrations
echo ""
echo "🗄️  Application des migrations..."
python manage.py migrate --noinput

# 4. Créer le superuser si nécessaire (première installation)
echo ""
echo "👤 Vérification du superuser..."
# 🛡️ SECURITY: Use createsuperuser --noinput to avoid password in build logs
python manage.py shell -c "
from django.contrib.auth import get_user_model
import os
User = get_user_model()
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@traitdunion.it')
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
if password and not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print('Superuser created.')
elif not password:
    print('DJANGO_SUPERUSER_PASSWORD not set, skipping.')
else:
    print('Superuser already exists.')
"

echo ""
echo "=========================================="
echo "✅ Build terminé avec succès!"
echo "=========================================="
