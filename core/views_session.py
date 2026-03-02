"""Lightweight session keep-alive endpoint for admin heartbeat.

Returns 204 No Content to authenticated staff users.
The simple act of receiving the request renews the session cookie
(thanks to SESSION_SAVE_EVERY_REQUEST = True).

Anonymous or non-staff users receive 403 Forbidden.
"""
import logging

from django.http import HttpResponse
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


@require_GET
def session_ping(request):
    """Keep-alive endpoint — renews session cookie for active admin users.

    Called by the admin heartbeat JS every few minutes while the user
    is actively interacting with the page (mouse / keyboard activity).
    Returns 204 (no body) to minimise bandwidth.
    """
    if not (
        hasattr(request, 'user')
        and request.user.is_authenticated
        and request.user.is_staff
    ):
        return HttpResponse(status=403)

    # Touch the session to ensure SESSION_SAVE_EVERY_REQUEST renews it.
    # Setting a lightweight timestamp guarantees the session is marked modified.
    import time
    request.session['_last_activity'] = int(time.time())

    response = HttpResponse(status=204)
    response['Cache-Control'] = 'no-store'
    return response
