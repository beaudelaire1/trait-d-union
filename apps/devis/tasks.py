"""
Tâches asynchrones pour les devis.

REFACTORISÉ : Les tâches sont maintenant centralisées dans ``core.tasks``
et exécutées via django-q2.

Ce module conserve les fonctions pour rétrocompatibilité, mais elles
délèguent au système de tâches centralisé.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def send_quote_pdf_email(quote_id: int) -> None:
    """Envoie le PDF du devis par email (async via django-q2)."""
    from core.tasks import async_send_quote_pdf_email
    async_send_quote_pdf_email(quote_id)


def send_quote_request_received(quote_request_id: int) -> None:
    """Confirme la demande de devis au client + notifie l'admin (async)."""
    from core.tasks import async_notify_quote_request
    async_notify_quote_request(quote_request_id)
