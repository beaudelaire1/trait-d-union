"""Correctifs de contenu des rapports stratégiques.

Ce module permet de corriger immédiatement un contenu publié sans dupliquer
l'ensemble du catalogue de ``report_content.py``. Les entrées non surchargées
continuent d'utiliser la source existante.
"""
from __future__ import annotations

from .report_content import get_content_for as _base_get_content_for


_ATERRISSAGE = {
    'category': 'Pilotage financier',
    'measures': (
        "L'atterrissage prévisionnel projette la fin de période à partir du "
        "chiffre d'affaires déjà réalisé, des objectifs par service ou produit, "
        "du pipeline pondéré par sa probabilité de conversion et des mois "
        "restants. Il met cette trajectoire en regard de la marge attendue, "
        "des RFA et des PPTG afin de distinguer le volume de chiffre d'affaires "
        "du résultat économique réellement attendu."
    ),
    'questions': [
        "Les taux de conversion appliqués au pipeline sont-ils fondés sur l'historique réel ou sur une hypothèse optimiste ?",
        "Quels services ou produits portent l'écart à l'objectif, et quelle cadence mensuelle faudrait-il tenir pour le résorber ?",
        "Une fois la marge, les RFA et les PPTG intégrés, la trajectoire reste-t-elle économiquement satisfaisante ?",
    ],
    'next_steps': [
        "Rapprochez le CA réalisé avec la comptabilité ou la facturation avant de figer la projection.",
        "Nettoyez le pipeline : retirez les opportunités perdues, doublons et montants insuffisamment qualifiés.",
        "Calibrez le taux de conversion de chaque service sur vos données historiques plutôt que sur un taux unique par défaut.",
        "Testez au moins trois scénarios — prudent, central et haut — pour mesurer la sensibilité de l'atterrissage.",
        "Transformez l'écart restant en objectif mensuel par service et suivez-le à fréquence régulière jusqu'à la clôture.",
    ],
    'framework': (
        "Un atterrissage n'est pas un budget bis : c'est une estimation révisable "
        "de la fin de période. Sa qualité dépend moins de la précision apparente "
        "du chiffre final que de la fiabilité des hypothèses de réalisation, "
        "de conversion, de marge et de remises commerciales."
    ),
}


def get_content_for(tool_slug: str) -> dict:
    """Retourne le contenu stratégique corrigé lorsqu'une surcharge existe."""
    if tool_slug == 'atterrissage':
        return _ATERRISSAGE.copy()
    return _base_get_content_for(tool_slug)
