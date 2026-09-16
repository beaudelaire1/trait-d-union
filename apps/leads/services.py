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
        """Envoie au prospect un accusé de réception réellement exploitable."""
        reference = f"LEAD-{lead.pk}"
        project_type = lead.get_project_type_display()
        budget = lead.get_budget_display() or 'Non spécifié'
        site_url = str(getattr(settings, 'SITE_URL', 'https://traitdunion.studio')).rstrip('/')

        subject = f"Merci de votre demande — {project_type} | Réf. {reference}"
        message = (
            f"Bonjour {lead.name},\n\n"
            f"Votre demande concernant « {project_type} » a bien été reçue. "
            "Nous reviendrons vers vous sous 24 à 48 heures ouvrées.\n\n"
            f"Référence : {reference}\n"
            f"Type de projet : {project_type}\n"
            f"Budget indiqué : {budget}\n"
            f"Téléphone : {lead.phone or 'Non renseigné'}\n"
            f"Site existant : {lead.existing_url or 'Non renseigné'}\n\n"
            "Votre message :\n"
            f"{lead.message}\n\n"
            "Si vous souhaitez ajouter une précision avant notre retour, vous pouvez répondre directement à cet email.\n\n"
            "Trait d'Union Studio"
        )

        details = [
            {'label': 'Référence', 'value': reference},
            {'label': 'Type de projet', 'value': project_type},
            {'label': 'Budget estimé', 'value': budget},
        ]
        if lead.phone:
            details.append({'label': 'Téléphone', 'value': str(lead.phone)})
        if lead.existing_url:
            details.append({'label': 'Plateforme existante', 'value': lead.existing_url})
        details.append({'label': 'Votre message', 'value': lead.message})

        html_body = render_to_string(
            'emails/notification_generic.html',
            {
                'headline': 'Votre demande a bien été reçue',
                'preheader': (
                    f"Réf. {reference} — {project_type}. "
                    "Récapitulatif de votre demande et délai de réponse : 24 à 48 h ouvrées."
                ),
                'message': (
                    f"Bonjour <strong>{lead.name}</strong>,<br><br>"
                    "Nous avons bien reçu votre demande. Nous reviendrons vers vous "
                    "sous <strong>24 à 48 heures ouvrées</strong>.<br><br>"
                    "Vous trouverez ci-dessous les informations enregistrées. "
                    "Si une précision manque, répondez simplement à cet email."
                ),
                'details': details,
                'reference': reference,
                'cta_url': site_url,
                'cta_text': "Accéder à Trait d'Union Studio",
            },
        )

        return _send_email(lead.email, subject, message, html_body)

    @staticmethod
    def send_admin_notification(lead: Lead) -> bool:
        """Notify the site administrator of a new lead."""
        reference = f"LEAD-{lead.pk}"
        project_type = lead.get_project_type_display()
        subject = f"[TUS] Nouveau contact {reference} — {project_type} — {lead.name}"
        message = (
            f"Référence : {reference}\n"
            f"Nom : {lead.name}\n"
            f"Email : {lead.email}\n"
            f"Téléphone : {lead.phone or '—'}\n"
            f"Type de projet : {project_type}\n"
            f"Budget : {lead.get_budget_display() or 'Non spécifié'}\n"
            f"Message :\n{lead.message}\n"
            f"URL existante : {lead.existing_url or '—'}\n"
            f"Pièce jointe : {lead.attachment.name if lead.attachment else '—'}\n"
            f"IP : {lead.ip_address or '—'}\n"
        )

        branding = getattr(settings, 'INVOICE_BRANDING', {})
        site_url = getattr(settings, 'SITE_URL', 'https://traitdunion.studio').rstrip('/')

        rows = [
            {'label': 'Nom', 'value': lead.name},
            {'label': 'Email', 'value': lead.email},
            {'label': 'Téléphone', 'value': str(lead.phone) if lead.phone else '—'},
            {'label': 'Type de projet', 'value': project_type},
            {'label': 'Budget', 'value': lead.get_budget_display() or 'Non spécifié'},
            {'label': 'Message', 'value': lead.message},
            {'label': 'Plateforme existante', 'value': lead.existing_url or '—'},
            {'label': 'Pièce jointe', 'value': lead.attachment.name if lead.attachment else '—'},
            {'label': 'IP', 'value': lead.ip_address or '—'},
        ]

        html_body = render_to_string(
            'emails/notification_generic.html',
            {
                'brand': branding.get('name', "Trait d'Union Studio"),
                'headline': 'Nouveau contact reçu',
                'title': f'{reference} — {lead.name}',
                'preheader': f"{reference} — {lead.name} — {project_type} — {lead.email}",
                'intro': "Un nouveau prospect vient de soumettre le formulaire de contact.",
                'rows': rows,
                'action_url': f"{site_url}/tus-gestion-secure/leads/lead/{lead.pk}/change/",
                'action_label': "Ouvrir la fiche dans l'admin",
                'reference': reference,
            },
        )

        admin_email = (
            os.environ.get('TASK_NOTIFICATION_EMAIL') or
            os.environ.get('ADMIN_EMAIL') or
            getattr(settings, 'ADMIN_EMAIL', 'contact@traitdunion.studio')
        )

        return _send_email(admin_email, subject, message, html_body)
