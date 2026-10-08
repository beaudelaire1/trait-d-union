from __future__ import annotations

import re

from django import forms
from django.conf import settings

from allauth.account.forms import LoginForm
from django_otp.admin import OTPAdminAuthenticationForm
from django_otp.plugins.otp_totp.models import TOTPDevice

from core.services.captcha import verify_recaptcha, verify_turnstile


# 🛡️ SECURITY: Single source of truth (DRY)
from core.utils import get_client_ip as _get_client_ip


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


class TUSOTPAdminAuthenticationForm(OTPAdminAuthenticationForm):
    """Admin OTP form compatible with django-otp's explicit device selection.

    Recent django-otp versions require an explicit OTP device. On the first
    login submission our template cannot render that selector yet because the
    user has not been authenticated by password. If the user has exactly one
    confirmed TOTP device, select it directly instead of rejecting a perfectly
    valid authenticator code and forcing a second submission.

    If several TOTP devices exist, keep django-otp's secure default and require
    an explicit device choice.
    """

    def clean_otp_token(self):
        # Authenticator apps display "123 456" and copy-paste keeps the space,
        # which django-otp's int() parsing rejects as an invalid token.
        return re.sub(r"\s+", "", self.cleaned_data.get("otp_token") or "")

    def _chosen_device(self, user):
        device = super()._chosen_device(user)
        if device is not None:
            return device

        devices = list(
            TOTPDevice.objects.filter(user=user, confirmed=True)
            .select_for_update()
            .order_by("pk")[:2]
        )
        return devices[0] if len(devices) == 1 else None
