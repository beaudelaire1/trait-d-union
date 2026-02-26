"""Health check endpoint for monitoring and Docker HEALTHCHECK."""
from django.db import connection
from django.http import JsonResponse


def healthz(request):
    """Return HTTP 200 if the application is healthy, 503 otherwise.

    Checks:
    - Database connectivity (SELECT 1)
    - Cache backend availability (set/get cycle)
    """
    checks = {"database": False, "cache": False}

    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = True
    except Exception:
        pass

    # Cache check
    try:
        from django.core.cache import cache
        cache.set("healthz_probe", "ok", 10)
        checks["cache"] = cache.get("healthz_probe") == "ok"
    except Exception:
        pass

    healthy = all(checks.values())
    return JsonResponse(
        {"status": "ok" if healthy else "degraded", "checks": checks},
        status=200 if healthy else 503,
    )
