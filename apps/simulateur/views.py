"""Views for the standalone Simulateur app."""
from __future__ import annotations

from typing import Any

from django.views.generic import TemplateView

from services.models import Service


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
