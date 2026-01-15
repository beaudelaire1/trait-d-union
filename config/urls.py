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
    path('admin/', admin.site.urls),
    path('', include('apps.pages.urls')),
    path('portfolio/', include('apps.portfolio.urls')),
    path('contact/', include('apps.leads.urls')),
    path('resources/', include('apps.resources.urls')),
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