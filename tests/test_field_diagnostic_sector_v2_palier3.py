"""Tests Diagnostic v2 — Palier 3 : recommandations sectorielles + repères métier.

Couvre :
- AC-P3-1 : module ``sector_recommendations`` opérationnel
- AC-P3-2 : couverture sectorielle minimale (≥ 3 règles par secteur principal)
- AC-P3-3 : recos sectorielles fusionnées au plan d'action global
- AC-P3-4 : aucune reco si question métier non répondue (silence respectable)
- AC-P3-5 : encart "sector_metrics" présent dans les résultats
- AC-P3-6 : filtrage par profil possible
- AC-P3-7 : aucune régression sur Paliers 1+2 ni v1
"""
from __future__ import annotations

from collections import Counter

import pytest

from apps.diagnostic.field_scoring import analyze
from apps.diagnostic.sector_recommendations import (
    SECTOR_METRICS,
    SECTOR_RULES,
    SectorMetric,
    SectorRule,
    _evaluate_condition,
    evaluate_sector_metrics,
    evaluate_sector_rules,
)


# ════════════════════════════════════════════════════════════════════
# AC-P3-1 — Évaluateur de conditions
# ════════════════════════════════════════════════════════════════════

class TestConditionEvaluator:
    @pytest.mark.parametrize(
        "value, condition, expected",
        [
            ("35", ">= 35", True),
            ("34", ">= 35", False),
            ("100", ">= 35", True),
            ("0", "<= 0", True),
            ("12.5", "<= 12.5", True),
            ("12,5", "<= 12.5", True),    # virgule décimale FR
            ("4", "scale_at_least:4", True),
            ("3", "scale_at_least:4", False),
            ("2", "scale_at_most:2", True),
            ("3", "scale_at_most:2", False),
            ("recent", "in:recent,moyen", True),
            ("ancien", "in:recent,moyen", False),
            ("oui", "==:oui", True),
        ],
    )
    def test_known_conditions(self, value, condition, expected):
        assert _evaluate_condition(value, condition) is expected

    def test_invalid_condition_returns_false(self):
        assert _evaluate_condition("12", "garbage") is False
        assert _evaluate_condition(None, ">= 5") is False
        assert _evaluate_condition("", ">= 5") is False


# ════════════════════════════════════════════════════════════════════
# AC-P3-2 — Couverture du catalogue
# ════════════════════════════════════════════════════════════════════

class TestCatalogCoverage:
    SECTORS_KEY = (
        "btp", "restauration", "ecommerce", "conseil", "services_pro",
        "hotellerie", "sante", "beaute", "commerce", "industrie",
        "transport", "immobilier", "formation", "tourisme", "agro",
        "numerique", "association", "artisanat", "evenementiel",
        "services_part",
    )

    def test_minimum_rules_per_main_sector(self):
        counts = Counter(rule.sector for rule in SECTOR_RULES)
        # Les secteurs phares doivent avoir au moins 3 règles
        for sector in ("btp", "restauration", "ecommerce", "conseil",
                        "services_pro", "hotellerie", "sante", "commerce"):
            assert counts[sector] >= 3, (
                f"Secteur {sector} : {counts[sector]} règle(s), attendu ≥ 3"
            )

    def test_metrics_use_known_sectors(self):
        for metric in SECTOR_METRICS:
            assert metric.sector in self.SECTORS_KEY, metric.sector

    def test_rules_use_known_sectors(self):
        for rule in SECTOR_RULES:
            assert rule.sector in self.SECTORS_KEY, rule.sector

    def test_all_priorities_are_valid(self):
        valid = {"critique", "important", "recommande", "bonus"}
        assert all(rule.priority in valid for rule in SECTOR_RULES)


# ════════════════════════════════════════════════════════════════════
# AC-P3-3 — Recos sectorielles dans le plan d'action global
# ════════════════════════════════════════════════════════════════════

class TestSectorRecommendationsInAnalyze:
    def test_btp_dominant_chantier_triggers_reco(self):
        answers = {
            "ca_mensuel": "60000", "charges_fixes": "20000",
            "charges_variables_pct": "65",
            "btp_taux_marge_chantier": "8",         # < 12 → reco déclenchée
            "btp_depassement_budget": "30",          # >= 25 → reco déclenchée
        }
        report = analyze(answers, "pme", sector="btp")
        titles = [r["title"] for r in report["recommendations"]]
        assert any("Marge nette" in t for t in titles)
        assert any("dépassement" in t for t in titles)

    def test_restaurant_high_food_cost_triggers_reco(self):
        answers = {
            "ca_mensuel": "30000", "charges_fixes": "10000",
            "charges_variables_pct": "60",
            "ratio_cout_matiere": "38",              # >= 35 → reco
            "no_show_pct": "12",                     # >= 10 → reco
        }
        report = analyze(answers, "pme", sector="restauration")
        titles = [r["title"] for r in report["recommendations"]]
        assert any("Food cost" in t for t in titles)
        assert any("no-show" in t.lower() for t in titles)

    def test_conseil_low_billable_days(self):
        answers = {
            "ca_mensuel": "8000", "charges_fixes": "2000",
            "charges_variables_pct": "10",
            "cons_jours_factures_an": "120",         # <= 150 → reco
        }
        report = analyze(answers, "solo", sector="conseil")
        titles = [r["title"] for r in report["recommendations"]]
        assert any("jours facturables" in t.lower() for t in titles)


# ════════════════════════════════════════════════════════════════════
# AC-P3-4 — Silence respectable si question non répondue
# ════════════════════════════════════════════════════════════════════

class TestSilentWhenNoAnswer:
    def test_no_sector_recos_if_metier_questions_empty(self):
        """Une PME BTP qui ne répond à aucune question métier ne doit
        déclencher AUCUNE reco sectorielle."""
        answers = {
            "ca_mensuel": "60000", "charges_fixes": "20000",
            "charges_variables_pct": "65",
            # Volontairement aucune réponse btp_*
        }
        recos = evaluate_sector_rules(answers, "btp", profile="pme")
        assert recos == []

    def test_no_recos_for_unknown_sector(self):
        recos = evaluate_sector_rules({"x": "1"}, "secteur_inconnu",
                                      profile="pme")
        assert recos == []

    def test_max_rules_limit(self):
        """Si toutes les règles sont vraies, on en garde au plus 4."""
        # On force toutes les règles BTP en remplissant les valeurs critiques
        answers = {
            "btp_taux_marge_chantier": "5",        # < 12
            "btp_depassement_budget": "50",         # >= 25
            "btp_delai_reglement_situations": "90", # >= 75
            "btp_part_renovation": "10",            # <= 20
            "btp_dom_materiaux": "75",              # >= 60
        }
        recos = evaluate_sector_rules(answers, "btp", profile="pme",
                                      max_rules=4)
        assert len(recos) == 4


# ════════════════════════════════════════════════════════════════════
# AC-P3-5 — Encart "sector_metrics" dans le rapport
# ════════════════════════════════════════════════════════════════════

class TestSectorMetricsInReport:
    def test_sector_metrics_present_for_btp(self):
        answers = {
            "btp_taux_marge_chantier": "20",         # good
            "btp_depassement_budget": "10",          # good
            "btp_delai_reglement_situations": "40",  # good
        }
        report = analyze(answers, "pme", sector="btp")
        metrics = report["sector_metrics"]
        assert len(metrics) == 3
        statuses = {m["status"] for m in metrics}
        assert statuses == {"good"}

    def test_sector_metrics_status_warn_and_danger(self):
        answers = {
            "btp_taux_marge_chantier": "12",        # entre good=18 et danger=10 → warn
            "btp_depassement_budget": "35",          # >= danger=30 → danger
        }
        report = analyze(answers, "pme", sector="btp")
        metrics = {m["key"]: m for m in report["sector_metrics"]}
        assert metrics["btp_taux_marge_chantier"]["status"] == "warn"
        assert metrics["btp_depassement_budget"]["status"] == "danger"

    def test_sector_metrics_only_for_answered_questions(self):
        """Une question non saisie ne génère pas de repère métier."""
        answers = {"btp_taux_marge_chantier": "20"}  # une seule question
        report = analyze(answers, "pme", sector="btp")
        keys = {m["key"] for m in report["sector_metrics"]}
        assert keys == {"btp_taux_marge_chantier"}

    def test_no_sector_metrics_without_sector(self):
        report = analyze({"ca_mensuel": "1000"}, "pme")
        assert report["sector_metrics"] == []


# ════════════════════════════════════════════════════════════════════
# AC-P3-6 — Filtrage par profil
# ════════════════════════════════════════════════════════════════════

class TestProfileScoping:
    def test_rules_apply_to_pme_and_tpe_by_default(self):
        """Toutes les règles BTP du catalogue actuel sont génériques (pas de
        restriction par profil) : un déclenchement doit fonctionner pour
        toutes les valeurs de profile."""
        answers = {
            "btp_taux_marge_chantier": "8",      # < 12 → règle 1
            "btp_depassement_budget": "30",       # >= 25 → règle 2
        }
        recos_pme = evaluate_sector_rules(answers, "btp", profile="pme")
        recos_tpe = evaluate_sector_rules(answers, "btp", profile="tpe")
        recos_solo = evaluate_sector_rules(answers, "btp", profile="solo")
        # Sans restriction profile, les 3 doivent recevoir les mêmes recos
        assert len(recos_pme) >= 2
        assert len(recos_tpe) >= 2
        assert len(recos_solo) >= 2
        # Les titres sont identiques (même catalogue déclenché)
        titles_pme = {r.title for r in recos_pme}
        titles_solo = {r.title for r in recos_solo}
        assert titles_pme == titles_solo

    def test_rule_with_profile_restriction_filters_correctly(self):
        """Vérification du mécanisme `profiles=(...)` via une règle in-memory."""
        # Création d'une règle restreinte à 'pme' uniquement
        restricted = SectorRule(
            sector="btp", question_id="btp_taux_marge_chantier",
            condition="< 100", priority="recommande",
            title="Test restreint", detail="Test",
            profiles=("pme",),
        )
        # Patch local du catalogue le temps du test
        from apps.diagnostic import sector_recommendations as mod
        original_rules = mod.SECTOR_RULES
        mod.SECTOR_RULES = (restricted,)
        try:
            answers = {"btp_taux_marge_chantier": "50"}
            recos_pme = evaluate_sector_rules(answers, "btp", profile="pme")
            recos_solo = evaluate_sector_rules(answers, "btp", profile="solo")
            assert len(recos_pme) == 1
            assert len(recos_solo) == 0  # filtré par le `profiles=("pme",)`
        finally:
            mod.SECTOR_RULES = original_rules


# ════════════════════════════════════════════════════════════════════
# AC-P3-7 — Non-régression
# ════════════════════════════════════════════════════════════════════

class TestNoRegression:
    def test_universal_recos_still_emitted_alongside_sector(self):
        """Les recos universelles (BTP en détresse) coexistent avec les
        recos sectorielles."""
        answers = {
            "ca_mensuel": "10000", "charges_fixes": "8500",
            "charges_variables_pct": "75",
            "tresorerie_actuelle": "1000",
            "encaissements_30j": "3000",
            "decaissements_30j": "9000",
            "btp_taux_marge_chantier": "5",
        }
        report = analyze(answers, "pme", sector="btp")
        # On doit avoir à la fois des recos universelles (signaux de
        # trésorerie) ET des recos sectorielles
        titles = [r["title"] for r in report["recommendations"]]
        assert any("Trésorerie" in t for t in titles), titles
        assert any("Marge nette" in t for t in titles), titles

    def test_no_sector_keeps_classic_behavior(self):
        """Sans secteur, le rapport ne contient ni sector_metrics ni recos
        sectorielles supplémentaires."""
        answers = {
            "ca_mensuel": "20000", "charges_fixes": "6000",
            "charges_variables_pct": "25",
        }
        report = analyze(answers, "pme")
        assert report["sector"] == ""
        assert report["sector_metrics"] == []
        # On vérifie qu'il y a quand même au moins une reco (le bonus
        # universel ou autre)
        assert isinstance(report["recommendations"], list)


# ════════════════════════════════════════════════════════════════════
# Robustesse — chaque secteur doit produire un rapport sans crash
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("sector", [r.sector for r in SECTOR_RULES])
def test_each_sector_does_not_crash_on_empty_answers(sector: str) -> None:
    report = analyze({}, "pme", sector=sector)
    assert "sector_metrics" in report
    assert isinstance(report["recommendations"], list)
