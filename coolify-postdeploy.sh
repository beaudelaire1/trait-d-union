#!/usr/bin/env sh
# Runtime-only operations for Coolify. Configure this file as the application's
# Post-deployment Command: sh ./coolify-postdeploy.sh
set -eu

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.coolify}"

echo "[TUS] Applying database migrations..."
python manage.py migrate --noinput

echo "[TUS] Normalizing django-allauth email records..."
python manage.py fix_email_addresses --apply

# Le portfolio n'est pas alimenté par les migrations : sans ces appels, les
# études de cas n'apparaissent jamais en ligne. « --si-absent » ne publie
# qu'une fois : les déploiements suivants ne réécrivent pas ce que l'admin a
# retouché.
echo "[TUS] Publishing the case studies if missing..."
python manage.py seed_iteag --si-absent
python manage.py seed_eebc --si-absent
python manage.py seed_netexpress --si-absent

# Remplissage initial des audits portfolio (chapitre 05), pour les fiches sans
# mesure. Repris de « build.sh », le pré-déploiement Render supprimé avec le
# reste de cet outillage. Non bloquant à dessein : une panne réseau ou un
# dépassement de délai chez SSL Labs ne doit jamais casser un déploiement.
echo "[TUS] Filling in missing portfolio audits..."
python manage.py audit_portfolio_projects --only-missing || \
    echo "[TUS] Portfolio audit skipped (non-blocking)."

# Ce qui n'a pas de remplaçant sous Coolify. « render.yaml » planifiait trois
# tâches récurrentes, consignées ici pour que leur suppression n'efface pas
# leur existence. Un post-déploiement ne les remplace pas : il faut un
# planificateur, côté Coolify ou en cron sur la machine.
#
#   sync_google_reviews               toutes les 6 heures   0 */6 * * *
#   audit_portfolio_projects          lundi à 04h00         0 4 * * 1
#   resend_unsent_simulator_reports   tous les quarts d'h.  */15 * * * *

# Initial admin creation is opt-in. Define all three variables in Coolify only
# for the first deployment, then remove DJANGO_SUPERUSER_PASSWORD afterwards.
if [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
    echo "[TUS] Ensuring initial superuser exists..."
    python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "contact@traitdunion.studio")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")

if password and not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"[TUS] Superuser '{username}' created.")
else:
    print(f"[TUS] Superuser '{username}' already exists; no change.")
PY
fi

echo "[TUS] Post-deployment operations completed."
