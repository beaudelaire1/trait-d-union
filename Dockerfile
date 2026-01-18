# ==============================================================================
# Dockerfile - Trait d'Union Studio
# ==============================================================================
# Multi-stage build optimisé pour Render.com
# Inclut les dépendances système pour WeasyPrint (génération PDF)

# ------------------------------------------------------------------------------
# STAGE 1: Builder - Installation des dépendances
# ------------------------------------------------------------------------------
FROM python:3.12-slim as builder

# Variables d'environnement pour Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Installer les dépendances de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les requirements
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# ------------------------------------------------------------------------------
# STAGE 2: Runtime - Image finale légère
# ------------------------------------------------------------------------------
FROM python:3.12-slim as runtime

# Labels
LABEL maintainer="contact@traitdunion.it" \
      version="1.0" \
      description="Trait d'Union Studio - Site vitrine & gestion commerciale"

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Django
    DJANGO_SETTINGS_MODULE=config.settings.production \
    # Port pour Render
    PORT=8000

# Créer un utilisateur non-root pour la sécurité
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# ==============================================================================
# DÉPENDANCES SYSTÈME POUR WEASYPRINT
# ==============================================================================
# WeasyPrint nécessite Pango, Cairo et leurs dépendances pour générer des PDFs
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        # WeasyPrint dependencies
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libcairo2 \
        libgdk-pixbuf2.0-0 \
        libffi-dev \
        shared-mime-info \
        # Fonts pour les PDFs
        fonts-liberation \
        fonts-dejavu-core \
        # PostgreSQL client
        libpq5 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copier les wheels depuis le builder
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copier le code source
COPY --chown=appuser:appgroup . .

# Créer les répertoires nécessaires
RUN mkdir -p /app/staticfiles /app/media && \
    chown -R appuser:appgroup /app/staticfiles /app/media

# Collecter les fichiers statiques
RUN python manage.py collectstatic --noinput --clear

# Passer à l'utilisateur non-root
USER appuser

# Exposer le port
EXPOSE ${PORT}

# ==============================================================================
# COMMANDE DE DÉMARRAGE
# ==============================================================================
# Gunicorn avec workers optimisés pour Render
# - 2 workers (adapté aux instances Render Standard)
# - 4 threads par worker (meilleur pour I/O bound comme BDD)
# - Timeout de 120s pour les générations PDF longues
CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --timeout 120 --access-logfile - --error-logfile -"]
