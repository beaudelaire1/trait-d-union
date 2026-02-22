from __future__ import annotations

from django.conf import settings


def captcha_settings(request):
    turnstile_site_key = getattr(settings, 'TURNSTILE_SITE_KEY', '')
    recaptcha_site_key = getattr(settings, 'RECAPTCHA_SITE_KEY', '')
    timeout_ms = getattr(settings, 'TURNSTILE_FALLBACK_TIMEOUT_MS', 2500)
    try:
        timeout_ms = int(timeout_ms)
    except (TypeError, ValueError):
        timeout_ms = 2500

    return {
        'turnstile_site_key': turnstile_site_key,
        'recaptcha_site_key': recaptcha_site_key,
        'turnstile_fallback_timeout_ms': timeout_ms,
    }
