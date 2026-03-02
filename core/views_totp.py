"""🛡️ SECURITY: TOTP QR code endpoint for admin 2FA login.

Returns a QR code PNG image only after validating username + password.
Rate-limited to prevent brute-force attacks.
"""
import io
import logging

from django.contrib.auth import authenticate
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from core.utils import get_client_ip

logger = logging.getLogger(__name__)

# Rate limit: 5 QR code requests per 15 minutes per IP
QR_RATE_LIMIT = 5
QR_RATE_WINDOW = 900  # 15 minutes


@csrf_protect
@require_POST
def totp_qr_code(request):
    """Generate TOTP QR code after credential validation.

    POST /tus-gestion-secure/totp-qr/
    Body: username, password (from the login form)
    Returns: PNG image of QR code or 403/429 JSON error
    """
    ip = get_client_ip(request)
    cache_key = f'totp_qr_rate:{ip}'

    # Rate limiting
    attempts = cache.get(cache_key, 0)
    if attempts >= QR_RATE_LIMIT:
        logger.warning('TOTP QR rate limit exceeded for IP %s', ip)
        return JsonResponse(
            {'error': 'Trop de tentatives. Réessayez dans 15 minutes.'},
            status=429,
        )

    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')

    if not username or not password:
        return JsonResponse({'error': 'Identifiants requis.'}, status=400)

    # Increment rate limit counter BEFORE auth check (prevents timing attacks)
    cache.set(cache_key, attempts + 1, QR_RATE_WINDOW)

    # Authenticate
    user = authenticate(request, username=username, password=password)
    if user is None or not user.is_staff:
        logger.warning('TOTP QR auth failed for user=%s ip=%s', username, ip)
        return JsonResponse({'error': 'Identifiants invalides.'}, status=403)

    # Find or auto-create user's TOTP device
    try:
        from django_otp.plugins.otp_totp.models import TOTPDevice
        device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
        if device is None:
            # Auto-provisioning: create a confirmed TOTP device on first request.
            # This solves the chicken-and-egg problem in production where no
            # admin access exists yet to manually create a device.
            device = TOTPDevice.objects.create(
                user=user,
                name=f'Auto-provisioned ({user.username})',
                confirmed=True,
            )
            logger.info(
                'TOTP device auto-created for staff user=%s ip=%s',
                username, ip,
            )
    except Exception:
        logger.exception('Error fetching/creating TOTP device for user=%s', username)
        return JsonResponse({'error': 'Erreur serveur.'}, status=500)

    # Generate QR code
    try:
        import qrcode
        from qrcode.image.pil import PilImage

        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(device.config_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='#0a0a0a', back_color='#ffffff', image_factory=PilImage)

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        response = HttpResponse(buffer.getvalue(), content_type='image/png')
        # Prevent caching of QR code (contains secret)
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        return response

    except ImportError:
        logger.error('qrcode library not installed')
        return JsonResponse(
            {'error': 'Module QR code non installé sur le serveur.'},
            status=500,
        )
