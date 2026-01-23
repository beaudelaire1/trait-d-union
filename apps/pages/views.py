"""View definitions for the static pages of the site."""
from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView

from services.models import Service


class HomeView(TemplateView):
    """Landing page of the website.

    Displays the slogan, previews of the services, testimonials and calls to action.
    The context will be populated with featured services and testimonials from the database.
    """

    template_name: str = 'pages/home.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        
        # Charger les services depuis la base de données
        services_qs = Service.objects.filter(is_active=True, is_featured=True)[:4]
        context['services'] = [
            {
                'title': service.name,
                'description': service.short_description or service.description[:150],
                'icon': service.category.icon if service.category else '🔧',
                'slug': service.slug,
            }
            for service in services_qs
        ]
        
        # Charger les témoignages depuis la base de données
        from apps.pages.models import Testimonial
        context['testimonials'] = Testimonial.objects.filter(is_published=True)[:3]
        
        return context


class ServicesView(TemplateView):
    """Services overview page."""

    template_name: str = 'pages/services.html'


class MethodView(TemplateView):
    """Methodology page describing the five‑step process."""

    template_name: str = 'pages/method.html'


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    """Custom 404 page handler."""
    return render(request, 'errors/404.html', status=404)


def server_error(request: HttpRequest) -> HttpResponse:
    """Custom 500 page handler."""
    return render(request, 'errors/500.html', status=500)