"""Correctifs P0 du parcours de rapport simulateur."""
from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable
from functools import wraps
from typing import Any

from django.http import HttpRequest, JsonResponse

from .forms import SimulatorReportForm
from .views import ReportSubmitView

logger = logging.getLogger(__name__)


class ReportSubmitP0View(ReportSubmitView):
    """Demande de rapport transactionnelle, sans inscription marketing implicite."""

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        try:
            payload = json.loads(request.body.decode('utf-8') or '{}')
        except (ValueError, UnicodeDecodeError):
            return JsonResponse(
                {'ok': False, 'message': 'Requête invalide.'}, status=400,
            )

        if not isinstance(payload, dict):
            return JsonResponse(
                {'ok': False, 'message': 'Format invalide.'}, status=400,
            )

        ip = self._client_ip(request)
        if self._is_rate_limited(ip):
            logger.warning("Rate limit atteint pour %s (report simulateur)", ip)
            return JsonResponse(
                {'ok': False,
                 'message': 'Trop de demandes. Merci de réessayer plus tard.'},
                status=429,
            )

        if payload.get('website'):
            logger.info("Honeypot simulateur déclenché depuis %s", ip)
            return JsonResponse({'ok': True, 'message': 'Merci.'})

        form = SimulatorReportForm(payload)
        if not form.is_valid():
            return JsonResponse(
                {
                    'ok': False,
                    'message': self._readable_error(form),
                    'errors': form.errors.get_json_data(),
                },
                status=400,
            )

        report = form.save(commit=False)
        report.ip_address = ip or None
        report.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        report.save()

        # IMPORTANT : la demande de rapport est transactionnelle.
        # Elle ne crée ni abonnement newsletter ni consentement marketing.
        transient_charts = getattr(form, '_transient_charts', None)

        delivery = payload.get('delivery', 'email')
        if delivery not in ('email', 'download'):
            delivery = 'email'

        pdf_bytes: bytes | None = None
        if delivery == 'download':
            pdf_bytes = self._render_pdf_resilient(report, transient_charts)
            if pdf_bytes is None:
                return JsonResponse(
                    {
                        'ok': False,
                        'message': (
                            "Nous n'avons pas pu générer le PDF. "
                            'Réessayez ou demandez-le par email.'
                        ),
                    },
                    status=500,
                )

        self._dispatch_report_email(
            report,
            pdf_bytes=pdf_bytes,
            charts=transient_charts,
        )

        response: dict[str, Any] = {
            'ok': True,
            'delivery': delivery,
        }
        if delivery == 'download' and pdf_bytes is not None:
            import base64

            response['pdf_base64'] = base64.b64encode(pdf_bytes).decode('ascii')
            response['filename'] = f"rapport_{report.tool_slug or 'simulateur'}.pdf"
            response['message'] = (
                "Téléchargement prêt. Une copie vous est envoyée par email."
            )
        else:
            response['message'] = (
                "Votre rapport est en cours d'envoi à l'adresse indiquée."
            )
        return JsonResponse(response)

    @staticmethod
    def _client_ip(request: HttpRequest) -> str:
        """Réutilise la source d'IP standard du projet sans dupliquer sa logique."""
        from core.utils import get_client_ip

        return get_client_ip(request)


def stabilize_simulator_page(view: Callable) -> Callable:
    """Corrige le HTML public des modales de rapport avant envoi au client.

    Cette couche est volontairement limitée aux pages simulateur et à trois
    défauts de rendu audités : commentaire Django multiligne exposé, libellé de
    consentement couplant rapport et marketing, et fineprint de désinscription
    devenu faux puisque l'inscription marketing automatique est supprimée.
    """

    @wraps(view)
    def _wrapped(request, *args, **kwargs):
        response = view(request, *args, **kwargs)
        if not hasattr(response, 'add_post_render_callback'):
            return response

        def _sanitize(rendered_response):
            content_type = rendered_response.get('Content-Type', '')
            if 'text/html' not in content_type:
                return rendered_response

            charset = getattr(rendered_response, 'charset', None) or 'utf-8'
            html = rendered_response.content.decode(charset, errors='replace')

            # Retire le commentaire multiligne qui apparaît dans le HTML public.
            html = re.sub(
                r'\{#\s*Attributs HTML\s*:.*?slug envoyé au serveur serait invalide\.\s*#\}',
                '',
                html,
                flags=re.DOTALL,
            )
            html = re.sub(
                r'Attributs HTML\s*:.*?slug envoyé au serveur serait invalide\.\s*',
                '',
                html,
                flags=re.DOTALL,
            )

            # Le consentement ne porte plus que sur la livraison demandée.
            html = html.replace(
                "J'accepte de recevoir ce rapport et, occasionnellement, "
                "du contenu utile de Trait d'Union Studio. Désinscription en un clic.",
                "J'accepte que mon adresse email soit utilisée pour me transmettre ce rapport.",
            )
            html = html.replace(
                'Aucune carte · Aucun spam · Désinscription en un clic',
                'Aucune carte · Aucun abonnement marketing automatique',
            )
            html = re.sub(
                r'(<p class="report-cta-fineprint">.*?)(Désinscription en un clic)(.*?</p>)',
                r'\1Pas d’inscription automatique\3',
                html,
                flags=re.DOTALL,
            )

            rendered_response.content = html.encode(charset)
            return rendered_response

        response.add_post_render_callback(_sanitize)
        return response

    return _wrapped