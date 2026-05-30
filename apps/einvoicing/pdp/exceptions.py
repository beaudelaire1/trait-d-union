"""Hiérarchie d'exceptions PDP — découple le métier du provider.

Le code applicatif (admin, tasks, API) ne capture JAMAIS d'exception spécifique
B2Brouter (`requests.HTTPError`, etc.). Il capture uniquement ces classes
abstraites, ce qui permet un swap de provider sans toucher au métier.
"""

from __future__ import annotations


class PDPError(Exception):
    """Erreur PDP générique (parent de toutes les autres)."""

    def __init__(self, message: str = "", *, provider: str = "", status_code: int | None = None,
                 payload: dict | None = None) -> None:
        super().__init__(message or self.__class__.__name__)
        self.provider = provider
        self.status_code = status_code
        self.payload = payload or {}


class PDPAuthError(PDPError):
    """Authentification refusée (clé API absente, expirée ou invalide)."""


class PDPRateLimitError(PDPError):
    """Trop de requêtes — l'appelant doit retry avec backoff."""

    def __init__(self, message: str = "", *, retry_after: int | None = None, **kwargs) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class PDPValidationError(PDPError):
    """La PDP a rejeté la facture (format, champs manquants, SIREN inconnu)."""


class PDPNotFoundError(PDPError):
    """Ressource introuvable côté PDP (id externe inconnu)."""


class PDPTransportError(PDPError):
    """Erreur réseau / timeout / 5xx — le retry a souvent du sens."""


__all__ = [
    "PDPError",
    "PDPAuthError",
    "PDPRateLimitError",
    "PDPValidationError",
    "PDPNotFoundError",
    "PDPTransportError",
]
