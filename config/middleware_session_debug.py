"""🔍 TEMPORARY: Session diagnostic middleware for admin.

Logs exactly what happens during admin session verification to diagnose
the "disconnected on every action" issue. REMOVE once resolved.

Place AFTER SessionMiddleware and AuthenticationMiddleware to see
the full picture.
"""
import logging

from django.contrib.auth import HASH_SESSION_KEY, BACKEND_SESSION_KEY
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('tus.session_debug')


class SessionDebugMiddleware(MiddlewareMixin):
    """Log admin session state for every admin request."""

    def process_request(self, request):
        if not request.path.startswith('/tus-gestion-secure/'):
            return None

        # 1. Check session cookie
        cookie_name = getattr(
            __import__('django.conf', fromlist=['settings']).settings,
            'SESSION_COOKIE_NAME', 'sessionid',
        )
        has_cookie = cookie_name in request.COOKIES
        session_key = request.COOKIES.get(cookie_name, '<ABSENT>')[:12]

        # 2. Check session data
        session = getattr(request, 'session', None)
        if session is None:
            logger.warning(
                "[SESSION-DEBUG] path=%s | cookie=%s(key=%s…) | "
                "NO session object on request!",
                request.path, has_cookie, session_key,
            )
            return None

        user_id = session.get('_auth_user_id', '<NONE>')
        backend = session.get(BACKEND_SESSION_KEY, '<NONE>')
        hash_in_session = session.get(HASH_SESSION_KEY, '<NONE>')
        otp_device = session.get('otp_device_id', '<NONE>')
        session_is_empty = not bool(dict(session))

        # 3. Check user
        user = getattr(request, 'user', None)
        user_repr = 'N/A'
        user_verified = False
        computed_hash = '<N/A>'
        if user and hasattr(user, 'is_authenticated'):
            if user.is_authenticated:
                user_repr = f"{user.username}(staff={user.is_staff})"
                if hasattr(user, 'get_session_auth_hash'):
                    computed_hash = user.get_session_auth_hash()[:12]
                if hasattr(user, 'is_verified'):
                    user_verified = user.is_verified()
            else:
                user_repr = 'AnonymousUser'

        hash_match = 'N/A'
        if hash_in_session != '<NONE>' and computed_hash != '<N/A>':
            hash_match = 'MATCH' if hash_in_session[:12] == computed_hash else 'MISMATCH'

        logger.warning(
            "[SESSION-DEBUG] path=%s | cookie=%s(key=%s…) | "
            "session_empty=%s | user_id=%s | user=%s | "
            "hash_match=%s | otp_device=%s | otp_verified=%s | "
            "backend=%s",
            request.path[:60], has_cookie, session_key,
            session_is_empty, user_id, user_repr,
            hash_match, otp_device, user_verified,
            backend[:30] if backend != '<NONE>' else backend,
        )

        return None
