"""Tests : conversion lead → client (fiche contact + profil portail)."""
import pytest
from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage

from apps.leads.models import Lead, LeadStatus, ProjectTypeChoice
from apps.leads.admin import LeadAdmin
from apps.clients.models import ClientProfile


def _make_admin_request(admin_user):
    """Fabrique une requête POST avec messages middleware."""
    factory = RequestFactory()
    request = factory.post("/admin/leads/lead/")
    request.user = admin_user
    # Django admin nécessite le storage messages
    setattr(request, "session", "session")
    messages = FallbackStorage(request)
    setattr(request, "_messages", messages)
    return request


@pytest.mark.django_db
class TestLeadConversion:
    """Vérifie que l'action 'Convertir en client' crée bien les deux modèles."""

    @patch("core.tasks.async_send_welcome_email")
    def test_conversion_creates_client_profile(self, mock_email, admin_user):
        """La conversion doit créer un ClientProfile avec compte portail."""
        lead = Lead.objects.create(
            name="Alice Dupont",
            email="alice@example.com",
            project_type=ProjectTypeChoice.SITE,
            message="Je veux un site.",
        )

        admin_instance = LeadAdmin(model=Lead, admin_site=AdminSite())
        request = _make_admin_request(admin_user)

        admin_instance.action_convert_to_client(request, Lead.objects.filter(pk=lead.pk))

        lead.refresh_from_db()
        assert lead.status == LeadStatus.CONVERTED
        assert lead.converted_to_client is not None

        # ClientProfile créé
        profile = lead.converted_to_client
        assert isinstance(profile, ClientProfile)
        assert profile.user.email == "alice@example.com"
        assert profile.full_name == "Alice Dupont"

    @patch("core.tasks.async_send_welcome_email")
    def test_conversion_reuses_existing_user(self, mock_email, admin_user):
        """Si un User existe déjà (même email), il est réutilisé."""
        from django.contrib.auth.models import User as AuthUser
        existing_user = AuthUser.objects.create_user(
            username="alice", email="alice@example.com", password="pass"
        )
        ClientProfile.objects.create(
            user=existing_user, full_name="Alice D.", email="alice@example.com",
        )
        lead = Lead.objects.create(
            name="Alice Dupont",
            email="alice@example.com",
            project_type=ProjectTypeChoice.COMMERCE,
            message="Besoin d'un e-commerce.",
        )

        admin_instance = LeadAdmin(model=Lead, admin_site=AdminSite())
        request = _make_admin_request(admin_user)

        admin_instance.action_convert_to_client(request, Lead.objects.filter(pk=lead.pk))

        lead.refresh_from_db()
        assert lead.status == LeadStatus.CONVERTED
        # Pas de doublon utilisateur
        assert AuthUser.objects.filter(email__iexact="alice@example.com").count() == 1

    @patch("core.tasks.async_send_welcome_email")
    def test_conversion_skips_already_converted(self, mock_email, admin_user):
        """Un lead déjà converti est ignoré (pas de doublon)."""
        user = User.objects.create_user(
            username="alice", email="alice@example.com", password="pass"
        )
        profile = ClientProfile.objects.create(user=user)

        lead = Lead.objects.create(
            name="Alice Dupont",
            email="alice@example.com",
            project_type=ProjectTypeChoice.SITE,
            message="Test",
            status=LeadStatus.CONVERTED,
            converted_to_client=profile,
        )

        admin_instance = LeadAdmin(model=Lead, admin_site=AdminSite())
        request = _make_admin_request(admin_user)

        admin_instance.action_convert_to_client(request, Lead.objects.filter(pk=lead.pk))

        # Pas de nouveau User créé
        assert User.objects.filter(email="alice@example.com").count() == 1
