"""Views for the standalone Simulateur app."""
from __future__ import annotations

import json
import logging
from typing import Any

from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from core.utils import get_client_ip
from services.models import Service

from .forms import SimulatorReportForm
from .services import SimulatorReportService

logger = logging.getLogger(__name__)


# ── Hub ──────────────────────────────────────────────────────
class HubView(TemplateView):
    """Hub listant tous les outils de simulation."""
    template_name: str = 'simulateur/hub.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx['breadcrumbs_list'] = [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'Simulateur', 'url': '/simulateur/'},
        ]
        return ctx


# ── Devis / Facture (existant) ───────────────────────────────
class SimulateurView(TemplateView):
    """Page de simulation interactive de devis / facture."""

    template_name: str = 'simulateur/simulateur.html'

    def dispatch(self, request, *args, **kwargs):
        from django.middleware.csrf import get_token
        get_token(request)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['services'] = list(
            Service.objects.filter(is_active=True)
            .values('name', 'base_price', 'price_unit')
            .order_by('name')
        )
        context['breadcrumbs_list'] = [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'Simulateur', 'url': '/simulateur/'},
            {'name': 'Devis', 'url': '/simulateur/devis/'},
        ]
        return context


# ── Outils stratégiques (100 % client-side) ──────────────────
@method_decorator(ensure_csrf_cookie, name='dispatch')
class _ToolView(TemplateView):
    """Base pour les outils sans logique serveur."""
    tool_name: str = ''

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx['breadcrumbs_list'] = [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'Simulateur', 'url': '/simulateur/'},
            {'name': self.tool_name},
        ]
        # Exposé pour le CTA capture email + rapport PDF (cf. tool_base.html).
        ctx['tool_name'] = self.tool_name
        match = getattr(self.request, 'resolver_match', None)
        ctx['tool_slug'] = match.url_name if match and match.url_name else ''
        return ctx


class PointMortView(_ToolView):
    template_name = 'simulateur/point_mort.html'
    tool_name = 'Seuil de Rentabilité'


class CacView(_ToolView):
    template_name = 'simulateur/cac.html'
    tool_name = 'Coût d\'Acquisition'


class FrictionView(_ToolView):
    template_name = 'simulateur/friction.html'
    tool_name = 'Friction Opérationnelle'


class FragmentationView(_ToolView):
    template_name = 'simulateur/fragmentation.html'
    tool_name = 'Indice de Fragmentation'


class AcseView(_ToolView):
    template_name = 'simulateur/acse.html'
    tool_name = 'Flux A.C.S.E'


class PlafondView(_ToolView):
    template_name = 'simulateur/plafond.html'
    tool_name = 'Plafond de Verre'


class ElasticiteView(_ToolView):
    template_name = 'simulateur/elasticite.html'
    tool_name = 'Élasticité-Prix'


class ValleeMortView(_ToolView):
    template_name = 'simulateur/vallee_mort.html'
    tool_name = 'Vallée de la Mort'


class RetentionView(_ToolView):
    template_name = 'simulateur/retention.html'
    tool_name = 'Effet Rétention'


# ── 20 Nouveaux Outils Stratégiques ──────────────────────────

class MixProduitsView(_ToolView):
    template_name = 'simulateur/mix_produits.html'
    tool_name = 'Optimiseur de Mix Produits/Services'


class AtterrissageView(_ToolView):
    template_name = 'simulateur/atterrissage.html'
    tool_name = 'Atterrissage Trimestriel / Annuel'


class TresorerieView(_ToolView):
    template_name = 'simulateur/tresorerie.html'
    tool_name = 'Atterrissage Mensuel Trésorerie'


class JumeauxClientsView(_ToolView):
    template_name = 'simulateur/jumeaux_clients.html'
    tool_name = 'Simulateur de Jumeaux Clients'


class CorrelationView(_ToolView):
    template_name = 'simulateur/correlation.html'
    tool_name = 'Corrélation Produits/Services'


class DelegationView(_ToolView):
    template_name = 'simulateur/delegation.html'
    tool_name = 'Seuil de Délégation'


class PrixPsychologiqueView(_ToolView):
    template_name = 'simulateur/prix_psychologique.html'
    tool_name = 'Prix Psychologique'


class DependanceView(_ToolView):
    template_name = 'simulateur/dependance.html'
    tool_name = 'Radar de Dépendance Commerciale'


class CapaciteView(_ToolView):
    template_name = 'simulateur/capacite.html'
    tool_name = 'Capacité Maximale Facturable'


class SaisonnaliteView(_ToolView):
    template_name = 'simulateur/saisonnalite.html'
    tool_name = 'Impact Saisonnalité'


class CoutPromotionView(_ToolView):
    template_name = 'simulateur/cout_promotion.html'
    tool_name = 'Vrai Coût d\'une Promotion'


class ValeurSortieView(_ToolView):
    template_name = 'simulateur/valeur_sortie.html'
    tool_name = 'Valeur de Sortie'


class EffortImpactView(_ToolView):
    template_name = 'simulateur/effort_impact.html'
    tool_name = 'Matrice Effort / Impact'


class CoutInactionView(_ToolView):
    template_name = 'simulateur/cout_inaction.html'
    tool_name = 'Coût d\'Inaction'


class ScenarioPivotView(_ToolView):
    template_name = 'simulateur/scenario_pivot.html'
    tool_name = 'Scénario Pivot'


class RoiMarketingView(_ToolView):
    template_name = 'simulateur/roi_marketing.html'
    tool_name = 'ROI Campagne Marketing'


class PricingPaliersView(_ToolView):
    template_name = 'simulateur/pricing_paliers.html'
    tool_name = 'Pricing par Paliers'


class TailleMarcheView(_ToolView):
    template_name = 'simulateur/taille_marche.html'
    tool_name = 'Taille de Marché Accessible'


class VulnerabileFournisseurView(_ToolView):
    template_name = 'simulateur/vulnerabilite_fournisseur.html'
    tool_name = 'Vulnérabilité Fournisseur'


class CoutNonQualiteView(_ToolView):
    template_name = 'simulateur/cout_non_qualite.html'
    tool_name = 'Coût de la Non-Qualité'


# ── Endpoint: capture email + envoi rapport PDF ─────────────
@method_decorator(require_POST, name='dispatch')
class ReportSubmitView(View):
    """Reçoit la demande de rapport PDF en fin de simulateur.

    Entrée : JSON ``{email, name?, company?, tool_slug, tool_name,
    snapshot, website (honeypot), consent}``.
    Sortie : JSON ``{ok, message}`` ou ``{ok:false, errors}``.
    """

    MAX_PER_IP_PER_HOUR = 5

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        # Parse JSON payload.
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

        # Rate-limit par IP (fenêtre 1h).
        ip = get_client_ip(request)
        if self._is_rate_limited(ip):
            logger.warning("Rate limit atteint pour %s (report simulateur)", ip)
            return JsonResponse(
                {'ok': False,
                 'message': 'Trop de demandes. Merci de réessayer plus tard.'},
                status=429,
            )

        # Honeypot : si rempli, succès factice, rien n'est persisté ni envoyé.
        if payload.get('website'):
            logger.info("Honeypot simulateur déclenché depuis %s", ip)
            return JsonResponse({'ok': True, 'message': 'Merci.'})

        form = SimulatorReportForm(payload)
        if not form.is_valid():
            return JsonResponse(
                {'ok': False, 'errors': form.errors.get_json_data()},
                status=400,
            )

        report = form.save(commit=False)
        report.ip_address = ip or None
        report.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        report.save()

        # Les graphiques (base64 lourds) ne sont pas persistés en DB :
        # ils sont passés de façon transiente au service PDF.
        transient_charts = getattr(form, '_transient_charts', None)

        # Mode de livraison : 'email' (défaut) ou 'download' (les deux).
        delivery = payload.get('delivery', 'email')
        if delivery not in ('email', 'download'):
            delivery = 'email'

        pdf_bytes: bytes | None = None
        email_ok = True
        email_error: str | None = None

        # 1) En mode download, on génère d'abord le PDF — c'est la livraison
        #    prioritaire, une erreur email ne doit pas bloquer le téléchargement.
        if delivery == 'download':
            try:
                pdf_bytes = SimulatorReportService.generate_pdf(
                    report, charts=transient_charts,
                )
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Échec génération PDF rapport simulateur #%s : %s",
                    report.pk, exc, exc_info=True,
                )
                return JsonResponse(
                    {'ok': False,
                     'message': "Nous n'avons pas pu générer le PDF. "
                                'Réessayez ou contactez-nous.'},
                    status=500,
                )

        # 2) Envoi email (copie). On tolère un échec en mode download.
        try:
            SimulatorReportService.send(
                report, pdf_bytes=pdf_bytes, charts=transient_charts,
            )
        except Exception as exc:  # noqa: BLE001
            email_ok = False
            email_error = str(exc)
            logger.error(
                "Échec envoi email rapport simulateur #%s : %s",
                report.pk, exc, exc_info=True,
            )
            if delivery == 'email':
                # Sans PDF en main, l'utilisateur n'a rien — on remonte l'erreur.
                return JsonResponse(
                    {'ok': False,
                     'message': "Nous n'avons pas pu envoyer le rapport. "
                                'Réessayez ou contactez-nous.'},
                    status=500,
                )

        response: dict[str, Any] = {
            'ok': True,
            'delivery': delivery,
        }
        if delivery == 'download' and pdf_bytes is not None:
            import base64
            response['pdf_base64'] = base64.b64encode(pdf_bytes).decode('ascii')
            response['filename'] = f"rapport_{report.tool_slug or 'simulateur'}.pdf"
            if email_ok:
                response['message'] = (
                    "Téléchargement prêt. Une copie a aussi été envoyée par email."
                )
            else:
                response['message'] = (
                    "Téléchargement prêt. (La copie email n'a pas pu partir, "
                    "mais vous avez le PDF.)"
                )
        else:
            response['message'] = (
                'Votre rapport a été envoyé. Vérifiez votre boîte mail '
                '(pensez à regarder dans les spams).'
            )
        return JsonResponse(response)

    def _is_rate_limited(self, ip: str) -> bool:
        if not ip:
            return False
        from datetime import timedelta
        from django.utils import timezone
        from .models import SimulatorReport
        since = timezone.now() - timedelta(hours=1)
        count = SimulatorReport.objects.filter(
            ip_address=ip, created_at__gte=since,
        ).count()
        return count >= self.MAX_PER_IP_PER_HOUR

