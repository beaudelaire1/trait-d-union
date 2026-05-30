"""Factory `get_pdp_client()` — point d'entrée unique pour l'application."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from django.conf import settings

from .base import PDPClient


@lru_cache(maxsize=8)
def _build_client(provider: str, sandbox: bool, version: str) -> PDPClient:
    if provider == "b2brouter":
        from .b2brouter import B2BrouterClient
        return B2BrouterClient(sandbox=sandbox, api_version=version)
    if provider == "iopole":
        from .iopole import IopoleClient
        return IopoleClient(sandbox=sandbox)
    raise ValueError(f"Provider PDP inconnu : {provider!r}")


def get_pdp_client(provider: Optional[str] = None) -> PDPClient:
    """Retourne un client PDP configuré.

    Lit `settings.INVOICING['PDP']` et instancie l'adapter correspondant.
    L'instance est mise en cache (un client par tuple provider/sandbox/version).
    """
    cfg = ((getattr(settings, "INVOICING", {}) or {}).get("PDP") or {})
    provider = provider or cfg.get("PROVIDER", "b2brouter")
    sandbox = bool(cfg.get("SANDBOX", True))
    version = cfg.get("API_VERSION", "2026-03-02")
    return _build_client(provider, sandbox, version)


__all__ = ["get_pdp_client"]
