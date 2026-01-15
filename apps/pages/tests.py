"""Tests for the pages app."""
from django.test import TestCase, Client
from django.urls import reverse


class HomeViewTest(TestCase):
    """Test the home page view."""

    def test_home_page_loads(self):
        """Test that the home page loads successfully."""
        response = self.client.get(reverse('pages:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/home.html')

    def test_home_page_contains_cta(self):
        """Test that home page contains call-to-action links."""
        response = self.client.get(reverse('pages:home'))
        self.assertContains(response, 'contact')


class ServicesViewTest(TestCase):
    """Test the services page view."""

    def test_services_page_loads(self):
        """Test that the services page loads successfully."""
        response = self.client.get(reverse('pages:services'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/services.html')

    def test_services_page_contains_offerings(self):
        """Test that services page contains service offerings."""
        response = self.client.get(reverse('pages:services'))
        self.assertContains(response, 'Site Vitrine')
        self.assertContains(response, 'E-commerce')
        self.assertContains(response, 'Plateforme')


class MethodViewTest(TestCase):
    """Test the method page view."""

    def test_method_page_loads(self):
        """Test that the method page loads successfully."""
        response = self.client.get(reverse('pages:method'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/method.html')

    def test_method_page_contains_steps(self):
        """Test that method page contains process steps."""
        response = self.client.get(reverse('pages:method'))
        self.assertContains(response, 'Découverte')
        self.assertContains(response, 'Stratégie')
        self.assertContains(response, 'Design')


class LegalViewTest(TestCase):
    """Test the legal page view."""

    def test_legal_page_loads(self):
        """Test that the legal page loads successfully."""
        response = self.client.get(reverse('pages:legal'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/legal.html')

    def test_legal_page_contains_sections(self):
        """Test that legal page contains required sections."""
        response = self.client.get(reverse('pages:legal'))
        self.assertContains(response, 'Éditeur')
        self.assertContains(response, 'Protection des données')


class ErrorPagesTest(TestCase):
    """Test custom error pages."""

    def test_404_page(self):
        """Test that 404 errors show custom page."""
        response = self.client.get('/nonexistent-page-xyz/')
        self.assertEqual(response.status_code, 404)
