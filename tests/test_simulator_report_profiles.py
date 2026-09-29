"""Contrat de qualité des rapports simulateur.

Le but est d'empêcher le retour à un PDF générique : chaque outil public qui
peut produire un rapport doit avoir un profil éditorial propre, des limites du
modèle et une marche à suivre.
"""
from __future__ import annotations

from pathlib import Path

from apps.simulateur.report_content import REPORT_OVERRIDES, get_content_for


REPORT_TOOL_SLUGS = (
    "point-mort",
    "cac",
    "friction",
    "fragmentation",
    "acse",
    "plafond",
    "elasticite",
    "vallee-mort",
    "retention",
    "mix-produits",
    "atterrissage",
    "tresorerie",
    "jumeaux-clients",
    "correlation",
    "delegation",
    "prix-psychologique",
    "dependance",
    "capacite",
    "saisonnalite",
    "cout-promotion",
    "valeur-sortie",
    "effort-impact",
    "cout-inaction",
    "scenario-pivot",
    "roi-marketing",
    "pricing-paliers",
    "taille-marche",
    "vulnerabilite-fournisseur",
    "cout-non-qualite",
)


def test_every_reportable_tool_has_an_explicit_profile():
    assert len(REPORT_TOOL_SLUGS) == 29
    missing = [slug for slug in REPORT_TOOL_SLUGS if slug not in REPORT_OVERRIDES]
    assert missing == [], f"Profils rapport manquants : {missing}"

    for slug in REPORT_TOOL_SLUGS:
        profile = get_content_for(slug)
        assert profile.get("category"), slug
        assert len(profile.get("measures", "")) >= 80, slug
        assert len(profile.get("limits", [])) >= 2, slug
        assert len(profile.get("next_steps", [])) >= 4, slug
        assert profile.get("framework"), slug


def test_known_semantic_mismatches_do_not_return():
    acse = get_content_for("acse")["measures"]
    assert "Structurer" in acse and "Exécuter" in acse
    assert "Servir" not in acse and "Étendre" not in acse

    atterrissage = get_content_for("atterrissage")["measures"]
    assert "pipeline" in atterrissage.lower()
    assert "onboarding" not in atterrissage.lower()

    fragmentation = get_content_for("fragmentation")["measures"]
    assert "SaaS" in fragmentation
    assert "abonnements" in fragmentation

    correlation = get_content_for("correlation")["measures"]
    assert "co-achat" in correlation.lower()
    assert "actions" not in correlation.lower()

    elasticite = get_content_for("elasticite")["measures"]
    assert "pas l'élasticité observée" in elasticite


def test_pdf_template_contains_the_full_decision_flow():
    template = Path("templates/pdf/simulateur_report.html").read_text(encoding="utf-8")

    required = (
        "Ce qu'il en est",
        "Les chiffres de votre simulation",
        "Ce que ce résultat ne dit pas",
        "Marche à suivre",
        "Transformer ce scénario en décision opérationnelle",
    )
    for text in required:
        assert text in template

    # Régression : cette légende était écrite pour Pricing par Paliers mais
    # apparaissait sous les graphiques de tous les simulateurs.
    assert "comparez le poids de chaque palier" not in template
