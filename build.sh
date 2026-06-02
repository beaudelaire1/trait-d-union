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

# 3. Fix: ajouter EmailAddress allauth vérifiée pour les comptes existants
echo ""
echo "📧 Vérification des EmailAddress allauth..."
python manage.py fix_email_addresses --apply

# 4. Fix: augmenter la tolérance TOTP (±90s) pour compenser le drift d'horloge cloud
echo ""
echo "🔐 Mise à jour tolérance TOTP..."
python manage.py shell << 'EOFTOTP'
from django_otp.plugins.otp_totp.models import TOTPDevice
updated = TOTPDevice.objects.filter(tolerance__lt=3).update(tolerance=3)
if updated:
    print(f"✅ {updated} device(s) TOTP mis à jour (tolerance=3)")
else:
    print("ℹ️  Tous les devices TOTP ont déjà tolerance≥3")
# Reset throttling au déploiement pour débloquer après échecs
reset = TOTPDevice.objects.filter(throttling_failure_count__gt=0).update(
    throttling_failure_count=0, throttling_failure_timestamp=None
)
if reset:
    print(f"🔓 {reset} device(s) TOTP débloqué(s) (throttling reset)")
EOFTOTP

# 5. Remplissage initial des audits portfolio (Ch.05) — projets sans mesure.
#    Inclut SSL Labs pour obtenir le grade officiel A+/A (scan mis en cache
#    côté SSL Labs, donc rapide aux déploiements suivants). Non bloquant :
#    un échec/timeout réseau ne doit jamais casser le déploiement — le grade
#    provisoire interne assure un badge en attendant, et le prochain déploiement
#    (ou le cron hebdo) récupère le grade officiel.
echo ""
echo "📊 Audit portfolio (remplissage initial des projets sans mesure)..."
python manage.py audit_portfolio_projects --only-missing || \
    echo "⚠️  Audit portfolio ignoré (non bloquant) — sera relancé par le cron."

echo ""
echo "=========================================="
echo "✅ Pre-deploy terminé avec succès!"
echo "=========================================="