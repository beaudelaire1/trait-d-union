"""Health check endpoint for monitoring and Docker HEALTHCHECK."""
from django.conf import settings
from django.db import connection
from django.http import JsonResponse


def healthz(request):
    """Return HTTP 200 if the application is healthy, 503 otherwise.

    Checks:
    - Database connectivity (SELECT 1)
    - Cache backend availability (set/get cycle)
    - Redis connectivity (if configured)

    🛡️ SECURITY: Detail checks are hidden in production to prevent info leakage.
    """
    checks = {"database": False, "cache": False, "redis": False}

    # Database check - ORM connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = True
    except Exception:
        checks["database"] = False

    # Cache check (Redis or LocMem)
    try:
        from django.core.cache import cache
        cache.set("healthz_probe", "ok", 10)
        checks["cache"] = cache.get("healthz_probe") == "ok"
    except Exception:
        checks["cache"] = False

    # Redis check (if configured separately from cache)
    try:
        from django.conf import settings
        redis_url = getattr(settings, 'REDIS_URL', None)
        if redis_url:
            import redis
            r = redis.from_url(redis_url, socket_connect_timeout=2)
            r.ping()
            checks["redis"] = True
        else:
            checks["redis"] = "not_configured"
    except Exception:
        checks["redis"] = False

    # Overall health status
    critical_checks = [checks["database"], checks["cache"]]
    healthy = all(critical_checks)

    # 🛡️ SECURITY: In production, only return status — never expose check details
    if not settings.DEBUG:
        return JsonResponse(
            {"status": "healthy" if healthy else "degraded"},
            status=200 if healthy else 503,
        )

    return JsonResponse(
        {
            "status": "healthy" if healthy else "degraded",
            "checks": checks,
        },
        status=200 if healthy else 503,
    )

