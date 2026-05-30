"""Calibration territoriale du diagnostic terrain — Outre-Mer & hexagone.

Ce module est la **source unique de vérité** pour intégrer la dimension
territoriale dans le diagnostic, au-delà du secteur. Il complète
:mod:`apps.diagnostic.sector_calibration` (qui ajuste par secteur) avec
des ajustements territoriaux propres aux DOM, COM et à l'hexagone.

Pourquoi ce niveau ?
- L'octroi de mer, le fret maritime, la saison cyclonique, la dépendance
  à la desserte aérienne, les dispositifs fiscaux DOM (Girardin, ZFANG…)
  changent radicalement les seuils de risque et les leviers d'action.
- Une "PME BTP" en Guyane n'a pas le même profil de risque qu'une "PME BTP"
  en Île-de-France — cf. carnet de commandes, retenues de garantie,
  matériaux importés, DSO de la commande publique locale.
- Les recommandations doivent être ancrées dans la réalité du terrain :
  proposer "diversifier les fournisseurs" en métropole vs "sécuriser un
  stock tampon avant la saison cyclonique" outre-mer.

Limitations assumées :
- La calibration est qualitative (à dire d'expert TUS), à recalibrer
  avec des cas réels et données INSEE/IEDOM/CCI sur la durée.
- Aucune dépendance externe : tout est en données statiques auditables.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ════════════════════════════════════════════════════════════════════
# Référentiel des territoires
# ════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Territory:
    """Description d'un territoire du diagnostic TUS."""

    code: str           # slug stable (DB-friendly)
    label: str
    region_kind: str    # "DOM" | "COM" | "HEXAGONE" | "AUTRE"
    is_outre_mer: bool
    insularity: str     # "ile" | "continent" | "archipel" | "hexagone"
    cyclonic_season: bool
    octroi_de_mer: bool
    intra_eu: bool
    notes: str = ""


TERRITORIES: tuple[Territory, ...] = (
    # ─── DOM (5) ─────────────────────────────────────────────────────
    Territory(
        "guyane", "Guyane", "DOM",
        is_outre_mer=True, insularity="continent",
        cyclonic_season=False, octroi_de_mer=True, intra_eu=True,
        notes="Continent sud-américain. TVA non applicable (art. 294 CGI). "
              "Saison des pluies marquée. Marché intérieur étroit, "
              "forte commande publique.",
    ),
    Territory(
        "martinique", "Martinique", "DOM",
        is_outre_mer=True, insularity="ile",
        cyclonic_season=True, octroi_de_mer=True, intra_eu=True,
        notes="Île, marché concentré. Saison cyclonique juin-novembre. "
              "Tourisme et services dominent.",
    ),
    Territory(
        "guadeloupe", "Guadeloupe", "DOM",
        is_outre_mer=True, insularity="archipel",
        cyclonic_season=True, octroi_de_mer=True, intra_eu=True,
        notes="Archipel, dépendance à la desserte inter-îles. "
              "Saison cyclonique juin-novembre. Tourisme structurant.",
    ),
    Territory(
        "reunion", "La Réunion", "DOM",
        is_outre_mer=True, insularity="ile",
        cyclonic_season=True, octroi_de_mer=True, intra_eu=True,
        notes="Île volcanique, marché plus large que les Antilles. "
              "Saison cyclonique novembre-avril. Industrie agroalimentaire "
              "et tourisme.",
    ),
    Territory(
        "mayotte", "Mayotte", "DOM",
        is_outre_mer=True, insularity="ile",
        cyclonic_season=True, octroi_de_mer=True, intra_eu=True,
        notes="Île de l'océan Indien. TVA non applicable (art. 294 CGI). "
              "Marché émergent, infrastructures en développement.",
    ),

    # ─── COM (4 principaux) ─────────────────────────────────────────
    Territory(
        "saint_martin", "Saint-Martin", "COM",
        is_outre_mer=True, insularity="ile",
        cyclonic_season=True, octroi_de_mer=False, intra_eu=False,
        notes="COM. Régime fiscal local distinct, marché tourisme dominant.",
    ),
    Territory(
        "saint_barth", "Saint-Barthélemy", "COM",
        is_outre_mer=True, insularity="ile",
        cyclonic_season=True, octroi_de_mer=False, intra_eu=False,
        notes="COM. Régime fiscal local. Marché de niche, tourisme haut de gamme.",
    ),
    Territory(
        "polynesie", "Polynésie française", "COM",
        is_outre_mer=True, insularity="archipel",
        cyclonic_season=True, octroi_de_mer=False, intra_eu=False,
        notes="Pays d'outre-mer. Fiscalité propre (TVA spécifique, droits "
              "de douane locaux). Archipel très étendu.",
    ),
    Territory(
        "nouvelle_caledonie", "Nouvelle-Calédonie", "COM",
        is_outre_mer=True, insularity="ile",
        cyclonic_season=True, octroi_de_mer=False, intra_eu=False,
        notes="Sui generis. Fiscalité locale. Industrie minière structurante.",
    ),

    # ─── HEXAGONE / AUTRE ───────────────────────────────────────────
    Territory(
        "hexagone", "France hexagonale", "HEXAGONE",
        is_outre_mer=False, insularity="continent",
        cyclonic_season=False, octroi_de_mer=False, intra_eu=True,
        notes="France métropolitaine.",
    ),
    Territory(
        "corse", "Corse", "HEXAGONE",
        is_outre_mer=False, insularity="ile",
        cyclonic_season=False, octroi_de_mer=False, intra_eu=True,
        notes="Région insulaire métropolitaine. Saisonnalité touristique forte.",
    ),
    Territory(
        "autre", "Autre / Non précisé", "AUTRE",
        is_outre_mer=False, insularity="hexagone",
        cyclonic_season=False, octroi_de_mer=False, intra_eu=True,
        notes="Territoire non précisé : aucune calibration territoriale.",
    ),
)


# Index O(1) pour lookup ─────────────────────────────────────────────
_BY_CODE: dict[str, Territory] = {t.code: t for t in TERRITORIES}


def get_territory(code: Optional[str]) -> Optional[Territory]:
    """Retourne un :class:`Territory` ou None si code absent / inconnu."""
    if not code:
        return None
    return _BY_CODE.get(code)


def territory_choices() -> list[tuple[str, str]]:
    """Choices Django, dans l'ordre du référentiel (DOM → COM → hexagone → autre)."""
    return [(t.code, t.label) for t in TERRITORIES]


def is_outre_mer(code: Optional[str]) -> bool:
    """Raccourci : True si DOM ou COM."""
    t = get_territory(code)
    return bool(t and t.is_outre_mer)


# ════════════════════════════════════════════════════════════════════
# Ajustements territoriaux des seuils KPI
# ════════════════════════════════════════════════════════════════════
#
# Logique : par-dessus la calibration sectorielle (Palier 2), on applique
# une couche territoriale qui assouplit ou durcit certains seuils selon
# la réalité du terrain (commande publique DOM, fret, désserte...).
#
# Format : (delta_good, delta_danger). delta positif sur un KPI
# "lower_is_better" rend le seuil plus tolérant (par ex. +15 sur le DSO
# = on accepte 15 jours de plus avant de basculer en zone d'alerte).
#
TERRITORY_KPI_ADJUSTMENTS: dict[str, dict[str, tuple[float, float]]] = {
    # DSO : la commande publique en DOM paie traditionnellement plus tard.
    "dso": {
        "guyane": (+15, +20),
        "martinique": (+10, +15),
        "guadeloupe": (+10, +15),
        "reunion": (+10, +15),
        "mayotte": (+15, +20),
        "polynesie": (+10, +20),
        "nouvelle_caledonie": (+10, +20),
        # Hexagone, COM riches : pas d'ajustement (delta 0).
    },
    # Matelas de trésorerie : exigence accrue Outre-Mer (saison cyclonique,
    # ruptures fret) — on attend plus de mois de couverture pour être "sain".
    "matelas": {
        "guyane": (+1, +0),       # good: 4 mois (vs 3) ; danger inchangé
        "martinique": (+1, +0),
        "guadeloupe": (+1, +0),
        "reunion": (+1, +0),
        "mayotte": (+2, +0),      # marché plus fragile : 5 mois recommandés
        "saint_martin": (+1, +0),
        "saint_barth": (+1, +0),
        "polynesie": (+2, +0),
        "nouvelle_caledonie": (+1, +0),
    },
    # Couverture des charges fixes : un peu plus de tolérance Outre-Mer
    # car les charges fixes y sont structurellement plus élevées (loyers,
    # logistique, énergie).
    "couverture": {
        "guyane": (+5, +5),
        "martinique": (+3, +3),
        "guadeloupe": (+3, +3),
        "reunion": (+3, +3),
        "mayotte": (+5, +5),
        "polynesie": (+5, +5),
        "nouvelle_caledonie": (+3, +3),
    },
}


def apply_territory_threshold_adjustment(
    kpi_key: str,
    territory_code: Optional[str],
    base_thresholds: tuple[float, float],
) -> tuple[float, float]:
    """Applique l'ajustement territorial sur un couple (good, danger).

    Si pas de territoire ou pas d'ajustement défini, renvoie le tuple
    inchangé. C'est le comportement par défaut (rétro-compat).
    """
    if not territory_code:
        return base_thresholds
    adjustments = TERRITORY_KPI_ADJUSTMENTS.get(kpi_key)
    if not adjustments:
        return base_thresholds
    delta = adjustments.get(territory_code)
    if not delta:
        return base_thresholds
    delta_good, delta_danger = delta
    good, danger = base_thresholds
    return (good + delta_good, danger + delta_danger)


# ════════════════════════════════════════════════════════════════════
# Score de résilience territoriale
# ════════════════════════════════════════════════════════════════════
#
# Synthèse /100 des questions DOM-spécifiques (`*_dom_*`) qui mesure la
# capacité de l'entreprise à absorber les chocs territoriaux : fret,
# octroi de mer, dépendance désserte, dispositifs locaux, etc.
#
# Indépendant du score global (ne le pollue pas) — exposé en complément.

@dataclass(frozen=True)
class TerritorialResilience:
    """Résultat compact de l'évaluation de résilience territoriale."""

    score: int                              # 0..100
    label: str                              # Solide / Sain / Fragile / Critique
    color: str
    facets: tuple[dict[str, object], ...]   # détail par facette mesurée
    notes: tuple[str, ...]                  # messages clés


# Mapping question DOM → poids dans le score de résilience.
# Toutes les questions DOM ne pèsent pas pareil : la dépendance fret /
# octroi de mer est plus structurante que l'exposition aux dispositifs
# fiscaux par exemple.
DOM_QUESTION_WEIGHTS: dict[str, dict[str, object]] = {
    # Format : qid → {weight, kind, scale_invert (si scale)}
    # kind ∈ {"percent_lower_better", "percent_higher_better",
    #         "scale_lower_better", "scale_higher_better"}
    "com_dom_import":          {"weight": 1.0, "kind": "percent_lower_better"},
    "eco_dom_logistique":      {"weight": 0.8, "kind": "scale_lower_better"},
    "rest_dom_appro":          {"weight": 1.0, "kind": "percent_lower_better"},
    "hot_dom_clientele":       {"weight": 0.6, "kind": "percent_lower_better"},
    "tou_dom_desserte":        {"weight": 1.0, "kind": "scale_lower_better"},
    "spro_dom_marche":         {"weight": 0.6, "kind": "scale_lower_better"},
    "spart_dom_pouvoir_achat": {"weight": 0.6, "kind": "scale_lower_better"},
    "cons_dom_concentration":  {"weight": 0.6, "kind": "scale_lower_better"},
    "sante_dom_appro":         {"weight": 0.8, "kind": "scale_lower_better"},
    "beau_dom_produits":       {"weight": 0.6, "kind": "scale_lower_better"},
    "art_dom_matiere":         {"weight": 0.8, "kind": "scale_lower_better"},
    "btp_dom_materiaux":       {"weight": 1.0, "kind": "percent_lower_better"},
    "ind_dom_intrants":        {"weight": 1.0, "kind": "percent_lower_better"},
    "tra_dom_inter_iles":      {"weight": 1.0, "kind": "scale_lower_better"},
    "immo_dom_defisc":         {"weight": 0.6, "kind": "percent_lower_better"},
    "for_dom_financement":     {"weight": 0.8, "kind": "scale_lower_better"},
    "eve_dom_prestataires":    {"weight": 0.6, "kind": "scale_lower_better"},
    "agro_dom_aides":          {"weight": 0.6, "kind": "percent_lower_better"},
    "num_dom_export":          {"weight": 0.8, "kind": "percent_higher_better"},
    "asso_dom_dispositifs":    {"weight": 0.6, "kind": "scale_lower_better"},
    "autre_dom_contraintes":   {"weight": 0.8, "kind": "scale_lower_better"},
    # Réalités universelles ultramarines (déjà dans le catalogue questions)
    "exposition_import":       {"weight": 0.8, "kind": "scale_lower_better"},
}


def _question_to_facet_score(qid: str, raw_value) -> Optional[float]:
    """Transforme une réponse brute en score /10 pour la résilience.

    Renvoie None si la valeur est manquante ou invalide.
    """
    if raw_value in (None, ""):
        return None
    spec = DOM_QUESTION_WEIGHTS.get(qid)
    if not spec:
        return None
    try:
        v = float(str(raw_value).replace(",", "."))
    except (TypeError, ValueError):
        return None
    kind = spec["kind"]
    # Nous voulons : 10 = très résilient, 0 = très exposé.
    if kind == "percent_lower_better":
        # 0% imports = résilience max, 100% = exposition max
        return max(0.0, min(10.0, (100 - v) / 10))
    if kind == "percent_higher_better":
        return max(0.0, min(10.0, v / 10))
    if kind == "scale_lower_better":
        # Échelle 1..5 où 5 = très exposé
        return max(0.0, min(10.0, (5 - v) / 4 * 10))
    if kind == "scale_higher_better":
        return max(0.0, min(10.0, (v - 1) / 4 * 10))
    return None


def _resilience_label(score: int) -> tuple[str, str]:
    """Verdict associé au score /100."""
    if score >= 75:
        return "Solide", "#30d158"
    if score >= 55:
        return "Sain", "#9acd32"
    if score >= 35:
        return "Fragile", "#ff9f0a"
    return "Critique", "#ff453a"


def compute_territorial_resilience(
    answers: dict[str, object],
    territory_code: Optional[str],
) -> Optional[TerritorialResilience]:
    """Calcule la résilience territoriale /100 à partir des réponses DOM.

    Renvoie ``None`` si :
    - aucun territoire fourni, OU
    - territoire non outre-mer (le score n'a pas de sens hexagone),
    - aucune question DOM n'a été répondue.

    Le score reste **indépendant** du score global : c'est un complément
    qualitatif, pas un correctif.
    """
    if not is_outre_mer(territory_code):
        return None

    facets: list[dict[str, object]] = []
    weighted_sum = 0.0
    total_weight = 0.0

    for qid, spec in DOM_QUESTION_WEIGHTS.items():
        if qid not in answers:
            continue
        score10 = _question_to_facet_score(qid, answers.get(qid))
        if score10 is None:
            continue
        weight = float(spec["weight"])
        weighted_sum += score10 * weight
        total_weight += weight
        facets.append({
            "key": qid,
            "score10": round(score10, 1),
            "weight": weight,
        })

    if total_weight == 0:
        return None

    score100 = int(round(weighted_sum / total_weight * 10))
    label, color = _resilience_label(score100)

    notes: list[str] = []
    territory = get_territory(territory_code)
    if territory and territory.cyclonic_season:
        notes.append(
            "Saison cyclonique : prévoir un plan de continuité d'activité "
            "(stock tampon, sauvegarde site, polices d'assurance adaptées)."
        )
    if territory and territory.octroi_de_mer:
        notes.append(
            "Octroi de mer applicable : intégrer le coût et les délais "
            "d'acheminement dans tout chiffrage et clause de révision."
        )
    if territory and territory.insularity in ("ile", "archipel"):
        notes.append(
            "Insularité : sécuriser un fournisseur secondaire et un stock "
            "minimum pour absorber les ruptures de fret."
        )

    return TerritorialResilience(
        score=score100,
        label=label,
        color=color,
        facets=tuple(facets),
        notes=tuple(notes),
    )


__all__ = [
    "Territory",
    "TerritorialResilience",
    "TERRITORIES",
    "TERRITORY_KPI_ADJUSTMENTS",
    "DOM_QUESTION_WEIGHTS",
    "get_territory",
    "territory_choices",
    "is_outre_mer",
    "apply_territory_threshold_adjustment",
    "compute_territorial_resilience",
]
