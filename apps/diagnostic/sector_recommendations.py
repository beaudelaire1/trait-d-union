"""Recommandations sectorielles & repères métier — Diagnostic terrain v2 Palier 3.

Ce module fournit deux moteurs déclaratifs alimentés par les réponses aux
questions métier (domaine ``metier`` du catalogue ``field_questions``) :

1. **Recommandations sectorielles** — règles évaluées sur une question métier.
   Quand la valeur saisie franchit un seuil, une recommandation ciblée est
   ajoutée au plan d'action. Ces recommandations s'intègrent à celles déjà
   produites par le moteur universel (cf. ``field_scoring.build_recommendations``).

2. **Repères métier** — seuils par question métier produisant un statut
   ``good`` / ``warn`` / ``danger`` pour l'encart "Repères de votre métier"
   du rapport PDF. Aucun impact sur le score global /100.

Principes :
- 100 % déclaratif : aucune règle métier n'est codée dans le moteur de scoring.
- Le silence est OK : si la question n'a pas été renseignée, la règle n'est
  jamais déclenchée (pas de pénalité fantôme).
- Les seuils proviennent d'observations métier sourcées dans les commentaires
  pour rester auditables.
- Les libellés sont des questions / actions concrètes, lisibles à voix haute.

À l'horizon Palier 4 : enrichissement des seuils avec des benchmarks
territoriaux (Outre-Mer / hexagone / international) et plus de règles par
secteur. La structure ne changera pas.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

from .field_scoring import _num


# ════════════════════════════════════════════════════════════════════
# Modèles de règles
# ════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SectorRule:
    """Règle de recommandation sectorielle déclenchée par une réponse métier.

    Attributes:
        sector: Slug du secteur (ex. "btp", "restauration"). Doit
            correspondre aux clés de ``field_questions.SECTORS``.
        question_id: Identifiant de la question métier observée.
        condition: Expression évaluable contre la valeur de la réponse.
            Formats supportés :
            - ">= 35"  / "<= 5" / "> 25" / "< 60" (numériques)
            - "in:val1,val2"   pour les choix
            - "==:value"       égalité stricte
            - "scale_at_most:3" / "scale_at_least:4" pour les échelles 1..5
        priority: ``critique`` | ``important`` | ``recommande`` | ``bonus``
        title: Titre court de la recommandation (≤ 80 caractères).
        detail: Détail descriptif. Peut contenir le placeholder ``{value}``
            qui sera remplacé par la valeur saisie.
        simulateur: Slug du simulateur TUS associé (facultatif).
        profiles: Si renseigné, restreint la règle aux profils listés.
        territories: Si renseigné, restreint la règle aux territoires listés
            (codes du référentiel ``territory_calibration``). Une règle sans
            ``territories`` s'applique à tous les territoires.
    """

    sector: str
    question_id: str
    condition: str
    priority: str
    title: str
    detail: str
    simulateur: str = ""
    profiles: tuple[str, ...] | None = None
    territories: tuple[str, ...] | None = None


@dataclass(frozen=True)
class SectorMetric:
    """Seuil sur une question métier pour l'encart "Repères de votre métier".

    Le statut résultant est ``good`` / ``warn`` / ``danger`` / ``na``.
    Les seuils sont à valeur unique : on définit le seuil "good"
    (cible) et "danger" (zone d'alerte).
    """

    sector: str
    question_id: str
    label: str
    higher_is_better: bool
    good: float
    danger: float
    unit: str = ""


# ════════════════════════════════════════════════════════════════════
# Évaluation d'une condition
# ════════════════════════════════════════════════════════════════════

_NUM_OP_RE = re.compile(r"^\s*(>=|<=|>|<|==)\s*(-?\d+(?:[.,]\d+)?)\s*$")


def _evaluate_condition(raw_value: Any, condition: str) -> bool:
    """Vrai si la valeur (telle que stockée dans `answers`) satisfait la condition."""
    cond = (condition or "").strip()
    if not cond or raw_value in (None, ""):
        return False

    # ── Choix dans une liste ────────────────────────────────────────
    if cond.startswith("in:"):
        whitelist = {v.strip() for v in cond[3:].split(",") if v.strip()}
        return str(raw_value).strip() in whitelist

    if cond.startswith("==:"):
        return str(raw_value).strip() == cond[3:].strip()

    # ── Échelles 1..5 ───────────────────────────────────────────────
    if cond.startswith("scale_at_most:"):
        threshold = float(cond.split(":", 1)[1])
        try:
            return float(str(raw_value).replace(",", ".")) <= threshold
        except ValueError:
            return False

    if cond.startswith("scale_at_least:"):
        threshold = float(cond.split(":", 1)[1])
        try:
            return float(str(raw_value).replace(",", ".")) >= threshold
        except ValueError:
            return False

    # ── Comparateurs numériques ─────────────────────────────────────
    match = _NUM_OP_RE.match(cond)
    if not match:
        return False
    op, threshold_str = match.groups()
    try:
        threshold = float(threshold_str.replace(",", "."))
        value = float(str(raw_value).replace(",", "."))
    except (TypeError, ValueError):
        return False

    return {
        ">=": value >= threshold,
        "<=": value <= threshold,
        ">": value > threshold,
        "<": value < threshold,
        "==": value == threshold,
    }[op]


# ════════════════════════════════════════════════════════════════════
# Catalogue des règles sectorielles
# ════════════════════════════════════════════════════════════════════
#
# Convention de nommage :
#   - 3 à 5 règles par secteur principal
#   - les seuils sont sourcés (commentaires) ou marqués "à calibrer"
#   - une même règle peut viser plusieurs profils via `profiles=(...)`
#
SECTOR_RULES: tuple[SectorRule, ...] = (

    # ─────────── BTP / CONSTRUCTION ─────────────────────────────────
    SectorRule(
        "btp", "btp_taux_marge_chantier", "< 12",
        "important",
        "Marge nette par chantier sous 12 %",
        "Une marge inférieure à 12 % expose à la perte au moindre aléa "
        "(intempéries, dépassement, retenues). Refondre le chiffrage et "
        "intégrer une provision aléas explicite dans chaque devis.",
        simulateur="point_mort",
    ),
    SectorRule(
        "btp", "btp_depassement_budget", ">= 25",
        "important",
        "Plus de 25 % de chantiers en dépassement",
        "Le dépassement systématique mange la marge prévue : revoir le "
        "process de chiffrage (BdM matériaux, charge atelier) et instaurer "
        "une revue financière mi-chantier.",
        simulateur="point_mort",
    ),
    SectorRule(
        "btp", "btp_delai_reglement_situations", ">= 75",
        "critique",
        "Délai de paiement situations supérieur à 75 jours",
        "Le BTP avance la trésorerie de ses clients sur des mois. À ce "
        "niveau, le besoin en fonds de roulement met l'entreprise en "
        "tension : facturer à l'avancement plus court et négocier acomptes.",
        simulateur="tresorerie",
    ),
    SectorRule(
        "btp", "btp_part_renovation", "<= 20",
        "recommande",
        "Mix neuf/rénovation peu équilibré",
        "Une dépendance forte au neuf vous expose aux cycles immobiliers. "
        "La rénovation, plus régulière et moins concurrentielle, sécurise "
        "le carnet de commandes.",
    ),

    # ─────────── RESTAURATION ───────────────────────────────────────
    SectorRule(
        "restauration", "ratio_cout_matiere", ">= 35",
        "important",
        "Food cost trop élevé (> 35 %)",
        "Au-delà de 35 %, la marge brute se dégrade et amortit mal les "
        "charges de personnel. Audit carte (rationalisation, food cost "
        "par plat) et optimisation des achats prioritaires.",
        simulateur="point_mort",
    ),
    SectorRule(
        "restauration", "no_show_pct", ">= 10",
        "important",
        "Taux de no-show supérieur à 10 %",
        "Un créneau perdu n'est jamais rattrapé. Mettre en place rappels "
        "automatiques (SMS J-1) et acompte sur réservations de groupes.",
    ),
    SectorRule(
        "restauration", "rest_part_livraison", ">= 30",
        "recommande",
        "Forte dépendance aux plateformes de livraison",
        "Les plateformes prélèvent jusqu'à 30 % : un volume fort gonfle "
        "le CA mais écrase la marge. Encourager la commande directe "
        "(QR, programme fidélité, livraison maison sur zone proche).",
    ),
    SectorRule(
        "restauration", "rest_pertes_matiere", ">= 7",
        "recommande",
        "Pertes matière supérieures à 7 %",
        "Le gaspillage s'ajoute au food cost. Pesée systématique, "
        "menus du marché et standardisation des portions sont les "
        "premiers leviers.",
    ),
    SectorRule(
        "restauration", "rest_part_boisson", "<= 18",
        "recommande",
        "Part boissons trop faible dans le ticket",
        "Les boissons portent une marge bien supérieure aux plats. "
        "Un travail sur la carte des boissons et l'upsell en salle "
        "peut récupérer 5 à 10 points de marge.",
    ),

    # ─────────── E-COMMERCE ─────────────────────────────────────────
    SectorRule(
        "ecommerce", "eco_panier_abandon", ">= 75",
        "important",
        "Abandon de panier supérieur à 75 %",
        "Le tunnel de paiement fuit. Audit prioritaire : transparence "
        "des frais de port, options de paiement, réassurance, retours.",
        simulateur="cac",
    ),
    SectorRule(
        "ecommerce", "taux_conversion_web", "<= 1",
        "important",
        "Taux de conversion sous 1 %",
        "En e-commerce, un taux de conversion < 1 % signale un problème "
        "majeur (trafic non qualifié, offre, vitesse, mobile). Audit "
        "complet recommandé avant d'investir plus en acquisition.",
        simulateur="cac",
    ),
    SectorRule(
        "ecommerce", "eco_part_marketplace", ">= 50",
        "important",
        "Plus de la moitié du CA via marketplaces",
        "Les marketplaces apportent du volume mais prélèvent 10-25 % "
        "et vous coupent de la relation client. Diversifier les canaux "
        "(site direct, email, fidélisation) est prioritaire.",
    ),
    SectorRule(
        "ecommerce", "eco_recurrence_achat", "scale_at_most:2",
        "recommande",
        "Faible réachat : modèle vulnérable à l'acquisition",
        "Un e-commerce qui repose uniquement sur l'acquisition est "
        "fragile (CAC en hausse continue). Travailler la rétention "
        "(emailing, programme fidélité, abonnement) protège la marge.",
        simulateur="retention",
    ),
    SectorRule(
        "ecommerce", "eco_delai_prepa", ">= 48",
        "recommande",
        "Délai de préparation supérieur à 48 h",
        "Au-delà de 48 h, le taux de litige et d'annulation grimpe. "
        "Optimiser la préparation (slotting, picking, intégration "
        "transporteur) fait gagner sur tous les indicateurs.",
    ),

    # ─────────── CONSEIL / LIBÉRAL ──────────────────────────────────
    SectorRule(
        "conseil", "cons_jours_factures_an", "<= 150",
        "important",
        "Moins de 150 jours facturables / an",
        "Le plafond de revenu d'un libéral est borné par les jours "
        "facturables. Sous 150 j, la marge est rapidement sous tension. "
        "Prioriser : déléguer l'admin, packager des forfaits, prospecter.",
        simulateur="capacite",
    ),
    SectorRule(
        "conseil", "cons_taux_realisation", "<= 70",
        "important",
        "Taux de réalisation faible (< 70 %)",
        "Trop de temps « offert » (dépassements, reprises) ronge le "
        "TJM réel. Cadrer les missions (livrables, périmètre, avenants) "
        "restaure la marge effective.",
    ),
    SectorRule(
        "conseil", "cons_temps_admin", ">= 30",
        "recommande",
        "Plus de 30 % de temps administratif",
        "Chaque heure d'admin est une heure non vendue. Externaliser "
        "(secrétariat, compta) ou outiller (factur., banque pro, "
        "automatisations) devient rentable au-delà de 25 %.",
        simulateur="friction",
    ),
    SectorRule(
        "conseil", "cons_specialisation", "scale_at_most:2",
        "recommande",
        "Positionnement généraliste",
        "La spécialisation justifie un tarif premium et réduit la "
        "concurrence. Choisir une niche (verticale ou expertise) est "
        "souvent le levier de marge le plus puissant.",
        simulateur="elasticite",
    ),

    # ─────────── SERVICES B2B ──────────────────────────────────────
    SectorRule(
        "services_pro", "spro_cycle_vente", ">= 90",
        "important",
        "Cycle de vente supérieur à 90 jours",
        "Un cycle long mobilise de la trésorerie commerciale. "
        "Enrichir le pipeline en amont, qualifier mieux et instaurer "
        "des points de décision intermédiaires raccourcissent le cycle.",
    ),
    SectorRule(
        "services_pro", "spro_taux_upsell", "<= 15",
        "recommande",
        "Faible upsell sur la base existante",
        "Vendre à un client acquis coûte 5x moins cher que d'en gagner "
        "un nouveau. Cartographier les besoins de la base actuelle est "
        "un quick-win souvent négligé.",
        simulateur="retention",
    ),
    SectorRule(
        "services_pro", "spro_pipe_couverture", "<= 1",
        "critique",
        "Pipeline qui couvre moins d'un mois de CA",
        "Risque de trou d'activité dans 1 à 3 mois. Plan d'action "
        "commercial intensif : réveil de prospects dormants, demandes "
        "de recommandations actives, prospection ciblée.",
    ),
    SectorRule(
        "services_pro", "spro_concentration_secteur", "scale_at_least:4",
        "recommande",
        "Forte concentration sectorielle",
        "Une dépendance à un seul secteur expose à ses retournements. "
        "Diversifier les verticales (a minima 2-3 secteurs cibles) "
        "lisse les cycles d'activité.",
    ),
    SectorRule(
        "services_pro", "spro_nps", "scale_at_most:2",
        "important",
        "Faible propension à recommander",
        "En B2B, la recommandation est le premier canal d'acquisition. "
        "Un NPS bas annonce du churn : audit satisfaction prioritaire.",
    ),

    # ─────────── SERVICES B2C ──────────────────────────────────────
    SectorRule(
        "services_part", "spart_taux_reabonnement", "<= 25",
        "important",
        "Faible récurrence client",
        "Un service local sans réachat dépend de l'acquisition "
        "permanente. Programme de suivi, contrats annuels, offres "
        "d'entretien préventif transforment l'occasionnel en récurrent.",
        simulateur="retention",
    ),
    SectorRule(
        "services_part", "spart_recommandation_pct", ">= 75",
        "recommande",
        "Dépendance critique au bouche-à-oreille",
        "Le bouche-à-oreille est gratuit mais peu maîtrisable. "
        "Diversifier l'acquisition (Google Business Profile, avis, "
        "partenariats locaux) sécurise la croissance.",
        simulateur="cac",
    ),
    SectorRule(
        "services_part", "spart_avis_note", "scale_at_most:2",
        "important",
        "Note d'e-réputation faible",
        "Pour un service local, les avis Google sont décisifs. "
        "Plan d'action : sollicitation systématique des avis post-"
        "intervention, réponse aux retours négatifs sous 48 h.",
    ),
    SectorRule(
        "services_part", "spart_part_urgence", ">= 50",
        "recommande",
        "Activité dominée par l'urgence",
        "L'urgence se facture plus cher mais désorganise le planning. "
        "Mixer avec du planifié (contrats d'entretien) lisse l'activité "
        "et la rend délégable.",
    ),

    # ─────────── HÔTELLERIE ────────────────────────────────────────
    SectorRule(
        "hotellerie", "hot_repeat_client", "<= 15",
        "recommande",
        "Faible part de clients fidèles",
        "Un client fidèle réserve souvent en direct (commissions "
        "économisées) et coûte moins cher à servir. Programme de "
        "fidélité, email post-séjour, offres exclusives.",
    ),
    SectorRule(
        "hotellerie", "hot_part_extra", "<= 15",
        "recommande",
        "Faible part de revenus annexes",
        "Les extras (restauration, spa, services) améliorent fortement "
        "la rentabilité par client sans dépendre du taux d'occupation. "
        "Étoffer la proposition de valeur en place est rentable.",
    ),
    SectorRule(
        "hotellerie", "reservation_directe_pct", "<= 25",
        "important",
        "Forte dépendance aux OTA",
        "Avec moins de 25 % de réservations directes, les commissions "
        "OTA pèsent lourdement sur la marge. Plan : SEO local, retargeting, "
        "offres exclusives au site, programme fidélité.",
        simulateur="cac",
    ),
    SectorRule(
        "hotellerie", "hot_avis_note", "scale_at_most:2",
        "important",
        "Note d'e-réputation insuffisante",
        "La note conditionne le classement sur Booking et le taux de "
        "conversion direct. Audit qualité de service et plan de réponse "
        "aux avis prioritaires.",
    ),

    # ─────────── SANTÉ / BIEN-ÊTRE ─────────────────────────────────
    SectorRule(
        "sante", "sante_delai_rdv", ">= 30",
        "important",
        "Délai de RDV supérieur à 30 jours",
        "Un délai long signale une demande forte mais aussi un risque "
        "de fuite (patients qui consultent ailleurs). Évaluer une "
        "embauche, un partenariat ou un ajustement tarifaire.",
    ),
    SectorRule(
        "sante", "sante_part_actes_techniques", "<= 25",
        "recommande",
        "Faible part d'actes à forte valeur",
        "Un mix saturé d'actes peu valorisés sature l'agenda sans "
        "dégager de marge. Recentrer sur les actes techniques rentables "
        "est souvent un levier de marge majeur.",
    ),
    SectorRule(
        "sante", "sante_fidelisation", "<= 30",
        "recommande",
        "Patientèle peu suivie de manière régulière",
        "Le suivi régulier stabilise l'activité. Système de rappels, "
        "consultations annuelles dédiées, offres bien-être complémentaires "
        "renforcent la base.",
    ),
    SectorRule(
        "sante", "no_show_pct", ">= 12",
        "important",
        "Taux de no-show élevé (>= 12 %)",
        "Chaque créneau perdu pèse directement sur le CA. Mettre en "
        "place rappels automatiques et politique de double-booking sur "
        "les créneaux à risque.",
    ),

    # ─────────── BEAUTÉ / ESTHÉTIQUE ───────────────────────────────
    SectorRule(
        "beaute", "beau_taux_remplissage_agenda", "<= 60",
        "important",
        "Agenda rempli sous 60 %",
        "Le fauteuil vide est du revenu perdu pour toujours. Audit du "
        "calendrier : créneaux creux, no-show, durée des prestations. "
        "Optimiser le remplissage prime sur la hausse des prix.",
    ),
    SectorRule(
        "beaute", "beau_part_revente_produits", "<= 8",
        "recommande",
        "Revente produits trop faible",
        "La revente porte une marge élevée sans consommer de temps de "
        "fauteuil. Sélection ciblée, mise en valeur, recommandation "
        "post-prestation : 5 à 10 points de CA récupérables.",
    ),
    SectorRule(
        "beaute", "beau_reservation_en_ligne", "scale_at_most:2",
        "recommande",
        "Pas de réservation en ligne fluide",
        "La réservation en ligne réduit les no-shows, remplit les "
        "créneaux creux et libère du temps au comptoir. ROI très rapide.",
    ),
    SectorRule(
        "beaute", "beau_clients_reguliers", "<= 30",
        "important",
        "Faible base de clientes régulières",
        "Dans un métier de récurrence, la fidélisation fait la "
        "stabilité du CA. Carte de fidélité, abonnement (forfaits "
        "mensuels), suivi personnalisé sont les leviers prioritaires.",
        simulateur="retention",
    ),

    # ─────────── COMMERCE DE DÉTAIL ────────────────────────────────
    SectorRule(
        "commerce", "com_invendus_pct", ">= 10",
        "important",
        "Démarque supérieure à 10 %",
        "La démarque détruit directement la marge. Politique d'achat, "
        "rotation des stocks et gestion des invendus (soldes "
        "anticipées, ventes flash) sont prioritaires.",
    ),
    SectorRule(
        "commerce", "com_taux_transformation", "<= 15",
        "important",
        "Taux de transformation magasin faible",
        "Un trafic qui ne convertit pas signale un problème d'offre, "
        "de prix, de merchandising ou d'accueil. Audit en magasin "
        "(parcours client, perception prix, présence vendeur).",
        simulateur="cac",
    ),
    SectorRule(
        "commerce", "com_part_ligne", "<= 5",
        "recommande",
        "Très faible part de ventes en ligne",
        "Une présence digitale (e-shop, click & collect, marketplace) "
        "est devenue indispensable pour capter la demande omnicanale "
        "et compléter le point de vente physique.",
    ),
    SectorRule(
        "commerce", "com_fidelite", "scale_at_most:2",
        "recommande",
        "Pas de programme de fidélité actif",
        "Faire revenir un client coûte beaucoup moins cher que d'en "
        "conquérir un nouveau. Programme fidélité simple, base CRM "
        "minimale et campagnes ciblées sont des quick-wins.",
        simulateur="retention",
    ),

    # ─────────── INDUSTRIE ─────────────────────────────────────────
    SectorRule(
        "industrie", "ind_taux_utilisation_machines", "<= 60",
        "important",
        "Outil de production sous-utilisé",
        "Sous 60 % d'utilisation, le capital immobilisé n'est pas "
        "rentabilisé. Élargir la cible commerciale, sous-traiter pour "
        "d'autres ou diversifier la production absorbe le sous-régime.",
    ),
    SectorRule(
        "industrie", "ind_taux_rebut", ">= 5",
        "important",
        "Taux de rebut élevé (>= 5 %)",
        "Chaque rebut est de la matière et du temps machine perdus. "
        "Démarche qualité (5S, SPC, formation opérateurs) a un ROI "
        "rapide en termes de marge.",
    ),
    SectorRule(
        "industrie", "ind_dependance_matiere", "scale_at_least:4",
        "important",
        "Forte exposition matières premières",
        "Sans clause de révision de prix, une flambée transforme un "
        "carnet plein en chantiers à perte. Indexer ses contrats et "
        "diversifier les sources protègent la marge.",
    ),

    # ─────────── TRANSPORT ─────────────────────────────────────────
    SectorRule(
        "transport", "tra_part_retour_vide", ">= 30",
        "important",
        "Plus de 30 % de trajets à vide",
        "Un km à vide coûte presque autant qu'un km chargé. "
        "Adhérer à des bourses de fret, mutualiser les retours, "
        "ajuster le pricing différencié sont les premiers leviers.",
    ),
    SectorRule(
        "transport", "tra_dependance_carburant", "scale_at_least:4",
        "important",
        "Forte exposition au prix du carburant",
        "Sans clause de répercussion gazole, chaque hausse se paie "
        "directement sur la marge. Renégocier les contrats avec "
        "indexation est prioritaire.",
    ),
    SectorRule(
        "transport", "tra_taux_ponctualite", "<= 92",
        "important",
        "Ponctualité sous 92 %",
        "La fiabilité est le critère n°1 des donneurs d'ordre. "
        "Un taux qui baisse annonce des pénalités et la perte de "
        "contrats. Diagnostic causes-racines prioritaire.",
    ),

    # ─────────── IMMOBILIER ────────────────────────────────────────
    SectorRule(
        "immobilier", "immo_taux_impayes", ">= 5",
        "important",
        "Taux d'impayés supérieur à 5 %",
        "Les impayés engagent votre responsabilité de gestionnaire et "
        "pèsent sur la satisfaction des bailleurs. Renforcer le "
        "scoring locataire et la procédure de relance.",
    ),
    SectorRule(
        "immobilier", "immo_mandats_exclusifs", "<= 25",
        "recommande",
        "Faible part de mandats exclusifs",
        "L'exclusivité sécurise la commission et accélère la vente. "
        "Argumentation sur la valeur ajoutée (visibilité, qualité "
        "de service) est à renforcer.",
    ),
    SectorRule(
        "immobilier", "immo_taux_occupation_parc", "<= 90",
        "important",
        "Vacance locative supérieure à 10 %",
        "La vacance est une perte sèche. Audit prix de marché, "
        "qualité des annonces, photos et délai de remise en état.",
    ),

    # ─────────── FORMATION ─────────────────────────────────────────
    SectorRule(
        "formation", "for_qualiopi", "scale_at_most:2",
        "critique",
        "Certification Qualiopi absente",
        "Sans Qualiopi, l'accès aux fonds publics (CPF, OPCO) est "
        "fermé : c'est une large part du marché finançable. "
        "Lancer la démarche Qualiopi est prioritaire.",
    ),
    SectorRule(
        "formation", "for_taux_remplissage_sessions", "<= 60",
        "important",
        "Sessions remplies à moins de 60 %",
        "Les coûts d'une session sont quasi fixes : sous 60 %, "
        "la marge devient négative. Repenser le format (distanciel, "
        "intra-entreprise) ou la cible permet d'améliorer le taux.",
    ),
    SectorRule(
        "formation", "for_satisfaction_stagiaires", "scale_at_most:3",
        "recommande",
        "Satisfaction stagiaires moyenne",
        "La satisfaction conditionne le bouche-à-oreille B2B et le "
        "maintien de la certification. Plan d'amélioration (contenu, "
        "animation, supports) à formaliser.",
    ),

    # ─────────── TOURISME / LOISIRS ────────────────────────────────
    SectorRule(
        "tourisme", "tou_meteo_dependance", "scale_at_least:4",
        "important",
        "Forte dépendance à la météo",
        "Une dépendance météo augmente la volatilité du CA. "
        "Compenser par des offres « tout temps » (couvert, indoor) "
        "ou une politique de report flexible.",
    ),
    SectorRule(
        "tourisme", "tou_panier_extra", "<= 15",
        "recommande",
        "Faibles ventes additionnelles",
        "Augmenter le panier par client est plus rentable que "
        "d'augmenter la fréquentation, déjà plafonnée par la capacité. "
        "Boutique, restauration, options premium : leviers à activer.",
    ),
    SectorRule(
        "tourisme", "tou_dom_desserte", "scale_at_least:4",
        "important",
        "Très forte dépendance à la desserte aérienne",
        "Une grève ou réduction de lignes peut effondrer la "
        "fréquentation. Cibler une clientèle locale et inter-îles "
        "amortit ce risque structurel.",
    ),

    # ─────────── AGRICULTURE / AGRO ────────────────────────────────
    SectorRule(
        "agro", "agro_part_vente_directe", "<= 20",
        "recommande",
        "Vente directe trop faible",
        "La vente directe capte une marge bien supérieure aux "
        "circuits longs. Marchés, AMAP, e-shop, boutique à la ferme "
        "ouvrent des relais de marge.",
    ),
    SectorRule(
        "agro", "agro_dependance_distributeur", ">= 60",
        "important",
        "Dépendance forte à un distributeur unique",
        "Dépendre d'un acheteur dominant expose à une pression "
        "permanente sur les prix et à un risque de déréférencement. "
        "Diversifier les débouchés est prioritaire.",
    ),
    SectorRule(
        "agro", "agro_part_transformation", "<= 15",
        "recommande",
        "Faible part de produits transformés",
        "Transformer (conserves, jus, fromages) capte de la valeur "
        "ajoutée et lisse la saisonnalité de la vente du brut. "
        "Investissement souvent rentable même à petite échelle.",
    ),

    # ─────────── NUMÉRIQUE / TECH ─────────────────────────────────
    SectorRule(
        "numerique", "num_churn", ">= 12",
        "important",
        "Taux de churn supérieur à 12 %",
        "Le churn est le poison du SaaS. Au-delà de 12 % annuel, "
        "vous remplissez un seau percé. Audit causes (NPS, usage, "
        "valeur perçue) et plan rétention prioritaires.",
        simulateur="retention",
    ),
    SectorRule(
        "numerique", "num_dependance_plateforme", "scale_at_least:4",
        "important",
        "Forte dépendance à une plateforme tierce",
        "Un changement de règles ou de commission peut balayer la "
        "rentabilité du jour au lendemain. Diversifier les canaux "
        "de distribution sécurise le modèle.",
    ),
    SectorRule(
        "numerique", "num_part_recurrent_saas", "<= 20",
        "recommande",
        "Faible part de revenu récurrent",
        "Le récurrent valorise l'entreprise tech bien plus que la "
        "prestation au coup par coup. Identifier ce qui peut "
        "devenir abonnement / maintenance est un chantier rentable.",
    ),

    # ─────────── ASSOCIATION / ESS ─────────────────────────────────
    SectorRule(
        "association", "asso_part_autofinancement", "<= 20",
        "important",
        "Autofinancement très faible",
        "Une dépendance forte aux subventions fragilise le projet : "
        "tout ajustement public déséquilibre le budget. Développer "
        "des activités propres (prestations, événements) sécurise.",
    ),
    SectorRule(
        "association", "asso_dependance_benevoles", "scale_at_least:4",
        "important",
        "Dépendance critique au bénévolat",
        "Le bénévolat est une force mais un risque de continuité. "
        "Documenter les rôles, former, salarier les fonctions clés "
        "protège l'activité de l'essoufflement.",
    ),
    SectorRule(
        "association", "asso_renouvellement_subventions", "scale_at_most:2",
        "important",
        "Financements publics annuels et incertains",
        "Sans conventions pluriannuelles, la visibilité est nulle. "
        "Négocier des engagements pluriannuels et diversifier les "
        "financeurs est prioritaire.",
    ),

    # ─────────── ARTISANAT ─────────────────────────────────────────
    SectorRule(
        "artisanat", "art_valorisation_savoir", "scale_at_most:2",
        "important",
        "Savoir-faire mal valorisé",
        "Le piège classique : un travail d'excellence facturé au prix "
        "d'un produit standard. Repositionnement, communication "
        "(storytelling, photos, vidéos) et grille tarifaire à revoir.",
        simulateur="elasticite",
    ),
    SectorRule(
        "artisanat", "art_transmission", "scale_at_least:4",
        "important",
        "Savoir-faire concentré sur une seule personne",
        "Un savoir-faire reposant sur une personne est un risque "
        "majeur de continuité et un frein à la valorisation de "
        "l'entreprise. Plan de transmission/formation à initier.",
    ),

    # ─────────── ÉVÉNEMENTIEL ──────────────────────────────────────
    SectorRule(
        "evenementiel", "eve_acompte_signature", "<= 25",
        "important",
        "Acompte à la signature trop faible",
        "L'acompte finance les engagements pris auprès des prestataires "
        "et protège des annulations. Sous 25 %, l'amortisseur de "
        "trésorerie est insuffisant.",
    ),
    SectorRule(
        "evenementiel", "eve_taux_marge_event", "<= 15",
        "important",
        "Marge nette par projet sous 15 %",
        "Entre prestataires, location et imprévus, la marge fond "
        "vite. Un chiffrage avec provision aléas et clause de "
        "révision protège la rentabilité.",
        simulateur="point_mort",
    ),
    SectorRule(
        "evenementiel", "eve_part_recurrent_clients", "<= 20",
        "recommande",
        "Peu de clients récurrents",
        "Les clients récurrents (événements annuels) réduisent l'effort "
        "commercial et donnent de la visibilité. Plan de fidélisation "
        "B2B (relances annuelles, offres pluriannuelles).",
    ),

    # ════════════════════════════════════════════════════════════════
    # RÈGLES TERRITORIALES — OUTRE-MER (Palier 4)
    # ════════════════════════════════════════════════════════════════
    # Ces règles ne s'activent que sur des territoires Outre-Mer ciblés,
    # et corrigent / complètent les recommandations sectorielles standard.

    # ─── BTP Outre-Mer ─────────────────────────────────────────────
    SectorRule(
        "btp", "btp_dom_materiaux", ">= 70",
        "important",
        "Dépendance critique aux matériaux importés",
        "Au-delà de 70 % de matériaux importés, la moindre rupture de "
        "fret immobilise les chantiers. Sécuriser : fournisseurs "
        "alternatifs, stock tampon, clause de révision dans tous les "
        "marchés. Anticiper la saison cyclonique (juin-novembre / "
        "novembre-avril selon zone).",
        territories=("guyane", "martinique", "guadeloupe", "reunion",
                     "mayotte", "saint_martin", "polynesie",
                     "nouvelle_caledonie"),
    ),
    SectorRule(
        "btp", "btp_delai_reglement_situations", ">= 60",
        "important",
        "DSO élevé sur la commande publique locale",
        "La commande publique en territoire ultramarin paie souvent à "
        "60-90 jours. Plan : facturation à l'avancement plus serré, "
        "négocier acomptes, surveiller les retenues de garantie qui "
        "s'accumulent.",
        territories=("guyane", "martinique", "guadeloupe", "reunion",
                     "mayotte"),
    ),

    # ─── Restauration / Hôtellerie / Tourisme Outre-Mer ────────────
    SectorRule(
        "restauration", "rest_dom_appro", ">= 60",
        "important",
        "Carte trop dépendante des produits importés",
        "Au-delà de 60 % de denrées importées, vous êtes exposé aux "
        "ruptures de fret et à la volatilité des prix. Réorienter une "
        "part de la carte vers le local sécurise l'appro ET fait un "
        "argument commercial fort en territoire ultramarin.",
        territories=("guyane", "martinique", "guadeloupe", "reunion",
                     "mayotte"),
    ),
    SectorRule(
        "hotellerie", "hot_dom_clientele", ">= 70",
        "important",
        "Très forte dépendance à la clientèle hors territoire",
        "Une clientèle à 70 %+ extérieure lie votre remplissage à la "
        "desserte aérienne et à la haute saison. Développer une offre "
        "locale (séjours week-end, B2B local, événementiel) amortit ce "
        "risque structurel.",
        territories=("guyane", "martinique", "guadeloupe", "reunion",
                     "mayotte", "polynesie", "nouvelle_caledonie"),
    ),
    SectorRule(
        "tourisme", "tou_dom_desserte", "scale_at_least:4",
        "important",
        "Dépendance critique à la desserte aérienne",
        "Une grève ou réduction de lignes peut effondrer votre "
        "fréquentation en quelques jours. Diversifier vers la clientèle "
        "locale et inter-îles donne une base de revenu indépendante "
        "des aléas aériens.",
        territories=("guyane", "martinique", "guadeloupe", "reunion",
                     "mayotte", "saint_martin", "saint_barth",
                     "polynesie", "nouvelle_caledonie"),
    ),

    # ─── Transport inter-îles ──────────────────────────────────────
    SectorRule(
        "transport", "tra_dom_inter_iles", "scale_at_least:4",
        "important",
        "Forte dépendance au transport inter-îles / portuaire",
        "Les ruptures de charge (port, aéroport, liaisons maritimes) "
        "ajoutent des délais et coûts incompressibles. Mutualiser avec "
        "d'autres opérateurs et anticiper les rotations en saison "
        "cyclonique sécurise les engagements clients.",
        territories=("martinique", "guadeloupe", "saint_martin",
                     "polynesie"),
    ),

    # ─── Industrie / artisanat Outre-Mer ───────────────────────────
    SectorRule(
        "industrie", "ind_dom_intrants", ">= 70",
        "important",
        "Production très dépendante d'intrants importés",
        "Au-delà de 70 % d'intrants importés, la marge est exposée aux "
        "hausses du fret et à l'octroi de mer. Sourcer une partie en "
        "local, ou produire pour le marché inter-îles, ouvre un relais "
        "de marge et de débouchés.",
        territories=("guyane", "martinique", "guadeloupe", "reunion",
                     "mayotte"),
    ),
    SectorRule(
        "artisanat", "art_dom_matiere", "scale_at_least:4",
        "recommande",
        "Matières premières fortement dépendantes du fret",
        "Le coût et le délai d'acheminement pèsent sur le prix et la "
        "planification. Quand c'est possible, valoriser des matières "
        "locales devient un avantage commercial (label terroir) et "
        "sécurise l'approvisionnement.",
        territories=("guyane", "martinique", "guadeloupe", "reunion",
                     "mayotte"),
    ),

    # ─── Numérique : opportunité export hors territoire ────────────
    SectorRule(
        "numerique", "num_dom_export", "<= 20",
        "recommande",
        "Activité concentrée sur le marché local",
        "Le numérique permet de dépasser l'étroitesse du marché local. "
        "Moins de 20 % de CA hors territoire signifie un fort "
        "potentiel de croissance externe inexploité (hexagone, "
        "international, autres DOM/COM).",
        territories=("guyane", "martinique", "guadeloupe", "reunion",
                     "mayotte", "polynesie", "nouvelle_caledonie"),
    ),

    # ─── Formation : dispositifs régionaux ─────────────────────────
    SectorRule(
        "formation", "for_dom_financement", "scale_at_least:4",
        "important",
        "Modèle dépendant des dispositifs régionaux",
        "Les fonds régionaux et FSE/FEDER conditionnent une grande "
        "part de l'activité formation outre-mer. Calendrier et "
        "critères évoluent : diversifier vers la formation B2B "
        "directement financée par les entreprises sécurise.",
        territories=("guyane", "martinique", "guadeloupe", "reunion",
                     "mayotte"),
    ),

    # ─── Association / ESS : dispositifs locaux ────────────────────
    SectorRule(
        "association", "asso_dom_dispositifs", "scale_at_least:4",
        "important",
        "Structure portée par les dispositifs locaux",
        "Politique de la ville, contrats aidés, FSE : ces dispositifs "
        "irriguent beaucoup de structures ultramarines. Une révision "
        "(cycle politique, budgétaire) peut déséquilibrer brutalement. "
        "Diversifier vers des ressources propres et plurifinanceurs.",
        territories=("guyane", "martinique", "guadeloupe", "reunion",
                     "mayotte"),
    ),
)


# ════════════════════════════════════════════════════════════════════
# Catalogue des "Repères de votre métier"
# ════════════════════════════════════════════════════════════════════
#
# Seuils par question métier, exposés dans le rapport pour donner au
# client une lecture directe ("Vous êtes dans la zone saine / à
# surveiller / de danger sur tel indicateur").
#
SECTOR_METRICS: tuple[SectorMetric, ...] = (
    # BTP
    SectorMetric("btp", "btp_taux_marge_chantier", "Marge nette par chantier",
                 higher_is_better=True, good=18, danger=10, unit="%"),
    SectorMetric("btp", "btp_depassement_budget", "Chantiers en dépassement",
                 higher_is_better=False, good=15, danger=30, unit="%"),
    SectorMetric("btp", "btp_delai_reglement_situations",
                 "Délai de paiement des situations",
                 higher_is_better=False, good=45, danger=75, unit="j"),
    # Restauration
    SectorMetric("restauration", "ratio_cout_matiere", "Food cost",
                 higher_is_better=False, good=30, danger=38, unit="%"),
    SectorMetric("restauration", "no_show_pct", "Taux de no-show",
                 higher_is_better=False, good=5, danger=12, unit="%"),
    SectorMetric("restauration", "rest_pertes_matiere", "Pertes matière",
                 higher_is_better=False, good=4, danger=8, unit="%"),
    SectorMetric("restauration", "rest_part_boisson", "Part boissons du ticket",
                 higher_is_better=True, good=28, danger=18, unit="%"),
    # E-commerce
    SectorMetric("ecommerce", "taux_conversion_web", "Taux de conversion site",
                 higher_is_better=True, good=2, danger=1, unit="%"),
    SectorMetric("ecommerce", "eco_panier_abandon", "Abandon de panier",
                 higher_is_better=False, good=65, danger=80, unit="%"),
    SectorMetric("ecommerce", "eco_delai_prepa", "Délai de préparation",
                 higher_is_better=False, good=24, danger=48, unit="h"),
    # Conseil / libéral
    SectorMetric("conseil", "cons_jours_factures_an", "Jours facturables / an",
                 higher_is_better=True, good=180, danger=140, unit="j"),
    SectorMetric("conseil", "cons_taux_realisation", "Taux de réalisation",
                 higher_is_better=True, good=85, danger=65, unit="%"),
    SectorMetric("conseil", "cons_temps_admin", "Temps administratif",
                 higher_is_better=False, good=20, danger=35, unit="%"),
    # Services Pro (B2B)
    SectorMetric("services_pro", "spro_cycle_vente", "Cycle de vente",
                 higher_is_better=False, good=45, danger=120, unit="j"),
    SectorMetric("services_pro", "spro_pipe_couverture",
                 "Couverture du pipeline",
                 higher_is_better=True, good=3, danger=1, unit="mois"),
    # Hôtellerie
    SectorMetric("hotellerie", "reservation_directe_pct",
                 "Part réservations directes",
                 higher_is_better=True, good=40, danger=20, unit="%"),
    SectorMetric("hotellerie", "hot_repeat_client", "Clients fidèles",
                 higher_is_better=True, good=25, danger=10, unit="%"),
    # Santé
    SectorMetric("sante", "sante_delai_rdv", "Délai de RDV",
                 higher_is_better=False, good=10, danger=30, unit="j"),
    SectorMetric("sante", "sante_part_actes_techniques",
                 "Actes à forte valeur",
                 higher_is_better=True, good=40, danger=20, unit="%"),
    # Beauté
    SectorMetric("beaute", "beau_taux_remplissage_agenda",
                 "Remplissage de l'agenda",
                 higher_is_better=True, good=75, danger=55, unit="%"),
    SectorMetric("beaute", "beau_clients_reguliers", "Clientes régulières",
                 higher_is_better=True, good=55, danger=30, unit="%"),
    # Commerce
    SectorMetric("commerce", "com_invendus_pct", "Démarque",
                 higher_is_better=False, good=5, danger=12, unit="%"),
    SectorMetric("commerce", "com_taux_transformation",
                 "Taux de transformation",
                 higher_is_better=True, good=25, danger=12, unit="sur 100"),
    # Industrie
    SectorMetric("industrie", "ind_taux_utilisation_machines",
                 "Utilisation des machines",
                 higher_is_better=True, good=75, danger=55, unit="%"),
    SectorMetric("industrie", "ind_taux_rebut", "Taux de rebut",
                 higher_is_better=False, good=2, danger=6, unit="%"),
    # Transport
    SectorMetric("transport", "tra_part_retour_vide", "Trajets à vide",
                 higher_is_better=False, good=15, danger=35, unit="%"),
    SectorMetric("transport", "tra_taux_ponctualite", "Ponctualité",
                 higher_is_better=True, good=96, danger=88, unit="%"),
    # Immobilier
    SectorMetric("immobilier", "immo_taux_occupation_parc",
                 "Occupation du parc",
                 higher_is_better=True, good=95, danger=85, unit="%"),
    SectorMetric("immobilier", "immo_taux_impayes", "Impayés",
                 higher_is_better=False, good=2, danger=6, unit="%"),
    # Formation
    SectorMetric("formation", "for_taux_remplissage_sessions",
                 "Remplissage des sessions",
                 higher_is_better=True, good=80, danger=55, unit="%"),
    # Numérique
    SectorMetric("numerique", "num_churn", "Churn annuel",
                 higher_is_better=False, good=8, danger=15, unit="%"),
    SectorMetric("numerique", "num_part_recurrent_saas", "CA récurrent",
                 higher_is_better=True, good=50, danger=20, unit="%"),
    # Association
    SectorMetric("association", "asso_part_autofinancement",
                 "Autofinancement",
                 higher_is_better=True, good=40, danger=20, unit="%"),
    # Événementiel
    SectorMetric("evenementiel", "eve_taux_marge_event",
                 "Marge nette par projet",
                 higher_is_better=True, good=25, danger=12, unit="%"),
    SectorMetric("evenementiel", "eve_acompte_signature",
                 "Acompte à la signature",
                 higher_is_better=True, good=40, danger=20, unit="%"),
)


# ════════════════════════════════════════════════════════════════════
# Évaluation — moteur de production des recommandations sectorielles
# ════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SectorRecommendation:
    """Recommandation sectorielle prête à fusionner avec celles du moteur universel."""

    priority: str
    title: str
    detail: str
    simulateur: str = ""
    sector: str = ""
    question_id: str = ""


def evaluate_sector_rules(
    answers: dict[str, Any],
    sector: Optional[str],
    profile: Optional[str] = None,
    *,
    territory: Optional[str] = None,
    max_rules: int = 4,
) -> list[SectorRecommendation]:
    """Évalue toutes les règles sectorielles applicables et retourne les
    recommandations déclenchées (limitées à ``max_rules`` pour ne pas
    noyer le rapport).

    Si ``sector`` est ``None`` ou inconnu, retourne une liste vide.
    Les règles avec ``territories`` filtrent sur le territoire fourni.
    """
    if not sector:
        return []
    triggered: list[SectorRecommendation] = []
    priority_rank = {"critique": 0, "important": 1, "recommande": 2, "bonus": 3}

    for rule in SECTOR_RULES:
        if rule.sector != sector:
            continue
        if rule.profiles and profile and profile not in rule.profiles:
            continue
        if rule.territories:
            # Si la règle est restreinte à des territoires, on doit avoir un
            # territoire ET il doit faire partie de la liste autorisée.
            if not territory or territory not in rule.territories:
                continue
        raw = answers.get(rule.question_id)
        if raw in (None, ""):
            continue
        if not _evaluate_condition(raw, rule.condition):
            continue
        # Substitution {value} — best-effort
        try:
            detail = rule.detail.format(value=raw)
        except (KeyError, IndexError, ValueError):
            detail = rule.detail
        triggered.append(SectorRecommendation(
            priority=rule.priority,
            title=rule.title,
            detail=detail,
            simulateur=rule.simulateur,
            sector=rule.sector,
            question_id=rule.question_id,
        ))

    triggered.sort(key=lambda r: priority_rank.get(r.priority, 99))
    return triggered[:max_rules]


# ════════════════════════════════════════════════════════════════════
# Évaluation — repères métier (pour l'encart du rapport)
# ════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SectorMetricResult:
    """Résultat d'évaluation d'un repère métier."""

    key: str
    label: str
    value: float | None
    unit: str
    status: str   # good | warn | danger | na
    direction: str  # "higher_is_better" | "lower_is_better"
    good: float
    danger: float

    @property
    def color(self) -> str:
        return {
            "good": "#30d158", "warn": "#ff9f0a",
            "danger": "#ff453a", "na": "#8e8e93",
        }[self.status]


def evaluate_sector_metrics(
    answers: dict[str, Any],
    sector: Optional[str],
) -> list[SectorMetricResult]:
    """Évalue les repères métier renseignés pour le secteur donné.

    Les questions non répondues sont simplement ignorées (pas de "na" affiché),
    pour ne montrer dans le rapport que les indicateurs concrètement mesurés.
    """
    if not sector:
        return []
    out: list[SectorMetricResult] = []
    for metric in SECTOR_METRICS:
        if metric.sector != sector:
            continue
        value = _num(answers, metric.question_id)
        if value is None:
            continue
        if metric.higher_is_better:
            if value >= metric.good:
                status = "good"
            elif value <= metric.danger:
                status = "danger"
            else:
                status = "warn"
        else:
            if value <= metric.good:
                status = "good"
            elif value >= metric.danger:
                status = "danger"
            else:
                status = "warn"
        out.append(SectorMetricResult(
            key=metric.question_id,
            label=metric.label,
            value=value,
            unit=metric.unit,
            status=status,
            direction=("higher_is_better" if metric.higher_is_better
                       else "lower_is_better"),
            good=metric.good,
            danger=metric.danger,
        ))
    return out


__all__ = [
    "SectorRule",
    "SectorMetric",
    "SectorRecommendation",
    "SectorMetricResult",
    "SECTOR_RULES",
    "SECTOR_METRICS",
    "evaluate_sector_rules",
    "evaluate_sector_metrics",
]
