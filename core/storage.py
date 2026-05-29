"""Custom static files storage for production.

🛡️ ROBUSTNESS: ``CompressedManifestStaticFilesStorage`` raises a ``ValueError``
(HTTP 500) at template render time whenever a ``{% static %}`` tag references a
file that is missing from the manifest. Third-party apps such as Jazzmin
reference theme assets (e.g. ``vendor/bootswatch/...``) that may not always be
collected or post-processed cleanly, which can take down the whole admin
(including the login page) with a 500 error.

Setting ``manifest_strict = False`` makes the storage fall back to the original
(un-hashed) path for missing entries instead of crashing. The page still renders;
at worst a single asset is served without cache-busting.
"""
from whitenoise.storage import CompressedManifestStaticFilesStorage


class ResilientManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    """Manifest static storage that does not 500 on missing entries."""

    # Fall back to the passed-in name instead of raising ValueError.
    manifest_strict = False
