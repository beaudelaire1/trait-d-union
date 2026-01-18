"""Services related to leads, such as sending emails."""
from __future__ import annotations

import os
import logging

from django.conf import settings
from django.template.loader import render_to_string

from .models import Lead

logger = logging.getLogger(__name__)


def _send_email(to_email: str, subject: str, message: str, html_body: str = None) -> bool:
    """
    Envoie un email via Brevo ou fallback Django.
    
    Args:
        to_email: Destinataire
        subject: Sujet de l'email
        message: Corps texte brut (fallback)
        html_body: Corps HTML optionnel (template premium TUS)
    """
    try:
        from core.services.email_backends import send_simple_email, brevo_service
        
        if html_body and brevo_service.is_configured():
            # Utiliser l'API Brevo avec HTML
            from core.services.email_backends import send_transactional_email
            
            result = send_transactional_email(
                to_email=to_email,
                subject=subject,
                html_content=html_body,
                tags=['lead', 'contact']
            )
            return result.get('success', False)
        
        # Fallback sur send_simple_email
        return send_simple_email(to_email=to_email, subject=subject, text_body=message, html_body=html_body)
    except ImportError:
        # Fallback si le module n'existe pas
        from django.core.mail import send_mail
        return send_mail(subject, message, None, [to_email]) > 0


class EmailService:
    """Service class responsible for sending emails on lead creation."""

    @staticmethod
    def send_confirmation_email(lead: Lead) -> bool:
        """Send a confirmation email to the prospect with a summary of their request."""
        subject = "Merci de votre demande – Trait d'Union Studio"
        message = (
            f"Bonjour {lead.name},\n\n"
            "Nous avons bien reçu votre demande concernant un projet de type "
            f"{lead.get_project_type_display()}. Nous reviendrons vers vous rapidement pour discuter des détails.\n\n"
            "Résumé de votre message :\n"
            f"{lead.message}\n\n"
            "L'équipe Trait d'Union Studio"
        )
        
        # Template HTML premium TUS
        html_body = render_to_string(
            'emails/notification_generic.html',
            {
                'headline': 'Confirmation de votre demande',
                'intro': f"Bonjour {lead.name},\n\nNous avons bien reçu votre demande concernant un projet de type {lead.get_project_type_display()}. Notre équipe reviendra vers vous dans les plus brefs délais.",
                'rows': [
                    {'label': 'Type de projet', 'value': lead.get_project_type_display()},
                    {'label': 'Budget estimé', 'value': lead.get_budget_display() or 'Non spécifié'},
                ],
                'action_url': getattr(settings, 'SITE_URL', 'https://traitdunion.it'),
                'action_label': 'Visiter notre site',
            },
        )
        
        return _send_email(lead.email, subject, message, html_body)

    @staticmethod
    def send_admin_notification(lead: Lead) -> bool:
        """Notify the site administrator of a new lead."""
        subject = f'🔔 Nouveau lead : {lead.name}'
        message = (
            f"Nom : {lead.name}\n"
            f"Email : {lead.email}\n"
            f"Type de projet : {lead.get_project_type_display()}\n"
            f"Budget : {lead.get_budget_display() or 'Non spécifié'}\n"
            f"Message :\n{lead.message}\n"
            f"URL existante : {lead.existing_url or '—'}\n"
            f"IP : {lead.ip_address or '—'}\n"
        )
        
        # Template HTML premium TUS pour l'admin
        branding = getattr(settings, 'INVOICE_BRANDING', {})
        site_url = getattr(settings, 'SITE_URL', 'https://traitdunion.it').rstrip('/')
        
        html_body = render_to_string(
            'emails/notification_generic.html',
            {
                'brand': branding.get('name', "Trait d'Union Studio"),
                'headline': '🔔 Nouveau contact reçu',
                'title': 'Notification Admin',
                'intro': f"Un nouveau prospect vient de vous contacter via le formulaire du site.",
                'rows': [
                    {'label': 'Nom', 'value': lead.name},
                    {'label': 'Email', 'value': lead.email},
                    {'label': 'Type de projet', 'value': lead.get_project_type_display()},
                    {'label': 'Budget', 'value': lead.get_budget_display() or 'Non spécifié'},
                    {'label': 'Message', 'value': lead.message[:200] + '...' if len(lead.message) > 200 else lead.message},
                    {'label': 'URL existante', 'value': lead.existing_url or '—'},
                    {'label': 'IP', 'value': lead.ip_address or '—'},
                ],
                'action_url': f"{site_url}/admin/leads/lead/{lead.pk}/change/",
                'action_label': 'Voir dans l\'admin',
                'reference': f"LEAD-{lead.pk}",
            },
        )
        
        # Utiliser ADMIN_EMAIL ou TASK_NOTIFICATION_EMAIL
        admin_email = (
            os.environ.get('TASK_NOTIFICATION_EMAIL') or
            os.environ.get('ADMIN_EMAIL') or 
            getattr(settings, 'ADMIN_EMAIL', 'contact@traitdunion.it')
        )
        
        return _send_email(admin_email, subject, message, html_body)
