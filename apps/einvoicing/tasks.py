"""Jobs asynchrones django-q2 pour l'envoi PDP."""

from __future__ import annotations

import logging

from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)


def _async_q(func_path: str, *args, sync_fallback: bool = True, **kwargs):
    """Délègue à django-q2 si dispo, sinon exécution synchrone (CI/dev/tests)."""
    try:
        from django_q.tasks import async_task
    except Exception:  # noqa: BLE001
        async_task = None  # type: ignore[assignment]
    if async_task is not None:
        try:
            return async_task(func_path, *args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            logger.warning("django-q indisponible (%s) — fallback sync.", exc)
            if not sync_fallback:
                raise
    func = import_string(func_path)
    return func(*args, **kwargs)


def submit_invoice_async(invoice_id: int) -> None:
    """À planifier en async via `_async_q`."""
    from apps.factures.models import Invoice
    from .services import submit_invoice_to_pdp

    invoice = Invoice.objects.get(pk=invoice_id)
    submit_invoice_to_pdp(invoice)


def queue_submit_invoice(invoice_id: int):
    return _async_q("apps.einvoicing.tasks.submit_invoice_async", invoice_id)


__all__ = ["submit_invoice_async", "queue_submit_invoice"]
