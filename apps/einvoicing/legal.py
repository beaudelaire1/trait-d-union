"""
Régimes TVA supportés par TUS — source unique de vérité.

Tout le code applicatif (templates PDF, builder CII, admin) doit consommer
ces helpers et JAMAIS écrire de mention légale en dur. Cela permet de :

- adapter automatiquement la mention au régime configuré (`VAT_REGIME`);
- déduire la catégorie TVA EN 16931 par défaut (S/E/O/AE...) ;
- déduire le motif d'exemption VATEX par défaut.

Régimes connus :

- ``STANDARD``               : assujetti normal, TVA collectée sur les factures.
- ``FRANCHISE``              : franchise en base TVA (art. 293 B du CGI).
                               Métropole, micro-entreprise sous seuils.
- ``DOM_GUYANE_MAYOTTE``     : TVA provisoirement non applicable
                               (art. 294 du CGI). Cas TUS (Guyane).
- ``EXEMPT_OTHER``           : autre exonération (cas particuliers).

Nota : Guadeloupe / Martinique / Réunion sont assujettis à la TVA (taux
réduits) — ne PAS confondre avec ``DOM_GUYANE_MAYOTTE``.
"""

from __future__ import annotations

from typing import Optional

from django.conf import settings


# ---------------------------------------------------------------------------
# Table de référence
# ---------------------------------------------------------------------------
_REGIMES: dict[str, dict[str, str]] = {
    "STANDARD": {
        "mention": "",
        "vat_category": "S",
        "vatex_code": "",
        "label": "Régime normal de TVA",
    },
    "FRANCHISE": {
        # Métropole, art. 293 B (micro-entreprise)
        "mention": "TVA non applicable, art. 293 B du CGI",
        "vat_category": "E",
        "vatex_code": "VATEX-EU-79-C",
        "label": "Franchise en base TVA (art. 293 B CGI)",
    },
    "DOM_GUYANE_MAYOTTE": {
        # Guyane / Mayotte, art. 294 — territoire hors champ TVA
        "mention": "TVA non applicable, art. 294 du CGI",
        "vat_category": "O",
        "vatex_code": "VATEX-EU-O",
        "label": "TVA non applicable (art. 294 CGI · Guyane / Mayotte)",
    },
    "EXEMPT_OTHER": {
        "mention": "TVA non applicable",
        "vat_category": "E",
        "vatex_code": "VATEX-EU-O",
        "label": "Autre exonération de TVA",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_active_regime(override: Optional[str] = None) -> str:
    """Retourne le régime actif (override > settings.INVOICING > STANDARD)."""
    if override:
        return override
    cfg = getattr(settings, "INVOICING", {}) or {}
    return cfg.get("VAT_REGIME", "STANDARD")


def get_legal_tva_mention(regime: Optional[str] = None) -> str:
    """Mention légale TVA à afficher en pied de facture / footer.

    Chaîne vide si le régime est STANDARD (TVA appliquée).
    """
    return _REGIMES.get(get_active_regime(regime), _REGIMES["STANDARD"])["mention"]


def get_default_vat_category(regime: Optional[str] = None) -> str:
    """Code catégorie TVA EN 16931 par défaut pour les nouvelles lignes."""
    return _REGIMES.get(get_active_regime(regime), _REGIMES["STANDARD"])["vat_category"]


def get_default_vatex_code(regime: Optional[str] = None) -> str:
    """Code VATEX par défaut. Vide pour le régime STANDARD."""
    return _REGIMES.get(get_active_regime(regime), _REGIMES["STANDARD"])["vatex_code"]


def get_regime_label(regime: Optional[str] = None) -> str:
    """Libellé humain du régime, pour l'admin."""
    return _REGIMES.get(get_active_regime(regime), _REGIMES["STANDARD"])["label"]


def is_vat_applicable(regime: Optional[str] = None) -> bool:
    """True si la TVA est réellement collectée (régime STANDARD uniquement)."""
    return get_active_regime(regime) == "STANDARD"


__all__ = [
    "get_active_regime",
    "get_legal_tva_mention",
    "get_default_vat_category",
    "get_default_vatex_code",
    "get_regime_label",
    "is_vat_applicable",
]
