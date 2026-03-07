"""Root URL configuration for TUS website."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include, URLPattern, URLResolver
from django.views.generic import TemplateView


def _staff_protected_include(module):
    """Wrap all views from an included module with staff_member_required."""
    result = include(module)
    # include() may return a 2-tuple (urlpatterns, app_ns) or 3-tuple
    if len(result) == 3:
        url_patterns, app_ns, inst_ns = result
    else:
        url_patterns, app_ns = result
        inst_ns = app_ns
    # url_patterns may be a module with a .urlpatterns attribute
    if hasattr(url_patterns, 'urlpatterns'):
        url_patterns = url_patterns.urlpatterns
    for pattern in url_patterns:
        if isinstance(pattern, URLPattern) and pattern.callback:
            pattern.callback = staff_member_required(pattern.callback)
    return url_patterns, app_ns, inst_ns

# 🛡️ SECURITY: OTP-protected admin site (2FA required for all staff)
from django_otp.admin import OTPAdminSite


class TUSOTPAdminSite(OTPAdminSite):
    """OTPAdminSite with TOTP QR code URL injected into login context."""

    def login(self, request, extra_context=None):
        from django.urls import reverse
        extra_context = extra_context or {}
        extra_context['totp_qr_url'] = reverse('admin_totp_qr')
        return super().login(request, extra_context)


admin.site.__class__ = TUSOTPAdminSite

from config.sitemaps import StaticViewSitemap, PortfolioSitemap, ChroniquesSitemap
from apps.pages.healthz import healthz
from core.views_totp import totp_qr_code
from core.views_session import session_ping


# Sitemap configuration
sitemaps = {
    'static': StaticViewSitemap,
    'portfolio': PortfolioSitemap,
    'chroniques': ChroniquesSitemap,
}

urlpatterns = [
    # Dashboard BI (Phase 5)
    path('tus-gestion-secure/dashboard/', include('apps.pages.dashboard_urls')),
    path('tus-gestion-secure/messaging/', include('apps.messaging.urls', namespace='messaging')),
    path('tus-gestion-secure/emails/', include('apps.leads.email_urls', namespace='admin_emails')),
    # 🛡️ TOTP QR code endpoint (credentials required via POST)
    path('tus-gestion-secure/totp-qr/', totp_qr_code, name='admin_totp_qr'),
    # 🛡️ Session keep-alive (heartbeat JS in admin calls this every few minutes)
    path('tus-gestion-secure/session-ping/', session_ping, name='session_ping'),
    path('tus-gestion-secure/', admin.site.urls),  # URL admin sécurisée
    path('', include('apps.pages.urls')),
    path('simulateur/', include('apps.simulateur.urls')),
    path('nos-signatures/', include('apps.portfolio.urls')),
    path('contact/', include('apps.leads.urls')),
    path('resources/', include('apps.resources.urls')),
    path('chroniques/', include('apps.chroniques.urls')),
    # Business apps
    path('devis/', include('apps.devis.urls')),
    path('factures/', include('apps.factures.urls')),
    # Client portal (Phase 4)
    path('ecosysteme-tus/', include('apps.clients.urls')),
    path('accounts/', include('allauth.urls')),
    # TinyMCE — 🛡️ SECURITY: restricted to authenticated staff only
    path('tinymce/', _staff_protected_include('tinymce.urls')),
    # SEO
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain'), name='robots'),
    # Health check (Docker + uptime monitoring)
    path('healthz/', healthz, name='healthz'),
]

# Servir les fichiers statiques et média en développement
if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Error handlers
handler403 = 'apps.pages.views.permission_denied'
handler404 = 'apps.pages.views.page_not_found'
handler500 = 'apps.pages.views.server_error'