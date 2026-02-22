from __future__ import annotations

from django import forms
from django.conf import settings

from allauth.account.forms import LoginForm

from core.services.captcha import verify_recaptcha, verify_turnstile


def _get_client_ip(request) -> str:
    if not request:
        return ''
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '') or ''


def _has_turnstile() -> bool:
    return bool(getattr(settings, 'TURNSTILE_SITE_KEY', '')) and bool(
        getattr(settings, 'TURNSTILE_SECRET_KEY', '')
    )


def _has_recaptcha() -> bool:
    return bool(getattr(settings, 'RECAPTCHA_SITE_KEY', '')) and bool(
        getattr(settings, 'RECAPTCHA_SECRET_KEY', '')
    )


class CaptchaLoginForm(LoginForm):
    def clean(self):
        cleaned_data = super().clean()
        if not self.request:
            return cleaned_data

        if not (_has_turnstile() or _has_recaptcha()):
            return cleaned_data

        remote_ip = _get_client_ip(self.request)
        turnstile_token = self.request.POST.get('cf-turnstile-response', '')
        recaptcha_token = self.request.POST.get('g-recaptcha-response', '')

        if turnstile_token:
            is_valid = verify_turnstile(token=turnstile_token, remote_ip=remote_ip)
        elif recaptcha_token:
            is_valid = verify_recaptcha(token=recaptcha_token, remote_ip=remote_ip)
        else:
            is_valid = False

        if not is_valid:
            raise forms.ValidationError(
                'La verification de securite a echoue. Veuillez reessayer.'
            )

        return cleaned_data
