"""Root URL configuration for TUS website."""
from types import SimpleNamespace

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.sitemaps.views import x_robots_tag, _get_latest_lastmod
from django.core.paginator import EmptyPage, PageNotAnInteger
from django.http import Http404
from django.template.response import TemplateResponse
from django.urls import path, include, URLPattern, URLResolver
from django.utils.http import http_date
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


def canonical_sitemap_view(request):
    """Serve sitemap with canonical host to avoid indexing redirecting URLs."""
    return _canonical_sitemap(request, sitemaps=sitemaps)


@x_robots_tag
def _canonical_sitemap(
    request,
    sitemaps,
    section=None,
    template_name='sitemap.xml',
    content_type='application/xml',
):
    req_protocol = request.scheme
    canonical_domain = getattr(settings, 'CANONICAL_DOMAIN', '') or request.get_host().split(':')[0]
    req_site = SimpleNamespace(domain=canonical_domain, name='Trait d\'Union Studio')

    if section is not None:
        if section not in sitemaps:
            raise Http404("No sitemap available for section: %r" % section)
        maps = [sitemaps[section]]
    else:
        maps = sitemaps.values()

    page = request.GET.get('p', 1)

    lastmod = None
    all_sites_lastmod = True
    urls = []
    for site in maps:
        try:
            if callable(site):
                site = site()
            urls.extend(site.get_urls(page=page, site=req_site, protocol=req_protocol))
            if all_sites_lastmod:
                site_lastmod = getattr(site, 'latest_lastmod', None)
                if site_lastmod is not None:
                    lastmod = _get_latest_lastmod(lastmod, site_lastmod)
                else:
                    all_sites_lastmod = False
        except EmptyPage:
            raise Http404('Page %s empty' % page)
        except PageNotAnInteger:
            raise Http404("No page '%s'" % page)

    headers = {'Last-Modified': http_date(lastmod.timestamp())} if (all_sites_lastmod and lastmod) else None
    return TemplateResponse(
        request,
        template_name,
        {'urlset': urls},
        content_type=content_type,
        headers=headers,
    )

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
    path('sitemap.xml', canonical_sitemap_view, name='sitemap'),
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