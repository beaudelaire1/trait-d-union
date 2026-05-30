"""Endpoints Django pour les webhooks PDP entrants.

Sécurité (commune à toutes les Plateformes Agréées supportées) :
- POST uniquement
- Vérification HMAC-SHA256 obligatoire (header dépendant du provider)
- Anti-replay (timestamp signé, tolérance 5 min)
- Logs structurés sans PII de la facture (numéro + état uniquement)

Endpoints :
- ``/webhooks/b2brouter/`` (provider=b2brouter, header X-B2Brouter-Signature)
- ``/webhooks/iopole/``    (provider=iopole,    header X-Iopole-Signature)
"""

from __future__ import annotations

import json
import logging

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .codelists import LifecycleState
from .pdp import get_pdp_client
from .services import ingest_lifecycle_event

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Cœur générique
# ---------------------------------------------------------------------------
def _process_webhook(request, *, provider: str, signature_header: str):
    """Pipeline commun : vérification de signature + ingestion."""
    body = request.body or b""
    signature = request.headers.get(signature_header, "")

    pdp = get_pdp_client(provider)
    if not pdp.verify_webhook_signature(body=body, signature_header=signature):
        logger.warning("Webhook %s rejeté : signature invalide.", provider)
        return HttpResponseForbidden("invalid signature")

    try:
        payload = json.loads(body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return HttpResponseBadRequest("invalid json")

    event_type = (payload.get("event") or payload.get("type") or "").lower()
    data = payload.get("data") or payload

    invoice = _resolve_invoice(data)
    if invoice is None:
        logger.info("Webhook %s : facture introuvable (event=%s).", provider, event_type)
        # On répond 204 quand-même pour éviter que le PDP retry indéfiniment.
        return HttpResponse(status=204)

    state = _normalize_state(data.get("state") or data.get("status") or "")
    if not state:
        return HttpResponse(status=204)

    ingest_lifecycle_event(
        invoice,
        state=state,
        source=f"pdp.{provider}.webhook",
        payload={
            "event": event_type,
            "external_id": invoice.external_pdp_id,
            "reason": data.get("reason") or data.get("rejection_reason") or "",
        },
    )
    return HttpResponse(status=204)


# ---------------------------------------------------------------------------
# Vues exposées
# ---------------------------------------------------------------------------
@csrf_exempt
@require_POST
def b2brouter_webhook(request):
    """Réception des notifications de cycle de vie B2Brouter."""
    return _process_webhook(
        request, provider="b2brouter", signature_header="X-B2Brouter-Signature"
    )


@csrf_exempt
@require_POST
def iopole_webhook(request):
    """Réception des notifications de cycle de vie IOPOLE."""
    return _process_webhook(
        request, provider="iopole", signature_header="X-Iopole-Signature"
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _resolve_invoice(data: dict):
    """Retrouve la facture liée au webhook (par external_pdp_id puis par numéro)."""
    from apps.factures.models import Invoice

    external_id = str(data.get("invoice_id") or data.get("id") or "")
    if external_id:
        inv = Invoice.objects.filter(external_pdp_id=external_id).first()
        if inv is not None:
            return inv
    number = str(data.get("external_reference") or data.get("number") or "")
    if number:
        return Invoice.objects.filter(number=number).first()
    return None


def _normalize_state(state: str) -> str:
    """Mappe un état PDP / DGFiP CDAR vers `LifecycleState`."""
    if not state:
        return ""
    mapping = {
        "DEPOSEE": LifecycleState.SUBMITTED,
        "DEPOSITED": LifecycleState.SUBMITTED,
        "RECUE": LifecycleState.DELIVERED,
        "RECEIVED": LifecycleState.DELIVERED,
        "DELIVERED": LifecycleState.DELIVERED,
        "APPROUVEE": LifecycleState.APPROVED,
        "APPROVED": LifecycleState.APPROVED,
        "REFUSEE": LifecycleState.REJECTED,
        "REJECTED": LifecycleState.REJECTED,
        "DISPUTED": LifecycleState.DISPUTED,
        "ENCAISSEE": LifecycleState.PAID,
        "PAID": LifecycleState.PAID,
        "SENT": LifecycleState.SENT,
        "SUBMITTED": LifecycleState.SUBMITTED,
        "CANCELLED": LifecycleState.CANCELLED,
    }
    return mapping.get(state.upper(), "")


__all__ = ["b2brouter_webhook", "iopole_webhook"]
