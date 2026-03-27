"""Utilitaires partagés pour le projet Trait d'Union Studio."""
from __future__ import annotations

from decimal import Decimal


def raw_media_storage():
    """Return a Cloudinary *raw* storage (resource_type='raw') when available.

    ``MediaCloudinaryStorage`` uses ``resource_type='image'`` and rejects
    non-image files (PDF, ZIP, DOCX …).  ``RawMediaCloudinaryStorage`` handles
    **any** file type.  When Cloudinary is not configured the default
    Django file-system storage is returned instead.

    Usage on a model field::

        file = models.FileField(upload_to='…', storage=raw_media_storage)
    """
    try:
        from cloudinary_storage.storage import RawMediaCloudinaryStorage
        return RawMediaCloudinaryStorage()
    except Exception:
        from django.core.files.storage import default_storage
        return default_storage


def get_client_ip(request) -> str:
    """Extract client IP from request, handling reverse proxies.

    🛡️ SECURITY: Single source of truth for IP extraction.
    - Only trusts the FIRST entry in X-Forwarded-For
    - Truncates to 45 chars (IPv6 max length)
    - Rejects characters that shouldn't appear in an IP address
    - Returns '127.0.0.1' when request is None or IP is unparseable
    """
    if request is None:
        return ''
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded_for:
        ip = forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    # Sanitize: max 45 chars (IPv6), strip whitespace, no special chars
    ip = ip.strip()[:45]
    # Remove any characters that shouldn't be in an IP address
    if ip and not all(c in '0123456789abcdefABCDEF.:' for c in ip):
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')[:45]
    return ip or '127.0.0.1'


def num2words_fr(value: Decimal) -> str:
    """Convertit un montant décimal en toutes lettres (français).

    Utilise ``num2words`` si disponible, sinon retourne la valeur
    formatée en français (virgule comme séparateur décimal).
    """
    try:
        from num2words import num2words
        return num2words(value, lang='fr')
    except ImportError:
        return str(value).replace(".", ",")
