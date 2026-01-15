"""Sitemap configuration for SEO optimization."""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.portfolio.models import Project


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
    
    def priority(self, item):
        if item == 'pages:home':
            return 1.0
        elif item in ('pages:services', 'leads:contact'):
            return 0.9
        elif item == 'pages:method':
            return 0.8
        return 0.5


class PortfolioSitemap(Sitemap):
    """Sitemap for portfolio projects."""
    
    changefreq = 'weekly'
    priority = 0.8
    
    def items(self):
        return Project.objects.filter(is_published=True)
    
    def lastmod(self, obj):
        return obj.updated_at
