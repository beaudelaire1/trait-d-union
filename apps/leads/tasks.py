"""Async tasks for the leads app (Django-Q2)."""
from __future__ import annotations

import logging
import time

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


def send_bulk_emails_task(
    emails: list[str],
    subject: str,
    html_body: str,
    delay_seconds: float,
    body_html_raw: str,
    template_id: str | None,
    user_id: int,
) -> dict:
    """Send bulk emails one by one with a delay between each.

    This function is designed to be called via ``django_q.tasks.async_task``
    so that the HTTP request returns immediately while emails are sent in the
    background by a Django-Q2 worker.

    Returns a summary dict with success/failure counts.
    """
    from core.services.email_backends import brevo_service
    from .email_models import EmailComposition
    from django.contrib.auth import get_user_model

    User = get_user_model()

    success_count = 0
    failed_emails: list[str] = []

    for i, recipient in enumerate(emails):
        try:
            result = brevo_service.send_email(
                to_email=recipient,
                subject=subject,
                html_content=html_body,
                tags=['bulk-email', 'prospection'],
            )

            if result.get('success'):
                success_count += 1
                logger.info("[%d/%d] Email envoyé à %s", i + 1, len(emails), recipient)
            else:
                failed_emails.append(recipient)
                logger.error(
                    "[%d/%d] Échec envoi à %s: %s",
                    i + 1, len(emails), recipient, result.get('error'),
                )

            # Delay between sends to avoid rate limits
            if i < len(emails) - 1 and delay_seconds > 0:
                time.sleep(delay_seconds)

        except Exception as e:
            failed_emails.append(recipient)
            logger.error("Erreur envoi à %s: %s", recipient, e)

    # Record campaign in EmailComposition for history
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        user = None

    EmailComposition.objects.create(
        to_emails=', '.join(emails[:10]) + (f'... (+{len(emails) - 10})' if len(emails) > 10 else ''),
        subject=f"[BULK x{len(emails)}] {subject}",
        body_html=body_html_raw,
        template_id=template_id if template_id else None,
        is_draft=False,
        sent_at=timezone.now(),
        created_by=user,
    )

    logger.info(
        "Bulk email terminé: %d/%d envoyés, %d échecs",
        success_count, len(emails), len(failed_emails),
    )

    return {
        'total': len(emails),
        'success': success_count,
        'failed': failed_emails,
    }
