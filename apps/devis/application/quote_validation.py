from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from django.db import transaction

from devis.email_service import send_quote_validation_code
from devis.models import Quote, QuoteValidation

logger = logging.getLogger(__name__)


class QuoteNotValidatableError(Exception):
    """Le devis n'est pas dans un état permettant la validation."""


class QuoteValidationExpiredError(Exception):
    """Le jeton/code de validation a expiré."""


@dataclass(frozen=True)
class QuoteValidationStartResult:
    quote: Quote
    validation: QuoteValidation


def start_quote_validation(
    quote: Quote,
    *,
    request=None,
    to_email: Optional[str] = None,
    ttl_minutes: int = 15,
) -> QuoteValidationStartResult:
    """Démarre le workflow de validation (2FA) pour un devis.

    Règles:
    - Le devis doit être au statut SENT.
    - Un nouveau QuoteValidation est créé (les précédents non confirmés sont invalidés).
    - Un email OTP est envoyé au client.
    """
    if quote.status != Quote.QuoteStatus.SENT:
        raise QuoteNotValidatableError(f"Devis non validable (status={quote.status!r}).")

    validation = QuoteValidation.create_for_quote(quote, ttl_minutes=ttl_minutes)
    send_quote_validation_code(quote, validation, request=request, to_email=to_email)
    return QuoteValidationStartResult(quote=quote, validation=validation)


def get_pending_validation_for_quote(quote: Quote) -> QuoteValidation:
    """Retourne la validation en cours la plus récente (non confirmée) pour un devis."""
    return (
        QuoteValidation.objects.filter(quote=quote, confirmed_at__isnull=True)
        .latest("created_at")
    )


def confirm_quote_validation_code(
    *,
    validation: QuoteValidation,
    submitted_code: str,
) -> bool:
    """Confirme un code de validation et applique les effets métier.

    Effets métier si le code est valide:
    - devis.status = ACCEPTED
    - régénération du PDF (best-effort)
    - notification UI/email (best-effort)
    """
    quote = validation.quote

    if validation.is_expired:
        raise QuoteValidationExpiredError("Validation expirée.")

    ok = validation.verify(submitted_code)
    if not ok:
        return False

    with transaction.atomic():
        if quote.status != Quote.QuoteStatus.ACCEPTED:
            quote.status = Quote.QuoteStatus.ACCEPTED
            quote.save(update_fields=["status"])

    # Best-effort: regenerate PDF to ensure current content
    try:
        quote.generate_pdf(attach=True)
    except Exception:
        logger.exception("Echec génération PDF après validation devis (%s)", getattr(quote, "number", quote.pk))

    # Best-effort: notify admins/clients
    try:
        from core.services.notification_service import NotificationService

        NotificationService().notify_quote_validation(quote)
    except Exception:
        logger.exception("Echec notification après validation devis (%s)", getattr(quote, "number", quote.pk))

    return True


