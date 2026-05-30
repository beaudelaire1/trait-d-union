"""Calibration sectorielle du moteur de scoring — Diagnostic terrain v2.

Ce module est la **source unique de vérité** pour adapter le scoring au
secteur d'activité. Il complète :class:`apps.diagnostic.field_scoring`
sans dupliquer sa logique.

Deux dimensions de calibration :

1. **Pondérations des domaines** (poids dans le score /100).
   Pour un même profil "PME", le poids de chaque domaine peut varier selon
   le secteur : en BTP les risques pèsent plus lourd, en restauration
   l'organisation est cruciale, en e-commerce le commercial est central.

2. **Seuils des KPIs vitaux** (good / danger).
   Un DSO de 60 jours est normal en BTP (commande publique) mais
   catastrophique en e-commerce. La marge brute attendue d'un cabinet de
   conseil est très différente de celle d'un BTP. Les seuils universels
   sont calibrés métropole "moyenne" — on les ajuste secteur par secteur.

Principe :
- Aucun seuil ni pondération sectorielle n'écrase silencieusement les
  valeurs universelles : l'absence dans la matrice = fallback explicite.
- Les profils sans surcharge sectorielle utilisent la matrice universelle
  héritée de field_scoring.DOMAIN_WEIGHTS.

Versionning :
- ``SCORING_VERSION`` est tracé dans les résultats (results['scoring_version']).
- v1 = pondérations + seuils universels (legacy)
- v2 = calibration sectorielle (Paliers 1+2)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


SCORING_VERSION = 2


# ════════════════════════════════════════════════════════════════════
# PALIER 1 — Pondérations des domaines par couple (profil × secteur)
# ════════════════════════════════════════════════════════════════════
#
# Lecture :
#   DOMAIN_WEIGHTS_BY_SECTOR[<sector>][<profile>][<domain>] = poids (0..1)
#
# Règles :
# - Pour un secteur donné, on peut surcharger UN OU PLUSIEURS profils.
# - La somme des poids d'un profil DOIT valoir 1.0 (vérifié au démarrage).
# - Tout secteur/profil non défini ici → fallback sur DOMAIN_WEIGHTS
#   (matrice universelle de field_scoring).
#
# Justifications par secteur (résumé) :
#
#   BTP            : risques (intempéries, retenues, octroi de mer en DOM)
#                    et finance (DSO long, encours élevés) sont structurants.
#   Restauration   : organisation (food cost, no-show, rotation) prime,
#                    finance reste forte (marges fines).
#   E-commerce     : commercial (CAC, conversion, marketplaces) domine.
#   Conseil/B2B    : stratégie (positionnement, niche) et risques
#                    (concentration sectorielle, prescription).
#   Hôtellerie     : organisation (taux d'occupation, RevPAR) +
#                    commercial (réservations directes vs OTA).
#   Santé          : organisation (capacité, agenda) + finance (mix conv).
#   Transport      : finance (coût/km) + risques (carburant, ponctualité).
#   Industrie      : organisation (utilisation machines) + risques
#                    (matières premières, export).
#   Immobilier     : commercial (mandats, transformation) + finance
#                    (transactions vs gestion).
#   Services part. : organisation (capacité RDV) + commercial (réachat).
#
DOMAIN_WEIGHTS_BY_SECTOR: dict[str, dict[str, dict[str, float]]] = {
    "btp": {
        "solo": {
            "finance": 0.32, "commercial": 0.18, "organisation": 0.20,
            "strategie": 0.10, "risques": 0.20,
        },
        "tpe": {
            "finance": 0.30, "commercial": 0.18, "organisation": 0.18,
            "strategie": 0.10, "risques": 0.24,
        },
        "pme": {
            "finance": 0.28, "commercial": 0.18, "organisation": 0.18,
            "strategie": 0.12, "risques": 0.24,
        },
        "croissance": {
            "finance": 0.25, "commercial": 0.20, "organisation": 0.20,
            "strategie": 0.15, "risques": 0.20,
        },
    },
    "restauration": {
        "solo": {
            "finance": 0.30, "commercial": 0.20, "organisation": 0.30,
            "strategie": 0.10, "risques": 0.10,
        },
        "tpe": {
            "finance": 0.27, "commercial": 0.18, "organisation": 0.30,
            "strategie": 0.12, "risques": 0.13,
        },
        "pme": {
            "finance": 0.27, "commercial": 0.17, "organisation": 0.28,
            "strategie": 0.13, "risques": 0.15,
        },
    },
    "ecommerce": {
        "solo": {
            "finance": 0.25, "commercial": 0.32, "organisation": 0.18,
            "strategie": 0.13, "risques": 0.12,
        },
        "tpe": {
            "finance": 0.25, "commercial": 0.30, "organisation": 0.18,
            "strategie": 0.15, "risques": 0.12,
        },
        "pme": {
            "finance": 0.25, "commercial": 0.30, "organisation": 0.18,
            "strategie": 0.15, "risques": 0.12,
        },
        "croissance": {
            "finance": 0.22, "commercial": 0.30, "organisation": 0.18,
            "strategie": 0.18, "risques": 0.12,
        },
    },
    "conseil": {
        "solo": {
            "finance": 0.28, "commercial": 0.20, "organisation": 0.20,
            "strategie": 0.22, "risques": 0.10,
        },
        "tpe": {
            "finance": 0.27, "commercial": 0.20, "organisation": 0.18,
            "strategie": 0.22, "risques": 0.13,
        },
        "pme": {
            "finance": 0.25, "commercial": 0.20, "organisation": 0.18,
            "strategie": 0.22, "risques": 0.15,
        },
    },
    "services_pro": {
        "solo": {
            "finance": 0.28, "commercial": 0.22, "organisation": 0.20,
            "strategie": 0.20, "risques": 0.10,
        },
        "tpe": {
            "finance": 0.27, "commercial": 0.22, "organisation": 0.20,
            "strategie": 0.18, "risques": 0.13,
        },
        "pme": {
            "finance": 0.25, "commercial": 0.22, "organisation": 0.20,
            "strategie": 0.18, "risques": 0.15,
        },
    },
    "hotellerie": {
        "solo": {
            "finance": 0.27, "commercial": 0.22, "organisation": 0.27,
            "strategie": 0.12, "risques": 0.12,
        },
        "tpe": {
            "finance": 0.25, "commercial": 0.22, "organisation": 0.28,
            "strategie": 0.13, "risques": 0.12,
        },
        "pme": {
            "finance": 0.25, "commercial": 0.22, "organisation": 0.26,
            "strategie": 0.14, "risques": 0.13,
        },
    },
    "sante": {
        "solo": {
            "finance": 0.30, "commercial": 0.15, "organisation": 0.30,
            "strategie": 0.15, "risques": 0.10,
        },
        "tpe": {
            "finance": 0.27, "commercial": 0.15, "organisation": 0.30,
            "strategie": 0.16, "risques": 0.12,
        },
        "pme": {
            "finance": 0.25, "commercial": 0.15, "organisation": 0.30,
            "strategie": 0.17, "risques": 0.13,
        },
    },
    "transport": {
        "solo": {
            "finance": 0.32, "commercial": 0.18, "organisation": 0.20,
            "strategie": 0.10, "risques": 0.20,
        },
        "tpe": {
            "finance": 0.30, "commercial": 0.18, "organisation": 0.20,
            "strategie": 0.10, "risques": 0.22,
        },
        "pme": {
            "finance": 0.28, "commercial": 0.18, "organisation": 0.20,
            "strategie": 0.12, "risques": 0.22,
        },
    },
    "industrie": {
        "tpe": {
            "finance": 0.27, "commercial": 0.18, "organisation": 0.25,
            "strategie": 0.13, "risques": 0.17,
        },
        "pme": {
            "finance": 0.25, "commercial": 0.18, "organisation": 0.25,
            "strategie": 0.15, "risques": 0.17,
        },
        "croissance": {
            "finance": 0.22, "commercial": 0.20, "organisation": 0.23,
            "strategie": 0.18, "risques": 0.17,
        },
    },
    "immobilier": {
        "tpe": {
            "finance": 0.28, "commercial": 0.27, "organisation": 0.18,
            "strategie": 0.15, "risques": 0.12,
        },
        "pme": {
            "finance": 0.27, "commercial": 0.25, "organisation": 0.18,
            "strategie": 0.17, "risques": 0.13,
        },
    },
    "services_part": {
        "solo": {
            "finance": 0.28, "commercial": 0.25, "organisation": 0.25,
            "strategie": 0.12, "risques": 0.10,
        },
        "tpe": {
            "finance": 0.27, "commercial": 0.23, "organisation": 0.25,
            "strategie": 0.13, "risques": 0.12,
        },
    },
    "agro": {
        "solo": {
            "finance": 0.30, "commercial": 0.18, "organisation": 0.18,
            "strategie": 0.12, "risques": 0.22,
        },
        "tpe": {
            "finance": 0.28, "commercial": 0.18, "organisation": 0.20,
            "strategie": 0.12, "risques": 0.22,
        },
    },
    "tourisme": {
        "solo": {
            "finance": 0.27, "commercial": 0.22, "organisation": 0.20,
            "strategie": 0.13, "risques": 0.18,
        },
        "tpe": {
            "finance": 0.25, "commercial": 0.22, "organisation": 0.20,
            "strategie": 0.15, "risques": 0.18,
        },
    },
}


# ════════════════════════════════════════════════════════════════════
# PALIER 2 — Seuils sectoriels des KPIs vitaux
# ════════════════════════════════════════════════════════════════════
#
# Lecture :
#   KPI_THRESHOLDS_BY_SECTOR[<kpi_key>][<sector>] = (good, danger)
#
# Sémantique :
# - Pour les KPIs où "plus c'est élevé, mieux c'est" (marge, conversion,
#   récurrence, capacité_facturable, matelas), on lit (good >= , danger <=).
# - Pour les KPIs où "plus c'est bas, mieux c'est" (DSO, couverture,
#   dependance_client), on lit (good <= , danger >=).
# - Une valeur ``None`` au lieu d'un tuple signifie "KPI non pertinent
#   pour ce secteur" (ex. DSO en restauration au comptoir) et doit être
#   masqué dans le rapport.
# - Tout secteur absent → fallback aux seuils universels de field_scoring.
#
KPI_THRESHOLDS_BY_SECTOR: dict[str, dict[str, Optional[tuple[float, float]]]] = {
    # ── DSO (jours, plus c'est bas mieux c'est) ──────────────────────
    "dso": {
        # BTP / commande publique : 60-75 j est la norme, 90+ devient critique.
        "btp": (45.0, 90.0),
        "industrie": (45.0, 75.0),
        "transport": (40.0, 75.0),
        # Services intellectuels B2B : norme = 30-45 j
        "services_pro": (30.0, 60.0),
        "conseil": (30.0, 60.0),
        # E-commerce B2C : paiement immédiat — au-delà de 7 j c'est anormal
        "ecommerce": (7.0, 30.0),
        # Commerce / restauration / beauté / hôtellerie : transactionnel,
        # le KPI DSO n'a pas vraiment de sens (paiement à la commande).
        "commerce": None,
        "restauration": None,
        "beaute": None,
        "hotellerie": None,
        "tourisme": None,
        # Santé conventionné : remboursements caisses ~30-45 j
        "sante": (30.0, 60.0),
        "immobilier": (30.0, 60.0),
        "evenementiel": (30.0, 60.0),
        "agro": (30.0, 75.0),
        "association": (45.0, 90.0),  # subventions souvent en retard
    },

    # ── Marge brute (%, plus c'est élevé mieux c'est) ───────────────
    # Note : universel = good=50, danger=30. On ajuste selon les normes.
    "marge_brute": {
        # BTP / industrie : marge brute typique 25-35 %
        "btp": (35.0, 15.0),
        "industrie": (35.0, 18.0),
        "transport": (30.0, 15.0),
        # Restauration : food cost autour de 30 % → marge brute 60-70 %
        "restauration": (65.0, 50.0),
        # Hôtellerie : marge brute ~70-80 % (services prédominants)
        "hotellerie": (70.0, 55.0),
        # Conseil / services intellectuels : marge brute très élevée
        "conseil": (75.0, 55.0),
        "services_pro": (65.0, 45.0),
        "numerique": (70.0, 50.0),
        # Commerce de détail : 30-40 % typique, 25 % seuil bas
        "commerce": (40.0, 25.0),
        # E-commerce : 35-45 % pour rester rentable après acquisition
        "ecommerce": (40.0, 25.0),
        "beaute": (60.0, 40.0),
        "sante": (65.0, 45.0),
        "evenementiel": (45.0, 25.0),
        "artisanat": (50.0, 30.0),
    },

    # ── Couverture des charges fixes (% — plus c'est bas mieux c'est) ─
    # Universel : good=70%, danger=85%
    "couverture": {
        # Activités à charges fixes lourdes (loyer, masse salariale) :
        # plus de tolérance.
        "restauration": (75.0, 90.0),
        "hotellerie": (75.0, 92.0),
        "industrie": (72.0, 88.0),
        # Services intellectuels : faibles charges fixes hors salaires →
        # exigence plus stricte.
        "conseil": (65.0, 80.0),
        "services_pro": (65.0, 80.0),
        "numerique": (65.0, 80.0),
        # E-commerce : charges fixes faibles, exigence stricte.
        "ecommerce": (60.0, 80.0),
    },

    # ── Dépendance au plus gros client (% — plus c'est bas mieux c'est) ─
    # Universel : good=20%, danger=30%
    "dependance_client": {
        # B2B projets longs : tolérance plus large historiquement.
        "btp": (25.0, 40.0),
        "services_pro": (25.0, 40.0),
        "conseil": (25.0, 40.0),
        "industrie": (25.0, 45.0),
        # B2C diffus : KPI non pertinent (cf. SECTEURS_CLIENTELE_DIFFUSE
        # dans field_questions). On le marque None pour cohérence.
        "commerce": None,
        "ecommerce": None,
        "restauration": None,
        "beaute": None,
        "hotellerie": None,
        "tourisme": None,
        "sante": None,
    },
}


# ════════════════════════════════════════════════════════════════════
# Helpers — accès défensif, fallback systématique
# ════════════════════════════════════════════════════════════════════

def get_domain_weights(profile: str, sector: Optional[str] = None) -> Optional[dict[str, float]]:
    """Retourne la pondération des domaines à utiliser.

    Returns None si aucune surcharge sectorielle n'existe — l'appelant doit
    alors retomber sur :data:`field_scoring.DOMAIN_WEIGHTS`.
    """
    if not sector:
        return None
    by_sector = DOMAIN_WEIGHTS_BY_SECTOR.get(sector)
    if not by_sector:
        return None
    return by_sector.get(profile)


def get_kpi_thresholds(kpi_key: str, sector: Optional[str] = None) -> Optional[tuple[float, float]]:
    """Retourne les seuils sectoriels (good, danger) pour un KPI.

    Returns ``None`` si :
    - aucun secteur fourni
    - le KPI n'a pas de surcharge sectorielle
    L'appelant doit alors retomber sur les seuils universels.

    Returns la chaîne sentinelle ``"hidden"`` (cast en tuple ``(None, None)``)
    si le KPI est explicitement non pertinent pour ce secteur. À ce
    moment-là l'appelant peut décider de masquer le KPI du rapport.
    """
    if not sector:
        return None
    kpi_map = KPI_THRESHOLDS_BY_SECTOR.get(kpi_key)
    if not kpi_map:
        return None
    if sector not in kpi_map:
        return None
    return kpi_map[sector]  # peut être None (KPI non pertinent)


def is_kpi_hidden(kpi_key: str, sector: Optional[str]) -> bool:
    """Indique si un KPI est explicitement non pertinent pour le secteur."""
    if not sector:
        return False
    kpi_map = KPI_THRESHOLDS_BY_SECTOR.get(kpi_key)
    if not kpi_map:
        return False
    return sector in kpi_map and kpi_map[sector] is None


@dataclass(frozen=True)
class SectorContext:
    """Contexte sectoriel agrégé pour le moteur de scoring."""

    sector: Optional[str]
    weights: Optional[dict[str, float]]  # None = utiliser DOMAIN_WEIGHTS

    @classmethod
    def for_(cls, profile: str, sector: Optional[str]) -> "SectorContext":
        return cls(sector=sector or None, weights=get_domain_weights(profile, sector))


# ── Validation au chargement ────────────────────────────────────────
def _validate_weights() -> None:
    """Vérifie que les pondérations sectorielles somment bien à ~1.0."""
    tolerance = 0.001
    for sector, by_profile in DOMAIN_WEIGHTS_BY_SECTOR.items():
        for profile, weights in by_profile.items():
            total = sum(weights.values())
            if abs(total - 1.0) > tolerance:
                raise ValueError(
                    f"DOMAIN_WEIGHTS_BY_SECTOR[{sector!r}][{profile!r}] : "
                    f"somme = {total:.4f} (attendu 1.0)."
                )


_validate_weights()


__all__ = [
    "SCORING_VERSION",
    "DOMAIN_WEIGHTS_BY_SECTOR",
    "KPI_THRESHOLDS_BY_SECTOR",
    "SectorContext",
    "get_domain_weights",
    "get_kpi_thresholds",
    "is_kpi_hidden",
]
