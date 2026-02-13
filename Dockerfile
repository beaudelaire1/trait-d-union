# ==============================================================================
# Dockerfile - Trait d'Union Studio
# ==============================================================================
# Image simple basée sur Python Bookworm (miroirs Debian stables)

FROM python:3.11-bookworm

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    PORT=8000 \
    DJANGO_SECRET_KEY=dummy-build-key-not-used-in-production \
    DATABASE_URL=sqlite:///dummy.db

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

# Collecter les fichiers statiques (StaticFilesStorage en prod, pas de manifest strict)
RUN python manage.py collectstatic --noinput --clear

# Port
EXPOSE ${PORT}

# Démarrage - Force les settings de production
CMD ["sh", "-c", "DJANGO_SETTINGS_MODULE=config.settings.production gunicorn config.wsgi:application --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --timeout 120"]
