from __future__ import annotations

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _has_keys(site_key: str, secret_key: str) -> bool:
    return bool(site_key) and bool(secret_key)


def verify_recaptcha(token: str, remote_ip: str = '') -> bool:
    secret_key = getattr(settings, 'RECAPTCHA_SECRET_KEY', '')
    site_key = getattr(settings, 'RECAPTCHA_SITE_KEY', '')

    if not _has_keys(site_key, secret_key):
        logger.debug('reCAPTCHA: Missing keys, skipping validation')
        return True

    if not token:
        logger.warning('reCAPTCHA: Missing token from client')
        return False

    try:
        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': secret_key,
                'response': token,
                'remoteip': remote_ip,
            },
            timeout=5,
        )
        result = response.json()

        if not result.get('success'):
            error_codes = result.get('error-codes', [])
            logger.warning('reCAPTCHA verification failed: %s', error_codes)
            if 'invalid-input-secret' in error_codes or 'bad-request' in error_codes:
                logger.error('reCAPTCHA: Invalid secret key or malformed request')
                return True
            return False

        return True
    except requests.RequestException as exc:
        logger.error('reCAPTCHA API error: %s', exc)
        return True


def verify_turnstile(token: str, remote_ip: str = '') -> bool:
    secret_key = getattr(settings, 'TURNSTILE_SECRET_KEY', '')
    site_key = getattr(settings, 'TURNSTILE_SITE_KEY', '')

    if not _has_keys(site_key, secret_key):
        logger.debug('Turnstile: Missing keys, skipping validation')
        return True

    if not token:
        logger.warning('Turnstile: Missing token from client')
        return False

    try:
        response = requests.post(
            'https://challenges.cloudflare.com/turnstile/v0/siteverify',
            data={
                'secret': secret_key,
                'response': token,
                'remoteip': remote_ip,
            },
            timeout=5,
        )
        result = response.json()

        if not result.get('success'):
            error_codes = result.get('error-codes', [])
            logger.warning('Turnstile verification failed: %s', error_codes)
            if 'invalid-input-secret' in error_codes or 'bad-request' in error_codes:
                logger.error('Turnstile: Invalid secret key or malformed request')
                return True
            return False

        return True
    except requests.RequestException as exc:
        logger.error('Turnstile API error: %s', exc)
        return True
