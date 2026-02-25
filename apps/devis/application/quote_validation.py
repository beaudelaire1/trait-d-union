from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from apps.devis.email_service import send_quote_validation_code
from apps.devis.models import Quote, QuoteValidation

logger = logging.getLogger(__name__)


class QuoteNotValidatableError(Exception):
    """Le devis n'est pas dans un état permettant la validation."""


class QuoteValidationExpiredError(Exception):
    """Le jeton/code de validation a expiré."""


class QuoteValidationRateLimitError(Exception):
    """Trop de demandes de code OTP pour ce devis."""


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
    - Rate-limit : 1 envoi OTP par minute par devis (anti-spam email).
    - Un nouveau QuoteValidation est créé (les précédents non confirmés sont invalidés).
    - Un email OTP est envoyé au client.
    """
    if quote.status != Quote.QuoteStatus.SENT:
        raise QuoteNotValidatableError(f"Devis non validable (status={quote.status!r}).")

    # Rate-limit : 1 code OTP par minute par devis
    rate_key = f"otp_ratelimit:quote:{quote.pk}"
    if cache.get(rate_key):
        raise QuoteValidationRateLimitError(
            "Un code vient d'être envoyé. Veuillez patienter 1 minute."
        )

    validation = QuoteValidation.create_for_quote(quote, ttl_minutes=ttl_minutes)
    send_quote_validation_code(quote, validation, request=request, to_email=to_email)

    cache.set(rate_key, 1, 60)  # 60 secondes de cooldown
    return QuoteValidationStartResult(quote=quote, validation=validation)


def get_pending_validation_for_quote(quote: Quote) -> QuoteValidation:
    """Retourne la validation en cours la plus récente (non confirmée) pour un devis."""
    return (
        QuoteValidation.objects.filter(quote=quote, confirmed_at__isnull=True)
        .latest("created_at")
    )


def _get_client_ip(request) -> str:
    """Extrait l'IP du client depuis la requête HTTP."""
    if request is None:
        return ""
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if xff:
        return xff.split(",")[0].strip()[:45]
    return request.META.get("REMOTE_ADDR", "")[:45]


def confirm_quote_validation_code(
    *,
    validation: QuoteValidation,
    submitted_code: str,
    request=None,
) -> bool:
    """Confirme un code de validation et applique les effets métier.

    Conçu comme signature électronique fiable :
    - devis.status = ACCEPTED
    - devis.validated_at = horodatage de la confirmation
    - devis.validated_audit_trail = {ip, user_agent, method, timestamp, validation_id}
    - régénération du PDF (best-effort)
    - notification admin par email (best-effort)
    - le signal post_save déclenche l'onboarding client automatique
    """
    quote = validation.quote

    if validation.is_expired:
        raise QuoteValidationExpiredError("Validation expirée.")

    ok = validation.verify(submitted_code)
    if not ok:
        return False

    # ── Audit trail e-signature ──────────────────────────────────
    now = timezone.now()
    audit_trail = {
        "method": "otp_code",
        "timestamp": now.isoformat(),
        "validation_id": validation.pk,
        "ip": _get_client_ip(request),
        "user_agent": (
            request.META.get("HTTP_USER_AGENT", "")[:500]
            if request else ""
        ),
        "quote_number": quote.number,
        "code_sent_at": validation.created_at.isoformat(),
        "code_confirmed_at": now.isoformat(),
    }

    with transaction.atomic():
        quote.status = Quote.QuoteStatus.ACCEPTED
        quote.validated_at = now
        quote.validated_audit_trail = audit_trail
        quote.save(update_fields=[
            "status",
            "validated_at",
            "validated_audit_trail",
        ])

    logger.info(
        "Devis %s accepté par le client (e-signature OTP, IP=%s)",
        quote.number,
        audit_trail["ip"],
    )

    # Best-effort: regenerate PDF to include validation info
    try:
        quote.generate_pdf(attach=True)
    except Exception:
        logger.exception(
            "Echec génération PDF après validation devis (%s)",
            quote.number,
        )

    # Best-effort: notification admin
    try:
        _notify_admin_quote_accepted(quote, audit_trail)
    except Exception:
        logger.exception(
            "Echec notification admin après validation devis (%s)",
            quote.number,
        )

    return True


def _notify_admin_quote_accepted(quote: Quote, audit_trail: dict) -> None:
    """Envoie un email de notification à l'admin quand un client accepte un devis."""
    from django.conf import settings
    from django.core.mail import EmailMessage
    from django.template.loader import render_to_string

    admin_email = (
        getattr(settings, "TASK_NOTIFICATION_EMAIL", None)
        or getattr(settings, "ADMIN_EMAIL", None)
        or "contact@traitdunion.it"
    )

    client = getattr(quote, "client", None)
    client_name = getattr(client, "full_name", "N/A") if client else "N/A"
    client_email = getattr(client, "email", "N/A") if client else "N/A"

    subject = f"\u2705 Devis {quote.number} accepté par le client"
    body = (
        f"Le devis <strong>{quote.number}</strong> a été accepté par le client "
        f"via signature électronique (code OTP).\n\n"
        f"<strong>Client :</strong> {client_name} ({client_email})\n"
        f"<strong>Montant TTC :</strong> {quote.total_ttc} €\n"
        f"<strong>Date :</strong> {audit_trail.get('timestamp', '')}\n"
        f"<strong>IP :</strong> {audit_trail.get('ip', 'N/A')}\n"
    )

    try:
        html_body = render_to_string(
            "emails/notification_generic.html",
            {
                "headline": "Devis accepté",
                "message": body.replace("\n", "<br>"),
                "details": [
                    {"label": "Devis", "value": quote.number},
                    {"label": "Client", "value": f"{client_name} ({client_email})"},
                    {"label": "Montant TTC", "value": f"{quote.total_ttc} €"},
                ],
            },
        )
    except Exception:
        html_body = body.replace("\n", "<br>")

    email = EmailMessage(
        subject=subject,
        body=html_body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "contact@traitdunion.it"),
        to=[admin_email],
    )
    email.content_subtype = "html"
    email.send(fail_silently=False)
    logger.info("Notification admin envoyée pour devis %s à %s", quote.number, admin_email)


