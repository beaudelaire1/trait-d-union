"""View definitions for the leads (contact form) app."""
from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import FormView, TemplateView

from core.services.captcha import verify_recaptcha as core_verify_recaptcha
from core.services.captcha import verify_turnstile as core_verify_turnstile
from .forms import ContactForm, DynamicFieldsForm
from .models import Lead
from .services import EmailService

logger = logging.getLogger(__name__)


def verify_recaptcha(token: str, remote_ip: str = '') -> bool:
    """Proxy to shared reCAPTCHA verification helper."""
    return core_verify_recaptcha(token=token, remote_ip=remote_ip)


def verify_turnstile(token: str, remote_ip: str = '') -> bool:
    """Proxy to shared Turnstile verification helper."""
    return core_verify_turnstile(token=token, remote_ip=remote_ip)


class ContactView(FormView):
    """Main contact form view."""

    template_name: str = 'leads/contact.html'
    form_class = ContactForm
    success_url: str = '/contact/success/'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['turnstile_site_key'] = getattr(settings, 'TURNSTILE_SITE_KEY', '')
        context['recaptcha_site_key'] = getattr(settings, 'RECAPTCHA_SITE_KEY', '')
        context['turnstile_fallback_timeout_ms'] = int(
            getattr(settings, 'TURNSTILE_FALLBACK_TIMEOUT_MS', 2500)
        )
        return context

    def form_valid(self, form: ContactForm) -> HttpResponse:
        remote_ip = self.get_client_ip()

        # Turnstile en priorité, reCAPTCHA en fallback
        turnstile_token = self.request.POST.get('cf-turnstile-response', '')
        recaptcha_token = self.request.POST.get('g-recaptcha-response', '')

        if turnstile_token:
            is_valid = verify_turnstile(token=turnstile_token, remote_ip=remote_ip)
        elif recaptcha_token:
            is_valid = verify_recaptcha(token=recaptcha_token, remote_ip=remote_ip)
        else:
            # Aucun captcha n'est configuré → on laisse passer
            has_captcha = (
                getattr(settings, 'TURNSTILE_SITE_KEY', '')
                or getattr(settings, 'RECAPTCHA_SITE_KEY', '')
            )
            is_valid = not has_captcha
        
        if not is_valid:
            logger.warning("Captcha verification failed (turnstile=%s, recaptcha=%s)",
                           bool(turnstile_token), bool(recaptcha_token))
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