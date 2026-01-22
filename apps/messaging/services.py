import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
import requests
import json

from .models import Prospect, ProspectMessage, EmailTemplate

logger = logging.getLogger(__name__)

def send_email_brevo(to_email, subject, html_content, to_name=None, sender=None):
    """
    Send email using Brevo (Sendinblue) API directly or via Django SMTP.
    Prefers Django's configured email backend if available.
    """
    try:
        # 1. Try Standard Django send_mail
        # This will use whatever backend is configured in settings.py (SMTP, Console, Anymail)
        send_mail(
            subject=subject,
            message="",  # Plain text version (optional, could strip tags)
            from_email=sender or settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=html_content,
            fail_silently=False,
        )
        
        return {
            'success': True,
            'message_id': f"local-{timezone.now().timestamp()}"
        }
        
    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}")
        return {
            'success': False, 
            'error': str(e)
        }

def send_prospection_template(prospect, template_slug='prospection-standard'):
    """
    Send a specific template to a prospect.
    """
    try:
        template = EmailTemplate.objects.filter(slug=template_slug).first()
        if not template:
            return {'success': False, 'error': f"Template {template_slug} not found"}
            
        # Render template context
        context = {
            'prospect': prospect,
            'contact_name': prospect.contact_name,
            'company_name': prospect.company_name,
        }
        
        # If template is stored as database content
        # We might need to render the liquid/django tags inside the content
        # For simplicity, let's assume content is just HTML string
        content = template.content
        subject = template.subject
        
        # Simple string replacement for basic personalization
        subject = subject.replace('{{ name }}', prospect.contact_name)
        subject = subject.replace('{{ company }}', prospect.company_name)
        
        content = content.replace('{{ name }}', prospect.contact_name)
        content = content.replace('{{ company }}', prospect.company_name)
        
        return send_email_brevo(
            to_email=prospect.email,
            subject=subject,
            html_content=content,
            to_name=prospect.contact_name
        )
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def send_prospect_email(prospect, subject, content):
    """Legacy wrapper."""
    return send_email_brevo(prospect.email, subject, content, prospect.contact_name)
