"""View definitions for the static pages of the site."""
from __future__ import annotations

from typing import Any

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
        
        # ⚡ PERFORMANCE: Cache homepage data (services, testimonials, portfolio count)
        from django.core.cache import cache
        
        # Charger les services depuis la base de données (cached 5 min)
        services_data = cache.get('homepage_services')
        if services_data is None:
            services_qs = Service.objects.select_related('category').filter(is_active=True, is_featured=True)[:4]
            services_data = [
                {
                    'title': service.name,
                    'description': service.short_description or service.description[:150],
                    'icon': service.category.icon if service.category else '🔧',
                    'slug': service.slug,
                }
                for service in services_qs
            ]
            cache.set('homepage_services', services_data, 300)
        context['services'] = services_data
        
        # Charger les témoignages depuis la base de données (cached 5 min)
        testimonials = cache.get('homepage_testimonials')
        if testimonials is None:
            from apps.pages.models import Testimonial
            testimonials = list(Testimonial.objects.filter(is_published=True)[:3])
            cache.set('homepage_testimonials', testimonials, 300)
        context['testimonials'] = testimonials
        
        # Compteur dynamique de projets portfolio (cached 10 min)
        portfolio_count = cache.get('homepage_portfolio_count')
        if portfolio_count is None:
            from apps.portfolio.models import Project
            portfolio_count = Project.objects.filter(is_published=True).count()
            cache.set('homepage_portfolio_count', portfolio_count, 600)
        context['portfolio_count'] = portfolio_count
        
        # Breadcrumbs SEO (page d'accueil = racine)
        context['breadcrumbs_list'] = [
            {'name': 'Accueil', 'url': '/'},
        ]
        
        return context


class ServicesView(TemplateView):
    """Services overview page."""

    template_name: str = 'pages/services.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['breadcrumbs_list'] = [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'Services', 'url': '/services/'},
        ]
        return context


class MethodView(TemplateView):
    """Methodology page describing the five‑step process."""

    template_name: str = 'pages/method.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['breadcrumbs_list'] = [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'Méthode', 'url': '/method/'},
        ]
        return context


class FAQView(TemplateView):
    """FAQ page with breadcrumbs for SEO rich snippets."""

    template_name: str = 'pages/faq.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['breadcrumbs_list'] = [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'FAQ', 'url': '/faq/'},
        ]
        return context


class MentionsLegalesView(TemplateView):
    """Mentions légales page with breadcrumbs."""

    template_name: str = 'pages/mentions_legales.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['breadcrumbs_list'] = [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'Mentions légales', 'url': '/mentions-legales/'},
        ]
        return context


class ConfidentialiteView(TemplateView):
    """Politique de confidentialité page with breadcrumbs."""

    template_name: str = 'pages/confidentialite.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['breadcrumbs_list'] = [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'Politique de confidentialité', 'url': '/confidentialite/'},
        ]
        return context


class CGVView(TemplateView):
    """Conditions générales de vente page with breadcrumbs."""

    template_name: str = 'pages/cgv.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['breadcrumbs_list'] = [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'Conditions générales de vente', 'url': '/cgv/'},
        ]
        return context


class LegalView(TemplateView):
    """Legal page with breadcrumbs."""

    template_name: str = 'pages/legal.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['breadcrumbs_list'] = [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'Informations légales', 'url': '/legal/'},
        ]
        return context



def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    """Custom 404 page handler."""
    return render(request, 'errors/404.html', status=404)


def server_error(request: HttpRequest) -> HttpResponse:
    """Custom 500 page handler."""
    return render(request, 'errors/500.html', status=500)


def permission_denied(request: HttpRequest, exception: Exception) -> HttpResponse:
    """Custom 403 page handler."""
    return render(request, 'errors/403.html', status=403)