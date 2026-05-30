"""Interface abstraite `PDPClient` + DTOs.

Tout adapter (B2Brouter, Pennylane, Sellsy, ...) doit implémenter cette
interface. Le métier travaille uniquement contre cette abstraction.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:  # pragma: no cover
    from apps.factures.models import Invoice


# ---------------------------------------------------------------------------
# DTOs (immuables) — découplés des modèles Django
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class PDPSubmission:
    """Le résultat d'un POST de facture vers une PDP."""

    external_id: str             # identifiant interne PDP (track ID)
    state: str                   # état initial annoncé par la PDP
    accepted_at: datetime
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PDPLifecycleEvent:
    """Événement de cycle de vie reçu de la PDP (Flux 6 DGFiP)."""

    external_id: str
    state: str                   # SUBMITTED / SENT / DELIVERED / APPROVED / REJECTED / PAID
    occurred_at: datetime
    reason: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SubmissionResult:
    """Résultat compact d'une soumission (sucre syntaxique pour l'admin/UI)."""

    submission: PDPSubmission
    invoice_id: int


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
class PDPClient(ABC):
    """Contrat commun à toutes les PDP supportées par TUS."""

    #: identifiant logique du provider (ex. "b2brouter", "pennylane")
    provider: str = ""

    # -------- Soumission ---------------------------------------------------
    @abstractmethod
    def submit_invoice(
        self,
        invoice: "Invoice",
        *,
        facturx_pdf: bytes | None = None,
        cii_xml: bytes | None = None,
    ) -> PDPSubmission:
        """Pousse une facture vers la PDP.

        L'adapter peut accepter un Factur-X complet (PDF/A-3 + XML) OU le XML
        seul OU les deux. Retourne un identifiant externe + état initial.

        Lève :
        - PDPAuthError       : clé invalide
        - PDPValidationError : facture rejetée par la PDP (format, données)
        - PDPRateLimitError  : 429
        - PDPTransportError  : timeout / 5xx
        """

    # -------- Suivi du cycle de vie ----------------------------------------
    @abstractmethod
    def get_lifecycle(self, external_id: str) -> list[PDPLifecycleEvent]:
        """Récupère le journal d'événements pour une facture déjà soumise."""

    # -------- Annuaire / SIREN→PDP ----------------------------------------
    @abstractmethod
    def lookup_directory(self, siren_or_siret: str) -> Optional[dict[str, Any]]:
        """Cherche un destinataire dans l'annuaire central PDP/PPF.

        Retourne `None` si introuvable, sinon un dict avec au minimum
        `{name, siret, peppol_id, country_code}`.
        """

    # -------- Webhook ------------------------------------------------------
    def verify_webhook_signature(self, *, body: bytes, signature_header: str) -> bool:
        """Vérifie la signature d'un webhook entrant. Implémentation par défaut
        utilise `apps.einvoicing.webhooks.verify_b2brouter_signature`.

        Les adapters peuvent override pour leur propre format de signature.
        """
        from ..webhooks import verify_b2brouter_signature
        return verify_b2brouter_signature(body=body, header=signature_header)


__all__ = [
    "PDPClient",
    "PDPSubmission",
    "PDPLifecycleEvent",
    "SubmissionResult",
]
