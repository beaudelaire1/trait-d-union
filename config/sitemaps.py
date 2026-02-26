"""Sitemap configuration for SEO optimization."""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timezone

from apps.portfolio.models import Project
from apps.chroniques.models import Article

# Date de dernière mise à jour significative du site (à mettre à jour manuellement lors de changements majeurs)
_SITE_LAST_MODIFIED = datetime(2026, 2, 25, tzinfo=timezone.utc)


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages."""
    
    priority = 0.5
    changefreq = 'monthly'
    
    def items(self):
        return [
            'pages:home',
            'pages:services',
            'pages:method',
            'pages:legal',
            'leads:contact',
            'resources:index',
        ]
    
    def location(self, item):
        return reverse(item)
    
    def lastmod(self, item):
        """Return the last modification date for static pages."""
        return _SITE_LAST_MODIFIED
    
    def priority(self, item):
        # Priorité maximale pour pages stratégiques SEO Guyane/Outre-Mer
        if item == 'pages:home':
            return 1.0
        elif item in ('pages:services', 'leads:contact'):
            return 0.95  # Augmenté pour conversion
        elif item == 'pages:method':
            return 0.85  # Augmenté pour différenciation
        return 0.5


class PortfolioSitemap(Sitemap):
    """Sitemap for portfolio projects."""
    
    changefreq = 'weekly'
    priority = 0.8
    
    def items(self):
        return Project.objects.filter(is_published=True)
    
    def lastmod(self, obj):
        return obj.updated_at


class ChroniquesSitemap(Sitemap):
    """Sitemap for blog articles (Chroniques TUS)."""
    
    changefreq = 'weekly'
    priority = 0.7
    
    def items(self):
        return Article.objects.filter(is_published=True)
    
    def lastmod(self, obj):
        return obj.updated_at
