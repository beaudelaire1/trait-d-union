"""Durcissement des réponses publiques contenant des données commerciales."""
from __future__ import annotations

from django.http import HttpResponse

from .views import quote_public_pdf as _quote_public_pdf


def quote_public_pdf(request, token: str) -> HttpResponse:
    """Délivre un devis public sans autoriser son stockage par les caches partagés.

    Le jeton protège l'accès, mais le document contient des données commerciales
    et parfois personnelles. La réponse doit donc rester strictement privée et
    ne pas être conservée par un navigateur, un proxy ou un CDN.
    """
    response = _quote_public_pdf(request, token)
    response['Cache-Control'] = 'private, no-store, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response
