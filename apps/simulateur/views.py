"""Views for the standalone Simulateur app."""
from __future__ import annotations

from typing import Any

from django.views.generic import TemplateView

from services.models import Service


class SimulateurView(TemplateView):
    """Page de simulation interactive de devis / facture."""

    template_name: str = 'simulateur/simulateur.html'

    def dispatch(self, request, *args, **kwargs):
        from django.middleware.csrf import get_token
        get_token(request)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['services'] = list(
            Service.objects.filter(is_active=True)
            .values('name', 'base_price', 'price_unit')
            .order_by('name')
        )
        context['breadcrumbs_list'] = [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'Simulateur', 'url': '/simulateur/'},
        ]
        return context
