"""Durcissement des réponses publiques de facturation."""
from __future__ import annotations

from django.http import HttpResponse

from .views import invoice_public_pdf as _invoice_public_pdf


def invoice_public_pdf(request, token: str) -> HttpResponse:
    """Délivre une facture publique sans conservation dans les caches."""
    response = _invoice_public_pdf(request, token)
    response['Cache-Control'] = 'private, no-store, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response
