# ==============================================================================
# Dockerfile - Trait d'Union Studio
# ==============================================================================
# Image simple basée sur Python Bookworm (miroirs Debian stables)

FROM python:3.12-bookworm

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    PORT=8000

# Build-time only args (non persistants dans l'image finale)
ARG DJANGO_SECRET_KEY=build-only-placeholder
ARG DATABASE_URL=sqlite:///dummy.db

WORKDIR /app

# Dépendances système WeasyPrint
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    fonts-dejavu-core \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les requirements Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Créer les répertoires
RUN mkdir -p /app/staticfiles /app/media

# Collecter les fichiers statiques (ARGs disponibles au build-time uniquement)
RUN DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY} DATABASE_URL=${DATABASE_URL} \
    python manage.py collectstatic --noinput --clear

# Créer un utilisateur non-root pour la sécurité (avec home dir pour pip/cache)
RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup --home /home/appuser appuser \
    && mkdir -p /home/appuser \
    && chown -R appuser:appgroup /app /home/appuser
USER appuser

# Port
EXPOSE ${PORT}

# Health check — vérifie que l'app répond
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/healthz/')" || exit 1

# Démarrage - Force les settings de production
CMD ["sh", "-c", "DJANGO_SETTINGS_MODULE=config.settings.production gunicorn config.wsgi:application --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --timeout 120"]
