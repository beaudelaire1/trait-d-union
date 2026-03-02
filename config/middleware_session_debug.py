"""�️ Session guard middleware for admin — logs anomalies only.

Placed AFTER AuthenticationMiddleware + OTPMiddleware.  On admin requests,
checks for session-related problems and logs a WARNING only when something
is wrong (no noise on healthy requests).

Diagnostics logged:
- Session cookie absent
- Session data empty (cookie present but no data in DB)
- Auth hash mismatch (SECRET_KEY changed between session creation and now)
- OTP device missing from session
- OTP device lookup failed (device deleted from DB?)
- User became anonymous despite having a session cookie

This middleware NEVER blocks or modifies the request — it observes only.
"""
import logging

from django.conf import settings
from django.contrib.auth import HASH_SESSION_KEY, BACKEND_SESSION_KEY
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('tus.session_guard')


class SessionGuardMiddleware(MiddlewareMixin):
    """Log admin session anomalies (WARNING level only)."""

    def process_request(self, request):
        # Only check admin requests
        if not request.path.startswith('/tus-gestion-secure/'):
            return None

        # Skip static assets, login page, and session-ping
        skip_suffixes = ('/login/', '/session-ping/', '/jsi18n/')
        if any(request.path.endswith(s) for s in skip_suffixes):
            return None

        cookie_name = getattr(settings, 'SESSION_COOKIE_NAME', 'sessionid')
        has_cookie = cookie_name in request.COOKIES

        # ── Check 1: No session cookie at all ──
        if not has_cookie:
            logger.warning(
                "[SESSION-GUARD] NO_COOKIE | path=%s | "
                "The browser did not send the '%s' cookie. "
                "Possible causes: cookie expired, Secure flag with HTTP, "
                "domain mismatch, or first visit.",
                request.path[:80], cookie_name,
            )
            return None

        session = getattr(request, 'session', None)
        if session is None:
            logger.warning(
                "[SESSION-GUARD] NO_SESSION_OBJ | path=%s | "
                "SessionMiddleware did not attach a session.",
                request.path[:80],
            )
            return None

        session_key_prefix = request.COOKIES.get(cookie_name, '?')[:12]

        # ── Check 2: Session data empty ──
        user_id = session.get('_auth_user_id')
        if not user_id:
            logger.warning(
                "[SESSION-GUARD] EMPTY_SESSION | path=%s | key=%s… | "
                "Cookie present but _auth_user_id missing in session data. "
                "Session may have been flushed or expired in DB.",
                request.path[:80], session_key_prefix,
            )
            return None

        # ── Check 3: Auth hash mismatch (SECRET_KEY rotation) ──
        user = getattr(request, 'user', None)
        if user and hasattr(user, 'is_authenticated') and user.is_authenticated:
            hash_in_session = session.get(HASH_SESSION_KEY, '')
            if hash_in_session and hasattr(user, 'get_session_auth_hash'):
                computed = user.get_session_auth_hash()
                if hash_in_session != computed:
                    logger.warning(
                        "[SESSION-GUARD] HASH_MISMATCH | path=%s | key=%s… | "
                        "user=%s | session_hash=%s… | computed_hash=%s… | "
                        "SECRET_KEY may have changed since this session was created. "
                        "User will be logged out by Django.",
                        request.path[:80], session_key_prefix,
                        user.username, hash_in_session[:12], computed[:12],
                    )
                    return None

            # ── Check 4: OTP device missing ──
            otp_device_id = session.get('otp_device_id')
            if not otp_device_id:
                logger.warning(
                    "[SESSION-GUARD] NO_OTP_DEVICE | path=%s | key=%s… | "
                    "user=%s | Authenticated but otp_device_id not in session. "
                    "OTPAdminSite.has_permission() will reject access.",
                    request.path[:80], session_key_prefix, user.username,
                )
            elif hasattr(user, 'is_verified') and not user.is_verified():
                logger.warning(
                    "[SESSION-GUARD] OTP_NOT_VERIFIED | path=%s | key=%s… | "
                    "user=%s | otp_device_id=%s | Device stored in session but "
                    "is_verified()=False. Device may have been deleted from DB.",
                    request.path[:80], session_key_prefix,
                    user.username, otp_device_id,
                )
        elif user and not user.is_authenticated:
            logger.warning(
                "[SESSION-GUARD] ANON_WITH_COOKIE | path=%s | key=%s… | "
                "user_id_in_session=%s | User is AnonymousUser despite "
                "having session data. AuthenticationMiddleware may have "
                "flushed the session (hash mismatch or backend error).",
                request.path[:80], session_key_prefix, user_id,
            )

        return None
