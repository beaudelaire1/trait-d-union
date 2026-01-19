"""View definitions for the leads (contact form) app."""
from __future__ import annotations

import logging
from typing import Any

import requests
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import FormView, TemplateView

from .forms import ContactForm, DynamicFieldsForm
from .models import Lead
from .services import EmailService

logger = logging.getLogger(__name__)


def verify_recaptcha(token: str, remote_ip: str = '', expected_action: str = 'contact') -> tuple[bool, float]:
    """Vérifie le token reCAPTCHA v3 auprès de Google.
    
    Args:
        token: Le token reCAPTCHA généré côté client
        remote_ip: L'adresse IP du client (optionnel)
        expected_action: L'action attendue pour la vérification (défaut: 'contact')
    
    Returns:
        tuple: (is_valid, score) - Le score va de 0.0 (bot) à 1.0 (humain)
    """
    secret_key = getattr(settings, 'RECAPTCHA_SECRET_KEY', '')
    
    # Si pas de clé secrète configurée, on passe (mode développement)
    if not secret_key:
        logger.debug("reCAPTCHA: Pas de clé secrète configurée, vérification ignorée")
        return True, 1.0
    
    # Si pas de token mais clé configurée, c'est un problème
    if not token:
        logger.warning("reCAPTCHA: Token manquant alors que la clé secrète est configurée")
        # On laisse passer pour ne pas bloquer si le JS n'a pas chargé
        return True, 1.0
    
    try:
        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': secret_key,
                'response': token,
                'remoteip': remote_ip,
            },
            timeout=5,
        )
        result = response.json()
        
        logger.debug(f"reCAPTCHA response: success={result.get('success')}, "
                    f"score={result.get('score')}, action={result.get('action')}, "
                    f"hostname={result.get('hostname')}")
        
        if not result.get('success'):
            error_codes = result.get('error-codes', [])
            logger.warning(f"reCAPTCHA verification failed: {error_codes}")
            # En cas d'erreur de configuration (clés invalides), on laisse passer
            # pour ne pas bloquer les utilisateurs légitimes
            if 'invalid-input-secret' in error_codes or 'bad-request' in error_codes:
                logger.error("reCAPTCHA: Clé secrète invalide ou requête malformée - vérifiez la configuration")
                return True, 1.0
            return False, 0.0
        
        # Vérifier l'action pour plus de sécurité
        action = result.get('action', '')
        if action and action != expected_action:
            logger.warning(f"reCAPTCHA: Action inattendue '{action}', attendue '{expected_action}'")
            return False, 0.0
        
        score = result.get('score', 0.0)
        threshold = getattr(settings, 'RECAPTCHA_SCORE_THRESHOLD', 0.5)
        is_valid = score >= threshold
        
        if not is_valid:
            logger.info(f"reCAPTCHA: Score {score} inférieur au seuil {threshold}")
        
        return is_valid, score
        
    except requests.RequestException as e:
        logger.error(f"reCAPTCHA API error: {e}")
        # En cas d'erreur réseau, on laisse passer pour ne pas bloquer les utilisateurs
        return True, 1.0


class ContactView(FormView):
    """Main contact form view."""

    template_name: str = 'leads/contact.html'
    form_class = ContactForm
    success_url: str = '/contact/success/'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['recaptcha_site_key'] = getattr(settings, 'RECAPTCHA_SITE_KEY', '')
        return context

    def form_valid(self, form: ContactForm) -> HttpResponse:
        # Vérifier reCAPTCHA
        recaptcha_token = self.request.POST.get('g-recaptcha-response', '')
        is_valid, score = verify_recaptcha(
            token=recaptcha_token,
            remote_ip=self.get_client_ip(),
            expected_action='contact'
        )
        
        if not is_valid:
            logger.warning(f"reCAPTCHA rejected submission with score: {score}")
            form.add_error(None, "La vérification de sécurité a échoué. Veuillez réessayer.")
            return self.form_invalid(form)
        
        # Save lead
        lead: Lead = form.save(commit=False)
        lead.ip_address = self.get_client_ip()
        lead.save()
        # Send emails
        EmailService.send_confirmation_email(lead)
        EmailService.send_admin_notification(lead)
        return redirect(self.success_url)

    def get_client_ip(self) -> str:
        # Simplistic IP extraction; may need improvements behind proxy
        ip = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if ip:
            return ip.split(',')[0]
        return self.request.META.get('REMOTE_ADDR', '') or ''


class DynamicFieldsView(View):
    """Endpoint used by HTMX to load additional form fields."""

    def get(self, request: HttpRequest) -> HttpResponse:
        project_type = request.GET.get('type')
        # Here you would decide which extra fields to return based on project_type
        form = DynamicFieldsForm(initial={'project_type': project_type})
        return render(request, 'leads/dynamic_fields.html', {'form': form})


class ContactSuccessView(TemplateView):
    """Simple success page after the contact form is submitted."""

    template_name: str = 'leads/success.html'