"""URL configuration for the simulateur app."""
from django.urls import path

from .p0_views import ReportSubmitP0View, stabilize_simulator_page
from .views import (
    AcseView,
    AtterrissageView,
    CacView,
    CapaciteView,
    ConformiteCheckView,
    ConformiteFactureView,
    CorrelationView,
    CoutInactionView,
    CoutNonQualiteView,
    CoutPromotionView,
    DelegationView,
    DependanceView,
    EffortImpactView,
    ElasticiteView,
    FragmentationView,
    FrictionView,
    HubView,
    JumeauxClientsView,
    MixProduitsView,
    PlafondView,
    PointMortView,
    PricingPaliersView,
    PrixPsychologiqueView,
    RetentionView,
    RoiMarketingView,
    SaisonnaliteView,
    ScenarioPivotView,
    SimulateurView,
    TailleMarcheView,
    TresorerieView,
    ValeurSortieView,
    ValleeMortView,
    VulnerabileFournisseurView,
)

app_name = 'simulateur'


def page(view_cls):
    """Rend une page simulateur en appliquant les correctifs HTML P0."""
    return stabilize_simulator_page(view_cls.as_view())


urlpatterns = [
    path('', page(HubView), name='hub'),
    path('devis/', page(SimulateurView), name='devis'),
    # ── Endpoint capture email + envoi rapport PDF ──
    path('report/', ReportSubmitP0View.as_view(), name='report_submit'),
    # ── Conformité facture électronique (serveur) ──
    path('conformite-facture/', page(ConformiteFactureView), name='conformite-facture'),
    path('conformite-facture/check/', ConformiteCheckView.as_view(), name='conformite-facture-check'),
    # ── 10 outils existants ──
    path('point-mort/', page(PointMortView), name='point-mort'),
    path('cac/', page(CacView), name='cac'),
    path('friction/', page(FrictionView), name='friction'),
    path('fragmentation/', page(FragmentationView), name='fragmentation'),
    path('acse/', page(AcseView), name='acse'),
    path('plafond/', page(PlafondView), name='plafond'),
    path('elasticite/', page(ElasticiteView), name='elasticite'),
    path('vallee-mort/', page(ValleeMortView), name='vallee-mort'),
    path('retention/', page(RetentionView), name='retention'),
    # ── 20 nouveaux outils ──
    path('mix-produits/', page(MixProduitsView), name='mix-produits'),
    path('atterrissage/', page(AtterrissageView), name='atterrissage'),
    path('tresorerie/', page(TresorerieView), name='tresorerie'),
    path('jumeaux-clients/', page(JumeauxClientsView), name='jumeaux-clients'),
    path('correlation/', page(CorrelationView), name='correlation'),
    path('delegation/', page(DelegationView), name='delegation'),
    path('prix-psychologique/', page(PrixPsychologiqueView), name='prix-psychologique'),
    path('dependance/', page(DependanceView), name='dependance'),
    path('capacite/', page(CapaciteView), name='capacite'),
    path('saisonnalite/', page(SaisonnaliteView), name='saisonnalite'),
    path('cout-promotion/', page(CoutPromotionView), name='cout-promotion'),
    path('valeur-sortie/', page(ValeurSortieView), name='valeur-sortie'),
    path('effort-impact/', page(EffortImpactView), name='effort-impact'),
    path('cout-inaction/', page(CoutInactionView), name='cout-inaction'),
    path('scenario-pivot/', page(ScenarioPivotView), name='scenario-pivot'),
    path('roi-marketing/', page(RoiMarketingView), name='roi-marketing'),
    path('pricing-paliers/', page(PricingPaliersView), name='pricing-paliers'),
    path('taille-marche/', page(TailleMarcheView), name='taille-marche'),
    path('vulnerabilite-fournisseur/', page(VulnerabileFournisseurView), name='vulnerabilite-fournisseur'),
    path('cout-non-qualite/', page(CoutNonQualiteView), name='cout-non-qualite'),
]
