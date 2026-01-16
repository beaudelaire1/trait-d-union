"""Root URL configuration for TUS website."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.views.generic import TemplateView

from config.sitemaps import StaticViewSitemap, PortfolioSitemap


# Sitemap configuration
sitemaps = {
    'static': StaticViewSitemap,
    'portfolio': PortfolioSitemap,
}

urlpatterns = [
    # Dashboard BI (Phase 5)
    path('tus-gestion-secure/dashboard/', include('apps.pages.dashboard_urls')),
    path('tus-gestion-secure/', admin.site.urls),  # URL admin sécurisée
    path('', include('apps.pages.urls')),
    path('portfolio/', include('apps.portfolio.urls')),
    path('contact/', include('apps.leads.urls')),
    path('resources/', include('apps.resources.urls')),
    # Business apps
    path('devis/', include('apps.devis.urls')),
    path('factures/', include('apps.factures.urls')),
    # Client portal (Phase 4)
    path('espace-client/', include('apps.clients.urls')),
    path('accounts/', include('allauth.urls')),
    # SEO
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain'), name='robots'),
]

# Servir les fichiers statiques et média en développement
if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Error handlers
handler404 = 'apps.pages.views.page_not_found'
handler500 = 'apps.pages.views.server_error'