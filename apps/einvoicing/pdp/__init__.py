"""Couche d'abstraction PDP — Plateformes Agréées (réforme FR 2026/2027).

Exporte l'interface `PDPClient` et le factory `get_pdp_client()`. Le code
métier ne doit JAMAIS importer un adapter concret directement : passer
toujours par le factory pour permettre le swap d'adapter.
"""

from .base import (  # noqa: F401
    PDPClient,
    PDPSubmission,
    PDPLifecycleEvent,
    SubmissionResult,
)
from .exceptions import (  # noqa: F401
    PDPError,
    PDPAuthError,
    PDPRateLimitError,
    PDPValidationError,
    PDPTransportError,
    PDPNotFoundError,
)
from .factory import get_pdp_client  # noqa: F401
