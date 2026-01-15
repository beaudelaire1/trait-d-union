"""Services related to leads, such as sending emails."""
from __future__ import annotations

import os

from django.core.mail import send_mail

from .models import Lead


class EmailService:
    """Service class responsible for sending emails on lead creation."""

    @staticmethod
    def send_confirmation_email(lead: Lead) -> bool:
        """Send a confirmation email to the prospect with a summary of their request."""
        subject = 'Merci de votre demande – Trait d’Union Studio'
        message = (
            f"Bonjour {lead.name},\n\n"
            "Nous avons bien reçu votre demande concernant un projet de type "
            f"{lead.get_project_type_display()}. Nous reviendrons vers vous rapidement pour discuter des détails.\n\n"
            "Résumé de votre message :\n"
            f"{lead.message}\n\n"
            "L’équipe Trait d’Union Studio"
        )
        return send_mail(subject, message, None, [lead.email]) > 0

    @staticmethod
    def send_admin_notification(lead: Lead) -> bool:
        """Notify the site administrator of a new lead."""
        subject = f'Nouveau lead : {lead.name}'
        message = (
            f"Nom : {lead.name}\n"
            f"Email : {lead.email}\n"
            f"Type de projet : {lead.get_project_type_display()}\n"
            f"Budget : {lead.get_budget_display() or 'Non spécifié'}\n"
            f"Message :\n{lead.message}\n"
            f"URL existante : {lead.existing_url or '—'}\n"
            f"IP : {lead.ip_address or '—'}\n"
        )
        admin_email = os.environ.get('ADMIN_EMAIL', 'contact@traitdunion.it')
        return send_mail(subject, message, None, [admin_email]) > 0