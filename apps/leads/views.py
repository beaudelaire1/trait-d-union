"""View definitions for the leads (contact form) app."""
from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.decorators.http import require_http_methods
from django.views.generic import FormView, TemplateView

from core.services.captcha import verify_recaptcha as core_verify_recaptcha
from core.services.captcha import verify_turnstile as core_verify_turnstile
from core.utils import get_client_ip
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
        context['breadcrumbs_list'] = [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'Contact', 'url': '/contact/'},
        ]
        return context

    def form_valid(self, form: ContactForm) -> HttpResponse:
        remote_ip = self.get_client_ip()

        # 🛡️ HONEYPOT CHECK - Silent rejection for bots
        honeypot_value = form.cleaned_data.get('honeypot', '')
        if honeypot_value:
            # Bot detected - return fake success to avoid alerting the bot
            logger.warning(
                "Honeypot triggered - Bot detected from IP %s with value: %s",
                remote_ip, honeypot_value[:50]
            )
            # Return success page without saving or sending emails
            return redirect(self.success_url)

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
        return get_client_ip(self.request)


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


# ==============================================================================
# NEWSLETTER / EMAIL CAPTURE
# ==============================================================================

@require_http_methods(["POST"])
def newsletter_subscribe(request: HttpRequest) -> HttpResponse:
    """HTMX endpoint pour l'inscription newsletter.

    Accepte un email + source, retourne un fragment HTML de confirmation.
    Rate-limité à 5 inscriptions/heure par IP.
    """
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError as DjangoValidationError
    from django.core.cache import cache as _cache
    from .models import EmailSubscriber

    # Rate limit
    ip = get_client_ip(request)
    cache_key = f"ratelimit:newsletter:{ip}"
    try:
        count = _cache.get(cache_key, 0)
        if count >= 5:
            return HttpResponse(
                '<p class="text-amber-400 text-sm">Trop de tentatives. Réessayez plus tard.</p>',
                status=429,
            )
        try:
            _cache.incr(cache_key)
        except ValueError:
            _cache.set(cache_key, 1, 3600)
    except Exception:
        pass

    email = request.POST.get('email', '').strip().lower()
    source = request.POST.get('source', 'footer')
    source_detail = request.POST.get('source_detail', '')[:200]

    # Validate
    if not email:
        return HttpResponse(
            '<p class="text-red-400 text-sm">Veuillez saisir votre email.</p>',
            status=400,
        )
    try:
        validate_email(email)
    except DjangoValidationError:
        return HttpResponse(
            '<p class="text-red-400 text-sm">Email invalide.</p>',
            status=400,
        )

    # Create or update
    subscriber, created = EmailSubscriber.objects.get_or_create(
        email=email,
        defaults={
            'source': source,
            'source_detail': source_detail,
        },
    )

    if not created and not subscriber.is_active:
        subscriber.is_active = True
        subscriber.save(update_fields=['is_active'])

    return HttpResponse(
        '<p class="text-tus-green text-sm font-medium">'
        '✓ Bienvenue ! Vous recevrez nos prochains contenus.'
        '</p>'
    )


@require_http_methods(["GET"])
def newsletter_unsubscribe(request: HttpRequest) -> HttpResponse:
    """Page de désinscription newsletter (lien signé dans chaque email).

    Usage : /contact/newsletter/unsubscribe/?email=xxx@yyy.com&token=xxx
    Le token est un HMAC-SHA256 de l'email signé avec SECRET_KEY.
    """
    from django.conf import settings as _settings
    from .models import EmailSubscriber
    import hashlib
    import hmac

    email = request.GET.get('email', '').strip().lower()
    token = request.GET.get('token', '')
    valid = False

    if email and token:
        expected = hmac.new(
            _settings.SECRET_KEY.encode(), email.encode(), hashlib.sha256,
        ).hexdigest()[:32]
        valid = hmac.compare_digest(token, expected)

    if valid:
        EmailSubscriber.objects.filter(email=email).update(is_active=False)

    return render(request, 'leads/newsletter_unsubscribe.html', {
        'email': email if valid else '',
        'invalid_token': bool(email and not valid),
    })
