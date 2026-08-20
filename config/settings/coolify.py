"""Production settings for Trait d'Union Studio on Coolify/OVH.

This module deliberately extends ``production.py`` instead of replacing it.
Render can therefore keep using ``config.settings.production`` while Coolify
uses ``config.settings.coolify`` during the migration.
"""
from .production import *  # noqa: F401,F403

import os

import dj_database_url


def _csv_env(name: str, default: str) -> list[str]:
    """Read a comma-separated environment variable without empty entries."""
    return [
        value.strip()
        for value in os.environ.get(name, default).split(",")
        if value.strip()
    ]


# Coolify's Docker healthcheck reaches Django through localhost. Keep the
# public whitelist strict while explicitly allowing local container probes.
ALLOWED_HOSTS = _csv_env(
    "DJANGO_ALLOWED_HOSTS",
    "traitdunion.it,www.traitdunion.it,localhost,127.0.0.1",
)

CSRF_TRUSTED_ORIGINS = _csv_env(
    "CSRF_TRUSTED_ORIGINS",
    "https://traitdunion.it,https://www.traitdunion.it",
)

# Coolify terminates HTTPS at its reverse proxy and forwards the original
# protocol through X-Forwarded-Proto, as production.py already expects.
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# PostgreSQL on Coolify commonly lives on the private Docker network. The
# default libpq mode ``prefer`` works with both a non-TLS internal database and
# a TLS-enabled PostgreSQL instance. Set DB_SSLMODE=require once PostgreSQL SSL
# is enabled if strict transport encryption is desired.
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
DB_SSLMODE = os.environ.get("DB_SSLMODE", "prefer").strip().lower()
_ALLOWED_SSLMODES = {"disable", "allow", "prefer", "require", "verify-ca", "verify-full"}
if DB_SSLMODE not in _ALLOWED_SSLMODES:
    DB_SSLMODE = "prefer"

if DATABASE_URL:
    DATABASES["default"] = dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=False,
    )

    # Do not inject PostgreSQL-only options into the SQLite URL used during
    # Docker image build/collectstatic.
    if DATABASES["default"].get("ENGINE", "").endswith("postgresql"):
        DATABASES["default"].setdefault("OPTIONS", {})["sslmode"] = DB_SSLMODE
else:
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", ""),
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "CONN_MAX_AGE": 600,
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {"sslmode": DB_SSLMODE},
    }
