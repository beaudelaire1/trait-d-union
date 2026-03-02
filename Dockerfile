# ==============================================================================
# Dockerfile - Trait d'Union Studio (multi-stage build)
# ==============================================================================
# Stage 1: Build dependencies + collectstatic
# Stage 2: Slim production image

# ── STAGE 1 : Builder ────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install build dependencies (needed for pip compile steps, weasyprint libs, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── STAGE 2 : Production ─────────────────────────────────────────
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    PORT=8000

WORKDIR /app

# Runtime-only system dependencies (WeasyPrint + PostgreSQL client)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi8 \
    shared-mime-info \
    fonts-liberation \
    fonts-dejavu-core \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy source code
COPY . .

# Create directories
RUN mkdir -p /app/staticfiles /app/media

# Collect static files (build-time only — generate a throwaway secret key)
RUN DJANGO_SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')" \
    DATABASE_URL=sqlite:///dummy.db \
    python manage.py collectstatic --noinput --clear

# Create non-root user for security
RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup --home /home/appuser appuser \
    && mkdir -p /home/appuser \
    && chown -R appuser:appgroup /app /home/appuser
USER appuser

EXPOSE ${PORT}

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/healthz/')" || exit 1

# Gunicorn with production settings
# --preload : charge l'app UNE SEULE FOIS dans le master process avant de fork
# les workers. Garantit que SECRET_KEY, settings et connexions DB sont
# identiques dans tous les workers (élimine le risque de clé aléatoire
# différente par worker si DJANGO_SECRET_KEY est absent/faible).
CMD ["sh", "-c", "DJANGO_SETTINGS_MODULE=config.settings.production gunicorn config.wsgi:application --preload --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --timeout 120"]
