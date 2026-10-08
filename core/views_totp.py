"""Secure two-step TOTP enrolment for the staff administration.

A password alone must NEVER reveal the secret of an existing confirmed device.
New devices are unconfirmed until a freshly generated OTP has been verified.
Recovery of an existing factor requires an operator using the management command.
"""
import io
import logging
import re

from django.contrib.auth import authenticate, get_user_model, login as auth_login
from django.core.cache import cache
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django_otp import login as otp_login
from django_otp.plugins.otp_totp.models import TOTPDevice

from core.utils import get_client_ip

logger = logging.getLogger(__name__)
RATE_LIMIT = 10
RATE_WINDOW = 900
NO_STORE = 'no-store, no-cache, must-revalidate, max-age=0'


def _json(data, status=200):
    response = JsonResponse(data, status=status)
    response['Cache-Control'] = NO_STORE
    return response


def _authenticate_staff(request, operation):
    """Apply an IP limit before checking credentials, for both endpoints."""
    ip = get_client_ip(request)
    key = f'totp_enrol:{operation}:{ip}'
    # cache.add preserves the expiry window and increments atomically on Redis.
    cache.add(key, 0, RATE_WINDOW)
    try:
        attempts = cache.incr(key)
    except ValueError:
        cache.set(key, 1, RATE_WINDOW)
        attempts = 1
    if attempts > RATE_LIMIT:
        logger.warning('TOTP enrolment rate limited operation=%s ip=%s', operation, ip)
        return None, _json({'error': 'Trop de tentatives. Réessayez dans 15 minutes.'}, 429)

    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    if not username or not password:
        return None, _json({'error': 'Nom d’utilisateur et mot de passe requis.'}, 400)

    user = authenticate(request, username=username, password=password)
    if user is None or not user.is_active or not user.is_staff:
        logger.warning('TOTP enrolment credentials rejected operation=%s ip=%s', operation, ip)
        return None, _json({'error': 'Identifiants invalides.'}, 403)
    return user, None


@csrf_protect
@require_POST
def totp_qr_code(request):
    """Show a secret ONLY when the authenticated staff user has no active TOTP.

    Never redisplay a confirmed factor's secret at the login page. Only a
    deliberately reset (or not yet provisioned) account can enrol a factor.
    """
    user, error = _authenticate_staff(request, 'qr')
    if error is not None:
        return error

    try:
        with transaction.atomic():
            # Serialize QR requests and concurrent confirmations by user.
            get_user_model().objects.select_for_update().get(pk=user.pk)
            if TOTPDevice.objects.filter(user=user, confirmed=True).exists():
                return _json({
                    'error': (
                        'Un appareil d’authentification est déjà associé à ce compte. '
                        'Pour le remplacer si vous avez perdu l’accès, demandez une '
                        'réinitialisation depuis la console d’administration du serveur.'
                    )
                }, 409)

            device = TOTPDevice.objects.filter(
                user=user, confirmed=False
            ).order_by('-pk').first()
            if device is None:
                device = TOTPDevice.objects.create(
                    user=user,
                    name='Microsoft Authenticator (en attente)',
                    confirmed=False,
                    tolerance=1,
                )
                logger.info('TOTP enrolment initiated user_id=%s', user.pk)

        import qrcode
        from qrcode.image.pil import PilImage

        qr = qrcode.QRCode(box_size=8, border=2)
        qr.add_data(device.config_url)
        qr.make(fit=True)
        img = qr.make_image(
            fill_color='#0a0a0a',
            back_color='#ffffff',
            image_factory=PilImage,
        )
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        response = HttpResponse(buffer.getvalue(), content_type='image/png')
        response['Cache-Control'] = NO_STORE
        response['Pragma'] = 'no-cache'
        return response
    except Exception:
        logger.exception('TOTP enrolment QR failed user_id=%s', user.pk)
        return _json({'error': 'Impossible de générer le QR code.'}, 500)


@csrf_protect
@require_POST
def totp_verify_setup(request):
    """Confirm a pending device only after verifying its first TOTP code.

    Successful enrolment also creates a regular Django session verified through
    django-otp. No second use of the same code is required for the first login.
    """
    user, error = _authenticate_staff(request, 'verify')
    if error is not None:
        return error
    token = request.POST.get('token', '').strip()
    if not re.fullmatch(r'[0-9]{6}', token):
        return _json({'error': 'Saisissez les six chiffres du code Authenticator.'}, 400)

    try:
        with transaction.atomic():
            get_user_model().objects.select_for_update().get(pk=user.pk)
            if TOTPDevice.objects.filter(user=user, confirmed=True).exists():
                return _json({'error': 'Un appareil est déjà activé sur ce compte.'}, 409)

            pending = (
                TOTPDevice.objects.select_for_update()
                .filter(user=user, confirmed=False)
                .order_by('-pk')
                .first()
            )
            if pending is None:
                return _json({'error': 'Commencez par afficher le QR code.'}, 409)
            if not pending.verify_token(token):
                # django-otp applies per-device throttling and anti-replay.
                return _json({
                    'error': 'Code incorrect ou temporairement bloqué. '
                             'Attendez le prochain code, puis réessayez.'
                }, 400)

            pending.name = 'Microsoft Authenticator'
            pending.confirmed = True
            pending.save(update_fields=['name', 'confirmed'])
            TOTPDevice.objects.filter(user=user, confirmed=False).exclude(
                pk=pending.pk
            ).delete()

        auth_login(request, user)
        otp_login(request, pending)
        logger.info('TOTP enrolment confirmed user_id=%s device_id=%s', user.pk, pending.pk)
        return _json({'success': True, 'redirect': '/tus-gestion-secure/'})
    except Exception:
        logger.exception('TOTP enrolment confirmation failed user_id=%s', user.pk)
        return _json({'error': 'Impossible d’activer l’authentification.'}, 500)
