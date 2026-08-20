#!/usr/bin/env sh
# Runtime-only operations for Coolify. Configure this file as the application's
# Post-deployment Command: sh ./coolify-postdeploy.sh
set -eu

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.coolify}"

echo "[TUS] Applying database migrations..."
python manage.py migrate --noinput

echo "[TUS] Normalizing django-allauth email records..."
python manage.py fix_email_addresses --apply

# Initial admin creation is opt-in. Define all three variables in Coolify only
# for the first deployment, then remove DJANGO_SUPERUSER_PASSWORD afterwards.
if [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
    echo "[TUS] Ensuring initial superuser exists..."
    python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@traitdunion.it")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")

if password and not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"[TUS] Superuser '{username}' created.")
else:
    print(f"[TUS] Superuser '{username}' already exists; no change.")
PY
fi

echo "[TUS] Post-deployment operations completed."
