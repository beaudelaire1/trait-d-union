"""Smoke tests for all public pages.

Ensures every public URL returns HTTP 200 and renders its expected template.
These are the most critical tests — a single broken page costs SEO and conversions.
"""
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestPublicPages:
    """Every public URL should return 200."""

    PUBLIC_URLS = [
        ('pages:home', 200),
        ('pages:services', 200),
        ('pages:method', 200),
        ('pages:legal', 200),
        ('leads:contact', 200),
    ]

    @pytest.mark.parametrize('url_name,expected_status', PUBLIC_URLS)
    def test_public_page_status(self, client, url_name, expected_status):
        """Each public page must return its expected status code."""
        url = reverse(url_name)
        response = client.get(url)
        assert response.status_code == expected_status, (
            f"{url_name} returned {response.status_code} instead of {expected_status}"
        )

    def test_home_contains_h1(self, client):
        """Homepage must have an <h1> (SEO requirement)."""
        response = client.get(reverse('pages:home'))
        assert b'<h1' in response.content

    def test_home_template(self, client):
        """homepage uses correct template."""
        response = client.get(reverse('pages:home'))
        assert 'pages/home.html' in [t.name for t in response.templates]

    def test_services_template(self, client):
        response = client.get(reverse('pages:services'))
        assert 'pages/services.html' in [t.name for t in response.templates]

    def test_method_template(self, client):
        response = client.get(reverse('pages:method'))
        assert 'pages/method.html' in [t.name for t in response.templates]


@pytest.mark.django_db
class TestSEOEndpoints:
    """Verify SEO-critical endpoints."""

    def test_robots_txt(self, client):
        response = client.get('/robots.txt')
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/plain'
        assert b'Sitemap' in response.content

    def test_sitemap_xml(self, client):
        response = client.get('/sitemap.xml')
        assert response.status_code == 200
        assert 'xml' in response['Content-Type']

    def test_healthz(self, client):
        response = client.get('/healthz/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestMetaTags:
    """Verify SEO meta tags on key pages."""

    def test_home_has_title(self, client):
        response = client.get(reverse('pages:home'))
        assert b'<title>' in response.content

    def test_home_has_meta_description(self, client):
        response = client.get(reverse('pages:home'))
        assert b'meta name="description"' in response.content

    def test_home_has_canonical(self, client):
        response = client.get(reverse('pages:home'))
        assert b'rel="canonical"' in response.content

    def test_home_has_og_tags(self, client):
        response = client.get(reverse('pages:home'))
        content = response.content
        assert b'og:title' in content
        assert b'og:description' in content
        assert b'og:image' in content

    def test_contact_has_title(self, client):
        response = client.get(reverse('leads:contact'))
        assert b'<title>' in response.content
