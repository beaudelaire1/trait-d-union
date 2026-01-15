"""View definitions for the static pages of the site."""
from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView


class HomeView(TemplateView):
    """Landing page of the website.

    Displays the slogan, previews of the services, testimonials and calls to action.
    The context will be populated with three services and sample testimonials.
    """

    template_name: str = 'pages/home.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        # TODO: replace by dynamic content or database entries
        context['services'] = [
            {
                'title': 'Site vitrine',
                'description': 'Présentez votre marque avec élégance et efficacité.',
                'icon': '🌐',
            },
            {
                'title': 'E‑commerce',
                'description': 'Vendez vos produits en ligne avec une expérience haut de gamme.',
                'icon': '🛒',
            },
            {
                'title': 'Plateforme/ERP',
                'description': 'Construisez des outils internes sur mesure pour votre activité.',
                'icon': '⚙️',
            },
        ]
        context['testimonials'] = []  # placeholder
        return context


class ServicesView(TemplateView):
    """Services overview page."""

    template_name: str = 'pages/services.html'


class MethodView(TemplateView):
    """Methodology page describing the five‑step process."""

    template_name: str = 'pages/method.html'


class LegalView(TemplateView):
    """Legal pages (mentions légales, politique de confidentialité)."""

    # The template can be selected dynamically based on the URL; placeholder for now
    template_name: str = 'pages/legal.html'


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    """Custom 404 page handler."""
    return render(request, 'errors/404.html', status=404)


def server_error(request: HttpRequest) -> HttpResponse:
    """Custom 500 page handler."""
    return render(request, 'errors/500.html', status=500)